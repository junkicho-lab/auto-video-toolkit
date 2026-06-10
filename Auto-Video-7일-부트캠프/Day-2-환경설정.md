---
title: Day 2 — 환경 설정 (도구 설치)
type: lesson
day: 2
tags:
  - auto-video
  - 부트캠프
  - 실습
  - 환경설정
est_time: 120분
prev: "[[Day-1-큰그림과-개념]]"
next: "[[Day-3-에이전트-시스템]]"
---

# Day 2 — 환경 설정 (도구 설치)

> [!success] 오늘의 목표
> 내 맥에 필요한 도구를 모두 설치하고, "**준비 완료(ima2 ping 성공)**" 상태를 만듭니다. 오늘이 가장 손이 많이 가지만, 한 번만 하면 됩니다.

선행: [[Day-1-큰그림과-개념]] · ⏱️ 예상 120분 · 💻 **맥(macOS) 필요**

> [!warning] 막히면?
> 설치는 환경마다 에러가 잘 납니다. 막히면 바로 [[부록-트러블슈팅]]을 보거나, **Claude Code에게 에러 메시지를 그대로 복사해서 물어보세요.** 사실 이 프로젝트는 "Claude Code가 대신 설치해주는 것"을 전제로 설계됐습니다 (Day 3에서 설명).

---

## 1. 무엇을 설치하나? (전체 지도)

| 도구 | 용도 | 필수? |
|---|---|---|
| **Homebrew** | 맥용 설치 관리자 (다른 걸 깔기 위한 도구) | ✅ |
| **Python 3.10+** | 모든 스크립트의 실행 환경 | ✅ |
| **Node.js 20+** | 이미지 엔진 `ima2` 구동용 | ✅ |
| **ffmpeg** | 영상/오디오 길이 분석 (합성에 필수) | ✅ |
| **ima2 (ima2-gen)** | GPT Image 2 이미지 생성 엔진 | ✅ |
| **CapCut** | 최종 영상 편집/합성 (앱) | 합성 시 |
| **API 키들** | Gemini, ElevenLabs 등 | 사용분만 |

---

## 2. 단계별 설치

> [!tip] 터미널 여는 법
> `Spotlight(⌘+Space)` → "터미널" 입력 → Enter. 아래 명령어를 한 줄씩 복사해 붙여넣고 Enter.

### Step 1 — Homebrew (이미 있으면 건너뛰기)

```bash
# 설치 여부 확인
brew --version
# 없으면 설치 (공식 스크립트)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### Step 2 — Python · Node · ffmpeg

```bash
brew install python@3.12 node ffmpeg
# 확인
python3 --version   # 3.10 이상이면 OK
node --version      # v20 이상이면 OK
ffprobe -version    # 정보가 나오면 OK
```

### Step 3 — 파이썬 의존성 설치

```bash
cd /Users/woodncarpenter/Downloads/auto-video-toolkit

# 가상환경 만들기 (권장 — 시스템과 분리)
python3 -m venv .venv
source .venv/bin/activate          # 활성화 (터미널 줄 앞에 (.venv) 표시됨)

# 프로젝트 의존성 설치
pip install -e ".[dev]"
```

> [!note] 가상환경(venv)이 뭐예요?
> 프로젝트 전용 "격리된 파이썬 방"입니다. 여기 깐 패키지는 시스템 전체를 어지럽히지 않습니다. **새 터미널을 열 때마다** `source .venv/bin/activate`를 다시 해줘야 합니다.

`pyproject.toml`에 정의된 핵심 패키지: `google-genai`(Gemini), `elevenlabs`(TTS), `moviepy`(합성), `pyyaml`, `httpx`, `pillow`, `pyjwt`(Kling 인증).

### Step 4 — 이미지 엔진 ima2 (GPT Image 2)

```bash
# 전역 설치
npm install -g ima2-gen

# OpenAI(Codex) 로그인 — 브라우저가 열림 (API 키 불필요!)
npx @openai/codex login

# 로컬 이미지 서버 켜기 (별도 터미널에서 계속 켜둬야 함)
ima2 serve

