# CLAUDE.md

Claude Code로 이 패키지를 다룰 때의 작업 가이드입니다. 처음이라면 먼저 `README.md`를 읽으세요.

## Project Overview

AI 영상 콘텐츠 자동 제작 파이프라인. 에이전트 팀이 브랜드 세팅(Phase 1) → 콘텐츠 제작(Phase 2)을 오케스트레이션합니다.

## 진입점

- `/auto-video` — 자동 Phase 판단 (brand/ 상태 확인)
- `/auto-video brand` — Phase 1 강제 실행
- `/auto-video create "주제"` — Phase 2 강제 실행
- `/create-c` — 채널·주제·러닝타임·도구·보이스를 질문하며 진행

## 주요 명령

```bash
# 이미지 생성 (GPT Image 2 / ima2) — 사전: 다른 터미널에서 `ima2 serve`
python3 scripts/generate_images.py --project projects/{slug} --quality high

# 영상 생성 (provider: veo|grok|kling|higgsfield) / 나레이션 (ElevenLabs)
python3 scripts/generate_videos.py --project projects/{slug} --provider veo
python3 scripts/produce.py --project projects/{slug} --step voice --voice-id {id}

# 영상 합성 (MoviePy)
python3 scripts/compositor.py --project projects/{slug} --format landscape

# CapCut 프로젝트 자동 생성 (이 패키지의 scripts/ 안에 포함되어 있음)
python3 scripts/capcut-project-gen.py config.json

# 설치 / 테스트
pip install -e ".[dev]" && pytest
```

## Architecture

### 2-Phase 파이프라인

**Phase 1 (브랜드 세팅, 채널당 1회)** — `brand-architect → narrative-designer → topic-strategist → benchmark-analyst` → `brand/`에 4개 YAML(character, narrative, topics, benchmark) 출력. 구조 예시는 `brand-example/` 참고.

**Phase 2 (콘텐츠 제작, 에피소드당 1회)** — `researcher → scriptwriter → scene-director → [image-generator + video-generator 병렬] → voice-producer → compositor` → `projects/{slug}/`에 script.md, 이미지, 영상, 나레이션, SRT 출력.

Director(`agents/director.md`)가 Phase 판단 + 에이전트 배정 + 체크포인트를 관리합니다.

### 핵심 스크립트

| 스크립트 | 역할 |
| --- | --- |
| `generate_images.py` | 씬별 이미지 생성 — **GPT Image 2** (로컬 `ima2` CLI) |
| `generate_videos.py` | 영상 생성 — **veo / grok / kling / higgsfield** provider 선택 |
| `gemini_client.py` | Gemini API 래퍼 (리서치/대본; 모델 매핑은 `config/models.yaml`) |
| `produce.py` | ElevenLabs TTS(나레이션) + 합성 보조 |
| `compositor.py` | MoviePy 합성 (Ken Burns 포함) |
| `capcut-project-gen.py` | CapCut 프로젝트(draft_info.json) 자동 생성 |

## Key Constraints

### 길이 제한
- 숏폼: 59초 이내 (hard limit)
- 롱폼: 3~5분 (5분 초과 금지)
- 대본 길이 사전 계산: 영어 150 WPM 기준

### 제작 플로우 (Video-First)
대본이 아니라 **영상 러닝타임을 먼저** 정하고 역산합니다.
```
1. 러닝타임 설정 (예: 3분 30초)
2. 영상 도구 선택 → 클립 길이 결정 (Kling=10초, Veo3=8초 등)
3. 씬 수 = 러닝타임 ÷ 클립 길이
4. 총 단어 수 = 러닝타임(초) ÷ 60 × 150
5. 씬당 단어 수 = 총 단어 수 ÷ 씬 수
6. 앵커 → 이미지 → 영상 → 대본(씬 단위) → TTS(씬 단위) → CapCut 합성
```

### 이미지/영상 생성
- 캐릭터 앵커 이미지를 먼저 생성 (실존 인물이면 시대별 분리)
- **인종/피부색을 모든 프롬프트에 명시** — 누락 시 씬마다 다른 인종이 생성됨
- Kling 프롬프트 가이드: `docs/kling-prompt-guide.md`

### SRT 자막 규칙
- **플레인 텍스트만** — 번호·좌표·스타일 태그 등 메타데이터 금지
- **자막 1개당 1줄** — 2줄 이상 금지, 길면 별도 엔트리로 분할

### CapCut 통합
- macOS CapCut은 샌드박스 → 미디어를 프로젝트 `Resources/`에 복사 필요
- `capcut-project-gen.py` 사용 (draft_info.json 수동 생성 금지)
- 시간 단위: 마이크로초 (1초 = 1,000,000)
- 상세: `guides/CAPCUT_GUIDE.md`

## Environment

- Python 3.10+, Node.js 20+(ima2), ffmpeg(`brew install ffmpeg`)
- 이미지(ima2): `npm install -g ima2-gen` → `npx @openai/codex login` → `ima2 serve`
- API 키: `config/api-keys.env` — `config/api-keys.env.example` 복사 후 사용하는 provider 키만 작성
  - 영상: veo→`GEMINI_API_KEY` / grok→`XAI_API_KEY` / kling→`KLING_ACCESS_KEY`+`KLING_SECRET_KEY` / higgsfield→`SEGMIND_API_KEY`
  - 나레이션: `ELEVENLABS_API_KEY`
