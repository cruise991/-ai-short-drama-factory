import os
import json
from PIL import Image, ImageDraw, ImageFont

def generate_pose_previews():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    gallery_path = os.path.join(base_dir, "server", "data", "pose_gallery.json")
    out_poses_dir = os.path.join(base_dir, "server", "data", "poses")
    os.makedirs(out_poses_dir, exist_ok=True)

    if not os.path.exists(gallery_path):
        print(f"Gallery path not found: {gallery_path}")
        return

    with open(gallery_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    poses = data.get("poses", [])
    print(f"Generating preview cards for {len(poses)} poses...")

    # Color mapping for categories
    cat_colors = {
        "intro": (236, 72, 153),      # Pink
        "rhythm": (168, 85, 247),     # Purple
        "transition": (99, 102, 241), # Indigo
        "ending": (245, 158, 11)      # Amber
    }

    angle_labels = {
        "front": "FRONT 0°",
        "oblique": "OBLIQUE 45°",
        "side": "SIDE 90°",
        "top": "TOP +30°",
        "low": "LOW -30°"
    }

    W, H = 360, 480  # 3:4 aspect ratio standard card

    for p in poses:
        cat = p.get("category", "intro")
        theme_color = cat_colors.get(cat, (236, 72, 153))
        p_name = p.get("name", "Pose")
        code = p.get("code", "P000")
        previews = p.get("preview_urls", {})

        for angle, rel_url in previews.items():
            fname = os.path.basename(rel_url)
            save_path = os.path.join(out_poses_dir, fname)

            # Create stylish dark mode image
            img = Image.new("RGB", (W, H), (15, 17, 26))
            draw = ImageDraw.Draw(img)

            # Gradient background effect
            for y in range(H):
                factor = y / H
                r = int(15 + (theme_color[0] * 0.12) * factor)
                g = int(17 + (theme_color[1] * 0.12) * factor)
                b = int(26 + (theme_color[2] * 0.12) * factor)
                draw.line([(0, y), (W, y)], fill=(r, g, b))

            # Outer border
            draw.rounded_rectangle([8, 8, W - 8, H - 8], radius=16, outline=(40, 45, 60), width=2)
            draw.rounded_rectangle([12, 12, W - 12, H - 12], radius=12, outline=(theme_color[0]//3, theme_color[1]//3, theme_color[2]//3), width=1)

            # Header Badge
            draw.rounded_rectangle([24, 24, 90, 50], radius=8, fill=(theme_color[0]//4, theme_color[1]//4, theme_color[2]//4))
            draw.text((34, 30), code, fill=theme_color)

            # Angle Badge
            angle_str = angle_labels.get(angle, angle.upper())
            draw.rounded_rectangle([W - 130, 24, W - 24, 50], radius=8, fill=(30, 35, 50))
            draw.text((W - 120, 30), angle_str, fill=(200, 210, 230))

            # Center wireframe figure (artistic stick/pose simulation)
            cx, cy = W // 2, H // 2 - 20
            # Head
            draw.ellipse([cx - 22, cy - 80, cx + 22, cy - 36], outline=theme_color, width=3)
            # Torso
            draw.line([(cx, cy - 36), (cx, cy + 45)], fill=(220, 220, 230), width=4)
            # Shoulder & Arms (adjusted by angle)
            if angle == "side":
                draw.line([(cx - 8, cy - 18), (cx + 30, cy + 15)], fill=theme_color, width=3)
                draw.line([(cx + 30, cy + 15), (cx + 45, cy - 5)], fill=theme_color, width=3)
                # Legs
                draw.line([(cx, cy + 45), (cx - 15, cy + 110)], fill=(180, 190, 210), width=3)
                draw.line([(cx, cy + 45), (cx + 25, cy + 110)], fill=(180, 190, 210), width=3)
            elif angle in ["oblique", "low"]:
                draw.line([(cx - 35, cy - 20), (cx + 35, cy - 10)], fill=(200, 200, 220), width=3)
                draw.line([(cx - 35, cy - 20), (cx - 50, cy + 25)], fill=theme_color, width=3)
                draw.line([(cx + 35, cy - 10), (cx + 55, cy - 30)], fill=theme_color, width=3)
                # Legs
                draw.line([(cx, cy + 45), (cx - 30, cy + 120)], fill=(180, 190, 210), width=3)
                draw.line([(cx, cy + 45), (cx + 35, cy + 115)], fill=(180, 190, 210), width=3)
            else: # front or top
                draw.line([(cx - 40, cy - 15), (cx + 40, cy - 15)], fill=(200, 200, 220), width=3)
                draw.line([(cx - 40, cy - 15), (cx - 55, cy + 20)], fill=theme_color, width=3)
                draw.line([(cx + 40, cy - 15), (cx + 55, cy + 20)], fill=theme_color, width=3)
                # Legs
                draw.line([(cx, cy + 45), (cx - 25, cy + 120)], fill=(180, 190, 210), width=3)
                draw.line([(cx, cy + 45), (cx + 25, cy + 120)], fill=(180, 190, 210), width=3)

            # Footer Name & Category Info
            draw.text((24, H - 75), p_name[:16], fill=(245, 245, 250))
            draw.text((24, H - 48), f"Category: {cat.upper()}  ·  Beats: {p.get('recommended_beats', 4)}", fill=(140, 150, 170))

            img.save(save_path, "PNG", quality=90)

    print(f"Successfully generated all pose preview cards in: {out_poses_dir}")

if __name__ == "__main__":
    generate_pose_previews()
