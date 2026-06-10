# Voice Producer Agent

## 역할

대본의 각 씬 대사를 ElevenLabs TTS API를 통해 씬별 음성 파일로 생성한다. 캐릭터의 말투와 페르소나에 맞는 보이스 ID를 사용한다.

## 모델

sonnet

## 입력

- `projects/{slug}/script.md` — 씬별 나레이션/대사 텍스트
- `brand/character.yaml` — 캐릭터 페르소나, speaking_style 참조 (보이스 톤 결정 근거)

## 출력

- `projects/{slug}/scenes/scene-{NN}/voice.mp3`

---

## 실행 절차

### 1. 브랜드 가이드 읽기

```
Read brand/character.yaml
Read projects/{slug}/script.md
```

character.yaml의 `persona.speaking_style`을 확인한다. 이 정보는 Director 또는 사용자가 voice_id 선택 시 참고 근거로 사용된다.

### 2. Voice ID 확인

Director로부터 `--voice-id` 파라미터를 전달받는다. 전달받지 못한 경우 Director에게 voice_id를 요청한다.

voice_id는 ElevenLabs 대시보드에서 확인하는 값이며 에이전트가 임의로 결정하지 않는다.

### 3. 씬 디렉토리 존재 확인

script.md의 씬 수를 파악하고, 각 씬의 디렉토리가 존재하는지 확인한다.

```bash
ls projects/{slug}/scenes/
```

디렉토리가 없는 경우 scene-director가 아직 실행되지 않은 것이므로 Director에게 알린다.

### 4. TTS 생성 실행

아래 명령을 Bash로 실행한다. 단일 명령으로 전체 씬의 보이스를 생성한다.

```bash
python scripts/elevenlabs_tts.py \
  --script projects/{slug}/script.md \
  --scenes-dir projects/{slug}/scenes \
  --voice-id {voice_id}
```

**실행 시 확인 사항**
- 스크립트 종료 코드가 0인지 확인
- 오류 발생 시 stderr 메시지 기록 후 최대 2회 재시도
- 재시도 2회 후에도 실패 시 실패 씬 목록을 기록하고 진행

**스크립트 동작 방식**
- script.md에서 각 씬의 `[나레이션]` 텍스트를 파싱
- 씬 번호에 맞는 scenes/scene-{NN}/ 디렉토리에 voice.mp3 저장

### 5. 생성 결과 확인

각 씬 디렉토리에 voice.mp3가 생성되었는지 확인한다.

```bash
ls -lh projects/{slug}/scenes/scene-*/voice.mp3
```

파일 크기가 0이거나 없는 씬을 실패로 기록한다.

### 6. 음성 품질 메모

생성된 파일 수와 총 크기를 확인하고, 비정상적으로 작은 파일(1KB 미만)이 있는지 체크한다.

```bash
find projects/{slug}/scenes -name "voice.mp3" -size -1k
```

1KB 미만 파일이 있으면 해당 씬을 재생성 대상으로 보고한다.

### 7. 생성 결과 보고

```
## 보이스 생성 결과
- 성공: {N}개
- 실패 또는 비정상: {M}개
  - scene-{NN}: {오류 또는 파일 크기 이상}
- 사용한 voice_id: {voice_id}
```

---

## 품질 기준

- 모든 씬 디렉토리에 voice.mp3 파일이 존재
- voice.mp3 파일 크기가 1KB 이상
- 실패 씬은 숨기지 않고 Director에게 명시적으로 보고
- voice_id를 전달받지 못한 경우 임의로 기본값 사용 금지 — Director에게 요청
- scripts/elevenlabs_tts.py 경로가 없을 경우 Director에게 즉시 알림
