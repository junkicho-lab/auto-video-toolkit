"""에이전트 러너 — agents/*.md 프롬프트를 로드하고 LLM에 연결한다.

각 에이전트 .md는 'Claude Code에게 주는 지시서'다.
CLI에서는 이 지시서를 system instruction으로 LLM에 넘기고,
사용자/이전 산출물을 context로 합쳐 실행한다.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from . import env

# 에이전트 이름 -> 파일 경로
AGENT_PATHS = {
    # phase 1
    "brand-architect": env.AGENTS_DIR / "phase1" / "brand-architect.md",
    "narrative-designer": env.AGENTS_DIR / "phase1" / "narrative-designer.md",
    "topic-strategist": env.AGENTS_DIR / "phase1" / "topic-strategist.md",
    "benchmark-analyst": env.AGENTS_DIR / "phase1" / "benchmark-analyst.md",
    # phase 2
    "researcher": env.AGENTS_DIR / "phase2" / "researcher.md",
    "scriptwriter": env.AGENTS_DIR / "phase2" / "scriptwriter.md",
    "scene-director": env.AGENTS_DIR / "phase2" / "scene-director.md",
    "voice-producer": env.AGENTS_DIR / "phase2" / "voice-producer.md",
    "compositor": env.AGENTS_DIR / "phase2" / "compositor.md",
    "image-generator": env.AGENTS_DIR / "phase2" / "image-generator.md",
    "video-generator": env.AGENTS_DIR / "phase2" / "video-generator.md",
}


def load_agent_prompt(name: str) -> str:
    path = AGENT_PATHS.get(name)
    if not path or not path.exists():
        raise FileNotFoundError(f"에이전트 프롬프트를 찾을 수 없습니다: {name} ({path})")
    return path.read_text(encoding="utf-8")


def read_brand_context() -> str:
    """존재하는 brand/*.yaml을 모아 컨텍스트 문자열로."""
    chunks = []
    for name, p in env.brand_files().items():
        if p.exists() and p.read_text(encoding="utf-8").strip():
            chunks.append(f"### brand/{name}.yaml\n```yaml\n{p.read_text(encoding='utf-8').strip()}\n```")
    return "\n\n".join(chunks) if chunks else "(아직 brand 파일 없음)"


# CLI용 위저드 지시 — 에이전트가 '한 번에 한 질문'을 하고, 끝나면 YAML만 출력하도록
WIZARD_SUFFIX = """

---

## ⚙️ CLI 실행 모드 지침 (반드시 준수)

당신은 지금 터미널 CLI 안에서 사용자와 한국어로 대화합니다.

1. 질문은 **반드시 한 번에 하나씩**만 하세요. 여러 질문을 한꺼번에 묻지 마세요.
2. 충분한 정보를 모았다고 판단되면, 더 묻지 말고 **최종 결과를 아래 형식으로만** 출력하세요:

```
FINAL_YAML
```yaml
<여기에 스키마를 준수한 완성된 YAML>
```
```

3. `FINAL_YAML` 토큰은 결과가 완성되었을 때만 출력합니다. 그 전에는 절대 쓰지 마세요.
4. 모든 대화는 한국어로, 간결하게.
"""

# 단발 생성용 지시 — 한 번에 산출물(문서)을 만들도록
ONESHOT_SUFFIX = """

---

## ⚙️ CLI 실행 모드 지침

당신은 터미널 CLI에서 호출되었습니다. 사용자와의 추가 대화 없이,
주어진 컨텍스트만으로 **요구된 산출물 전체를 한 번에** 작성하세요.
설명/사족 없이 결과물 본문만 출력합니다. (마크다운 문서면 마크다운 본문만)
"""


def build_wizard_system(agent_name: str, extra: str = "") -> str:
    """대화형 에이전트용 system instruction."""
    base = load_agent_prompt(agent_name)
    ctx = read_brand_context()
    return f"{base}\n\n## 참고: 현재 브랜드 컨텍스트\n{ctx}\n{extra}\n{WIZARD_SUFFIX}"


def build_oneshot_prompt(agent_name: str, task_context: str) -> str:
    """단발 생성용 prompt (system+context 합본)."""
    base = load_agent_prompt(agent_name)
    ctx = read_brand_context()
    return (
        f"{base}\n\n## 참고: 현재 브랜드 컨텍스트\n{ctx}\n\n"
        f"## 이번 작업 컨텍스트\n{task_context}\n{ONESHOT_SUFFIX}"
    )


def build_brand_oneshot(agent_name: str, brief: str = "", feedback: str = "") -> str:
    """Phase 1 퀵 모드: 추가 질문 없이 단 1회 호출로 완성 YAML을 생성하는 프롬프트."""
    base = load_agent_prompt(agent_name)
    ctx = read_brand_context()
    brief_txt = brief.strip() if brief and brief.strip() else (
        "(사용자가 설명을 생략함 — 채널 특성을 합리적으로 추천하여 모든 필드를 채울 것)"
    )
    fb = f"\n\n## 사용자 수정 요청\n{feedback}" if feedback.strip() else ""
    return f"""{base}

## 참고: 현재 브랜드 컨텍스트(이전 단계 산출물)
{ctx}

## 사용자의 채널 설명(brief)
{brief_txt}{fb}

---

## ⚙️ CLI 퀵 모드 지침 (반드시 준수)
- **추가 질문을 하지 마세요.** 위 정보만으로 판단해 한 번에 완성합니다.
- 위 스키마를 100% 준수한 **완성된 YAML 하나만** 출력하세요.
- 모든 필드를 의미 있는 값으로 채우고, 빈 문자열("")/빈 배열([])을 남기지 마세요.
- 한국어 채널이면 값은 한국어로 작성하되, 영문 이미지 프롬프트 필드는 영문으로.
- 출력은 오직 ```yaml ... ``` 코드블록 하나. 그 앞뒤로 설명/사족을 쓰지 마세요.
"""


FINAL_RE = re.compile(r"FINAL_YAML", re.IGNORECASE)
YAML_BLOCK_RE = re.compile(r"```ya?ml\s*\n(.*?)```", re.DOTALL | re.IGNORECASE)


def extract_final_yaml(text: str) -> Optional[str]:
    """모델 응답에서 FINAL_YAML 이후의 yaml 블록을 추출한다."""
    if not FINAL_RE.search(text):
        return None
    m = YAML_BLOCK_RE.search(text)
    return m.group(1).strip() if m else None


def extract_any_yaml(text: str) -> Optional[str]:
    m = YAML_BLOCK_RE.search(text)
    return m.group(1).strip() if m else None
