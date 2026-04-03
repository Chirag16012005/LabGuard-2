import { create } from "zustand";
import { AuthState, User } from "@/types/auth";
import { clearPersistedAuth, getPersistedToken, getPersistedUser, persistAuth } from "@/lib/api-client";

const initialUser = getPersistedUser();
const initialToken = getPersistedToken();
const initialAuthenticated = Boolean(initialUser && initialToken);

export const useAuthStore = create<AuthState>((set) => ({
  user: initialUser,
  token: initialToken,
  isAuthenticated: initialAuthenticated,

  setUser: (user: User, token: string) => {
    persistAuth(user, token);
    set({
      user,
      token,
      isAuthenticated: true,
    });
  },

  logout: () => {
    clearPersistedAuth();
    set({
      user: null,
      token: null,
      isAuthenticated: false,
    });
  },
}));
