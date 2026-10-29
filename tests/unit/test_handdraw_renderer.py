import os
import sys
import unittest
import tempfile
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw

# Add workspace paths
AI_DRAMA_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(AI_DRAMA_ROOT))

from shared_tools.renderers import get_renderer, HanddrawRenderer, AgnesRenderer


class TestHanddrawRendererIntegration(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="test_handdraw_")
        self.test_img = os.path.join(self.temp_dir, "test_input.png")
        self.output_video = os.path.join(self.temp_dir, "output_film.mp4")
        
        # Create a simple test illustration image
        img = Image.new("RGBA", (400, 300), (255, 255, 255, 0))
        draw = ImageDraw.Draw(img)
        # Draw a house with ink strokes
        draw.polygon([(200, 40), (80, 140), (320, 140)], fill="#E26D5C", outline="#252525", width=4)
        draw.rectangle([(100, 140), (300, 280)], fill="#FFE3A8", outline="#252525", width=4)
        draw.rectangle([(170, 200), (230, 280)], fill="#3F88C5", outline="#252525", width=3)
        img.save(self.test_img)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_renderer_factory_routing(self):
        """Verify get_renderer dispatches HanddrawRenderer based on shot or config."""
        config_default = {"dance_factory": {}}
        renderer_default = get_renderer("Draft", False, config_default)
        self.assertIsInstance(renderer_default, AgnesRenderer)

        # Route by phase
        renderer_phase = get_renderer("Handdraw", False, config_default)
        self.assertIsInstance(renderer_phase, HanddrawRenderer)

        # Route by shot_type
        shot = {"shot_id": "shot_01", "shot_type": "handdraw_whiteboard"}
        renderer_shot = get_renderer("Draft", False, config_default, shot=shot)
        self.assertIsInstance(renderer_shot, HanddrawRenderer)

        # Route by project_type in config
        config_handdraw = {"project_type": "handdraw"}
        renderer_config = get_renderer("Draft", False, config_handdraw)
        self.assertIsInstance(renderer_config, HanddrawRenderer)

    def test_handdraw_video_generation(self):
        """Verify HanddrawRenderer generates an actual valid mp4 video."""
        renderer = HanddrawRenderer()
        config = {
            "voice_script": "线索推演：嫌疑人在案发前曾在此处停留",
        }
        shot = {
            "shot_id": "deduction_shot_1",
            "voice_script": "线索推演：嫌疑人在案发前曾在此处停留",
            "shot_type": "handdraw"
        }
        
        success = renderer.generate_video_with_frames(
            source_image=self.test_img,
            prompt="嫌疑人行动路线推演",
            output_path=self.output_video,
            config=config,
            num_frames=150, # 5.0s standard shot render
            size="720x1280", # 9:16 mobile canvas
            shot=shot
        )

        
        self.assertTrue(success, "HanddrawRenderer failed to generate video")
        self.assertTrue(os.path.exists(self.output_video), "Output video does not exist")
        self.assertGreater(os.path.getsize(self.output_video), 1000, "Output video is empty or too small")
        
        # Verify valid mp4 container with ffprobe
        probe_cmd = [
            "ffprobe", "-v", "error", "-show_entries", "format=duration,format_name",
            "-of", "default=noprint_wrappers=1:nokey=1", self.output_video
        ]
        result = subprocess.run(probe_cmd, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, f"ffprobe error: {result.stderr}")
        self.assertIn("mov,mp4", result.stdout)


if __name__ == "__main__":
    unittest.main()
