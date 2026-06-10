"""영상 제작 파이프라인.

scene-prompts.md의 프롬프트로 Veo 3 영상 + ElevenLabs TTS 생성 후 MoviePy로 합성.
"""

import os
import re
import time
import argparse
from pathlib import Path

import yaml


def load_env():
    """config/api-keys.env에서 환경변수 로드."""
    env_path = Path("config/api-keys.env")
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    # 인라인 주석( ' #...') 제거 + 따옴표 제거 + 예시값 무시
                    val = re.split(r"\s+#", val, maxsplit=1)[0].strip().strip('"').strip("'")
                    if val and not val.lower().startswith(("your-", "your_", "<")):
                        os.environ.setdefault(key.strip(), val)


def parse_scene_prompts(prompts_path: str) -> list[dict]:
    """scene-prompts.md에서 씬별 프롬프트를 파싱한다."""
    text = Path(prompts_path).read_text(encoding="utf-8")
    scenes = []

    # ### Scene N: Title 패턴으로 분할
    pattern = r"### Scene (\d+): (.+?)(?=\n)"
    parts = re.split(r"(?=### Scene \d+:)", text)

    for part in parts:
        match = re.match(r"### Scene (\d+): (.+)", part)
        if not match:
            continue

        scene_num = int(match.group(1))
        title = match.group(2).strip()

        # Duration 추출
        dur_match = re.search(r"\*\*Duration:\*\*\s*(\d+)\s*seconds", part)
        duration = int(dur_match.group(1)) if dur_match else 30

        # Prompt 추출
        prompt_match = re.search(r"\*\*Prompt:\*\*\n(.+?)(?=\n\*\*Audio Direction)", part, re.DOTALL)
        prompt = prompt_match.group(1).strip() if prompt_match else ""

        # Audio Direction 추출
        audio_match = re.search(r"\*\*Audio Direction:\*\*\n(.+?)(?=\n\*\*Consistency)", part, re.DOTALL)
        audio = audio_match.group(1).strip() if audio_match else ""

        scenes.append({
            "scene_number": scene_num,
            "title": title,
            "duration_sec": duration,
            "prompt": prompt,
            "audio_direction": audio,
        })

    return scenes


def parse_narrations(script_path: str) -> list[dict]:
    """script.md에서 씬별 나레이션 텍스트를 파싱한다."""
    text = Path(script_path).read_text(encoding="utf-8")
    narrations = []

    # 헤더 포맷 허용: "## Scene 1", "## Scene 1: 제목", "## Scene 7 (마지막)"
    parts = re.split(r"(?=## Scene \d+\b)", text)
    for part in parts:
        match = re.match(r"## Scene (\d+)\b", part)
        if not match:
            continue

        scene_num = int(match.group(1))

        # 나레이션 추출 — 포맷: **[나레이션]** 텍스트... (다음 **[...] 지시 블록 전까지)
        nar_match = re.search(
            r"\*\*\\?\[나레이션\\?\]?\*{0,2}\s*(.+?)(?=\n\*\*\\?\[|\Z)",
            part, re.DOTALL,
        )
        narration = nar_match.group(1).strip() if nar_match else ""

        narrations.append({
            "scene_number": scene_num,
            "narration": narration,
        })

    return narrations


