"""MoviePy 합성/렌더링 스크립트.

씬별 비주얼(이미지/영상) + 보이스(MP3) → 최종 MP4 합성.
- 영상 씬: 그대로 사용 (인트로/아웃트로)
- 이미지 씬: 씬당 2-3장 이미지에 Ken Burns(줌인/줌아웃) 효과 적용
"""

import argparse
import os
import random
from pathlib import Path

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
VIDEO_EXTS = {".mp4", ".mov", ".webm", ".avi", ".mkv"}


def detect_scene_type(visual_path: str) -> str:
    ext = Path(visual_path).suffix.lower()
    if ext in IMAGE_EXTS:
        return "image"
    if ext in VIDEO_EXTS:
        return "video"
    raise ValueError(f"알 수 없는 비주얼 파일 형식: {ext} ({visual_path})")


def collect_scene_assets(scene_dir: Path) -> dict:
    """씬 디렉토리에서 비주얼/보이스 파일을 수집한다.

    이미지가 여러 장이면 images 리스트로 반환.
    영상이 있으면 video로 반환 (우선).
    """
    images = []
    video = None
    voice = None

    for f in sorted(scene_dir.iterdir()):
        ext = f.suffix.lower()
        if ext in VIDEO_EXTS and f.stem.startswith("visual"):
            video = str(f)
        elif ext in IMAGE_EXTS and (f.stem.startswith("visual") or f.stem.startswith("img")):
            images.append(str(f))
        elif ext in {".mp3", ".wav", ".ogg"} and f.stem == "voice":
            voice = str(f)

    return {
        "video": video,
        "images": sorted(images),
        "voice": voice,
        "type": "video" if video else ("image" if images else None),
    }


def validate_project_dir(project_dir: str) -> list[dict]:
    scenes_dir = Path(project_dir) / "scenes"
    if not scenes_dir.exists():
        return []

    scenes = []
    for scene_path in sorted(scenes_dir.iterdir()):
        if not scene_path.is_dir():
            continue
        assets = collect_scene_assets(scene_path)
        if assets["type"] and assets["voice"]:
            assets["name"] = scene_path.name
            scenes.append(assets)

    return scenes


def build_timeline(scenes: list[dict]) -> list[dict]:
    timeline = []
    for i, scene in enumerate(scenes):
        timeline.append({"index": i, **scene})
    return timeline


def ken_burns_clip(image_path: str, duration: float, target_size: tuple, effect: str = "auto") -> "VideoClip":
    """이미지에 Ken Burns(줌인/줌아웃) 효과를 적용한 클립을 생성한다.

    Args:
        image_path: 이미지 파일 경로
        duration: 클립 길이(초)
        target_size: (width, height) 출력 해상도
        effect: "zoom_in", "zoom_out", "auto" (자동 번갈아)
    """
    from moviepy import ImageClip
    import numpy as np

    w, h = target_size

    # 줌 범위: 1.0 ~ 1.15 (과하지 않게)
    if effect == "zoom_in":
        start_scale, end_scale = 1.0, 1.15
    elif effect == "zoom_out":
        start_scale, end_scale = 1.15, 1.0
    else:
        # auto: 랜덤
        if random.random() > 0.5:
            start_scale, end_scale = 1.0, 1.15
        else:
            start_scale, end_scale = 1.15, 1.0

    # 원본 비율 유지 + cover fit (화면을 채우고 넘치는 부분 크롭)
    from PIL import Image as PILImage
    orig = PILImage.open(image_path)
    orig_w, orig_h = orig.size
    orig.close()

    # 줌 여유분(1.2x) 포함하여 cover 스케일 계산
    cover_w = int(w * 1.2)
    cover_h = int(h * 1.2)
    scale_factor = max(cover_w / orig_w, cover_h / orig_h)
    new_w = int(orig_w * scale_factor)
    new_h = int(orig_h * scale_factor)

    base = ImageClip(image_path)
    base = base.resized((new_w, new_h))

    def make_frame(t):
        progress = t / max(duration, 0.001)
        scale = start_scale + (end_scale - start_scale) * progress

        # 현재 스케일에서의 크롭 영역
        crop_w = int(w / scale)
        crop_h = int(h / scale)

        # 얼굴 우선 크롭: 수평은 중앙, 수직은 상단 35% 기준
        frame = base.get_frame(0)
        fh, fw = frame.shape[:2]
        cx = (fw - crop_w) // 2
        cy = int((fh - crop_h) * 0.35)  # 상단 편향 — 인물 얼굴 유지

        cropped = frame[cy:cy + crop_h, cx:cx + crop_w]

        # 리사이즈
        from PIL import Image
        img = Image.fromarray(cropped)
        img = img.resize((w, h), Image.LANCZOS)
        return np.array(img)

    from moviepy import VideoClip
    clip = VideoClip(make_frame, duration=duration)
    clip = clip.with_fps(24)

    base.close()
    return clip


