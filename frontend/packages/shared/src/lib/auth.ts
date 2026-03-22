import type { LoginRequest, SignupRequest, TokenResponse, User } from "../types/auth";
import { api } from "./api";

export function getAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("access_token");
}

export function isAuthenticated(): boolean {
  return !!getAccessToken();
}

export async function login(credentials: LoginRequest): Promise<TokenResponse> {
  const data = await api.post<TokenResponse>("/auth/login", credentials);
  localStorage.setItem("access_token", data.access_token);
  localStorage.setItem("refresh_token", data.refresh_token);
  return data;
}

export async function signup(data: SignupRequest): Promise<User> {
  return api.post<User>("/auth/users", data);
}

export function logout(): void {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
  window.location.href = "/login";
}

export async function getCurrentUser(): Promise<User> {
  return api.get<User>("/auth/me");
}
