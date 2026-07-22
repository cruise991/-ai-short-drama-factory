import os
import time
import random
import subprocess
from .base_renderer import BaseRenderer
import importlib
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
production_agent = importlib.import_module("departments.03_production.production_agent")

class AgnesRenderer(BaseRenderer):
    def generate_image(self, prompt: str, output_path: str, config: dict, size: str = "1024x768") -> str:
        print(f"  [AgnesRenderer] Calling REAL Image API for prompt: {prompt[:20]}...")
        return production_agent.generate_image_agnes(prompt, output_path, config, size)

    def generate_image_with_neg(self, prompt: str, output_path: str, config: dict, size: str = "1024x768", negative_prompt: str = None) -> str:
        print(f"  [AgnesRenderer] Calling REAL Image API for prompt: {prompt[:20]}...")
        return production_agent.generate_image_agnes(prompt, output_path, config, size, negative_prompt=negative_prompt)

    def generate_video(self, img_url: str, prompt: str, output_path: str, config: dict) -> str:
        return self.generate_video_with_frames(img_url, prompt, output_path, config, num_frames=121)

    def generate_video_with_frames(self, img_url: str, prompt: str, output_path: str, config: dict, num_frames: int, size: str = "1152x768", negative_prompt: str = None, **kwargs) -> str:
        print(f"  [AgnesRenderer] Calling REAL Video API for {output_path}...")
        
        success = production_agent.generate_video_agnes(img_url, prompt, output_path, config, size=size, num_frames=num_frames, negative_prompt=negative_prompt, **kwargs)
        return "real_video_url" if success else ""
