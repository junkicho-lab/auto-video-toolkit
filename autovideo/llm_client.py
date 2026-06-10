"""LLM 클라이언트 — provider 추상화 (Gemini + Claude).

provider는 --llm > AUTOVIDEO_LLM 환경변수 > 'gemini' 순으로 결정.
google-genai / anthropic 은 실제 호출 시점에만 import한다(미설치 환경에서도 CLI 로드 가능).
"""
from __future__ import annotations

import os
import sys
import time
from typing import Callable, Optional

from . import env

# provider별 기본 모델 (──model 또는 AUTOVIDEO_MODEL로 덮어쓰기)
DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"
DEFAULT_CLAUDE_MODEL = "claude-opus-4-8"  # Anthropic 최신 Opus (claude-api 레퍼런스 기준)

# 서버 혼잡 등 '잠깐 기다리면 풀리는' 오류 → 지수 백오프 재시도
_TRANSIENT_MARKERS = (
    "503", "500", "529", "UNAVAILABLE", "overloaded", "high demand",
    "DEADLINE", "temporarily",
)
# 할당량/요청수 초과 → 짧은 재시도로는 안 풀림 → 빠르게 실패 + 안내
_QUOTA_MARKERS = ("429", "RESOURCE_EXHAUSTED", "rate_limit", "quota")


class LLMError(RuntimeError):
    pass


def _is_transient(err: Exception) -> bool:
    s = str(err)
    return any(m in s for m in _TRANSIENT_MARKERS)


def _is_quota(err: Exception) -> bool:
    s = str(err)
    return any(m in s for m in _QUOTA_MARKERS)


def _error_hint(err: Exception) -> str:
    s = str(err)
    if "NOT_FOUND" in s or "404" in s:
        return ("\n  → 모델명이 잘못되었습니다. 사용 가능 모델 확인: autovideo models\n"
                "    또는: --model <모델명> 으로 지정")
    if _is_quota(err):
        return (
            "\n  ──────────────────────────────────────────────\n"
            "  ⚠ 할당량(요청 수)을 초과했습니다. 진행 상황은 저장되어 있어\n"
            "  해결 후 다시 실행하면 완료된 단계는 건너뜁니다.\n"
            "  해결: 잠시 대기 / 다른 모델(--model) / 결제 등급 상향 /\n"
            "        다른 provider(--llm gemini|claude)\n"
            "  ──────────────────────────────────────────────"
        )
    if _is_transient(err):
        return "\n  → 서버 일시 혼잡입니다. 잠시 후 다시 시도하세요."
    return ""


def _retry(fn: Callable, attempts: int = 4, base: float = 2.0):
    """일시적 서버 오류면 지수 백오프 재시도. 할당량/기타 오류는 즉시 raise."""
    last = None
    for i in range(attempts):
        try:
            return fn()
        except Exception as e:  # noqa: BLE001
            if _is_quota(e) or not _is_transient(e):
                raise
            last = e
            if i < attempts - 1:
                wait = base * (2 ** i)
                sys.stderr.write(
                    f"  ⏳ 서버 혼잡(일시적). {int(wait)}초 후 재시도... "
                    f"({i + 1}/{attempts - 1})\n"
                )
                sys.stderr.flush()
                time.sleep(wait)
    raise last


def resolve_provider(explicit: Optional[str]) -> str:
    return (explicit or os.environ.get("AUTOVIDEO_LLM") or "gemini").lower()


