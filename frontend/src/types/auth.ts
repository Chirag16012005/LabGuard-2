export interface User {
  id: string;
  email: string;
  name: string;
  role: "student" | "teacher";
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterCredentials {
  name: string;
  email: string;
  password: string;
  role: "student" | "teacher";
}

export interface LoginResponse {
  user: User;
  token: string;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  hydrated: boolean;
  hydrateFromStorage: () => void;
  setUser: (user: User, token: string) => void;
  logout: () => void;
}
