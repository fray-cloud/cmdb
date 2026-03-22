// Types
export type { PaginatedResponse, ApiError } from "./types/common";
export type { LoginRequest, TokenResponse, User, SignupRequest } from "./types/auth";
export type {
  Prefix,
  IPAddress,
  VRF,
  VLAN,
  IPRange,
  RIR,
  ASN,
  FHRPGroup,
  RouteTarget,
  VLANGroup,
  Service,
  SearchResult,
  GlobalSearchResponse,
  ChangeLogEntry,
  JournalEntry,
} from "./types/ipam";

// API
export { api, authApi } from "./lib/api";
export {
  prefixApi,
  ipAddressApi,
  vrfApi,
  vlanApi,
  ipRangeApi,
  rirApi,
  asnApi,
  fhrpGroupApi,
  routeTargetApi,
  vlanGroupApi,
  serviceApi,
  searchApi,
  changelogApi,
  journalApi,
} from "./lib/api-client";

// Auth
export { getAccessToken, isAuthenticated, login, signup, logout, getCurrentUser } from "./lib/auth";
export { AuthProvider, useAuth } from "./hooks/use-auth";
