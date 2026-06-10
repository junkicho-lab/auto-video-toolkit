---
title: Day 3 — 에이전트 시스템 이해
type: lesson
day: 3
tags:
  - auto-video
  - 부트캠프
  - 개념
  - 에이전트
est_time: 100분
prev: "[[Day-2-환경설정]]"
next: "[[Day-4-Phase1-브랜드세팅]]"
---

# Day 3 — 에이전트 시스템 이해

> [!success] 오늘의 목표
> "12명의 AI 일꾼"이 각각 누구이고, 무엇을 입력받아 무엇을 내놓는지, 그리고 **팀장(Director)이 어떻게 지휘하는지** 이해합니다. 오늘도 읽고 이해하는 날입니다.

선행: [[Day-1-큰그림과-개념]], [[Day-2-환경설정]] · ⏱️ 예상 100분

---

## 1. 에이전트 = "역할이 정해진 AI 직원"

다시 강조: 에이전트는 **마법이 아니라 잘 쓰여진 지시서(프롬프트 텍스트, `.md` 파일)** 입니다.

각 에이전트 파일을 열어보면 거의 항상 이런 구조입니다:

```
## 역할 정의   ← "너는 OO 전문가야"
## 입력        ← "이 파일들을 먼저 읽어"
## 출력        ← "결과를 이 파일에 저장해"
## 진행 방식    ← "사용자에게 이렇게 질문하고 제안해"
## 품질 기준    ← "이 조건을 만족해야 해"
## 저장 지시    ← "Write 도구로 저장하고 다음 단계를 안내해"
```

> [!important] 이게 핵심 패턴입니다
> **입력(읽기) → 질문/제안 → 산출물 생성 → 저장 → 다음 단계 안내.**
> 모든 에이전트가 이 패턴을 따릅니다. 이 패턴 하나를 이해하면 12개를 다 이해한 셈입니다.

---

## 2. 팀장: Director

`agents/director.md`가 전체를 지휘합니다. 하는 일:

1. **Phase 판단** — `brand/` 폴더의 YAML 4개가 비었나 채워졌나 확인 → 비었으면 Phase 1, 채워졌으면 Phase 2
2. **에이전트 배정** — 각 단계에 맞는 에이전트를 순서대로 호출
3. **체크포인트 관리** — 각 단계가 끝나면 사용자에게 *승인 / 수정 / 재생성* 을 물어봄

> [!note] "체크포인트"가 중요한 이유
> AI가 혼자 끝까지 달리지 않습니다. **단계마다 멈춰서 당신의 승인을 받습니다.** 마음에 안 들면 그 단계만 다시 시킬 수 있어요. (수정 3회 초과 시 방향 재확인)

---

## 3. Phase 1 에이전트 4명 (브랜드 세팅)

| 순서 | 에이전트 | 역할 | 입력 | 출력 |
|---|---|---|---|---|
| 1 | **brand-architect** | 캐릭터 외형·성격·말투 설계 | 사용자 채널 방향 | `brand/character.yaml` |
| 2 | **narrative-designer** | 세계관·서사·에피소드 공식 | character.yaml | `brand/narrative.yaml` |
| 3 | **topic-strategist** | 주제 영역·콘텐츠 기둥 | character + narrative | `brand/topics.yaml` |
| 4 | **benchmark-analyst** | 성공 채널 벤치마크 분석 | 위 3개 | `brand/benchmark.yaml` |

> 뒤 에이전트는 항상 **앞 에이전트의 산출물을 먼저 Read**합니다. 그래서 순서가 중요합니다 (캐릭터가 정해져야 서사를 짜죠).

---

## 4. Phase 2 에이전트 7명 (콘텐츠 제작)

| 순서 | 에이전트 | 역할 | 출력 |
|---|---|---|---|
| 1 | **researcher** | 주제 자료 조사 | `research.md` |
| 2 | **scriptwriter** | 대본 작성 (창작 핵심) | `script.md` (+`script-ko.md`) |
| 3 | **scene-director** | 대본을 씬별 연출 지시서로 변환 | `direction.yaml` (씬별) |
| 4a | **image-generator** | `visual_type:image` 씬 이미지 생성 | `scenes/images/scene-NN.png` |
| 4b | **video-generator** | `visual_type:video` 씬 영상 생성 | `scenes/videos/scene-NN.mp4` |
| 5 | **voice-producer** | 씬별 나레이션 TTS | `narration/scene-NN.wav` |
| 6 | **compositor** | 전부 합쳐 최종 영상 렌더 | `final.mp4` + 메타데이터 |

