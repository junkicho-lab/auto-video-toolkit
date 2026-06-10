#!/usr/bin/env python3
"""
capcut-project-gen.py — CapCut 프로젝트 자동 생성기

MP4 세그먼트 + WAV 오디오 + SRT 자막 → CapCut 프로젝트 폴더 생성.
CapCut을 열면 프로젝트 목록에 바로 표시됨.

Usage:
  python3 capcut-project-gen.py config.json

config.json 예시:
{
  "name": "EP2-슬래시커맨드",
  "fps": 30,
  "canvas": { "width": 1920, "height": 1080 },
  "video": [
    "/abs/path/seg-01.mp4",
    "/abs/path/seg-02.mp4"
  ],
  "audio": [
    { "path": "/abs/path/voice-01.wav", "start": 0 },
    { "path": "/abs/path/voice-02.wav", "start": 15.5 },
    "/abs/path/voice-03.wav"
  ],
  "subtitle": "/abs/path/subtitles.srt",
  "subtitle_style": {
    "font_size": 5.0,
    "color": [1, 1, 1],
    "position_y": -0.8,
    "scale": 0.65
  }
}

- video: 경로 배열 → 타임라인에 순차 배치 (duration ffprobe 자동 감지)
- audio: 경로 또는 {path, start(초)} 배열 → start 생략 시 순차 배치
- subtitle: SRT 파일 경로 (선택)
- subtitle_style: 자막 스타일 (선택)
"""

import json
import uuid
import os
import sys
import subprocess
import time
import re
import shutil
from pathlib import Path

CAPCUT_DRAFTS = Path.home() / "Movies" / "CapCut" / "User Data" / "Projects" / "com.lveditor.draft"
CAPCUT_FONT = "/Applications/CapCut.app/Contents/Resources/Font/SystemFont/en.ttf"


# ─── Utilities ───────────────────────────────────────────────

def new_id():
    return str(uuid.uuid4()).upper()


def sec_to_us(sec):
    return int(float(sec) * 1_000_000)


def us_to_sec(us):
    return us / 1_000_000


def probe_file(path):
    """ffprobe로 파일 정보 추출 → {duration_us, width, height, has_audio}"""
    r = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json",
         "-show_streams", "-show_format", str(path)],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        raise RuntimeError(f"ffprobe 실패: {path}")
    d = json.loads(r.stdout)
    dur = sec_to_us(float(d["format"]["duration"]))
    w, h, has_audio = 1920, 1080, False
    for s in d.get("streams", []):
        if s.get("codec_type") == "video":
            w = s.get("width", 1920)
            h = s.get("height", 1080)
        if s.get("codec_type") == "audio":
            has_audio = True
    return {"duration_us": dur, "width": w, "height": h, "has_audio": has_audio}


def parse_srt(srt_path):
    """SRT 파일 파싱 → [{text, start_us, duration_us}, ...]"""
    content = Path(srt_path).read_text(encoding="utf-8")
    blocks = re.split(r"\n\s*\n", content.strip())
    result = []
    for block in blocks:
        lines = block.strip().split("\n")
        if len(lines) < 3:
            continue
        m = re.match(
            r"(\d{2}):(\d{2}):(\d{2})[,.](\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2})[,.](\d{3})",
            lines[1],
        )
        if not m:
            continue
        g = [int(x) for x in m.groups()]
        start_ms = g[0] * 3600000 + g[1] * 60000 + g[2] * 1000 + g[3]
        end_ms = g[4] * 3600000 + g[5] * 60000 + g[6] * 1000 + g[7]
        text = "\n".join(lines[2:])
        result.append({
            "text": text,
            "start_us": start_ms * 1000,
            "duration_us": (end_ms - start_ms) * 1000,
        })
    return result


# ─── Material Factories ─────────────────────────────────────

def make_speed():
    mid = new_id()
    return mid, {"curve_speed": None, "id": mid, "mode": 0, "speed": 1.0, "type": "speed"}


def make_placeholder_info():
    mid = new_id()
    return mid, {
        "error_path": "", "error_text": "", "id": mid,
        "meta_type": "none", "res_path": "", "res_text": "",
        "type": "placeholder_info",
    }


def make_canvas():
    mid = new_id()
    return mid, {
        "album_image": "", "blur": 0.0, "color": "", "id": mid,
        "image": "", "image_id": "", "image_name": "",
        "source_platform": 0, "team_id": "", "type": "canvas_color",
    }


