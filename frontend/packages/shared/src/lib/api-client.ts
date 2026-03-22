import type { PaginatedResponse } from "../types/common";
import type {
  ASN,
  ChangeLogEntry,
  FHRPGroup,
  GlobalSearchResponse,
  IPAddress,
  IPRange,
  JournalEntry,
  Prefix,
  RIR,
  RouteTarget,
  Service,
  VLAN,
  VLANGroup,
  VRF,
} from "../types/ipam";
import { api } from "./api";

function buildQuery(params: Record<string, unknown>): string {
  const entries = Object.entries(params).filter(([, v]) => v != null && v !== "");
  if (entries.length === 0) return "";
  return "?" + entries.map(([k, v]) => `${k}=${encodeURIComponent(String(v))}`).join("&");
}

function createEntityApi<T>(basePath: string) {
  return {
    list: (params: Record<string, unknown> = {}) =>
      api.get<PaginatedResponse<T>>(`${basePath}${buildQuery(params)}`),
    get: (id: string) => api.get<T>(`${basePath}/${id}`),
    create: (data: Partial<T>) => api.post<T>(basePath, data),
    update: (id: string, data: Partial<T>) => api.patch<T>(`${basePath}/${id}`, data),
    delete: (id: string) => api.delete<void>(`${basePath}/${id}`),
  };
}

export const prefixApi = createEntityApi<Prefix>("/api/v1/prefixes");
export const ipAddressApi = createEntityApi<IPAddress>("/api/v1/ip-addresses");
export const vrfApi = createEntityApi<VRF>("/api/v1/vrfs");
export const vlanApi = createEntityApi<VLAN>("/api/v1/vlans");
export const ipRangeApi = createEntityApi<IPRange>("/api/v1/ip-ranges");
export const rirApi = createEntityApi<RIR>("/api/v1/rirs");
export const asnApi = createEntityApi<ASN>("/api/v1/asns");
export const fhrpGroupApi = createEntityApi<FHRPGroup>("/api/v1/fhrp-groups");
export const routeTargetApi = createEntityApi<RouteTarget>("/api/v1/route-targets");
export const vlanGroupApi = createEntityApi<VLANGroup>("/api/v1/vlan-groups");
export const serviceApi = createEntityApi<Service>("/api/v1/services");

export const searchApi = {
  search: (q: string, entityTypes?: string[], offset = 0, limit = 20) => {
    const params: Record<string, unknown> = { q, offset, limit };
    if (entityTypes?.length) params.entity_types = entityTypes.join(",");
    return api.get<GlobalSearchResponse>(`/api/v1/search${buildQuery(params)}`);
  },
};

export const changelogApi = {
  getByObject: (aggregateId: string, params: Record<string, unknown> = {}) =>
    api.get<PaginatedResponse<ChangeLogEntry>>(`/api/v1/event/changelog/${aggregateId}${buildQuery(params)}`),
};

export const journalApi = {
  list: (params: Record<string, unknown> = {}) =>
    api.get<PaginatedResponse<JournalEntry>>(`/api/v1/event/journal-entries${buildQuery(params)}`),
  create: (data: { object_type: string; object_id: string; entry_type: string; comment: string }) =>
    api.post<JournalEntry>("/api/v1/event/journal-entries", data),
  delete: (id: string) => api.delete<void>(`/api/v1/event/journal-entries/${id}`),
};
