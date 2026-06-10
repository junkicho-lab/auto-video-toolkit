"""다중 provider 영상 생성 어댑터.

config/models.yaml의 `video_generation` 값(또는 --provider)으로 provider를 선택한다:
  veo | grok | kling | higgsfield

provider별 필요 키 (config/api-keys.env):
  veo        → GEMINI_API_KEY
  grok       → XAI_API_KEY
  kling      → KLING_ACCESS_KEY, KLING_SECRET_KEY  (+ pip install pyjwt)
  higgsfield → SEGMIND_API_KEY  (Higgsfield 모델을 Segmind 호스팅으로 호출)

text-to-video가 기본. image_url(공개 URL)이 주어지면 image-to-video.
모든 엔드포인트/파라미터는 각 provider 공식 문서 기준이며, 실제 영상 출력 품질은
해당 provider 키·과금이 있어야 검증된다.

공식 문서:
  Veo        https://ai.google.dev/gemini-api/docs/video
  Grok       https://docs.x.ai/developers/rest-api-reference/inference/videos
  Kling      https://app.klingai.com/global/dev/document-api
  Higgsfield https://www.segmind.com/models/higgsfield-image2video/api
"""

import argparse
import os
import re
import time
from pathlib import Path


def load_env(env_path: str = "config/api-keys.env") -> None:
    p = Path(env_path)
    if not p.exists():
        return
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            # 인라인 주석( ' #...') 제거 + 따옴표 제거 + 예시값 무시
            v = re.split(r"\s+#", v, maxsplit=1)[0].strip().strip('"').strip("'")
            if v and not v.lower().startswith(("your-", "your_", "<")):
                os.environ.setdefault(k.strip(), v)


def _require(*keys: str) -> None:
    missing = [k for k in keys if not os.environ.get(k)]
    if missing:
        raise SystemExit(
            f"[video] 필요한 키 미설정: {', '.join(missing)} — config/api-keys.env 확인"
        )


def _download(url: str, out_path: Path) -> None:
    import httpx

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with httpx.stream("GET", url, timeout=180, follow_redirects=True) as r:
        r.raise_for_status()
        with open(out_path, "wb") as f:
            for chunk in r.iter_bytes():
                f.write(chunk)


# ---------------- Veo (Google Gemini) ----------------
def veo_generate(prompt, out_path, *, image_path=None, duration="8",
                 aspect_ratio="16:9", resolution="720p", **_):
    _require("GEMINI_API_KEY")
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    kwargs = dict(
        model=os.environ.get("VEO_MODEL", "veo-3.1-generate-preview"),
        prompt=prompt,
        config=types.GenerateVideosConfig(
            aspect_ratio=aspect_ratio, resolution=resolution
        ),
    )
    if image_path:
        kwargs["image"] = types.Image.from_file(location=str(image_path))

    op = client.models.generate_videos(**kwargs)
    while not op.done:
        time.sleep(10)
        op = client.operations.get(op)
    video = op.response.generated_videos[0]
    client.files.download(file=video.video)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    video.video.save(str(out_path))
    return out_path.exists()


# ---------------- Grok (xAI) ----------------
def grok_generate(prompt, out_path, *, image_url=None, duration=8,
                  aspect_ratio="16:9", resolution="720p", **_):
    _require("XAI_API_KEY")
    import httpx

    headers = {"Authorization": f"Bearer {os.environ['XAI_API_KEY']}"}
    body = {
        "model": os.environ.get("GROK_VIDEO_MODEL", "grok-imagine-video"),
        "prompt": prompt,
        "duration": int(duration),
        "aspect_ratio": aspect_ratio,
        "resolution": resolution,
    }
    if image_url:
        body["image"] = {"url": image_url}

    r = httpx.post("https://api.x.ai/v1/videos/generations",
                   headers=headers, json=body, timeout=60)
    r.raise_for_status()
    req_id = r.json()["request_id"]

    while True:
        time.sleep(8)
        pr = httpx.get(f"https://api.x.ai/v1/videos/{req_id}",
                       headers=headers, timeout=60).json()
        status = pr.get("status")
        if status == "done":
            _download(pr["video"]["url"], out_path)
            return out_path.exists()
        if status == "failed":
            raise RuntimeError("Grok 영상 생성 실패")


