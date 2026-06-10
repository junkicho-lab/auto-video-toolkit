---
title: Day 6 — Phase 2 (2): 이미지 · 영상 · 나레이션 · 자막
type: lesson
day: 6
tags:
  - auto-video
  - 부트캠프
  - 실습
  - phase2
est_time: 120분
prev: "[[Day-5-Phase2-리서치와대본]]"
next: "[[Day-7-합성과-완주]]"
---

# Day 6 — Phase 2 (2): 이미지 · 영상 · 나레이션 · 자막

> [!success] 오늘의 목표
> 대본·씬 분할을 바탕으로 **실제 미디어**를 생성합니다: 캐릭터 앵커 → 씬 이미지 → 영상 클립 → 나레이션 → 자막(SRT). 가장 "결과물이 눈에 보이는" 날입니다.

선행: [[Day-5-Phase2-리서치와대본]] (script.md + 씬 분할 완료) · ⏱️ 예상 120분 · 💰 **API 과금 발생**

> [!warning] ima2 serve 켜기
> 이미지 생성 전에 **별도 터미널에서 `ima2 serve`가 실행 중**이어야 합니다. `ima2 ping`으로 확인하세요. ([[Day-2-환경설정]] 참고)

---

## 1. 단계 ②.5 — 캐릭터 앵커 이미지 (가장 먼저!)

> [!important] 앵커가 뭐고 왜 먼저?
> **앵커 = 캐릭터의 "기준 이미지"** 입니다. 이걸 먼저 만들어두고 모든 씬 이미지가 이걸 참조하면, **씬마다 캐릭터가 딴사람이 되는 사고**를 막습니다.

> [!warning] 가장 흔한 실수: 인종/피부색 누락
> **모든 프롬프트에 인종·피부색을 명시**하세요. 빼먹으면 씬마다 다른 인종의 인물이 생성됩니다. 실존 인물이면 시대별로 앵커를 분리합니다.

앵커는 `anchors/` 폴더에 저장됩니다.

---

## 2. 단계 ④a — 씬 이미지 생성 (GPT Image 2 / ima2)

`visual_type: image`인 씬들을 처리합니다.

### 에이전트로 (권장)
director가 image-generator를 호출하면 알아서 진행됩니다.

### 스크립트 직접 실행 (원리 이해용)

```bash
cd /Users/woodncarpenter/Downloads/auto-video-toolkit
source .venv/bin/activate

python3 scripts/generate_images.py \
  --project projects/{slug} \
  --prompts image-prompts.md \
  --quality high \
  --anchor anchors/character.png
```

| 옵션 | 의미 |
|---|---|
| `--project` | 프로젝트 폴더 (필수) |
| `--prompts` | 프롬프트 파일 (기본 `scene-prompts.md`) |
| `--quality` | low / medium / high |
| `--anchor` | 일관성용 기준 이미지(`--ref`로 전달) |
| `--start` / `--end` | 특정 씬 범위만 (예: 1~3씬만) |

> [!tip] 비용 절약
> 처음엔 `--quality medium` + `--start 1 --end 2`로 **2씬만 테스트**해 결과를 보고, 만족하면 전체를 돌리세요.

→ 결과: `scenes/images/scene-01.png` ~

---

## 3. 단계 ④b — 영상 클립 생성

`visual_type: video`인 씬들을 처리합니다.

```bash
python3 scripts/generate_videos.py \
  --project projects/{slug} \
  --prompts video-prompts.md \
  --provider veo \
  --duration 5 \
  --aspect-ratio 16:9
```

provider는 `--provider` > 환경변수 > `config/models.yaml` 순으로 결정됩니다.

| provider | 키 | 클립 길이 기준 |
|---|---|---|
| `veo` | GEMINI_API_KEY | 8초 |
| `grok` | XAI_API_KEY | — |
| `kling` | KLING_ACCESS_KEY + SECRET | 10초 |
| `higgsfield` | SEGMIND_API_KEY | — |

> [!note] Kling 쓸 거면
> `docs/kling-prompt-guide.md`에 Kling 전용 프롬프트 작성법이 있습니다.

→ 결과: `scenes/videos/scene-02.mp4` ~

