import { create } from 'zustand';

interface User {
  id: string;
  name: string;
  email?: string;
}

interface AuthStore {
  user: User | null;
  role: "student" | "teacher" | null;
  setUser: (user: User, role: "student" | "teacher") => void;
  logout: () => void;
}

// Default state with mock role = "student"
export const useAuthStore = create<AuthStore>((set) => ({
  user: {
    id: "mock123",
    name: "Mock Student",
  },
  role: "student",
  
  setUser: (user, role) => set({ user, role }),
  
  logout: () => set({ user: null, role: null }),
}));
