#!/usr/bin/env python3
"""Integration and aspect-ratio validation tests for agent-video-pipeline & drama closed-loop."""

import importlib
import json
import os
import subprocess
from pathlib import Path

import pytest
from shared_tools.explainer_adapter import ExplainerPipelineAdapter
from orchestrator import run_marketing_recap_pipeline

planning_mod = importlib.import_module("departments.02_planning.planning_agent")
generate_marketing_recap = planning_mod.generate_marketing_recap


@pytest.fixture
def sample_avatar_image(tmp_path):
    """Generate a clean test face image."""
    img_path = tmp_path / "avatar_test.png"
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", "color=c=0x3498db:s=512x512:d=1",
        "-vframes", "1",
        str(img_path)
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return img_path


def get_video_metadata(video_path: Path) -> dict:
    """Extract width, height, aspect ratio from video via ffprobe."""
    cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height,sample_aspect_ratio,display_aspect_ratio",
        "-of", "json",
        str(video_path)
    ]
    res = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    info = json.loads(res.stdout)
    return info["streams"][0]


def test_input_validation():
    adapter = ExplainerPipelineAdapter()
    
    with pytest.raises(ValueError, match="cannot be empty"):
        adapter.validate_inputs("")

    with pytest.raises(ValueError, match="too short"):
        adapter.validate_inputs("你好")

    with pytest.raises(FileNotFoundError):
        adapter.validate_inputs("这是一个合法的口播文案测试内容。", avatar_image=Path("/non_existent_avatar.png"))


def test_circuit_breaker():
    adapter = ExplainerPipelineAdapter(max_retries=3)
    
    for _ in range(2):
        with pytest.raises(Exception):
            adapter.run_explainer_task("bad_task", script_text="")
    
    with pytest.raises(RuntimeError, match="Circuit Breaker Triggered"):
        adapter.run_explainer_task("bad_task", script_text="")


def test_aspect_ratio_vertical_vs_horizontal(sample_avatar_image):
    """Verify 9:16 vertical and 16:9 horizontal outputs have strict dimensions and no distortion."""
    adapter = ExplainerPipelineAdapter()
    test_text = "这是一段用于测试竖屏与横屏安全区排版及比例严格性的口播文本。"
    
    # 1. Test 9:16 Vertical
    res_v = adapter.run_explainer_task(
        task_id="test_vertical_9_16",
        script_text=test_text,
        avatar_image=sample_avatar_image,
        mode="pip",
        canvas="9:16",
    )
    meta_v = get_video_metadata(Path(res_v["output_video"]))
    assert meta_v["width"] == 1080
    assert meta_v["height"] == 1920
    assert meta_v.get("sample_aspect_ratio", "1:1") in ("1:1", "1/1")

    # 2. Test 16:9 Horizontal
    res_h = adapter.run_explainer_task(
        task_id="test_horizontal_16_9",
        script_text=test_text,
        avatar_image=sample_avatar_image,
        mode="pip",
        canvas="16:9",
    )
    meta_h = get_video_metadata(Path(res_h["output_video"]))
    assert meta_h["width"] == 1920
    assert meta_h["height"] == 1080
    assert meta_h.get("sample_aspect_ratio", "1:1") in ("1:1", "1/1")


def test_drama_to_marketing_closed_loop(tmp_path, sample_avatar_image):
    """Test Phase 3 automated closed-loop: drama project -> marketing recap script -> explainer video."""
    drama_run = tmp_path / "mock_drama_ep01"
    scripts_dir = drama_run / "01_storyboards_scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    
    ticket = {
        "goal": "重生成为千亿总裁",
        "style": "爽剧反转",
        "aspect_ratio": "9:16",
    }
    with open(drama_run / "00_task_ticket.json", "w", encoding="utf-8") as f:
        json.dump(ticket, f, ensure_ascii=False, indent=2)

    storyboard_md = """# 第1集：真假继承人
## Shot 01 (0-5s)
画面：主角冷笑，拿出一纸合同。
台词：“这份千亿家产，现在是我的了！”
"""
    with open(scripts_dir / "01_storyboard.md", "w", encoding="utf-8") as f:
        f.write(storyboard_md)

    # 1. Test recap script extraction
    recap_info = generate_marketing_recap(str(drama_run))
    assert "text" in recap_info
    assert len(recap_info["text"]) > 10

    # 2. Test orchestrator auto-marketing pipeline
    workspace_dir = str(Path(__file__).resolve().parent.parent)
    out_video = run_marketing_recap_pipeline(workspace_dir, str(drama_run), ticket)
    assert Path(out_video).exists()
    assert Path(out_video).stat().st_size > 1024
