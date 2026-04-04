// ── SentinelClaw Auth Store (Zustand) ───────────────────────────────

import { create } from 'zustand';

export interface User {
  id: string;
  email: string;
  display_name: string;
  role: string;
}

interface AuthState {
  token: string | null;
  user: User | null;
  isAuthenticated: boolean;
  login: (token: string, user: User) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  token: localStorage.getItem('sc_token'),
  user: JSON.parse(localStorage.getItem('sc_user') || 'null'),
  isAuthenticated: !!localStorage.getItem('sc_token'),

  login: (token, user) => {
    localStorage.setItem('sc_token', token);
    localStorage.setItem('sc_user', JSON.stringify(user));
    set({ token, user, isAuthenticated: true });
  },

  logout: () => {
    localStorage.removeItem('sc_token');
    localStorage.removeItem('sc_user');
    set({ token: null, user: null, isAuthenticated: false });
  },
}));
