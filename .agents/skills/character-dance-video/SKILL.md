---
name: character-dance-video
description: Generate 15-40s character-consistent seamless looping dance videos with dynamic character analysis, 12 dance templates choreography, 8-genre EDM master BGM library, and automated tri-tier quality audit.
---

# Character Dance Video Skill (`character-dance-video`) Pro

Use this skill when the user requests generating a 15-40 second upbeat dance video from a character image or reference video, requiring character & background consistency, professional dance choreography, seamless head-to-tail looping, high-fidelity music, and zero playable/cropping defects.

## Core Architecture (Director-Producer-Engineer Framework)

1. **Visual Feature Analyzer (`character_analyzer.py`)**:
   - Dynamic 4-layer prompt lock: `[Camera Lock + Subject Lock + Outfit Lock + Scene Lock]`. Full-height 9-head model proportions and anti-sinking constraints.
   - Eradicates hardcoded prompt cross-contamination and preserves texture details with unsharp filter.
2. **Choreography Engine (`choreography_engine.py`)**:
   - Supports 12 viral dance templates (`DANCE_THAI_SWAY`, `DANCE_JUMP_BLACKPINK`, `DANCE_CAI_BAO_XIAO`, etc.) from `assets/dance/07_templates/`.
   - Deterministic final shot pose loop closure (smooth transition back to starting posture).
3. **Audio Director (`audio_director.py`)**:
   - 3-Tier dynamic resolution: P1 Custom Audio -> P2 8-Genre Master Library (K-Pop, Fitness, Street, Luxury, Thai Sway, Cai Bao Xiao, Blackpink, Electronic) -> P3 Procedural Super-Saw Synth fallback.
   - Dynamic BPM `atempo` time-stretching and EBU R128 loudness mastering (-14 LUFS, True Peak -1.5 dB).
4. **Multi-Shot Chaining & Loop Closure (`dance_pipeline_pro.py`)**:
   - Shots 1 to N-1: Frame relay via Cloudflare R2 / S3 storage.
   - Shot N: Keyframes mode linking final frame back to initial anchor for seamless loop.
5. **Two-Step Safe Muxing (`video_muxer.py`)**:
   - Pure video concatenation followed by audio track remux (`libx264 yuv420p` + AAC stereo).
6. **Tri-Tier Quality Audit Gate (`quality_auditor.py`)**:
   - Rigorous checks for H.264 yuv420p video, AAC audio, sub-0.5s audio-video duration match, and audio energy thresholds.

---

## Command Line Usage

```bash
python3 ai-short-drama/.agents/skills/character-dance-video/scripts/dance_pipeline_pro.py \
    --input-image /path/to/character_ref.png \
    --duration 30 \
    --template DANCE_THAI_SWAY \
    --style fitness \
    --bpm 120 \
    --output /path/to/output_dance_30s.mp4
```

### Supported Styles:
- `fitness`: Athletic workout / energetic dance (sports bra, leggings, gym/studio).
- `kpop`: Cute idol point dance with hand flower gestures.
- `street`: Urban hip-hop & rhythmic footwork.
- `luxury`: Elegant slow-groove evening cocktail dance.

---

## File Structure

```
.agents/skills/character-dance-video/
├── SKILL.md                  # Skill specification and guidelines
├── scripts/
│   ├── dance_pipeline_pro.py  # Unified CLI orchestrator
│   ├── character_analyzer.py  # 4-layer prompt builder & style extractor
│   ├── choreography_engine.py # Professional dance sequence planner (12 templates)
│   ├── audio_director.py      # 3-Tier Studio EDM audio engine with 8-genre master library
│   ├── video_muxer.py         # Two-step safe FFmpeg encoder
│   └── quality_auditor.py     # Tri-tier Quality Assurance Gate
└── assets/
    └── bgm_library/          # Pre-mastered EDM dance stems across 8 genres
```
