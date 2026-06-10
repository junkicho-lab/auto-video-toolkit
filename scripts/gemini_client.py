"""Gemini API 공통 클라이언트.

config/models.yaml에서 모델 매핑을 로드하고,
텍스트/이미지 생성 기능을 제공한다.
"""

import os
from pathlib import Path
from typing import Optional

import yaml


class GeminiClient:
    """Gemini API 클라이언트. 모델 매핑 + API 호출을 통합 관리."""

    def __init__(
        self,
        config_path: str = "config/models.yaml",
        require_key: bool = False,
    ):
        self._config = self._load_config(config_path)
        self._models = self._config.get("models", {})
        self.api_config = self._config.get("api", {})
        self._api_key: Optional[str] = os.environ.get("GEMINI_API_KEY")

        if require_key and not self._api_key:
            raise ValueError(
                "GEMINI_API_KEY 환경변수가 설정되지 않았습니다. "
                "config/api-keys.env.example을 참조하세요."
            )

    @staticmethod
    def _load_config(config_path: str) -> dict:
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"설정 파일을 찾을 수 없습니다: {config_path}")
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f)

    def get_model(self, purpose: str) -> str:
        """용도별 모델 이름을 반환한다.

        Args:
            purpose: 모델 용도 (research, script, scene_direction, ...)

        Returns:
            모델 이름 문자열

        Raises:
            KeyError: 알 수 없는 용도
        """
        if purpose not in self._models:
            raise KeyError(f"알 수 없는 모델 용도: {purpose}. 가능한 값: {list(self._models.keys())}")
        return self._models[purpose]

    async def generate_text(self, purpose: str, prompt: str) -> str:
        """Gemini API로 텍스트를 생성한다.

        Args:
            purpose: 모델 용도 (research, script, metadata 등)
            prompt: 생성 프롬프트

        Returns:
            생성된 텍스트
        """
        from google import genai

        model_name = self.get_model(purpose)
        client = genai.Client(api_key=self._api_key)
        response = await client.aio.models.generate_content(
            model=model_name,
            contents=prompt,
        )
        return response.text

    async def generate_image(self, prompt: str, output_path: str) -> str:
        """Gemini API로 이미지를 생성한다.

        Args:
            prompt: 이미지 생성 프롬프트
            output_path: 저장할 파일 경로

        Returns:
            저장된 파일 경로
        """
        from google import genai

        client = genai.Client(api_key=self._api_key)
        response = await client.aio.models.generate_content(
            model=self.get_model("image_generation"),
            contents=prompt,
        )

        # 이미지 바이트 추출 및 저장
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)

        for part in response.candidates[0].content.parts:
            if part.inline_data:
                out.write_bytes(part.inline_data.data)
                return str(out)

        raise RuntimeError("API 응답에 이미지 데이터가 없습니다.")