def render(project_dir: str, output_path: str, video_format: str = "long") -> str:
    """전체 씬을 합성하여 최종 영상을 렌더링한다."""
    from moviepy import (
        AudioFileClip,
        VideoFileClip,
        concatenate_videoclips,
    )

    scenes = validate_project_dir(project_dir)
    if not scenes:
        raise RuntimeError(f"프로젝트에 유효한 씬이 없습니다: {project_dir}")

    timeline = build_timeline(scenes)

    if video_format == "short":
        target_size = (1080, 1920)
    else:
        target_size = (1920, 1080)

    clips = []
    effects_cycle = ["zoom_in", "zoom_out"]

    for entry in timeline:
        audio = AudioFileClip(entry["voice"])
        duration = audio.duration

        if entry["type"] == "video":
            # 인트로/아웃트로: 영상 사용
            clip = VideoFileClip(entry["video"])
            if clip.duration < duration:
                loops = int(duration / clip.duration) + 1
                clip = concatenate_videoclips([clip] * loops).subclipped(0, duration)
            elif clip.duration > duration:
                clip = clip.subclipped(0, duration)
            clip = clip.resized(target_size)
            clip = clip.with_audio(audio)
            clips.append(clip)
            print(f"  {entry['name']}: 영상 {duration:.1f}초")

        elif entry["type"] == "image":
            images = entry["images"]
            num_images = len(images)

            if num_images == 0:
                continue

            # 이미지별 시간 배분 (균등)
            per_image_dur = duration / num_images

            img_clips = []
            for j, img_path in enumerate(images):
                effect = effects_cycle[j % 2]
                img_clip = ken_burns_clip(img_path, per_image_dur, target_size, effect)
                img_clips.append(img_clip)

            scene_clip = concatenate_videoclips(img_clips, method="compose")
            scene_clip = scene_clip.with_audio(audio)
            clips.append(scene_clip)
            print(f"  {entry['name']}: 이미지 {num_images}장 × Ken Burns ({duration:.1f}초)")

    final = concatenate_videoclips(clips, method="compose")

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    final.write_videofile(
        str(out),
        fps=24,
        codec="libx264",
        audio_codec="aac",
        threads=4,
    )

    print(f"\n렌더링 완료: {out}")
    print(f"총 길이: {final.duration:.1f}초 ({final.duration / 60:.1f}분)")

    final.close()
    for clip in clips:
        clip.close()

    return str(out)


def main():
    parser = argparse.ArgumentParser(description="MoviePy 영상 합성 (Ken Burns)")
    parser.add_argument("--project", required=True, help="프로젝트 디렉토리 경로")
    parser.add_argument(
        "--format",
        choices=["short", "long"],
        default="long",
        help="영상 포맷 (short=9:16, long=16:9)",
    )
    parser.add_argument("--output", default=None, help="출력 경로")
    args = parser.parse_args()

    output = args.output or str(Path(args.project) / "output" / "final.mp4")
    render(args.project, output, args.format)


if __name__ == "__main__":
    main()
