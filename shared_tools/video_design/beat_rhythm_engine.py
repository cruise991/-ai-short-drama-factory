"""
beat_rhythm_engine.py — 超级峰声画节拍与导演时码引擎 (Audio-Visual Rhythm Engine)
"""

import math
from typing import List, Dict, Optional, Tuple
from shared_tools.video_design.storyboard_schema import (
    TimecodedBeatSpec, DirectorShot, AudioVisualSyncRule, MusicalSection
)
from shared_tools.video_design.visual_focus_router import resolve_focus_relay, validate_focus_continuity

CPS_MIN = 3.2
CPS_STANDARD = 4.2
CPS_FAST = 5.2

def calculate_shot_timing_from_bpm(
    bpm: float,
    total_duration: float = 15.0,
    shot_count: int = 4
) -> List[Tuple[float, float, str]]:
    seconds_per_beat = 60.0 / bpm
    
    if shot_count == 4:
        ratios = [0.20, 0.35, 0.25, 0.20]
        sections = ["Intro_Hook", "Verse_Setup", "Build_Up", "Chorus_Climax"]
    elif shot_count == 5:
        ratios = [0.15, 0.25, 0.25, 0.20, 0.15]
        sections = ["Intro_Hook", "Verse_Setup", "Build_Up", "Chorus_Climax", "Drop_Punchline"]
    elif shot_count == 2:
        ratios = [0.4, 0.6]
        sections = ["Intro_Hook", "Chorus_Climax"]
    elif shot_count == 3:
        ratios = [0.25, 0.45, 0.30]
        sections = ["Intro_Hook", "Verse_Setup", "Chorus_Climax"]
    else:
        ratios = [1.0 / shot_count] * shot_count
        sections = ["Intro_Hook"] + ["Verse_Setup"] * (shot_count - 2) + ["Chorus_Climax"]

    cuts = []
    current_t = 0.0
    for i, (ratio, sec) in enumerate(zip(ratios, sections)):
        raw_dur = total_duration * ratio
        beats_in_shot = max(2, round(raw_dur / seconds_per_beat))
        quantized_dur = beats_in_shot * seconds_per_beat
        
        if i == len(ratios) - 1:
            end_t = total_duration
        else:
            end_t = min(total_duration, current_t + quantized_dur)
            
        cuts.append((round(current_t, 3), round(end_t, 3), sec))
        current_t = end_t
        if current_t >= total_duration:
            break
            
    return cuts

def estimate_word_budget(duration: float, cps: float = CPS_STANDARD) -> Tuple[int, int]:
    effective_duration = max(0.5, duration - 0.2)
    center = effective_duration * cps
    return max(3, math.floor(center * 0.85)), max(5, math.ceil(center * 1.15))

def generate_director_storyboard(
    project_id: str,
    episode_id: str,
    theme: str,
    narrations: List[str],
    bpm: float = 120.0,
    total_duration: float = 15.0,
    visual_style_id: str = "dark_gold_lines",
    citations: Optional[List[str]] = None
) -> TimecodedBeatSpec:
    shot_count = len(narrations)
    cuts = calculate_shot_timing_from_bpm(bpm, total_duration, shot_count)
    
    shots: List[DirectorShot] = []
    prev_exit_focus = "center"
    
    camera_motions = ["push_in", "whip_pan_right", "tilt_up", "pull_out"]
    
    for i, (start_t, end_t, sec) in enumerate(cuts):
        dur = end_t - start_t
        text = narrations[i] if i < len(narrations) else ""
        char_cnt = len(text)
        actual_cps = round(char_cnt / max(0.5, dur), 2)
        
        cam_mov = camera_motions[i % len(camera_motions)]
        entry_focus, trans_out = resolve_focus_relay(prev_exit_focus, cam_mov)
        exit_focus = "center" if entry_focus != "center" else "center_right"
        prev_exit_focus = exit_focus
        
        citation = citations[i] if citations and i < len(citations) else None
        
        shot = DirectorShot(
            shot_id=f"S{i+1:02d}",
            beat_index=i + 1,
            time_start=start_t,
            time_end=end_t,
            duration=round(dur, 3),
            musical_section=sec,
            narration=text,
            character_count=char_cnt,
            speech_rate_cps=actual_cps,
            target_audio_duration=round(dur, 2),
            camera_movement=cam_mov,
            visual_focus_entry=entry_focus,
            visual_focus_exit=exit_focus,
            transition_out=trans_out,
            render_mode="code_motion",
            visual_style_id=visual_style_id,
            visual_prompt=f"【{sec}】基于主题'{theme}'展示：{text}",
            source_citation=citation,
            locked=False
        )
        shots.append(shot)
        
    spec = TimecodedBeatSpec(
        project_id=project_id,
        episode_id=episode_id,
        theme=theme,
        target_duration=total_duration,
        sync_rule=AudioVisualSyncRule(bpm=bpm, seconds_per_beat=round(60.0/bpm, 3)),
        shots=shots,
        total_characters=sum(s.character_count for s in shots),
        average_wpm=round(sum(s.character_count for s in shots) / (total_duration / 60.0), 1),
        director_notes="由 beat_rhythm_engine 自动生成，严格遵照超级峰声画拍点与焦点接力协议。"
    )
    return spec

def re_roll_single_shot(
    spec: TimecodedBeatSpec,
    shot_id: str,
    new_narration: Optional[str] = None,
    new_style_id: Optional[str] = None,
    new_camera_movement: Optional[str] = None
) -> Tuple[TimecodedBeatSpec, bool, str]:
    target_idx = None
    for idx, s in enumerate(spec.shots):
        if s.shot_id == shot_id:
            target_idx = idx
            break
            
    if target_idx is None:
        return spec, False, f"未找到指定分镜 ID: {shot_id}"
        
    shot = spec.shots[target_idx]
    if shot.locked:
        return spec, False, f"分镜 {shot_id} 已被锁定，禁止重编"
        
    if new_narration is not None:
        shot.narration = new_narration
        shot.character_count = len(new_narration)
        shot.speech_rate_cps = round(len(new_narration) / max(0.5, shot.duration), 2)
        
    if new_style_id is not None:
        shot.visual_style_id = new_style_id
        
    if new_camera_movement is not None:
        shot.camera_movement = new_camera_movement
        prev_exit = spec.shots[target_idx - 1].visual_focus_exit if target_idx > 0 else "center"
        entry_f, trans_out = resolve_focus_relay(prev_exit, new_camera_movement)
        shot.visual_focus_entry = entry_f
        shot.transition_out = trans_out
        
    spec.total_characters = sum(s.character_count for s in spec.shots)
    spec.average_wpm = round(spec.total_characters / (spec.target_duration / 60.0), 1)
    
    return spec, True, f"分镜 {shot_id} 局部重编成功"

