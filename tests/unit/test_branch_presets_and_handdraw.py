import pytest
import os
import sys

# Append server directory
SERVER_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../server"))
if SERVER_DIR not in sys.path:
    sys.path.insert(0, SERVER_DIR)

from api.routes.config import get_branch_presets
from models.database import Project, create_db_and_tables, engine
from sqlmodel import Session, select

def test_branch_presets_schema():
    """Verify that get_branch_presets returns all essential assets for the 5 pipelines."""
    data = get_branch_presets()
    assert isinstance(data, dict)
    
    # 1. Transformation assets
    assert "costumes" in data
    assert "scenes" in data
    assert "motions" in data
    
    # 2. Handdraw presets
    assert "hands" in data
    assert len(data["hands"]) >= 4
    hand_ids = [h["id"] for h in data["hands"]]
    assert "teacher-pen" in hand_ids
    assert "cardigan-fountain" in hand_ids
    
    assert "papers" in data
    paper_ids = [p["id"] for p in data["papers"]]
    assert "ivory_white" in paper_ids
    
    assert "caption_styles" in data
    caption_ids = [c["id"] for c in data["caption_styles"]]
    assert "pill_dark" in caption_ids
    
    # Check WCAG compliance attributes in pill_dark
    pill_dark = next(c for c in data["caption_styles"] if c["id"] == "pill_dark")
    assert pill_dark["bg_opacity"] >= 0.8
    assert pill_dark["text_color"] == "#FFFFFF"

def test_project_model_branch_fields():
    """Verify Project database model supports multi-branch fields."""
    project = Project(
        project_slug="test_slug_123",
        goal="测试多分支工程",
        branch_type="handdraw_video",
        hand_preset="teacher-pen",
        caption_style="pill_dark",
        costume_id="cyber_dress",
        scene_id="cyber_street",
        motion_id="model_spin",
        status="Pending"
    )
    assert project.branch_type == "handdraw_video"
    assert project.hand_preset == "teacher-pen"
    assert project.caption_style == "pill_dark"
    assert project.costume_id == "cyber_dress"