def make_sound_channel_mapping():
    mid = new_id()
    return mid, {"audio_channel_mapping": 0, "id": mid, "is_config_open": False, "type": "none"}


def make_material_color():
    mid = new_id()
    return mid, {
        "gradient_angle": 90.0, "gradient_colors": [], "gradient_percents": [],
        "height": 0.0, "id": mid, "is_color_clip": False, "is_gradient": False,
        "solid_color": "", "width": 0.0,
    }


def make_vocal_separation():
    mid = new_id()
    return mid, {
        "choice": 0, "enter_from": "", "final_algorithm": "", "id": mid,
        "production_path": "", "removed_sounds": [], "time_range": None,
        "type": "vocal_separation",
    }


def make_beat():
    mid = new_id()
    return mid, {
        "ai_beats": {
            "beats_path": "", "beats_url": "",
            "melody_path": "", "melody_percents": [], "melody_url": "",
        },
        "enable_ai_beats": False, "gear": 404, "gear_count": 0,
        "id": mid, "mode": 404, "type": "beats",
        "user_beats": [], "user_delete_ai_beats": None,
    }


def make_material_animation():
    mid = new_id()
    return mid, {
        "animations": [], "id": mid,
        "multi_language_current": "none", "type": "sticker_animation",
    }


# ─── Track Material Factories ───────────────────────────────

def make_video_material(filepath, info):
    mid = new_id()
    local_id = str(uuid.uuid4())
    mat = {
        "aigc_type": "none",
        "audio_fade": None,
        "cartoon_path": "",
        "category_id": "",
        "category_name": "local",
        "check_flag": 62978047,
        "content_feature_info": None,
        "corner_pin": None,
        "crop": {
            "lower_left_x": 0.0, "lower_left_y": 1.0,
            "lower_right_x": 1.0, "lower_right_y": 1.0,
            "upper_left_x": 0.0, "upper_left_y": 0.0,
            "upper_right_x": 1.0, "upper_right_y": 0.0,
        },
        "crop_ratio": "free",
        "crop_scale": 1.0,
        "duration": info["duration_us"],
        "extra_type_option": 0,
        "formula_id": "",
        "freeze": None,
        "has_audio": info["has_audio"],
        "has_sound_separated": False,
        "height": info["height"],
        "id": mid,
        "intensifies_path": "",
        "is_ai_generate_content": False,
        "is_copyright": False,
        "is_text_edit_overdub": False,
        "is_unified_beauty_mode": False,
        "local_id": "",
        "local_material_from": "",
        "local_material_id": local_id,
        "material_id": "",
        "material_name": Path(filepath).name,
        "material_url": "",
        "matting": {
            "flag": 0, "has_use_quick_brush": False,
            "has_use_quick_eraser": False, "interactiveTime": [],
            "path": "", "strokes": [],
        },
        "media_path": "",
        "multi_camera_info": None,
        "object_locked": None,
        "origin_material_id": "",
        "path": filepath,
        "picture_from": "none",
        "request_id": "",
        "reverse_path": "",
        "source": 0,
        "source_platform": 0,
        "stable": {"matrix_path": "", "stable_level": 0, "time_range": {"duration": 0, "start": 0}},
        "team_id": "",
        "type": "video",
        "video_algorithm": {
            "algorithms": [], "path": "",
        },
        "width": info["width"],
    }
    return mid, local_id, mat


def make_audio_material(filepath, name, dur_us):
    mid = new_id()
    local_id = str(uuid.uuid4())
    mat = {
        "app_id": 0,
        "category_id": "",
        "category_name": "local",
        "check_flag": 1,
        "copyright_limit_type": "none",
        "duration": dur_us,
        "effect_id": "",
        "formula_id": "",
        "id": mid,
        "intensifies_path": "",
        "is_ai_clone_tone": False,
        "is_ugc": False,
        "local_material_id": local_id,
        "music_id": str(uuid.uuid4()),
        "name": name,
        "path": filepath,
        "request_id": "",
        "resource_id": "",
        "source_platform": 0,
        "team_id": "",
        "text_id": "",
        "tone_category_id": "",
        "tone_category_name": "",
        "tone_effect_id": "",
        "tone_effect_name": "",
        "tone_platform": "",
        "tone_speaker": "",
        "tone_type": "",
        "type": "extract_music",
        "video_id": "",
        "wave_points": [],
    }
    return mid, local_id, mat


