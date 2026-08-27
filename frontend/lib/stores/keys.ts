"use client";

import { create } from "zustand";
import { keysApi } from "../api";
import { KeyStatus } from "../api/types";

interface KeyVaultState {
  status: KeyStatus[];
  loading: boolean;
  fetch: () => Promise<void>;
  connect: (providerId: string, apiKey: string) => Promise<void>;
  disconnect: (providerId: string) => Promise<void>;
}

export const useKeyVaultStore = create<KeyVaultState>((set) => ({
  status: [],
  loading: false,

  fetch: async () => {
    set({ loading: true });
    try {
      const status = await keysApi.list();
      set({ status, loading: false });
    } catch (e) {
      set({ loading: false });
      throw e;
    }
  },

  connect: async (providerId, apiKey) => {
    await keysApi.connect(providerId, apiKey);
    const status = await keysApi.list();
    set({ status });
  },

  disconnect: async (providerId) => {
    await keysApi.disconnect(providerId);
    const status = await keysApi.list();
    set({ status });
  },
}));
