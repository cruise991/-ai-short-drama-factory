#!/usr/bin/env python3
"""Explainer & Review Pipeline Adapter for AI Short Drama Factory.

Bridges Orchestrator with agent-video-pipeline, enforcing:
- Profile Contract compliance (.agent-video/)
- Circuit breaking and retry safeguards
- Input validation gates (Avatar image & voice sample)
- Safe area positioning and 9:16 / 16:9 aspect ratio support
- Automatic output routing to out/<slugified_goal>/
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
SKILL_DIR = WORKSPACE_ROOT / ".agents/skills/agent-video-pipeline"
CONFIG_ROOT = WORKSPACE_ROOT / ".agent-video"


class ExplainerPipelineAdapter:
    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries
        self.failure_count = 0
        self.skill_dir = SKILL_DIR
        self.config_root = CONFIG_ROOT

    def ensure_config_root(self) -> None:
        if not self.config_root.exists():
            init_script = self.skill_dir / "scripts/init_config_root.py"
            if not init_script.exists():
                raise FileNotFoundError(f"Skill init script missing: {init_script}")
            subprocess.run([sys.executable, str(init_script), "--workspace", str(WORKSPACE_ROOT)], check=True)

    def validate_inputs(self, spoken_text: str, avatar_image: Path | None = None) -> None:
        if not spoken_text or not spoken_text.strip():
            raise ValueError("Spoken script text cannot be empty")
        if len(spoken_text.strip()) < 5:
            raise ValueError("Spoken script is too short (< 5 characters)")

        if avatar_image:
            img = Path(avatar_image).resolve()
            if not img.is_file():
                raise FileNotFoundError(f"Avatar image not found: {img}")
            if img.stat().st_size < 1024:
                raise ValueError(f"Avatar image file is corrupted or too small ({img.stat().st_size} bytes)")

    def run_explainer_task(
        self,
        task_id: str,
        script_text: str,
        avatar_image: Path | None = None,
        background_video: Path | None = None,
        voice: str = "zh-CN-XiaoxiaoNeural",
        mode: str = "pip",
        canvas: str = "9:16",
    ) -> dict[str, Any]:
        """Execute end-to-end explainer video generation with circuit breaker."""
        try:
            self.ensure_config_root()
            self.validate_inputs(script_text, avatar_image)

            project_dir = WORKSPACE_ROOT / f"ai-short-drama/projects/explainer_{task_id}"
            project_dir.mkdir(parents=True, exist_ok=True)
            
            # Standardize output to internal out/ for FastAPI StaticFiles (/media/out),
            # while maintaining root out/ compatibility
            out_dir = WORKSPACE_ROOT / f"ai-short-drama/out/explainer_{task_id}"
            out_dir.mkdir(parents=True, exist_ok=True)
            compat_root_out = WORKSPACE_ROOT / f"out/explainer_{task_id}"
            compat_root_out.mkdir(parents=True, exist_ok=True)


            # 1. Write spoken-script.json
            script_data = {
                "title": f"Explainer_{task_id}",
                "text": script_text.strip(),
                "timestamp": time.time(),
            }
            script_file = project_dir / "spoken-script.json"
            with open(script_file, "w", encoding="utf-8") as f:
                json.dump(script_data, f, ensure_ascii=False, indent=2)

            # 2. Resolve Profile Contract
            resolve_script = self.skill_dir / "scripts/resolve_profile.py"
            cmd_resolve = [
                sys.executable, str(resolve_script),
                "--config-root", str(self.config_root),
                "--profile-id", "workspace",
                "--project", str(project_dir)
            ]
            subprocess.run(cmd_resolve, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            # 3. Universal TTS Generation
            tts_script = self.skill_dir / "scripts/generate_tts_universal.py"
            cmd_tts = [
                sys.executable, str(tts_script),
                "--project", str(project_dir),
                "--voice", voice
            ]
            subprocess.run(cmd_tts, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            audio_wav = project_dir / "audio/narration_master.wav"
            subtitles_srt = project_dir / "audio/captions.srt"

            # 4. Video Compositing
            final_video_path = out_dir / f"explainer_{task_id}_master.mp4"
            
            if avatar_image:
                avatar_script = self.skill_dir / "scripts/compose_avatar.py"
                cmd_avatar = [
                    sys.executable, str(avatar_script),
                    "--avatar-image", str(avatar_image),
                    "--audio", str(audio_wav),
                    "--output", str(final_video_path),
                    "--subtitles", str(subtitles_srt),
                    "--mode", mode,
                    "--canvas", canvas,
                ]
                if background_video:
                    cmd_avatar.extend(["--background", str(background_video)])
                subprocess.run(cmd_avatar, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            else:
                cw, ch = (1080, 1920) if canvas == "9:16" else (1920, 1080)
                aspect_val = "9:16" if canvas == "9:16" else "16:9"
                cmd_render = [
                    "ffmpeg", "-y",
                    "-f", "lavfi", "-i", f"color=c=0x111625:s={cw}x{ch}",
                    "-i", str(audio_wav),
                    "-i", str(subtitles_srt),
                    "-map", "0:v", "-map", "1:a", "-map", "2:s",
                    "-aspect", aspect_val,
                    "-c:v", "libx264", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "192k",
                    "-c:s", "mov_text",
                    "-shortest", str(final_video_path)
                ]
                subprocess.run(cmd_render, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            if final_video_path.exists() and compat_root_out != out_dir:
                try:
                    compat_file = compat_root_out / final_video_path.name
                    if not compat_file.exists():
                        shutil.copy2(final_video_path, compat_file)
                except Exception:
                    pass

            # Success, reset failure count
            self.failure_count = 0
            
            return {
                "status": "success",
                "task_id": task_id,
                "output_video": str(final_video_path),
                "audio_wav": str(audio_wav),
                "captions_srt": str(subtitles_srt),
                "canvas": canvas,
                "project_dir": str(project_dir),
                "out_dir": str(out_dir),
            }

        except Exception as err:
            self.failure_count += 1
            if self.failure_count >= self.max_retries:
                raise RuntimeError(f"Circuit Breaker Triggered: Explainer task failed {self.failure_count} consecutive times: {err}") from err
            raise err
