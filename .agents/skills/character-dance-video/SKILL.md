---
name: character-dance-video
description: Generate 20-40s character-consistent seamless looping dance videos with synced BPM music and automated quality audit.
---

# Character Dance Video Skill (`character-dance-video`)

Use this skill when the user requests generating a 20-40 second upbeat dance video from a character image or reference video, requiring character consistency, seamless head-to-tail looping, synced BPM audio, and zero playable/cropping defects.

## Overview & Architecture

The skill implements a robust multi-shot chaining pipeline with an automated Quality Audit Gate:

1. **Character Lock & Aspect Ratio Alignment**: Extracts image aspect ratio (9:16 portrait) and locks framing using explicit headroom/feet prompts to prevent cropping.
2. **Multi-Shot Chaining (5s per Shot)**:
   - **Shots 1 to N-1**: Sequential chaining using `FFmpeg` last-frame extraction & R2 cloud re-upload.
   - **Shot N (Final)**: Keyframes mode (`start=Shot N-1 end_frame`, `end=Shot 1 initial_pose`) for forced seamless loop closure.
3. **BPM Audio Sync Engine**: Generates or aligns continuous 120 BPM upbeat music matching the total video duration.
4. **Two-Step Safe Muxing**: Decouples video concatenation from audio muxing (`libx264 yuv420p` + AAC stereo) to guarantee 100% video playability across QuickTime and web browsers.
5. **Quality Audit Gate**: Automated pre-delivery assertions on playability, video stream specs, and non-silent audio amplitude.

---

## Command Line Usage

### Standard 20s Dance Generation:
```bash
python3 ai-short-drama/.agents/skills/character-dance-video/scripts/dance_pipeline.py \
    --input-image /path/to/character_reference.jpg \
    --duration 20 \
    --bpm 120 \
    --output /path/to/output_dance_20s.mp4
```

### Options & Portable Environment Variables:
- `--input-image`: Path to the character reference image (PNG/JPEG).
- `--duration`: Video duration in seconds (default: 20, supports 20, 30, 40).
- `--bpm`: Music tempo in Beats Per Minute (default: 120).
- `--output`: Path for the final audited MP4 video.

---

## Portability & Environment Setup

To ensure seamless migration across machines or deployment environments, configure the following environment variables in `.env` or system shell:

```env
# API Keys & Endpoints (Auto-fallback to standard OpenAI/Agnes schemas)
AGNES_BASE_URL=https://apihub.agnes-ai.com/v1
AGNES_API_KEY_1=sk-xxx...

# Cloud Asset Storage (AWS S3 / Cloudflare R2 / MinIO compatible)
R2_ENDPOINT=https://<account_id>.r2.cloudflarestorage.com
R2_ACCESS_KEY=<access_key>
R2_SECRET_KEY=<secret_key>
R2_BUCKET=short-ai
R2_PUBLIC_URL=https://<public_domain>.r2.dev
```

---

## File Structure

```
.agents/skills/character-dance-video/
├── SKILL.md                  # Skill specification and usage guidelines
├── scripts/
│   ├── dance_pipeline.py     # Main CLI entrypoint executing full dance pipeline & Quality Gate
│   ├── bpm_engine.py         # Rhythmic BGM synthesizer and beat matcher
│   ├── video_muxer.py        # Robust two-step FFmpeg encoder
│   └── quality_auditor.py    # Automated Quality Audit Gate assertion script
└── assets/
    └── bgm_templates/        # Default 120 BPM beat templates
```