def generate_videos(scenes: list[dict], output_dir: str, model: str = "veo-3.0-fast-generate-001"):
    """Veo 3로 모든 씬의 영상을 생성한다."""
    from google import genai

    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    operations = []

    print(f"\n=== Veo 3 영상 생성 시작 ({len(scenes)}씬) ===\n")

    for scene in scenes:
        scene_dir = Path(output_dir) / f"scene-{scene['scene_number']:02d}"
        scene_dir.mkdir(parents=True, exist_ok=True)

        video_path = scene_dir / "visual.mp4"
        if video_path.exists():
            print(f"  Scene {scene['scene_number']:02d}: 이미 존재 — 스킵")
            operations.append({"scene": scene, "path": str(video_path), "operation": None, "done": True})
            continue

        print(f"  Scene {scene['scene_number']:02d}: 생성 요청 중...")
        max_retries = 3
        for attempt in range(max_retries):
            try:
                operation = client.models.generate_videos(
                    model=model,
                    prompt=scene["prompt"],
                )
                print(f"    → Operation: {operation.name}")
                operations.append({
                    "scene": scene,
                    "path": str(video_path),
                    "operation": operation,
                    "done": False,
                })
                # API 속도 제한 방지 — 요청 간 30초 대기
                time.sleep(30)
                break
            except Exception as e:
                error_str = str(e)
                if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                    wait = 60 * (attempt + 1)
                    print(f"    → Rate limit — {wait}초 대기 후 재시도 ({attempt+1}/{max_retries})")
                    time.sleep(wait)
                else:
                    print(f"    → 에러: {e}")
                    operations.append({"scene": scene, "path": str(video_path), "operation": None, "done": False, "error": error_str})
                    break
        else:
            print(f"    → 최대 재시도 초과")
            operations.append({"scene": scene, "path": str(video_path), "operation": None, "done": False, "error": "max retries exceeded"})

    # 완료 대기
    print(f"\n=== 영상 생성 대기 중... ===\n")
    pending = [op for op in operations if op["operation"] and not op["done"]]

    while pending:
        for op in pending:
            try:
                updated = client.operations.get(op["operation"])
                if updated.done:
                    op["done"] = True
                    # 다운로드
                    if updated.response and updated.response.generated_videos:
                        video = updated.response.generated_videos[0]
                        video_data = client.files.download(file=video.video)
                        # video_data는 bytes 객체
                        with open(op["path"], "wb") as f:
                            if hasattr(video_data, "save"):
                                video_data.save(f)
                            elif isinstance(video_data, bytes):
                                f.write(video_data)
                            else:
                                # iterator인 경우
                                for chunk in video_data:
                                    f.write(chunk)
                        fsize = Path(op["path"]).stat().st_size
                        print(f"  Scene {op['scene']['scene_number']:02d}: 완료 ✓ ({fsize//1024}KB)")
                    else:
                        print(f"  Scene {op['scene']['scene_number']:02d}: 영상 없음")
                        op["error"] = "No video in response"
            except Exception as e:
                print(f"  Scene {op['scene']['scene_number']:02d}: 폴링 에러 — {e}")

        pending = [op for op in operations if op["operation"] and not op["done"]]
        if pending:
            print(f"  ... {len(pending)}개 대기 중")
            time.sleep(15)

    success = sum(1 for op in operations if op["done"] and "error" not in op)
    print(f"\n영상 생성 완료: {success}/{len(scenes)}\n")
    return operations


def generate_voices(narrations: list[dict], output_dir: str, voice_id: str = "EXAVITQu4vr4xnSDxMaL"):
    """ElevenLabs로 모든 씬의 보이스를 생성한다."""
    from elevenlabs import ElevenLabs

    client = ElevenLabs(api_key=os.environ["ELEVENLABS_API_KEY"])

    print(f"\n=== ElevenLabs TTS 생성 시작 ({len(narrations)}씬) ===\n")

    for nar in narrations:
        scene_dir = Path(output_dir) / f"scene-{nar['scene_number']:02d}"
        scene_dir.mkdir(parents=True, exist_ok=True)

        voice_path = scene_dir / "voice.mp3"
        if voice_path.exists():
            print(f"  Scene {nar['scene_number']:02d}: 이미 존재 — 스킵")
            continue

        if not nar["narration"]:
            print(f"  Scene {nar['scene_number']:02d}: 나레이션 없음 — 스킵")
            continue

        print(f"  Scene {nar['scene_number']:02d}: TTS 생성 중...")
        try:
            audio = client.text_to_speech.convert(
                voice_id=voice_id,
                text=nar["narration"],
                model_id="eleven_multilingual_v2",
                voice_settings={
                    "stability": 0.6,
                    "similarity_boost": 0.75,
                    "speed": 0.82,
                },
            )
            with open(voice_path, "wb") as f:
                for chunk in audio:
                    f.write(chunk)
            print(f"    → 완료 ✓")
        except Exception as e:
            print(f"    → 에러: {e}")

        time.sleep(1)  # 속도 제한 방지

    print(f"\nTTS 생성 완료\n")


