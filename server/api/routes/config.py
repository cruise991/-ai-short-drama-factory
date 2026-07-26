import os
import yaml
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any

router = APIRouter(prefix="/api/config", tags=["config"])

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ENV_PATH = os.path.join(BASE_DIR, ".env")
YAML_PATH = os.path.join(BASE_DIR, "company_config.yaml")

class ConfigUpdate(BaseModel):
    env_vars: Dict[str, str] = {}
    yaml_vars: Dict[str, Any] = {}

@router.get("/")
def get_config():
    env_data = {}
    if os.path.exists(ENV_PATH):
        with open(ENV_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    k, v = line.split("=", 1)
                    env_data[k.strip()] = v.strip()
                    
    yaml_data = {}
    if os.path.exists(YAML_PATH):
        with open(YAML_PATH, "r", encoding="utf-8") as f:
            yaml_data = yaml.safe_load(f) or {}

    return {
        "env": env_data,
        "yaml": yaml_data
    }

@router.post("/")
def update_config(payload: ConfigUpdate):
    # Update .env
    if payload.env_vars:
        env_lines = []
        if os.path.exists(ENV_PATH):
            with open(ENV_PATH, "r", encoding="utf-8") as f:
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
                
        with open(ENV_PATH, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
            
    # Update company_config.yaml
    if payload.yaml_vars:
        yaml_data = {}
        if os.path.exists(YAML_PATH):
            with open(YAML_PATH, "r", encoding="utf-8") as f:
                yaml_data = yaml.safe_load(f) or {}
                
        # Deep merge payload.yaml_vars into yaml_data
        for k, v in payload.yaml_vars.items():
            yaml_data[k] = v
            
        with open(YAML_PATH, "w", encoding="utf-8") as f:
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
    
    ips = []
    for f in ip_files:
        name = os.path.basename(f).replace(".json", "")
        ips.append(name)
        
    return {"ips": sorted(ips)}
