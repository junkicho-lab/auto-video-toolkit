# CapCut 프로젝트 자동 생성 가이드

> 이 문서는 Claude Code 세션에서 CapCut 프로젝트를 코드로 생성할 때 참조하는 가이드다.
> 스크립트: `scripts/capcut-project-gen.py`

---

## 1. 핵심 제약: macOS 샌드박스

CapCut은 macOS 샌드박스 앱 (`com.lemon.lvoverseas`)이다.

**`~/Movies/CapCut/` 외부 파일에 접근 불가.** 절대 경로를 JSON에 넣어도 CapCut에서 "파일에 액세스할 수 없음" 오류가 발생한다.

해결: 모든 소재 파일(MP4, WAV, SRT)을 프로젝트 `Resources/` 폴더에 **복사**한 후 해당 경로를 사용. `capcut-project-gen.py`가 자동으로 처리한다.

---

## 2. 디렉토리 구조

```
~/Movies/CapCut/User Data/Projects/com.lveditor.draft/
├── {프로젝트명}/
│   ├── draft_info.json          ← 타임라인 전체 데이터 (핵심)
│   ├── draft_meta_info.json     ← 프로젝트 메타 + 소재 임포트 목록
│   └── Resources/               ← 소재 파일 복사본 (MP4, WAV 등)
```

- `draft_info.json` — 트랙, 세그먼트, 머티리얼 전부 여기에
- `draft_meta_info.json` — CapCut이 프로젝트 목록에 표시하는 데 필요
- `Resources/` — 소재 파일 실체. 이 안에 없으면 CapCut이 못 읽음

---

## 3. 시간 단위

**모든 시간값은 마이크로초 (microsecond).**

```
1초 = 1,000,000
1분 = 60,000,000
5.5초 = 5,500,000
```

변환 함수:
```python
def sec_to_us(sec): return int(float(sec) * 1_000_000)
def us_to_sec(us): return us / 1_000_000
```

---

## 4. draft_info.json 핵심 구조

```json
{
  "canvas_config": { "width": 1920, "height": 1080, "ratio": "original" },
  "fps": 30.0,
  "duration": 전체_duration_us,
  "tracks": [ ... ],           // 트랙 배열 (비디오, 오디오, 텍스트)
  "materials": { ... },        // 머티리얼 저장소 (모든 소재 정보)
  "id": "UUID",
  "name": "프로젝트명"
}
```

### 4.1 tracks → segments 관계

```
tracks[0] (video)  → segments[] → 각 segment.material_id → materials.videos[]
tracks[1] (audio)  → segments[] → 각 segment.material_id → materials.audios[]
tracks[2] (text)   → segments[] → 각 segment.material_id → materials.texts[]
```

각 세그먼트는 `material_id`로 머티리얼을 참조하고, `extra_material_refs`로 부속 머티리얼(speed, placeholder 등)을 참조한다.

### 4.2 세그먼트 타입별 extra_material_refs (필수)

이걸 틀리면 CapCut이 프로젝트를 열다 크래시한다.

**Video segment — 6개:**
```
[speed_id, placeholder_info_id, canvas_id, sound_channel_mapping_id, material_color_id, vocal_separation_id]
```

**Audio segment — 5개:**
```
[speed_id, placeholder_info_id, beat_id, sound_channel_mapping_id, vocal_separation_id]
```

**Text segment — 1개:**
```
[material_animation_id]
```

### 4.3 세그먼트 시간 배치

```json
{
  "source_timerange": { "duration": 5000000, "start": 0 },
  "target_timerange": { "duration": 5000000, "start": 10000000 }
}
```

- `source_timerange` — 원본 소재에서 어디부터 어디까지 사용하는지
- `target_timerange` — 타임라인에서 어디에 배치하는지
  - `start` = 타임라인상 시작 위치 (마이크로초)
  - `duration` = 타임라인에서 차지하는 길이

비디오를 순차 배치하려면:
```python
cursor = 0
for each video:
    segment.target_timerange.start = cursor
    segment.target_timerange.duration = video_duration
    cursor += video_duration
```

---

## 5. materials 버킷

