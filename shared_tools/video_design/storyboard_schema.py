"""
storyboard_schema.py — 超级峰视频设计方法论 (chaojifeng-video-design) 标准协议
"""

from typing import List, Dict, Optional, Tuple, Literal
from pydantic import BaseModel, Field

VisualFocusPosition = Literal["top_left", "top_center", "top_right", "center_left", "center", "center_right", "bottom_left", "bottom_center", "bottom_right"]
TransitionType = Literal["cut", "whip_pan_left", "whip_pan_right", "push_in", "pull_out", "fade_black", "cross_dissolve", "mask_wipe", "match_cut"]
MusicalSection = Literal["Intro_Hook", "Verse_Setup", "Build_Up", "Chorus_Climax", "Drop_Punchline", "Outro_CTA"]

class DirectorShot(BaseModel):
    shot_id: str = Field(..., description="唯一分镜编号，如 S01, S02")
    beat_index: int = Field(..., description="节拍序号 (从1开始)")
    time_start: float = Field(..., description="起始时码 (秒)")
    time_end: float = Field(..., description="结束时码 (秒)")
    duration: float = Field(..., description="持续时长 (秒)")
    musical_section: MusicalSection = Field("Verse_Setup", description="对应乐段结构")
    
    # 台词与声画节奏
    narration: str = Field("", description="旁白台词/台词文本")
    character_count: int = Field(0, description="台词字数")
    speech_rate_cps: float = Field(4.2, description="预估语速 (字符/秒，中文标准 3.8~4.5)")
    target_audio_duration: float = Field(0.0, description="音频对齐目标时码")
    
    # 视听与镜头语言 (超级峰方法论)
    camera_movement: str = Field("static", description="运镜动作：push_in, pull_out, pan_left, pan_right, tilt_up, crane_down, orbital")
    visual_focus_entry: VisualFocusPosition = Field("center", description="视线切入焦点锚点")
    visual_focus_exit: VisualFocusPosition = Field("center", description="视线切出焦点锚点")
    transition_out: TransitionType = Field("cut", description="与下个镜头的转场接力方式")
    
    # 视觉表现模式与风格
    render_mode: Literal["code_motion", "dance", "handdraw", "seedance_ai"] = Field("code_motion", description="渲染执行引擎")
    visual_style_id: str = Field("dark_gold_lines", description="绑定的视觉风格模版ID")
    visual_prompt: str = Field("", description="渲染/提示词描述")
    source_citation: Optional[str] = Field(None, description="知识出处/文献事实证据标注 (vibe-knowledge)")
    
    # 局部重编控制
    locked: bool = Field(False, description="是否锁定 (Re-roll时不可被重算)")

class AudioVisualSyncRule(BaseModel):
    bgm_track: str = Field("default_dynamic.mp3", description="使用的BGM音轨文件名")
    bpm: float = Field(120.0, description="每分钟节拍数 (Beats Per Minute)")
    seconds_per_beat: float = Field(0.5, description="每拍秒数")
    bars_structure: Dict[str, Tuple[float, float]] = Field(
        default_factory=lambda: {
            "Intro_Hook": (0.0, 3.0),
            "Verse_Setup": (3.0, 9.0),
            "Build_Up": (9.0, 12.0),
            "Chorus_Climax": (12.0, 15.0)
        },
        description="各乐段的时码窗口映射"
    )

class TimecodedBeatSpec(BaseModel):
    project_id: str = Field(..., description="所属项目/短剧ID")
    episode_id: str = Field(..., description="集数/视频标识")
    theme: str = Field(..., description="主题/核心知识点")
    target_duration: float = Field(15.0, description="目标总时长 (标准15s/30s/60s)")
    sync_rule: AudioVisualSyncRule = Field(default_factory=AudioVisualSyncRule)
    shots: List[DirectorShot] = Field(default_factory=list, description="有序分镜镜头列表")
    total_characters: int = Field(0, description="全剧本文案总字数")
    average_wpm: float = Field(240.0, description="全片平均配音速率 (CPM/WPM)")
    director_notes: str = Field("", description="导演声画排版与转场接力执行备忘")

