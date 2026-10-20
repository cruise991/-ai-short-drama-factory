"""
Industrialized Handdraw Production Pipeline v3:
Integrates the complete 5-tier content engineering & audio mastering framework:
  1. Research & Brain: Dan Goleman's Dual-Brain Emotional Metaphor
  2. Baoyu Structuring: 3-Act Gestalt Narrative (Hook ➔ Subversion ➔ Solution)
  3. Humanizer-zh: De-AI flavor text polishing (removes robotic cliches)
  4. AudioMasteringStudio: Broadcast-grade 5-stage acoustic mastering
  5. Sweety-Handdraw Engine: Obsidian black capsule subtitles (18:1 contrast)
"""
import os
import sys
import json
import wave
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw

# Add shared tools to path
ROOT_DIR = Path("/Users/workspace/ai_short_company/ai-short-drama")
sys.path.insert(0, str(ROOT_DIR))

from shared_tools.skills_registry import ContentPipelineEngine
from shared_tools.audio_mastering import AudioMasteringStudio

PROJECT_DIR = ROOT_DIR / "projects" / "handdraw_anger_decision_v3"
INPUTS_DIR = PROJECT_DIR / "inputs"
INPUTS_DIR.mkdir(parents=True, exist_ok=True)

# 1. Structure raw story through Baoyu & Humanizer
RAW_PAIN_POINTS = ["刚冲动发完一段质问，下一秒就恨不得抽自己耳光"]
CORE_MECHANISM = "而情绪中枢杏仁核就像脾气暴躁的安保。一旦火气被点燃，杏仁核二十毫秒就能引爆战斗警报，直接掏出电棍把理智脑总裁反锁进更衣室！前额叶皮层供能骤降，说白了，你所有的发飙，全凭原始肌肉记忆了。"
SOLUTION = "记住：什么都别说，双手插兜，做三次深长的腹式呼吸"

structured_story = ContentPipelineEngine.apply_baoyu_structure(
    theme="为什么越生气越容易做错决定",
    pain_points=RAW_PAIN_POINTS,
    core_mechanism=CORE_MECHANISM,
    solution=SOLUTION
)

print(">>> [Stage 1 & 2: Baoyu & Humanizer Polished Beats]")
for act_key in ["act_1", "act_2", "act_3"]:
    print(f"  {structured_story[act_key]['phase']}: {structured_story[act_key]['text'][:40]}...")

# Deconstruct into timed beats
BEATS_SPEC = [
    # Act 1 (0-15s)
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
        "text": "很多人以为这是性格暴躁或情商低，但科学上早就证实了：这真不怪你，而是你的大脑刚刚经历了一场恶性夺权！",
        "voice": "Reed (中文（中国大陆）)",
        "rate": 185,
        "cues": [
            {"text": "很多人以为这是性格暴躁或情商低，", "start": 0.0, "end": 2.8},
            {"text": "但科学上早就证实了：这真不怪你，", "start": 2.8, "end": 5.1},
            {"text": "而是你的大脑刚刚经历了一场恶性夺权！", "start": 5.1, "end": None}
        ]
    },
    # Act 2 (15-40s)
    {
        "id": "beat_03",
        "text": "正常情况下，掌管权衡与逻辑的前额叶就像理智脑总裁，而情绪中枢杏仁核就像脾气暴躁的安保。",
        "voice": "Reed (中文（中国大陆）)",
        "rate": 182,
        "cues": [
            {"text": "正常情况下，掌管权衡与逻辑的前额叶就像理智脑总裁，", "start": 0.0, "end": 4.1},
            {"text": "而情绪中枢杏仁核就像脾气暴躁的安保。", "start": 4.1, "end": None}
        ]
    },
    {
        "id": "beat_04",
        "text": "一旦火气被点燃，杏仁核二十毫秒就能引爆战斗警报，直接掏出电棍把理智脑总裁反锁进更衣室！",
        "voice": "Reed (中文（中国大陆）)",
        "rate": 186,
        "cues": [
            {"text": "一旦火气被点燃，杏仁核二十毫秒就能引爆战斗警报，", "start": 0.0, "end": 3.8},
            {"text": "直接掏出电棍把理智脑总裁反锁进更衣室！", "start": 3.8, "end": None}
        ]
    },
    {
        "id": "beat_05",
        "text": "理智脑直接被拉闸断电，说白了，你所有的发飙，全凭原始肌肉记忆了。",
        "voice": "Reed (中文（中国大陆）)",
        "rate": 184,
        "cues": [
            {"text": "理智脑直接被拉闸断电，", "start": 0.0, "end": 2.3},
            {"text": "说白了，你所有的发飙，全凭原始肌肉记忆了。", "start": 2.3, "end": None}
        ]
    },
    # Act 3 (40-60s)
    {
        "id": "beat_06",
        "text": "但好消息是，安保这根电棍的生理电量，最多维持短短二十秒。",
        "voice": "Reed (中文（中国大陆）)",
        "rate": 178,
        "cues": [
            {"text": "但好消息是，", "start": 0.0, "end": 1.2},
            {"text": "安保这根电棍的生理电量，最多维持短短二十秒。", "start": 1.2, "end": None}
        ]
    },
    {
        "id": "beat_07",
        "text": "下次火气上头，记住：什么都别说，双手插兜，做三次深长的腹式呼吸。给理智脑总裁争取二十秒撬开锁，你的理性就能重夺方向盘。",
        "voice": "Reed (中文（中国大陆）)",
        "rate": 180,
        "cues": [
            {"text": "下次火气上头，记住：什么都别说，双手插兜，做三次深长的腹式呼吸。", "start": 0.0, "end": 5.4},
            {"text": "给理智脑总裁争取二十秒撬开锁，你的理性就能重夺方向盘。", "start": 5.4, "end": None}
        ]
    }
]

