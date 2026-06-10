# autovideo — 독립 실행 CLI (Claude Code 불필요)

기존 toolkit은 **Claude Code가 지휘자(두뇌)** 였습니다.
이 패키지는 그 두뇌를 **코드로 직접 구현**해, 터미널 명령어만으로 영상 제작 파이프라인을 돌립니다.

```
당신 → autovideo create "주제" → 🧠 오케스트레이터(LLM API 직접 호출) → scripts/ 실행
```

## 구조

| 파일 | 역할 |
|---|---|
| `cli.py` | 명령어 진입점 (`doctor`/`status`/`brand`/`create`) |
| `orchestrator.py` | 🧠 두뇌 — Phase 판단·단계 진행·체크포인트 (director.md 로직) |
| `agent_runner.py` | `agents/*.md` 프롬프트 로드 → LLM 입력으로 변환 |
| `llm_client.py` | Gemini API 래퍼 (단발 생성 + 멀티턴 대화) |
| `env.py` | API 키·설정·brand 상태·slug 유틸 |

> 기존 `scripts/`, `agents/`, `config/`, `brand/` 는 그대로 재사용합니다. 이 폴더만 새로 추가됨.

## 설치

```bash
cd auto-video-toolkit
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"          # autovideo 명령어 등록 + 의존성
cp config/api-keys.env.example config/api-keys.env   # 키 입력
```

## 사용

```bash
autovideo doctor                  # 환경/키 점검 (가장 먼저)
autovideo status                  # 브랜드/프로젝트 상태
autovideo brand                   # Phase 1 — 대화형 브랜드 세팅
autovideo brand --only character  # 특정 brand 파일만 다시
autovideo create "AI가 거짓말하는 이유"            # Phase 2 — 텍스트(리서치/대본/씬)만
autovideo create "주제" --duration 59 --provider veo --media   # 미디어까지 전부
```

설치 없이 바로 실행도 가능:
```bash
python3 -m autovideo.cli doctor
```

## 동작 방식

- **Phase 1 (brand)**: 각 에이전트(.md)를 system instruction으로 LLM 대화 세션에 넣고,
  한 번에 한 질문씩 → 충분하면 `FINAL_YAML` 블록 출력 → 추출해 `brand/*.yaml` 저장.
- **Phase 2 (create)**: Video-First 계산 → researcher/scriptwriter/scene-director를
  단발 생성으로 실행(체크포인트마다 승인/수정/재생성) → `--media`면 기존 scripts로
  이미지/음성/합성까지.

## 체크포인트

각 단계 후: `[y] 승인  [e] 수정요청  [r] 재생성  [q] 중단`

## 현재 상태 (프로토타입)

- ✅ CLI 골격·두뇌·Phase 판단·체크포인트·Video-First 계산
- ✅ 의존성/키 없이도 `doctor`/`status`/가드 동작
- ⏳ 실제 LLM 호출(brand 위저드, create 텍스트 생성)은 **GEMINI_API_KEY + 설치** 필요
- ⏳ TODO: 모델명 검증, video-generator 연동, 진행률 표시 고도화

## 메모

`config/models.yaml`의 모델명(gemini-3-flash 등)이 실제 미존재할 수 있습니다.
그 경우 `--model gemini-2.5-flash` 또는 `AUTOVIDEO_MODEL` 환경변수로 덮어쓰세요.
