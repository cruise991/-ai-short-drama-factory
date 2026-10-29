import json
import wave
from pathlib import Path

job_dir = Path("/Users/workspace/ai_short_company/ai-short-drama/projects/handdraw_anger_decision")

def get_duration(wav_name):
    wav_path = job_dir / "inputs" / wav_name
    with wave.open(str(wav_path), "rb") as f:
        return f.getnframes() / f.getframerate()

durs = {f"beat_{i:02d}": get_duration(f"beat_{i:02d}.wav") for i in range(1, 9)}
print("Measured durations:", durs)

# Canvas: 1080x1920 (9:16 vertical), 30fps
# Style: minimalist line art, warm ivory paper #FBF9F1, teacher-pen, no watermark, no ads
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
        "sentence_pause_seconds": 0.20,
        "page_pause_seconds": 0.35,
        "end_hold_seconds": 0.80
    },
    "captions": {
        "font_size": 36,
        "bottom_margin": 140
    },
    "pages": [
        # Page 1: 痛点引入与现实共鸣 (Beats 01 & 02, ~13.8s)
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
                            "parts": [
                                {
                                    "id": "anger_figure",
                                    "polygon": [[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0]]
                                }
                            ],
                            "source": "inputs/scene1_anger.png",
                            "x": 90,
                            "y": 280,
                            "width": 900,
                            "height": 1200,
                            "weight": 3.0,
                            "lineart_exception": True,
                            "drawing": {
                                "mode": "draw",
                                "speed": 1.0
                            }
                        }
                    ]
                }
            ],
            "beats": [
                {
                    "id": "beat_01",
                    "text": "你有没有经历过这种时刻？在极度愤怒的几秒钟里，脱口而出伤人的狠话，或者做出事后无比后悔的决定。",
                    "audio": "inputs/beat_01.wav",
                    "caption_cues": [
                        {"text": "你有没有经历过这种时刻？", "start": 0.0, "end": 2.2},
                        {"text": "在极度愤怒的几秒钟里，脱口而出伤人的狠话，", "start": 2.2, "end": 4.9},
                        {"text": "或者做出事后无比后悔的决定。", "start": 4.9, "end": round(durs["beat_01"] - 0.02, 3)}
                    ]
                },
                {
                    "id": "beat_02",
                    "text": "很多人以为这是性格暴躁，或者意志力太薄弱。但在脑科学视角下，这其实是一场大脑内部的生理故障。",
                    "audio": "inputs/beat_02.wav",
                    "caption_cues": [
                        {"text": "很多人以为这是性格暴躁，或者意志力太薄弱。", "start": 0.0, "end": 3.2},
                        {"text": "但在脑科学视角下，这其实是一场大脑内部的生理故障。", "start": 3.2, "end": round(durs["beat_02"] - 0.02, 3)}
                    ]
                }
            ]
        },
        # Page 2: 大脑内部双雄对峙 (Beats 03 & 04, ~16.0s)
        {
            "transition": {"type": "cut"},
            "visual_groups": [
                {
                    "start_beat": "beat_03",
                    "end_beat": "beat_04",
                    "lead": 0.40,
                    "hold": 0.80,
                    "actions": [
                        {
                            "type": "illustration",
                            "parts": [
                                {
                                    "id": "brain_structure",
                                    "polygon": [[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0]]
                                }
                            ],
                            "source": "inputs/scene2_brain.png",
                            "x": 90,
                            "y": 280,
                            "width": 900,
                            "height": 1200,
                            "weight": 3.0,
                            "lineart_exception": True,
                            "drawing": {
                                "mode": "draw",
                                "speed": 1.0
                            }
                        }
                    ]
                }
            ],
            "beats": [
                {
                    "id": "beat_03",
                    "text": "在正常情况下，我们负责理性思考、逻辑判断和长远决策的，是大脑前端的‘前额叶皮层’，它是人类的理智总指挥。",
                    "audio": "inputs/beat_03.wav",
                    "caption_cues": [
                        {"text": "在正常情况下，我们负责理性思考、逻辑判断和长远决策的，", "start": 0.0, "end": 4.2},
                        {"text": "是大脑前端的‘前额叶皮层’，它是人类的理智总指挥。", "start": 4.2, "end": round(durs["beat_03"] - 0.02, 3)}
                    ]
                },
                {
                    "id": "beat_04",
                    "text": "而在大脑深处，还隐藏着一个古老的警报系统——‘杏仁核’。它从远古进化而来，专门在危险来临时掌管恐惧与进攻。",
                    "audio": "inputs/beat_04.wav",
                    "caption_cues": [
                        {"text": "而在大脑深处，还隐藏着一个古老的警报系统——‘杏仁核’。", "start": 0.0, "end": 4.0},
                        {"text": "它从远古进化而来，专门在危险来临时掌管恐惧与进攻。", "start": 4.0, "end": round(durs["beat_04"] - 0.02, 3)}
                    ]
                }
            ]
        },
        # Page 3: 核心机制：杏仁核劫持 (Beats 05 & 06, ~19.1s)
        {
            "transition": {"type": "cut"},
            "visual_groups": [
                {
                    "start_beat": "beat_05",
                    "end_beat": "beat_06",
                    "lead": 0.40,
                    "hold": 0.80,
                    "actions": [
                        {
                            "type": "illustration",
                            "parts": [
                                {
                                    "id": "hijack_process",
                                    "polygon": [[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0]]
                                }
                            ],
                            "source": "inputs/scene3_hijack.png",
                            "x": 90,
                            "y": 280,
                            "width": 900,
                            "height": 1200,
                            "weight": 3.0,
                            "lineart_exception": True,
                            "drawing": {
                                "mode": "draw",
                                "speed": 1.0
                            }
                        }
                    ]
                }
            ],
            "beats": [
                {
                    "id": "beat_05",
                    "text": "当你情绪被引爆时，杏仁核会瞬间激活，抢先劫持神经信号。这就是心理学上著名的‘杏仁核劫持’。血液和能量被疯狂抽调给战斗本能，前额叶供能骤降，理智指挥部直接掉线！",
                    "audio": "inputs/beat_05.wav",
                    "caption_cues": [
                        {"text": "当你情绪被引爆时，杏仁核会瞬间激活，抢先劫持神经信号。", "start": 0.0, "end": 3.8},
                        {"text": "这就是心理学上著名的‘杏仁核劫持’。", "start": 3.8, "end": 6.4},
                        {"text": "血液和能量被疯狂抽调给战斗本能，前额叶供能骤降，理智指挥部直接掉线！", "start": 6.4, "end": round(durs["beat_05"] - 0.02, 3)}
                    ]
                },
                {
                    "id": "beat_06",
                    "text": "也就是说，当你暴怒时，你的大脑并不是在理性分析，而是一个远古原始人握住了你身体的最高控制权。",
                    "audio": "inputs/beat_06.wav",
                    "caption_cues": [
                        {"text": "也就是说，当你暴怒时，你的大脑并不是在理性分析，", "start": 0.0, "end": 3.9},
                        {"text": "而是一个远古原始人握住了你身体的最高控制权。", "start": 3.9, "end": round(durs["beat_06"] - 0.02, 3)}
                    ]
                }
            ]
        },
        # Page 4: 科学破局法：黄金六秒法则 (Beats 07 & 08, ~17.2s)
        {
            "transition": {"type": "cut"},
            "visual_groups": [
                {
                    "start_beat": "beat_07",
                    "end_beat": "beat_08",
                    "lead": 0.40,
                    "hold": 0.80,
                    "actions": [
                        {
                            "type": "illustration",
                            "parts": [
                                {
                                    "id": "solution_timer",
                                    "polygon": [[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0]]
                                }
                            ],
                            "source": "inputs/scene4_timer.png",
                            "x": 90,
                            "y": 280,
                            "width": 900,
                            "height": 1200,
                            "weight": 3.0,
                            "lineart_exception": True,
                            "drawing": {
                                "mode": "draw",
                                "speed": 1.0
                            }
                        }
                    ]
                }
            ],
            "beats": [
                {
                    "id": "beat_07",
                    "text": "神经生理学研究表明，杏仁核爆发带来的肾上腺素激增，在体内的剧烈生理峰值只有大约六秒钟。",
                    "audio": "inputs/beat_07.wav",
                    "caption_cues": [
                        {"text": "神经生理学研究表明，杏仁核爆发带来的肾上腺素激增，", "start": 0.0, "end": 3.7},
                        {"text": "在体内的剧烈生理峰值只有大约六秒钟。", "start": 3.7, "end": round(durs["beat_07"] - 0.02, 3)}
                    ]
                },
                {
                    "id": "beat_08",
                    "text": "所以，下次感到怒火中烧时，先深呼吸闭嘴六秒钟。给前额叶留出重新连线的时间，你的理智就不会被情绪绑架。",
                    "audio": "inputs/beat_08.wav",
                    "caption_cues": [
                        {"text": "所以，下次感到怒火中烧时，先深呼吸闭嘴六秒钟。", "start": 0.0, "end": 4.6},
                        {"text": "给前额叶留出重新连线的时间，你的理智就不会被情绪绑架。", "start": 4.6, "end": round(durs["beat_08"] - 0.02, 3)}
                    ]
                }
            ]
        }
    ]
}

job_file = job_dir / "job.json"
job_file.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Successfully generated clean job.json at {job_file}")