# ---------------- Kling (Kuaishou) ----------------
def kling_generate(prompt, out_path, *, image_url=None, duration="5",
                   aspect_ratio="16:9", model_name=None, **_):
    _require("KLING_ACCESS_KEY", "KLING_SECRET_KEY")
    import httpx
    import jwt  # PyJWT

    ak, sk = os.environ["KLING_ACCESS_KEY"], os.environ["KLING_SECRET_KEY"]

    def _token():
        now = int(time.time())
        return jwt.encode(
            {"iss": ak, "exp": now + 1800, "nbf": now - 5}, sk, algorithm="HS256"
        )

    base = os.environ.get("KLING_BASE_URL", "https://api.klingai.com")
    model_name = model_name or os.environ.get("KLING_MODEL", "kling-v1")
    if image_url:
        path = "/v1/videos/image2video"
        body = {"model_name": model_name, "image": image_url,
                "prompt": prompt, "duration": str(duration)}
    else:
        path = "/v1/videos/text2video"
        body = {"model_name": model_name, "prompt": prompt,
                "aspect_ratio": aspect_ratio, "duration": str(duration)}

    r = httpx.post(base + path, headers={"Authorization": f"Bearer {_token()}"},
                   json=body, timeout=60)
    r.raise_for_status()
    task_id = r.json()["data"]["task_id"]

    while True:
        time.sleep(10)
        pr = httpx.get(f"{base}{path}/{task_id}",
                       headers={"Authorization": f"Bearer {_token()}"},
                       timeout=60).json()
        status = pr["data"]["task_status"]
        if status == "succeed":
            url = pr["data"]["task_result"]["videos"][0]["url"]
            _download(url, out_path)
            return out_path.exists()
        if status == "failed":
            raise RuntimeError(f"Kling 실패: {pr['data'].get('task_status_msg')}")


# ---------------- Higgsfield (via Segmind) ----------------
def higgsfield_generate(prompt, out_path, *, image_url=None, seed=12345,
                        motion_id=None, **_):
    _require("SEGMIND_API_KEY")
    import httpx

    headers = {"x-api-key": os.environ["SEGMIND_API_KEY"],
               "Content-Type": "application/json"}
    body = {
        "model": os.environ.get("HIGGSFIELD_MODEL", "dop-preview"),
        "prompt": prompt,
        "seed": int(seed),
        "motion_id": motion_id or os.environ.get("HIGGSFIELD_MOTION_ID", ""),
        "enhance_prompt": True,
        "check_nsfw": True,
    }
    if image_url:
        body["image_urls"] = [image_url]

    r = httpx.post("https://api.segmind.com/v1/higgsfield-image2video",
                   headers=headers, json=body, timeout=600)
    r.raise_for_status()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(r.content)
    return out_path.exists()


PROVIDERS = {
    "veo": veo_generate,
    "grok": grok_generate,
    "kling": kling_generate,
    "higgsfield": higgsfield_generate,
}


def resolve_provider(explicit: str | None) -> str:
    """--provider > VIDEO_PROVIDER env > config/models.yaml > 'veo'."""
    prov = explicit or os.environ.get("VIDEO_PROVIDER")
    if not prov:
        try:
            import yaml
            cfg = yaml.safe_load(Path("config/models.yaml").read_text(encoding="utf-8"))
            prov = (cfg.get("models", {}) or {}).get("video_generation", "veo")
        except Exception:  # noqa: BLE001
            prov = "veo"
    prov = str(prov).lower()
    if prov.startswith("veo"):
        return "veo"
    return prov if prov in PROVIDERS else "veo"


def parse_video_prompts(path: str) -> list[dict]:
    """video-prompts.md / scene-prompts.md 에서 씬별 영상 프롬프트 파싱."""
    text = Path(path).read_text(encoding="utf-8")
    scenes = []
    for part in re.split(r"(?=### Scene \d+:)", text):
        m = re.match(r"### Scene (\d+):", part)
        if not m:
            continue
        pm = re.search(
            r"\*\*(?:Video |Motion |Video )?Prompt:\*\*\n(.+?)(?=\n\*\*|\Z)",
            part, re.DOTALL,
        )
        if pm:
            scenes.append({"scene_number": int(m.group(1)), "prompt": pm.group(1).strip()})
    return scenes


def main():
    parser = argparse.ArgumentParser(description="다중 provider 영상 생성")
    parser.add_argument("--project", required=True)
    parser.add_argument("--prompts", default="video-prompts.md")
    parser.add_argument("--provider", default=None,
                        help="veo|grok|kling|higgsfield (생략 시 config/models.yaml)")
    parser.add_argument("--duration", default="5")
    parser.add_argument("--aspect-ratio", default="16:9")
    args = parser.parse_args()

    load_env()
    provider = resolve_provider(args.provider)
    fn = PROVIDERS[provider]

    scenes_dir = Path(args.project) / "scenes"
    prompts = parse_video_prompts(str(Path(args.project) / args.prompts))
    print(f"\n=== 영상 생성 [{provider}] — {len(prompts)}씬 ===\n")

    ok_n, err_n = 0, 0
    for s in prompts:
        out = scenes_dir / f"scene-{s['scene_number']:02d}" / "video.mp4"
        if out.exists():
            print(f"  Scene {s['scene_number']:02d}: 존재 — 스킵")
            ok_n += 1
            continue
        out.parent.mkdir(parents=True, exist_ok=True)
        print(f"  Scene {s['scene_number']:02d}: 생성 중 [{provider}]...")
        try:
            if fn(s["prompt"], out, duration=args.duration, aspect_ratio=args.aspect_ratio):
                print("    → 완료 ✓")
                ok_n += 1
            else:
                err_n += 1
        except Exception as e:  # noqa: BLE001
            print(f"    → 실패: {str(e)[:200]}")
            err_n += 1

    print(f"\n영상 생성 완료: {ok_n} 성공, {err_n} 실패  (provider={provider})\n")


if __name__ == "__main__":
    main()