def make_text_material(text, font_size=5.0, color=None):
    if color is None:
        color = [1, 1, 1]
    mid = new_id()
    # CapCut 형식: styles→text 키 순서, compact JSON (공백 없음)
    from collections import OrderedDict
    content_obj = OrderedDict([
        ("styles", [OrderedDict([
            ("fill", OrderedDict([
                ("content", OrderedDict([
                    ("solid", OrderedDict([("color", color)])),
                    ("render_type", "solid"),
                ])),
            ])),
            ("range", [0, len(text)]),
            ("size", font_size),
            ("font", OrderedDict([("path", CAPCUT_FONT), ("id", "")])),
        ])]),
        ("text", text),
    ])
    mat = {
        "add_type": 2,
        "alignment": 1,
        "background_alpha": 1.0,
        "background_color": "",
        "background_height": 0.14,
        "background_round_radius": 0.0,
        "background_style": 0,
        "background_width": 0.14,
        "bold_width": 0.0,
        "border_alpha": 1.0,
        "border_color": "",
        "border_width": 0.08,
        "check_flag": 7,
        "combo_info": {"text_templates": []},
        "content": json.dumps(content_obj, ensure_ascii=False, separators=(",", ":")),
        "fixed_height": -1.0,
        "fixed_width": -1.0,
        "font_id": "",
        "font_name": "",
        "font_path": CAPCUT_FONT,
        "font_resource_id": "",
        "font_size": font_size,
        "font_source_platform": 0,
        "font_title": "none",
        "font_url": "",
        "fonts": [],
        "force_apply_line_max_width": False,
        "global_alpha": 1.0,
        "group_id": "",
        "has_shadow": False,
        "id": mid,
        "initial_scale": 1.0,
        "inner_padding": -1.0,
        "is_rich_text": False,
        "italic_degree": 0,
        "ktv_color": "",
        "language": "",
        "layer_weight": 1,
        "letter_spacing": 0.0,
        "line_feed": 1,
        "line_max_width": 0.82,
        "line_spacing": 0.02,
        "multi_language_current": "none",
        "name": "",
        "original_size": [],
        "preset_category": "",
        "preset_category_id": "",
        "preset_has_set_alignment": False,
        "preset_id": "",
        "preset_index": 0,
        "preset_name": "",
        "recognize_task_id": "",
        "recognize_type": 0,
        "relevance_segment": [],
        "shadow_alpha": 0.9,
        "shadow_angle": -45.0,
        "shadow_color": "",
        "shadow_distance": 0.04,
        "shadow_point": {"x": 0.6401844, "y": 0.6401844},
        "shadow_smoothing": 0.45,
        "shape_clip_x": False,
        "shape_clip_y": False,
        "style_name": "",
        "sub_type": 0,
        "subtitle_keywords": None,
        "text_alpha": 1.0,
        "text_color": "",
        "text_curve": None,
        "text_preset_resource_id": "",
        "text_size": 30,
        "text_to_audio_ids": [],
        "tts_auto_update": False,
        "type": "subtitle",
        "typesetting": 0,
        "underline": False,
        "underline_offset": 0.22,
        "underline_width": 0.05,
        "use_effect_default_color": True,
        "words": {"end_time": [], "start_time": [], "text": []},
    }
    return mid, mat


# ─── Segment Factories ──────────────────────────────────────

def make_video_segment(material_id, extra_refs, dur_us, target_start_us):
    return {
        "caption_info": None,
        "cartoon": False,
        "clip": {
            "alpha": 1.0,
            "flip": {"horizontal": False, "vertical": False},
            "rotation": 0.0,
            "scale": {"x": 1.0, "y": 1.0},
            "transform": {"x": 0.0, "y": 0.0},
        },
        "color_correct_alg_result": "",
        "common_keyframes": [],
        "desc": "",
        "digital_human_template_group_id": "",
        "enable_adjust": True,
        "enable_adjust_mask": False,
        "enable_color_adjust_pro": False,
        "enable_color_correct_adjust": False,
        "enable_color_curves": True,
        "enable_color_match_adjust": False,
        "enable_color_wheels": True,
        "enable_hsl": False,
        "enable_hsl_curves": True,
        "enable_lut": True,
        "enable_mask_shadow": False,
        "enable_mask_stroke": False,
        "enable_smart_color_adjust": False,
        "enable_video_mask": True,
        "extra_material_refs": extra_refs,
        "group_id": "",
        "hdr_settings": {"intensity": 1.0, "mode": 1, "nits": 1000},
        "id": new_id(),
        "intensifies_audio": False,
        "is_loop": False,
        "is_placeholder": False,
        "is_tone_modify": False,
        "keyframe_refs": [],
        "last_nonzero_volume": 1.0,
        "lyric_keyframes": None,
        "material_id": material_id,
        "raw_segment_id": "",
        "render_index": 0,
        "render_timerange": {"duration": 0, "start": 0},
        "responsive_layout": {
            "enable": False, "horizontal_pos_layout": 0,
            "size_layout": 0, "target_follow": "", "vertical_pos_layout": 0,
        },
        "reverse": False,
        "source": "segmentsourcenormal",
        "source_timerange": {"duration": dur_us, "start": 0},
        "speed": 1.0,
        "state": 0,
        "target_timerange": {"duration": dur_us, "start": target_start_us},
        "template_id": "",
        "template_scene": "default",
        "track_attribute": 0,
        "track_render_index": 0,
        "uniform_scale": {"on": True, "value": 1.0},
        "visible": True,
        "volume": 1.0,
    }


