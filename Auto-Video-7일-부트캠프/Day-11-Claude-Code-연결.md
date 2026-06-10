---
title: Day 11 (심화) — 이 앱과 Claude Code 연결하기
type: lesson
day: 11
tags:
  - auto-video
  - 부트캠프
  - 심화
  - claude-code
  - mcp
  - 통합
est_time: 70분
prev: "[[Day-10-검증과-개선안]]"
next: "[[00-시작하기]]"
---

# Day 11 (심화) — 이 앱과 Claude Code 연결하기

> [!success] 이 노트의 목표
> 이 앱(autovideo)을 Claude Code와 연결하는 4가지 방식을 이해하고, 어떤 조합이 적합한지 판단합니다.

선행: [[Day-8-에이전트-하네스와-AI-Native]], [[Day-10-검증과-개선안]] · ⏱️ 70분 · 심화

---

## 결론 먼저

> **네, 연결 가능. 사실 이 앱은 원래 Claude Code용으로 설계됨** (CLAUDE.md, agents/*.md, director.md, /create-c가 증거).
> 우리가 만든 `autovideo`(Gemini 두뇌)는 "Claude Code 없이도 돌게" 한 갈래일 뿐, 둘은 **공존** 가능.

> [!note] 한 줄 관점
> [[Day-8-에이전트-하네스와-AI-Native]] 식으로: **연결 = 하네스의 "두뇌(LLM)"나 "입구(도구 노출)"를 Claude 쪽으로 바꿔 끼우는 것.**

---

## 현재 상태 점검

| 요소 | 현재 | 연결 관점 |
|---|---|---|
| CLAUDE.md | ✅ | Claude Code가 규칙으로 자동 로드 |
| agents/*.md | ✅ | 그대로 **서브에이전트**로 승격 가능 |
| 슬래시커맨드 | ⚠️ `commands/`(루트) | Claude Code는 **`.claude/commands/`** 를 봄 → 이동 필요 |
| scripts/*.py | ✅ | **MCP 도구**로 노출하면 Claude가 직접 호출 |
| autovideo 두뇌 | Gemini | **Claude로 교체** 가능 |

---

## 연결 4가지 방식

| 방식 | 핵심 | 👍 | 👎 |
|---|---|---|---|
| ① 슬래시커맨드/스킬 | `.claude/commands/*.md` → `/auto-video` | 즉시, 대화형 | 세션 안에서만 |
| ② 서브에이전트 | `.claude/agents/*.md` 자동/명시 호출 | 우리 12에이전트와 1:1 | 세션 안, 진짜 병렬 X |
| ③ **MCP 서버** | scripts를 도구로 노출, `.mcp.json` 등록 | 어디서나 재사용·긴작업 | 서버 구현 필요 |
| ④ **Agent SDK** | `claude-agent-sdk`로 Claude가 두뇌 | 독립 실행·CI/CD | 별도 키/루프 관리 |

*(+ 훅: 단계 후 자동 커밋 등 부수효과용)*

---

## 핵심 토의 — "두뇌를 누구로?"

```
(a) Claude Code 안에서      → 사람이 /auto-video + 서브에이전트
(b) MCP로 도구 노출         → Claude가 scripts를 도구로 호출
(c) Agent SDK로 두뇌 임베드  → autovideo가 Claude를 두뇌로 독립 실행
```

| | 두뇌 | 사람 위치 | 강점 |
|---|---|---|---|
| (a) | Claude Code | 안 | 즉시·대화형 |
| (b) | Claude Code | 어디서나 | 도구 재사용·긴작업 |
| (c) | Claude(SDK) | 터미널/자동화 | 독립·CI/CD |

> [!important] 추천: 하이브리드 (b)+(c) + provider 추상화
> 1. **MCP 서버**로 scripts 노출 (b)
> 2. `llm_client`에 **Claude provider 추가** → `autovideo --llm claude` (c의 경량판)
> 3. agents/commands를 `.claude/`로 정리 (a도 살림)
>
> → 하나의 앱이 **Gemini로도, Claude로도, Claude Code 안에서도** 돈다. [[Day-8]]의 "프롬프트 재사용 + 하네스 교체"의 완성형.

---

## 구현 메모 (이 부트캠프에서 실제로 한 것)

- **옵션 A (provider 추상화)**: `autovideo/llm_client.py`에 Gemini/Claude 분기 → `--llm {gemini,claude}` 추가.
- **옵션 B (MCP 서버)**: `autovideo/mcp_server.py`로 scripts를 도구 노출 + `.mcp.json`.

> 구체 클래스명·모델 ID는 버전마다 다르므로 구현 시 공식 문서(Anthropic SDK / MCP Python SDK)로 확인.

---

## ✅ 이해 점검
1. "연결"을 하네스 관점에서 한 문장으로?
2. MCP 서버 방식과 Agent SDK 방식의 차이는?
3. 추천 하이브리드 구성은?

> [!success]- 정답
> 1. 하네스의 두뇌(LLM) 또는 입구(도구 노출)를 Claude 쪽으로 바꿔 끼우는 것.
> 2. MCP=Claude Code가 내 scripts를 도구로 호출(두뇌는 Claude Code), Agent SDK=내 앱이 Claude를 두뇌로 임베드(독립 실행).
> 3. MCP로 도구 노출 + llm_client에 Claude provider 추가 + agents/commands를 .claude/로 정리.

⬅️ 돌아가기: [[00-시작하기]] · 관련: [[Day-8-에이전트-하네스와-AI-Native]], [[Day-10-검증과-개선안]]
