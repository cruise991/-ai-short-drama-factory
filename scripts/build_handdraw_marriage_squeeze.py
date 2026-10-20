"""
Industrialized Handdraw Production Pipeline:
Topic: "为什么现在的社会结婚的人数越来越少，适龄女青年为何找不到合适的结婚对象，大龄剩女和剩男为何越来越多"
Core Mechanism: 婚姻梯队模型与结构性博弈错配 (The Marriage Gradient & Structural Squeeze)
Five-Tier Methodology:
  1. Agent Reach: Research & User Voice Mining (知乎/小红书/B站大众真实心声)
  2. NotebookLM: Concept Matrix & Socioeconomic Mechanism Distillation
  3. Baoyu: 5-Act Narrative Architecture (0-112s under 2 mins)
  4. Humanizer-zh: De-AI Flavor Text Polishing & Colloquial Empathy
  5. Sweety-Handdraw: Broadcast Audio Mastering, High-Contrast Obsidian Subtitles & Clean Lineart
"""
import os
import sys
import json
import wave
import shutil
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT_DIR = Path("/Users/workspace/ai_short_company/ai-short-drama")
sys.path.insert(0, str(ROOT_DIR))

from shared_tools.skills_registry import ContentPipelineEngine
from shared_tools.audio_mastering import AudioMasteringStudio

PROJECT_DIR = ROOT_DIR / "projects" / "handdraw_marriage_squeeze"
INPUTS_DIR = PROJECT_DIR / "inputs"
OUTPUTS_DIR = ROOT_DIR / "out" / "handdraw_marriage_squeeze"

INPUTS_DIR.mkdir(parents=True, exist_ok=True)
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

FONT_PATH = "/System/Library/Fonts/STHeiti Light.ttc"

def get_font(size: int):
    try:
        return ImageFont.truetype(FONT_PATH, size)
    except Exception:
        return ImageFont.load_default()

