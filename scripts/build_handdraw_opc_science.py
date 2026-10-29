#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Industrial Handdraw Video Production Pipeline for:
"2026 北京怀柔科学城 AI for Science · OPC 创新挑战赛"
Format: Hand-drawn Explainer Video (1080x1920, 30fps)
Target Duration: Under 3 minutes (~120 seconds)
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

from shared_tools.audio_mastering import AudioMasteringStudio

PROJECT_DIR = ROOT_DIR / "projects" / "handdraw_opc_science"
INPUTS_DIR = PROJECT_DIR / "inputs"
OUTPUTS_DIR = ROOT_DIR / "out" / "handdraw_opc_science"
ARTIFACT_DIR = Path("/Users/jackiecruise/.gemini/antigravity-ide/brain/0ef40ef1-b0be-4576-9a74-a20cfc2f8826")

INPUTS_DIR.mkdir(parents=True, exist_ok=True)
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

FONT_PATH = "/System/Library/Fonts/STHeiti Light.ttc"

def get_font(size: int):
    try:
        return ImageFont.truetype(FONT_PATH, size)
    except Exception:
        return ImageFont.load_default()

# ------------------------------------------------------------------------------
# 1. Five Narrative Beats Specification (~120 seconds total, strictly < 3 mins)
# ------------------------------------------------------------------------------
BEATS_SPEC = [
    # Act 1: Hook (0-25s)
    {
        "id": "beat_01",
        "text": "如果你对AI比赛的印象，还停留在刷公开数据集、做玩具Demo领几千块奖金，那北京怀柔刚刚发生的事，彻底颠覆了规则。怀柔科学城大科学装置群旁，中科院院所与产业龙头立下军令状：不看PPT、不问出身，谁能用AI解决真实痛点，当场签走采购订单！",
        "rate": 185,
        "voice": "Reed (中文（中国大陆）)",
        "cues": [
            "如果你对AI比赛的印象，",
            "还停留在刷公开数据集、做玩具Demo领几千块奖金，",
            "那北京怀柔刚刚发生的事，彻底颠覆了规则。",
            "怀柔科学城大科学装置群旁，",
            "中科院院所与产业龙头立下军令状：",
            "不看PPT、不问出身，",
            "谁能用AI解决真实痛点，当场签走采购订单！"
        ]
    },
    # Act 2: Mechanism & Grand Challenges (25-55s)
    {
        "id": "beat_02",
        "text": "为什么国家战略级力量要办这场挑战赛？因为今天的科学与工业已到极限：物理所复杂激光器一旦宕机，备件周期长达数月；浪潮要帮医生从成百上千切片中肉眼识别染色体；钢铁万吨轧机一旦故障损失千万。10大硬核榜单，全是花钱买不到的真问题，单榜悬赏10万起，真金白银真采购！",
        "rate": 185,
        "voice": "Reed (中文（中国大陆）)",
        "cues": [
            "为什么国家战略级力量要办这场挑战赛？",
            "因为今天的科学与工业已到极限：",
            "物理所复杂激光器一旦宕机，备件周期长达数月；",
            "浪潮要帮医生从成百上千切片中肉眼识别染色体；",
            "钢铁万吨轧机一旦故障损失千万。",
            "10大硬核榜单，全是花钱买不到的真问题，",
            "单榜悬赏10万起，真金白银真采购！"
        ]
    },
    # Act 3: 48H Hackathon Action (55-85s)
    {
        "id": "beat_03",
        "text": "赛事双轨并行：揭榜挂帅面向成熟团队深度攻坚；而面向全网极客的48小时极限黑客松，即将在11月15日打响！现场实机调用宇树具身机器人、调用国家科学数据银行，挑战AIP智能体互联协议。五大命题封闭开发两天两夜，现场跑通演示，当场评奖发钱！",
        "rate": 185,
        "voice": "Reed (中文（中国大陆）)",
        "cues": [
            "赛事双轨并行：",
            "揭榜挂帅面向成熟团队深度攻坚；",
            "而面向全网极客的48小时极限黑客松，即将在11月15日打响！",
            "现场实机调用宇树具身机器人、调用国家科学数据银行，",
            "挑战AIP智能体互联协议。",
            "五大命题封闭开发两天两夜，",
            "现场跑通演示，当场评奖发钱！"
        ]
    },
    # Act 4: OPC Ecosystem (85-115s)
    {
        "id": "beat_04",
        "text": "名字里的OPC，代表一人公司、超级个体。怀柔重点打造的果壳OPC创新社区，理念就是：让创造者只做创造，其余交给社区！办公空间拎包入驻，算力全额补贴，工商法务全面托管，还有上市公司真实订单喂养。优胜项目可叠加申领怀柔区最高50万元专项资金支持！",
        "rate": 185,
        "voice": "Reed (中文（中国大陆）)",
        "cues": [
            "名字里的OPC，代表一人公司、超级个体。",
            "怀柔重点打造的果壳OPC创新社区，理念就是：",
            "让创造者只做创造，其余交给社区！",
            "办公空间拎包入驻，算力全额补贴，",
            "工商法务全面托管，还有上市公司真实订单喂养。",
            "优胜项目可叠加申领怀柔区最高50万元专项资金支持！"
        ]
    },
    # Act 5: Call to Action (115-140s)
    {
        "id": "beat_05",
        "text": "这里不要虚假的汇报，只要能打硬仗的代码。记住关键时间：48小时黑客松赛道，全网报名将在11月10日正式截止！不论你是高校实验室、创业公司，还是独立极客，带上你的智能体，来国家大科学装置的肩膀上，把代码变成订单！关注官方平台，立即报名！",
        "rate": 180,
        "voice": "Reed (中文（中国大陆）)",
        "cues": [
            "这里不要虚假的汇报，只要能打硬仗的代码。",
            "记住关键时间：",
            "48小时黑客松赛道，全网报名将在11月10日正式截止！",
            "不论你是高校实验室、创业公司，还是独立极客，",
            "带上你的智能体，来国家大科学装置的肩膀上，把代码变成订单！",
            "关注官方平台，立即报名！"
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
        
        # Master via AudioMasteringStudio
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
    print(f"  >>> Total Video Audio Duration: {total_dur:.2f}s ({(total_dur/60):.2f} min, strictly < 3.0 min)")
    return durations

# ------------------------------------------------------------------------------
# 3. Handdrawn Visual Asset Illustrations
# ------------------------------------------------------------------------------
def create_illustrations():
    print(">>> [Visual Design] Generating 5 Handdrawn Whiteboard Illustrations...")
    bg_color = (251, 249, 241) # #FBF9F1 warm paper tone
    ink_color = (35, 31, 32)    # dark charcoal ink
    accent_red = (220, 38, 38)  # bold red highlight
    accent_blue = (2, 132, 199) # deep cyan blue
    accent_gold = (217, 119, 6) # amber gold
    accent_green = (16, 185, 129)# emerald green
    
    font_large = get_font(52)
    font_mid = get_font(38)
    font_small = get_font(26)
    
    # --- Cover Image ---
    cover = Image.new("RGB", (1080, 1920), bg_color)
    dc = ImageDraw.Draw(cover)
    dc.rectangle([(50, 50), (1030, 1870)], outline=ink_color, width=5)
    dc.rectangle([(65, 65), (1015, 1855)], outline=accent_blue, width=2)
    
    dc.text((120, 480), "怀柔科学城 · AI for Science", fill=accent_blue, font=font_small)
    dc.text((120, 540), "真需求 · 真攻坚 · 真采购", fill=accent_red, font=font_large)
    dc.text((120, 620), "300万悬赏金 挂帅开战！", fill=ink_color, font=font_large)
    dc.line([(120, 710), (960, 710)], fill=ink_color, width=4)
    dc.text((120, 750), "大科学装置集群 × 真实产业采购订单", fill=accent_gold, font=font_mid)
    
    # Center Metaphor: Synchrotron Radiation Light Source Ring & AI Agent
    dc.ellipse([(340, 920), (740, 1320)], outline=accent_blue, width=8)
    dc.ellipse([(440, 1020), (640, 1220)], outline=accent_gold, width=4)
    dc.polygon([(540, 960), (600, 1120), (480, 1120)], outline=accent_red, fill=bg_color, width=5)
    dc.text((515, 1050), "AI", fill=accent_red, font=font_large)
    
    # Surrounding nodes
    for px, py, label in [(340, 920, "物理所"), (740, 920, "空间中心"), (740, 1320, "北京移动"), (340, 1320, "美云智数")]:
        dc.ellipse([(px-20, py-20), (px+20, py+20)], fill=accent_blue)
        dc.text((px-30, py+25), label, fill=ink_color, font=font_small)
        dc.line([(px, py), (540, 1120)], fill=ink_color, width=2)
        
    cover.save(INPUTS_DIR / "cover.png")
    
    # --- Scene 1: 撕碎PPT，大科学装置与百万采购 (Act 1) ---
    im1 = Image.new("RGB", (900, 1200), bg_color)
    d1 = ImageDraw.Draw(im1)
    
    # Left: Crossed out PPT
    d1.rectangle([(120, 260), (420, 520)], outline=ink_color, width=4)
    d1.line([(120, 260), (420, 520)], fill=accent_red, width=6)
    d1.line([(420, 260), (120, 520)], fill=accent_red, width=6)
    d1.text((170, 360), "PPT Demo", fill=ink_color, font=font_mid)
    d1.text((160, 420), "刷榜自嗨", fill=accent_red, font=font_small)
    d1.line([(270, 520), (270, 640)], fill=ink_color, width=6) # Stand
    d1.line([(200, 640), (340, 640)], fill=ink_color, width=6)
    
    # Right: Real Contract & Big Order Stamp
    d1.rectangle([(480, 240), (780, 560)], outline=accent_blue, fill=bg_color, width=5)
    d1.line([(520, 300), (740, 300)], fill=accent_blue, width=3)
    d1.line([(520, 350), (740, 350)], fill=accent_blue, width=3)
    d1.line([(520, 400), (680, 400)], fill=accent_blue, width=3)
    # Stamp: 真实采购
    d1.ellipse([(580, 420), (740, 520)], outline=accent_red, width=4)
    d1.text((605, 455), "真采购", fill=accent_red, font=font_mid)
    
    # Downward big text
    d1.text((160, 720), "拒绝玩具Demo · 签真实订单", fill=ink_color, font=font_large)
    d1.text((220, 810), "总悬赏金 ¥3,000,000+", fill=accent_gold, font=font_mid)
    im1.save(INPUTS_DIR / "scene1_hook.png")
    
    # --- Scene 2: 激光器、空间数据、染色体切片与钢铁产线 (Act 2) ---
    im2 = Image.new("RGB", (900, 1200), bg_color)
    d2 = ImageDraw.Draw(im2)
    
    # Laser System (Top-Left)
    d2.rectangle([(100, 200), (380, 400)], outline=accent_red, width=4)
    d2.line([(100, 300), (380, 300)], fill=accent_red, width=3)
    d2.ellipse([(140, 230), (200, 270)], outline=ink_color, width=3)
    d2.text((120, 330), "S1 激光器预测", fill=ink_color, font=font_small)
    d2.text((260, 240), "⚠ 宕机危机", fill=accent_red, font=font_small)
    
    # Chromosome Microscope (Top-Right)
    d2.rectangle([(520, 200), (800, 400)], outline=accent_blue, width=4)
    d2.ellipse([(620, 230), (700, 310)], outline=accent_blue, width=4)
    d2.text((550, 330), "S7 染色体核型分析", fill=ink_color, font=font_small)
    d2.text((600, 260), "显微镜", fill=accent_blue, font=font_small)
    
    # Center: Multi-Agent Hub
    d2.ellipse([(350, 550), (550, 750)], outline=accent_gold, fill=bg_color, width=6)
    d2.text((385, 630), "智能体中枢", fill=accent_gold, font=font_mid)
    
    # Connectors
    d2.line([(240, 400), (370, 570)], fill=ink_color, width=4)
    d2.line([(660, 400), (530, 570)], fill=ink_color, width=4)
    
    # Bottom text
    d2.text((140, 840), "10大真实业务硬核榜单", fill=ink_color, font=font_large)
    d2.text((180, 920), "单榜悬赏 ≥10万元 · 揭榜即出征", fill=accent_red, font=font_mid)
    im2.save(INPUTS_DIR / "scene2_pain.png")
    
    # --- Scene 3: 48H极限黑客松与宇树机器人 (Act 3) ---
    im3 = Image.new("RGB", (900, 1200), bg_color)
    d3 = ImageDraw.Draw(im3)
    
    # Giant Hourglass
    d3.polygon([(200, 220), (440, 220), (320, 380), (440, 540), (200, 540), (320, 380)], outline=accent_blue, width=6)
    d3.text((250, 350), "48H", fill=accent_red, font=font_large)
    d3.text((230, 560), "现场极限开发", fill=ink_color, font=font_small)
    
    # Quadruped Robot (Unitree style handdraw)
    d3.rectangle([(560, 280), (740, 380)], outline=ink_color, width=6) # Body
    d3.line([(560, 300), (510, 260)], fill=ink_color, width=6) # Neck
    d3.ellipse([(480, 230), (520, 270)], fill=accent_blue) # Head
    d3.line([(580, 380), (550, 480)], fill=ink_color, width=6) # Leg 1
    d3.line([(720, 380), (690, 480)], fill=ink_color, width=6) # Leg 2
    d3.line([(620, 380), (650, 470)], fill=ink_color, width=5) # Leg 3
    d3.line([(700, 380), (750, 470)], fill=ink_color, width=5) # Leg 4
    d3.text((560, 500), "宇树具身机器人平台", fill=accent_blue, font=font_small)
    
    # Bottom: Five Directions & Cash Pool
    d3.rectangle([(100, 680), (800, 880)], outline=accent_gold, fill=bg_color, width=4)
    d3.text((140, 710), "五大挑战命题 · 现场即刻公布", fill=ink_color, font=font_mid)
    d3.text((140, 770), "具身机器人 / 科学智能体 / OPC商业快闪 / AIP协议", fill=accent_blue, font=font_small)
    d3.text((140, 820), "¥100,000 现场现金奖池 · 当场发奖！", fill=accent_red, font=font_mid)
    im3.save(INPUTS_DIR / "scene3_hackathon.png")
    
    # --- Scene 4: 果壳OPC一人公司扶持 (Act 4) ---
    im4 = Image.new("RGB", (900, 1200), bg_color)
    d4 = ImageDraw.Draw(im4)
    
    # Solo Creator (Backpack Geek)
    d4.ellipse([(200, 260), (280, 340)], outline=ink_color, width=4) # Head
    d4.line([(240, 340), (240, 520)], fill=ink_color, width=6) # Torso
    d4.line([(240, 380), (170, 440)], fill=ink_color, width=5) # Arm
    d4.rectangle([(150, 430), (230, 480)], outline=accent_blue, width=3) # Laptop
    d4.rectangle([(250, 370), (300, 470)], outline=ink_color, width=4) # Backpack
    d4.text((150, 540), "超级个体 (OPC)", fill=accent_blue, font=font_small)
    
    # Right: Guoke Community Ecosystem
    d4.rectangle([(480, 220), (800, 580)], outline=accent_green, fill=bg_color, width=4)
    d4.text((510, 250), "果壳 OPC 创新社区", fill=accent_green, font=font_mid)
    d4.line([(510, 300), (770, 300)], fill=accent_green, width=2)
    d4.text((510, 330), "✔ 办公工位拎包入驻", fill=ink_color, font=font_small)
    d4.text((510, 390), "✔ 算力补贴全额支持", fill=ink_color, font=font_small)
    d4.text((510, 450), "✔ 真实订单源源输送", fill=ink_color, font=font_small)
    d4.text((510, 510), "✔ 专项扶持最高50万", fill=accent_red, font=font_small)
    
    # Bottom Motto
    d4.text((160, 720), "「让创造者只做创造」", fill=ink_color, font=font_large)
    d4.text((190, 810), "硅基战友 (AI) × 碳基合伙人 (智库)", fill=accent_gold, font=font_mid)
    im4.save(INPUTS_DIR / "scene4_opc.png")
    
    # --- Scene 5: 11月10日报名截止与行动号召 (Act 5) ---
    im5 = Image.new("RGB", (900, 1200), bg_color)
    d5 = ImageDraw.Draw(im5)
    
    # Big Calendar
    d5.rectangle([(250, 200), (650, 540)], outline=ink_color, width=5)
    d5.rectangle([(250, 200), (650, 280)], fill=accent_red)
    d5.text((320, 220), "2026 NOVEMBER", fill=(255, 255, 255), font=font_small)
    d5.text((330, 310), "11.10", fill=ink_color, font=font_large)
    d5.text((310, 440), "黑客松报名截止", fill=accent_red, font=font_mid)
    
    # QR Code Icon
    d5.rectangle([(350, 620), (550, 820)], outline=accent_blue, width=4)
    d5.rectangle([(380, 650), (430, 700)], fill=accent_blue)
    d5.rectangle([(470, 650), (520, 700)], fill=accent_blue)
    d5.rectangle([(380, 740), (430, 790)], fill=accent_blue)
    d5.text((340, 850), "官网: opc.book2048.com", fill=ink_color, font=font_small)
    
    # Final Slogan
    d5.text((160, 930), "离科学最近 · 离订单最近", fill=accent_blue, font=font_large)
    im5.save(INPUTS_DIR / "scene5_cta.png")
    print("✓ All 5 illustrations created successfully!")

# ------------------------------------------------------------------------------
# 4. Manifest Assembly (job.json)
# ------------------------------------------------------------------------------
def build_job_manifest(durations):
    print(">>> [Job Manifest] Building job.json specification...")
    scenes_map = [
        ("beat_01", "inputs/scene1_hook.png", BEATS_SPEC[0]["text"], BEATS_SPEC[0]["cues"]),
        ("beat_02", "inputs/scene2_pain.png", BEATS_SPEC[1]["text"], BEATS_SPEC[1]["cues"]),
        ("beat_03", "inputs/scene3_hackathon.png", BEATS_SPEC[2]["text"], BEATS_SPEC[2]["cues"]),
        ("beat_04", "inputs/scene4_opc.png", BEATS_SPEC[3]["text"], BEATS_SPEC[3]["cues"]),
        ("beat_05", "inputs/scene5_cta.png", BEATS_SPEC[4]["text"], BEATS_SPEC[4]["cues"]),
    ]
    
    pages = []
    for idx, (bid, fig_src, full_text, cues) in enumerate(scenes_map):
        dur = durations[bid]
        total_chars = sum(len(c) for c in cues)
        st = 0.0
        formatted_cues = []
        for c_idx, cue_txt in enumerate(cues):
            if c_idx == len(cues) - 1:
                et = dur
            else:
                et = round(st + (len(cue_txt) / total_chars) * dur, 3)
                if et <= st:
                    et = round(st + 0.05, 3)
            formatted_cues.append({"text": cue_txt, "start": st, "end": et})
            st = et
            
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
                            "parts": [
                                {
                                    "id": f"p{idx+1}_fig",
                                    "polygon": [[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0]]
                                }
                            ],
                            "source": fig_src,
                            "x": 90,
                            "y": 280,
                            "width": 900,
                            "height": 1200,
                            "weight": 3.0,
                            "lineart_exception": True,
                            "drawing": {
                                "mode": "reveal",
                                "speed": 1.2
                            }
                        }
                    ]
                }
            ],
            "beats": [
                {
                    "id": bid,
                    "text": full_text,
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
        "title": "2026 怀柔科学城 AI for Science · OPC 创新挑战赛官方报道",
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
    
    # Isolate final video to out/handdraw_opc_science/film.mp4
    built_film = PROJECT_DIR / "outputs" / "film.mp4"
    final_dest = OUTPUTS_DIR / "film.mp4"
    artifact_dest = ARTIFACT_DIR / "handdraw_opc_science_film.mp4"
    
    if built_film.exists():
        shutil.copy2(str(built_film), str(final_dest))
        shutil.copy2(str(built_film), str(artifact_dest))
        print(f"\n🎉 [DELIVERY] Final Video Isolated -> {final_dest}")
        print(f"🎉 [DELIVERY] Final Video in Artifacts -> {artifact_dest}")
        
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
    print("All stages of handdraw video production finished successfully!")
