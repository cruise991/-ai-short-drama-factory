"""
test_video_design_and_code_motion.py — 针对 chaojifeng-video-design 与 vibe-knowledge 整合的单元与回归测试
"""

import os
import sys
import unittest
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from shared_tools.video_design.storyboard_schema import (
    TimecodedBeatSpec, DirectorShot, AudioVisualSyncRule
)
from shared_tools.video_design.visual_focus_router import (
    resolve_focus_relay, validate_focus_continuity
)
from shared_tools.video_design.beat_rhythm_engine import (
    calculate_shot_timing_from_bpm,
    estimate_word_budget,
    generate_director_storyboard,
    re_roll_single_shot
)
from shared_tools.video_design.code_motion_producer import (
    CodeMotionRenderer,
    verify_motion_video_quality
)

class TestVideoDesignAndCodeMotion(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="test_vd_")

    def test_01_bpm_quantization_and_timing(self):
        """测试 1: 验证 BPM 量化到音乐小节的时码划分 (chaojifeng-video-design)"""
        cuts = calculate_shot_timing_from_bpm(bpm=120.0, total_duration=15.0, shot_count=4)
        self.assertEqual(len(cuts), 4)
        self.assertEqual(cuts[0][0], 0.0)
        self.assertEqual(cuts[-1][1], 15.0)
        for start, end, section in cuts:
            self.assertGreater(end, start)
            self.assertIn(section, ["Intro_Hook", "Verse_Setup", "Build_Up", "Chorus_Climax"])

    def test_02_visual_focus_relay_and_continuity(self):
        """测试 2: 验证视线焦点接力与跳变质检"""
        entry_f, trans = resolve_focus_relay("center", "whip_pan_right")
        self.assertEqual(entry_f, "center_left")
        self.assertEqual(trans, "whip_pan_right")

        ok, msg = validate_focus_continuity("center", "center", "cut")
        self.assertTrue(ok)

        ok_jump, alert_msg = validate_focus_continuity("top_left", "bottom_right", "cut")
        self.assertFalse(ok_jump)
        self.assertIn("视觉眼跳预警", alert_msg)

    def test_03_director_storyboard_generation_and_re_roll(self):
        """测试 3: 验证完整的导演分镜生成与单镜头局部重编 (Re-roll)"""
        narrations = [
            "第一句：传统算力已经逼近物理极限。",
            "第二句：量子世界中叠加态改写了规则。",
            "第三句：这不是快十倍，是复杂度的降维打击。",
            "第四句：未来三年将重构整个密码与安全产业。"
        ]
        citations = ["Nature 2024", "IBM Quantum", "MIT Tech Review", "Science 2025"]
        
        spec = generate_director_storyboard(
            project_id="test_proj",
            episode_id="EP_TEST",
            theme="量子计算",
            narrations=narrations,
            bpm=120.0,
            total_duration=15.0,
            visual_style_id="dark_gold_lines",
            citations=citations
        )
        
        self.assertEqual(spec.project_id, "test_proj")
        self.assertEqual(len(spec.shots), 4)
        self.assertEqual(spec.shots[0].shot_id, "S01")
        self.assertEqual(spec.shots[0].source_citation, "Nature 2024")
        self.assertEqual(spec.shots[0].character_count, len(narrations[0]))

        new_text = "第二句全新改写：量子叠加态创造出指数级的并行通道。"
        spec_updated, success, msg = re_roll_single_shot(
            spec=spec,
            shot_id="S02",
            new_narration=new_text,
            new_style_id="ink_wash_scroll",
            new_camera_movement="push_in"
        )
        self.assertTrue(success)
        self.assertEqual(spec_updated.shots[1].narration, new_text)
        self.assertEqual(spec_updated.shots[1].visual_style_id, "ink_wash_scroll")
        self.assertEqual(spec_updated.shots[0].time_start, spec.shots[0].time_start)
        self.assertEqual(spec_updated.shots[2].time_start, spec.shots[2].time_start)

    def test_04_code_motion_renderer_frame_generation(self):
        """测试 4: 验证代码动效渲染器逐帧合成能力 (vibe-knowledge)"""
        renderer = CodeMotionRenderer(width=540, height=960, fps=15)
        cfg = renderer.load_style_config("dark_gold_lines")
        
        shot = DirectorShot(
            shot_id="S01",
            beat_index=1,
            time_start=0.0,
            time_end=3.0,
            duration=3.0,
            narration="测试代码逐帧动效渲染画面",
            musical_section="Intro_Hook",
            source_citation="arXiv:2026.12345"
        )
        
        frame = renderer.render_shot_frame(shot, local_t=1.5, style_cfg=cfg, theme_title="单元测试主题")
        self.assertEqual(frame.size, (540, 960))
        
        test_frame_path = os.path.join(self.temp_dir, "test_frame.jpg")
        frame.save(test_frame_path)
        self.assertTrue(os.path.exists(test_frame_path))
        self.assertGreater(os.path.getsize(test_frame_path), 1000)

if __name__ == "__main__":
    unittest.main()
