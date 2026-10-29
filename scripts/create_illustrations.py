import os
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

PROJECT_DIR = Path("/Users/workspace/ai_short_company/ai-short-drama/projects/handdraw_anger_decision")
INPUTS_DIR = PROJECT_DIR / "inputs"
INPUTS_DIR.mkdir(parents=True, exist_ok=True)

PAPER_COLOR = (251, 249, 241, 255) # #FBF9F1
INK_COLOR = (45, 41, 38, 255)      # #2D2926
RED_ACCENT = (226, 85, 75, 255)    # #E2554B
BLUE_ACCENT = (70, 130, 180, 255)  # #4682B4
AMBER_ACCENT = (235, 160, 60, 255) # #EBA03C
GREEN_ACCENT = (80, 160, 110, 255) # #50A06E


def create_cover():
    """1080x1920 Cover Image."""
    im = Image.new("RGBA", (1080, 1920), PAPER_COLOR)
    draw = ImageDraw.Draw(im)
    
    # Outer elegant sketch border
    draw.rounded_rectangle([60, 80, 1020, 1840], radius=32, outline=INK_COLOR, width=6)
    draw.rounded_rectangle([80, 100, 1000, 1820], radius=24, outline=(180, 175, 165, 255), width=2)
    
    # Head silhouette & brain outline
    center_x, center_y = 540, 850
    # Head contour
    draw.ellipse([center_x - 220, center_y - 280, center_x + 220, center_y + 200], outline=INK_COLOR, width=8)
    draw.polygon([
        (center_x + 180, center_y),
        (center_x + 280, center_y + 40),
        (center_x + 240, center_y + 160),
        (center_x + 160, center_y + 180)
    ], fill=None, outline=INK_COLOR, width=6)
    
    # Prefrontal Cortex (Blue zone)
    draw.chord([center_x + 10, center_y - 240, center_x + 190, center_y - 80], start=220, end=40, fill=BLUE_ACCENT, outline=INK_COLOR, width=5)
    # Amygdala (Red flashing center)
    draw.ellipse([center_x - 30, center_y - 40, center_x + 50, center_y + 40], fill=RED_ACCENT, outline=INK_COLOR, width=6)
    
    # Connecting lightning / nerve pulse
    draw.line([(center_x + 10, center_y - 80), (center_x + 10, center_y - 40)], fill=RED_ACCENT, width=6)
    
    # Text headers
    try:
        font_large = ImageFont.truetype("/System/Library/Fonts/STHeiti Medium.ttc", 72)
        font_sub = ImageFont.truetype("/System/Library/Fonts/STHeiti Medium.ttc", 44)
    except:
        font_large = ImageFont.load_default()
        font_sub = ImageFont.load_default()
        
    title_line1 = "为什么越生气"
    title_line2 = "越容易做错决定？"
    sub_title = "脑科学深度拆解 · 杏仁核劫持"
    
    draw.text((center_x, 320), title_line1, fill=INK_COLOR, font=font_large, anchor="mm")
    draw.text((center_x, 420), title_line2, fill=RED_ACCENT, font=font_large, anchor="mm")
    draw.text((center_x, 520), sub_title, fill=(120, 110, 100, 255), font=font_sub, anchor="mm")
    
    cover_path = INPUTS_DIR / "cover.png"
    im.save(cover_path)
    print("Saved cover.png")


def create_scene1_anger():
    """Scene 1: Person bursting with anger (Figure)."""
    w, h = 800, 700
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(im)
    
    cx, cy = 400, 360
    # Head & bust silhouette
    draw.ellipse([cx - 180, cy - 220, cx + 180, cy + 180], fill=None, outline=INK_COLOR, width=8)
    draw.line([(cx - 160, cy + 160), (cx - 240, cy + 300)], fill=INK_COLOR, width=8)
    draw.line([(cx + 160, cy + 160), (cx + 240, cy + 300)], fill=INK_COLOR, width=8)
    
    # Anger flame bursts around head
    flames = [
        [(cx - 140, cy - 200), (cx - 210, cy - 300), (cx - 110, cy - 240)],
        [(cx - 50, cy - 220), (cx, cy - 340), (cx + 50, cy - 220)],
        [(cx + 110, cy - 240), (cx + 210, cy - 300), (cx + 140, cy - 200)],
        [(cx - 200, cy - 60), (cx - 310, cy - 80), (cx - 190, cy + 20)],
        [(cx + 190, cy + 20), (cx + 310, cy - 80), (cx + 200, cy - 60)]
    ]
    for pts in flames:
        draw.polygon(pts, fill=RED_ACCENT, outline=INK_COLOR, width=5)
        
    # Shock wave lightning marks
    draw.line([(cx - 240, cy - 140), (cx - 200, cy - 120), (cx - 230, cy - 90)], fill=AMBER_ACCENT, width=6)
    draw.line([(cx + 240, cy - 140), (cx + 200, cy - 120), (cx + 230, cy - 90)], fill=AMBER_ACCENT, width=6)
    
    im.save(INPUTS_DIR / "scene1_anger.png")
    print("Saved scene1_anger.png")