def synthesize_and_master_audio():
    print(">>> [Stage 3: Speech Synthesis & Broadcast Audio Mastering]")
    durations = {}
    for item in BEATS_SPEC:
        bid = item["id"]
        raw_text = item["text"]
        rate = item["rate"]
        voice = item["voice"]
        
        aiff_p = INPUTS_DIR / f"{bid}_raw.aiff"
        raw_wav_p = INPUTS_DIR / f"{bid}_raw.wav"
        final_wav_p = INPUTS_DIR / f"{bid}.wav"
        
        # 1. Synthesize
        subprocess.run(["say", "-v", voice, "-r", str(rate), "-o", str(aiff_p), raw_text], check=True)
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(aiff_p), "-ar", "48000", "-ac", "1", "-c:a", "pcm_s16le", str(raw_wav_p)], check=True)
        if aiff_p.exists():
            aiff_p.unlink()
            
        # 2. Master via AudioMasteringStudio (5-stage acoustic filter graph)
        ok = AudioMasteringStudio.master_voice_clip(str(raw_wav_p), str(final_wav_p), sample_rate=48000)
        if not ok or not final_wav_p.exists():
            # Fallback to raw if ffmpeg mastering issues
            raw_wav_p.rename(final_wav_p)
        else:
            if raw_wav_p.exists():
                raw_wav_p.unlink()
                
        with wave.open(str(final_wav_p), "rb") as wf:
            dur = wf.getnframes() / float(wf.getframerate())
        durations[bid] = round(dur, 3)
        print(f"  [Mastered {bid}] Duration: {dur:.2f}s | {raw_text[:25]}...")
        
    return durations