def make_audio_segment(material_id, extra_refs, dur_us, target_start_us):
    return {
        "caption_info": None,
        "cartoon": False,
        "clip": None,
        "color_correct_alg_result": "",
        "common_keyframes": [],
        "desc": "",
        "digital_human_template_group_id": "",
        "enable_adjust": False,
        "enable_adjust_mask": False,
        "enable_color_adjust_pro": False,
        "enable_color_correct_adjust": False,
        "enable_color_curves": True,
        "enable_color_match_adjust": False,
        "enable_color_wheels": True,
        "enable_hsl": False,
        "enable_hsl_curves": True,
        "enable_lut": False,
        "enable_mask_shadow": False,
        "enable_mask_stroke": False,
        "enable_smart_color_adjust": False,
        "enable_video_mask": True,
        "extra_material_refs": extra_refs,
        "group_id": "",
        "hdr_settings": None,
        "id": new_id(),
        "intensifies_audio": False,
        "is_loop": False,
        "is_placeholder": False,
        "is_tone_modify": False,
        "keyframe_refs": [],
        "last_nonzero_volume": 1.0,
        "lyric_keyframes": None,
        "material_id": material_id,
        "raw_segment_id": "",
        "render_index": 0,
        "render_timerange": {"duration": 0, "start": 0},
        "responsive_layout": {
            "enable": False, "horizontal_pos_layout": 0,
            "size_layout": 0, "target_follow": "", "vertical_pos_layout": 0,
        },
        "reverse": False,
        "source": "segmentsourcenormal",
        "source_timerange": {"duration": dur_us, "start": 0},
        "speed": 1.0,
        "state": 0,
        "target_timerange": {"duration": dur_us, "start": target_start_us},
        "template_id": "",
        "template_scene": "default",
        "track_attribute": 0,
        "track_render_index": 2,
        "uniform_scale": None,
        "visible": True,
        "volume": 1.0,
    }


def make_text_segment(material_id, extra_refs, dur_us, target_start_us, pos_y=-0.8, scale=0.65):
    return {
        "caption_info": None,
        "cartoon": False,
        "clip": {
            "alpha": 1.0,
            "flip": {"horizontal": False, "vertical": False},
            "rotation": 0.0,
            "scale": {"x": scale, "y": scale},
            "transform": {"x": 0.0, "y": pos_y},
        },
        "color_correct_alg_result": "",
        "common_keyframes": [],
        "desc": "",
        "digital_human_template_group_id": "",
        "enable_adjust": False,
        "enable_adjust_mask": False,
        "enable_color_adjust_pro": False,
        "enable_color_correct_adjust": False,
        "enable_color_curves": True,
        "enable_color_match_adjust": False,
        "enable_color_wheels": True,
        "enable_hsl": False,
        "enable_hsl_curves": True,
        "enable_lut": False,
        "enable_mask_shadow": False,
        "enable_mask_stroke": False,
        "enable_smart_color_adjust": False,
        "enable_video_mask": True,
        "extra_material_refs": extra_refs,
        "group_id": "",
        "hdr_settings": None,
        "id": new_id(),
        "intensifies_audio": False,
        "is_loop": False,
        "is_placeholder": False,
        "is_tone_modify": False,
        "keyframe_refs": [],
        "last_nonzero_volume": 1.0,
        "lyric_keyframes": None,
        "material_id": material_id,
        "raw_segment_id": "",
        "render_index": 14000,
        "render_timerange": {"duration": 0, "start": 0},
        "responsive_layout": {
            "enable": False, "horizontal_pos_layout": 0,
            "size_layout": 0, "target_follow": "", "vertical_pos_layout": 0,
        },
        "reverse": False,
        "source": "segmentsourcenormal",
        "source_timerange": None,
        "speed": 1.0,
        "state": 0,
        "target_timerange": {"duration": dur_us, "start": target_start_us},
        "template_id": "",
        "template_scene": "default",
        "track_attribute": 0,
        "track_render_index": 1,
        "uniform_scale": {"on": True, "value": 1.0},
        "visible": True,
        "volume": 1.0,
    }