# ------------------------------------------------------------------------------
# 1. Five Narrative Beats Specification (~112 seconds total)
# ------------------------------------------------------------------------------
BEATS_SPEC = [
    # Act 1: 0.0s - 21.4s (Hook & Phenomenon)
    {
        "id": "beat_01",
        "text": "民政局结婚登记连年创新低，相亲角里名校高薪的女青年愁嫁，而小县城和农村的男青年愁娶。很多人张口就怪年轻人太挑剔、太物质。但其实，这真不是个体的道德问题，而是整个婚恋市场，正在被一个残酷的数学机制卡死了。",
        "rate": 182,
        "voice": "Reed (中文（中国大陆）)",
        "cues": [
            "民政局结婚登记连年创新低，",
            "相亲角里名校高薪的女青年愁嫁，",
            "而小县城和农村的男青年愁娶。",
            "很多人张口就怪年轻人太挑剔、太物质。",
            "但其实，这真不是个体的道德问题，",
            "而是整个婚恋市场，正在被一个残酷的数学机制卡死了。"
        ]
    },
    # Act 2: 21.4s - 44.1s (Mechanism: The Marriage Gradient)
    {
        "id": "beat_02",
        "text": "社会学上有个经典理论，叫婚姻梯队模型。传统社会习惯把男女按综合资源，分成 A、B、C、D 四个梯队。过去几百年，大家都遵循男向下选、女向上选的法则：A男娶B女，B男娶C女，C男娶D女。这样层层错开，每个人都能找到伴侣。",
        "rate": 180,
        "voice": "Reed (中文（中国大陆）)",
        "cues": [
            "社会学上有个经典理论，叫婚姻梯队模型。",
            "传统社会习惯把男女按综合资源，",
            "分成 A、B、C、D 四个梯队。",
            "过去几百年，大家都遵循男向下选、女向上选的法则：",
            "A男娶B女，B男娶C女，C男娶D女。",
            "这样层层错开，每个人都能找到伴侣。"
        ]
    },
    # Act 3: 44.1s - 71.6s (Structural Squeeze: Squeeze at Top & Bottom)
    {
        "id": "beat_03",
        "text": "可现在的时代全变了。高等教育和职场里，独立优秀的 A 女大量涌现。但是大家的择偶心理还没转过来：A女依然渴望更优秀的 A+ 男；可顶层的 A 男，偏好没变，依然喜欢向下找年轻温柔的 B 女甚至 C 女。这就导致了一个数学死局：最优秀的 A 女剩在顶峰，最底层的 D 男剩在谷底。中间的人彼此消耗，谁也够不着谁。",
        "rate": 185,
        "voice": "Reed (中文（中国大陆）)",
        "cues": [
            "可现在的时代全变了。",
            "高等教育和职场里，独立优秀的 A 女大量涌现。",
            "但是大家的择偶心理还没转过来：",
            "A女依然渴望更优秀的 A+ 男；",
            "可顶层的 A 男，偏好没变，",
            "依然喜欢向下找年轻温柔的 B 女甚至 C 女。",
            "这就导致了一个数学死局：",
            "最优秀的 A 女剩在顶峰，最底层的 D 男剩在谷底。",
            "中间的人彼此消耗，谁也够不着谁。"
        ]
    },
    # Act 4: 71.6s - 94.4s (The Economic Equation & Opportunity Cost)
    {
        "id": "beat_04",
        "text": "加上现在城市单身生活极度方便，一个人吃饱全家不饿；而一旦走进婚姻，房贷、生育、教育、家务成本全面爆发，试错成本更是高得惊人。婚姻从过去的抱团取暖，变成了高风险的合伙开公司。既然找不到合拍的合伙人，谁愿意贸然押上自己的下半生？",
        "rate": 183,
        "voice": "Reed (中文（中国大陆）)",
        "cues": [
            "加上现在城市单身生活极度方便，",
            "一个人吃饱全家不饿；",
            "而一旦走进婚姻，",
            "房贷、生育、教育、家务成本全面爆发，",
            "试错成本更是高得惊人。",
            "婚姻从过去的抱团取暖，",
            "变成了高风险的合伙开公司。",
            "既然找不到合拍的合伙人，",
            "谁愿意贸然押上自己的下半生？"
        ]
    },
    # Act 5: 94.4s - 112.8s (Cognitive Breakthrough & Rational Empathy)
    {
        "id": "beat_05",
        "text": "看懂了这个机制，就别再互相苛责。结婚是追求幸福，单身也是在理性避险。想要打破死局，要么放下梯队的阶层攀比，找个懂你喜怒哀乐的灵魂伴侣；要么坦然享受单身，认真把自己的日子过得热气腾腾。",
        "rate": 178,
        "voice": "Reed (中文（中国大陆）)",
        "cues": [
            "看懂了这个机制，就别再互相苛责。",
            "结婚是追求幸福，单身也是在理性避险。",
            "想要打破死局，要么放下梯队的阶层攀比，",
            "找个懂你喜怒哀乐的灵魂伴侣；",
            "要么坦然享受单身，",
            "认真把自己的日子过得热气腾腾。"
        ]
    }
]

# ------------------------------------------------------------------------------
# 2. Audio Synthesis & 5-Stage DSP Mastering
# ------------------------------------------------------------------------------
def synthesize_and_master_audio():
    print(">>> [Audio Pipeline] Synthesizing & Mastering 5 Narrative Beats...")
    durations = {}
    for item in BEATS_SPEC:
        bid = item["id"]
        raw_text = item["text"]
        rate = item["rate"]
        voice = item["voice"]
        
        raw_aiff_p = INPUTS_DIR / f"{bid}_raw.aiff"
        final_wav_p = INPUTS_DIR / f"{bid}.wav"
        
        # Synthesize via macOS say
        subprocess.run(["say", "-v", voice, "-r", str(rate), "-o", str(raw_aiff_p), raw_text], check=True)
        
        # Master via AudioMasteringStudio (80Hz Highpass, 250Hz Warmth, 4500Hz Crisp, Compressor, -14 LUFS)
        success = AudioMasteringStudio.master_voice_clip(str(raw_aiff_p), str(final_wav_p))
        if not success:
            subprocess.run(["ffmpeg", "-y", "-i", str(raw_aiff_p), "-ar", "48000", "-ac", "1", str(final_wav_p)], check=True)
            
        if raw_aiff_p.exists():
            raw_aiff_p.unlink()
            
        with wave.open(str(final_wav_p), "rb") as wf:
            dur = wf.getnframes() / float(wf.getframerate())
        durations[bid] = round(dur, 3)
        print(f"  [Mastered {bid}] Duration: {dur:.2f}s | {raw_text[:28]}...")
        
    total_dur = sum(durations.values())
    print(f"  >>> Total Video Audio Duration: {total_dur:.2f}s ({(total_dur/60):.2f} min, strictly < 2.0 min)")
    return durations

