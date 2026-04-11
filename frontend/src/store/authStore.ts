import { create } from "zustand";
import { AuthState, User } from "@/types/auth";
import { clearPersistedAuth, getPersistedToken, getPersistedUser, persistAuth } from "@/lib/api-client";

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: null,
  isAuthenticated: false,
  hydrated: false,

  hydrateFromStorage: () => {
    const user = getPersistedUser();
    const token = getPersistedToken();
    set({
      user,
      token,
      isAuthenticated: Boolean(user && token),
      hydrated: true,
    });
  },

  setUser: (user: User, token: string) => {
    persistAuth(user, token);
    set({
      user,
      token,
      isAuthenticated: true,
      hydrated: true,
    });
  },

  logout: () => {
    clearPersistedAuth();
    set({
      user: null,
      token: null,
      isAuthenticated: false,
      hydrated: true,
    });
  },
}));
