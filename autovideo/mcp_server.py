"""autovideo MCP 서버 — scripts/ 파이프라인을 Claude Code의 '도구'로 노출.

Claude Code(또는 Claude Desktop)가 .mcp.json으로 이 서버에 연결하면
`mcp__autovideo__generate_images` 같은 네이티브 도구로 파이프라인을 구동할 수 있다.

실행: python -m autovideo.mcp_server   (stdio 전송)
의존성: pip install -e ".[mcp]"   (mcp 패키지)
"""
from __future__ import annotations

import subprocess
import sys

from . import env

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:  # pragma: no cover
    raise SystemExit(
        "mcp 패키지가 필요합니다 — pip install -e \".[mcp]\" (또는 pip install mcp)"
    )

mcp = FastMCP("autovideo")

_MAX_OUT = 4000


def _run(args: list[str]) -> str:
    """scripts/ 명령을 실행하고 stdout/stderr 요약을 반환."""
    cmd = [sys.executable, *args]
    try:
        r = subprocess.run(cmd, cwd=str(env.ROOT), capture_output=True,
                           text=True, timeout=1800)
    except subprocess.TimeoutExpired:
        return "⏱️ 타임아웃(30분 초과)"
    out = (r.stdout or "") + (("\n[stderr]\n" + r.stderr) if r.returncode != 0 and r.stderr else "")
    out = out.strip() or "(출력 없음)"
    tag = "✅" if r.returncode == 0 else f"❌ exit {r.returncode}"
    return f"{tag}\n{out[-_MAX_OUT:]}"


# ---------------- 조회 도구 (subprocess 없음) ----------------
@mcp.tool()
def av_status() -> str:
    """브랜드(Phase 1) 4종 YAML과 프로젝트(Phase 2) 폴더 상태를 보고한다."""
    bs = env.brand_status()
    lines = ["[브랜드 Phase 1]"]
    lines += [f"  {k}: {'작성됨' if v else '비어있음'}" for k, v in bs.items()]
    lines.append("→ " + ("Phase 2 가능" if all(bs.values()) else "Phase 1 필요"))
    lines.append("[프로젝트 Phase 2]")
    if env.PROJECTS_DIR.exists():
        projs = sorted(p.name for p in env.PROJECTS_DIR.iterdir() if p.is_dir())
        lines += [f"  {p}" for p in projs] or ["  (없음)"]
    else:
        lines.append("  (projects/ 없음)")
    return "\n".join(lines)


@mcp.tool()
def video_first_calc(duration_sec: int, clip_len: int = 8) -> str:
    """Video-First 역산: 러닝타임·클립길이로 씬 수/총 단어/씬당 단어를 계산한다."""
    scenes = max(1, round(duration_sec / clip_len))
    total = round(duration_sec / 60 * 150)
    return (f"러닝타임 {duration_sec}s ÷ 클립 {clip_len}s = {scenes}씬 / "
            f"총 단어 ≈ {total} / 씬당 ≈ {round(total / scenes)}")


# ---------------- 실행 도구 (기존 scripts 호출) ----------------
@mcp.tool()
def generate_images(project: str, quality: str = "medium",
                    prompts: str = "image-prompts.md") -> str:
    """GPT Image 2(ima2)로 프로젝트의 씬 이미지를 생성한다. (사전: ima2 serve 실행)

    project: projects/ 하위 폴더명 또는 경로
    quality: low | medium | high
    """
    proj = project if "/" in project else f"projects/{project}"
    return _run(["scripts/generate_images.py", "--project", proj,
                 "--prompts", prompts, "--quality", quality])


@mcp.tool()
def generate_videos(project: str, provider: str = "veo",
                    prompts: str = "video-prompts.md") -> str:
    """선택한 provider(veo|grok|kling|higgsfield)로 영상 클립을 생성한다."""
    proj = project if "/" in project else f"projects/{project}"
    return _run(["scripts/generate_videos.py", "--project", proj,
                 "--prompts", prompts, "--provider", provider])


@mcp.tool()
def produce_voice(project: str, voice_id: str = "EXAVITQu4vr4xnSDxMaL",
                  fmt: str = "short") -> str:
    """ElevenLabs TTS로 씬별 나레이션을 생성한다. fmt: short | long"""
    proj = project if "/" in project else f"projects/{project}"
    return _run(["scripts/produce.py", "--project", proj, "--step", "voice",
                 "--voice-id", voice_id, "--format", fmt])


@mcp.tool()
def compositor(project: str, fmt: str = "short") -> str:
    """MoviePy로 이미지/영상/나레이션을 합성해 final.mp4를 만든다. fmt: short | long"""
    proj = project if "/" in project else f"projects/{project}"
    return _run(["scripts/compositor.py", "--project", proj, "--format", fmt])


def main():
    mcp.run()


if __name__ == "__main__":
    main()
