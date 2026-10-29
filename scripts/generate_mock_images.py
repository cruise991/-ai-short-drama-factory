import os
from PIL import Image, ImageDraw, ImageFont

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
workspace = os.path.join(base_dir, "projects", "paperai-series", "episode-01", "02_raw_assets")
os.makedirs(workspace, exist_ok=True)

# Generate Shot 01
img1 = Image.new('RGB', (1024, 1024), color = (73, 109, 137))
d1 = ImageDraw.Draw(img1)
d1.text((100, 500), "Shot 01: Theft", fill=(255, 255, 0))
img1.save(os.path.join(workspace, "shot_01.png"))
print("Generated shot_01.png")

# Generate Shot 02
img2 = Image.new('RGB', (1024, 1024), color = (137, 73, 109))
d2 = ImageDraw.Draw(img2)
d2.text((100, 500), "Shot 02: Checkmate", fill=(255, 255, 0))
img2.save(os.path.join(workspace, "shot_02.png"))
print("Generated shot_02.png")