# ─── Project Generator ──────────────────────────────────────

def generate_project(config, config_dir):
    name = config["name"]
    fps = config.get("fps", 30.0)
    canvas_w = config.get("canvas", {}).get("width", 1920)
    canvas_h = config.get("canvas", {}).get("height", 1080)
    sub_style = config.get("subtitle_style", {})

    project_dir = CAPCUT_DRAFTS / name
    project_dir.mkdir(parents=True, exist_ok=True)
    resources_dir = project_dir / "Resources"
    resources_dir.mkdir(exist_ok=True)

    def copy_to_project(src_path):
        """파일을 프로젝트 Resources/에 복사하고 복사된 경로 반환.
        CapCut은 샌드박스 앱이라 ~/Movies/CapCut/ 외부 파일에 접근 불가."""
        src = Path(src_path)
        dst = resources_dir / src.name
        if not dst.exists():
            shutil.copy2(str(src), str(dst))
        return str(dst)

    # Initialize all material buckets
    materials = {
        "ai_translates": [], "audio_balances": [], "audio_effects": [],
        "audio_fades": [], "audio_pannings": [], "audio_pitch_shifts": [],
        "audio_track_indexes": [], "audios": [], "beats": [],
        "canvases": [], "chromas": [], "color_curves": [],
        "common_mask": [], "digital_human_model_dressing": [],
        "digital_humans": [], "drafts": [], "effects": [],
        "flowers": [], "green_screens": [], "handwrites": [],
        "hsl": [], "hsl_curves": [], "images": [],
        "log_color_wheels": [], "loudnesses": [],
        "manual_beautys": [], "manual_deformations": [],
        "material_animations": [], "material_colors": [],
        "multi_language_refs": [], "placeholder_infos": [],
        "placeholders": [], "plugin_effects": [],
        "primary_color_wheels": [], "realtime_denoises": [],
        "shapes": [], "smart_crops": [], "smart_relights": [],
        "sound_channel_mappings": [], "speeds": [],
        "stickers": [], "tail_leaders": [],
        "text_templates": [], "texts": [],
        "time_marks": [], "transitions": [],
        "video_effects": [], "video_radius": [],
        "video_shadows": [], "video_strokes": [],
        "video_trackings": [], "videos": [],
        "vocal_beautifys": [], "vocal_separations": [],
    }

    video_segments = []
    audio_segments = []
    text_segments = []
    meta_materials = []  # draft_meta_info.draft_materials

    def resolve_path(p):
        p = Path(p)
        if not p.is_absolute():
            p = (config_dir / p).resolve()
        return str(p)

    # ── Videos ───────────────────────────────────────────────
    video_cursor = 0
    for vpath_raw in config.get("video", []):
        vpath_orig = resolve_path(vpath_raw)
        info = probe_file(vpath_orig)
        vpath = copy_to_project(vpath_orig)
        dur = info["duration_us"]
        print(f"  video: {Path(vpath).name} ({us_to_sec(dur):.2f}s) @ {us_to_sec(video_cursor):.2f}s")

        vid_id, vid_local_id, vid_mat = make_video_material(vpath, info)
        materials["videos"].append(vid_mat)

        sp_id, sp = make_speed()
        ph_id, ph = make_placeholder_info()
        cv_id, cv = make_canvas()
        sc_id, sc = make_sound_channel_mapping()
        mc_id, mc = make_material_color()
        vs_id, vs = make_vocal_separation()
        materials["speeds"].append(sp)
        materials["placeholder_infos"].append(ph)
        materials["canvases"].append(cv)
        materials["sound_channel_mappings"].append(sc)
        materials["material_colors"].append(mc)
        materials["vocal_separations"].append(vs)

        seg = make_video_segment(vid_id, [sp_id, ph_id, cv_id, sc_id, mc_id, vs_id], dur, video_cursor)
        video_segments.append(seg)

        meta_materials.append({
            "ai_group_type": "", "create_time": int(time.time()),
            "duration": dur, "enter_from": 0,
            "extra_info": Path(vpath_orig).name,
            "file_Path": vpath,
            "height": info["height"], "width": info["width"],
            "id": vid_local_id, "import_time": int(time.time()),
            "import_time_ms": int(time.time() * 1_000_000),
            "item_source": 1, "md5": "", "metetype": "video",
            "roughcut_time_range": {"duration": dur, "start": 0},
            "sub_time_range": {"duration": -1, "start": -1},
            "type": 0,
        })

        video_cursor += dur

    # ── Audios ───────────────────────────────────────────────
    audio_cursor = 0
    for aitem in config.get("audio", []):
        if isinstance(aitem, str):
            apath_orig = resolve_path(aitem)
            astart = audio_cursor
        else:
            apath_orig = resolve_path(aitem["path"])
            astart = sec_to_us(aitem["start"]) if "start" in aitem else audio_cursor

        info = probe_file(apath_orig)
        apath = copy_to_project(apath_orig)
        dur = info["duration_us"]
        print(f"  audio: {Path(apath).name} ({us_to_sec(dur):.2f}s) @ {us_to_sec(astart):.2f}s")

        aud_id, aud_local_id, aud_mat = make_audio_material(apath, Path(apath).name, dur)
        materials["audios"].append(aud_mat)

        sp_id, sp = make_speed()
        ph_id, ph = make_placeholder_info()
        bt_id, bt = make_beat()
        sc_id, sc = make_sound_channel_mapping()
        vs_id, vs = make_vocal_separation()
        materials["speeds"].append(sp)
        materials["placeholder_infos"].append(ph)
        materials["beats"].append(bt)
        materials["sound_channel_mappings"].append(sc)
        materials["vocal_separations"].append(vs)

        seg = make_audio_segment(aud_id, [sp_id, ph_id, bt_id, sc_id, vs_id], dur, astart)
        audio_segments.append(seg)

        meta_materials.append({
            "ai_group_type": "", "create_time": int(time.time()),
            "duration": dur, "enter_from": 0,
            "extra_info": Path(apath_orig).name,
            "file_Path": apath,
            "height": 0, "width": 0,
            "id": aud_local_id, "import_time": int(time.time()),
            "import_time_ms": int(time.time() * 1_000_000),
            "item_source": 1, "md5": "", "metetype": "music",
            "roughcut_time_range": {"duration": dur, "start": 0},
            "sub_time_range": {"duration": -1, "start": -1},
            "type": 0,
        })

        audio_cursor = astart + dur

    # ── Subtitles (SRT) ──────────────────────────────────────
    srt_meta = []
    subtitle_path = config.get("subtitle")
    if subtitle_path:
        srt_file = resolve_path(subtitle_path)
        subs = parse_srt(srt_file)
        font_size = sub_style.get("font_size", 5.0)
        color = sub_style.get("color", [1, 1, 1])
        pos_y = sub_style.get("position_y", -0.8)
        scale = sub_style.get("scale", 0.65)
        print(f"  subtitle: {len(subs)} entries from {Path(srt_file).name}")

        for sub in subs:
            txt_id, txt_mat = make_text_material(sub["text"], font_size, color)
            materials["texts"].append(txt_mat)

            anim_id, anim = make_material_animation()
            materials["material_animations"].append(anim)

            seg = make_text_segment(txt_id, [anim_id], sub["duration_us"], sub["start_us"], pos_y, scale)
            text_segments.append(seg)

        srt_meta.append({
            "ai_group_type": "", "create_time": 0,
            "duration": 0, "enter_from": 0,
            "extra_info": Path(srt_file).name,
            "file_Path": srt_file,
            "height": 0, "width": 0,
            "id": new_id(), "import_time": int(time.time()),
            "import_time_ms": -1,
            "item_source": 1, "md5": "", "metetype": "none",
            "roughcut_time_range": {"duration": -1, "start": -1},
            "sub_time_range": {"duration": -1, "start": -1},
            "type": 2,
        })

    # ── Total duration ───────────────────────────────────────
    total_dur = 0
    for segs in [video_segments, audio_segments, text_segments]:
        for s in segs:
            end = s["target_timerange"]["start"] + s["target_timerange"]["duration"]
            total_dur = max(total_dur, end)

    # ── Build tracks ─────────────────────────────────────────
    tracks = []
    if video_segments:
        tracks.append({
            "attribute": 0, "flag": 0, "id": new_id(),
            "is_default_name": True, "name": "",
            "segments": video_segments, "type": "video",
        })
    if text_segments:
        tracks.append({
            "attribute": 0, "flag": 0, "id": new_id(),
            "is_default_name": True, "name": "",
            "segments": text_segments, "type": "text",
        })
    if audio_segments:
        tracks.append({
            "attribute": 0, "flag": 0, "id": new_id(),
            "is_default_name": True, "name": "",
            "segments": audio_segments, "type": "audio",
        })

    # ── Build draft_info.json ────────────────────────────────
    draft_id = new_id()
    now_us = int(time.time() * 1_000_000)

    draft_info = {
        "canvas_config": {
            "background": None,
            "height": canvas_h,
            "ratio": "original",
            "width": canvas_w,
        },
        "color_space": 0,
        "config": {
            "adjust_max_index": 1,
            "attachment_info": [],
            "combination_max_index": 1,
            "export_range": None,
            "extract_audio_last_index": 1,
            "lyrics_recognition_id": "",
            "lyrics_sync": True,
            "lyrics_taskinfo": [],
            "maintrack_adsorb": True,
            "material_save_mode": 0,
            "multi_language_current": "none",
            "multi_language_list": [],
            "multi_language_main": "none",
            "multi_language_mode": "none",
            "original_sound_last_index": 1,
            "record_audio_last_index": 1,
            "sticker_max_index": 1,
            "subtitle_keywords_config": None,
            "subtitle_recognition_id": "",
            "subtitle_sync": True,
            "subtitle_taskinfo": [],
            "system_font_list": [],
            "use_float_render": False,
            "video_mute": False,
            "zoom_info_params": None,
        },
        "cover": "",
        "create_time": int(time.time()),
        "draft_type": "",
        "duration": total_dur,
        "extra_info": "",
        "fps": float(fps),
        "free_render_index_mode_on": False,
        "function_assistant_info": "",
        "group_container": None,
        "id": draft_id,
        "is_drop_frame_timecode": False,
        "keyframe_graph_list": [],
        "keyframes": [],
        "last_modified_platform": {
            "app_id": 359289,
            "app_source": "cc",
            "app_version": "8.3.0",
            "device_id": "",
            "hard_disk_id": "",
            "mac_address": "",
            "os": "mac",
            "os_version": "",
        },
        "lyrics_effects": [],
        "materials": materials,
        "mutable_config": None,
        "name": name,
        "new_version": "",
        "path": str(project_dir),
        "platform": {
            "app_id": 359289,
            "app_source": "cc",
            "app_version": "8.3.0",
            "device_id": "",
            "hard_disk_id": "",
            "mac_address": "",
            "os": "mac",
            "os_version": "",
        },
        "relationships": [],
        "render_index_track_mode_on": False,
        "retouch_cover": None,
        "smart_ads_info": None,
        "source": "default",
        "static_cover_image_path": "",
        "time_marks": None,
        "tracks": tracks,
        "update_time": int(time.time()),
        "version": 360000,
    }

    # ── Write draft_info.json ────────────────────────────────
    draft_info_path = project_dir / "draft_info.json"
    with open(draft_info_path, "w", encoding="utf-8") as f:
        json.dump(draft_info, f, ensure_ascii=False, separators=(",", ":"))
    print(f"\n  draft_info.json ({draft_info_path.stat().st_size / 1024:.0f}KB)")

    # ── Write draft_meta_info.json ───────────────────────────
    total_size = sum(
        f.stat().st_size for f in resources_dir.iterdir() if f.is_file()
    )
    draft_meta = {
        "cloud_draft_cover": False,
        "cloud_draft_sync": False,
        "cloud_package_completed_time": "",
        "draft_cloud_last_action_download": False,
        "draft_cloud_purchase_info": "",
        "draft_cloud_template_id": "",
        "draft_cloud_tutorial_info": "",
        "draft_cloud_videocut_purchase_info": "",
        "draft_cover": "draft_cover.jpg",
        "draft_deeplink_url": "",
        "draft_enterprise_info": {
            "draft_enterprise_extra": "",
            "draft_enterprise_id": "",
            "draft_enterprise_name": "",
            "enterprise_material": [],
        },
        "draft_fold_path": str(project_dir),
        "draft_id": draft_id,
        "draft_is_ai_shorts": False,
        "draft_is_cloud_temp_draft": False,
        "draft_is_invisible": False,
        "draft_materials": [
            {"type": 0, "value": meta_materials},
            {"type": 1, "value": []},
            {"type": 2, "value": srt_meta},
            {"type": 3, "value": []},
            {"type": 6, "value": []},
            {"type": 7, "value": []},
            {"type": 8, "value": []},
        ],
        "draft_materials_copied_info": [],
        "draft_name": name,
        "draft_need_rename_folder": False,
        "draft_new_version": "",
        "draft_removable_storage_device": "",
        "draft_root_path": str(CAPCUT_DRAFTS),
        "draft_segment_extra_info": [],
        "draft_timeline_materials_size_": total_size,
        "draft_type": "",
        "tm_draft_cloud_completed": "",
        "tm_draft_cloud_entry_id": -1,
        "tm_draft_cloud_modified": 0,
        "tm_draft_cloud_parent_entry_id": -1,
        "tm_draft_cloud_space_id": -1,
        "tm_draft_cloud_user_id": -1,
        "tm_draft_create": now_us,
        "tm_draft_modified": now_us,
        "tm_draft_removed": 0,
        "tm_duration": total_dur,
    }
    with open(project_dir / "draft_meta_info.json", "w", encoding="utf-8") as f:
        json.dump(draft_meta, f, ensure_ascii=False, indent=4)
    print(f"  draft_meta_info.json")

    # ── Generate cover (black 1920x1080) ─────────────────────
    cover_path = project_dir / "draft_cover.jpg"
    if not cover_path.exists():
        subprocess.run(
            ["ffmpeg", "-y", "-f", "lavfi", "-i",
             f"color=c=black:s={canvas_w}x{canvas_h}:d=1",
             "-frames:v", "1", str(cover_path)],
            capture_output=True,
        )
        print(f"  draft_cover.jpg")

    # ── Update root_meta_info.json ───────────────────────────
    root_meta_path = CAPCUT_DRAFTS / "root_meta_info.json"
    if root_meta_path.exists():
        with open(root_meta_path, "r", encoding="utf-8") as f:
            root_meta = json.load(f)
    else:
        root_meta = {"all_draft_store": []}

    # 중복 제거 (같은 이름의 기존 프로젝트가 있으면 교체)
    root_meta["all_draft_store"] = [
        d for d in root_meta["all_draft_store"]
        if d.get("draft_name") != name
    ]

    root_meta["all_draft_store"].insert(0, {
        "cloud_draft_cover": False,
        "cloud_draft_sync": False,
        "draft_cloud_last_action_download": False,
        "draft_cloud_purchase_info": "",
        "draft_cloud_template_id": "",
        "draft_cloud_tutorial_info": "",
        "draft_cloud_videocut_purchase_info": "",
        "draft_cover": str(cover_path),
        "draft_fold_path": str(project_dir),
        "draft_id": draft_id,
        "draft_is_ai_shorts": False,
        "draft_is_cloud_temp_draft": False,
        "draft_is_invisible": False,
        "draft_is_web_article_video": False,
        "draft_json_file": str(draft_info_path),
        "draft_name": name,
        "draft_new_version": "",
        "draft_root_path": str(CAPCUT_DRAFTS),
        "draft_timeline_materials_size": total_size,
        "draft_type": "",
        "streaming_edit_draft_ready": True,
        "tm_draft_cloud_completed": "",
        "tm_draft_cloud_entry_id": -1,
        "tm_draft_cloud_modified": 0,
        "tm_draft_cloud_parent_entry_id": -1,
        "tm_draft_cloud_space_id": -1,
        "tm_draft_cloud_user_id": -1,
        "tm_draft_create": now_us,
        "tm_draft_modified": now_us,
        "tm_draft_removed": 0,
        "tm_duration": total_dur,
    })

    with open(root_meta_path, "w", encoding="utf-8") as f:
        json.dump(root_meta, f, ensure_ascii=False, indent=4)
    print(f"  root_meta_info.json (updated)")

    print(f"\n=== 완료: {project_dir} ===")
    print(f"    duration: {us_to_sec(total_dur):.1f}s")
    print(f"    video: {len(video_segments)} segments")
    print(f"    audio: {len(audio_segments)} segments")
    print(f"    text:  {len(text_segments)} segments")
    print(f"\n  CapCut을 열면 '{name}' 프로젝트가 목록에 표시됩니다.")


# ─── Main ────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    config_path = Path(sys.argv[1]).resolve()
    if not config_path.exists():
        print(f"설정 파일 없음: {config_path}")
        sys.exit(1)

    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    print(f"=== CapCut 프로젝트 생성: {config['name']} ===\n")
    generate_project(config, config_path.parent)


if __name__ == "__main__":
    main()
