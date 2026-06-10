# Auto-Video Toolkit

AI 에이전트 팀으로 영상 콘텐츠를 자동 제작하는 워크플로우 패키지입니다.
브랜드 세팅(Phase 1) → 콘텐츠 제작(Phase 2)을 에이전트들이 단계별로 진행합니다.

리서치 → 대본 → 씬 이미지(**GPT Image 2**) → 영상 클립(**Veo / Grok / Kling / Higgsfield 중 선택**) → 나레이션(ElevenLabs) → 자막 → CapCut 합성까지 하나의 파이프라인으로 이어집니다.

> **멀티 플랫폼**: Claude Code · Codex · Antigravity · Cursor에서 동작합니다.
> 공용 진입 규약은 `AGENTS.md`, Claude Code는 `CLAUDE.md`를 추가로 읽습니다. 플랫폼별 시작법은 `AGENTS.md` 참고.

---

## 1. 무엇이 필요한가

| 항목 | 필수 | 비고 |
|---|---|---|
| **macOS** | ✅ | ima2(GPT Image 2)·CapCut 합성이 macOS 기준 |
| **Python 3.10+** | ✅ | `python3 --version` |
| **Node.js 20+** | ✅ | 이미지 생성 엔진 ima2 구동용 |
| **ffmpeg (ffprobe)** | ✅ | `brew install ffmpeg` |
| **에이전트 도구** | ✅ | Claude Code / Codex / Antigravity 중 하나 |
| **CapCut 데스크톱 앱** | 합성 시 | 무료(macOS) |

### 필요한 키 (사용하는 것만)

- **이미지 (GPT Image 2)**: OpenAI 계정 — `npx @openai/codex login`(OAuth, 키 불필요) 또는 `OPENAI_API_KEY`
- **영상 (provider 1개 선택)**:
  - `veo` → Gemini API 키 · `grok` → xAI 키 · `kling` → Kling Access/Secret 키 · `higgsfield` → Segmind 키
- **나레이션**: ElevenLabs 키
- **리서치/대본**: Gemini API 키

> 키는 본인 계정에서 발급하며 사용량에 따라 각 서비스에 과금됩니다.

---

## 2. 설치

```bash
cd auto-video-toolkit

# 파이썬 의존성 (가상환경 권장)
python3 -m venv .venv && source .venv/bin/activate
pip install -e .

# ffmpeg
brew install ffmpeg

# 이미지 생성 엔진 ima2 (GPT Image 2) — 동봉본 또는 전역 설치
npm install -g ima2-gen           # 또는: cd vendor/ima2-gen && npm install && npm link
npx @openai/codex login           # OpenAI(Codex) OAuth 로그인
ima2 serve &                      # 로컬 이미지 서버 기동(별도 터미널 권장)
ima2 ping                         # 동작 확인
```

## 3. API 키 설정

```bash
cp config/api-keys.env.example config/api-keys.env
# 사용할 provider의 키만 채우면 됩니다. (config/api-keys.env 는 .gitignore에 포함)
```

영상 provider는 `config/models.yaml`의 `video_generation` 값으로 선택합니다(`veo`/`grok`/`kling`/`higgsfield`).

---

## 4. 사용법 (플랫폼별)

### Claude Code
```
/auto-video               # 자동 Phase 판단
/auto-video brand         # Phase 1 (브랜드 세팅)
/auto-video create "주제"  # Phase 2 (콘텐츠 제작)
/create-c                 # 인터뷰형 진입점
```

### Codex / Antigravity / Cursor
폴더를 열면 `AGENTS.md`가 세션 시작 시 자동 로드됩니다.
에이전트에게 **"Phase 1 브랜드 세팅 시작"** 또는 **"Phase 2로 '주제' 제작"**이라고 지시하면 `agents/director.md` 기준으로 진행합니다. 개별 단계는 아래 스크립트를 직접 호출해도 됩니다.

---

## 5. 워크플로우 개요

**Phase 1 (브랜드 세팅 · 채널당 1회)**
`brand-architect → narrative-designer → topic-strategist → benchmark-analyst`
→ `brand/`에 4개 YAML. 구조 예시는 `brand-example/`.

