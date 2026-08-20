---
name: character-dance-video
description: Generate 15-40s character-consistent seamless looping dance videos with dynamic character analysis, professional choreography, multi-layered producer BGM, and automated tri-tier quality audit.
---

# Character Dance Video Skill (`character-dance-video`) Pro

Use this skill when the user requests generating a 15-40 second upbeat dance video from a character image or reference video, requiring character & background consistency, professional dance choreography, seamless head-to-tail looping, high-fidelity music, and zero playable/cropping defects.

## Core Architecture (Director-Producer-Engineer Framework)

1. **Visual Feature Analyzer (`character_analyzer.py`)**:
   - Dynamic 4-layer prompt lock: `[Camera Lock + Subject Lock + Outfit Lock + Scene Lock]`.
   - Eradicates hardcoded prompt cross-contamination.
2. **Choreography Engine (`choreography_engine.py`)**:
   - Professional dance structure (Intro -> Groove -> Climax -> Release -> Loop Closure).
   - Kinetic momentum continuity across shots with safe AI motion rules.
3. **Audio Director (`audio_director.py`)**:
   - Multi-layered synthesizer (Kick, Snare/Clap, 16th Hi-Hat, Synth Lead, Sub-Bass).
   - EBU R128 audio mastering with 0.05s anti-pop micro-fades.
4. **Multi-Shot Chaining & Loop Closure (`dance_pipeline_pro.py`)**:
   - Shots 1 to N-1: Frame relay via Cloudflare R2 / S3 storage.
   - Shot N: Keyframes mode linking final frame back to initial anchor for seamless loop.
5. **Two-Step Safe Muxing (`video_muxer.py`)**:
   - Pure video concatenation followed by audio track remux (`libx264 yuv420p` + AAC stereo).
6. **Tri-Tier Quality Audit Gate (`quality_auditor.py`)**:
   - Checks container/codec, audio RMS energy, and file integrity.

---

## Command Line Usage

```bash
python3 ai-short-drama/.agents/skills/character-dance-video/scripts/dance_pipeline_pro.py \
    --input-image /path/to/character_ref.png \
    --duration 30 \
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
│   ├── choreography_engine.py # Professional dance sequence planner
│   ├── audio_director.py      # Multi-layered producer BGM synthesizer
│   ├── video_muxer.py         # Two-step safe FFmpeg encoder
│   └── quality_auditor.py     # Tri-tier Quality Assurance Gate
└── assets/                   # BGM and style templates
```
