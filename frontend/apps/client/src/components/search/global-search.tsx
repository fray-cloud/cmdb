"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import type { SearchResult } from "@cmdb/shared";
import { searchApi } from "@cmdb/shared";
import {
  Dialog,
  DialogContent,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { Loader2, Search } from "lucide-react";

const ENTITY_ROUTES: Record<string, string> = {
  prefix: "/ipam/prefixes",
  ip_address: "/ipam/ip-addresses",
  vrf: "/ipam/vrfs",
  vlan: "/ipam/vlans",
  ip_range: "/ipam/ip-ranges",
  rir: "/ipam/rirs",
  asn: "/ipam/asns",
  fhrp_group: "/ipam/fhrp-groups",
  route_target: "/ipam/route-targets",
  vlan_group: "/ipam/vlan-groups",
  service: "/ipam/services",
};

function getEntityRoute(entityType: string, entityId: string): string {
  const base = ENTITY_ROUTES[entityType] ?? `/ipam/${entityType}s`;
  return `${base}/${entityId}`;
}

function groupByEntityType(results: SearchResult[]): Record<string, SearchResult[]> {
  const grouped: Record<string, SearchResult[]> = {};
  for (const result of results) {
    const key = result.entity_type;
    if (!grouped[key]) grouped[key] = [];
    grouped[key].push(result);
  }
  return grouped;
}

export function GlobalSearch() {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [debouncedQuery, setDebouncedQuery] = useState("");
  const router = useRouter();
  const inputRef = useRef<HTMLInputElement>(null);

  // Debounce the query
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedQuery(query);
    }, 300);
    return () => clearTimeout(timer);
  }, [query]);

  // Cmd+K shortcut
  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setOpen((prev) => !prev);
      }
    }
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, []);

  // Focus input when dialog opens
  useEffect(() => {
    if (open) {
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [open]);

  const handleOpenChange = useCallback((nextOpen: boolean) => {
    setOpen(nextOpen);
    if (!nextOpen) {
      setQuery("");
      setDebouncedQuery("");
    }
  }, []);

  const { data, isLoading } = useQuery({
    queryKey: ["global-search", debouncedQuery],
    queryFn: () => searchApi.search(debouncedQuery),
    enabled: debouncedQuery.length >= 2,
  });

  const navigateToResult = useCallback(
    (result: SearchResult) => {
      setOpen(false);
      router.push(getEntityRoute(result.entity_type, result.entity_id));
    },
    [router],
  );

  const grouped = data?.results ? groupByEntityType(data.results) : {};
  const hasResults = Object.keys(grouped).length > 0;
  const showNoResults = debouncedQuery.length >= 2 && !isLoading && !hasResults;

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent
        className="sm:max-w-lg top-[20%] translate-y-0"
        showCloseButton={false}
      >
        <DialogTitle className="sr-only">Global Search</DialogTitle>
        <div className="flex items-center gap-2 border-b pb-3">
          <Search className="h-4 w-4 shrink-0 text-muted-foreground" />
          <Input
            ref={inputRef}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search prefixes, IPs, VRFs..."
            className="border-0 p-0 shadow-none focus-visible:ring-0"
          />
          {isLoading && <Loader2 className="h-4 w-4 shrink-0 animate-spin text-muted-foreground" />}
        </div>

        <div className="max-h-80 overflow-y-auto">
          {showNoResults && (
            <p className="py-6 text-center text-sm text-muted-foreground">No results found.</p>
          )}

          {debouncedQuery.length < 2 && !hasResults && (
            <p className="py-6 text-center text-sm text-muted-foreground">
              Type at least 2 characters to search.
            </p>
          )}

          {Object.entries(grouped).map(([entityType, results]) => (
            <div key={entityType} className="mb-2">
              <p className="mb-1 px-2 text-xs font-medium uppercase tracking-wider text-muted-foreground">
                {entityType.replace(/_/g, " ")}
              </p>
              {results.map((result) => (
                <button
                  key={`${result.entity_type}-${result.entity_id}`}
                  onClick={() => navigateToResult(result)}
                  className={cn(
                    "flex w-full items-center gap-3 rounded-md px-2 py-2 text-left text-sm",
                    "hover:bg-accent hover:text-accent-foreground",
                    "focus:bg-accent focus:text-accent-foreground focus:outline-none",
                  )}
                >
                  <div className="flex-1 min-w-0">
                    <p className="truncate font-medium">{result.display_text}</p>
                    {result.description && (
                      <p className="truncate text-xs text-muted-foreground">
                        {result.description}
                      </p>
                    )}
                  </div>
                  <Badge variant="secondary">{result.entity_type.replace(/_/g, " ")}</Badge>
                </button>
              ))}
            </div>
          ))}
        </div>
      </DialogContent>
    </Dialog>
  );
}
