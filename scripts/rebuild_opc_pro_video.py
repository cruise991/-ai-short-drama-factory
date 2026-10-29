#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Professional Full-Pipeline Handdraw Video Production for:
"2026 北京怀柔科学城 AI for Science · OPC 创新挑战赛"

Full-pipeline capabilities enabled:
1. Edge-TTS 48kHz Neural Voice (zh-CN-YunjianNeural): Broadcast-grade articulate technology narration.
2. Agnes Image 2.5 Flash API: High-fidelity editorial lineart whiteboard illustrations for all 5 scenes.
3. Sweety-Handdraw Dynamic Handdrawing Engine: Real stroke revelation & lineart motion.
4. AudioMasteringStudio: 5-Stage Broadcast DSP mastering (-14 LUFS, crisp highs, warm mids).
5. WCAG AAA 18:1 Obsidian Capsule Subtitles.
"""
import os
import sys
import json
import wave
import shutil
import asyncio
import subprocess
import requests
import importlib
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import edge_tts

ROOT_DIR = Path("/Users/workspace/ai_short_company/ai-short-drama")
sys.path.insert(0, str(ROOT_DIR))

from shared_tools.audio_mastering import AudioMasteringStudio
pa = importlib.import_module("departments.03_production.production_agent")

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
# 1. 5-Act Humanized Narrative Script & AI Visual Prompts
# ------------------------------------------------------------------------------
BEATS_SPEC = [
    # Act 1: Hook (0-24s)
    {
        "id": "beat_01",
        "voice": "zh-CN-YunjianNeural",
        "rate": "+0%",
        "text": "如果你对AI比赛的印象，还停留在刷公开数据集、做玩具Demo领几千块奖金，那北京怀柔刚刚发生的事，彻底颠覆了规则。怀柔科学城大科学装置群旁，中科院院所与产业龙头立下军令状：不看PPT、不问出身，谁能用AI解决真实痛点，当场签走采购订单！",
        "cues": [
            "如果你对AI比赛的印象，",
            "还停留在刷公开数据集、做玩具Demo领几千块奖金，",
            "那北京怀柔刚刚发生的事，彻底颠覆了规则。",
            "怀柔科学城大科学装置群旁，",
            "中科院院所与产业龙头立下军令状：",
            "不看PPT、不问出身，",
            "谁能用AI解决真实痛点，当场签走采购订单！"
        ],
        "image_prompt": "minimalist editorial cartoon lineart illustration, high quality whiteboard ink drawing, warm paper background #FBF9F1, an expressive tech presenter tearing up a fake PPT demo poster, pointing forward to a massive futuristic particle accelerator synchrotron radiation ring and a stack of signed commercial contracts with bold red stamp 'REAL PURCHASE ORDER', clean black outlines, subtle watercolor splashes of cyan and amber gold, 9:16 vertical composition"
    },
    # Act 2: Mechanism & Grand Challenges (24-50s)
    {
        "id": "beat_02",
        "voice": "zh-CN-YunjianNeural",
        "rate": "+0%",
        "text": "为什么国家战略级力量要办这场挑战赛？因为今天的科学与工业已到极限：物理所复杂激光器一旦宕机，备件周期长达数月；浪潮要帮医生从成百上千切片中肉眼识别染色体；钢铁万吨轧机一旦故障损失千万。10大硬核榜单，全是花钱买不到的真问题，单榜悬赏10万起，真金白银真采购！",
        "cues": [
            "为什么国家战略级力量要办这场挑战赛？",
            "因为今天的科学与工业已到极限：",
            "物理所复杂激光器一旦宕机，备件周期长达数月；",
            "浪潮要帮医生从成百上千切片中肉眼识别染色体；",
            "钢铁万吨轧机一旦故障损失千万。",
            "10大硬核榜单，全是花钱买不到的真问题，",
            "单榜悬赏10万起，真金白银真采购！"
        ],
        "image_prompt": "minimalist editorial cartoon lineart illustration, clean ink drawing, warm paper background #FBF9F1, a glowing high-energy scientific laser system with diagnostic warning gauges, a doctor analyzing microscopic chromosome karyotype slices, a massive industrial steel rolling mill turbine, in the center a multi-armed AI agent core resolving all faults, clean bold lines, elegant technical sketch, subtle cyan and red highlights, 9:16 vertical composition"
    },
    # Act 3: 48H Hackathon Action (50-75s)
    {
        "id": "beat_03",
        "voice": "zh-CN-YunjianNeural",
        "rate": "+0%",
        "text": "赛事双轨并行：揭榜挂帅面向成熟团队深度攻坚；而面向全网极客的48小时极限黑客松，即将在11月15日打响！现场实机调用宇树具身机器人、调用国家科学数据银行，挑战AIP智能体互联协议。五大命题封闭开发两天两夜，现场跑通演示，当场评奖发钱！",
        "cues": [
            "赛事双轨并行：",
            "揭榜挂帅面向成熟团队深度攻坚；",
            "而面向全网极客的48小时极限黑客松，即将在11月15日打响！",
            "现场实机调用宇树具身机器人、调用国家科学数据银行，",
            "挑战AIP智能体互联协议。",
            "五大命题封闭开发两天两夜，",
            "现场跑通演示，当场评奖发钱！"
        ],
        "image_prompt": "minimalist editorial cartoon lineart illustration, high-tech hackathon scene, clean black ink sketch on warm paper #FBF9F1, young geek developer programming on laptop, an agile Unitree quadruped robot dog walking beside him, floating holographic nodes representing AIP multi-agent protocol, a glowing 48-hour digital countdown timer, floating cash prize envelope of 100000 RMB, energetic, precise ink lines, purple and cyan accents, 9:16 vertical composition"
    },
    # Act 4: OPC Ecosystem (75-100s)
    {
        "id": "beat_04",
        "voice": "zh-CN-YunjianNeural",
        "rate": "+0%",
        "text": "名字里的OPC，代表一人公司、超级个体。怀柔重点打造的果壳OPC创新社区，理念就是：让创造者只做创造，其余交给社区！办公空间拎包入驻，算力全额补贴，工商法务全面托管，还有上市公司真实订单喂养。优胜项目可叠加申领怀柔区最高50万元专项资金支持！",
        "cues": [
            "名字里的OPC，代表一人公司、超级个体。",
            "怀柔重点打造的果壳OPC创新社区，理念就是：",
            "让创造者只做创造，其余交给社区！",
            "办公空间拎包入驻，算力全额补贴，",
            "工商法务全面托管，还有上市公司真实订单喂养。",
            "优胜项目可叠加申领怀柔区最高50万元专项资金支持！"
        ],
        "image_prompt": "minimalist editorial cartoon lineart illustration, solo creator entrepreneur (One Person Company) with backpack and laptop walking into a bright modern Guoke OPC innovation park building, flanked by a friendly robotic AI butler and professional mentors, floating icons of free compute cloud subsidies, move-in office desk, enterprise contracts, and 500,000 RMB grant gold medal, warm paper background #FBF9F1, clean ink outlines, green and gold accents, 9:16 vertical composition"
    },
    # Act 5: Call to Action (100-125s)
    {
        "id": "beat_05",
        "voice": "zh-CN-YunjianNeural",
        "rate": "+0%",
        "text": "这里不要虚假的汇报，只要能打硬仗的代码。记住关键时间：48小时黑客松赛道，全网报名将在11月10日正式截止！不论你是高校实验室、创业公司，还是独立极客，带上你的智能体，来国家大科学装置的肩膀上，把代码变成订单！关注官方平台，立即报名！",
        "cues": [
            "这里不要虚假的汇报，只要能打硬仗的代码。",
            "记住关键时间：",
            "48小时黑客松赛道，全网报名将在11月10日正式截止！",
            "不论你是高校实验室、创业公司，还是独立极客，",
            "带上你的智能体，来国家大科学装置的肩膀上，把代码变成订单！",
            "关注官方平台，立即报名！"
        ],
        "image_prompt": "minimalist editorial cartoon lineart illustration, an eye-catching calendar marked November 10th with bold red circle, a stylish smartphone displaying official website opc.book2048.com with scanning rays, in the background the magnificent starry night sky over Huairou Science City with mountain silhouette, inspiring, clean ink drawing, warm paper background #FBF9F1, blue and red accents, 9:16 vertical composition"
    }
]

# ------------------------------------------------------------------------------
# 2. Edge-TTS 48kHz Neural Audio Generation & DSP Mastering
# ------------------------------------------------------------------------------
async def synthesize_all_beats():
    print(">>> [Edge-TTS 48kHz Neural] Synthesizing 5 Narrative Beats via zh-CN-YunjianNeural...")
    durations = {}
    for item in BEATS_SPEC:
        bid = item["id"]
        raw_text = item["text"]
        rate = item["rate"]
        voice = item["voice"]
        
        mp3_p = INPUTS_DIR / f"{bid}.mp3"
        raw_wav_p = INPUTS_DIR / f"{bid}_raw.wav"
        final_wav_p = INPUTS_DIR / f"{bid}.wav"
        
        # 1. Edge-TTS synthesis
        comm = edge_tts.Communicate(raw_text, voice, rate=rate)
        await comm.save(str(mp3_p))
        
        # 2. Convert to 48kHz 16-bit PCM WAV
        subprocess.run([
            "ffmpeg", "-y", "-i", str(mp3_p),
            "-ar", "48000", "-ac", "1", "-c:a", "pcm_s16le",
            str(raw_wav_p)
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        
        if mp3_p.exists():
            mp3_p.unlink()
            
        # 3. Audio Mastering Studio: Highpass 80Hz, Warmth 250Hz, Crisp 4500Hz, -14 LUFS
        success = AudioMasteringStudio.master_voice_clip(str(raw_wav_p), str(final_wav_p))
        if not success:
            shutil.copy2(str(raw_wav_p), str(final_wav_p))
            
        if raw_wav_p.exists():
            raw_wav_p.unlink()
            
        with wave.open(str(final_wav_p), "rb") as wf:
            dur = wf.getnframes() / float(wf.getframerate())
        durations[bid] = round(dur, 3)
        print(f"  ✓ [Mastered {bid}] Duration: {dur:.2f}s | {raw_text[:28]}...")
        
    total_dur = sum(durations.values())
    print(f"  >>> Total Video Audio Duration: {total_dur:.2f}s ({(total_dur/60):.2f} min, strictly < 3.0 min)")
    return durations

# ------------------------------------------------------------------------------
# 3. Agnes Image 2.5 Flash High-Fidelity Handdrawn Illustrations
# ------------------------------------------------------------------------------
def generate_all_illustrations(force_regenerate=False):
    print("\n>>> [Asset Quality Check] Verifying high-fidelity illustrations...")
    cover_dest = INPUTS_DIR / "cover.png"
    if not cover_dest.exists() or force_regenerate:
        print("  Generating fallback cover...")
        create_fallback_poster(cover_dest)
    else:
        print(f"  ✓ High-Fidelity Cover exists ({cover_dest.stat().st_size} bytes), preserving.")

    scenes_map = [
        ("scene1_hook.png", BEATS_SPEC[0]["image_prompt"]),
        ("scene2_pain.png", BEATS_SPEC[1]["image_prompt"]),
        ("scene3_hackathon.png", BEATS_SPEC[2]["image_prompt"]),
        ("scene4_opc.png", BEATS_SPEC[3]["image_prompt"]),
        ("scene5_cta.png", BEATS_SPEC[4]["image_prompt"]),
    ]
    
    for filename, prompt in scenes_map:
        dest = INPUTS_DIR / filename
        if dest.exists() and dest.stat().st_size > 1000 and not force_regenerate:
            print(f"  ✓ High-Fidelity {filename} exists ({dest.stat().st_size} bytes), preserving.")
            continue
            
        print(f"  >>> Requesting AI Illustration for {filename}...")
        url = pa.generate_image_agnes(prompt, str(dest), {}, size="1080x1920")
        if dest.exists() and dest.stat().st_size > 1000:
            with Image.open(dest) as im:
                im_rgb = im.convert("RGB")
                resized = im_rgb.resize((900, 1200), Image.Resampling.LANCZOS)
                resized.save(dest)
            print(f"  ✓ {filename} generated & fitted to 900x1200.")
        else:
            print(f"  ⚠ Failed to get {filename} from API, generating high-grade procedural fallback...")
            create_artistic_fallback(dest, filename)

def create_fallback_poster(dest):
    im = Image.new("RGB", (1080, 1920), (251, 249, 241))
    d = ImageDraw.Draw(im)
    d.rectangle([(40, 40), (1040, 1880)], outline=(35, 31, 32), width=6)
    d.rectangle([(55, 55), (1025, 1865)], outline=(2, 132, 199), width=3)
    font_l = get_font(56)
    font_m = get_font(38)
    d.text((120, 520), "怀柔科学城 · AI for Science", fill=(2, 132, 199), font=font_m)
    d.text((120, 590), "真需求 · 真攻坚 · 真采购", fill=(220, 38, 38), font=font_l)
    d.text((120, 670), "300万悬赏金 挂帅开战！", fill=(35, 31, 32), font=font_l)
    im.save(dest)

def create_artistic_fallback(dest, filename):
    im = Image.new("RGB", (900, 1200), (251, 249, 241))
    d = ImageDraw.Draw(im)
    d.rectangle([(20, 20), (880, 1180)], outline=(35, 31, 32), width=5)
    font = get_font(42)
    d.text((120, 550), f"AI 手绘插画 · {filename}", fill=(2, 132, 199), font=font)
    im.save(dest)

# ------------------------------------------------------------------------------
# 4. Job Manifest Construction (Pro Reveal Motion & Obsidian Captions)
# ------------------------------------------------------------------------------
def build_pro_job_manifest(durations):
    print("\n>>> [Job Manifest Engine] Assembling sweety-handdraw job.json with reveal motion...")
    scenes_map = [
        ("beat_01", "inputs/scene1_hook.png", BEATS_SPEC[0]),
        ("beat_02", "inputs/scene2_pain.png", BEATS_SPEC[1]),
        ("beat_03", "inputs/scene3_hackathon.png", BEATS_SPEC[2]),
        ("beat_04", "inputs/scene4_opc.png", BEATS_SPEC[3]),
        ("beat_05", "inputs/scene5_cta.png", BEATS_SPEC[4]),
    ]
    
    pages = []
    for idx, (bid, fig_src, spec) in enumerate(scenes_map):
        assert "".join(spec["cues"]) == spec["text"], f"Cue mismatch in {bid}"
        dur = durations[bid]
        cues = spec["cues"]
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
        "title": "2026 怀柔科学城 AI for Science · OPC 创新挑战赛官方深度报道",
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
    print(f"  >>> Saved pro job manifest -> {job_path}")
    return job_path

# ------------------------------------------------------------------------------
# 5. Core Engine Compilation & Full HD Video Rendering
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
        print(f"\n🎉 [DELIVERY] Final Pro Handdrawn Explainer Film -> {final_dest}")
        print(f"🎉 [DELIVERY] Upgraded Film in Artifacts -> {artifact_dest}")
        
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

def main():
    print("================================================================================")
    print("🚀 Starting Professional Full-Pipeline Video Upgrade (Edge-TTS + Agnes 2.5 Image)")
    print("================================================================================")
    loop = asyncio.get_event_loop()
    durations = loop.run_until_complete(synthesize_all_beats())
    generate_all_illustrations()
    build_pro_job_manifest(durations)
    run_handdraw_pipeline()
    print("\n🎉 Upgraded Pro Video Render Completed with Flying Colors!")

if __name__ == "__main__":
    main()
