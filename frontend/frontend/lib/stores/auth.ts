"use client";

import { create } from "zustand";
import { authApi } from "../api";
import { setAccessToken, logout as apiLogout } from "../api/client";
import { User } from "../api/types";

interface AuthState {
  user: User | null;
  accessToken: string | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (email: string, name: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  fetchMe: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  accessToken: null,
  loading: false,

  login: async (email, password) => {
    set({ loading: true });
    try {
      const res = await authApi.login(email, password);
      setAccessToken(res.access_token);
      set({ user: res.user, accessToken: res.access_token, loading: false });
    } catch (e) {
      set({ loading: false });
      throw e;
    }
  },

  signup: async (email, name, password) => {
    set({ loading: true });
    try {
      const res = await authApi.signup(email, name, password);
      setAccessToken(res.access_token);
      set({ user: res.user, accessToken: res.access_token, loading: false });
    } catch (e) {
      set({ loading: false });
      throw e;
    }
  },

  logout: async () => {
    apiLogout();
    setAccessToken(null);
    set({ user: null, accessToken: null });
  },

  fetchMe: async () => {
    try {
      const user = await authApi.me();
      set({ user });
    } catch {
      set({ user: null, accessToken: null });
    }
  },
}));