> [!tip] 초보자 전략
> 영상 생성은 비쌉니다. **첫 영상은 전부 `image`로** 만들고 합성 때 Ken Burns(자동 줌/팬) 효과로 움직임을 주세요. 영상 클립은 익숙해진 뒤 도입.

---

## 4. 단계 ⑤ — 나레이션 (ElevenLabs TTS)

```bash
python3 scripts/produce.py \
  --project projects/{slug} \
  --step voice \
  --voice-id EXAVITQu4vr4xnSDxMaL \
  --format short
```

> [!important] 씬 단위로 생성 (가이드북 규칙)
> 나레이션은 **씬마다 따로** 생성합니다. ACT(여러 씬)를 한 번에 길게 뽑지 마세요 — 합성 때 타이밍이 안 맞습니다. 씬당 길이는 클립 길이 ±2초로 가변(기계적 끊김 방지).

→ 결과: `narration/scene-01.wav` ~

> [!note] voice-id 찾기
> ElevenLabs 사이트의 Voice Library에서 마음에 드는 보이스의 ID를 복사해 `--voice-id`에 넣습니다. (위 예시는 기본 보이스)

---

## 5. 자막 (SRT) 규칙

자막은 `capcut-export/subtitles.srt`로 생성됩니다.

> [!warning] SRT 철칙 — 어기면 CapCut에서 깨짐
> - **플레인 텍스트만** — 번호·좌표·스타일 태그 등 메타데이터 금지
> - **자막 1개당 1줄** — 2줄 이상 금지. 길면 별도 엔트리로 쪼갠다.

> [!example] 올바른 SRT
> ```
> 1
> 00:00:00,000 --> 00:00:03,000
> AI는 왜 거짓말을 할까요?
>
> 2
> 00:00:03,000 --> 00:00:06,000
> 그 이유는 의외로 단순합니다.
> ```

---

## 🛠️ 오늘의 실습

> [!todo] 따라 하기
> - [ ] `ima2 serve` 켜고 `ima2 ping` 확인
> - [ ] 캐릭터 앵커 이미지 생성 (인종/피부색 명시!)
> - [ ] 씬 이미지를 **먼저 2씬만** 테스트 생성 (`--start 1 --end 2`)
> - [ ] 결과 만족하면 전체 이미지 생성
> - [ ] (선택) 영상 클립이 있으면 video-generator 실행
> - [ ] 나레이션 생성 (`--step voice`)
> - [ ] `scenes/images/`, `narration/`에 파일이 쌓였는지 확인

---

## ✅ 오늘의 테스트

### 실습 검증

```bash
cd /Users/woodncarpenter/Downloads/auto-video-toolkit
ls projects/{slug}/scenes/images/    # ✅ scene-01.png ... 존재
ls projects/{slug}/narration/        # ✅ scene-01.wav ... 존재
# 오디오 길이 확인 (0초면 문제!)
ffprobe -i projects/{slug}/narration/scene-01.wav 2>&1 | grep Duration
```

### 개념 퀴즈
1. 앵커 이미지를 왜 먼저 만드나?
2. 모든 이미지 프롬프트에 반드시 명시할 것은?
3. 나레이션은 왜 씬 단위로 생성하나?
4. SRT 자막의 두 가지 철칙은?

> [!success]- 정답 펼치기
> 1. 캐릭터 일관성을 위해 — 모든 씬이 참조할 기준이 되어 인물이 딴사람 되는 걸 막음.
> 2. 인종/피부색 (누락 시 씬마다 다른 인종 생성).
> 3. 합성 시 타이밍을 맞추고 기계적 끊김을 막기 위해 (ACT 일괄 생성 금지).
> 4. ①플레인 텍스트만 ②자막 1개당 1줄.

### 자가 점검
- [ ] 씬 이미지가 생성됐고 캐릭터가 일관적이다
- [ ] 나레이션 wav가 0초가 아니다
- [ ] 비용을 아끼는 테스트 전략(소수 씬 먼저)을 실천했다

---

> [!quote]
> Claude는 완벽하지 않습니다. 중요한 결정은 항상 확인하세요.

➡️ 다음: [[Day-7-합성과-완주]] — 모든 걸 합쳐 영상 1편을 완성합니다!
