# AGENTS.md

AI 에이전트 팀으로 영상 콘텐츠를 자동 제작하는 워크플로우 패키지입니다.
이 파일은 **Claude Code · Codex · Antigravity · Cursor 등 모든 에이전트 도구가 공통으로 읽는 진입 규약**입니다.
처음이라면 `README.md`(설치·키)를 먼저 보세요.

> 플랫폼 우선순위: Claude Code는 `CLAUDE.md`, Antigravity는 `GEMINI.md`(있을 경우) → `AGENTS.md`, Codex/Cursor는 `AGENTS.md`. 세 도구 모두 이 파일로 동작합니다.

## 무엇을 하는가

리서치 → 대본 → 씬 이미지(GPT Image 2) → 영상 클립(선택형 API) → 나레이션(ElevenLabs) → 자막 → CapCut 합성까지 하나의 파이프라인으로 잇습니다.

- **이미지 생성**: GPT Image 2 — 로컬 `ima2` CLI/서버 (`vendor/ima2-gen`)
- **영상 생성**: Gemini(Veo) / Grok / Kling / Higgsfield 중 `config/models.yaml`에서 선택
- **나레이션**: ElevenLabs
- **합성**: MoviePy + CapCut (`scripts/capcut-project-gen.py`)

## 플랫폼별 시작법

### Claude Code
```
/auto-video               # 자동 Phase 판단
/auto-video brand         # Phase 1 (브랜드 세팅)
/auto-video create "주제"  # Phase 2 (콘텐츠 제작)
/create-c                 # 인터뷰형 진입점
```
스킬 정의: `skills/auto-video/SKILL.md`, 커맨드: `commands/create-c.md`

### Codex
```bash
codex            # 이 폴더에서 실행 → AGENTS.md 자동 로드
```
그다음 에이전트에게 "Phase 1 브랜드 세팅 시작" 또는 "Phase 2로 '주제' 제작"이라고 지시하면,
`agents/director.md`의 Phase 판단 로직을 따라 `agents/phase1`·`agents/phase2`의 에이전트 프롬프트를 순서대로 실행합니다.
개별 단계는 `scripts/`의 파이썬 스크립트를 직접 호출해도 됩니다(아래 명령 참고).

### Antigravity
워크스페이스로 이 폴더를 열면 AGENTS.md가 세션 시작 시 자동 로드됩니다.
Agent Manager에서 "Phase 1 시작" / "Phase 2로 '주제' 제작"을 지시하면 `agents/director.md` 기준으로 진행합니다.
(Antigravity 전용 오버라이드가 필요하면 `GEMINI.md`를 추가하세요. 기본은 이 파일로 충분합니다.)

## 워크플로우 (공통)

**Phase 1 (브랜드 세팅 · 채널당 1회)**
`brand-architect → narrative-designer → topic-strategist → benchmark-analyst`
→ `brand/`에 4개 YAML(character, narrative, topics, benchmark). 구조 예시는 `brand-example/`.

**Phase 2 (콘텐츠 제작 · 에피소드당 1회)**
`researcher → scriptwriter → scene-director → [image-generator + video-generator 병렬] → voice-producer → compositor`
→ `projects/{slug}/`에 대본·이미지·영상·나레이션·자막.

제작은 **Video-First** — 영상 러닝타임을 먼저 정하고 씬 수·단어 수를 역산합니다.
Director(`agents/director.md`)가 Phase 판단·에이전트 배정·체크포인트를 관리합니다.

## 스크립트 명령

```bash
# 이미지 (GPT Image 2 / ima2) — 사전: 다른 터미널에서 `ima2 serve`
python3 scripts/generate_images.py --project projects/{slug} --quality high --anchor anchors/character.png

# 영상 (provider는 config/models.yaml의 video_generation 값)
python3 scripts/generate_videos.py --project projects/{slug}

# 나레이션 (ElevenLabs)
python3 scripts/produce.py --project projects/{slug} --step voice --voice-id {id}

# 합성
python3 scripts/compositor.py --project projects/{slug} --format landscape
python3 scripts/capcut-project-gen.py config.json
```

## 환경 / 사전조건

- **macOS**, **Python 3.10+**, **Node.js 20+**(ima2용), **ffmpeg**(`brew install ffmpeg`)
- 이미지(ima2): `npm install -g ima2-gen` 또는 `vendor/ima2-gen`에서 `npm install` → `ima2 serve`
  - 인증: `npx @openai/codex login`(OAuth) 또는 `OPENAI_API_KEY`
- API 키: `config/api-keys.env`(= `config/api-keys.env.example` 복사) — 사용하는 provider의 키만 채우면 됩니다.

## 핵심 제약

- 숏폼 59초 이내 / 롱폼 3~5분
- 이미지 프롬프트에 인종·피부색 명시(씬마다 인물 달라짐 방지)
- SRT 자막: 플레인 텍스트, 1엔트리 1줄
- CapCut 합성은 macOS 기준(샌드박스 → `Resources/` 복사, `capcut-project-gen.py`가 자동 처리)
