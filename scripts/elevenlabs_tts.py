import argparse
import os
import re
from pathlib import Path


def split_script_to_scenes(script_text: str) -> list[dict]:
    """대본 텍스트를 ## Scene N 패턴으로 분할."""
    pattern = re.compile(r"##\s+Scene\s+(\d+)\s*\n(.*?)(?=##\s+Scene\s+\d+|\Z)", re.DOTALL)
    matches = pattern.findall(script_text)
    scenes = []
    for scene_number, content in matches:
        dialogue = content.strip()
        scenes.append({"scene_number": int(scene_number), "dialogue": dialogue})
    return scenes


def save_audio(audio_bytes: bytes, output_path: str) -> None:
    """바이트를 MP3 파일로 저장. 부모 디렉토리 자동 생성."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(audio_bytes)


def generate_voice(text: str, voice_id: str, output_path: str) -> None:
    """ElevenLabs API 호출 후 MP3 저장."""
    from elevenlabs import ElevenLabs

    api_key = os.environ.get("ELEVENLABS_API_KEY")
    client = ElevenLabs(api_key=api_key)

    audio_generator = client.text_to_speech.convert(
        voice_id=voice_id,
        text=text,
        model_id="eleven_multilingual_v2",
    )
    audio_bytes = b"".join(audio_generator)
    save_audio(audio_bytes, output_path)


def generate_all_voices(script_path: str, scenes_dir: str, voice_id: str) -> None:
    """script.md 전체를 읽어서 씬별로 보이스 일괄 생성."""
    script_text = Path(script_path).read_text(encoding="utf-8")
    scenes = split_script_to_scenes(script_text)

    for scene in scenes:
        scene_num = scene["scene_number"]
        dialogue = scene["dialogue"]
        output_path = os.path.join(scenes_dir, f"scene-{scene_num:02d}", "voice.mp3")
        generate_voice(dialogue, voice_id, output_path)
        print(f"Scene {scene_num} 보이스 생성 완료: {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ElevenLabs TTS 보이스 생성")
    parser.add_argument("--script", required=True, help="script.md 경로")
    parser.add_argument("--scenes-dir", required=True, help="scenes 디렉토리 경로")
    parser.add_argument("--voice-id", required=True, help="ElevenLabs voice ID")
    args = parser.parse_args()

    generate_all_voices(args.script, args.scenes_dir, args.voice_id)
