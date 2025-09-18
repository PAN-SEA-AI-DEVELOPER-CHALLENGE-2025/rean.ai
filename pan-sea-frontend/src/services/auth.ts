import { apiFetch } from "@/lib/http";
import {
  RegisterRequest,
  RegisterRequestSchema,
  RegisterResponse,
  RegisterResponseSchema,
  LoginRequest,
  LoginRequestSchema,
  LoginResponse,
  LoginResponseSchema
} from "@/lib/schemas/auth";
import { ProfileResponse } from "@/types/api";

export async function registerUser(payload: RegisterRequest): Promise<RegisterResponse> {
  const body = RegisterRequestSchema.parse(payload);
  return apiFetch<RegisterResponse>("/auth/register", {
    method: "POST",
    body,
    schema: RegisterResponseSchema,
  });
}

export async function loginUser(payload: LoginRequest): Promise<LoginResponse> {
  // Validate before sending
  const body = LoginRequestSchema.parse(payload);
  return apiFetch<LoginResponse>("/auth/login", {
    method: "POST",
    body,
    schema: LoginResponseSchema,
  });
}

// Fetch current user's profile via our Next.js API proxy
export async function fetchMyProfile(limit: number = 50): Promise<ProfileResponse> {
  return apiFetch<ProfileResponse>(`/auth/me/profile?limit=${encodeURIComponent(String(limit))}`, {
    method: "GET",
    ttlMs: 10000,
  });
}
