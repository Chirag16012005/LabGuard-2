import { create } from "zustand";
import { AuthState, User } from "@/types/auth";

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: null,
  isAuthenticated: false,

  setUser: (user: User, token: string) =>
    set({
      user,
      token,
      isAuthenticated: true,
    }),

  logout: () =>
    set({
      user: null,
      token: null,
      isAuthenticated: false,
    }),
}));
