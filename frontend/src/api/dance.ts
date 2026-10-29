import apiClient from './client';

export interface DanceTemplate {
  dance_id: string;
  name: string;
  bpm: string;
  duration_range: number[];
  tags: string[];
  stats?: { views?: string; difficulty?: number; virality?: number };
  timeline?: Array<{ time: string; name: string; action_prompt: string; expression?: string }>;
}

export interface DanceTaskStatus {
  task_id: string;
  status: 'queued' | 'processing' | 'completed' | 'failed';
  progress: number;
  message: string;
  duration?: number;
  style?: string;
  template_id?: string;
  aspect_ratio?: string;
  video_url?: string;
  video_path?: string;
  jianying_draft_zip?: string;
  jianying_synced?: boolean;
}

export interface ViewDetail {
  index: number;
  role: 'FRONT' | 'SIDE' | 'BACK';
  path: string;
  preview_url: string;
  is_primary_start: boolean;
  confidence: number;
}

export interface MultiViewResult {
  detected_n: number;
  is_multiview: boolean;
  primary_front_path: string;
  views: ViewDetail[];
  elapsed_ms: number;
}

export interface PoseCategory {
  id: string;
  name: string;
  description?: string;
  count?: number;
}

export interface PoseAngle {
  id: string;
  name: string;
  degree: string;
  desc: string;
}

export interface PoseItem {
  id: string;
  code: string;
  name: string;
  category: string;
  category_name?: string;
  default_angle: string;
  available_angles: string[];
  recommended_beats: number;
  recommended_seconds: number;
  recommended_bpm: number[];
  tags: string[];
  dynamic_prompt: string;
  transition_affinity?: string[];
  preview_urls?: Record<string, string>;
}

export interface PoseGalleryResponse {
  version: string;
  total: number;
  filtered_count: number;
  categories: PoseCategory[];
  angles: PoseAngle[];
  poses: PoseItem[];
}

export interface PoseSlot {
  slot_id: string;
  pose_id: string;
  name: string;
  category: string;
  angle: string;
  beats: number;
  seconds: number;
  dynamic_prompt?: string;
  tags?: string[];
  preview_urls?: Record<string, string>;
}

export interface ChoreographyRecipe {
  recipe_id?: string;
  title: string;
  creator?: string;
  style: string;
  bpm: number;
  aspect_ratio?: string;
  sequence: PoseSlot[];
  created_at?: number;
}

export const danceApi = {
  getTemplates: async (): Promise<DanceTemplate[]> => {
    const res = await apiClient.get<DanceTemplate[]>('/api/dance/templates');
    return res.data;
  },

  analyzeViews: async (formData: FormData): Promise<MultiViewResult> => {
    const res = await apiClient.post<MultiViewResult>('/api/dance/analyze-views', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return res.data;
  },

  generateDance: async (formData: FormData): Promise<{ task_id: string; status: string }> => {
    const res = await apiClient.post('/api/dance/generate', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return res.data;
  },

  getPoseGallery: async (params?: { category?: string; angle?: string; tag?: string; search?: string }): Promise<PoseGalleryResponse> => {
    const res = await apiClient.get<PoseGalleryResponse>('/api/dance/poses', { params });
    return res.data;
  },

  choreographDance: async (formData: FormData): Promise<{ task_id: string; status: string; duration: number; poses_count: number }> => {
    const res = await apiClient.post('/api/dance/choreograph', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return res.data;
  },

  saveRecipe: async (recipe: ChoreographyRecipe): Promise<{ recipe_id: string; title: string; total_duration: number; total_beats: number; share_url: string; message: string }> => {
    const res = await apiClient.post('/api/dance/recipe', recipe);
    return res.data;
  },

  getRecipe: async (recipeId: string): Promise<ChoreographyRecipe> => {
    const res = await apiClient.get<ChoreographyRecipe>(`/api/dance/recipe/${recipeId}`);
    return res.data;
  },

  getTaskStatus: async (taskId: string): Promise<DanceTaskStatus> => {
    const res = await apiClient.get<DanceTaskStatus>(`/api/dance/tasks/${taskId}`);
    return res.data;
  },
};
