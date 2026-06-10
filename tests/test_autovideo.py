"""autovideo 두뇌 로직 스모크 테스트 (API 불필요)."""
from autovideo.orchestrator import video_first_calc
from autovideo.env import slugify, _yaml_has_values
from autovideo.agent_runner import extract_final_yaml, extract_any_yaml


def test_video_first_calc_short():
    c = video_first_calc(59, 8)
    assert c["scenes"] == 7
    assert c["total_words"] == 148
    assert c["words_per_scene"] == 21


def test_video_first_calc_long():
    c = video_first_calc(210, 10)
    assert c == {
        "duration_sec": 210, "clip_len": 10,
        "scenes": 21, "total_words": 525, "words_per_scene": 25,
    }


def test_slugify():
    assert slugify("Why AI Lies 2026") == "why-ai-lies-2026"
    # 한글만 있으면 fallback
    assert slugify("거짓말") == "untitled"


def test_yaml_has_values():
    empty = 'persona:\n  name: ""\n  personality: []\n'
    filled = 'persona:\n  name: "애덕이"\n  personality: []\n'
    assert _yaml_has_values(empty) is False
    assert _yaml_has_values(filled) is True


def test_extract_final_yaml():
    text = "여기까지 대화\nFINAL_YAML\n```yaml\npersona:\n  name: \"덕\"\n```\n"
    out = extract_final_yaml(text)
    assert out is not None and 'name: "덕"' in out
    # FINAL_YAML 없으면 None
    assert extract_final_yaml("```yaml\na: 1\n```") is None
    # extract_any_yaml은 토큰 없이도 추출
    assert extract_any_yaml("```yaml\na: 1\n```").strip() == "a: 1"
