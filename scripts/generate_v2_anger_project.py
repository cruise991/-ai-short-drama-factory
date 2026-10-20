import os
import sys
import json
import wave
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# Set project paths
PROJECT_DIR = Path("/Users/workspace/ai_short_company/ai-short-drama/projects/handdraw_anger_decision_v2")
INPUTS_DIR = PROJECT_DIR / "inputs"
INPUTS_DIR.mkdir(parents=True, exist_ok=True)

# 1. Spoken narration beats tailored for adult psychology and emotional curve
BEATS_CONFIG = [
    {
        "id": "beat_01",
        "text": "你有没有过这种经历：刚冲动发完一段质问，下一秒就恨不得抽自己耳光？在暴怒的那几秒钟里，我们做出的决定，几乎百分之百是错的。",
        "voice": "Reed (中文（中国大陆）)",
        "rate": 182,
        "cues": [
            {"text": "你有没有过这种经历：", "start": 0.0, "end": 1.6},
            {"text": "刚冲动发完一段质问，下一秒就恨不得抽自己耳光？", "start": 1.6, "end": 5.4},
            {"text": "在暴怒的那几秒钟里，我们做出的决定，几乎百分之百是错的。", "start": 5.4, "end": None}
        ]
    },
    {
        "id": "beat_02",
        "text": "很多人以为这是性格暴躁或情商低。但在脑科学看来，这真不怪你，而是你的大脑刚刚经历了一场恶性夺权！",
        "voice": "Reed (中文（中国大陆）)",
        "rate": 185,
        "cues": [
            {"text": "很多人以为这是性格暴躁或情商低。", "start": 0.0, "end": 2.8},
            {"text": "但在脑科学看来，这真不怪你，", "start": 2.8, "end": 5.0},
            {"text": "而是你的大脑刚刚经历了一场恶性夺权！", "start": 5.0, "end": None}
        ]
    },
    {
        "id": "beat_03",
        "text": "在正常情况下，我们负责理性分析和权衡利弊的，是前额叶皮层，他是掌管全局的理智脑总裁。",
        "voice": "Reed (中文（中国大陆）)",
        "rate": 180,
        "cues": [
            {"text": "在正常情况下，我们负责理性分析和权衡利弊的，", "start": 0.0, "end": 3.6},
            {"text": "是前额叶皮层，他是掌管全局的理智脑总裁。", "start": 3.6, "end": None}
        ]
    },
    {
        "id": "beat_04",
        "text": "而大脑深处还有一个原始的战斗警报器——杏仁核，就像公司里脾气火爆的暴走安保。",
        "voice": "Reed (中文（中国大陆）)",
        "rate": 184,
        "cues": [
            {"text": "而大脑深处还有一个原始的战斗警报器——杏仁核，", "start": 0.0, "end": 3.6},
            {"text": "就像公司里脾气火爆的暴走安保。", "start": 3.6, "end": None}
        ]
    },
    {
        "id": "beat_05",
        "text": "一旦火气被点燃，杏仁核只要二十毫秒就能引爆战斗，掏出电棍，直接把理智脑总裁反锁进了更衣室！前额叶瞬间掉线，你所有的发飙，全凭原始肌肉记忆了。",
        "voice": "Reed (中文（中国大陆）)",
        "rate": 188,
        "cues": [
            {"text": "一旦火气被点燃，杏仁核只要二十毫秒就能引爆战斗，", "start": 0.0, "end": 3.6},
            {"text": "掏出电棍，直接把理智脑总裁反锁进了更衣室！", "start": 3.6, "end": 6.8},
            {"text": "前额叶瞬间掉线，你所有的发飙，全凭原始肌肉记忆了。", "start": 6.8, "end": None}
        ]
    },
    {
        "id": "beat_06",
        "text": "但好消息是，安保掏出的电棍，生理电量只能维持大约二十秒。",
        "voice": "Reed (中文（中国大陆）)",
        "rate": 178,
        "cues": [
            {"text": "但好消息是，", "start": 0.0, "end": 1.2},
            {"text": "安保掏出的电棍，生理电量只能维持大约二十秒。", "start": 1.2, "end": None}
        ]
    },
    {
        "id": "beat_07",
        "text": "下次血涌上头时，记住：什么都别说，双手插兜，做三次深长的腹式呼吸。给更衣室里的总裁二十秒撬开锁，你的理性就能夺回方向盘。",
        "voice": "Reed (中文（中国大陆）)",
        "rate": 180,
        "cues": [
            {"text": "下次血涌上头时，记住：什么都别说，双手插兜，做三次深长的腹式呼吸。", "start": 0.0, "end": 5.4},
            {"text": "给更衣室里的总裁二十秒撬开锁，你的理性就能夺回方向盘。", "start": 5.4, "end": None}
        ]
    }
]

