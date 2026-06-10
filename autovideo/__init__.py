"""autovideo — Claude Code 없이 독립 실행되는 AI 영상 제작 CLI.

기존 toolkit의 두뇌(오케스트레이터)를 코드로 구현한 패키지.
- agents/*.md 프롬프트를 직접 읽어 LLM API에 전달
- scripts/*.py(이미지/영상/음성/합성)를 재사용
- Phase 1(브랜드) / Phase 2(콘텐츠)를 단계별 체크포인트로 진행
"""

__version__ = "0.1.0"