**Phase 2 (콘텐츠 제작 · 에피소드당 1회)**
`researcher → scriptwriter → scene-director → [image-generator + video-generator 병렬] → voice-producer → compositor`
→ `projects/{slug}/`에 대본·이미지·영상·나레이션·자막.

제작은 **Video-First** — 영상 러닝타임을 먼저 정하고 씬 수·단어 수를 역산합니다.

---

## 6. 개별 스크립트 직접 실행

```bash
# 이미지 (GPT Image 2 / ima2) — 사전: 다른 터미널에서 `ima2 serve`
python3 scripts/generate_images.py --project projects/{slug} \
  --quality high --anchor anchors/character.png

# 영상 (provider는 --provider 또는 config/models.yaml)
python3 scripts/generate_videos.py --project projects/{slug} --provider veo

# 나레이션 (ElevenLabs)
python3 scripts/produce.py --project projects/{slug} --step voice --voice-id {id}

# 합성
python3 scripts/compositor.py --project projects/{slug} --format landscape
python3 scripts/capcut-project-gen.py config.json
```

---

## 7. 영상 provider

`config/models.yaml`의 `video_generation` 값으로 선택합니다.

| provider | 키 | 비고 |
|---|---|---|
| `veo` | `GEMINI_API_KEY` | Google Veo 3.1 — `google-genai` SDK |
| `grok` | `XAI_API_KEY` | xAI `grok-imagine-video` (api.x.ai) |
| `kling` | `KLING_ACCESS_KEY`+`KLING_SECRET_KEY` | JWT 인증, task 폴링 |
| `higgsfield` | `SEGMIND_API_KEY` | Higgsfield(dop) 모델을 Segmind 호스팅으로 호출 |

공식 문서: [Veo](https://ai.google.dev/gemini-api/docs/video) · [Grok](https://docs.x.ai/developers/rest-api-reference/inference/videos) · [Kling](https://app.klingai.com/global/dev/document-api) · [Higgsfield/Segmind](https://www.segmind.com/models/higgsfield-image2video/api)

> 어댑터(`scripts/generate_videos.py`)는 각 provider 공식 스펙 기준으로 작성되었습니다. **실제 영상 출력은 해당 provider 키·과금이 있어야 검증**됩니다.

---

## 8. 폴더 구조

```
auto-video-toolkit/
├── README.md / AGENTS.md / CLAUDE.md   # 진입 규약(멀티 플랫폼)
├── pyproject.toml
├── config/  (api-keys.env.example, models.yaml)
├── skills/  (auto-video)
├── agents/  (director + phase1×4 + phase2×7)
├── scripts/ (generate_images=ima2, generate_videos=4 provider, produce, compositor, capcut-project-gen)
├── commands/create-c.md
├── guides/ docs/                       # CapCut·Kling 가이드
├── vendor/ima2-gen/                    # GPT Image 2 엔진(동봉)
├── brand-example/                      # Phase 1 산출물 예시
└── examples/sample-project/            # 표준 산출물 예시(텍스트만)
```

---

## 9. 샘플 참고

`examples/sample-project/`에 실제 에피소드의 텍스트 산출물(대본·프롬프트·CapCut config 템플릿)이 들어 있습니다(미디어 제외). 워크플로우 산출물 구조를 미리 확인하는 용도입니다.

---

## 10. 문제 해결

- **`ima2 ping` 실패 / 이미지가 안 나옴** → 다른 터미널에서 `ima2 serve` 실행 중인지, `npx @openai/codex login` 했는지 확인.
- **`ima2` 명령 없음** → `npm install -g ima2-gen` 또는 `vendor/ima2-gen`에서 설치.
- **영상 "필요한 키 미설정"** → 선택한 provider의 키를 `config/api-keys.env`에 채우세요.
- **`ffprobe 없음`** → `brew install ffmpeg`.
- **나레이션 0초** → ElevenLabs 키/크레딧 확인.
- **이미지마다 인물이 달라짐** → 프롬프트에 인종·피부색 명시 + 앵커(`--anchor`) 사용.
- **CapCut 합성은 macOS 기준**(샌드박스 → `Resources/` 복사, `capcut-project-gen.py`가 자동 처리). Windows는 영상·나레이션·자막까지 만든 뒤 수동 합성.
