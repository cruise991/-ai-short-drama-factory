import apiClient from './client';

export interface SystemConfigResponse {
  env: Record<string, string>;
  yaml: Record<string, any>;
}

export interface BranchPresetsResponse {
  costumes: Record<string, any>;
  scenes: Record<string, any>;
  motions: Record<string, any>;
  hands: Array<{ id: string; name: string; desc: string; icon: string }>;
  papers: Array<{ id: string; name: string; color: string; text_color: string; recommended_caption: string }>;
  caption_styles: Array<{ id: string; name: string; desc: string; bg_color: string; bg_opacity: number; text_color: string; size: number }>;
  ips: string[];
}

export const configApi = {
  getSystemConfig: async (): Promise<SystemConfigResponse> => {
    const res = await apiClient.get<SystemConfigResponse>('/api/config');
    return res.data;
  },

  updateSystemConfig: async (payload: {
    env_vars: Record<string, string>;
    yaml_vars: Record<string, any>;
  }): Promise<{ message: string }> => {
    const res = await apiClient.post('/api/config', payload);
    return res.data;
  },

  getAvailableIps: async (): Promise<string[]> => {
    try {
      const res = await apiClient.get<{ ips: string[] }>('/api/config/ips');
      return res.data.ips || [];
    } catch {
      return ['C001_Luna', 'C003_Aria', 'C006_Yumi', 'C007_Nana'];
    }
  },

  getBranchPresets: async (): Promise<BranchPresetsResponse> => {
    const res = await apiClient.get<BranchPresetsResponse>('/api/config/branch_presets');
    return res.data;
  },
};
