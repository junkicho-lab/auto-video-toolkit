---
title: Day 4 — Phase 1 브랜드 세팅 실습
type: lesson
day: 4
tags:
  - auto-video
  - 부트캠프
  - 실습
  - phase1
est_time: 120분
prev: "[[Day-3-에이전트-시스템]]"
next: "[[Day-5-Phase2-리서치와대본]]"
---

# Day 4 — Phase 1 브랜드 세팅 실습

> [!success] 오늘의 목표
> Claude Code(또는 Codex)와 대화하며 **내 채널의 정체성 4종 세트**(캐릭터·서사·주제·벤치마크)를 만듭니다. 결과물은 `brand/` 폴더의 YAML 4개입니다. **이 단계는 채널당 딱 한 번만** 합니다.

선행: [[Day-3-에이전트-시스템]] · ⏱️ 예상 120분

---

## 1. 오늘 만들 것 (산출물)

```
brand/
├── character.yaml    # 캐릭터: 외형·성격·말투·이미지 기본 프롬프트
├── narrative.yaml    # 서사: 세계관·톤·에피소드 공식(숏폼/롱폼)
├── topics.yaml       # 주제: 콘텐츠 기둥·에버그린·트렌드 키워드
└── benchmark.yaml    # 벤치마크: 성공 채널·체크리스트·성공 패턴
```

> [!tip] 미리 보고 가기
> `brand-example/` 폴더에 이미 완성된 예시 4개가 있습니다. **먼저 열어보고** "내 결과물도 이런 모양이 되겠구나"를 머릿속에 그리세요.

---

## 2. 실행 방법

### 방법 A — Claude Code (가장 쉬움)

프로젝트 폴더에서 Claude Code를 열고 입력:

```
/auto-video brand
```

또는 인터뷰 방식:

```
/create-c
```

그러면 director가 `brand-architect`부터 순서대로 4개 에이전트를 호출하며, **단계마다 당신에게 질문**합니다.

### 방법 B — Codex / Antigravity / Cursor

폴더를 열면 `AGENTS.md`가 자동 로드됩니다. 에이전트에게:

```
Phase 1 브랜드 세팅 시작해줘
```

---

## 3. 단계별로 무슨 일이 일어나나

### ① brand-architect — 캐릭터 설계

AI가 이런 질문을 합니다 (한 번에 하나씩):

> Q1. 이 채널은 어떤 주제를 다루나요? (테크/과학/역사/금융…)
> Q2. 주요 시청자는 누구인가요?
> Q3. 채널 분위기는? (유머 / 전문적 / 친근 / 세련 / 직접입력)
> Q4. 참고하고 싶은 채널이 있나요?

→ 답하면 **캐릭터 3안(A/B/C)**을 제안 → 하나 고르고 세부 조정 → 영문 이미지 기본 프롬프트(`nano_banana_base_prompt`) 생성 → 승인하면 `character.yaml` 저장.

> [!example] character.yaml 핵심 필드
> ```yaml
> persona:
>   name: ""              # 캐릭터 이름
>   personality: []       # 성격 키워드 3-5개
>   speaking_style: ""    # 말투
>   catchphrase: []       # 시그니처 표현
> visual:
>   art_style: ""         # 2D/3D/실사
>   nano_banana_base_prompt: ""  # 이미지 생성 기본 프롬프트(영문)
> consistency_rules:
>   always: []            # 항상 지킬 것
>   never: []             # 절대 금지 (최소 3개)
> ```

### ② narrative-designer — 서사/세계관

character.yaml을 읽은 뒤, 핵심 메시지·콘텐츠 형태(숏폼/롱폼)·에피소드 패턴을 물어보고 → **숏폼/롱폼 에피소드 공식**을 설계합니다.

> [!example] 숏폼 60초 공식 예시
> - 0-3초: 오프닝 훅
> - 4-20초: 문제/상황 전개
> - 21-45초: 핵심 내용
> - 46-55초: 반전/결론
> - 56-60초: CTA(좋아요/구독)

### ③ topic-strategist — 주제 전략

character + narrative를 읽고 → 대주제·세부영역·금지영역·업로드 빈도를 물어 → **콘텐츠 기둥 3~5개** + 에버그린 주제 5개+ + 트렌드 키워드 10개+ 를 도출.

### ④ benchmark-analyst — 벤치마크

성공 채널을 분석해 첫 3초·리텐션·썸네일·제목 체크리스트와 성공 패턴을 `benchmark.yaml`로 정리.

---

## 4. 체크포인트에서 당신이 할 일

각 에이전트가 끝나면 AI가 결과를 요약해 보여주고 묻습니다:

- **승인** → 다음 에이전트로
- **수정 요청** → "캐치프레이즈를 더 짧게" 같은 피드백 → 같은 에이전트 재실행
- **처음부터** → 빈 상태에서 재실행

> [!warning] 너무 완벽주의하지 마세요
> Phase 1은 나중에 언제든 고칠 수 있습니다. 80% 만족이면 승인하고 넘어가세요. 영상을 만들다 보면 뭘 고쳐야 할지 더 명확해집니다.

---

## 🛠️ 오늘의 실습

> [!todo] 따라 하기
> - [ ] `brand-example/`의 YAML 4개를 먼저 읽어본다
> - [ ] Claude Code에서 `/auto-video brand` (또는 `/create-c`) 실행
> - [ ] brand-architect 질문 4개에 답하고 캐릭터 1안 선택·승인
> - [ ] narrative → topic → benchmark 까지 4개 에이전트 모두 완료
> - [ ] `brand/` 폴더에 YAML 4개가 생겼는지 확인

> [!tip] 연습용 추천 채널 컨셉
> 처음이면 **숏폼 중심 + 단순 컨셉**으로 잡으세요. 예: "AI 도구를 귀여운 오리 캐릭터가 1분에 소개하는 채널". 단순할수록 Day 5~7이 쉬워집니다.

---

## ✅ 오늘의 테스트

### 실습 검증 (터미널)

```bash
cd /Users/woodncarpenter/Downloads/auto-video-toolkit
ls brand/                                    # ✅ 4개 yaml 존재
cat brand/character.yaml | grep -A1 "name"   # ✅ 캐릭터 이름이 채워짐
```

빈 필드가 남아 있으면 아직 미완성입니다.

### 개념 퀴즈

1. Phase 1은 얼마나 자주 하나?
2. narrative-designer는 작업 시작 시 무엇을 먼저 읽나?
3. character.yaml의 `consistency_rules.never`는 왜 중요한가?

> [!success]- 정답 펼치기
> 1. 채널당 1회.
> 2. `brand/character.yaml` (앞 에이전트 산출물). 없으면 brand-architect 먼저.
> 3. 브랜드를 보호하는 금지 규칙 — 모든 영상 생성 시 이 규칙이 프롬프트에 주입되어 일관성을 지킨다.

### 자가 점검
- [ ] `brand/` YAML 4개가 모두 채워졌다
- [ ] 체크포인트에서 승인/수정을 직접 해봤다
- [ ] 내 채널의 캐릭터 이름과 컨셉을 한 줄로 말할 수 있다

---

➡️ 다음: [[Day-5-Phase2-리서치와대본]] — 이제 실제 영상 만들기 시작!
