---
title: Day 5 — Phase 2 (1): 리서치 · 대본 · 씬 분할
type: lesson
day: 5
tags:
  - auto-video
  - 부트캠프
  - 실습
  - phase2
  - video-first
est_time: 120분
prev: "[[Day-4-Phase1-브랜드세팅]]"
next: "[[Day-6-Phase2-비주얼과음성]]"
---

# Day 5 — Phase 2 (1): 리서치 · 대본 · 씬 분할

> [!success] 오늘의 목표
> 영상 제작의 앞 절반을 완성합니다: **주제 정하기 → Video-First 계산 → 리서치 → 대본 → 씬 분할.** 비주얼/음성 생성은 [[Day-6-Phase2-비주얼과음성]]에서.

선행: [[Day-4-Phase1-브랜드세팅]] (brand/ YAML 4개 완성 필수) · ⏱️ 예상 120분

> [!warning] 사전 조건
> Phase 2는 `brand/` YAML 4개가 채워져 있어야 시작됩니다. 안 됐으면 [[Day-4-Phase1-브랜드세팅]]을 먼저 끝내세요.

---

## 1. 시작: 영상 1편 의뢰하기

Claude Code에서:

```
/auto-video create "AI가 거짓말하는 이유"
```

또는 인터뷰 방식:

```
/create-c
```

`/create-c`는 5가지를 물어봅니다:

| 질문 | 예시 답 |
|---|---|
| Q1. 채널/트랙 | 내 채널 (Day 4에서 만든 것) |
| Q2. 주제 | "AI가 거짓말하는 이유" |
| Q3. 러닝타임 | 숏폼 59초 / 롱폼 3~5분 |
| Q4. 영상 도구 | Veo3(8초) / Kling(10초) / 혼합 |
| Q5. 보이스 | 채널 기본 보이스 |

---

## 2. 핵심: Video-First 역산 (직접 계산해보기)

질문에 답하면 AI가 자동으로 계산하지만, **원리를 직접 손으로 계산해보는 게 오늘의 핵심**입니다.

> [!important] 공식
> ```
> 씬 수      = 러닝타임(초) ÷ 클립 길이(초)
> 총 단어 수 = 러닝타임(초) ÷ 60 × 150        (영어 150 WPM)
> 씬당 단어  = 총 단어 수 ÷ 씬 수
> ```

### 예제 1: 숏폼 59초 + Veo3(8초)

```
씬 수      = 59 ÷ 8  ≈ 7씬
총 단어 수 = 59 ÷ 60 × 150 ≈ 148단어
씬당 단어  = 148 ÷ 7 ≈ 21단어
```

### 예제 2: 롱폼 3분30초(210초) + Kling(10초)

```
씬 수      = 210 ÷ 10 = 21씬
총 단어 수 = 210 ÷ 60 × 150 = 525단어
씬당 단어  = 525 ÷ 21 = 25단어
```

> [!tip] 왜 미리 계산?
> 대본을 다 써놓고 보니 영상 길이가 안 맞아 다시 쓰는 사태를 막기 위함입니다. **길이가 먼저, 대본은 그 틀에 맞춤.**

---

## 3. 단계 ① researcher — 리서치

researcher 에이전트가 주제에 대한 자료(채널·뉴스·SNS·팩트)를 모아 `research.md`로 정리합니다. scriptwriter가 바로 쓸 수 있는 형태로요.

> [!note] 체크포인트
> 리서치 결과를 읽고 → **사실 오류·빠진 내용**이 없는지 확인 → 승인.

---

## 4. 단계 ② scriptwriter — 대본 (창작의 핵심)

리서치 + brand 가이드를 바탕으로 대본을 씁니다. 채널 톤·서사 공식·리텐션을 모두 반영.

> [!example] 영어 콘텐츠라면 이중 생성
> - `script.md` — 영문(실제 사용)
> - `script-ko.md` — 한글(검수용)

### 영어 콘텐츠 주의사항 (가이드북 노하우)

> [!warning] 미국 구어체 필수 (BBC식 금지)
> - footballer → **player**
> - nil → **nothing**
> - pitch → **field**
> - HOOK과 본편에 **같은 문장 반복 금지**
> - **나레이션 = 서사 / 자막 = 팩트·수치** 역할 분담 (둘이 같은 말 반복 X)

> [!note] 체크포인트
> 대본을 읽고 → 길이(단어 수)·톤·흐름 확인 → 수정 요청 or 승인. 이 단계에서 충분히 다듬으세요. 대본이 모든 것의 기초입니다.

---

## 5. 단계 ③ scene-director — 씬 분할

대본을 **씬별 연출 지시서(direction.yaml)**로 변환합니다. 각 씬마다:

- 분위기, 카메라 무빙
- **`visual_type: image` 인지 `video` 인지** ← 매우 중요 (Day 6에서 누가 처리할지 갈림)
- 캐릭터 비주얼 일관성 키워드

> [!important] image vs video 구분
> - `image` → image-generator(GPT Image 2)가 정지 이미지 생성 → 합성 때 Ken Burns(움직임) 효과
> - `video` → video-generator가 실제 영상 클립 생성 (비용 ↑)
> 초보자는 **image 위주**로 시작하면 저렴하고 빠릅니다.

---

## 🛠️ 오늘의 실습

> [!todo] 따라 하기
> - [ ] 종이/메모에 **내 영상의 Video-First 계산**을 직접 해본다 (씬 수·단어 수)
> - [ ] `/auto-video create "주제"` 또는 `/create-c` 실행
> - [ ] researcher 완료 → `research.md` 확인·승인
> - [ ] scriptwriter 완료 → `script.md` 확인·(필요시 수정)·승인
> - [ ] scene-director 완료 → 각 씬의 `visual_type`을 확인
> - [ ] `examples/sample-project/script.md`, `image-prompts.md`와 내 결과를 비교

---

## ✅ 오늘의 테스트

### 계산 테스트 (직접 풀기)

> 롱폼 **4분(240초)** + **Veo3(8초)** 라면? 씬 수 / 총 단어 / 씬당 단어는?

> [!success]- 정답
> 씬 수 = 240÷8 = **30씬** / 총 단어 = 240÷60×150 = **600단어** / 씬당 = 600÷30 = **20단어**

### 실습 검증

```bash
cd /Users/woodncarpenter/Downloads/auto-video-toolkit
ls projects/                          # ✅ 새 프로젝트 폴더 생성됨
cat projects/*/script.md | head -20   # ✅ 대본 내용 존재
```

### 개념 퀴즈
1. Video-First에서 가장 먼저 정하는 것은?
2. scene-director가 각 씬에 찍는 중요한 도장(필드)은?
3. 나레이션과 자막의 역할 분담은?

> [!success]- 정답 펼치기
> 1. 영상 러닝타임(길이).
> 2. `visual_type` (image / video).
> 3. 나레이션=서사 전달, 자막=팩트·수치 (서로 중복 금지).

### 자가 점검
- [ ] Video-First 계산을 스스로 할 수 있다
- [ ] `script.md`가 생성됐고 내용을 검토했다
- [ ] 각 씬이 image인지 video인지 안다

---

➡️ 다음: [[Day-6-Phase2-비주얼과음성]] — 이미지·영상·목소리를 실제로 생성합니다.