def create_scene2_brain():
    """Scene 2: Prefrontal Cortex vs Amygdala Dual Brain Architecture."""
    w, h = 800, 700
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(im)
    
    cx, cy = 400, 340
    # Brain outer cortex contour
    brain_points = [
        (cx - 280, cy - 40), (cx - 250, cy - 180), (cx - 120, cy - 260),
        (cx + 80, cy - 260), (cx + 260, cy - 160), (cx + 280, cy + 30),
        (cx + 220, cy + 180), (cx + 90, cy + 210), (cx - 40, cy + 160),
        (cx - 150, cy + 190), (cx - 260, cy + 90), (cx - 280, cy - 40)
    ]
    draw.polygon(brain_points, fill=None, outline=INK_COLOR, width=8)
    
    # Prefrontal Cortex (Frontal lobe: blue logical executive)
    draw.chord([cx + 40, cy - 220, cx + 250, cy + 40], start=250, end=90, fill=BLUE_ACCENT, outline=INK_COLOR, width=6)
    
    # Amygdala (Deep emotional almond nucleus: red alert)
    draw.ellipse([cx - 40, cy - 10, cx + 60, cy + 90], fill=RED_ACCENT, outline=INK_COLOR, width=6)
    
    # Balance beam / scales line showing rivalry
    draw.line([(cx - 200, cy + 230), (cx + 200, cy + 230)], fill=INK_COLOR, width=6)
    draw.polygon([(cx, cy + 230), (cx - 30, cy + 280), (cx + 30, cy + 280)], fill=(150, 140, 130, 255), outline=INK_COLOR, width=4)
    
    im.save(INPUTS_DIR / "scene2_brain.png")
    print("Saved scene2_brain.png")


def create_scene3_hijack():
    """Scene 3: Amygdala Hijack (Circuit Break)."""
    w, h = 800, 700
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(im)
    
    cx, cy = 400, 340
    # Surging Amygdala center
    draw.ellipse([cx - 120, cy - 120, cx + 120, cy + 120], fill=RED_ACCENT, outline=INK_COLOR, width=8)
    
    # Pulse rings expanding
    draw.arc([cx - 180, cy - 180, cx + 180, cy + 180], start=0, end=360, fill=AMBER_ACCENT, width=6)
    draw.arc([cx - 240, cy - 240, cx + 240, cy + 240], start=0, end=360, fill=RED_ACCENT, width=4)
    
    # Disconnect switch: circuit breaking
    draw.line([(cx - 260, cy - 190), (cx - 120, cy - 190)], fill=INK_COLOR, width=8)
    # Open / broken switch
    draw.line([(cx - 120, cy - 190), (cx - 40, cy - 260)], fill=RED_ACCENT, width=8)
    draw.line([(cx + 40, cy - 190), (cx + 260, cy - 190)], fill=(180, 180, 180, 255), width=8)
    
    # Red cross on logic connection
    draw.line([(cx + 100, cy - 240), (cx + 160, cy - 140)], fill=RED_ACCENT, width=8)
    draw.line([(cx + 160, cy - 240), (cx + 100, cy - 140)], fill=RED_ACCENT, width=8)
    
    im.save(INPUTS_DIR / "scene3_hijack.png")
    print("Saved scene3_hijack.png")


def create_scene4_timer():
    """Scene 4: Six Seconds Timer & Deep Breath Reset."""
    w, h = 800, 700
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(im)
    
    cx, cy = 400, 340
    # Stylized Clock / Countdown Circle
    draw.ellipse([cx - 200, cy - 200, cx + 200, cy + 200], fill=None, outline=INK_COLOR, width=8)
    draw.arc([cx - 170, cy - 170, cx + 170, cy + 170], start=-90, end=90, fill=GREEN_ACCENT, width=14)
    
    # Clock ticks
    for angle in [0, 60, 120, 180, 240, 300]:
        rad = np.radians(angle)
        x1 = cx + 180 * np.cos(rad)
        y1 = cy + 180 * np.sin(rad)
        x2 = cx + 155 * np.cos(rad)
        y2 = cy + 155 * np.sin(rad)
        draw.line([(x1, y1), (x2, y2)], fill=INK_COLOR, width=5)
        
    # Large 6s symbol inside clock
    draw.ellipse([cx - 60, cy - 20, cx + 60, cy + 100], fill=GREEN_ACCENT, outline=INK_COLOR, width=6)
    draw.arc([cx - 50, cy - 120, cx + 50, cy], start=120, end=340, fill=INK_COLOR, width=8)
    
    # Calming breath waves below
    xs = np.linspace(cx - 280, cx + 280, 150)
    ys = cy + 260 + 20 * np.sin(xs / 50.0)
    points = list(zip(xs, ys))
    for p1, p2 in zip(points[:-1], points[1:]):
        draw.line([p1, p2], fill=BLUE_ACCENT, width=6)
        
    im.save(INPUTS_DIR / "scene4_timer.png")
    print("Saved scene4_timer.png")


if __name__ == "__main__":
    create_cover()
    create_scene1_anger()
    create_scene2_brain()
    create_scene3_hijack()
    create_scene4_timer()
