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

  getTaskStatus: async (taskId: string): Promise<DanceTaskStatus> => {
    const res = await apiClient.get<DanceTaskStatus>(`/api/dance/tasks/${taskId}`);
    return res.data;
  },
};

