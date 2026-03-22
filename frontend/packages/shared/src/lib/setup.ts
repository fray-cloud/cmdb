const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface SetupStatus {
  initialized: boolean;
}

export interface CreateTenantRequest {
  name: string;
  slug: string;
}

export interface TenantResponse {
  id: string;
  name: string;
  slug: string;
  status: string;
  settings: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export async function getSetupStatus(): Promise<SetupStatus> {
  const res = await fetch(`${API_BASE_URL}/setup/status`);
  if (!res.ok) throw new Error("Failed to check setup status");
  return res.json();
}

export async function setupCreateTenant(data: CreateTenantRequest): Promise<TenantResponse> {
  const res = await fetch(`${API_BASE_URL}/setup/create-tenant`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || "Failed to create tenant");
  }
  return res.json();
}