def synthesize_voices():
    print(">>> 1. Synthesizing high-res expressive voices...")
    durations = {}
    for item in BEATS_CONFIG:
        bid = item["id"]
        text = item["text"]
        rate = item["rate"]
        voice = item["voice"]
        
        aiff_p = INPUTS_DIR / f"{bid}.aiff"
        wav_p = INPUTS_DIR / f"{bid}.wav"
        
        # Synthesize with rate control
        cmd_say = ["say", "-v", voice, "-r", str(rate), "-o", str(aiff_p), text]
        subprocess.run(cmd_say, check=True)
        
        # Convert to standard 48kHz mono 16-bit PCM WAV
        cmd_ffmpeg = [
            "ffmpeg", "-y", "-v", "error", "-i", str(aiff_p),
            "-ar", "48000", "-ac", "1", "-c:a", "pcm_s16le", str(wav_p)
        ]
        subprocess.run(cmd_ffmpeg, check=True)
        if aiff_p.exists():
            aiff_p.unlink()
            
        with wave.open(str(wav_p), "rb") as wf:
            dur = wf.getnframes() / float(wf.getframerate())
        durations[bid] = round(dur, 3)
        print(f"  [{bid}] Duration: {dur:.2f}s | Text: {text[:25]}...")
        
    total_time = sum(durations.values())
    print(f"Total Spoken Time: {total_time:.2f}s (Target: ~55s)\n")
    return durations