# 동작 확인 (또 다른 터미널에서)
ima2 ping
```

> [!important] ima2 serve는 "켜둔 채" 작업
> `ima2 serve`는 이미지를 만드는 동안 **계속 실행 중**이어야 합니다. 터미널 하나를 이 용도로 열어두고, 작업은 다른 터미널에서 하세요. `ima2 ping`이 성공해야 이미지 생성이 됩니다.

### Step 5 — CapCut 설치

Mac App Store에서 **CapCut** 검색 → 무료 설치. (합성 단계인 Day 7에서 사용)

---

## 3. API 키 설정

```bash
cd /Users/woodncarpenter/Downloads/auto-video-toolkit

# 예시 파일을 복사 (실제 키 파일은 git에 안 올라감 = 안전)
cp config/api-keys.env.example config/api-keys.env

# 편집기로 열어서 사용할 키만 채우기
open -e config/api-keys.env
```

`config/api-keys.env`에서 **사용할 것만** 채웁니다:

```bash
GEMINI_API_KEY=...        # 리서치/대본/이미지프롬프트 + veo 영상 (가장 많이 씀)
XAI_API_KEY=...           # grok 영상 쓸 때만
KLING_ACCESS_KEY=...      # kling 영상 쓸 때만
KLING_SECRET_KEY=...
SEGMIND_API_KEY=...       # higgsfield 영상 쓸 때만
ELEVENLABS_API_KEY=...    # 나레이션(TTS)
```

> [!tip] 초보자 추천 최소 구성
> **`GEMINI_API_KEY` + `ELEVENLABS_API_KEY` 두 개만** 있으면 충분히 연습 가능합니다.
> - Gemini 키: [aistudio.google.com](https://aistudio.google.com) → Get API key
> - ElevenLabs 키: elevenlabs.io 가입 → Profile → API key

### 키 발급처 정리

| provider | 발급처 | 용도 |
|---|---|---|
| Gemini | aistudio.google.com | 리서치·대본·veo영상 |
| xAI (Grok) | console.x.ai | grok 영상 |
| Kling | app.klingai.com | kling 영상 |
| Segmind | segmind.com | higgsfield 영상 |
| ElevenLabs | elevenlabs.io | 나레이션 |

---

## 4. 영상 provider 선택

`config/models.yaml`의 `video_generation` 값으로 어떤 영상 도구를 쓸지 정합니다:

```yaml
video_generation: "veo"    # veo | grok | kling | higgsfield 중 하나
```

> [!tip] 초보자는 `veo` 추천 — Gemini 키 하나로 영상까지 됩니다.

---

## 🛠️ 오늘의 실습

> [!todo] 따라 하기
> - [ ] Homebrew 설치/확인 (`brew --version`)
> - [ ] Python·Node·ffmpeg 설치 (`python3 --version`, `node --version`, `ffprobe -version`)
> - [ ] 가상환경 만들고 `pip install -e ".[dev]"` 성공
> - [ ] `ima2 serve` 켜고 → 다른 터미널에서 `ima2 ping` 성공
> - [ ] `config/api-keys.env` 만들고 Gemini + ElevenLabs 키 입력
> - [ ] CapCut 앱 설치

---

## ✅ 오늘의 테스트 (환경 점검)

아래 명령을 모두 실행해 **에러 없이** 나오면 통과입니다:

```bash
cd /Users/woodncarpenter/Downloads/auto-video-toolkit
source .venv/bin/activate

python3 --version            # ✅ 3.10+
node --version               # ✅ v20+
ffprobe -version             # ✅ 버전 정보 출력
ima2 ping                    # ✅ 성공 응답
python3 -c "import yaml, httpx, PIL; print('파이썬 패키지 OK')"   # ✅ 'OK' 출력
ls config/api-keys.env       # ✅ 파일 존재
```

> [!success]- 통과 기준
> 위 6줄이 모두 에러 없이 통과하면 환경 설정 완료! `import` 줄에서 에러가 나면 `pip install -e ".[dev]"`를 다시, `ima2 ping` 실패면 `ima2 serve`가 켜져 있는지 확인.

### 자가 점검
- [ ] 6개 점검 명령이 모두 통과했다
- [ ] `ima2 serve`를 켜고 끄는 법을 안다
- [ ] API 키 파일이 어디 있는지 안다 (`config/api-keys.env`)

---

> [!quote]
> Claude는 완벽하지 않습니다. 중요한 결정은 항상 확인하세요.

➡️ 다음: [[Day-3-에이전트-시스템]] — 이제 12명의 AI 일꾼을 만나봅니다.
