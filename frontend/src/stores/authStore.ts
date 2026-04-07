// ── SentinelClaw Auth Store (Zustand) ───────────────────────────────
//
// Token wird als HttpOnly Cookie verwaltet (nicht per JS zugänglich).
// Der Store verwaltet nur User-Daten und Auth-Status.

import { create } from 'zustand';

export interface User {
  id: string;
  email: string;
  display_name: string;
  role: string;
}

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  mustChangePassword: boolean;
  login: (user: User, mustChangePassword?: boolean) => void;
  clearMustChangePassword: () => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: JSON.parse(localStorage.getItem('sc_user') || 'null'),
  isAuthenticated: !!localStorage.getItem('sc_user'),
  mustChangePassword: localStorage.getItem('sc_must_change') === 'true',

  login: (user, mustChangePassword = false) => {
    localStorage.setItem('sc_user', JSON.stringify(user));
    if (mustChangePassword) {
      localStorage.setItem('sc_must_change', 'true');
    } else {
      localStorage.removeItem('sc_must_change');
    }
    set({ user, isAuthenticated: true, mustChangePassword });
  },

  clearMustChangePassword: () => {
    localStorage.removeItem('sc_must_change');
    set({ mustChangePassword: false });
  },

  logout: () => {
    localStorage.removeItem('sc_user');
    localStorage.removeItem('sc_must_change');
    set({ user: null, isAuthenticated: false, mustChangePassword: false });
  },
}));
