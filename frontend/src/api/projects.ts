import apiClient from './client';

export interface Project {
  id: number;
  project_slug: string;
  status: string;
  created_at: string;
  goal: string;
  format_type: string;
  branch_type: string;
  selected_ip?: string;
  vibe?: string;
  trend_enabled?: boolean;
  costume_id?: string;
  scene_id?: string;
  motion_id?: string;
  hand_preset?: string;
  caption_style?: string;
  error_message?: string;
}

export interface CreateProjectPayload {
  goal: string;
  format_type?: string;
  branch_type?: string;
  selected_ip?: string;
  vibe?: string;
  trend_enabled?: boolean;
  costume_id?: string;
  scene_id?: string;
  motion_id?: string;
  hand_preset?: string;
  caption_style?: string;
}

export interface ProjectDetailResponse {
  project: Project;
  latest_run_id: string | null;
  ticket: Record<string, any>;
  storyboard: string;
  is_waiting_approval: boolean;
  current_status: string;
}

export interface ProjectAssetsResponse {
  videos: string[];
  images: string[];
  drafts?: string[];
  subtitles?: string[];
}

export const projectsApi = {
  // List all projects
  getProjects: async (): Promise<Project[]> => {
    const res = await apiClient.get<Project[]>('/api/projects/');
    return res.data;
  },

  // Create new project with structured JSON body
  createProject: async (payload: CreateProjectPayload): Promise<Project> => {
    const res = await apiClient.post<Project>('/api/projects/', payload);
    return res.data;
  },

  // Fetch detailed project status and current storyboard draft
  getProjectDetail: async (slug: string): Promise<ProjectDetailResponse> => {
    const res = await apiClient.get<ProjectDetailResponse>(`/api/projects/${slug}/detail`);
    return res.data;
  },

  // Fetch rendered assets & storyboards
  getProjectAssets: async (slug: string): Promise<ProjectAssetsResponse> => {
    const res = await apiClient.get<ProjectAssetsResponse>(`/api/projects/${slug}/assets`);
    return res.data;
  },

  // One-click approval
  approveProject: async (projectId: number): Promise<{ success: boolean; message?: string }> => {
    const res = await apiClient.post(`/api/projects/${projectId}/approve`);
    return res.data;
  },

  // Submit modification feedback / rejection
  rejectProject: async (projectId: number, feedback: string): Promise<{ success: boolean; message?: string }> => {
    const res = await apiClient.post(`/api/projects/${projectId}/reject`, { message: feedback });
    return res.data;
  },

  // Submit general user input
  submitInput: async (projectId: number, message: string): Promise<{ success: boolean }> => {
    const res = await apiClient.post(`/api/projects/${projectId}/input`, { message });
    return res.data;
  },

  // Delete project
  deleteProject: async (projectId: number): Promise<{ success: boolean; message?: string }> => {
    const res = await apiClient.delete(`/api/projects/${projectId}`);
    return res.data;
  },

  // Retry paused or failed project
  retryProject: async (projectId: number): Promise<{ success: boolean; message?: string }> => {
    const res = await apiClient.post(`/api/projects/${projectId}/retry`);
    return res.data;
  },
};
