"""autovideo CLI 진입점.

명령:
  autovideo doctor              환경/키 점검
  autovideo status              브랜드/프로젝트 상태
  autovideo brand [--only X]    Phase 1 브랜드 세팅 (대화형)
  autovideo create "주제" ...    Phase 2 콘텐츠 제작
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from . import __version__, env
from .orchestrator import cprint, hr


def cmd_doctor(args):
    cprint("🩺 autovideo doctor — 환경 점검", "head")
    hr()
    ok = True

    # 1) Python
    print(f"Python         : {sys.version.split()[0]}  ({sys.executable})")

    # 2) 설정 파일
    print(f"config/models  : {'✔' if env.MODELS_FILE.exists() else '✖ 없음'}")
    print(f"api-keys.env   : {'✔' if env.API_KEYS_FILE.exists() else '✖ 없음 (api-keys.env.example 복사 필요)'}")

    # 3) API 키
    keys = env.load_api_keys()
    def keystat(name):
        return "✔ 설정됨" if env.get_key(name) else "− 미설정"
    print(f"GEMINI_API_KEY : {keystat('GEMINI_API_KEY')}   (gemini provider / veo)")
    print(f"ANTHROPIC_KEY  : {keystat('ANTHROPIC_API_KEY')}   (claude provider)")
    print(f"ELEVENLABS_KEY : {keystat('ELEVENLABS_API_KEY')}   (나레이션)")
    provider = (os.environ.get("AUTOVIDEO_LLM") or "gemini").lower()
    need_key = "GEMINI_API_KEY" if provider == "gemini" else "ANTHROPIC_API_KEY"
    print(f"기본 provider   : {provider}  (전환: --llm 또는 AUTOVIDEO_LLM)")
    if not env.get_key(need_key):
        ok = False

    # 4) 의존성
    def has(mod):
        try:
            __import__(mod); return True
        except ImportError:
            return False
    print(f"google-genai   : {'✔' if has('google.genai') else '✖ 미설치 (pip install -e \".[dev]\")'}")
    print(f"anthropic      : {'✔' if has('anthropic') else '− 미설치 (claude 쓸 때: pip install anthropic)'}")
    print(f"pyyaml         : {'✔' if has('yaml') else '✖ 미설치'}")
    pkg = "google.genai" if provider == "gemini" else "anthropic"
    if not has(pkg):
        ok = False

    # 5) 외부 도구
    import shutil
    print(f"ffmpeg/ffprobe : {'✔' if shutil.which('ffprobe') else '✖ 미설치 (brew install ffmpeg)'}")
    print(f"ima2           : {'✔' if shutil.which('ima2') else '− 미설치 (이미지 생성 시 필요)'}")

    # 6) 브랜드 상태
    hr()
    bs = env.brand_status()
    cprint("브랜드(Phase 1) 상태:", "info")
    for k, v in bs.items():
        print(f"  {k:10s}: {'✔ 작성됨' if v else '− 비어있음'}")

    hr()
    if ok:
        cprint("✅ 핵심 준비 완료 — `autovideo brand` 또는 `autovideo create \"주제\"` 가능", "ok")
    else:
        cprint("⚠ 일부 미준비 — 위 ✖ 항목을 먼저 해결하세요.", "warn")
    return 0 if ok else 1


def cmd_status(args):
    cprint("📊 상태", "head")
    hr()
    bs = env.brand_status()
    cprint("브랜드(Phase 1):", "info")
    for k, v in bs.items():
        print(f"  {k:10s}: {'✔' if v else '−'}")
    phase = "Phase 2 가능" if all(bs.values()) else "Phase 1 필요"
    print(f"\n→ 현재: {phase}")

    hr()
    cprint("프로젝트(Phase 2):", "info")
    if env.PROJECTS_DIR.exists():
        projs = sorted([p for p in env.PROJECTS_DIR.iterdir() if p.is_dir()])
        if projs:
            for p in projs:
                has_script = (p / "script.md").exists()
                has_final = any(p.glob("output/final.mp4")) or any(p.glob("**/final.mp4"))
                mark = "🎬" if has_final else ("📝" if has_script else "📂")
                print(f"  {mark} {p.name}")
        else:
            print("  (없음)")
    else:
        print("  (projects/ 없음)")
    return 0


def cmd_models(args):
    from .llm_client import LLM, LLMError
    cprint("🔎 사용 가능한 Gemini 모델 (generateContent 지원)", "head")
    hr()
    try:
        llm = LLM(provider=args.llm, model_override=args.model)
        names = llm.list_models()
    except LLMError as e:
        cprint(f"✖ {e}", "warn")
        return 1
    if not names:
        cprint("− 목록이 비어 있습니다.", "warn")
        return 1
    for n in names:
        mark = "⭐" if n in ("gemini-2.5-flash", "gemini-2.5-pro") else "  "
        print(f"  {mark} {n}")
    hr()
    cprint("권장: gemini-2.5-flash (기본) / gemini-2.5-pro (고품질)", "info")
    cprint("설정 변경: config/models.yaml  또는  --model 플래그", "dim")
    return 0


def cmd_brand(args):
    from .llm_client import LLM, LLMError
    from .orchestrator import run_phase1
    try:
        llm = LLM(provider=args.llm, model_override=args.model)
        run_phase1(llm, only=args.only, quick=args.quick)
    except LLMError as e:
        cprint(f"\n✖ {e}", "warn")
        return 1
    return 0


def cmd_create(args):
    from .llm_client import LLM, LLMError
    from .orchestrator import run_phase2
    try:
        llm = LLM(provider=args.llm, model_override=args.model)
        run_phase2(
            llm,
            topic=args.topic,
            duration_sec=args.duration,
            provider=args.provider,
            run_media=args.media,
            force=args.force,
        )
    except LLMError as e:
        cprint(f"\n✖ {e}", "warn")
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="autovideo",
        description="Claude Code 없이 독립 실행되는 AI 영상 제작 CLI",
    )
    p.add_argument("--version", action="version", version=f"autovideo {__version__}")

    # --model 을 모든 서브명령에서 쓸 수 있도록 공통 부모 파서로 정의
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--model", default=None,
                        help="LLM 모델 강제 지정 (예: gemini-2.5-flash, claude-opus-4-8)")
    common.add_argument("--llm", default=None, choices=["gemini", "claude"],
                        help="LLM provider 선택 (기본 gemini, 또는 AUTOVIDEO_LLM 환경변수)")

    sub = p.add_subparsers(dest="command", required=True)

    sp = sub.add_parser("doctor", parents=[common], help="환경/키 점검")
    sp.set_defaults(func=cmd_doctor)

    sp = sub.add_parser("status", parents=[common], help="브랜드/프로젝트 상태")
    sp.set_defaults(func=cmd_status)

    sp = sub.add_parser("models", parents=[common], help="사용 가능한 LLM 모델 목록")
    sp.set_defaults(func=cmd_models)

    sp = sub.add_parser("brand", parents=[common], help="Phase 1 브랜드 세팅 (대화형)")
    sp.add_argument("--only", choices=["character", "narrative", "topics", "benchmark"],
                    default=None, help="특정 brand 파일만 (재)생성")
    sp.add_argument("--quick", action="store_true",
                    help="퀵 모드: 에이전트당 API 1회만 호출 (무료 등급 친화)")
    sp.set_defaults(func=cmd_brand)

    sp = sub.add_parser("create", parents=[common], help="Phase 2 콘텐츠 제작")
    sp.add_argument("topic", help="영상 주제")
    sp.add_argument("--duration", type=int, default=59, help="러닝타임(초), 기본 59")
    sp.add_argument("--provider", default="veo",
                    choices=["veo", "grok", "kling", "higgsfield"], help="영상 provider")
    sp.add_argument("--media", action="store_true",
                    help="텍스트뿐 아니라 이미지/음성/합성까지 실행")
    sp.add_argument("--force", action="store_true",
                    help="brand 4개가 완성되지 않아도 강행 (테스트용)")
    sp.set_defaults(func=cmd_create)

    return p


def app(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    # --model 을 서브커맨드에서도 접근 가능하게
    if not hasattr(args, "model"):
        args.model = None
    return args.func(args)


def main():
    sys.exit(app())


if __name__ == "__main__":
    main()
