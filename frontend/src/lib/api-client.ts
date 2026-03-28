import { LoginCredentials, LoginResponse, RegisterCredentials } from "@/types/auth";

export async function loginApi(
  credentials: LoginCredentials
): Promise<LoginResponse> {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      if (
        credentials.email === "admin@labguard.com" &&
        credentials.password === "password123"
      ) {
        resolve({
          user: {
            id: "usr_1",
            email: credentials.email,
            name: "Lab Teacher",
            role: "teacher",
          },
          token: "mock-jwt-token-xyz",
        });
      } else if (credentials.email && credentials.password) {
        // Accept any non-empty credentials for demo purposes
        resolve({
          user: {
            id: "usr_2",
            email: credentials.email,
            name: "Lab Student",
            role: "student",
          },
          token: "mock-jwt-token-abc",
        });
      } else {
        reject(new Error("Invalid email or password. Please try again."));
      }
    }, 1200);
  });
}
export async function registerApi(
  credentials: RegisterCredentials
): Promise<LoginResponse> {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      if (!credentials.email || !credentials.password || !credentials.name || !credentials.role) {
        reject(new Error("Missing required fields."));
        return;
      }
      
      resolve({
        user: {
          id: `usr_${Math.random().toString(36).substring(7)}`,
          email: credentials.email,
          name: credentials.name,
          role: credentials.role as "student" | "teacher",
        },
        token: "mock-jwt-token-register",
      });
    }, 1200);
  });
}