class LLM:
    """Gemini/Claude 텍스트 생성·대화 통합 래퍼."""

    def __init__(self, provider: Optional[str] = None, model_override: Optional[str] = None):
        env.load_api_keys()
        self.provider = resolve_provider(provider)
        self._model_override = model_override or os.environ.get("AUTOVIDEO_MODEL")
        self._models = env.load_models_config().get("models", {})
        self._client = None  # lazy

        if self.provider == "gemini":
            self._api_key = env.get_key("GEMINI_API_KEY")
        elif self.provider == "claude":
            self._api_key = env.get_key("ANTHROPIC_API_KEY")
        else:
            raise LLMError(f"알 수 없는 provider: {self.provider} (gemini|claude)")

    # ---- 모델 선택 ----
    def model_for(self, purpose: str) -> str:
        if self._model_override:
            return self._model_override
        if self.provider == "claude":
            return DEFAULT_CLAUDE_MODEL
        return self._models.get(purpose) or DEFAULT_GEMINI_MODEL

    # ---- 클라이언트 (lazy) ----
    def _ensure_gemini(self):
        if self._client is not None:
            return self._client
        if not self._api_key:
            raise LLMError(
                "GEMINI_API_KEY가 설정되지 않았습니다.\n"
                "  config/api-keys.env 에 키를 채우세요. (발급: https://aistudio.google.com)"
            )
        try:
            from google import genai  # noqa
        except ImportError as e:
            raise LLMError("google-genai 미설치 — pip install -e \".[dev]\"") from e
        from google import genai
        self._client = genai.Client(api_key=self._api_key)
        return self._client

    def _ensure_claude(self):
        if self._client is not None:
            return self._client
        if not self._api_key:
            raise LLMError(
                "ANTHROPIC_API_KEY가 설정되지 않았습니다.\n"
                "  config/api-keys.env 에 ANTHROPIC_API_KEY=... 를 추가하세요.\n"
                "  발급: https://console.anthropic.com"
            )
        try:
            import anthropic  # noqa
        except ImportError as e:
            raise LLMError("anthropic 미설치 — pip install anthropic (또는 pip install -e \".[dev]\")") from e
        import anthropic
        self._client = anthropic.Anthropic(api_key=self._api_key)
        return self._client

    # ---- 단발 생성 ----
    def generate(self, prompt: str, purpose: str = "script") -> str:
        if self.provider == "claude":
            return self._generate_claude(prompt, purpose)
        return self._generate_gemini(prompt, purpose)

    def _generate_gemini(self, prompt: str, purpose: str) -> str:
        client = self._ensure_gemini()
        model = self.model_for(purpose)
        try:
            resp = _retry(lambda: client.models.generate_content(model=model, contents=prompt))
        except Exception as e:  # noqa: BLE001
            raise LLMError(f"LLM 호출 실패 (model={model}): {e}{_error_hint(e)}") from e
        return (resp.text or "").strip()

    def _generate_claude(self, prompt: str, purpose: str) -> str:
        client = self._ensure_claude()
        model = self.model_for(purpose)
        try:
            resp = _retry(lambda: client.messages.create(
                model=model, max_tokens=8000,
                messages=[{"role": "user", "content": prompt}],
            ))
        except Exception as e:  # noqa: BLE001
            raise LLMError(f"LLM 호출 실패 (model={model}): {e}{_error_hint(e)}") from e
        return "".join(b.text for b in resp.content if b.type == "text").strip()

    # ---- 사용 가능한 모델 목록 ----
    def list_models(self) -> list[str]:
        if self.provider == "claude":
            client = self._ensure_claude()
            try:
                return sorted(m.id for m in client.models.list())
            except Exception as e:  # noqa: BLE001
                raise LLMError(f"모델 목록 조회 실패: {e}") from e
        # gemini
        client = self._ensure_gemini()
        names = []
        try:
            for m in client.models.list():
                actions = getattr(m, "supported_actions", None) or getattr(
                    m, "supported_generation_methods", None) or []
                if not actions or "generateContent" in actions:
                    names.append((getattr(m, "name", "") or "").replace("models/", ""))
        except Exception as e:  # noqa: BLE001
            raise LLMError(f"모델 목록 조회 실패: {e}") from e
        return sorted(set(n for n in names if n))

    # ---- 멀티턴 대화 세션 ----
    def chat(self, purpose: str = "script", system: Optional[str] = None):
        if self.provider == "claude":
            client = self._ensure_claude()
            return ClaudeChatSession(client, self.model_for(purpose), system)
        # gemini
        client = self._ensure_gemini()
        model = self.model_for(purpose)
        kwargs = {}
        if system:
            try:
                from google.genai import types
                kwargs["config"] = types.GenerateContentConfig(system_instruction=system)
            except Exception:  # noqa: BLE001
                kwargs = {}
        try:
            session = client.chats.create(model=model, **kwargs)
        except Exception as e:  # noqa: BLE001
            raise LLMError(f"대화 세션 생성 실패 (model={model}): {e}") from e
        return GeminiChatSession(session, prepend_system=None if kwargs else system)


class GeminiChatSession:
    """google-genai chat 세션 래퍼 (멀티턴)."""

    def __init__(self, session, prepend_system: Optional[str] = None):
        self._session = session
        self._prepend = prepend_system
        self._first = True

    def send(self, message: str) -> str:
        if self._first and self._prepend:
            message = f"{self._prepend}\n\n---\n\n{message}"
        self._first = False
        try:
            resp = _retry(lambda: self._session.send_message(message))
        except Exception as e:  # noqa: BLE001
            raise LLMError(f"대화 메시지 전송 실패: {e}{_error_hint(e)}") from e
        return (resp.text or "").strip()


class ClaudeChatSession:
    """Anthropic messages API 기반 멀티턴 세션 (stateless → history 직접 보관)."""

    def __init__(self, client, model: str, system: Optional[str] = None):
        self._client = client
        self._model = model
        self._system = system
        self._messages: list[dict] = []

    def send(self, message: str) -> str:
        self._messages.append({"role": "user", "content": message})
        kwargs = dict(model=self._model, max_tokens=8000, messages=self._messages)
        if self._system:
            kwargs["system"] = self._system
        try:
            resp = _retry(lambda: self._client.messages.create(**kwargs))
        except Exception as e:  # noqa: BLE001
            raise LLMError(f"대화 메시지 전송 실패: {e}{_error_hint(e)}") from e
        text = "".join(b.text for b in resp.content if b.type == "text").strip()
        self._messages.append({"role": "assistant", "content": text})
        return text
