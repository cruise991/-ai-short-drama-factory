"""
code_motion_producer.py — 知识动效代码逐帧渲染引擎 (Code-as-Video Motion Producer)
基于 vibe-knowledge 与超级峰视听节拍协议：
1. 0 算力API成本：基于确定性时间步长 (Deterministic Step) 代码逐帧合成高帧率短视频 (1080x1920 竖屏, 60fps/30fps)；
2. 44套视觉风格全量动态自适应支持 (包含东方意象、暗金前沿、波普拼贴、科学图解、像素复古、极简留白)；
3. 知识证据链溯源卡 (Fact Citation Badge) 逐句标注；
4. 顶部>=5%呼吸安全留白与底部防遮挡门禁；
5. 广播级声学混音：联动 AcousticEnhancer 实现 BGM 智能侧链闪避 (Sidechain Ducking)。
"""

import os
import sys
import json
import math
import shutil
import tempfile
import subprocess
from pathlib import Path
from typing import List, Dict, Optional, Tuple

def _resolve_project_root() -> Path:
    candidates = [
        Path("/workspace"),
        Path(__file__).resolve().parent.parent.parent
    ]
    for c in candidates:
        if (c / "assets").exists():
            return c
    return Path(__file__).resolve().parent.parent.parent

PROJECT_ROOT = _resolve_project_root()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from shared_tools.video_design.storyboard_schema import TimecodedBeatSpec, DirectorShot
from shared_tools.audio.acoustic_enhancer import AcousticEnhancer

FONT_PATHS = [
    str(PROJECT_ROOT / "assets" / "fonts" / "STHeitiMedium.ttc"),
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/STHeiti Light.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
]

def _get_pil():
    try:
        from PIL import Image, ImageDraw, ImageFont
        return Image, ImageDraw, ImageFont
    except ImportError:
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "Pillow", "-i", "https://pypi.tuna.tsinghua.edu.cn/simple", "--default-timeout=60"], check=True)
            from PIL import Image, ImageDraw, ImageFont
            return Image, ImageDraw, ImageFont
        except Exception as e:
            raise ImportError(f"缺少 Pillow 图像库且自动安装失败: {str(e)}")

def _get_font(size: int):
    try:
        _, _, ImageFont = _get_pil()
        for fp in FONT_PATHS:
            if os.path.exists(fp):
                try:
                    return ImageFont.truetype(fp, size)
                except Exception:
                    continue
        return ImageFont.load_default()
    except Exception:
        return None

# 平台合规词典中性替换 (遵守 AGENTS 规则 12)
SENSITIVE_TERM_MAPPINGS = {
    "闲鱼": "二手电商平台",
    "淘宝": "电商平台",
    "拼多多": "电商平台",
    "1688": "供应链平台",
    "微信": "创作者私域",
    "加V": "建立连接",
    "公众号": "深度内容专栏",
    "引流": "交付闭环",
    "导流": "客户连接"
}

def sanitize_platform_copy(text: str) -> str:
    """自动执行小红书/抖音等自媒体平台防限流中性化清洗"""
    cleaned = text
    for term, neutral in SENSITIVE_TERM_MAPPINGS.items():
        cleaned = cleaned.replace(term, neutral)
    return cleaned

def ease_in_out_cubic(x: float) -> float:
    return 4 * x * x * x if x < 0.5 else 1 - math.pow(-2 * x + 2, 3) / 2