def create_visual_metaphor_illustrations():
    print(">>> 2. Creating custom handdrawn visual metaphor illustrations...")
    # Canvas for illustrations: 900x1200 on #FBF9F1 background, pure black minimalist ink lines
    bg_color = (251, 249, 241) # #FBF9F1
    ink_color = (35, 31, 32)   # Deep ink black
    accent_red = (211, 47, 47) # Red accent for alarm/emergency
    accent_gold = (212, 160, 23)# Gold for the unlock key
    
    # -------------------------------------------------------------
    # Illustration 1: 理智脑总裁 vs 暴走安保拉响火警 (Scene 1)
    # -------------------------------------------------------------
    im1 = Image.new("RGB", (900, 1200), bg_color)
    d1 = ImageDraw.Draw(im1)
    
    # Draw desk & CEO (Suit, glasses, calm coffee)
    # Desk
    d1.line([(100, 750), (450, 750)], fill=ink_color, width=6)
    d1.line([(140, 750), (140, 1050)], fill=ink_color, width=5)
    d1.line([(410, 750), (410, 1050)], fill=ink_color, width=5)
    # Coffee cup on desk
    d1.rectangle([(180, 700), (220, 750)], outline=ink_color, width=4)
    d1.arc([(220, 715), (240, 735)], start=270, end=90, fill=ink_color, width=4)
    # CEO figure
    d1.ellipse([(240, 480), (320, 560)], outline=ink_color, width=5) # Head
    d1.rectangle([(255, 510), (275, 525)], outline=ink_color, width=3) # Glasses L
    d1.rectangle([(285, 510), (305, 525)], outline=ink_color, width=3) # Glasses R
    d1.line([(275, 518), (285, 518)], fill=ink_color, width=3)
    d1.line([(280, 560), (280, 720)], fill=ink_color, width=6) # Body
    d1.line([(280, 600), (200, 690)], fill=ink_color, width=5) # Arm to cup
    d1.line([(280, 600), (350, 680)], fill=ink_color, width=5) # Arm to paper
    # Label "前额叶 · 理智脑 CEO"
    d1.rectangle([(160, 420), (400, 465)], outline=ink_color, width=3)
    # Brain outline
    d1.arc([(150, 200), (750, 700)], start=160, end=380, fill=ink_color, width=4)
    
    # Berserk Security Guard (Right side, helmet, alarm bell, lightning shock)
    d1.ellipse([(620, 520), (700, 600)], outline=accent_red, width=6) # Guard head
    d1.arc([(610, 500), (710, 550)], start=180, end=360, fill=ink_color, width=6) # Helmet
    d1.line([(660, 600), (660, 780)], fill=accent_red, width=7) # Body
    # Raised arms pulling alarm lever
    d1.line([(660, 650), (750, 580)], fill=accent_red, width=6)
    d1.line([(750, 580), (780, 520)], fill=accent_red, width=6)
    # Alarm lever & Bell
    d1.rectangle([(770, 460), (840, 560)], outline=accent_red, width=5)
    d1.line([(800, 560), (760, 620)], fill=accent_red, width=7) # Lever pulled
    # Shockwaves & Alarm rings
    d1.arc([(740, 380), (870, 480)], start=200, end=340, fill=accent_red, width=5)
    d1.arc([(720, 360), (890, 480)], start=200, end=340, fill=accent_red, width=4)
    # Lightning bolt connecting guard to CEO chair
    d1.line([(640, 680), (560, 710)], fill=accent_red, width=6)
    d1.line([(560, 710), (580, 730)], fill=accent_red, width=6)
    d1.line([(580, 730), (500, 760)], fill=accent_red, width=6)
    
    # Save scene 1
    p1 = INPUTS_DIR / "scene1_anger.png"
    im1.save(p1)
    print(f"  Created Scene 1 (CEO vs Berserk Guard) -> {p1}")

    # -------------------------------------------------------------
    # Illustration 2: 杏仁核劫持，更衣室大铁链焊死 (Scene 2)
    # -------------------------------------------------------------
    im2 = Image.new("RGB", (900, 1200), bg_color)
    d2 = ImageDraw.Draw(im2)
    
    # Giant Locker / Door frame
    d2.rectangle([(250, 180), (650, 1020)], outline=ink_color, width=8)
    d2.line([(250, 180), (650, 180)], fill=ink_color, width=12) # Door top beam
    d2.line([(250, 1020), (650, 1020)], fill=ink_color, width=12) # Door threshold
    
    # Prison / Locker Window
    d2.rectangle([(340, 260), (560, 480)], outline=ink_color, width=6)
    d2.line([(395, 260), (395, 480)], fill=ink_color, width=5) # Bar 1
    d2.line([(450, 260), (450, 480)], fill=ink_color, width=5) # Bar 2
    d2.line([(505, 260), (505, 480)], fill=ink_color, width=5) # Bar 3
    
    # Trapped CEO face inside window (Knocking hands)
    d2.ellipse([(420, 320), (480, 380)], outline=ink_color, width=4)
    d2.line([(380, 410), (420, 400)], fill=ink_color, width=4) # Knocking Hand L
    d2.line([(520, 410), (480, 400)], fill=ink_color, width=4) # Knocking Hand R
    
    # Heavy Cross Chains & Giant Padlock
    # Diagonal chain 1
    d2.line([(230, 350), (670, 850)], fill=ink_color, width=14)
    # Diagonal chain 2
    d2.line([(230, 850), (670, 350)], fill=ink_color, width=14)
    
    # Padlock in center
    d2.arc([(400, 520), (500, 620)], start=180, end=360, fill=accent_red, width=10) # Lock shackle
    d2.rectangle([(380, 600), (520, 720)], fill=bg_color, outline=accent_red, width=8) # Lock body
    d2.ellipse([(440, 640), (460, 660)], fill=accent_red) # Keyhole
    d2.polygon([(445, 655), (455, 655), (452, 685), (448, 685)], fill=accent_red)
    
    # Sign on door: "DECISION LOCKED - AMYGDALA HIJACK"
    d2.rectangle([(290, 770), (610, 840)], fill=bg_color, outline=accent_red, width=4)
    # Disconnect waves
    d2.line([(120, 600), (220, 600)], fill=accent_red, width=4)
    d2.line([(150, 560), (190, 640)], fill=accent_red, width=4)
    d2.line([(680, 600), (780, 600)], fill=accent_red, width=4)
    d2.line([(710, 560), (750, 640)], fill=accent_red, width=4)
    
    p2 = INPUTS_DIR / "scene2_hijack.png"
    im2.save(p2)
    print(f"  Created Scene 2 (Locked Door & Chain Hijack) -> {p2}")

    # -------------------------------------------------------------
    # Illustration 3: 20秒沙漏倒计时、深呼吸波纹与解锁金钥匙 (Scene 3)
    # -------------------------------------------------------------
    im3 = Image.new("RGB", (900, 1200), bg_color)
    d3 = ImageDraw.Draw(im3)
    
    # Elegant 20s Hourglass in center top
    # Hourglass top and bottom plates
    d3.line([(320, 220), (580, 220)], fill=ink_color, width=10)
    d3.line([(320, 540), (580, 540)], fill=ink_color, width=10)
    # Glass curves
    d3.line([(340, 220), (440, 380)], fill=ink_color, width=6)
    d3.line([(560, 220), (460, 380)], fill=ink_color, width=6)
    d3.line([(440, 380), (340, 540)], fill=ink_color, width=6)
    d3.line([(460, 380), (560, 540)], fill=ink_color, width=6)
    # Sand flowing & Sand heap
    d3.polygon([(360, 240), (540, 240), (450, 370)], fill=accent_gold) # Top sand
    d3.line([(450, 370), (450, 480)], fill=accent_gold, width=4) # Flow
    d3.polygon([(370, 530), (530, 530), (450, 480)], fill=accent_gold) # Bottom heap
    # Label "20s" inside circle
    d3.ellipse([(600, 330), (700, 430)], outline=ink_color, width=5)
    
    # 3 Deep Breathing Waves (Flowing soothing water/air currents)
    d3.arc([(180, 600), (420, 700)], start=180, end=360, fill=ink_color, width=5)
    d3.arc([(420, 600), (660, 700)], start=0, end=180, fill=ink_color, width=5)
    d3.arc([(220, 650), (460, 750)], start=180, end=360, fill=ink_color, width=4)
    d3.arc([(460, 650), (700, 750)], start=0, end=180, fill=ink_color, width=4)
    d3.arc([(260, 700), (500, 800)], start=180, end=360, fill=ink_color, width=4)
    d3.arc([(500, 700), (740, 800)], start=0, end=180, fill=ink_color, width=4)
    
    # Golden Key unlocking padlock (Bottom right)
    # Key ring
    d3.ellipse([(380, 860), (460, 940)], outline=accent_gold, width=8)
    # Key blade
    d3.line([(460, 900), (650, 900)], fill=accent_gold, width=10)
    # Key teeth
    d3.line([(580, 900), (580, 950)], fill=accent_gold, width=8)
    d3.line([(630, 900), (630, 960)], fill=accent_gold, width=8)
    # Click! Sparks around key
    d3.line([(660, 880), (680, 860)], fill=ink_color, width=3)
    d3.line([(670, 900), (700, 900)], fill=ink_color, width=3)
    d3.line([(660, 920), (680, 940)], fill=ink_color, width=3)
    
    p3 = INPUTS_DIR / "scene3_solution.png"
    im3.save(p3)
    print(f"  Created Scene 3 (20s Hourglass, Breath & Golden Key) -> {p3}\n")
    
    # Create cover
    cover_p = INPUTS_DIR / "cover.png"
    im1_resized = im1.resize((1080, 1920), Image.Resampling.LANCZOS)
    im1_resized.save(cover_p)
    print(f"  Created Cover -> {cover_p}")