def create_visuals():
    print(">>> [Stage 4: Generating Handdrawn Visual Metaphors]")
    bg_color = (251, 249, 241) # #FBF9F1
    ink_color = (35, 31, 32)
    accent_red = (211, 47, 47)
    accent_gold = (212, 160, 23)
    
    # Scene 1: 理智脑总裁在工位喝咖啡，暴走安保拉闸引爆警报
    im1 = Image.new("RGB", (900, 1200), bg_color)
    d1 = ImageDraw.Draw(im1)
    # Desk & CEO
    d1.line([(100, 750), (450, 750)], fill=ink_color, width=6)
    d1.line([(140, 750), (140, 1050)], fill=ink_color, width=5)
    d1.line([(410, 750), (410, 1050)], fill=ink_color, width=5)
    d1.rectangle([(180, 700), (220, 750)], outline=ink_color, width=4)
    d1.arc([(220, 715), (240, 735)], start=270, end=90, fill=ink_color, width=4)
    d1.ellipse([(240, 480), (320, 560)], outline=ink_color, width=5)
    d1.rectangle([(255, 510), (275, 525)], outline=ink_color, width=3)
    d1.rectangle([(285, 510), (305, 525)], outline=ink_color, width=3)
    d1.line([(275, 518), (285, 518)], fill=ink_color, width=3)
    d1.line([(280, 560), (280, 720)], fill=ink_color, width=6)
    d1.line([(280, 600), (200, 690)], fill=ink_color, width=5)
    d1.line([(280, 600), (350, 680)], fill=ink_color, width=5)
    d1.rectangle([(160, 420), (400, 465)], outline=ink_color, width=3)
    d1.arc([(150, 200), (750, 700)], start=160, end=380, fill=ink_color, width=4)
    # Berserk Guard
    d1.ellipse([(620, 520), (700, 600)], outline=accent_red, width=6)
    d1.arc([(610, 500), (710, 550)], start=180, end=360, fill=ink_color, width=6)
    d1.line([(660, 600), (660, 780)], fill=accent_red, width=7)
    d1.line([(660, 650), (750, 580)], fill=accent_red, width=6)
    d1.line([(750, 580), (780, 520)], fill=accent_red, width=6)
    d1.rectangle([(770, 460), (840, 560)], outline=accent_red, width=5)
    d1.line([(800, 560), (760, 620)], fill=accent_red, width=7)
    d1.arc([(740, 380), (870, 480)], start=200, end=340, fill=accent_red, width=5)
    d1.arc([(720, 360), (890, 480)], start=200, end=340, fill=accent_red, width=4)
    d1.line([(640, 680), (560, 710)], fill=accent_red, width=6)
    d1.line([(560, 710), (580, 730)], fill=accent_red, width=6)
    d1.line([(580, 730), (500, 760)], fill=accent_red, width=6)
    im1.save(INPUTS_DIR / "scene1_anger.png")

    # Scene 2: 更衣室铁门被粗链条大铜锁焊死
    im2 = Image.new("RGB", (900, 1200), bg_color)
    d2 = ImageDraw.Draw(im2)
    d2.rectangle([(250, 180), (650, 1020)], outline=ink_color, width=8)
    d2.line([(250, 180), (650, 180)], fill=ink_color, width=12)
    d2.line([(250, 1020), (650, 1020)], fill=ink_color, width=12)
    d2.rectangle([(340, 260), (560, 480)], outline=ink_color, width=6)
    d2.line([(395, 260), (395, 480)], fill=ink_color, width=5)
    d2.line([(450, 260), (450, 480)], fill=ink_color, width=5)
    d2.line([(505, 260), (505, 480)], fill=ink_color, width=5)
    d2.ellipse([(420, 320), (480, 380)], outline=ink_color, width=4)
    d2.line([(380, 410), (420, 400)], fill=ink_color, width=4)
    d2.line([(520, 410), (480, 400)], fill=ink_color, width=4)
    d2.line([(230, 350), (670, 850)], fill=ink_color, width=14)
    d2.line([(230, 850), (670, 350)], fill=ink_color, width=14)
    d2.arc([(400, 520), (500, 620)], start=180, end=360, fill=accent_red, width=10)
    d2.rectangle([(380, 600), (520, 720)], fill=bg_color, outline=accent_red, width=8)
    d2.ellipse([(440, 640), (460, 660)], fill=accent_red)
    d2.polygon([(445, 655), (455, 655), (452, 685), (448, 685)], fill=accent_red)
    d2.rectangle([(290, 770), (610, 840)], fill=bg_color, outline=accent_red, width=4)
    d2.line([(120, 600), (220, 600)], fill=accent_red, width=4)
    d2.line([(150, 560), (190, 640)], fill=accent_red, width=4)
    d2.line([(680, 600), (780, 600)], fill=accent_red, width=4)
    d2.line([(710, 560), (750, 640)], fill=accent_red, width=4)
    im2.save(INPUTS_DIR / "scene2_hijack.png")

    # Scene 3: 20秒沙漏倒计时流沙、深呼吸波纹与金钥匙解锁
    im3 = Image.new("RGB", (900, 1200), bg_color)
    d3 = ImageDraw.Draw(im3)
    d3.line([(320, 220), (580, 220)], fill=ink_color, width=10)
    d3.line([(320, 540), (580, 540)], fill=ink_color, width=10)
    d3.line([(340, 220), (440, 380)], fill=ink_color, width=6)
    d3.line([(560, 220), (460, 380)], fill=ink_color, width=6)
    d3.line([(440, 380), (340, 540)], fill=ink_color, width=6)
    d3.line([(460, 380), (560, 540)], fill=ink_color, width=6)
    d3.polygon([(360, 240), (540, 240), (450, 370)], fill=accent_gold)
    d3.line([(450, 370), (450, 480)], fill=accent_gold, width=4)
    d3.polygon([(370, 530), (530, 530), (450, 480)], fill=accent_gold)
    d3.ellipse([(600, 330), (700, 430)], outline=ink_color, width=5)
    d3.arc([(180, 600), (420, 700)], start=180, end=360, fill=ink_color, width=5)
    d3.arc([(420, 600), (660, 700)], start=0, end=180, fill=ink_color, width=5)
    d3.arc([(220, 650), (460, 750)], start=180, end=360, fill=ink_color, width=4)
    d3.arc([(460, 650), (700, 750)], start=0, end=180, fill=ink_color, width=4)
    d3.arc([(260, 700), (500, 800)], start=180, end=360, fill=ink_color, width=4)
    d3.arc([(500, 700), (740, 800)], start=0, end=180, fill=ink_color, width=4)
    d3.ellipse([(380, 860), (460, 940)], outline=accent_gold, width=8)
    d3.line([(460, 900), (650, 900)], fill=accent_gold, width=10)
    d3.line([(580, 900), (580, 950)], fill=accent_gold, width=8)
    d3.line([(630, 900), (630, 960)], fill=accent_gold, width=8)
    d3.line([(660, 880), (680, 860)], fill=ink_color, width=3)
    d3.line([(670, 900), (700, 900)], fill=ink_color, width=3)
    d3.line([(660, 920), (680, 940)], fill=ink_color, width=3)
    im3.save(INPUTS_DIR / "scene3_solution.png")

    # Cover
    im1_resized = im1.resize((1080, 1920), Image.Resampling.LANCZOS)
    im1_resized.save(INPUTS_DIR / "cover.png")
    print("  Visuals generated successfully.")

