"""YouTube 메타데이터 생성 스크립트.

대본 + 브랜드 가이드 → Gemini API로 YouTube 제목/설명/태그 생성 → metadata.yaml 저장.
"""

import argparse
from pathlib import Path

import yaml


def validate_metadata(metadata: dict) -> bool:
    """메타데이터 필수 필드를 검증한다.

    Args:
        metadata: {"title": str, "description": str, "tags": list}

    Returns:
        유효하면 True
    """
    title = metadata.get("title", "")
    if not title or len(title) > 100:
        return False

    if "description" not in metadata:
        return False

    description = metadata.get("description", "")
    if not description:
        return False

    return True


def format_metadata_yaml(metadata: dict) -> str:
    """메타데이터를 YAML 문자열로 변환한다."""
    return yaml.dump(metadata, allow_unicode=True, default_flow_style=False)


async def generate_metadata(
    script_path: str,
    brand_dir: str,
    output_path: str,
) -> dict:
    """Gemini API로 YouTube 메타데이터를 생성한다.

    Args:
        script_path: script.md 경로
        brand_dir: brand/ 디렉토리 경로
        output_path: 출력 metadata.yaml 경로

    Returns:
        생성된 메타데이터 dict
    """
    from scripts.gemini_client import GeminiClient

    # 대본 로드
    script_text = Path(script_path).read_text(encoding="utf-8")

    # 브랜드 가이드 로드
    brand_path = Path(brand_dir)
    character = yaml.safe_load((brand_path / "character.yaml").read_text(encoding="utf-8"))
    topics = yaml.safe_load((brand_path / "topics.yaml").read_text(encoding="utf-8"))
    benchmark = yaml.safe_load((brand_path / "benchmark.yaml").read_text(encoding="utf-8"))

    # 프롬프트 구성
    prompt = f"""다음 영상 대본과 채널 정보를 기반으로 YouTube 메타데이터를 생성해주세요.

## 채널 정보
- 캐릭터: {character.get('persona', {}).get('name', '미정')}
- 주제 카테고리: {topics.get('main_category', '미정')}
- 벤치마킹 체크리스트 (제목): {benchmark.get('checklist', {}).get('title', [])}

## 대본
{script_text[:3000]}

## 요청사항
다음 형식으로 정확히 응답해주세요 (YAML):

title: "매력적인 YouTube 제목 (70자 이내)"
description: "영상 설명 (500자 이내, 타임스탬프 포함)"
tags:
  - "관련 태그1"
  - "관련 태그2"
  - "관련 태그3"
"""

    client = GeminiClient(require_key=True)
    response = await client.generate_text("metadata", prompt)

    # YAML 파싱
    metadata = yaml.safe_load(response)
    if not validate_metadata(metadata):
        raise ValueError(f"생성된 메타데이터가 유효하지 않습니다: {metadata}")

    # 저장
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(format_metadata_yaml(metadata), encoding="utf-8")

    return metadata


def main():
    parser = argparse.ArgumentParser(description="YouTube 메타데이터 생성")
    parser.add_argument("--script", required=True, help="script.md 경로")
    parser.add_argument("--brand", default="brand/", help="brand 디렉토리 경로")
    parser.add_argument("--output", required=True, help="출력 metadata.yaml 경로")
    args = parser.parse_args()

    import asyncio

    asyncio.run(generate_metadata(args.script, args.brand, args.output))
    print(f"메타데이터 생성 완료: {args.output}")


if __name__ == "__main__":
    main()