def build_job_manifest(durations):
    print(">>> 3. Generating compliant job.json with obsidian black capsule subtitles...")
    
    manifest = {
        "version": 1,
        "runtime_fixture": True,
        "title": "为什么越生气越容易做错决定",
        "canvas": {
            "width": 1080,
            "height": 1920,
            "fps": 30
        },
        "paper": "#FBF9F1",
        "cover": {
            "source": "inputs/cover.png",
            "seconds": 1.0
        },
        "hand": {
            "preset": "teacher-pen",
            "scale": 0.35
        },
        "audio": {
            "pace": 1.0,
            "trim_silence": False,
            "sentence_pause_seconds": 0.25,
            "page_pause_seconds": 0.40,
            "end_hold_seconds": 1.0
        },
        # Obsidian Black Semi-Transparent Capsule Subtitles (WCAG 18.2:1 AAA Contrast)
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
            # Page 1: Act 1 (Beats 01 & 02)
            {
                "visual_groups": [
                    {
                        "start_beat": "beat_01",
                        "end_beat": "beat_02",
                        "lead": 0.40,
                        "hold": 0.80,
                        "actions": [
                            {
                                "type": "illustration",
                                "parts": [{"id": "p1_fig", "polygon": [[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0]]}],
                                "source": "inputs/scene1_anger.png",
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
                        "id": "beat_01",
                        "text": BEATS_CONFIG[0]["text"],
                        "audio": "inputs/beat_01.wav",
                        "caption_cues": [
                            {"text": BEATS_CONFIG[0]["cues"][0]["text"], "start": BEATS_CONFIG[0]["cues"][0]["start"], "end": BEATS_CONFIG[0]["cues"][0]["end"]},
                            {"text": BEATS_CONFIG[0]["cues"][1]["text"], "start": BEATS_CONFIG[0]["cues"][1]["start"], "end": BEATS_CONFIG[0]["cues"][1]["end"]},
                            {"text": BEATS_CONFIG[0]["cues"][2]["text"], "start": BEATS_CONFIG[0]["cues"][2]["start"], "end": round(durations["beat_01"] - 0.02, 3)}
                        ]
                    },
                    {
                        "id": "beat_02",
                        "text": BEATS_CONFIG[1]["text"],
                        "audio": "inputs/beat_02.wav",
                        "caption_cues": [
                            {"text": BEATS_CONFIG[1]["cues"][0]["text"], "start": BEATS_CONFIG[1]["cues"][0]["start"], "end": BEATS_CONFIG[1]["cues"][0]["end"]},
                            {"text": BEATS_CONFIG[1]["cues"][1]["text"], "start": BEATS_CONFIG[1]["cues"][1]["start"], "end": BEATS_CONFIG[1]["cues"][1]["end"]},
                            {"text": BEATS_CONFIG[1]["cues"][2]["text"], "start": BEATS_CONFIG[1]["cues"][2]["start"], "end": round(durations["beat_02"] - 0.02, 3)}
                        ]
                    }
                ]
            },
            # Page 2: Act 2 (Beats 03, 04, 05)
            {
                "transition": {"type": "cut"},
                "visual_groups": [
                    {
                        "start_beat": "beat_03",
                        "end_beat": "beat_05",
                        "lead": 0.40,
                        "hold": 0.80,
                        "actions": [
                            {
                                "type": "illustration",
                                "parts": [{"id": "p2_fig", "polygon": [[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0]]}],
                                "source": "inputs/scene2_hijack.png",
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
                        "id": "beat_03",
                        "text": BEATS_CONFIG[2]["text"],
                        "audio": "inputs/beat_03.wav",
                        "caption_cues": [
                            {"text": BEATS_CONFIG[2]["cues"][0]["text"], "start": BEATS_CONFIG[2]["cues"][0]["start"], "end": BEATS_CONFIG[2]["cues"][0]["end"]},
                            {"text": BEATS_CONFIG[2]["cues"][1]["text"], "start": BEATS_CONFIG[2]["cues"][1]["start"], "end": round(durations["beat_03"] - 0.02, 3)}
                        ]
                    },
                    {
                        "id": "beat_04",
                        "text": BEATS_CONFIG[3]["text"],
                        "audio": "inputs/beat_04.wav",
                        "caption_cues": [
                            {"text": BEATS_CONFIG[3]["cues"][0]["text"], "start": BEATS_CONFIG[3]["cues"][0]["start"], "end": BEATS_CONFIG[3]["cues"][0]["end"]},
                            {"text": BEATS_CONFIG[3]["cues"][1]["text"], "start": BEATS_CONFIG[3]["cues"][1]["start"], "end": round(durations["beat_04"] - 0.02, 3)}
                        ]
                    },
                    {
                        "id": "beat_05",
                        "text": BEATS_CONFIG[4]["text"],
                        "audio": "inputs/beat_05.wav",
                        "caption_cues": [
                            {"text": BEATS_CONFIG[4]["cues"][0]["text"], "start": BEATS_CONFIG[4]["cues"][0]["start"], "end": BEATS_CONFIG[4]["cues"][0]["end"]},
                            {"text": BEATS_CONFIG[4]["cues"][1]["text"], "start": BEATS_CONFIG[4]["cues"][1]["start"], "end": BEATS_CONFIG[4]["cues"][1]["end"]},
                            {"text": BEATS_CONFIG[4]["cues"][2]["text"], "start": BEATS_CONFIG[4]["cues"][2]["start"], "end": round(durations["beat_05"] - 0.02, 3)}
                        ]
                    }
                ]
            },
            # Page 3: Act 3 (Beats 06 & 07)
            {
                "transition": {"type": "cut"},
                "visual_groups": [
                    {
                        "start_beat": "beat_06",
                        "end_beat": "beat_07",
                        "lead": 0.40,
                        "hold": 0.80,
                        "actions": [
                            {
                                "type": "illustration",
                                "parts": [{"id": "p3_fig", "polygon": [[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0]]}],
                                "source": "inputs/scene3_solution.png",
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
                        "id": "beat_06",
                        "text": BEATS_CONFIG[5]["text"],
                        "audio": "inputs/beat_06.wav",
                        "caption_cues": [
                            {"text": BEATS_CONFIG[5]["cues"][0]["text"], "start": BEATS_CONFIG[5]["cues"][0]["start"], "end": BEATS_CONFIG[5]["cues"][0]["end"]},
                            {"text": BEATS_CONFIG[5]["cues"][1]["text"], "start": BEATS_CONFIG[5]["cues"][1]["start"], "end": round(durations["beat_06"] - 0.02, 3)}
                        ]
                    },
                    {
                        "id": "beat_07",
                        "text": BEATS_CONFIG[6]["text"],
                        "audio": "inputs/beat_07.wav",
                        "caption_cues": [
                            {"text": BEATS_CONFIG[6]["cues"][0]["text"], "start": BEATS_CONFIG[6]["cues"][0]["start"], "end": BEATS_CONFIG[6]["cues"][0]["end"]},
                            {"text": BEATS_CONFIG[6]["cues"][1]["text"], "start": BEATS_CONFIG[6]["cues"][1]["start"], "end": round(durations["beat_07"] - 0.02, 3)}
                        ]
                    }
                ]
            }
        ]
    }
    
    job_file = PROJECT_DIR / "job.json"
    job_file.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  Successfully wrote job manifest -> {job_file}\n")
    return job_file

if __name__ == "__main__":
    durs = synthesize_voices()
    create_visual_metaphor_illustrations()
    build_job_manifest(durs)
    print("Project preparation completed successfully!")
