export interface Prefix {
  id: string;
  network: string;
  vrf_id: string | null;
  vlan_id: string | null;
  status: string;
  role: string | null;
  tenant_id: string | null;
  description: string;
  custom_fields: Record<string, unknown>;
  tags: string[];
  created_at: string;
  updated_at: string;
}

export interface IPAddress {
  id: string;
  address: string;
  vrf_id: string | null;
  status: string;
  dns_name: string;
  tenant_id: string | null;
  description: string;
  custom_fields: Record<string, unknown>;
  tags: string[];
  created_at: string;
  updated_at: string;
}

export interface VRF {
  id: string;
  name: string;
  rd: string | null;
  import_targets: string[];
  export_targets: string[];
  tenant_id: string | null;
  description: string;
  custom_fields: Record<string, unknown>;
  tags: string[];
  created_at: string;
  updated_at: string;
}

export interface VLAN {
  id: string;
  vid: number;
  name: string;
  group_id: string | null;
  status: string;
  role: string | null;
  tenant_id: string | null;
  description: string;
  custom_fields: Record<string, unknown>;
  tags: string[];
  created_at: string;
  updated_at: string;
}

export interface IPRange {
  id: string;
  start_address: string;
  end_address: string;
  vrf_id: string | null;
  status: string;
  tenant_id: string | null;
  description: string;
  custom_fields: Record<string, unknown>;
  tags: string[];
  created_at: string;
  updated_at: string;
}

export interface RIR {
  id: string;
  name: string;
  is_private: boolean;
  description: string;
  custom_fields: Record<string, unknown>;
  tags: string[];
  created_at: string;
  updated_at: string;
}

export interface ASN {
  id: string;
  asn: number;
  rir_id: string | null;
  tenant_id: string | null;
  description: string;
  custom_fields: Record<string, unknown>;
  tags: string[];
  created_at: string;
  updated_at: string;
}

export interface FHRPGroup {
  id: string;
  protocol: string;
  group_id_value: number;
  auth_type: string;
  name: string;
  description: string;
  custom_fields: Record<string, unknown>;
  tags: string[];
  created_at: string;
  updated_at: string;
}

export interface RouteTarget {
  id: string;
  name: string;
  tenant_id: string | null;
  description: string;
  custom_fields: Record<string, unknown>;
  tags: string[];
  created_at: string;
  updated_at: string;
}

export interface VLANGroup {
  id: string;
  name: string;
  slug: string;
  min_vid: number;
  max_vid: number;
  tenant_id: string | null;
  description: string;
  custom_fields: Record<string, unknown>;
  tags: string[];
  created_at: string;
  updated_at: string;
}

export interface Service {
  id: string;
  name: string;
  protocol: string;
  ports: number[];
  ip_addresses: string[];
  description: string;
  custom_fields: Record<string, unknown>;
  tags: string[];
  created_at: string;
  updated_at: string;
}

export interface SearchResult {
  entity_type: string;
  entity_id: string;
  display_text: string;
  description: string;
  relevance: number;
}

export interface GlobalSearchResponse {
  results: SearchResult[];
  total: number;
}

export interface ChangeLogEntry {
  id: number;
  aggregate_id: string;
  aggregate_type: string;
  action: string;
  event_type: string;
  user_id: string | null;
  tenant_id: string | null;
  correlation_id: string | null;
  timestamp: string;
}

export interface JournalEntry {
  id: string;
  object_type: string;
  object_id: string;
  entry_type: "info" | "success" | "warning" | "danger";
  comment: string;
  user_id: string | null;
  tenant_id: string | null;
  created_at: string;
}