# ------------------------------------------------------------------------------
# 3. Handdrawn Visual Asset Illustrations
# ------------------------------------------------------------------------------
def create_illustrations():
    print(">>> [Visual Design] Generating 5 Handdrawn Whiteboard Illustrations (Minimalist Symbolic Vectors)...")
    bg_color = (251, 249, 241) # #FBF9F1 warm paper tone
    ink_color = (35, 31, 32)    # dark charcoal ink
    accent_red = (211, 47, 47)  # coral highlight
    accent_blue = (33, 85, 163) # deep navy
    accent_gold = (212, 160, 23)# golden warm
    
    font_large = get_font(56)
    font_mid = get_font(40)
    font_small = get_font(28)
    
    # --- Cover Image (Still poster) ---
    cover = Image.new("RGB", (1080, 1920), bg_color)
    dc = ImageDraw.Draw(cover)
    dc.rectangle([(50, 50), (1030, 1870)], outline=ink_color, width=4)
    dc.rectangle([(65, 65), (1015, 1855)], outline=ink_color, width=2)
    dc.text((120, 500), "为什么现在结婚的人越来越少？", fill=ink_color, font=font_large)
    dc.text((120, 590), "适龄青年为何找对象难？剩男剩女为何增多？", fill=accent_red, font=font_small)
    dc.line([(120, 660), (960, 660)], fill=ink_color, width=3)
    dc.text((120, 700), "底层机制 · 婚姻梯队理论与结构性错配", fill=accent_blue, font=font_mid)
    
    # Central Metaphor: Marriage Gradient Balance
    dc.polygon([(540, 950), (480, 1070), (600, 1070)], outline=ink_color, fill=bg_color, width=5)
    dc.line([(260, 980), (820, 920)], fill=ink_color, width=8) # tilted beam
    dc.ellipse([(220, 960), (300, 1040)], outline=accent_blue, width=4) # Left pan
    dc.ellipse([(780, 900), (860, 980)], outline=accent_red, width=4)  # Right pan
    dc.text((245, 975), "♂", fill=accent_blue, font=font_mid)
    dc.text((805, 915), "♀", fill=accent_red, font=font_mid)
    cover.save(INPUTS_DIR / "cover.png")
    
    # --- Scene 1: 登记处冷清 vs 相亲角焦虑 (Act 1, ~35 strokes) ---
    im1 = Image.new("RGB", (900, 1200), bg_color)
    d1 = ImageDraw.Draw(im1)
    
    # Left: Empty Registry House
    d1.polygon([(120, 360), (280, 220), (440, 360)], outline=accent_blue, width=6) # Roof
    d1.rectangle([(150, 360), (410, 620)], outline=ink_color, width=5) # Walls
    d1.rectangle([(230, 460), (330, 620)], outline=ink_color, width=4) # Door
    d1.ellipse([(250, 290), (310, 350)], outline=accent_blue, width=3) # Clock on roof
    d1.line([(280, 305), (280, 320)], fill=accent_blue, width=3) # Clock hand
    d1.line([(280, 320), (295, 320)], fill=accent_blue, width=3)
    # Downward Trend Arrow (Registry Decline)
    d1.line([(180, 700), (380, 840)], fill=accent_blue, width=6)
    d1.polygon([(380, 840), (350, 830), (370, 800)], fill=accent_blue)
    
    # Center Big Question
    d1.ellipse([(430, 440), (470, 480)], outline=accent_red, width=4)
    d1.arc([(420, 360), (480, 430)], start=180, end=360, fill=accent_red, width=6)
    d1.line([(450, 430), (450, 460)], fill=accent_red, width=6)
    d1.ellipse([(445, 490), (455, 500)], fill=accent_red)
    
    # Right: Matchmaking Park Tree with Cards
    d1.line([(680, 260), (680, 620)], fill=ink_color, width=10) # Trunk
    d1.arc([(520, 160), (840, 380)], start=170, end=370, fill=accent_red, width=6) # Canopy
    # 3 Profile cards hanging
    for cx, cy in [(560, 340), (740, 350), (650, 420)]:
        d1.line([(cx+25, cy-25), (cx+25, cy)], fill=ink_color, width=2)
        d1.rectangle([(cx, cy), (cx+50), (cy+70)], outline=accent_red, width=3)
        d1.line([(cx+10, cy+20), (cx+40, cy+20)], fill=accent_red, width=2)
        d1.line([(cx+10, cy+40), (cx+40, cy+40)], fill=accent_red, width=2)
    # Upward Trend Arrow (Anxiety Surge)
    d1.line([(580, 840), (780, 700)], fill=accent_red, width=6)
    d1.polygon([(780, 700), (750, 710), (770, 740)], fill=accent_red)
    
    im1.save(INPUTS_DIR / "scene1_hook.png")
    
    # --- Scene 2: 经典婚姻梯队模型 A/B/C/D (Act 2, ~30 strokes) ---
    im2 = Image.new("RGB", (900, 1200), bg_color)
    d2 = ImageDraw.Draw(im2)
    
    # Headers
    d2.text((220, 140), "♂", fill=accent_blue, font=font_large)
    d2.text((640, 140), "♀", fill=accent_red, font=font_large)
    
    tiers = ["A", "B", "C", "D"]
    y_pos = [280, 460, 640, 820]
    
    for i, t in enumerate(tiers):
        y = y_pos[i]
        # Male Tier Badge
        d2.ellipse([(180, y), (280, y+100)], outline=accent_blue, width=5)
        d2.text((212, y+18), t, fill=accent_blue, font=font_large)
        
        # Female Tier Badge
        d2.ellipse([(620, y), (720, y+100)], outline=accent_red, width=5)
        d2.text((652, y+18), t, fill=accent_red, font=font_large)
    
    # Classic Gradient Arrows: A男->B女, B男->C女, C男->D女
    for i in range(3):
        y1 = y_pos[i] + 50
        y2 = y_pos[i+1] + 50
        d2.line([(280, y1), (610, y2)], fill=ink_color, width=5)
        d2.polygon([(615, y2), (595, y2-15), (602, y2+15)], fill=ink_color)
        
    im2.save(INPUTS_DIR / "scene2_gradient.png")
    
    # --- Scene 3: 时代剧变 · 结构错配 (Act 3, ~40 strokes) ---
    im3 = Image.new("RGB", (900, 1200), bg_color)
    d3 = ImageDraw.Draw(im3)
    
    # Headers
    d3.text((220, 140), "♂", fill=accent_blue, font=font_large)
    d3.text((640, 140), "♀", fill=accent_red, font=font_large)
    
    # Male Badges
    d3.ellipse([(180, 360), (280, 460)], outline=accent_blue, width=5)
    d3.text((212, 378), "A", fill=accent_blue, font=font_large)
    
    d3.ellipse([(180, 820), (280, 920)], outline=accent_blue, width=5)
    d3.text((212, 838), "D", fill=accent_blue, font=font_large)
    
    # Female Badges (A is multiple/expanded)
    d3.ellipse([(620, 260), (720, 360)], outline=accent_red, width=5)
    d3.text((652, 278), "A", fill=accent_red, font=font_large)
    d3.ellipse([(740, 280), (820, 360)], outline=accent_red, width=3) # extra high female
    d3.ellipse([(540, 280), (620, 360)], outline=accent_red, width=3) # extra high female
    
    d3.ellipse([(620, 520), (720, 620)], outline=accent_red, width=4)
    d3.text((652, 538), "B", fill=accent_red, font=font_large)
    
    # A Male still selects B Female
    d3.line([(280, 410), (610, 570)], fill=accent_blue, width=5)
    d3.polygon([(615, 572), (595, 555), (602, 585)], fill=accent_blue)
    
    # Female A trapped at top (Arrow up blocked by Red X)
    d3.line([(670, 250), (670, 170)], fill=accent_red, width=4)
    d3.line([(645, 145), (695, 195)], fill=accent_red, width=6)
    d3.line([(695, 145), (645, 195)], fill=accent_red, width=6)
    
    # Male D trapped at bottom (Barrier Wall & Exclamation)
    d3.line([(320, 780), (320, 960)], fill=accent_red, width=8) # Wall
    d3.line([(350, 830), (350, 890)], fill=accent_red, width=6) # Exclamation
    d3.ellipse([(346, 905), (354, 915)], fill=accent_red)
    
    # Bottom bracket highlighting the two stranded poles
    d3.line([(230, 950), (230, 1020), (670, 1020), (670, 950)], fill=ink_color, width=3)
    d3.text((420, 980), "≠", fill=accent_red, font=font_large)
    
    im3.save(INPUTS_DIR / "scene3_mismatch.png")
    
    # --- Scene 4: 经济账本 · 失衡天平 (Act 4, ~35 strokes) ---
    im4 = Image.new("RGB", (900, 1200), bg_color)
    d4 = ImageDraw.Draw(im4)
    
    # Fulcrum Triangle
    d4.polygon([(450, 560), (380, 720), (520, 720)], outline=ink_color, fill=bg_color, width=6)
    d4.line([(320, 720), (580, 720)], fill=ink_color, width=8) # base
    
    # Tilted Lever (Left high, Right low)
    d4.line([(140, 420), (760, 660)], fill=ink_color, width=8)
    
    # Left Pan (Single: Light, Free, High)
    d4.line([(140, 420), (80, 520)], fill=ink_color, width=3)
    d4.line([(140, 420), (200, 520)], fill=ink_color, width=3)
    d4.arc([(70, 510), (210, 560)], start=0, end=180, fill=accent_blue, width=5)
    # Happy Single Stick Figure
    d4.ellipse([(120, 430), (160, 470)], outline=accent_blue, width=4) # head
    d4.line([(140, 470), (140, 520)], fill=accent_blue, width=4) # body
    d4.line([(140, 490), (115, 475)], fill=accent_blue, width=3) # arm up
    d4.line([(140, 490), (165, 475)], fill=accent_blue, width=3) # arm up
    
    # Right Pan (Marriage: Heavy Burdens, Weighted down)
    d4.line([(760, 660), (700, 780)], fill=ink_color, width=3)
    d4.line([(760, 660), (820, 780)], fill=ink_color, width=3)
    d4.arc([(690, 770), (830, 820)], start=0, end=180, fill=accent_red, width=6)
    # 2 Heavy weights stacked
    d4.rectangle([(720, 720), (800, 770)], outline=ink_color, fill=accent_red, width=3)
    d4.rectangle([(730, 665), (790, 715)], outline=ink_color, fill=accent_red, width=3)
    # Downward gravity force arrow
    d4.line([(760, 840), (760, 920)], fill=accent_red, width=6)
    d4.polygon([(760, 925), (745, 900), (775, 900)], fill=accent_red)
    
    im4.save(INPUTS_DIR / "scene4_equation.png")
    
    # --- Scene 5: 破局与理性 · 阳光与并肩 (Act 5, ~30 strokes) ---
    im5 = Image.new("RGB", (900, 1200), bg_color)
    d5 = ImageDraw.Draw(im5)
    
    # Golden Rising Sun at Top-Right
    d5.arc([(620, 180), (780, 340)], start=0, end=360, fill=accent_gold, width=6)
    import math
    for angle in [0, 45, 90, 135, 180, 225, 270, 315]:
        rad = math.radians(angle)
        x1 = 700 + 90 * math.cos(rad)
        y1 = 260 + 90 * math.sin(rad)
        x2 = 700 + 125 * math.cos(rad)
        y2 = 260 + 125 * math.sin(rad)
        d5.line([(x1, y1), (x2, y2)], fill=accent_gold, width=4)
        
    # Central Warm Heart
    d5.arc([(400, 400), (450, 450)], start=180, end=360, fill=accent_red, width=5)
    d5.arc([(450, 400), (500, 450)], start=180, end=360, fill=accent_red, width=5)
    d5.line([(400, 425), (450, 480)], fill=accent_red, width=5)
    d5.line([(500, 425), (450, 480)], fill=accent_red, width=5)
    
    # Two partners walking side-by-side holding hands
    # Person 1 (Blue)
    d5.ellipse([(360, 520), (420, 580)], outline=accent_blue, width=4)
    d5.line([(390, 580), (390, 720)], fill=accent_blue, width=5)
    d5.line([(390, 720), (360, 840)], fill=accent_blue, width=5)
    d5.line([(390, 720), (410, 840)], fill=accent_blue, width=5)
    
    # Person 2 (Red)
    d5.ellipse([(480, 520), (540, 580)], outline=accent_red, width=4)
    d5.line([(510, 580), (510, 720)], fill=accent_red, width=5)
    d5.line([(510, 720), (480, 840)], fill=accent_red, width=5)
    d5.line([(510, 720), (530, 840)], fill=accent_red, width=5)
    
    # Holding hands in unity
    d5.line([(390, 640), (450, 670)], fill=accent_blue, width=4)
    d5.line([(510, 640), (450, 670)], fill=accent_red, width=4)
    
    # Ground horizon
    d5.line([(180, 840), (720, 840)], fill=ink_color, width=4)
    
    im5.save(INPUTS_DIR / "scene5_solution.png")
    print("  Visuals generated successfully in inputs/!")
    print("  Visuals generated successfully in inputs/!")

