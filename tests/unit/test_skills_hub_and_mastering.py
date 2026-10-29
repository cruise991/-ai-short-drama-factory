import pytest
import os
import sys
from pathlib import Path

# Append root directory
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from shared_tools.skills_registry import SkillsRegistry, ContentPipelineEngine
from shared_tools.audio_mastering import AudioMasteringStudio

def test_skills_registry_discovery():
    """Verify SkillsRegistry auto-discovers and registers standard 5-tier skills."""
    skills = SkillsRegistry.list_all()
    assert len(skills) >= 5
    skill_ids = [s.id for s in skills]
    assert "agent-reach" in skill_ids
    assert "opencli" in skill_ids
    assert "notebooklm" in skill_ids
    assert "baoyu" in skill_ids
    assert "humanizer-zh" in skill_ids

def test_humanizer_pipeline_cleaning():
    """Verify ContentPipelineEngine strips banned AI clichés and conclusion tones."""
    raw = "在这个快节奏的时代，众所周知，总而言之，前额叶皮层供能骤降。"
    polished = ContentPipelineEngine.humanize_text(raw)
    assert "在这个快节奏的时代" not in polished
    assert "众所周知" not in polished
    assert "总而言之" not in polished
    assert "理智脑直接被拉闸断电" in polished

def test_baoyu_structure_generator():
    """Verify baoyu 3-act Gestalt structuring output."""
    res = ContentPipelineEngine.apply_baoyu_structure(
        theme="愤怒决策测试",
        pain_points=["刚冲动发完一段质问就后悔"],
        core_mechanism="杏仁核劫持理智脑",
        solution="做三次深呼吸"
    )
    assert "act_1" in res
    assert "act_2" in res
    assert "act_3" in res
    assert "0-15s" in res["act_1"]["phase"]
    assert "15-40s" in res["act_2"]["phase"]
    assert "40-60s" in res["act_3"]["phase"]
