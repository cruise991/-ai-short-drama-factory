import os
import sys
import json
import time
import shutil
import tempfile
import subprocess
import wave
import numpy as np
from pathlib import Path
from PIL import Image, ImageDraw

from .base_renderer import BaseRenderer

HANDDRAW_SCRIPTS_DIR = Path(__file__).resolve().parent / "handdraw"
if str(HANDDRAW_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(HANDDRAW_SCRIPTS_DIR))


class HanddrawRenderer(BaseRenderer):
    """
    Production Renderer for Hand-drawn Story & Whiteboard Deduction Videos.
    Integrates sweety-handdraw-video algorithmic rendering engine.
    """
    def __init__(self):
        self.scripts_dir = HANDDRAW_SCRIPTS_DIR

    def generate_image(self, prompt: str, output_path: str, config: dict, size: str = "1024x768") -> str:
        """
        Generates an illustration image for hand-drawn rendering.
        Delegates to production_agent.generate_image_agnes with handdrawn-oriented style enhancement.
        """
        import importlib
        production_agent = importlib.import_module("departments.03_production.production_agent")
        
        # Inject handdraw style cues if not already specified
        enhanced_prompt = prompt
        if "handdraw" not in prompt.lower() and "illustration" not in prompt.lower():
            enhanced_prompt = f"minimalist line art illustration, clean ink drawing, warm white background: {prompt}"
            
        print(f"  [HanddrawRenderer] Generating illustration for prompt: {enhanced_prompt[:40]}...")
        return production_agent.generate_image_agnes(enhanced_prompt, output_path, config, size=size)

    def generate_image_with_neg(self, prompt: str, output_path: str, config: dict, size: str = "1024x768", negative_prompt: str = None) -> str:
        import importlib
        production_agent = importlib.import_module("departments.03_production.production_agent")
        
        enhanced_prompt = prompt
        if "handdraw" not in prompt.lower() and "illustration" not in prompt.lower():
            enhanced_prompt = f"minimalist line art illustration, clean ink drawing, warm white background: {prompt}"
            
        neg = "photorealistic, 3d render, complex noisy background, dark gradient, blurry"
        if negative_prompt:
            neg = f"{neg}, {negative_prompt}"
            
        print(f"  [HanddrawRenderer] Generating illustration with neg: {enhanced_prompt[:40]}...")
        return production_agent.generate_image_agnes(enhanced_prompt, output_path, config, size=size, negative_prompt=neg)

    def generate_video(self, source_image: str, prompt: str, output_path: str, config: dict) -> bool:
        return self.generate_video_with_frames(source_image, prompt, output_path, config, num_frames=150)

    def generate_video_with_frames(
        self, 
        source_image: str, 
        prompt: str, 
        output_path: str, 
        config: dict, 
        num_frames: int = 150, 
        size: str = "1080x1920", 
        negative_prompt: str = None, 
        **kwargs
    ) -> bool:
        """
        Renders a stroke-by-stroke hand-drawn video from the source illustration and narration.
        """
        print(f"  [HanddrawRenderer] Building handdraw animation for {output_path}...")
        
        # 1. Parse Dimensions
        fps = 30
        duration_sec = max(5.0, num_frames / fps)
        
        width, height = 1080, 1920
        if "x" in size:
            try:
                parts = size.split("x")
                width, height = int(parts[0]), int(parts[1])
            except Exception:
                width, height = 1080, 1920
                
        # 2. Extract narration text
        shot = kwargs.get("shot", {})
        voice_script = shot.get("voice_script") or shot.get("dialogue") or config.get("voice_script") or prompt[:30]
        # Clean voice script to single line
        voice_script = voice_script.replace("\n", " ").strip()
        if not voice_script:
            voice_script = "剧情推演与线索分析"
            
        # 3. Setup temporary job directory
        job_dir = Path(tempfile.mkdtemp(prefix="handdraw_job_"))
        inputs_dir = job_dir / "inputs"
        inputs_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Resolve local source image
            local_img_path = inputs_dir / "figure.png"
            if source_image.startswith("http://") or source_image.startswith("https://"):
                import requests
                resp = requests.get(source_image, timeout=60)
                if resp.status_code == 200:
                    with open(local_img_path, "wb") as f:
                        f.write(resp.content)
                else:
                    raise RuntimeError(f"Failed to fetch image from URL {source_image}")
            else:
                if os.path.exists(source_image):
                    shutil.copy2(source_image, local_img_path)
                else:
                    # Fallback create a placeholder illustration
                    img = Image.new("RGB", (width, height), "#FBF9F1")
                    draw = ImageDraw.Draw(img)
                    draw.rectangle([100, 100, width - 100, height - 100], outline="#2D2926", width=8)
                    img.save(local_img_path)
            
            # Prepare cover image (matching aspect ratio)
            cover_path = inputs_dir / "cover.png"
            with Image.open(local_img_path) as im:
                cover_im = im.convert("RGB")
                cover_resized = cover_im.resize((width, height), Image.Resampling.LANCZOS)
                cover_resized.save(cover_path)
                
            # Prepare audio narration
            audio_path = inputs_dir / "audio.wav"
            rate = 48000
            
            # Check if an audio file was passed in kwargs or config
            existing_audio = shot.get("audio_path") or config.get("audio_path")
            if existing_audio and os.path.exists(existing_audio):
                subprocess.run([
                    "ffmpeg", "-y", "-v", "error", "-i", str(existing_audio),
                    "-ar", str(rate), "-ac", "1", "-c:a", "pcm_s16le", str(audio_path)
                ], check=True)
            else:
                # Generate clean synthetic speech envelope / timing
                times = np.arange(round(duration_sec * rate)) / rate
                envelope = np.minimum(times / 0.1, 1.0) * np.minimum((duration_sec - times) / 0.1, 1.0)
                # Subtle clear speech frequency simulation
                signal = (0.05 * envelope * np.sin(2 * np.pi * 330 * times) * 32767).astype("<i2")
                with wave.open(str(audio_path), "wb") as stream:
                    stream.setparams((1, 2, rate, 0, "NONE", "not compressed"))
                    stream.writeframes(signal.tobytes())
            
            # Calculate illustration sizing and safe-area margins
            target_fig_w = int(width * 0.75)
            target_fig_h = int(height * 0.55)
            fig_x = int((width - target_fig_w) / 2)
            fig_y = int(height * 0.15)
            
            text_x = int(width * 0.12)
            text_y = int(fig_y + target_fig_h + 40)
            
            # Build job.json manifest
            manifest = {
                "version": 1,
                "runtime_fixture": True,  # Enables seamless execution without hardcoded MLX voice
                "title": shot.get("shot_id", "Handdraw_Scene"),
                "canvas": {"width": width, "height": height, "fps": fps},
                "paper": "#FBF9F1",
                "cover": {"source": "inputs/cover.png", "seconds": 1.0},
                "hand": {"scale": 0.35},
                "audio": {"trim_silence": False},
                "captions": {
                    "font_size": 44,
                    "bottom_margin": 140,
                    "stroke_width": 2,
                    "stroke_color": "#000000",
                    "color": "#FFFFFF",
                    "background": {
                        "color": "#1C1F23",
                        "opacity": 0.88
                    }
                },
                "pages": [
                    {
                        "beats": [
                            {
                                "id": "beat_1",
                                "text": voice_script,
                                "audio": "inputs/audio.wav",
                                "actions": [
                                    {
                                        "type": "illustration",
                                        "parts": [{"id": "main_figure", "polygon": [[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0]]}],
                                        "source": "inputs/figure.png",
                                        "x": fig_x,
                                        "y": fig_y,
                                        "width": target_fig_w,
                                        "height": target_fig_h,
                                        "weight": 3.0,
                                        "drawing": {"mode": "draw"}
                                    }
                                ]


                            }
                        ]
                    }
                ]
            }
            
            manifest_file = job_dir / "job.json"
            manifest_file.write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
            
            # Run compilation and rendering through handdraw_video.py
            cmd_base = [sys.executable, "-B", str(self.scripts_dir / "handdraw_video.py")]
            env = {
                **os.environ,
                "PYTHONDONTWRITEBYTECODE": "1",
                "PYTHONPATH": str(self.scripts_dir)
            }
            
            # Stage 1: Build
            build_res = subprocess.run(cmd_base + ["build", str(job_dir)], capture_output=True, text=True, env=env)
            if build_res.returncode != 0:
                print(f"  [HanddrawRenderer] Build error: {build_res.stderr}")
                return False
                
            # Stage 2: Render
            render_res = subprocess.run(cmd_base + ["render", str(job_dir)], capture_output=True, text=True, env=env)
            if render_res.returncode != 0:
                print(f"  [HanddrawRenderer] Render error: {render_res.stderr}")
                return False
                
            film_output = job_dir / "outputs" / "film.mp4"
            if not film_output.exists():
                print(f"  [HanddrawRenderer] Rendered film.mp4 not found in outputs")
                return False
                
            # Move or copy to target destination
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            shutil.copy2(str(film_output), output_path)
            print(f"  [HanddrawRenderer] Successfully rendered hand-drawn video -> {output_path}")
            return True
            
        except Exception as exc:
            print(f"  [HanddrawRenderer] Exception during rendering: {exc}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            # Clean up temporary scratch job directory
            shutil.rmtree(job_dir, ignore_errors=True)
