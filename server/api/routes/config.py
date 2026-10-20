import os
import yaml
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any

router = APIRouter(prefix="/config", tags=["config"])

if os.path.exists("/workspace"):
    BASE_DIR = "/workspace"
else:
    candidate = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if not os.path.exists(os.path.join(candidate, "assets")) and os.path.exists(os.path.join(os.path.dirname(candidate), "assets")):
        BASE_DIR = os.path.dirname(candidate)
    else:
        BASE_DIR = candidate

def get_env_path():
    for p in ["/app/.env", os.path.join(BASE_DIR, ".env")]:
        if os.path.exists(p) and not os.path.isdir(p):
            return p
    return os.path.join(BASE_DIR, ".env")

def get_yaml_path():
    for p in ["/app/company_config.yaml", os.path.join(BASE_DIR, "config", "company_config.yaml"), os.path.join(BASE_DIR, "company_config.yaml")]:
        if os.path.exists(p) and not os.path.isdir(p):
            return p
    return os.path.join(BASE_DIR, "config", "company_config.yaml")

class ConfigUpdate(BaseModel):
    env_vars: Dict[str, str] = {}
    yaml_vars: Dict[str, Any] = {}

@router.get("/")
def get_config():
    env_data = {}
    env_path = get_env_path()
    if os.path.exists(env_path) and not os.path.isdir(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    k, v = line.split("=", 1)
                    env_data[k.strip()] = v.strip()
                    
    yaml_data = {}
    yaml_path = get_yaml_path()
    if os.path.exists(yaml_path) and not os.path.isdir(yaml_path):
        with open(yaml_path, "r", encoding="utf-8") as f:
            yaml_data = yaml.safe_load(f) or {}

    return {
        "env": env_data,
        "yaml": yaml_data
    }

@router.post("/")
def update_config(payload: ConfigUpdate):
    env_path = get_env_path()
    # Update .env
    if payload.env_vars:
        env_lines = []
        if os.path.exists(env_path) and not os.path.isdir(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                env_lines = f.readlines()
        
        updated_keys = set()
        new_lines = []
        for line in env_lines:
            stripped = line.strip()
            if stripped and not stripped.startswith("#") and "=" in stripped:
                k = stripped.split("=", 1)[0].strip()
                if k in payload.env_vars:
                    new_lines.append(f"{k}={payload.env_vars[k]}\n")
                    updated_keys.add(k)
                    continue
            new_lines.append(line)
            
        for k, v in payload.env_vars.items():
            if k not in updated_keys:
                # Add newline if previous line didn't have one
                if new_lines and not new_lines[-1].endswith("\n"):
                    new_lines.append("\n")
                new_lines.append(f"{k}={v}\n")
                
        with open(env_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
            
    # Update company_config.yaml
    if payload.yaml_vars:
        yaml_path = get_yaml_path()
        yaml_data = {}
        if os.path.exists(yaml_path) and not os.path.isdir(yaml_path):
            with open(yaml_path, "r", encoding="utf-8") as f:
                yaml_data = yaml.safe_load(f) or {}
                
        # Deep merge payload.yaml_vars into yaml_data
        for k, v in payload.yaml_vars.items():
            yaml_data[k] = v
            
        with open(yaml_path, "w", encoding="utf-8") as f:
            yaml.dump(yaml_data, f, allow_unicode=True, default_flow_style=False)
            
    return {"status": "success", "message": "Configuration updated successfully"}

import glob

@router.get("/ips")
def get_ips():
    ips_dir = os.path.join(BASE_DIR, "assets", "dance", "01_characters", "ips")
    if not os.path.exists(ips_dir):
        return {"ips": []}
        
    ip_files = glob.glob(os.path.join(ips_dir, "*.json"))
    ip_files = [f for f in ip_files if "expressions" not in f and "hairstyles" not in f and "makeup" not in f]
    ips = [os.path.basename(f).replace('.json', '') for f in ip_files]
    
    return {"ips": sorted(ips)}

import json

@router.get("/branch_presets")
def get_branch_presets():
    """
    Returns unified metadata assets for all 4+1 branches:
    - costumes, scenes, motions (Transformation branch)
    - hand presets, papers, caption presets (Handdraw branch)
    - character IPs (Dance & Drama branches)
    """
    assets_dir = os.path.join(BASE_DIR, "assets")
    
    # Costumes, Scenes, Motions for Transformation branch
    def load_asset_json(filename):
        p = os.path.join(assets_dir, filename)
        if os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    costumes = load_asset_json("costumes.json")
    scenes = load_asset_json("scenes.json")
    motions = load_asset_json("motions.json")

    # Handdraw presets
    hands = [
        {"id": "teacher-pen", "name": "白衬衫讲师中性笔 (推荐)", "desc": "知性专业，适合认知科学、心理学与严肃推理", "icon": "pen"},
        {"id": "cardigan-fountain", "name": "针织袖经典钢笔", "desc": "典雅深邃，适合文学历史与哲理探讨", "icon": "feather"},
        {"id": "waner-brush", "name": "上官婉儿灵感毛笔", "desc": "东方意蕴，适合国学文史与传统美学", "icon": "brush"},
        {"id": "navy", "name": "深蓝袖马克笔", "desc": "活泼有力，适合商业逻辑与思维导图", "icon": "pen-tool"},
        {"id": "pen-only", "name": "极简纯笔尖 · 无手臂", "desc": "极客清爽，无手臂遮挡，适合复杂算法推导", "icon": "mouse-pointer"}
    ]

    papers = [
        {"id": "ivory_white", "name": "象牙米白护眼纸", "color": "#FBF9F1", "text_color": "#2D2926", "recommended_caption": "pill_dark"},
        {"id": "vintage_kraft", "name": "复古暖色牛皮纸", "color": "#F5EFEB", "text_color": "#332B25", "recommended_caption": "pill_dark"},
        {"id": "slate_blackboard", "name": "沉浸深灰黑板", "color": "#20252B", "text_color": "#E6ECF2", "recommended_caption": "pill_light"}
    ]

    caption_styles = [
        {"id": "pill_dark", "name": "曜石黑胶囊底衬 (推荐)", "desc": "85% 半透明深黑底衬 + 纯白粗体，对比度 18:1 极清抗干扰", "bg_color": "#1C1F23", "bg_opacity": 0.85, "text_color": "#FFFFFF", "size": 48},
        {"id": "clean_ink", "name": "极简深墨黑字", "desc": "无底衬纯字，适合深色黑板或高对比度插画", "bg_color": "transparent", "bg_opacity": 0.0, "text_color": "#1E1E1E", "size": 50}
    ]

    # Character IPs for Dance & Drama
    ips_res = get_ips()

    return {
        "costumes": costumes,
        "scenes": scenes,
        "motions": motions,
        "hands": hands,
        "papers": papers,
        "caption_styles": caption_styles,
        "ips": ips_res.get("ips", [])
    }

