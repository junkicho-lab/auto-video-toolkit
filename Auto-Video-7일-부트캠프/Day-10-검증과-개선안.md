---
title: Day 10 (심화) — 앱 검증과 최신 기법 개선안
type: lesson
day: 10
tags:
  - auto-video
  - 부트캠프
  - 심화
  - 검증
  - 개선안
  - ai-native
est_time: 80분
prev: "[[Day-9-스크립트는-누가-만드나]]"
next: "[[00-시작하기]]"
---

# Day 10 (심화) — 앱 검증과 최신 LLM 기법 개선안

> [!success] 이 노트의 목표
> 실제 코드를 점검해 발견한 문제를 정리하고, 2026년 최신 LLM 기법으로 개선안을 우선순위와 함께 제시합니다.

선행: [[Day-8-에이전트-하네스와-AI-Native]], [[Day-9-스크립트는-누가-만드나]] · ⏱️ 80분 · 심화

---

## A. 검증 결과 — 실제 코드에서 찾은 문제

### 🔴 Critical (정합성 — 지금 파이프라인이 안 이어짐)

| # | 문제 | 근거 | 영향 |
|---|---|---|---|
| C1 | **씬 입출력 "계약" 불일치** | scene-director는 YAML 출력 / `generate_images.py`는 `### Scene N:`+`**Prompt:**`, `generate_videos.py`는 `**Video Prompt:**` 기대 | LLM 산출물을 스크립트가 못 읽음 |
| C2 | **디렉토리 레이아웃 3종 혼재** | orchestrator=`scenes/images,videos/` / images=`scenes/scene-NN/img_01.png` / videos=`scenes/scene-NN/video.mp4` | compositor 입력 불명 → 합성 실패 위험 |
| C3 | **compositor `--format portrait` 무효** | compositor는 `short\|long`만 허용, orchestrator는 `portrait` 전달 | `--media` 합성 단계 에러 |

### 🟠 High (신뢰성/비용)

| # | 문제 | 해결 기법 |
|---|---|---|
| H1 | 출력 파싱이 정규식 의존 (깨지기 쉬움) | **구조화 출력(responseSchema)** |
| H2 | 브랜드 컨텍스트 매 호출 재전송 (토큰 낭비) | **컨텍스트 캐싱** |
| H3 | 미디어 스크립트에 재시도 없음 | 백오프 재시도(두뇌엔 이미 있음) |
| H4 | 모델 라우팅 미사용 (전부 flash) | 창작=pro, 실행=flash |

### 🟡 Medium (품질/운영)

| # | 문제 | 기법 |
|---|---|---|
| M1 | 품질 평가/회귀 테스트 없음 | **Evaluator-Optimizer (LLM-as-judge)** |
| M2 | 리서치 근거 부재 (환각 위험) | **RAG/웹검색 그라운딩 (ReAct)** |
| M3 | veo가 글자를 영상에 구움 + 캐릭터 일관성 약함 | "no text" 가드 + **image-to-video**(앵커) |
| M4 | 관측성 부재 (토큰/비용/추적) | 구조적 로깅·비용 트래킹 |
| M5 | 씬 생성 순차 처리 | 병렬 fan-out |

---

## B. 최신 LLM 기법 (2026 조사 요약)

1. **구조화 출력** — Gemini `responseSchema`로 JSON/enum 강제. 스키마는 responseSchema에만, 필드 `description` 활용, **값 의미 검증은 앱이 따로**.
2. **함수 호출(ReAct)** — 모델이 도구 직접 호출, 생각↔행동 교차로 환각↓. 결과 있는 행동은 사용자 확인 후 실행.
3. **프롬프트/컨텍스트 캐싱** — 반복 컨텍스트 캐시 → 지연/비용↓.
4. **Evaluator-Optimizer** — 생성자/심판(LLM-as-judge) 분리 → 루브릭 점수 → 자동 개선 루프.
5. **병렬화 + 플래너/실행기 분리** — 보고 사례 3.6배 속도.
6. **Evals** — 골든셋·충실도·인용정확도로 회귀 방지.

---

## C. 개선 로드맵 (우선순위)

### P0 — 정합성 복구 (먼저, 비용 0)
- **단일 진실원천(scenes.json)**: scene-director를 responseSchema로 강제 → `scenes.json` 하나만 생성 → 모든 미디어 스크립트가 이 파일을 읽게 통일 (C1·C2)
- **compositor `--format` 매핑 + 레이아웃 표준화** (C3)

### P1 — 신뢰성/비용
- 컨텍스트 캐싱 (H2) / 미디어 재시도 (H3) / 모델 라우팅 (H4) / 프리플라이트 모델 검증

### P2 — 품질
- Evaluator-Optimizer 자동 개선 (M1) / 그라운디드 리서치 (M2) / 자막=SRT 분리 + no-text + image-to-video (M3)

### P3 — 스케일/운영
- 씬 병렬 생성 (M5) / 관측성·비용 로깅 (M4) / Eval 하네스

---

## 가장 임팩트 큰 한 방

> [!important] 1순위: **구조화 출력 + 단일 scenes.json 계약** (H1+C1+C2)
> 모든 정합성 문제의 뿌리는 "LLM 자유 텍스트 ↔ 스크립트 파서" 사이에 **계약이 없다**는 것. Gemini `responseSchema`로 씬을 JSON으로 강제하고 모든 스크립트가 그 JSON 하나를 읽게 하면 한 번에 해결.

---

## 참고 출처
- [Gemini 구조화 출력](https://ai.google.dev/gemini-api/docs/structured-output)
- [Improving Structured Outputs in the Gemini API](https://blog.google/innovation-and-ai/technology/developers-tools/gemini-api-structured-outputs/)
- [Function calling with the Gemini API](https://ai.google.dev/gemini-api/docs/function-calling)
- [Agents At Work: 2026 Playbook](https://promptengineering.org/agents-at-work-the-2026-playbook-for-building-reliable-agentic-workflows/)
- [Agentic Design Patterns: 2026 Guide](https://www.sitepoint.com/the-definitive-guide-to-agentic-design-patterns-in-2026/)

---

## ✅ 이해 점검
1. 이 앱의 가장 근본적인 정합성 문제(뿌리)는?
2. 그것을 한 번에 해결하는 최신 기법은?
3. Evaluator-Optimizer 패턴이란?

> [!success]- 정답
> 1. LLM 자유 텍스트와 스크립트 파서 사이에 "계약(스키마)"이 없음.
> 2. 구조화 출력(responseSchema) + 단일 scenes.json 계약.
> 3. 생성자와 심판(LLM-as-judge)을 분리해 점수 매기고 자동 개선하는 루프.

⬅️ 돌아가기: [[00-시작하기]] · 관련: [[Day-8-에이전트-하네스와-AI-Native]]