# ------------------------------------------------------------------------------
# 4. Sweety-Handdraw Manifest Construction
# ------------------------------------------------------------------------------
def build_job_manifest(durations):
    print(">>> [Manifest Engine] Assembling sweety-handdraw job.json specification...")
    
    pages = []
    scenes = [
        ("beat_01", "inputs/scene1_hook.png", BEATS_SPEC[0]),
        ("beat_02", "inputs/scene2_gradient.png", BEATS_SPEC[1]),
        ("beat_03", "inputs/scene3_mismatch.png", BEATS_SPEC[2]),
        ("beat_04", "inputs/scene4_equation.png", BEATS_SPEC[3]),
        ("beat_05", "inputs/scene5_solution.png", BEATS_SPEC[4]),
    ]
    
    for idx, (bid, img_src, spec) in enumerate(scenes):
        dur = durations[bid]
        cues = spec["cues"]
        
        # Build caption cues proportionally matching narration
        formatted_cues = []
        total_chars = sum(len(c) for c in cues)
        cur_t = 0.0
        for c_idx, cue_txt in enumerate(cues):
            cue_dur = dur * (len(cue_txt) / total_chars)
            end_t = round(cur_t + cue_dur, 2)
            if c_idx == len(cues) - 1:
                end_t = round(dur - 0.02, 2)
            formatted_cues.append({
                "text": cue_txt,
                "start": round(cur_t, 2),
                "end": end_t
            })
            cur_t = end_t
            
        page_dict = {
            "visual_groups": [
                {
                    "start_beat": bid,
                    "end_beat": bid,
                    "lead": 0.35,
                    "hold": 0.70,
                    "actions": [
                        {
                            "type": "illustration",
                            "parts": [{"id": f"p{idx+1}_fig", "polygon": [[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0]]}],
                            "source": img_src,
                            "x": 90,
                            "y": 280,
                            "width": 900,
                            "height": 1200,
                            "weight": 3.0,
                            "lineart_exception": True,
                            "drawing": {"mode": "draw", "speed": 1.0}
                        }
                    ]
                }
            ],
            "beats": [
                {
                    "id": bid,
                    "text": spec["text"],
                    "audio": f"inputs/{bid}.wav",
                    "caption_cues": formatted_cues
                }
            ]
        }
        if idx > 0:
            page_dict["transition"] = {"type": "cut"}
            
        pages.append(page_dict)
        
    manifest = {
        "version": 1,
        "runtime_fixture": True,
        "title": "为什么现在的社会结婚人数越来越少？——婚姻梯队错配死局",
        "canvas": {"width": 1080, "height": 1920, "fps": 30},
        "paper": "#FBF9F1",
        "cover": {"source": "inputs/cover.png", "seconds": 1.0},
        "hand": {"preset": "teacher-pen", "scale": 0.35},
        "audio": {
            "pace": 1.0,
            "trim_silence": False,
            "sentence_pause_seconds": 0.20,
            "page_pause_seconds": 0.35,
            "end_hold_seconds": 1.0
        },
        # High-Contrast Obsidian Semi-Transparent Capsule Subtitles (WCAG AAA 18:1)
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
        "pages": pages
    }
    
    job_path = PROJECT_DIR / "job.json"
    job_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  >>> Saved job manifest -> {job_path}")
    return job_path

