"""
Automated Comprehensive Regression Test Suite (全量功能与部署回归测试)
Covers:
1. JianYing Pro Draft Exporter (剪映双模原生草稿、1080x1920竖屏、12%缓推运镜、ZIP打包)
2. Acoustic Space & BGM Sidechain Ducking (VoiceStudio 空间声学混响与人声侧链闪避)
3. Dance Pose Gallery API (ai-pose-gallery-zh 5视角4阶段动作检索)
4. Choreography Recipe Lifecycle (配方保存、唯一ID签发与一键同款读取)
5. Docker Container Health & Web Endpoints (前端 3008 与 后端 8008 服务存活核验)
"""

import os
import sys
import json
import zipfile
import tempfile
import requests
import unittest

WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(WORKSPACE_DIR)

from shared_tools.drafts.jianying_exporter import JianyingExporter
from shared_tools.audio.acoustic_enhancer import AcousticEnhancer

# 端口自适应：容器内访问 8000，宿主机访问 8008
BACKEND_PORT = "8000" if (os.path.exists("/.dockerenv") or os.path.exists("/app")) else "8008"

class TestOpenSourceIntegrationV5(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="test_v5_")

    def test_01_jianying_draft_export_and_zip(self):
        """测试 1: 剪映专业版工程草稿生成与 ZIP 打包合法性"""
        exporter = JianyingExporter()
        
        # 构造模拟分镜数据
        dummy_video = os.path.join(self.temp_dir, "shot01.mp4")
        with open(dummy_video, "wb") as f:
            f.write(b"fake_mp4_bytes")

        shots_data = [
            {
                "id": "shot_01",
                "video_path": dummy_video,
                "audio_path": None,
                "duration": 3.0,
                "subtitle": "天龙集团新董事长林宇，第一天就被当成外卖员轰出门外？",
                "enable_slow_zoom": True
            },
            {
                "id": "shot_02",
                "video_path": dummy_video,
                "audio_path": None,
                "duration": 2.5,
                "subtitle": "周经理，你刚才说谁是穷酸的底层？",
                "enable_slow_zoom": True
            }
        ]

        dummy_bgm = os.path.join(self.temp_dir, "cinematic_bgm.mp3")
        with open(dummy_bgm, "wb") as f:
            f.write(b"fake_bgm_bytes")

        result = exporter.export_project_draft(
            project_name="Test_Regression_Drama",
            shots_data=shots_data,
            output_dir=self.temp_dir,
            bgm_path=dummy_bgm,
            canvas_width=1080,
            canvas_height=1920,
            fps=25
        )

        self.assertIsNotNone(result)
        self.assertIn("zip_path", result)
        zip_path = result["zip_path"]
        self.assertTrue(os.path.exists(zip_path), f"ZIP draft file not found: {zip_path}")

        # 检查 ZIP 内文件结构
        with zipfile.ZipFile(zip_path, "r") as zf:
            namelist = zf.namelist()
            # 必须包含 draft_content.json 与 draft_meta_info.json
            has_content = any("draft_content.json" in name for name in namelist)
            has_meta = any("draft_meta_info.json" in name for name in namelist)
            self.assertTrue(has_content, "Missing draft_content.json in draft zip")
            self.assertTrue(has_meta, "Missing draft_meta_info.json in draft zip")

            # 验证 draft_content.json 的画幅和结构以及 BGM 独立音轨
            for name in namelist:
                if "draft_content.json" in name:
                    content_bytes = zf.read(name)
                    content_json = json.loads(content_bytes.decode("utf-8"))
                    canvas_cfg = content_json.get("canvas_config", {})
                    self.assertEqual(canvas_cfg.get("width"), 1080, "Canvas width must be 1080")
                    self.assertEqual(canvas_cfg.get("height"), 1920, "Canvas height must be 1920")
                    self.assertEqual(canvas_cfg.get("ratio"), "9:16", "Canvas ratio must be 9:16")

                    # 验证独立分轨：主视频轨、旁白音频轨、可编辑硬字幕轨、背景音乐轨
                    tracks = content_json.get("tracks", [])
                    track_names = [t.get("name") for t in tracks]
                    self.assertIn("主视频轨", track_names)
                    self.assertIn("旁白音频轨", track_names)
                    self.assertIn("可编辑硬字幕轨", track_names)
                    self.assertIn("背景音乐轨", track_names)

    def test_02_acoustic_presets_and_matching(self):
        """测试 2: VoiceStudio 空间声学环境预设与自适应匹配逻辑"""
        presets = AcousticEnhancer.ACOUSTIC_PRESETS
        self.assertIn("lobby", presets)
        self.assertIn("rainy_night", presets)
        self.assertIn("luxury_car", presets)
        self.assertIn("studio_dry", presets)
        self.assertIn("cinematic_reverb", presets)

        # 验证智能环境匹配
        p1 = AcousticEnhancer.match_acoustic_preset("劳斯莱斯后排，林宇端坐，神色冷峻")
        self.assertEqual(p1, "luxury_car")

        p2 = AcousticEnhancer.match_acoustic_preset("天龙集团挑高三十米的大堂，回音阵阵")
        self.assertEqual(p2, "lobby")

        p3 = AcousticEnhancer.match_acoustic_preset("雨夜街头，冷风如刀，主角孤身伫立")
        self.assertEqual(p3, "rainy_night")

    def test_03_pose_gallery_api(self):
        """测试 3: 后端动作知识库接口 (/api/dance/poses)"""
        url = f"http://localhost:{BACKEND_PORT}/api/dance/poses"
        try:
            res = requests.get(url, timeout=5)
            self.assertEqual(res.status_code, 200, f"Pose gallery API returned {res.status_code}")
            data = res.json()
            self.assertIn("categories", data)
            self.assertIn("angles", data)
            self.assertIn("poses", data)
            self.assertGreaterEqual(len(data["poses"]), 10, "Should contain at least 10 poses")

            # 验证分类过滤
            res_intro = requests.get(f"{url}?category=intro", timeout=5)
            self.assertEqual(res_intro.status_code, 200)
            intro_data = res_intro.json()
            for p in intro_data["poses"]:
                self.assertEqual(p["category"], "intro")

            # 验证视角过滤
            res_angle = requests.get(f"{url}?angle=oblique", timeout=5)
            self.assertEqual(res_angle.status_code, 200)
            angle_data = res_angle.json()
            for p in angle_data["poses"]:
                self.assertIn("oblique", p.get("available_angles", []))
        except requests.exceptions.ConnectionError:
            self.skipTest("Backend server on localhost:8008 not reachable in current env")

    def test_04_choreography_recipe_api(self):
        """测试 4: 编舞配方保存与一键同款读取 (/api/dance/recipe)"""
        url_save = f"http://localhost:{BACKEND_PORT}/api/dance/recipe"
        sample_recipe = {
            "title": "回归测试·女团高光编舞",
            "creator": "Tester",
            "style": "kpop",
            "bpm": 128,
            "sequence": [
                {
                    "pose_id": "intro_hip_hand_01",
                    "name": "单手叉腰·微仰起势",
                    "category": "intro",
                    "angle": "oblique",
                    "beats": 4,
                    "seconds": 2.0
                },
                {
                    "pose_id": "rhythm_kpop_sway_01",
                    "name": "K-Pop 动感摆胯",
                    "category": "rhythm",
                    "angle": "front",
                    "beats": 4,
                    "seconds": 2.0
                }
            ]
        }

        try:
            res = requests.post(url_save, json=sample_recipe, timeout=5)
            self.assertEqual(res.status_code, 200, f"Save recipe returned {res.status_code}")
            save_res = res.json()
            self.assertIn("recipe_id", save_res)
            rec_id = save_res["recipe_id"]

            # 读取配方
            url_get = f"http://localhost:{BACKEND_PORT}/api/dance/recipe/{rec_id}"
            res_get = requests.get(url_get, timeout=5)
            self.assertEqual(res_get.status_code, 200)
            get_data = res_get.json()
            self.assertEqual(get_data.get("title"), sample_recipe["title"])
            self.assertEqual(len(get_data.get("sequence", [])), 2)
        except requests.exceptions.ConnectionError:
            self.skipTest("Backend server on localhost:8008 not reachable in current env")

    def test_05_frontend_and_backend_health(self):
        """测试 5: 前后端 Docker 容器 HTTP 存活探针"""
        try:
            fe_res = requests.get("http://localhost:3008", timeout=5)
            self.assertEqual(fe_res.status_code, 200, "Frontend container port 3008 must return 200")
            self.assertIn("html", fe_res.text.lower())
        except requests.exceptions.ConnectionError:
            self.skipTest("Frontend container port 3008 not reachable")

        try:
            be_res = requests.get(f"http://localhost:{BACKEND_PORT}/docs", timeout=5)
            self.assertEqual(be_res.status_code, 200, "Backend OpenAPI port 8008 must return 200")
        except requests.exceptions.ConnectionError:
            self.skipTest("Backend OpenAPI port 8008 not reachable")

    def test_06_project_assets_dual_delivery(self):
        """测试 6: 短剧项目资源双模交付与 JWT 鉴权端点 (/api/projects/{slug}/assets)"""
        try:
            from server.core.security import create_access_token
        except ImportError:
            self.skipTest("Host environment missing server python dependencies (python-jose)")
        test_slug = "regression_test_dual_delivery"
        out_test_dir = os.path.join(WORKSPACE_DIR, "out", test_slug)
        os.makedirs(out_test_dir, exist_ok=True)

        dummy_mp4 = os.path.join(out_test_dir, "episode_01.mp4")
        dummy_draft = os.path.join(out_test_dir, f"{test_slug}_jianying_draft.zip")
        dummy_srt = os.path.join(out_test_dir, "episode_01.srt")

        with open(dummy_mp4, "wb") as f: f.write(b"dummy_mp4_content")
        with open(dummy_draft, "wb") as f: f.write(b"dummy_draft_zip_content")
        with open(dummy_srt, "wb") as f: f.write(b"dummy_srt_subtitles")

        try:
            token = create_access_token({"sub": "admin", "tenant_id": "default", "role": "admin"})
            headers = {"Authorization": f"Bearer {token}"}
            url = f"http://localhost:{BACKEND_PORT}/api/projects/{test_slug}/assets"
            
            res = requests.get(url, headers=headers, timeout=5)
            self.assertEqual(res.status_code, 200, f"Get project assets returned {res.status_code}")
            data = res.json()
            
            self.assertIn("videos", data)
            self.assertIn("images", data)
            self.assertIn("drafts", data)
            self.assertIn("subtitles", data)
            
            self.assertTrue(any(f"{test_slug}_jianying_draft.zip" in d for d in data["drafts"]), "Draft zip not found in drafts list")
            self.assertTrue(any("episode_01.srt" in s for s in data["subtitles"]), "SRT subtitle not found in subtitles list")
            self.assertTrue(any("episode_01.mp4" in v for v in data["videos"]), "MP4 video not found in videos list")
        finally:
            import shutil
            shutil.rmtree(out_test_dir, ignore_errors=True)

    def test_07_video_design_and_code_motion_integration(self):
        """测试 7: 超级峰视频设计方法论与 vibe-knowledge 44套代码风格及代码成片接口"""
        try:
            from server.core.security import create_access_token
        except ImportError:
            self.skipTest("Host environment missing server python dependencies (python-jose)")
        token = create_access_token({"sub": "admin", "tenant_id": "default", "role": "admin"})
        headers = {"Authorization": f"Bearer {token}"}
        base_url = f"http://localhost:{BACKEND_PORT}/api/v1/video-design"
        
        try:
            # 1. 验证 44 种视觉风格字典
            res_styles = requests.get(f"{base_url}/styles", headers=headers, timeout=5)
            self.assertEqual(res_styles.status_code, 200)
            catalog = res_styles.json()["data"]
            self.assertEqual(catalog["total_styles"], 44)
            self.assertEqual(len(catalog["categories"]), 6)
            
            # 2. 验证节拍编排与时码切分
            payload_analyze = {
                "project_id": "reg_test_vd",
                "episode_id": "EP01",
                "theme": "量子纠缠的微观图景",
                "narrations": [
                    "在两个相距光年的粒子之间，",
                    "一种神秘的瞬时协同打破了局域实在性。"
                ],
                "citations": ["PRL 2024", "Bell Theorem Analysis"],
                "bpm": 120.0,
                "total_duration": 4.0,
                "visual_style_id": "dark_gold_lines"
            }
            res_analyze = requests.post(f"{base_url}/beats/analyze", json=payload_analyze, headers=headers, timeout=5)
            self.assertEqual(res_analyze.status_code, 200)
            spec = res_analyze.json()["spec"]
            self.assertEqual(len(spec["shots"]), 2)
            self.assertEqual(spec["shots"][0]["musical_section"], "Intro_Hook")
            
            # 3. 验证单镜头可寻址微调 (Re-roll)
            payload_reroll = {
                "spec": spec,
                "shot_id": "S01",
                "new_narration": "改写：微观尺度上的量子叠加与隐形传态。",
                "new_camera_movement": "push_in"
            }
            res_reroll = requests.post(f"{base_url}/shots/re-roll", json=payload_reroll, headers=headers, timeout=5)
            self.assertEqual(res_reroll.status_code, 200)
            updated_spec = res_reroll.json()["spec"]
            self.assertIn("微观尺度", updated_spec["shots"][0]["narration"])
        except requests.exceptions.ConnectionError:
            self.skipTest("Backend server on localhost:8008 not reachable in current env")

if __name__ == "__main__":
    unittest.main()