`materials`는 40개 이상의 배열 키를 가진 거대한 객체다. 주요 버킷:

| 버킷 | 용도 | 세그먼트 연결 |
|------|------|-------------|
| `videos` | 비디오 파일 정보 | video segment → material_id |
| `audios` | 오디오 파일 정보 | audio segment → material_id |
| `texts` | 텍스트/자막 정보 | text segment → material_id |
| `speeds` | 재생 속도 | 모든 segment → extra_material_refs |
| `placeholder_infos` | 플레이스홀더 | 모든 segment → extra_material_refs |
| `canvases` | 캔버스 배경 | video segment → extra_material_refs |
| `sound_channel_mappings` | 오디오 채널 | video/audio → extra_material_refs |
| `material_colors` | 색상 보정 | video segment → extra_material_refs |
| `vocal_separations` | 보컬 분리 | video/audio → extra_material_refs |
| `beats` | 비트 정보 | audio segment → extra_material_refs |
| `material_animations` | 애니메이션 | text segment → extra_material_refs |

**빈 배열이라도 모든 버킷 키가 존재해야 한다.** 누락되면 CapCut이 프로젝트를 못 연다.

전체 버킷 키 목록 (알파벳순):
```
ai_translates, audio_balances, audio_effects, audio_fades, audio_pannings,
audio_pitch_shifts, audio_track_indexes, audios, beats, canvases, chromas,
color_curves, common_mask, digital_human_model_dressing, digital_humans,
drafts, effects, flowers, green_screens, handwrites, hsl, hsl_curves,
images, log_color_wheels, loudnesses, manual_beautys, manual_deformations,
material_animations, material_colors, multi_language_refs, placeholder_infos,
placeholders, plugin_effects, primary_color_wheels, realtime_denoises,
shapes, smart_crops, smart_relights, sound_channel_mappings, speeds,
stickers, tail_leaders, text_templates, texts, time_marks, transitions,
video_effects, video_radius, video_shadows, video_strokes, video_trackings,
videos, vocal_beautifys, vocal_separations
```

---

## 6. 자막 (Text Material)

### 자동 생성의 한계

CapCut의 텍스트 material `content` 필드는 **중첩 JSON 문자열**이다:

```json
{
  "content": "{\"styles\":[{\"fill\":{\"content\":{\"solid\":{\"color\":[1,1,1]},\"render_type\":\"solid\"}},\"range\":[0,5],\"size\":5.0,\"font\":{\"path\":\"/Applications/CapCut.app/.../en.ttf\",\"id\":\"\"}}],\"text\":\"안녕하세요\"}"
}
```

이 형식을 코드로 생성할 수는 있지만, CapCut이 자체적으로 렌더링하는 텍스트 레이아웃과 100% 일치시키기 어렵다.

### 권장 방식: SRT 수동 임포트

1. `voice/subtitles.srt`를 SRT 표준 형식으로 생성
2. CapCut에서 "자막 > 로컬 자막 가져오기"로 임포트
3. CapCut 내에서 스타일 일괄 적용

`capcut-project-gen.py`로 텍스트 세그먼트를 넣으면 타이밍은 맞지만, **호흡 단위로 자연스럽게 분리하려면 사용자가 수동으로 편집하는 게 현실적**이다.

---

## 7. capcut-project-gen.py 사용법

### config.json 작성

```json
{
  "name": "EP3-에이전트와MCP-v3",
  "fps": 30,
  "canvas": { "width": 1920, "height": 1080 },
  "video": [
    "/abs/path/seg-01.mp4",
    "/abs/path/seg-02.mp4"
  ],
  "audio": [
    { "path": "/abs/path/scene-01.wav", "start": 0 },
    { "path": "/abs/path/scene-02.wav", "start": 35.2 },
    "/abs/path/scene-03.wav"
  ],
  "subtitle": "/abs/path/subtitles.srt",
  "subtitle_style": {
    "font_size": 5.0,
    "color": [1, 1, 1],
    "position_y": -0.8,
    "scale": 0.65
  }
}
```