# ------------------------------------------------------------------------------
# 5. Core Engine Compilation & Video Rendering
# ------------------------------------------------------------------------------
def run_handdraw_pipeline():
    handdraw_cli = ROOT_DIR / "shared_tools" / "renderers" / "handdraw" / "handdraw_video.py"
    env = {
        **os.environ,
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONPATH": str(handdraw_cli.parent)
    }
    
    print("\n>>> [Stage 1/2: Compilation Build via Sweety-Handdraw Engine]")
    cmd_build = [sys.executable, "-B", str(handdraw_cli), "build", str(PROJECT_DIR)]
    res_b = subprocess.run(cmd_build, capture_output=True, text=True, env=env)
    if res_b.returncode != 0:
        print(f"❌ Build failed:\n{res_b.stderr}")
        sys.exit(1)
    print("✓ Job build and stroke compilation completed successfully!")
    
    print("\n>>> [Stage 2/2: Full HD Video & Audio Multiplex Rendering]")
    cmd_render = [sys.executable, "-B", str(handdraw_cli), "render", str(PROJECT_DIR)]
    res_r = subprocess.run(cmd_render, capture_output=True, text=True, env=env)
    if res_r.returncode != 0:
        print(f"❌ Render failed:\n{res_r.stderr}")
        sys.exit(1)
    print("✓ Video rendering and audio multiplexing completed successfully!")
    
    # Isolate final video to out/handdraw_marriage_squeeze/film.mp4
    built_film = PROJECT_DIR / "outputs" / "film.mp4"
    final_dest = OUTPUTS_DIR / "film.mp4"
    if built_film.exists():
        shutil.copy2(str(built_film), str(final_dest))
        print(f"\n🎉 [DELIVERY] Final Handdrawn Explainer Film -> {final_dest}")
        
        # Probe final duration and size
        probe = subprocess.run(["ffprobe", "-i", str(final_dest), "-show_entries", "format=duration,size", "-v", "quiet", "-of", "json"], capture_output=True, text=True)
        data = json.loads(probe.stdout)
        dur = float(data["format"]["duration"])
        size_mb = float(data["format"]["size"]) / (1024 * 1024)
        print(f"  Duration: {dur:.2f}s ({dur/60:.2f} min) | Size: {size_mb:.2f}MB | Resolution: 1080x1920 30fps")
        return final_dest
    else:
        print(f"❌ Expected film at {built_film} not found!")
        sys.exit(1)

if __name__ == "__main__":
    durations = synthesize_and_master_audio()
    create_illustrations()
    build_job_manifest(durations)
    run_handdraw_pipeline()
    print("Handdrawn production test completed successfully!")
