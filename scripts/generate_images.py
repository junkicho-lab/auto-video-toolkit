"""GPT Image 2 (ima2) 기반 씬별 이미지 생성.

로컬 ima2 서버(`ima2 serve`)를 통해 GPT Image 2 / GPT-5 이미지 모델로 씬 이미지를 생성한다.
기존 Imagen/Nano Banana(google-genai) 경로를 대체한다.

사전조건:
  1. `npm install -g ima2-gen` (또는 vendor/ima2-gen 에서 npm install 후 사용)
  2. `ima2 serve` 가 실행 중
  3. Codex OAuth 로그인(`npx @openai/codex login`) 또는 OPENAI_API_KEY 설정

scene-prompts.md 포맷(### Scene N: / **Image N Prompt:**)을 파싱한다.
캐릭터 일관성을 위해 앵커 이미지를 --ref(--anchor) 로 전달할 수 있다.
"""

import argparse
import os
import re
import shutil
import subprocess
import time
from pathlib import Path

IMA2_BIN = os.environ.get("IMA2_BIN", "ima2")


def check_ima2_ready() -> tuple[bool, str]:
    """ima2 CLI 존재 + 서버 health 확인. (ok, message)"""
    if shutil.which(IMA2_BIN) is None:
        return False, (
            f"'{IMA2_BIN}' 명령을 찾을 수 없습니다. "
            "`npm install -g ima2-gen` 또는 vendor/ima2-gen 에서 설치하세요."
        )
    try:
        r = subprocess.run(
            [IMA2_BIN, "ping"], capture_output=True, timeout=15, text=True
        )
        if r.returncode != 0:
            return False, (
                "ima2 서버에 연결할 수 없습니다. 다른 터미널에서 `ima2 serve` 를 먼저 실행하세요."
            )
        return True, "ok"
    except Exception as e:  # noqa: BLE001
        return False, f"ima2 ping 실패: {e}"


def generate_image_ima2(
    prompt: str,
    out_path: Path,
    *,
    quality: str = "high",
    size: str = "1024x1536",
    refs: list[str] | None = None,
    model: str | None = None,
    mode: str = "direct",
    timeout: int = 300,
) -> bool:
    """ima2 CLI로 이미지 1장 생성. 성공 시 True."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        IMA2_BIN, "gen", prompt,
        "-o", str(out_path),
        "-q", quality,
        "-s", size,
        "--mode", mode,
        "--no-web-search",
    ]
    if model:
        cmd += ["--model", model]
    for ref in refs or []:
        cmd += ["--ref", str(ref)]

    try:
        r = subprocess.run(cmd, capture_output=True, timeout=timeout, text=True)
    except subprocess.TimeoutExpired:
        print(f"    → 타임아웃({timeout}s)")
        return False

    if r.returncode != 0:
        print(f"    → ima2 에러: {(r.stderr or r.stdout).strip()[:200]}")
        return False
    if not out_path.exists():
        print("    → 생성 파일 없음")
        return False
    return True


def parse_prompts(prompts_path: str) -> list[dict]:
    """scene-prompts.md에서 씬별 프롬프트를 파싱한다.

    단일(**Prompt:**) / 멀티 이미지(**Image N Prompt:**) 포맷을 지원.
    """
    text = Path(prompts_path).read_text(encoding="utf-8")
    scenes: list[dict] = []

    parts = re.split(r"(?=### Scene \d+:)", text)
    for part in parts:
        match = re.match(r"### Scene (\d+): (.+)", part)
        if not match:
            continue
        scene_num = int(match.group(1))
        title = match.group(2).strip()

        image_prompts = re.findall(
            r"\*\*Image \d+ Prompt:\*\*\n(.+?)(?=\n\*\*(?:Ken Burns|Consistency|Image \d+ Prompt))",
            part,
            re.DOTALL,
        )
        if image_prompts:
            scenes.append({
                "scene_number": scene_num,
                "title": title,
                "image_prompts": [p.strip() for p in image_prompts],
            })
        else:
            prompt_match = re.search(
                r"\*\*Prompt:\*\*\n(.+?)(?=\n\*\*Audio Direction)", part, re.DOTALL
            )
            prompt = prompt_match.group(1).strip() if prompt_match else ""
            if prompt:
                scenes.append({
                    "scene_number": scene_num,
                    "title": title,
                    "image_prompts": [prompt],
                })
    return scenes


def generate_scene_images(
    scenes: list[dict],
    scenes_dir: str,
    *,
    quality: str = "high",
    size: str = "1024x1536",
    model: str | None = None,
    anchor: str | None = None,
):
    """ima2(GPT Image 2)로 씬별 이미지를 생성한다."""
    ready, msg = check_ima2_ready()
    if not ready:
        raise SystemExit(f"[ima2] {msg}")

    refs = [anchor] if anchor else None
    print(f"\n=== GPT Image 2 (ima2) 이미지 생성 — {len(scenes)}씬 ===\n")
    total, errors = 0, 0

    for scene in scenes:
        scene_dir = Path(scenes_dir) / f"scene-{scene['scene_number']:02d}"
        prompts = scene.get("image_prompts", [])
        for j, prompt in enumerate(prompts):
            img_path = scene_dir / f"img_{j + 1:02d}.png"
            if img_path.exists():
                print(f"  Scene {scene['scene_number']:02d} img_{j + 1}: 존재 — 스킵")
                total += 1
                continue
            print(f"  Scene {scene['scene_number']:02d} img_{j + 1}: 생성 중...")
            ok = generate_image_ima2(
                prompt, img_path,
                quality=quality, size=size, refs=refs, model=model,
            )
            if ok:
                kb = img_path.stat().st_size // 1024
                print(f"    → 완료 ✓ ({kb}KB)")
                total += 1
            else:
                errors += 1
            time.sleep(1)

    print(f"\n이미지 생성 완료: {total}장 성공, {errors}개 실패\n")


def main():
    parser = argparse.ArgumentParser(description="GPT Image 2(ima2) 씬별 이미지 생성")
    parser.add_argument("--project", required=True, help="프로젝트 디렉토리")
    parser.add_argument("--prompts", default="scene-prompts.md", help="프롬프트 파일명")
    parser.add_argument("--quality", default="high", choices=["low", "medium", "high"])
    parser.add_argument("--size", default="1024x1536", help="WxH 또는 auto")
    parser.add_argument("--model", default=None, help="gpt-5.5 | gpt-5.4 | gpt-5.4-mini")
    parser.add_argument("--anchor", default=None, help="캐릭터 일관성용 앵커 이미지 경로(--ref)")
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--end", type=int, default=999)
    args = parser.parse_args()

    prompts_path = Path(args.project) / args.prompts
    scenes_dir = Path(args.project) / "scenes"

    all_scenes = parse_prompts(str(prompts_path))
    target = [s for s in all_scenes if args.start <= s["scene_number"] <= args.end]
    print(f"대상 씬: {len(target)}개 (Scene {args.start}~{args.end})")
    generate_scene_images(
        target, str(scenes_dir),
        quality=args.quality, size=args.size, model=args.model, anchor=args.anchor,
    )


if __name__ == "__main__":
    main()