| 필드 | 필수 | 설명 |
|------|------|------|
| `name` | O | CapCut 프로젝트명 (폴더명이 됨) |
| `fps` | X | 기본 30 |
| `canvas` | X | 기본 1920x1080 |
| `video` | O | MP4 파일 절대 경로 배열. 타임라인에 순차 배치 |
| `audio` | X | WAV 파일. 문자열 또는 `{path, start(초)}` 객체 |
| `subtitle` | X | SRT 파일 경로 |
| `subtitle_style` | X | 자막 스타일 오버라이드 |

### audio 배치 규칙

- 문자열만 넣으면 순차 배치 (이전 오디오 끝난 직후)
- `{"path": "...", "start": 초}` 형태면 지정한 시간에 배치
- 비디오와 별도 트랙이므로 시작 시간이 비디오와 다를 수 있음

### 실행

```bash
python3 scripts/capcut-project-gen.py config.json
```

실행하면:
1. `~/Movies/CapCut/User Data/Projects/com.lveditor.draft/{name}/` 생성
2. 모든 소재 파일을 `Resources/`에 복사
3. `draft_info.json`, `draft_meta_info.json` 생성
4. CapCut을 열면 프로젝트 목록에 표시됨

### ffprobe 필수

스크립트가 `ffprobe`로 각 파일의 duration, 해상도, 오디오 유무를 자동 감지한다. `ffprobe`가 PATH에 있어야 한다.

```bash
# 확인
which ffprobe
# 없으면
brew install ffmpeg
```

---

## 8. 흔한 실수와 해결

### "파일에 액세스할 수 없음"
- **원인**: 소재 파일이 `~/Movies/CapCut/` 외부에 있음
- **해결**: `Resources/` 폴더에 복사. `capcut-project-gen.py`는 자동으로 함

### CapCut이 프로젝트를 못 열거나 크래시
- **원인 1**: `extra_material_refs` 개수가 안 맞음 (video=6개, audio=5개, text=1개)
- **원인 2**: `materials` 버킷에 키가 누락됨 (빈 배열이라도 있어야 함)
- **원인 3**: `material_id`가 실제 머티리얼과 매칭 안 됨
- **해결**: `capcut-project-gen.py`를 사용하면 이 문제가 발생하지 않음

### 프로젝트가 CapCut 목록에 안 나옴
- **원인**: CapCut이 실행 중일 때 프로젝트를 생성함
- **해결**: CapCut을 종료하고 스크립트 실행 → CapCut 재실행

### 자막이 안 보임 / 깨짐
- **원인**: `content` 필드의 중첩 JSON 문자열 형식 오류
- **해결**: SRT를 CapCut에서 수동 임포트하는 것을 권장

### 오디오 싱크가 안 맞음
- **원인**: `target_timerange.start`가 비디오와 맞지 않음
- **해결**: audio config에 `"start": 초` 값을 명시적으로 지정

---

## 9. 수동 편집이 필요한 작업

자동 생성 후 CapCut에서 수동으로 해야 하는 것들:

1. **SRT 자막 임포트** — "자막 > 로컬 자막 가져오기"
2. **자막 호흡 단위 편집** — 자동 SRT(청크 단위)를 자연스러운 호흡 단위로 분리
3. **비디오/오디오 미세 싱크 조정** — 0.1~0.3초 단위 미세 조정
4. **전환 효과 추가** — 코드 생성은 가능하나 CapCut 내장 이펙트 선택이 더 빠름
5. **BGM 추가** — CapCut 내장 음악 라이브러리에서 선택

---

## 10. 새 프로젝트 생성 체크리스트

```
1. [ ] 비디오 MP4 파일들 준비 (절대 경로 확인)
2. [ ] 오디오 WAV 파일들 준비 (씬별 또는 전체)
3. [ ] SRT 자막 파일 준비 (선택)
4. [ ] config.json 작성
5. [ ] ffprobe 설치 확인 (which ffprobe)
6. [ ] CapCut 종료
7. [ ] python3 scripts/capcut-project-gen.py config.json 실행
8. [ ] CapCut 실행 → 프로젝트 목록에서 확인
9. [ ] SRT 수동 임포트 (필요 시)
10. [ ] 싱크 미세 조정
```
