import { create } from 'zustand';

export interface UserInfo {
  id: number;
  username: string;
  role: 'admin' | 'operator' | 'viewer';
  tenant_id: string;
  email?: string;
}

interface AuthState {
  token: string | null;
  user: UserInfo | null;
  isAuthenticated: boolean;
  setAuth: (token: string, user: UserInfo) => void;
  logout: () => void;
  updateTenant: (tenantId: string) => void;
}

const STORAGE_TOKEN_KEY = 'shortdrama_auth_token';
const STORAGE_USER_KEY = 'shortdrama_user_info';

export const useAuthStore = create<AuthState>((set) => {
  // Read initial from localStorage
  const savedToken = localStorage.getItem(STORAGE_TOKEN_KEY);
  let savedUser: UserInfo | null = null;
  try {
    const rawUser = localStorage.getItem(STORAGE_USER_KEY);
    if (rawUser) savedUser = JSON.parse(rawUser);
  } catch (e) {
    console.error('Failed to parse saved user', e);
  }

  return {
    token: savedToken,
    user: savedUser,
    isAuthenticated: !!savedToken,

    setAuth: (token: string, user: UserInfo) => {
      localStorage.setItem(STORAGE_TOKEN_KEY, token);
      localStorage.setItem(STORAGE_USER_KEY, JSON.stringify(user));
      set({ token, user, isAuthenticated: true });
    },

    logout: () => {
      localStorage.removeItem(STORAGE_TOKEN_KEY);
      localStorage.removeItem(STORAGE_USER_KEY);
      set({ token: null, user: null, isAuthenticated: false });
    },

    updateTenant: (tenantId: string) => {
      set((state) => {
        if (!state.user) return state;
        const updatedUser = { ...state.user, tenant_id: tenantId };
        localStorage.setItem(STORAGE_USER_KEY, JSON.stringify(updatedUser));
        return { user: updatedUser };
      });
    },
  };
});