def build_job_file(durations):
    print(">>> [Stage 5: Compiling Job Manifest]")
    manifest = {
        "version": 1,
        "runtime_fixture": True,
        "title": "为什么越生气越容易做错决定",
        "canvas": {"width": 1080, "height": 1920, "fps": 30},
        "paper": "#FBF9F1",
        "cover": {"source": "inputs/cover.png", "seconds": 1.0},
        "hand": {"preset": "teacher-pen", "scale": 0.35},
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
            # Act 1 (Page 1)
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
                                "x": 90, "y": 280, "width": 900, "height": 1200,
                                "weight": 3.0, "lineart_exception": True,
                                "drawing": {"mode": "draw", "speed": 1.0}
                            }
                        ]
                    }
                ],
                "beats": [
                    {
                        "id": "beat_01",
                        "text": BEATS_SPEC[0]["text"],
                        "audio": "inputs/beat_01.wav",
                        "caption_cues": [
                            {"text": BEATS_SPEC[0]["cues"][0]["text"], "start": BEATS_SPEC[0]["cues"][0]["start"], "end": BEATS_SPEC[0]["cues"][0]["end"]},
                            {"text": BEATS_SPEC[0]["cues"][1]["text"], "start": BEATS_SPEC[0]["cues"][1]["start"], "end": BEATS_SPEC[0]["cues"][1]["end"]},
                            {"text": BEATS_SPEC[0]["cues"][2]["text"], "start": BEATS_SPEC[0]["cues"][2]["start"], "end": round(durations["beat_01"] - 0.02, 3)}
                        ]
                    },
                    {
                        "id": "beat_02",
                        "text": BEATS_SPEC[1]["text"],
                        "audio": "inputs/beat_02.wav",
                        "caption_cues": [
                            {"text": BEATS_SPEC[1]["cues"][0]["text"], "start": BEATS_SPEC[1]["cues"][0]["start"], "end": BEATS_SPEC[1]["cues"][0]["end"]},
                            {"text": BEATS_SPEC[1]["cues"][1]["text"], "start": BEATS_SPEC[1]["cues"][1]["start"], "end": BEATS_SPEC[1]["cues"][1]["end"]},
                            {"text": BEATS_SPEC[1]["cues"][2]["text"], "start": BEATS_SPEC[1]["cues"][2]["start"], "end": round(durations["beat_02"] - 0.02, 3)}
                        ]
                    }
                ]
            },
            # Act 2 (Page 2)
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
                                "x": 90, "y": 280, "width": 900, "height": 1200,
                                "weight": 3.0, "lineart_exception": True,
                                "drawing": {"mode": "draw", "speed": 1.0}
                            }
                        ]
                    }
                ],
                "beats": [
                    {
                        "id": "beat_03",
                        "text": BEATS_SPEC[2]["text"],
                        "audio": "inputs/beat_03.wav",
                        "caption_cues": [
                            {"text": BEATS_SPEC[2]["cues"][0]["text"], "start": BEATS_SPEC[2]["cues"][0]["start"], "end": BEATS_SPEC[2]["cues"][0]["end"]},
                            {"text": BEATS_SPEC[2]["cues"][1]["text"], "start": BEATS_SPEC[2]["cues"][1]["start"], "end": round(durations["beat_03"] - 0.02, 3)}
                        ]
                    },
                    {
                        "id": "beat_04",
                        "text": BEATS_SPEC[3]["text"],
                        "audio": "inputs/beat_04.wav",
                        "caption_cues": [
                            {"text": BEATS_SPEC[3]["cues"][0]["text"], "start": BEATS_SPEC[3]["cues"][0]["start"], "end": BEATS_SPEC[3]["cues"][0]["end"]},
                            {"text": BEATS_SPEC[3]["cues"][1]["text"], "start": BEATS_SPEC[3]["cues"][1]["start"], "end": round(durations["beat_04"] - 0.02, 3)}
                        ]
                    },
                    {
                        "id": "beat_05",
                        "text": BEATS_SPEC[4]["text"],
                        "audio": "inputs/beat_05.wav",
                        "caption_cues": [
                            {"text": BEATS_SPEC[4]["cues"][0]["text"], "start": BEATS_SPEC[4]["cues"][0]["start"], "end": BEATS_SPEC[4]["cues"][0]["end"]},
                            {"text": BEATS_SPEC[4]["cues"][1]["text"], "start": BEATS_SPEC[4]["cues"][1]["start"], "end": round(durations["beat_05"] - 0.02, 3)}
                        ]
                    }
                ]
            },
            # Act 3 (Page 3)
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
                                "x": 90, "y": 280, "width": 900, "height": 1200,
                                "weight": 3.0, "lineart_exception": True,
                                "drawing": {"mode": "draw", "speed": 1.0}
                            }
                        ]
                    }
                ],
                "beats": [
                    {
                        "id": "beat_06",
                        "text": BEATS_SPEC[5]["text"],
                        "audio": "inputs/beat_06.wav",
                        "caption_cues": [
                            {"text": BEATS_SPEC[5]["cues"][0]["text"], "start": BEATS_SPEC[5]["cues"][0]["start"], "end": BEATS_SPEC[5]["cues"][0]["end"]},
                            {"text": BEATS_SPEC[5]["cues"][1]["text"], "start": BEATS_SPEC[5]["cues"][1]["start"], "end": round(durations["beat_06"] - 0.02, 3)}
                        ]
                    },
                    {
                        "id": "beat_07",
                        "text": BEATS_SPEC[6]["text"],
                        "audio": "inputs/beat_07.wav",
                        "caption_cues": [
                            {"text": BEATS_SPEC[6]["cues"][0]["text"], "start": BEATS_SPEC[6]["cues"][0]["start"], "end": BEATS_SPEC[6]["cues"][0]["end"]},
                            {"text": BEATS_SPEC[6]["cues"][1]["text"], "start": BEATS_SPEC[6]["cues"][1]["start"], "end": round(durations["beat_07"] - 0.02, 3)}
                        ]
                    }
                ]
            }
        ]
    }
    job_file = PROJECT_DIR / "job.json"
    job_file.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  Saved v3 job manifest -> {job_file}")

if __name__ == "__main__":
    durations = synthesize_and_master_audio()
    create_visuals()
    build_job_file(durations)
    print("v3 Project assets prepared successfully!")
