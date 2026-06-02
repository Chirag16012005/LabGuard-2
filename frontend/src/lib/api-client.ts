import axios, { AxiosRequestHeaders } from "axios";

import { LoginCredentials, LoginResponse, RegisterCredentials, User } from "@/types/auth";

const TOKEN_STORAGE_KEY = "labguard_token";
const USER_STORAGE_KEY = "labguard_user";
const TOKEN_KEY = "token";

type ApiEnvelope<T> = {
  message?: string;
  data: T;
};

type AuthPayload = {
  user_id: string;
  email: string;
  access_token: string;
  token_type: string;
};

type MePayload = {
  user: {
    id: string;
    email: string;
    full_name?: string;
    role: "student" | "teacher";
  };
};
const baseURL = process.env.NEXT_PUBLIC_API_BASE_URL;
if (!baseURL && process.env.NODE_ENV === "production") {
  throw new Error("NEXT_PUBLIC_API_BASE_URL is not set");
}

export const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8001/api/v1",
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 300000, // 30 second timeout for requests (in milliseconds)
});

apiClient.interceptors.request.use((config) => {
  // Add request logging with timing for debugging
  if (typeof window !== "undefined" && config.url) {
    // const startTime = performance.now();
    // config.metadata = { startTime };
    console.debug(
      `[API] ${config.method?.toUpperCase()} ${config.url} (timeout: ${config.timeout}ms)`,
      new Date().toLocaleTimeString()
    );
  }

  if (typeof window !== "undefined") 
  {
    const url = String(config.url ?? "");
    const isAuthLoginOrRegister = url.includes("/auth/login") || url.includes("/auth/register");
    if (isAuthLoginOrRegister) 
    return config;

    const headers = (config.headers ?? {}) as AxiosRequestHeaders;
    const existingAuth = headers.Authorization ?? headers.authorization;
    if (!existingAuth) 
    {
      const token = localStorage.getItem(TOKEN_STORAGE_KEY);
      if (token) 
      {
        headers.Authorization = `Bearer ${token}`;
        config.headers = headers;
      }
    }
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => {
    if (typeof window !== "undefined" && response.config?.url) {
      console.debug("[API] Success:", response.status, response.config.url);
    }
    return response;
  },
  (error) => {
    const status = error?.response?.status;
    const url = String(error?.config?.url ?? "");
    const isAuthLoginOrRegister = url.includes("/auth/login") || url.includes("/auth/register");
    
    // Log errors for debugging
    if (typeof window !== "undefined") {
      console.error("[API] Error:", status, url, error?.message);
    }
    
    // Only redirect on 401 if we're not already on login page and it's a protected endpoint
    if (status === 401 && typeof window !== "undefined" && !isAuthLoginOrRegister && window.location.pathname !== "/login") {
      clearPersistedAuth();
      // Use a flag to prevent multiple redirects
      const redirectFlag = sessionStorage.getItem("_redirecting_to_login");
      if (!redirectFlag) {
        sessionStorage.setItem("_redirecting_to_login", "true");
        setTimeout(() => {
          window.location.href = "/login";
        }, 100);
      }
    }

    const detail = error?.response?.data?.detail;
    const message = Array.isArray(detail)
      ? detail.map((item: { msg?: string }) => item.msg).filter(Boolean).join(", ")
      : typeof detail === "string"
        ? detail
        : error?.message || "Request failed";
    return Promise.reject(new Error(message));
  }
);

function mapBackendUser(user: MePayload["user"]): User {
  return {
    id: user.id,
    email: user.email,
    name: user.full_name || user.email,
    role: user.role,
  };
}

export function persistAuth(user: User, token: string): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(TOKEN_STORAGE_KEY, token);
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(user));
}

export function clearPersistedAuth(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(TOKEN_STORAGE_KEY);
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_STORAGE_KEY);
}

export function getPersistedToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY) ?? localStorage.getItem(TOKEN_STORAGE_KEY);
}

export function getPersistedUser(): User | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem(USER_STORAGE_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as User;
  } catch {
    return null;
  }
}

export async function getMe(): Promise<User> {
  const response = await apiClient.get<ApiEnvelope<MePayload>>("/auth/me");
  return mapBackendUser(response.data.data.user);
}

export async function loginApi(credentials: LoginCredentials): Promise<LoginResponse> {
  const response = await apiClient.post<ApiEnvelope<AuthPayload>>("/auth/login", {
    email: credentials.email,
    password: credentials.password,
  });

  const token = response.data.data.access_token;
  const me = await apiClient.get<ApiEnvelope<MePayload>>("/auth/me", {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  return {
    token,
    user: mapBackendUser(me.data.data.user),
  };
}

export async function registerApi(
  credentials: RegisterCredentials
): Promise<LoginResponse> {
  const response = await apiClient.post<ApiEnvelope<AuthPayload>>("/auth/register", {
    email: credentials.email,
    password: credentials.password,
    full_name: credentials.name,
    role: credentials.role,
  });

  const token = response.data.data.access_token;
  const me = await apiClient.get<ApiEnvelope<MePayload>>("/auth/me", {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  return {
    token,
    user: mapBackendUser(me.data.data.user),
  };
}

export async function logoutApi(): Promise<void> {
  if (typeof window === "undefined") return;
  const token = getPersistedToken();
  if (!token) return;
  await apiClient.post("/auth/logout");
}

export async function changePasswordApi(input: {
  currentPassword: string;
  newPassword: string;
}): Promise<{ loggedOut?: boolean }> {
  const response = await apiClient.post<ApiEnvelope<{ logged_out?: boolean }>>(
    "/auth/change-password",
    {
      current_password: input.currentPassword,
      new_password: input.newPassword,
    }
  );

  return {
    loggedOut: response.data.data?.logged_out,
  };
}

export async function forgotPasswordApi(email: string): Promise<void> {
  await apiClient.post("/auth/forgot-password", {
    email,
  });
}

export async function resetPasswordApi(token: string, newPassword: string): Promise<void> {
  await apiClient.post("/auth/reset-password", {
    token,
    new_password: newPassword,
  });
}
