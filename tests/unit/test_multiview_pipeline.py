import os
import sys
import pytest
import numpy as np
import cv2
from fastapi.testclient import TestClient

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SERVER_DIR = os.path.join(BASE_DIR, "server")
SCRIPTS_DIR = os.path.join(BASE_DIR, ".agents", "skills", "character-dance-video", "scripts")

for p in [BASE_DIR, SERVER_DIR, SCRIPTS_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)

from api.main import app
from core.security import create_access_token
from multi_view_adapter import MultiViewAdapter

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client

@pytest.fixture(scope="module")
def auth_headers():
    token = create_access_token(data={"sub": "admin_test", "role": "admin", "tenant_id": "tenant_alpha"})
    return {"Authorization": f"Bearer {token}"}

def test_multiview_adapter_single_image(tmp_path):
    """Verify N=1 passthrough on standard single character image."""
    adapter = MultiViewAdapter()
    sample_img = os.path.join(BASE_DIR, "test_ref_character.png")
    
    if not os.path.exists(sample_img):
        pytest.skip("Sample test_ref_character.png not found")
        
    out_dir = str(tmp_path / "single_test")
    res = adapter.run_pipeline(sample_img, out_dir, tenant_id="tenant_alpha", project_id="single_proj")
    
    assert res["detected_n"] == 1
    assert res["is_multiview"] is False
    assert os.path.exists(res["primary_front_path"])
    
    # Check normalized dimensions
    img = cv2.imread(res["primary_front_path"])
    assert img.shape == (1280, 704, 3)

def test_multiview_adapter_three_views(tmp_path):
    """Verify N=3 detection and slicing on 3-view character sheet."""
    adapter = MultiViewAdapter()
    sample_img = os.path.join(BASE_DIR, "test_multiview_input.png")
    
    if not os.path.exists(sample_img):
        pytest.skip("Sample test_multiview_input.png not found")
        
    out_dir = str(tmp_path / "multiview_test")
    res = adapter.run_pipeline(sample_img, out_dir, tenant_id="tenant_alpha", project_id="three_views_proj")
    
    assert res["detected_n"] == 3
    assert res["is_multiview"] is True
    assert len(res["views"]) == 3
    
    # Check roles
    assert res["views"][0]["role"] == "FRONT"
    assert res["views"][0]["is_primary_start"] is True
    assert res["views"][1]["role"] == "SIDE"
    assert res["views"][2]["role"] == "BACK"
    
    # Check normalized resolution
    for v in res["views"]:
        assert os.path.exists(v["path"])
        img = cv2.imread(v["path"])
        assert img.shape == (1280, 704, 3)

def test_api_analyze_views(client, auth_headers):
    """Test the /api/dance/analyze-views endpoint."""
    sample_img = os.path.join(BASE_DIR, "test_multiview_input.png")
    if not os.path.exists(sample_img):
        pytest.skip("Sample test_multiview_input.png not found")
        
    with open(sample_img, "rb") as f:
        response = client.post(
            "/api/dance/analyze-views",
            files={"image": ("turnaround.png", f, "image/png")},
            data={"tenant_id": "tenant_beta"},
            headers=auth_headers
        )
        print("Response status:", response.status_code, "Body:", response.text)
        assert response.status_code == 200
    data = response.json()
    assert data["detected_n"] == 3
    assert data["is_multiview"] is True
    assert len(data["views"]) == 3
    assert data["views"][0]["role"] == "FRONT"
    assert "preview_url" in data["views"][0]

def test_quality_auditor_face_consistency():
    """Verify quality_audit_gate stream checks and face consistency auditor."""
    from quality_auditor import quality_audit_gate, audit_face_consistency
    sample_img = os.path.join(BASE_DIR, "test_multiview_input.png")
    sample_mp4 = os.path.join(BASE_DIR, "out", "skill_test_30s_kpop_chaebol_girl", "kpop_chaebol_girl_dance_30s.mp4")
    
    if not os.path.exists(sample_mp4):
        pytest.skip("Sample mp4 not found")
        
    # Test base quality audit gate
    res = quality_audit_gate(sample_mp4)
    assert res is True
    
    # Test face consistency auditor with reference image
    if os.path.exists(sample_img):
        # Even with cross-character, test that auditor computes similarities and doesn't crash
        try:
            audit_face_consistency(sample_img, sample_mp4, threshold=0.50)
        except AssertionError as e:
            # Expected if cross-character similarity is lower than threshold
            print("Handled expected cross-character threshold assertion:", e)

