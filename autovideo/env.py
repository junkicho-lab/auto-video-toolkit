"""환경/설정 로딩 유틸 — API 키, 경로, 프로젝트 상태.

외부 의존성 없이 동작한다(pyyaml 제외). google-genai는 여기서 import하지 않는다.
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Optional

# 프로젝트 루트 = 이 파일의 부모의 부모 (autovideo/env.py -> repo root)
ROOT = Path(__file__).resolve().parent.parent

CONFIG_DIR = ROOT / "config"
AGENTS_DIR = ROOT / "agents"
SCRIPTS_DIR = ROOT / "scripts"
BRAND_DIR = ROOT / "brand"
PROJECTS_DIR = ROOT / "projects"
API_KEYS_FILE = CONFIG_DIR / "api-keys.env"
MODELS_FILE = CONFIG_DIR / "models.yaml"

# 키 값이 이 접두어로 시작하면 "아직 미설정(예시값)"으로 간주
PLACEHOLDER_PREFIXES = ("your-", "your_", "<", "...")


def load_api_keys(env_file: Path = API_KEYS_FILE) -> dict[str, str]:
    """config/api-keys.env를 파싱해 dict로 반환하고 os.environ에도 주입한다.

    - `KEY=value   # inline comment` 형식의 인라인 주석 제거
    - 예시값(your-...)은 미설정으로 취급해 제외
    """
    result: dict[str, str] = {}
    if not env_file.exists():
        return result
    for raw in env_file.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, rest = line.partition("=")
        key = key.strip()
        # 인라인 주석 제거 ( 값 뒤에 ' #' 또는 '\t#' 가 오면 잘라냄 )
        value = re.split(r"\s+#", rest, maxsplit=1)[0].strip().strip('"').strip("'")
        if not value or value.lower().startswith(PLACEHOLDER_PREFIXES):
            continue
        result[key] = value
        os.environ.setdefault(key, value)
    return result


def get_key(name: str) -> Optional[str]:
    """환경변수 또는 api-keys.env에서 키를 찾는다."""
    if os.environ.get(name):
        return os.environ[name]
    return load_api_keys().get(name)


def load_models_config(path: Path = MODELS_FILE) -> dict:
    try:
        import yaml  # pyyaml은 기존 의존성
    except ImportError:
        # pyyaml 미설치 시에도 CLI가 죽지 않도록 (기본 모델로 fallback)
        return {}
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def brand_files() -> dict[str, Path]:
    """Phase 1 산출물 4종 경로."""
    return {
        "character": BRAND_DIR / "character.yaml",
        "narrative": BRAND_DIR / "narrative.yaml",
        "topics": BRAND_DIR / "topics.yaml",
        "benchmark": BRAND_DIR / "benchmark.yaml",
    }


def brand_status() -> dict[str, bool]:
    """각 brand YAML이 '채워졌는지' 여부. (파일 존재 + 비어있지 않음)"""
    status = {}
    for name, p in brand_files().items():
        filled = False
        if p.exists():
            text = p.read_text(encoding="utf-8")
            # 빈 필드만 있는지 대략 판단: 값이 있는 라인이 하나라도 있으면 채워진 것으로
            filled = _yaml_has_values(text)
        status[name] = filled
    return status


def _yaml_has_values(text: str) -> bool:
    """key: "" / key: [] 같은 빈 값만 있으면 False, 실제 값이 있으면 True."""
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if ":" in line:
            _, _, val = line.partition(":")
            val = val.strip()
            if val and val not in ('""', "''", "[]", "{}", "[ ]"):
                return True
        elif line.startswith("- ") and line[2:].strip():
            return True
    return False


def slugify(text: str) -> str:
    """주제를 영문 소문자 kebab-case slug로 (한글은 음절 제거되므로 fallback 포함)."""
    import unicodedata

    ascii_text = (
        unicodedata.normalize("NFKD", text)
        .encode("ascii", "ignore")
        .decode("ascii")
    )
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_text).strip("-").lower()
    return slug or "untitled"
