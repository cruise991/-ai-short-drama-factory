import apiClient from './client';

export interface SystemConfigResponse {
  env: Record<string, string>;
  yaml: Record<string, any>;
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
};