> [!tip] 4a/4b는 "병렬" 실행
> scene-director가 각 씬에 `image`냐 `video`냐 도장을 찍어두면, 이미지 담당과 영상 담당이 **동시에** 일합니다. (시간 절약)

---

## 5. "사고형 vs 실행형" 모델 배정

director는 에이전트마다 다른 AI 모델을 씁니다:

| 모델 | 성격 | 맡는 에이전트 |
|---|---|---|
| **opus** (똑똑·창의) | 깊은 사고·창작 | brand-architect, scriptwriter, scene-director |
| **sonnet** (빠름·실무) | 정해진 작업 실행 | researcher, image/video-generator, voice-producer, compositor |

> [!note] 왜 나눌까?
> 대본 쓰기(창작)는 똑똑한 모델, 이미지 스크립트 돌리기(단순 실행)는 빠른 모델. **비용과 품질의 균형**입니다.

---

## 6. "이 PDF만으로 프로젝트가 생기는" 비밀

원본 가이드북의 진짜 컨셉: **빈 폴더에 PDF 하나만 넣고** Claude Code에게

> *"이 PDF 읽고 프로젝트 전체 세팅해줘. 환경 설정, 파일 생성, 의존성 설치까지 전부."*

라고 하면 → Claude Code가 PDF를 읽고 **디렉토리·에이전트 12개·스크립트 5개·설정파일을 전부 자동 생성**합니다.

> [!important] 통찰
> 즉 이 PDF는 "**재현 가능한 설계 명세서**"입니다. 코드 폴더는 그 PDF를 실행한 *결과물*이고요. 이 구조 자체가 배울 만한 패턴입니다 (Day 7 졸업 과제에서 다룸).

---

## 🛠️ 오늘의 실습 (코드 없음, 읽고 비교)

> [!todo] 따라 하기 — 에이전트 파일 직접 읽기
> - [ ] `agents/director.md`를 다시 열어 "Phase 판단 로직" 부분만 정독
> - [ ] `agents/phase1/brand-architect.md`를 열어 **5단계 진행 방식**(질문→제안→조정→프롬프트→저장)을 확인
> - [ ] `agents/phase2/scriptwriter.md` 와 `agents/phase2/image-generator.md`를 비교 — **"창작하는 에이전트"와 "실행만 하는 에이전트"의 톤 차이**를 느껴본다
>   - scriptwriter: "서사·리텐션을 판단해라" (창작)
>   - image-generator: "창작 판단은 하지 않으며 파라미터 결정과 스크립트 실행만" (실행)

---

## ✅ 오늘의 테스트

### 개념 퀴즈

1. 모든 에이전트가 공통으로 따르는 구조(패턴)는?
2. Director가 하는 3가지 일은?
3. "체크포인트"에서 사용자가 고를 수 있는 3가지 선택지는?
4. scriptwriter와 image-generator의 결정적 차이는?
5. opus와 sonnet은 각각 어떤 종류의 에이전트에 배정되나?

> [!success]- 정답 펼치기
> 1. 입력(읽기) → 질문/제안 → 산출물 생성 → 저장 → 다음 단계 안내.
> 2. Phase 판단 / 에이전트 배정 / 체크포인트(승인) 관리.
> 3. 승인 / 수정 요청 / 재생성.
> 4. scriptwriter는 **창작·판단**을 하고, image-generator는 **창작 없이 스크립트 실행만** 한다.
> 5. opus = 창작·사고형(대본·씬연출·캐릭터), sonnet = 실행형(리서치·생성·합성).

### 자가 점검
- [ ] 에이전트 12명의 이름과 대략의 역할을 댈 수 있다
- [ ] Phase 1과 Phase 2 에이전트를 구분할 수 있다
- [ ] 에이전트 파일을 실제로 3개 이상 열어봤다

---

➡️ 다음: [[Day-4-Phase1-브랜드세팅]] — 드디어 직접 실행! 내 채널 정체성을 만듭니다.
