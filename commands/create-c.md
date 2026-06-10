# create-c: 콘텐츠 제작 시작

사용자에게 아래 질문을 순서대로 한다. 각 질문은 짧고 선택지 기반으로. 사용자가 "추천해줘"라고 하면 최적 옵션을 제안한다.

## 질문 플로우

### Q1. 채널/트랙
어떤 채널로 제작할까요?
- 애덕이 (한국어, 숏폼)
- 니치 밴딩 (영어, 롱폼)
- 새 채널

### Q2. 주제
이번 에피소드 주제가 뭔가요? (자유 입력)

### Q3. 영상 러닝타임
영상 길이를 얼마로 할까요?
- 숏폼: 59초 이내
- 롱폼: 3분 / 3분 30초 / 4분 / 5분
- 직접 입력

### Q4. 영상 provider
영상 생성 provider는? (config/models.yaml의 video_generation)
- Veo (Google Gemini, 8초/클립)
- Grok (xAI imagine, image-to-video)
- Kling (5·10초/클립, JWT 인증)
- Higgsfield (Segmind, 시네마틱 모션)

### Q5. 보이스
나레이션 보이스는?
- (채널 기본 보이스 자동 선택 — 니치밴딩: Narrator/George, 애덕이: 애덕이)
- 새 보이스 생성

## 질문 완료 후 자동 계산

```
클립 길이 = Q4에서 결정
씬 수 = 러닝타임(초) ÷ 클립 길이
총 단어 수 = 러닝타임(초) ÷ 60 × 150
씬당 단어 수 = 총 단어 수 ÷ 씬 수
```

계산 결과를 사용자에게 보여주고 확인받는다:
```
## 제작 설정 확인

- 채널: {채널}
- 주제: {주제}
- 러닝타임: {시간}
- 영상 도구: {도구} ({클립길이}초/클립)
- 씬 수: {N}씬
- 대본: ~{총단어}단어 (씬당 ~{씬단어}단어)
- 보이스: {보이스}

이대로 진행할까요?
```

## 승인 후 제작 시작

Video-First 플로우로 진행:

1. **리서치** — 주제 팩트 조사
2. **캐릭터 앵커** — 실존 인물이면 시대별 레퍼런스 이미지 생성 (인종/피부색 명시 필수) → `anchors/`
3. **씬 이미지 생성** — {N}장, 앵커 일관성 유지 → `images/scene-01.png` ~ `scene-{N}.png`
4. **영상 클립 생성** — {N}클립, 도구별 프롬프트 최적화 → `videos/scene-01.mp4` ~ `scene-{N}.mp4`
5. **대본 작성** — 씬 단위, 영문+한글 이중 생성 (영어 콘텐츠 시) → `script.md` + `script-ko.md`
6. **TTS 생성** — 씬 단위, 채널 고정 보이스 → `narration/scene-01.wav` ~ `scene-{N}.wav`
7. **SRT 자막** — 나레이션/자막 역할 분담 → `capcut-export/subtitles.srt`
8. **CapCut 프로젝트** — `capcut-project-gen.py`로 자동 생성

프로젝트 구조:
```
projects/{slug}/
├── scenes/
│   ├── images/       # scene-01.png ~ scene-{N}.png
│   └── videos/       # scene-01.mp4 ~ scene-{N}.mp4
├── anchors/          # 캐릭터 앵커 이미지
├── narration/        # scene-01.wav ~ scene-{N}.wav
├── script.md
├── script-ko.md
├── image-prompts.md
├── video-prompts.md
├── capcut-config.json
└── capcut-export/subtitles.srt
```

각 단계 완료 후 체크포인트에서 사용자 승인.