def composite(project_dir: str, video_format: str = "long"):
    """MoviePy로 최종 합성."""
    from moviepy import (
        AudioFileClip,
        ImageClip,
        VideoFileClip,
        concatenate_videoclips,
    )

    scenes_dir = Path(project_dir) / "scenes"
    output_dir = Path(project_dir) / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n=== MoviePy 합성 시작 ===\n")

    # 씬 수집
    scene_dirs = sorted(scenes_dir.iterdir())
    clips = []

    for scene_path in scene_dirs:
        if not scene_path.is_dir():
            continue

        visual = None
        voice = None

        for f in scene_path.iterdir():
            if f.stem == "visual" and f.suffix in (".mp4", ".mov", ".webm"):
                visual = f
            elif f.stem == "voice" and f.suffix in (".mp3", ".wav"):
                voice = f

        if not visual or not voice:
            print(f"  {scene_path.name}: 비주얼 또는 보이스 누락 — 스킵")
            continue

        print(f"  {scene_path.name}: 합성 중...")

        audio = AudioFileClip(str(voice))
        video = VideoFileClip(str(visual))

        # 비디오 길이를 오디오에 맞춤
        if video.duration < audio.duration:
            # 비디오가 짧으면 마지막 프레임 유지
            video = video.with_effects([lambda c: c.time_transform(lambda t: min(t, video.duration - 0.1))])
            video = video.with_duration(audio.duration)
        elif video.duration > audio.duration:
            video = video.subclipped(0, audio.duration)

        video = video.with_audio(audio)
        clips.append(video)

    if not clips:
        print("합성할 클립이 없습니다!")
        return

    # 해상도
    if video_format == "short":
        target_size = (1080, 1920)
    else:
        target_size = (1920, 1080)

    # 합성
    final = concatenate_videoclips(clips, method="compose")
    output_path = output_dir / "final.mp4"

    final.write_videofile(
        str(output_path),
        fps=24,
        codec="libx264",
        audio_codec="aac",
        threads=4,
    )

    print(f"\n합성 완료: {output_path}")
    print(f"총 길이: {final.duration:.1f}초 ({final.duration/60:.1f}분)")

    final.close()
    for clip in clips:
        clip.close()


def main():
    parser = argparse.ArgumentParser(description="영상 제작 파이프라인")
    parser.add_argument("--project", default="projects/2026-03-24-senior-content", help="프로젝트 디렉토리")
    parser.add_argument("--step", choices=["all", "video", "voice", "composite"], default="all")
    parser.add_argument("--model", default="veo-3.0-fast-generate-001", help="Veo 모델")
    parser.add_argument("--voice-id", default="EXAVITQu4vr4xnSDxMaL", help="ElevenLabs voice ID")
    parser.add_argument("--format", choices=["short", "long"], default="long")
    args = parser.parse_args()

    load_env()

    prompts_path = Path(args.project) / "scene-prompts.md"
    script_path = Path(args.project) / "script.md"
    scenes_dir = Path(args.project) / "scenes"

    scenes = parse_scene_prompts(str(prompts_path))
    narrations = parse_narrations(str(script_path))

    print(f"프로젝트: {args.project}")
    print(f"씬 수: {len(scenes)} (프롬프트), {len(narrations)} (나레이션)")
    print(f"모델: {args.model}")
    print(f"보이스: {args.voice_id}")

    if args.step in ("all", "video"):
        generate_videos(scenes, str(scenes_dir), args.model)

    if args.step in ("all", "voice"):
        generate_voices(narrations, str(scenes_dir), args.voice_id)

    if args.step in ("all", "composite"):
        composite(args.project, args.format)


if __name__ == "__main__":
    main()
