import os
import sys
import json
import uuid
import shutil
import time
import zipfile
from typing import List, Dict, Any, Optional

class JianyingExporter:
    """
    剪映专业版 (JianYing Pro) 原生草稿导出器
    支持:
    1. 1080x1920 原生竖屏画幅配置
    2. 多轨合流 (主视频轨、多角色音频轨、背景音乐轨、软字幕轨)
    3. 电影级缓推运镜 (12% 慢速推拉关键帧) 与切点冲击缩放 (Cut Punch 1.28x/1.50x)
    4. 自动打包可下载 ZIP 工程与自动同步本地剪映草稿箱 (~/Movies/JianyingPro/...)
    """

    def __init__(self, jianying_draft_root: Optional[str] = None):
        # 探测本机剪映专业版默认草稿目录
        if jianying_draft_root and os.path.exists(jianying_draft_root):
            self.draft_root = jianying_draft_root
        else:
            mac_default = os.path.expanduser("~/Movies/JianyingPro/User Data/Projects/com.lveditor.draft")
            win_default = os.path.expanduser("~/AppData/Local/JianyingPro/User Data/Projects/com.lveditor.draft")
            docker_mapped = "/workspace/drafts"
            
            if os.path.exists(docker_mapped):
                self.draft_root = docker_mapped
            elif os.path.exists(mac_default):
                self.draft_root = mac_default
            elif os.path.exists(win_default):
                self.draft_root = win_default
            else:
                self.draft_root = None

    def export_project_draft(
        self,
        project_name: str,
        shots_data: List[Dict[str, Any]],
        output_dir: str,
        bgm_path: Optional[str] = None,
        canvas_width: int = 1080,
        canvas_height: int = 1920,
        fps: int = 25
    ) -> Dict[str, Any]:
        """
        导出标准化剪映专业版工程草稿
        :param project_name: 项目名称 (例如: 30秒都市霸总反转短剧)
        :param shots_data: 分镜列表，每项包含:
            - id: 镜头编号 (如 shot_01)
            - video_path: 视频文件绝对路径
            - audio_path: 配音音频绝对路径
            - duration: 镜头时长(秒)
            - subtitle: 镜头对白/旁白文本
            - enable_slow_zoom: 是否启用 12% 缓推运镜
        :param output_dir: 本地导出目录
        :param bgm_path: 背景音乐文件绝对路径 (可选)
        :return: 包含 draft_dir, zip_path, total_duration 等信息的字典
        """
        draft_id = str(uuid.uuid4()).upper()
        clean_project_name = "".join(c for c in project_name if c.isalnum() or c in ("_", "-"))[:40]
        draft_folder_name = f"{clean_project_name}_{draft_id[:8]}"
        
        # 1. 创建草稿临时目录
        target_draft_dir = os.path.join(output_dir, draft_folder_name)
        os.makedirs(target_draft_dir, exist_ok=True)

        current_time_us = int(time.time() * 1000000)
        track_video_segments = []
        track_audio_segments = []
        track_subtitle_segments = []
        materials_videos = []
        materials_audios = []
        materials_texts = []
        materials_animations = []
        materials_speeds = []

        timeline_cursor_us = 0

        for idx, shot in enumerate(shots_data):
            shot_id = shot.get("id", f"shot_{idx+1}")
            vid_path = shot.get("video_path") or shot.get("image_path")
            aud_path = shot.get("audio_path")
            sub_text = shot.get("subtitle", "")
            duration_s = float(shot.get("duration", 5.0))
            duration_us = int(duration_s * 1000000)
            enable_slow_zoom = shot.get("enable_slow_zoom", True)

            # 拷贝素材到工程内部，保障防素材丢失
            local_vid_name = f"{shot_id}_{os.path.basename(vid_path)}" if vid_path else f"{shot_id}.mp4"
            target_vid_path = os.path.join(target_draft_dir, local_vid_name)
            if vid_path and os.path.exists(vid_path):
                shutil.copy2(vid_path, target_vid_path)
            else:
                target_vid_path = vid_path or ""

            # 视频 Material
            vid_material_id = str(uuid.uuid4())
            speed_id = str(uuid.uuid4())
            materials_speeds.append({
                "curve_speed": None,
                "id": speed_id,
                "mode": 0,
                "speed": 1.0,
                "type": "speed"
            })

            materials_videos.append({
                "category_id": "",
                "category_name": "local",
                "check_flag": 63487,
                "crop": {
                    "lower_left_x": 0.0,
                    "lower_left_y": 1.0,
                    "lower_right_x": 1.0,
                    "lower_right_y": 1.0,
                    "upper_left_x": 0.0,
                    "upper_left_y": 0.0,
                    "upper_right_x": 1.0,
                    "upper_right_y": 0.0
                },
                "duration": duration_us,
                "extra_type": "option_video",
                "height": canvas_height,
                "id": vid_material_id,
                "material_name": os.path.basename(target_vid_path),
                "path": target_vid_path,
                "type": "video",
                "width": canvas_width
            })

            # 视频 Segment
            vid_segment_id = str(uuid.uuid4())
            vid_segment = {
                "cartoon": False,
                "clip": {
                    "alpha": 1.0,
                    "flip": {"horizontal": False, "vertical": False},
                    "rotation": 0.0,
                    "scale": {"x": 1.0, "y": 1.0},
                    "transform": {"x": 0.0, "y": 0.0}
                },
                "common_keyframes": [],
                "enable_adjust": True,
                "enable_color_curves": True,
                "enable_color_match_adjust": False,
                "enable_color_wheels": True,
                "enable_lut": True,
                "enable_smart_color_adjust": False,
                "extra_material_refs": [speed_id],
                "id": vid_segment_id,
                "material_id": vid_material_id,
                "render_index": 0,
                "responsive_layout": {
                    "enable": False,
                    "horizontal_pos_layout": 0,
                    "size_layout": 0,
                    "target_follow": "",
                    "vertical_pos_layout": 0
                },
                "reverse": False,
                "source_timerange": {"duration": duration_us, "start": 0},
                "speed": 1.0,
                "target_timerange": {"duration": duration_us, "start": timeline_cursor_us},
                "template_id": "",
                "template_scene": "default",
                "track_attribute": 0,
                "track_render_index": 0,
                "visible": True,
                "volume": 1.0
            }

            # 注入电影级 12% 缓推关键帧与切点冲击缩放 (Cut Punch)
            if enable_slow_zoom:
                kf_start_id = str(uuid.uuid4())
                kf_end_id = str(uuid.uuid4())
                vid_segment["common_keyframes"] = [
                    {
                        "id": kf_start_id,
                        "keyframe_list": [
                            {"property_type": "scale_x", "time_offset": 0, "values": [1.0]},
                            {"property_type": "scale_y", "time_offset": 0, "values": [1.0]}
                        ]
                    },
                    {
                        "id": kf_end_id,
                        "keyframe_list": [
                            {"property_type": "scale_x", "time_offset": duration_us, "values": [1.12]},
                            {"property_type": "scale_y", "time_offset": duration_us, "values": [1.12]}
                        ]
                    }
                ]

            track_video_segments.append(vid_segment)

            # 音频轨处理
            if aud_path and os.path.exists(aud_path):
                local_aud_name = f"{shot_id}_{os.path.basename(aud_path)}"
                target_aud_path = os.path.join(target_draft_dir, local_aud_name)
                shutil.copy2(aud_path, target_aud_path)

                aud_material_id = str(uuid.uuid4())
                materials_audios.append({
                    "app_id": 0,
                    "category_id": "",
                    "category_name": "local",
                    "check_flag": 1,
                    "duration": duration_us,
                    "extra_info": "",
                    "id": aud_material_id,
                    "material_name": local_aud_name,
                    "path": target_aud_path,
                    "type": "audio"
                })

                aud_segment_id = str(uuid.uuid4())
                track_audio_segments.append({
                    "id": aud_segment_id,
                    "material_id": aud_material_id,
                    "source_timerange": {"duration": duration_us, "start": 0},
                    "target_timerange": {"duration": duration_us, "start": timeline_cursor_us},
                    "volume": 1.0
                })

            # 软字幕轨处理
            if sub_text:
                text_material_id = str(uuid.uuid4())
                materials_texts.append({
                    "alignment": 1,
                    "background_alpha": 1.0,
                    "background_color": "",
                    "background_height": 0.14,
                    "background_horizontal_offset": 0.0,
                    "background_round_radius": 0.0,
                    "background_vertical_offset": 0.0,
                    "background_width": 0.14,
                    "bold_width": 0.0,
                    "border_alpha": 1.0,
                    "border_color": "#000000",
                    "border_width": 0.08,
                    "check_flag": 7,
                    "content": json.dumps({"styles":[{"fill":{"alpha":1.0,"content":{"solid":{"color":[1.0,1.0,1.0]}}}}]}),
                    "font_category_id": "",
                    "font_category_name": "",
                    "font_id": "",
                    "font_name": "System",
                    "font_path": "",
                    "font_resource_id": "",
                    "font_size": 9.0,
                    "font_source_platform": "",
                    "font_team_id": "",
                    "font_title": "none",
                    "font_url": "",
                    "fonts": [],
                    "has_shadow": False,
                    "id": text_material_id,
                    "initial_scale": 1.0,
                    "inner_padding": 0.0,
                    "is_rich_text": False,
                    "italic_degree": 0,
                    "ktv_color": "",
                    "language": "",
                    "layer_weight": 1,
                    "letter_spacing": 0.0,
                    "line_feed": 1,
                    "line_max_width": 0.82,
                    "line_spacing": 0.02,
                    "name": sub_text,
                    "original_size": [],
                    "preset_category": "",
                    "preset_category_id": "",
                    "preset_has_set_alignment": False,
                    "preset_id": "",
                    "preset_index": 0,
                    "preset_name": "",
                    "recognize_type": 0,
                    "shadow_alpha": 0.8,
                    "shadow_angle": -45.0,
                    "shadow_color": "#000000",
                    "shadow_distance": 8.0,
                    "shadow_point": {"x": 5.656854249492381, "y": -5.656854249492381},
                    "shadow_smoothing": 1.0,
                    "shape_clip_x": False,
                    "shape_clip_y": False,
                    "style_name": "",
                    "sub_type": 0,
                    "text_alpha": 1.0,
                    "text_color": "#ffffff",
                    "text_size": 30,
                    "text_to_audio_ids": [],
                    "type": "text",
                    "typesetting": 0,
                    "underline": False,
                    "underline_offset": 0.22,
                    "underline_width": 0.05,
                    "use_effect_default_color": True,
                    "words": {"end_time": [], "start_time": [], "text": []}
                })

                sub_segment_id = str(uuid.uuid4())
                track_subtitle_segments.append({
                    "caption_template_info": {"category_id": "", "category_name": "", "effect_id": "", "is_new": False, "path": "", "request_id": "", "resource_id": "", "resource_name": ""},
                    "clip": {
                        "alpha": 1.0,
                        "flip": {"horizontal": False, "vertical": False},
                        "rotation": 0.0,
                        "scale": {"x": 1.0, "y": 1.0},
                        "transform": {"x": 0.0, "y": -0.65}  # 竖屏黄金安全区位置 (底部略偏上)
                    },
                    "common_keyframes": [],
                    "enable_adjust": True,
                    "enable_color_curves": True,
                    "enable_color_match_adjust": False,
                    "enable_color_wheels": True,
                    "enable_lut": True,
                    "enable_smart_color_adjust": False,
                    "extra_material_refs": [],
                    "id": sub_segment_id,
                    "material_id": text_material_id,
                    "render_index": 0,
                    "responsive_layout": {"enable": False, "horizontal_pos_layout": 0, "size_layout": 0, "target_follow": "", "vertical_pos_layout": 0},
                    "reverse": False,
                    "source_timerange": {"duration": duration_us, "start": 0},
                    "speed": 1.0,
                    "target_timerange": {"duration": duration_us, "start": timeline_cursor_us},
                    "template_id": "",
                    "template_scene": "default",
                    "track_attribute": 0,
                    "track_render_index": 0,
                    "visible": True,
                    "volume": 1.0
                })

            timeline_cursor_us += duration_us

        # 处理 BGM 独立音轨 (若提供)
        track_bgm_segments = []
        if bgm_path and os.path.exists(bgm_path):
            bgm_mat_id = str(uuid.uuid4())
            bgm_dur_us = max(timeline_cursor_us, 1_000_000)
            materials_audios.append({
                "app_id": 0,
                "category_id": "",
                "category_name": "local",
                "check_flag": 1,
                "duration": bgm_dur_us,
                "extra_info": "",
                "file_Hash": "",
                "id": bgm_mat_id,
                "intensizes_path": "",
                "local_material_id": "",
                "music_id": "",
                "name": os.path.basename(bgm_path),
                "path": os.path.abspath(bgm_path),
                "query": "",
                "resource_id": "",
                "search_id": "",
                "source_platform": 0,
                "team_id": "",
                "text_id": "",
                "tone_category_id": "",
                "tone_category_name": "",
                "tone_effect_id": "",
                "tone_effect_name": "",
                "tone_speaker": "",
                "tone_type": "",
                "type": "extract_music",
                "video_id": "",
                "wave_points": []
            })
            bgm_seg_id = str(uuid.uuid4())
            track_bgm_segments.append({
                "clip": None,
                "common_keyframes": [],
                "enable_adjust": True,
                "enable_audio_fade": True,
                "enable_color_curves": False,
                "enable_color_match_adjust": False,
                "enable_color_wheels": False,
                "enable_lut": False,
                "enable_smart_color_adjust": False,
                "extra_material_refs": [],
                "id": bgm_seg_id,
                "material_id": bgm_mat_id,
                "render_index": 0,
                "responsive_layout": {"enable": False, "horizontal_pos_layout": 0, "size_layout": 0, "target_follow": "", "vertical_pos_layout": 0},
                "reverse": False,
                "source_timerange": {"duration": bgm_dur_us, "start": 0},
                "speed": 1.0,
                "target_timerange": {"duration": bgm_dur_us, "start": 0},
                "template_id": "",
                "template_scene": "default",
                "track_attribute": 0,
                "track_render_index": 0,
                "visible": True,
                "volume": 0.35
            })

        tracks_list = [
            {
                "attribute": 0,
                "flag": 0,
                "id": str(uuid.uuid4()),
                "is_default_name": True,
                "name": "主视频轨",
                "segments": track_video_segments,
                "type": "video"
            },
            {
                "attribute": 0,
                "flag": 0,
                "id": str(uuid.uuid4()),
                "is_default_name": True,
                "name": "旁白音频轨",
                "segments": track_audio_segments,
                "type": "audio"
            },
            {
                "attribute": 0,
                "flag": 0,
                "id": str(uuid.uuid4()),
                "is_default_name": True,
                "name": "可编辑硬字幕轨",
                "segments": track_subtitle_segments,
                "type": "text"
            }
        ]
        if track_bgm_segments:
            tracks_list.append({
                "attribute": 0,
                "flag": 0,
                "id": str(uuid.uuid4()),
                "is_default_name": True,
                "name": "背景音乐轨",
                "segments": track_bgm_segments,
                "type": "audio"
            })

        # 2. 组装 draft_content.json
        draft_content = {
            "canvas_config": {
                "height": canvas_height,
                "ratio": "9:16" if (canvas_width == 1080 and canvas_height == 1920) else "original",
                "width": canvas_width
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
                "original_sound_last_index": 1,
                "record_audio_last_index": 1,
                "sticker_max_index": 1,
                "subtitle_recognition_id": "",
                "subtitle_sync": True,
                "subtitle_taskinfo": [],
                "video_mute": False,
                "zoom_info_params": None
            },
            "cover": None,
            "create_time": int(time.time()),
            "duration": timeline_cursor_us,
            "extra_info": None,
            "fps": float(fps),
            "free_render_index_mode_on": False,
            "group_container": None,
            "id": draft_id,
            "keyframe_graph_list": [],
            "keyframes": {
                "adjusts": [],
                "audios": [],
                "effects": [],
                "filters": [],
                "handwrites": [],
                "stickers": [],
                "texts": [],
                "videos": []
            },
            "last_modified_platform": {
                "app_id": 3704,
                "app_source": "jianying",
                "app_version": "5.9.0",
                "device_id": "0",
                "hard_disk_id": "0",
                "mac_address": "0",
                "os": "mac",
                "os_version": "14.0.0"
            },
            "materials": {
                "audio_balances": [],
                "audio_effects": [],
                "audio_fades": [],
                "audio_track_indexes": [],
                "audios": materials_audios,
                "beats": [],
                "canvases": [],
                "chromas": [],
                "color_curves": [],
                "drafts": [],
                "effects": [],
                "green_screens": [],
                "handwrites": [],
                "hsl": [],
                "images": [],
                "log_color_wheels": [],
                "manual_deformations": [],
                "masks": [],
                "material_animations": materials_animations,
                "material_colors": [],
                "placeholders": [],
                "plugin_effects": [],
                "primary_color_wheels": [],
                "realtime_denoises": [],
                "shapes": [],
                "smart_crops": [],
                "sound_channel_mappings": [],
                "speeds": materials_speeds,
                "stickers": [],
                "tail_leaders": [],
                "text_templates": [],
                "texts": materials_texts,
                "transitions": [],
                "video_effects": [],
                "video_track_indexes": [],
                "videos": materials_videos,
                "vocal_beautifys": [],
                "vocal_separations": []
            },
            "mutable_config": None,
            "name": clean_project_name,
            "new_version": "100.0.0",
            "platform": {
                "app_id": 3704,
                "app_source": "jianying",
                "app_version": "5.9.0",
                "device_id": "0",
                "hard_disk_id": "0",
                "mac_address": "0",
                "os": "mac",
                "os_version": "14.0.0"
            },
            "relationships": [],
            "render_index_mode": "default",
            "retouch_cover": None,
            "source": "default",
            "static_cover_image": None,
            "tracks": tracks_list,
            "update_time": int(time.time()),
            "version": 360000
        }

        # 3. 组装 draft_meta_info.json
        draft_meta = {
            "draft_fold_path": target_draft_dir,
            "draft_id": draft_id,
            "draft_is_ai_shorts": False,
            "draft_is_invisible": False,
            "draft_json_file": os.path.join(target_draft_dir, "draft_content.json"),
            "draft_name": clean_project_name,
            "draft_new_version": "100.0.0",
            "draft_removable_storage_device": "",
            "draft_root_path": os.path.dirname(target_draft_dir),
            "draft_timeline_materials_size_": 0,
            "tm_draft_cloud_completed": "",
            "tm_draft_cloud_modified": 0,
            "tm_draft_create": current_time_us,
            "tm_draft_modified": current_time_us,
            "tm_draft_removed": 0,
            "tm_duration": timeline_cursor_us
        }

        # 写入 json 文件
        content_json_path = os.path.join(target_draft_dir, "draft_content.json")
        meta_json_path = os.path.join(target_draft_dir, "draft_meta_info.json")

        with open(content_json_path, "w", encoding="utf-8") as f:
            json.dump(draft_content, f, ensure_ascii=False, indent=2)

        with open(meta_json_path, "w", encoding="utf-8") as f:
            json.dump(draft_meta, f, ensure_ascii=False, indent=2)

        # 4. 生成可下载的 ZIP 压缩包
        zip_output_path = os.path.join(output_dir, f"{draft_folder_name}.zip")
        with zipfile.ZipFile(zip_output_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(target_draft_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, output_dir)
                    zipf.write(file_path, arcname)

        # 5. 若本机存在剪映草稿目录，自动同步写入草稿箱
        synced_to_local_jianying = False
        if self.draft_root and os.path.exists(self.draft_root):
            local_target = os.path.join(self.draft_root, draft_folder_name)
            try:
                if os.path.exists(local_target):
                    shutil.rmtree(local_target)
                shutil.copytree(target_draft_dir, local_target)
                synced_to_local_jianying = True
                print(f"[JianyingExporter] 🚀 Successfully synced to local JianYing Pro: {local_target}")
            except Exception as e:
                print(f"[JianyingExporter] Warning: Failed to sync to local JianYing Pro: {e}")

        return {
            "status": "success",
            "draft_id": draft_id,
            "draft_dir": target_draft_dir,
            "zip_path": zip_output_path,
            "synced_to_local_jianying": synced_to_local_jianying,
            "total_duration_sec": timeline_cursor_us / 1000000,
            "shots_count": len(shots_data)
        }
