import apiClient from './client';

export type VisualFocusPosition =
  | 'top_left'
  | 'top_center'
  | 'top_right'
  | 'center_left'
  | 'center'
  | 'center_right'
  | 'bottom_left'
  | 'bottom_center'
  | 'bottom_right';

export type MusicalSection =
  | 'Intro_Hook'
  | 'Verse_Setup'
  | 'Build_Up'
  | 'Chorus_Climax'
  | 'Drop_Punchline'
  | 'Outro_CTA';

export interface DirectorShot {
  shot_id: string;
  beat_index: number;
  time_start: number;
  time_end: number;
  duration: number;
  musical_section: MusicalSection;
  narration: string;
  character_count: number;
  speech_rate_cps: number;
  target_audio_duration: number;
  camera_movement: string;
  visual_focus_entry: VisualFocusPosition;
  visual_focus_exit: VisualFocusPosition;
  transition_out: string;
  render_mode: 'code_motion' | 'dance' | 'handdraw' | 'seedance_ai';
  visual_style_id: string;
  visual_prompt: string;
  source_citation?: string;
  locked: boolean;
}

export interface AudioVisualSyncRule {
  bgm_track: string;
  bpm: number;
  seconds_per_beat: number;
  bars_structure: Record<string, [number, number]>;
}

export interface TimecodedBeatSpec {
  project_id: string;
  episode_id: string;
  theme: string;
  target_duration: number;
  sync_rule: AudioVisualSyncRule;
  shots: DirectorShot[];
  total_characters: number;
  average_wpm: number;
  director_notes: string;
}

export interface StyleItem {
  id: string;
  name: string;
  primary_color: string;
  bg_color: string;
  accent: string;
  mood: string;
}

export interface StyleCategory {
  category_id: string;
  name: string;
  styles: StyleItem[];
}

export interface StylesCatalogResponse {
  system: string;
  version: string;
  total_styles: number;
  categories: StyleCategory[];
}

export const videoDesignApi = {
  /** 获取 44 种程序化视觉风格分类与清单 */
  getVisualStyles: async (): Promise<{ status: string; data: StylesCatalogResponse }> => {
    const res = await apiClient.get('/api/v1/video-design/styles');
    return res.data;
  },

  /** 依据超级峰视频设计方法论，将台词编排为导演级 TimecodedBeatSpec */
  analyzeBeats: async (payload: {
    project_id: string;
    episode_id: string;
    theme: string;
    narrations: string[];
    citations?: string[];
    bpm?: number;
    total_duration?: number;
    visual_style_id?: string;
  }): Promise<{ status: string; spec: TimecodedBeatSpec }> => {
    const res = await apiClient.post('/api/v1/video-design/beats/analyze', payload);
    return res.data;
  },

  /** 单镜头局部微调 (Single Shot Re-roll) */
  reRollShot: async (payload: {
    spec: TimecodedBeatSpec;
    shot_id: string;
    new_narration?: string;
    new_style_id?: string;
    new_camera_movement?: string;
  }): Promise<{ status: string; message: string; spec: TimecodedBeatSpec }> => {
    const res = await apiClient.post('/api/v1/video-design/shots/re-roll', payload);
    return res.data;
  },

  /** 调用 CodeMotion 引擎代码逐帧成片 (1080x1920 竖屏)，0 API成本 */
  renderCodeMotion: async (payload: {
    spec: TimecodedBeatSpec;
    output_filename?: string;
    audio_path?: string;
    bgm_path?: string;
    fps?: number;
  }): Promise<{
    status: string;
    tenant_id: string;
    video_path: string;
    video_url: string;
    ai_declaration: {
      ai_generated: boolean;
      declaration: string;
      compliance_checked: boolean;
    };
    quality_audit: {
      passed: boolean;
      issues: string[];
      resolution: string;
      fps: number;
      total_duration: number;
    };
  }> => {
    const res = await apiClient.post('/api/v1/video-design/render-code-motion', payload);
    return res.data;
  }
};
