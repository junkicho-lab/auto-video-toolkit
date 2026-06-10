"""오케스트레이터 — director.md 로직을 코드로 구현한 '두뇌'.

- Phase 판단 (brand 상태 기반)
- Phase 1: 대화형 위저드 4단계 + 체크포인트
- Phase 2: 리서치 → 대본 → 씬연출 → (이미지/음성: 기존 scripts 호출) → 합성
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Optional

from . import agent_runner, env
from .llm_client import LLM, LLMError

# ----- 터미널 출력 헬퍼 -----
C = {
    "head": "\033[1;31m", "ok": "\033[1;32m", "warn": "\033[1;33m",
    "info": "\033[1;36m", "dim": "\033[2m", "reset": "\033[0m",
}


def _supports_color() -> bool:
    return sys.stdout.isatty()


def cprint(text: str, color: str = "reset"):
    if _supports_color():
        print(f"{C.get(color, '')}{text}{C['reset']}")
    else:
        print(text)


def hr():
    print("─" * 56)


def ask(prompt: str) -> str:
    try:
        return input(prompt)
    except (EOFError, KeyboardInterrupt):
        print()
        cprint("중단되었습니다.", "warn")
        sys.exit(130)


# ----- 체크포인트 -----
def checkpoint(label: str) -> str:
    """승인/수정/재생성/중단 선택. 반환: approve|revise|regen|quit + (revise시 피드백)."""
    hr()
    cprint(f"체크포인트 — {label}", "info")
    print("[y] 승인   [e] 수정요청   [r] 재생성   [q] 중단")
    choice = ask("선택 ▶ ").strip().lower()
    if choice in ("y", "yes", ""):
        return "approve"
    if choice in ("e", "edit", "revise"):
        return "revise"
    if choice in ("r", "regen", "regenerate"):
        return "regen"
    return "quit"


# ===================================================================
# Phase 1 — 브랜드 세팅 (대화형 위저드)
# ===================================================================
PHASE1_SEQUENCE = [
    ("brand-architect", "character"),
    ("narrative-designer", "narrative"),
    ("topic-strategist", "topics"),
    ("benchmark-analyst", "benchmark"),
]


def run_phase1(llm: LLM, only: Optional[str] = None, quick: bool = False):
    cprint("\n🏗️  Phase 1 — 브랜드 세팅", "head")
    print("채널의 정체성(캐릭터·서사·주제·벤치마크)을 만듭니다.\n")

    brief = ""
    if quick:
        cprint("⚡ 퀵 모드 — 에이전트당 API 1회만 호출합니다 (무료 등급 친화).", "info")
        print("채널을 1~2문장으로 설명해 주세요. (주제/시청자/분위기 포함)")
        print("모르면 그냥 Enter — AI가 알아서 추천해 채웁니다.")
        brief = ask("채널 설명 ▶ ").strip()

    status = env.brand_status()
    for agent_name, out_key in PHASE1_SEQUENCE:
        if only and out_key != only:
            continue
        if status.get(out_key) and not only:
            cprint(f"✔ {out_key}.yaml 이미 작성됨 — 건너뜀 (다시 하려면 --only {out_key})", "dim")
            continue
        if quick:
            _run_brand_agent_quick(llm, agent_name, out_key, brief)
        else:
            _run_brand_agent(llm, agent_name, out_key)

    cprint("\n✅ Phase 1 완료. 이제 `autovideo create \"주제\"` 로 영상을 만드세요.", "ok")


def _run_brand_agent_quick(llm: LLM, agent_name: str, out_key: str, brief: str):
    """퀵 모드: 추가 대화 없이 1회 호출로 YAML 생성 → 체크포인트 → 저장."""
    out_path = env.brand_files()[out_key]
    feedback = ""
    while True:
        cprint(f"\n▶ {agent_name} 실행 ({out_key}.yaml) — 호출 1회", "info")
        prompt = agent_runner.build_brand_oneshot(agent_name, brief, feedback)
        cprint("  LLM 호출 중...", "dim")
        text = llm.generate(prompt, purpose="script")
        final_yaml = agent_runner.extract_any_yaml(text) or text.strip()

        hr()
        cprint(f"📄 {out_key}.yaml (미리보기)", "ok")
        print(final_yaml)

        action = checkpoint(f"{out_key}.yaml 승인")
        if action == "approve":
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(final_yaml + "\n", encoding="utf-8")
            cprint(f"💾 저장됨: {out_path.relative_to(env.ROOT)}", "ok")
            return
        if action == "regen":
            feedback = ""
            continue
        if action == "revise":
            feedback = ask("수정 요청 내용 ▶ ").strip()
            continue
        cprint("중단되었습니다.", "warn")
        sys.exit(0)


def _run_brand_agent(llm: LLM, agent_name: str, out_key: str):
    out_path = env.brand_files()[out_key]
    while True:  # 재생성 루프
        cprint(f"\n▶ {agent_name} 실행 ({out_key}.yaml)", "info")
        system = agent_runner.build_wizard_system(agent_name)
        session = llm.chat(purpose="script", system=system)

        # 위저드 시작
        reply = session.send("CLI 모드입니다. 첫 질문부터 시작하세요.")
        final_yaml = None
        while True:
            extracted = agent_runner.extract_final_yaml(reply)
            if extracted:
                final_yaml = extracted
                break
            # 모델의 질문/메시지 출력 후 사용자 답변
            hr()
            print(reply)
            hr()
            user = ask("답변 ▶ ").strip()
            if user.lower() in ("q", "quit", "중단"):
                cprint("중단되었습니다.", "warn")
                sys.exit(0)
            reply = session.send(user)

        # 결과 미리보기
        hr()
        cprint(f"📄 {out_key}.yaml (미리보기)", "ok")
        print(final_yaml)

        action = checkpoint(f"{out_key}.yaml 승인")
        if action == "approve":
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(final_yaml + "\n", encoding="utf-8")
            cprint(f"💾 저장됨: {out_path.relative_to(env.ROOT)}", "ok")
            return
        if action == "regen":
            continue
        if action == "revise":
            feedback = ask("수정 요청 내용 ▶ ").strip()
            reply = session.send(f"다음 피드백을 반영해 다시 FINAL_YAML을 출력하세요: {feedback}")
            # 피드백 후 다시 루프 상단으로 돌아가 추출
            while True:
                extracted = agent_runner.extract_final_yaml(reply)
                if extracted:
                    final_yaml = extracted
                    break
                hr(); print(reply); hr()
                reply = session.send(ask("답변 ▶ ").strip())
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(final_yaml + "\n", encoding="utf-8")
            cprint(f"💾 저장됨: {out_path.relative_to(env.ROOT)}", "ok")
            return
        # quit
        cprint("중단되었습니다.", "warn")
        sys.exit(0)


# ===================================================================
# Phase 2 — 콘텐츠 제작
# ===================================================================
def video_first_calc(duration_sec: int, clip_len: int) -> dict:
    scenes = max(1, round(duration_sec / clip_len))
    total_words = round(duration_sec / 60 * 150)
    return {
        "duration_sec": duration_sec,
        "clip_len": clip_len,
        "scenes": scenes,
        "total_words": total_words,
        "words_per_scene": round(total_words / scenes),
    }


CLIP_LEN = {"veo": 8, "grok": 8, "kling": 10, "higgsfield": 8}


def run_phase2(llm: LLM, topic: str, duration_sec: int = 59,
               provider: str = "veo", run_media: bool = False, force: bool = False):
    # 사전조건: brand 채워졌는지
    status = env.brand_status()
    if not all(status.values()):
        missing = [k for k, v in status.items() if not v]
        if not force:
            cprint(f"⚠ Phase 1 미완료 — 비어있는 brand: {missing}", "warn")
            cprint("  완성:  autovideo brand --quick", "warn")
            cprint("  또는 지금 테스트로 강행:  autovideo create \"주제\" --force", "dim")
            return
        cprint(f"⚠ Phase 1 미완료({missing})지만 --force 로 진행합니다.", "warn")
        cprint("  (브랜드 일관성이 약할 수 있음 — 정식 제작 전 Phase 1 완성 권장)", "dim")

    slug_base = env.slugify(topic)
    # 날짜는 외부에서 주입하기 어려우므로 사용자에게 폴더명 확인
    proj_name = ask(f"프로젝트 폴더명 [{slug_base}] ▶ ").strip() or slug_base
    proj_dir = env.PROJECTS_DIR / proj_name
    (proj_dir / "scenes" / "images").mkdir(parents=True, exist_ok=True)
    (proj_dir / "scenes" / "videos").mkdir(parents=True, exist_ok=True)
    (proj_dir / "narration").mkdir(parents=True, exist_ok=True)
    (proj_dir / "anchors").mkdir(parents=True, exist_ok=True)

    clip_len = CLIP_LEN.get(provider, 8)
    calc = video_first_calc(duration_sec, clip_len)

    cprint("\n🎬 Phase 2 — 콘텐츠 제작", "head")
    print(f"주제: {topic}")
    print(f"프로젝트: {proj_dir.relative_to(env.ROOT)}")
    cprint("\n📐 Video-First 계산", "info")
    print(f"  러닝타임 {calc['duration_sec']}초 ÷ 클립 {calc['clip_len']}초 = {calc['scenes']}씬")
    print(f"  총 단어 ≈ {calc['total_words']}  (씬당 ≈ {calc['words_per_scene']})")
    if checkpoint("이 설정으로 진행") != "approve":
        cprint("중단되었습니다.", "warn"); return

    # ① 리서치
    research_path = proj_dir / "research.md"
    _oneshot_step(llm, "researcher", "research", research_path,
                  task_context=f"주제: {topic}\n프로젝트 경로: {proj_dir}\n목표 러닝타임: {duration_sec}초",
                  purpose="research")

    # ② 대본
    script_path = proj_dir / "script.md"
    _oneshot_step(llm, "scriptwriter", "script", script_path,
                  task_context=(
                      f"주제: {topic}\n프로젝트 경로: {proj_dir}\n"
                      f"씬 수: {calc['scenes']}, 총 단어 ~{calc['total_words']}, 씬당 ~{calc['words_per_scene']}\n"
                      f"리서치 결과:\n{_safe_read(research_path)}"
                  ),
                  purpose="script")

    # ③ 씬 연출 (이미지/영상 프롬프트)
    image_prompts_path = proj_dir / "image-prompts.md"
    _oneshot_step(llm, "scene-director", "scene-director", image_prompts_path,
                  task_context=(
                      f"프로젝트 경로: {proj_dir}\n씬 수: {calc['scenes']}\n"
                      f"각 씬의 이미지 생성 프롬프트를 영문으로, 캐릭터 일관성(인종/피부색 명시)을 유지하여 작성.\n"
                      f"대본:\n{_safe_read(script_path)}"
                  ),
                  purpose="scene_direction")

    cprint("\n📝 텍스트 산출물 완료 (research/script/image-prompts).", "ok")

    if not run_media:
        cprint("\nℹ️ 미디어 생성(이미지/음성/합성)은 --media 플래그로 실행합니다.", "info")
        cprint("  예: autovideo create \"주제\" --media", "dim")
        _print_media_commands(proj_dir, provider)
        return

    # ④ 이미지 (기존 스크립트 호출)
    _run_script_step(
        "이미지 생성",
        [sys.executable, str(env.SCRIPTS_DIR / "generate_images.py"),
         "--project", str(proj_dir), "--prompts", "image-prompts.md", "--quality", "medium"],
    )
    # ⑤ 나레이션
    _run_script_step(
        "나레이션 생성",
        [sys.executable, str(env.SCRIPTS_DIR / "produce.py"),
         "--project", str(proj_dir), "--step", "voice", "--format", "short"],
    )
    # ⑥ 합성
    _run_script_step(
        "영상 합성",
        [sys.executable, str(env.SCRIPTS_DIR / "compositor.py"),
         "--project", str(proj_dir), "--format", "portrait"],
    )
    cprint("\n✅ Phase 2 완료!", "ok")


def _oneshot_step(llm: LLM, agent: str, label: str, out_path: Path,
                  task_context: str, purpose: str):
    while True:
        cprint(f"\n▶ {agent} 실행 → {out_path.name}", "info")
        prompt = agent_runner.build_oneshot_prompt(agent, task_context)
        cprint("  LLM 호출 중...", "dim")
        result = llm.generate(prompt, purpose=purpose)
        out_path.write_text(result + "\n", encoding="utf-8")
        hr()
        preview = result[:1200] + ("\n... (생략)" if len(result) > 1200 else "")
        print(preview)
        action = checkpoint(f"{label} 승인")
        if action == "approve":
            cprint(f"💾 저장됨: {out_path.relative_to(env.ROOT)}", "ok")
            return
        if action == "regen":
            continue
        if action == "revise":
            fb = ask("수정 요청 ▶ ").strip()
            task_context += f"\n\n[수정 요청] {fb}"
            continue
        cprint("중단되었습니다.", "warn"); sys.exit(0)


def _run_script_step(label: str, cmd: list[str]):
    hr()
    cprint(f"▶ {label}", "info")
    cprint("  " + " ".join(cmd), "dim")
    if checkpoint(f"{label} 실행") != "approve":
        cprint("  건너뜀", "dim"); return
    try:
        subprocess.run(cmd, check=True, cwd=str(env.ROOT))
        cprint(f"  ✔ {label} 완료", "ok")
    except subprocess.CalledProcessError as e:
        cprint(f"  ✖ {label} 실패 (exit {e.returncode})", "warn")
        cprint("  → 트러블슈팅: ima2 serve / API 키 / ffmpeg 확인", "dim")


def _print_media_commands(proj_dir: Path, provider: str):
    rel = proj_dir.relative_to(env.ROOT)
    print()
    cprint("수동 실행용 명령어:", "info")
    print(f"  python3 scripts/generate_images.py --project {rel} --prompts image-prompts.md --quality medium")
    print(f"  python3 scripts/generate_videos.py --project {rel} --provider {provider}")
    print(f"  python3 scripts/produce.py --project {rel} --step voice --format short")
    print(f"  python3 scripts/compositor.py --project {rel} --format portrait")


def _safe_read(p: Path, limit: int = 4000) -> str:
    if not p.exists():
        return "(없음)"
    t = p.read_text(encoding="utf-8")
    return t[:limit]