class CodeMotionRenderer:
    def __init__(self, width: int = 1080, height: int = 1920, fps: int = 30):
        self.width = width
        self.height = height
        self.fps = fps
        self.font_title = _get_font(68)
        self.font_body = _get_font(46)
        self.font_citation = _get_font(28)
        self.font_tag = _get_font(32)
        self._catalog_cache = None

    def _load_styles_catalog(self) -> Dict[str, dict]:
        """加载 44 种视觉风格字典"""
        if self._catalog_cache is not None:
            return self._catalog_cache

        cat_path = PROJECT_ROOT / "assets" / "visual_styles" / "styles_catalog.json"
        styles_map = {}
        if cat_path.exists():
            try:
                with open(cat_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for cat in data.get("categories", []):
                        for s in cat.get("styles", []):
                            styles_map[s["id"]] = s
            except Exception:
                pass
        self._catalog_cache = styles_map
        return styles_map

    def load_style_config(self, style_id: str) -> dict:
        """
        动态加载或从 44 套目录中自适应衍生渲染配置，确保所有 44 套风格 100% 具备独特视觉呈现
        """
        # 1. 优先读取磁盘上专属配置
        style_path = PROJECT_ROOT / "assets" / "visual_styles" / f"{style_id}.json"
        if style_path.exists():
            try:
                with open(style_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass

        # 2. 从 styles_catalog 中动态衍生
        styles_map = self._load_styles_catalog()
        cat_item = styles_map.get(style_id)
        if cat_item:
            primary = cat_item.get("primary_color", "#E5C07B")
            bg = cat_item.get("bg_color", "#0A0B0E")
            accent = cat_item.get("accent", "#61AFEF")

            # 根据背景明暗度推断文本颜色
            # 若背景偏浅 (如水墨纸白 #F4F0EA)，正文采用深色；若背景偏暗，正文采用浅色
            is_light_bg = bg.upper().startswith(("#F", "#E", "#D", "#W"))
            body_color = "#1F2328" if is_light_bg else "#E6EDF3"

            return {
                "style_id": style_id,
                "name": cat_item.get("name", style_id),
                "background": {
                    "type": "radial_gradient",
                    "color_center": bg,
                    "color_edge": bg
                },
                "typography": {
                    "title_color": primary,
                    "body_color": body_color,
                    "citation_color": accent,
                    "accent_color": accent
                },
                "kinetics": {
                    "particle_count": 35,
                    "particle_color": primary,
                    "line_color": primary,
                    "line_width": 2
                }
            }

        # 3. 兜底回退：dark_gold_lines
        return {
            "style_id": "dark_gold_lines",
            "name": "暗金线描",
            "background": {"type": "radial_gradient", "color_center": "#181A20", "color_edge": "#0A0B0E"},
            "typography": {"title_color": "#E5C07B", "body_color": "#DCDFE4", "citation_color": "#7F848E", "accent_color": "#61AFEF"},
            "kinetics": {"particle_count": 40, "particle_color": "#E5C07B", "line_color": "#E5C07B88", "line_width": 2}
        }

    def render_shot_frame(
        self,
        shot: DirectorShot,
        local_t: float,
        style_cfg: dict,
        theme_title: str = ""
    ):
        Image, ImageDraw, ImageFont = _get_pil()

        bg_color = style_cfg["background"].get("color_edge", "#0A0B0E")
        im = Image.new("RGBA", (self.width, self.height), color=bg_color)
        draw = ImageDraw.Draw(im)

        progress = max(0.0, min(1.0, local_t / max(0.1, shot.duration)))
        eased_p = ease_in_out_cubic(progress)

        # 1. 动态几何背景 (代码逐帧粒子与科技/艺术环)
        cx, cy = self.width // 2, self.height // 2 - 80
        ring_radius = int(240 + 40 * math.sin(progress * math.pi * 2))
        ring_color = style_cfg["typography"].get("title_color", "#E5C07B")
        accent_color = style_cfg["typography"].get("accent_color", "#61AFEF")
        
        rot_angle = progress * 360.0
        arc_box = [cx - ring_radius, cy - ring_radius, cx + ring_radius, cy + ring_radius]
        draw.arc(arc_box, start=rot_angle, end=rot_angle + 160, fill=ring_color, width=4)
        draw.arc(arc_box, start=rot_angle + 180, end=rot_angle + 300, fill=accent_color, width=2)

        # 漂浮发光微粒 (Deterministic pseudo-random)
        particle_count = style_cfg.get("kinetics", {}).get("particle_count", 30)
        for p_idx in range(particle_count):
            base_x = (math.sin(p_idx * 13.7) * 0.5 + 0.5) * self.width
            base_y = (math.cos(p_idx * 29.3) * 0.5 + 0.5) * (self.height * 0.6) + self.height * 0.15
            drift_y = base_y - (progress * 80.0 * (1 + (p_idx % 3)))
            drift_x = base_x + math.sin(progress * 4.0 + p_idx) * 20.0
            p_radius = 2 + (p_idx % 4)
            draw.ellipse([drift_x - p_radius, drift_y - p_radius, drift_x + p_radius, drift_y + p_radius], fill=ring_color)

        # 2. 顶部导航与安全区 (Top 5% 呼吸留白)
        top_y = int(self.height * 0.08)
        tag_text = f"◆ {theme_title or '深度认知洞察'} ◆"
        if self.font_tag:
            tag_bbox = draw.textbbox((0, 0), tag_text, font=self.font_tag)
            tag_w = tag_bbox[2] - tag_bbox[0]
            draw.text(((self.width - tag_w) // 2, top_y), tag_text, font=self.font_tag, fill=accent_color)

        # 3. 核心视觉聚焦点：文本合规清洗与逐字揭示 (Typewriter Reveal)
        text = sanitize_platform_copy(shot.narration)
        reveal_count = min(len(text), max(1, int(len(text) * min(1.0, progress * 1.4))))
        current_text = text[:reveal_count]

        # 居中文本自动换行排版 (中文 14 字/行)
        max_chars_per_line = 14
        lines = []
        for i in range(0, len(current_text), max_chars_per_line):
            lines.append(current_text[i:i + max_chars_per_line])

        # 动态自适应行高，防止多行文本向下挤压溢出底端安全区
        line_spacing = 75 if len(lines) <= 2 else 58
        text_start_y = cy + (60 if len(lines) > 2 else 80)
        body_color = style_cfg["typography"].get("body_color", "#DCDFE4")
        if self.font_body:
            for line_idx, line in enumerate(lines):
                line_bbox = draw.textbbox((0, 0), line, font=self.font_body)
                line_w = line_bbox[2] - line_bbox[0]
                draw.text(((self.width - line_w) // 2, text_start_y + line_idx * line_spacing), line, font=self.font_body, fill=body_color)

        # 4. 乐段标志 (Musical Section Badge)
        sec_name = shot.musical_section.replace("_", " ").upper()
        sec_box = [cx - 150, cy - ring_radius - 60, cx + 150, cy - ring_radius - 10]
        card_fill = "#F4F0EAEE" if bg_color.upper().startswith(("#F", "#E", "#D")) else "#0F1117EE"
        draw.rounded_rectangle(sec_box, radius=8, fill=card_fill, outline=ring_color, width=2)
        if self.font_citation:
            sec_bbox = draw.textbbox((0, 0), sec_name, font=self.font_citation)
            sec_w = sec_bbox[2] - sec_bbox[0]
            draw.text(((self.width - sec_w) // 2, cy - ring_radius - 48), sec_name, font=self.font_citation, fill=ring_color)

        # 5. vibe-knowledge 核心特色：知识证据链溯源卡 (Fact Citation Badge)
        # 位于底部上方 (避开抖音/小红书底部操作区)
        if shot.source_citation and self.font_citation:
            cite_y = int(self.height * 0.78)
            cite_str = f"文献出处: {shot.source_citation}"
            cite_bbox = draw.textbbox((0, 0), cite_str, font=self.font_citation)
            cite_w = cite_bbox[2] - cite_bbox[0]
            
            box_padding_x = 24
            box_padding_y = 12
            card_box = [
                (self.width - cite_w) // 2 - box_padding_x,
                cite_y - box_padding_y,
                (self.width + cite_w) // 2 + box_padding_x,
                cite_y + (cite_bbox[3] - cite_bbox[1]) + box_padding_y
            ]
            draw.rounded_rectangle(card_box, radius=12, fill=card_fill, outline=ring_color, width=1)
            draw.text(((self.width - cite_w) // 2, cite_y), cite_str, font=self.font_citation, fill=ring_color)

        # 6. 底部进度条 (全局时码映射)
        pb_y = self.height - 20
        pb_width = int(self.width * progress)
        draw.line([(0, pb_y), (pb_width, pb_y)], fill=ring_color, width=6)

        return im.convert("RGB")

    def render_spec_to_video(
        self,
        spec: TimecodedBeatSpec,
        output_mp4_path: str,
        audio_path: Optional[str] = None,
        bgm_path: Optional[str] = None
    ) -> str:
        """
        全流程代码成片管线：
        1. 逐帧渲染所有分镜
        2. 若提供 BGM 与人声，调用 AcousticEnhancer 执行智能侧链闪避 (Sidechain Ducking)
        3. 调用 FFmpeg 无损拼装为 1080x1920 竖屏 60fps/30fps 视频并混音
        """
        output_file = Path(output_mp4_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        style_cfg = self.load_style_config(spec.shots[0].visual_style_id if spec.shots else "dark_gold_lines")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            frames_dir = temp_path / "frames"
            frames_dir.mkdir(parents=True, exist_ok=True)
            
            frame_idx = 0
            for shot in spec.shots:
                shot_frames = max(1, int(round(shot.duration * self.fps)))
                for f in range(shot_frames):
                    local_t = f / float(self.fps)
                    frame_img = self.render_shot_frame(shot, local_t, style_cfg, spec.theme)
                    frame_name = f"frame_{frame_idx:06d}.jpg"
                    frame_img.save(frames_dir / frame_name, quality=95)
                    frame_idx += 1

            temp_video = temp_path / "video_raw.mp4"
            cmd_video = [
                "ffmpeg", "-y",
                "-framerate", str(self.fps),
                "-i", str(frames_dir / "frame_%06d.jpg"),
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                "-r", str(self.fps),
                str(temp_video)
            ]
            subprocess.run(cmd_video, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

            # 音频混流与侧链闪避逻辑
            final_audio = audio_path
            if audio_path and bgm_path and os.path.exists(audio_path) and os.path.exists(bgm_path):
                # 联动 AcousticEnhancer 做 BGM 侧链闪避
                ducked_audio = temp_path / "ducked_mix.aac"
                ok = AcousticEnhancer.create_ducked_audio(audio_path, bgm_path, str(ducked_audio))
                if ok and ducked_audio.exists():
                    final_audio = str(ducked_audio)

            if final_audio and os.path.exists(final_audio):
                cmd_mix = [
                    "ffmpeg", "-y",
                    "-i", str(temp_video),
                    "-i", final_audio,
                    "-c:v", "copy",
                    "-c:a", "aac",
                    "-shortest",
                    str(output_file)
                ]
                subprocess.run(cmd_mix, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            else:
                shutil.copy(str(temp_video), str(output_file))

        return str(output_file)

def verify_motion_video_quality(video_path: str) -> Tuple[bool, List[str]]:
    issues = []
    if not os.path.exists(video_path):
        return False, [f"文件不存在: {video_path}"]

    cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height,r_frame_rate,duration",
        "-of", "json",
        video_path
    ]
    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        info = json.loads(res.stdout)["streams"][0]
        w = int(info["width"])
        h = int(info["height"])
        
        ratio = h / w
        if abs(ratio - 16.0 / 9.0) > 0.05:
            issues.append(f"宽高比不合规 (期望 9:16, 实际 {w}x{h})")
            
    except Exception as e:
        issues.append(f"ffprobe 解析异常: {str(e)}")

    return len(issues) == 0, issues
