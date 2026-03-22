import type { LoginRequest, SignupRequest, TokenResponse, User } from "../types/auth";
import { authApi } from "./api";

export function getAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("access_token");
}

export function isAuthenticated(): boolean {
  return !!getAccessToken();
}

export async function login(credentials: LoginRequest): Promise<TokenResponse> {
  const tenantId = credentials.tenant_id || localStorage.getItem("tenant_id");
  const payload = { ...credentials, tenant_id: tenantId };
  const data = await authApi.post<TokenResponse>("/auth/login", payload);
  localStorage.setItem("access_token", data.access_token);
  localStorage.setItem("refresh_token", data.refresh_token);
  if (tenantId) localStorage.setItem("tenant_id", tenantId);
  return data;
}

export async function signup(data: SignupRequest): Promise<User> {
  return authApi.post<User>("/auth/register", data);
}

export function logout(): void {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
  window.location.href = "/login";
}

export function getCurrentUser(): User | null {
  const token = getAccessToken();
  if (!token) return null;
  try {
    const payload = JSON.parse(atob(token.split(".")[1]));
    return {
      id: payload.sub,
      email: "",
      username: "",
      status: "active",
      roles: payload.roles || [],
    };
  } catch {
    return null;
  }
}
