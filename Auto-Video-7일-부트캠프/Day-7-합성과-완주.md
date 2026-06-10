---
title: Day 7 — 합성 · 완주 · 졸업
type: lesson
day: 7
tags:
  - auto-video
  - 부트캠프
  - 실습
  - 합성
  - capcut
  - 졸업
est_time: 120분
prev: "[[Day-6-Phase2-비주얼과음성]]"
next: "[[부록-최종-체크리스트]]"
---

# Day 7 — 합성 · 완주 · 졸업

> [!success] 오늘의 목표
> 흩어진 이미지·영상·나레이션·자막을 **하나의 영상으로 합칩니다.** 두 가지 경로가 있습니다: ① MoviePy 자동 합성, ② CapCut 프로젝트 자동 생성(수동 편집). 그리고 **영상 1편을 완주**하고 졸업합니다.

선행: [[Day-6-Phase2-비주얼과음성]] (이미지·나레이션 완성) · ⏱️ 예상 120분

---

## 1. 두 가지 합성 경로

| 경로 | 도구 | 특징 | 추천 |
|---|---|---|---|
| A | **compositor.py** (MoviePy) | 완전 자동 → `final.mp4` 바로 나옴 | 빠른 결과 |
| B | **capcut-project-gen.py** | CapCut 프로젝트 생성 → 직접 편집 가능 | 품질·디테일 |

> [!tip] 초보자는 A로 결과를 먼저 보고, 만족스러우면 B로 디테일을 다듬으세요.

---

## 2. 경로 A — MoviePy 자동 합성

```bash
cd /Users/woodncarpenter/Downloads/auto-video-toolkit
source .venv/bin/activate

python3 scripts/compositor.py \
  --project projects/{slug} \
  --format landscape
```

| `--format` | 용도 |
|---|---|
| `landscape` | 16:9 가로 (롱폼/유튜브) |
| `portrait` 등 | 9:16 세로 (숏폼) — 스크립트 옵션 확인 |

이미지 씬에는 **Ken Burns 효과**(천천히 줌/팬)가 자동 적용돼 정지 이미지도 살아 움직입니다.

→ 결과: `output/final.mp4`

---

## 3. 경로 B — CapCut 프로젝트 생성

> [!important] 왜 전용 스크립트를 써야 하나
> macOS CapCut은 **샌드박스**라 외부 파일을 직접 못 읽습니다. 그래서 미디어를 프로젝트의 `Resources/`로 **복사**하고 `draft_info.json`을 만들어야 하는데, 이걸 손으로 하면 거의 실패합니다. **`capcut-project-gen.py`가 전부 자동 처리**합니다.

```bash
python3 scripts/capcut-project-gen.py config.json
```

`config.json`(또는 `capcut-config.json`)에 video/audio/subtitle 경로를 지정하면 됩니다. `examples/sample-project/capcut-config.example.json`을 템플릿으로 쓰세요.

### CapCut 핵심 상수 (가이드북)

> [!example] 알아두면 좋은 값
> - 시간 단위: **마이크로초** (1초 = 1,000,000)
> - 자막 스타일: font_size=6.0, color=[1,1,1](흰색), position_y=-0.764(하단), scale=0.7
> - extra_material_refs: video=6, audio=5, text=1
> - `ffprobe` 필수 (영상 길이 측정)

> [!warning] draft_info.json 수동 생성 금지
> 반드시 스크립트를 쓰세요. 수동 생성은 실패 확률이 매우 높습니다.

생성 후 CapCut 앱에서 프로젝트를 열어 자막·전환·BGM을 다듬고 내보내기(Export)하면 끝!

---

## 4. 전체 파이프라인 한눈에 복습

```
[Phase 1 — 채널당 1회]
brand-architect → narrative-designer → topic-strategist → benchmark-analyst
                         ↓
                  brand/ YAML 4개

[Phase 2 — 영상 1편당 1회]
주제 + Video-First 계산
  → researcher (research.md)
  → scriptwriter (script.md)
  → scene-director (씬별 direction.yaml)
  → 앵커 이미지
  → image-generator(이미지) ∥ video-generator(영상)
  → voice-producer (narration/*.wav)
  → SRT 자막
  → compositor / capcut-project-gen → 최종 영상 🎬
```

---

## 🎓 졸업 과제 (택 1)

> [!todo] 졸업 미션
> - [ ] **미션 A (필수):** 처음부터 끝까지 **숏폼 59초 영상 1편**을 완주해 `final.mp4`(또는 CapCut export)를 만든다.
> - [ ] **미션 B (도전):** 같은 채널로 **두 번째 영상**을 만들어, Phase 1을 건너뛰고 Phase 2만 반복하는 흐름을 체득한다.
> - [ ] **미션 C (응용):** "이 프로젝트가 어떻게 동작하는지"를 [[실습기록]]에 **나만의 설명서 1장**으로 정리한다 (남에게 가르칠 수 있게).

---

## ✅ 최종 테스트 (졸업 시험)

### 실습 검증

```bash
cd /Users/woodncarpenter/Downloads/auto-video-toolkit
# 최종 영상이 존재하고 0초가 아닌지
ls -la projects/{slug}/output/final.mp4
ffprobe -i projects/{slug}/output/final.mp4 2>&1 | grep Duration
```

### 종합 개념 시험 (5문제)

1. 에이전트와 스크립트의 차이를 한 줄로?
2. Phase 1과 Phase 2의 차이와 각 실행 빈도는?
3. Video-First 3대 공식(씬 수/총 단어/씬당 단어)을 쓰시오.
4. 캐릭터 일관성을 지키는 두 가지 장치는?
5. CapCut 합성에 전용 스크립트를 쓰는 이유는?

> [!success]- 정답 펼치기
> 1. 에이전트=판단/지시 프롬프트, 스크립트=실제 실행 Python 코드.
> 2. Phase 1=브랜드 세팅(채널당 1회) / Phase 2=콘텐츠 제작(영상당 1회).
> 3. 씬 수=러닝타임÷클립길이, 총 단어=러닝타임(초)÷60×150, 씬당=총단어÷씬수.
> 4. ①앵커 이미지 참조 ②모든 프롬프트에 인종/피부색 등 고정 요소 명시 (+ character.yaml consistency_rules 주입).
> 5. macOS CapCut 샌드박스 때문에 Resources/ 복사 + draft_info.json 자동 생성이 필요하고, 수동은 실패율이 높아서.

### 졸업 자가 점검
- [ ] 영상 1편을 처음부터 끝까지 완주했다
- [ ] 5문제 시험을 막힘없이 통과했다
- [ ] 문제가 생겼을 때 [[부록-트러블슈팅]]으로 스스로 해결해봤다
- [ ] 전체 파이프라인을 그림 없이 설명할 수 있다

---

## 🎉 축하합니다!

7일 부트캠프를 완주했습니다. 이제 당신은:
- AI 영상 자동제작 파이프라인을 **이해하고**
- 직접 **영상을 만들 수 있고**
- 막혀도 **스스로 해결**할 수 있습니다.

다음 단계 제안:
- 여러 영상을 만들며 프롬프트 감각 키우기
- `docs/kling-prompt-guide.md`로 영상 클립 품질 높이기
- 본인 워크플로우를 [[Day-3-에이전트-시스템]]의 "PDF 부트스트랩" 패턴처럼 **재현 가능한 명세서**로 만들어보기

> [!quote]
> Claude는 완벽하지 않습니다. 중요한 결정은 항상 확인하세요.

⬅️ 돌아가기: [[00-시작하기]] · 점검: [[부록-최종-체크리스트]]
