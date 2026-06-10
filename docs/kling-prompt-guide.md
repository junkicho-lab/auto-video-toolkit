# Kling AI 영상 생성 프롬프트 최적화 가이드

> 소스: fal.ai(공식 파트너), VEED, atlabs.ai, RunDiffusion, hixx.ai, Ambience AI 종합

---

## 1. 기본 프롬프트 구조

```
[피사체] + [피사체 묘사] + [동작/움직임] + [배경/씬] + [씬 묘사] + [카메라/조명/분위기]
```

**원칙:**
- 동시 동작 2개 이하 (복수 동작은 왜곡 유발)
- 숫자 사용 자제 ("5그루 나무" 같은 개수 명시 시 일관성 붕괴)
- 2.5 Turbo: 60단어 이하 / 2.6 Pro: 5~7개 환경 요소까지 허용

---

## 2. 물리 반응 및 자연스러운 움직임 개선

### 움직임을 구체적 단계로 분해

| 나쁜 예 | 좋은 예 |
|---|---|
| `the ball moves` | `the ball rolls forward, bounces once on the grass, then slows to a stop` |
| `he kicks the ball` | `his right foot swings back, makes contact with the ball, the ball arcs upward and forward` |
| `wear sunglasses` | `slowly raises her hand, grasps the sunglasses, places them on her face` |

### 물리 반응 향상 키워드
- `realistic physics`, `natural momentum`, `gravity-accurate`
- `gradual deceleration`, `smooth follow-through`
- `fabric ripples naturally`, `fluid dynamics`, `realistic bounce`
- 속도 수식어: `slowly`, `gently`, `smoothly`, `steadily` → 급격한 움직임 억제
- `then settles back` / `then comes to rest` → 움직임 끝 상태 명시 (99% 멈춤 현상 해결)

### 공 움직임 특화
```
The soccer ball is struck cleanly, rolls across the wet grass with realistic spin,
kicks up a small spray of water, and slows gradually near the goal line.
Natural ball physics, realistic momentum.
```

### 사람 운동 동작 특화
```
An athlete in mid-stride, arms pumping naturally at 90-degree angle,
feet landing heel-to-toe with realistic weight transfer.
Smooth, biomechanically accurate running motion.
```

---

## 3. 과도한 액션 억제

| 원인 | 해결책 |
|---|---|
| 열린 결말 동작 | 종료 상태 추가: `then settles`, `gradually stops` |
| 복수 동작 경쟁 | 동작 수 1~2개로 제한 |
| 모호한 공간 언어 | `positioned near`, `making contact with` 등 공간 명시 |
| 강도 미지정 | `slightly`, `gently`, `subtly`, `barely` 등 강도 수식어 추가 |

**억제 키워드:**
- `minimal camera movement`
- `subtle motion only`
- `gentle, restrained movement`
- `static background, only subject moves`
- `slow and deliberate motion`

---

## 4. Image-to-Video 모드 최적화

### 핵심: 이미지 내용을 재설명하지 말 것

이미지가 씬을 정의하므로 프롬프트는 **무엇이 움직이는지, 어떻게 움직이는지**에만 집중.

```
나쁜 예:
"A man in a blue shirt standing in a forest. He has brown hair and..."

좋은 예:
"Man slowly looks up toward the sky, light breeze moves his hair and shirt collar.
Background trees sway gently."
```

### Image-to-Video 전용 공식
```
[무엇이 움직이는가] + [어떻게 움직이는가] + [배경 움직임(있다면)] + [카메라 동작]
```

### 주의사항
- 워터마크, 텍스트 없는 클린 이미지 사용
- 움직임 방향을 이미지 구도와 일치 (인물이 오른쪽 보면 카메라도 오른쪽 패닝)
- Elements 기능: 참조 이미지 2~4장이 최적

---

## 5. 네거티브 프롬프트

> Kling의 네거티브 프롬프트는 Stable Diffusion 대비 **효과가 약함**. 긍정 프롬프트로 우회하는 것이 더 효과적.

### 고정 삽입 권장 목록

**품질:**
```
blur, motion blur, distortion, compression artifacts, pixelation,
low quality, poor lighting, flickering, noise, grain
```

**신체/물리 이상:**
```
extra limbs, deformed hands, morphing faces, unnatural physics,
body distortion, limb duplication, facial glitching
```

**영상 품질:**
```
watermark, text overlay, logo, subtitle, letterbox,
camera shake, unstable footage, jump cuts
```

---

## 6. 카메라 무브먼트 제어

### 전후 이동 (깊이감)
| 명령어 | 효과 |
|---|---|
| `slow dolly in` | 감정적 강조, 긴장감 |
| `dolly out` | 피사체 고립, 공간 확장 |
| `dolly zoom (vertigo effect)` | 배경 왜곡, 심리적 충격 |
| `slow push-in` | 집중, 친밀감 |

### 수평/수직 이동
| 명령어 | 효과 |
|---|---|
| `pan left / pan right` | 공간 탐색, 풍경 |
| `side tracking shot` | 달리는 피사체 추적 |
| `tilt up / tilt down` | 위압감, 규모 표현 |

### 회전/특수
| 명령어 | 효과 |
|---|---|
| `360-degree orbit around subject` | 캐릭터 소개, 제품 쇼케이스 |
| `handheld shaky cam` | 다큐멘터리, 긴박감 |
| `static locked-off shot` | 안정적, 관찰자 시점 |

### 초점/특수 기법
| 명령어 | 효과 |
|---|---|
| `rack focus from foreground to background` | 시선 유도 |
| `POV shot` | 몰입감 |
| `drone aerial shot` | 환경 설정 |
| `shallow depth of field` | 배경 분리 |

### 카메라 + 동작 조합 공식
```
[피사체] + [동작] + [배경] + [카메라 명령어] + [조명/분위기]
```

---

## 7. 모델별 최적화

| 모델 | 프롬프트 복잡도 | 특징 |
|---|---|---|
| **1.6 Standard** | 단순 (단일 피사체, 동작 1개) | Motion Brush 독점 |
| **2.5 Turbo** | 60단어 이하, 요소 3~4개 | 속도 최적화 |
| **2.6 Pro** | 요소 5~7개, 복잡 조명 가능 | 고품질, 세밀한 표현 |
| **3.0** | 멀티샷 스토리보드 (최대 6샷) | 씬 단위 연속 생성, 15초 지원 |

---

## 8. 프로젝트 적용 체크리스트

1. **image-to-video 시** 이미지 재설명 금지 — 움직임만 기술
2. **스포츠 씬** 물리 단계 분해 + `realistic physics, natural momentum`
3. **모든 동작 끝**에 `then settles` / `comes to rest` 추가
4. **네거티브 프롬프트** 고정 삽입: `morphing faces, extra limbs, unnatural physics, body distortion, flickering`
5. **카메라** 드라마틱 씬은 `slow dolly in`, 전체 씬은 `static locked-off shot`
6. **동시 동작 2개 이하** 유지

---

## 9. 금지 단어 필터

Kling은 설명 없이 특정 단어를 필터링함.
확인된 금지어: `chest`, `pig`, `exorcism`, `filthy` 등.
→ 동의어로 대체하거나 이미지 생성 후 animate 방식으로 우회.
