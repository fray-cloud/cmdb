"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { changelogApi } from "@cmdb/shared";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

const ACTION_STYLES: Record<string, { label: string; className: string }> = {
  created: { label: "Created", className: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200" },
  updated: { label: "Updated", className: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200" },
  deleted: { label: "Deleted", className: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200" },
};

interface ChangelogTimelineProps {
  objectId: string;
}

export function ChangelogTimeline({ objectId }: ChangelogTimelineProps) {
  const [limit, setLimit] = useState(10);

  const { data, isLoading } = useQuery({
    queryKey: ["changelog", objectId, limit],
    queryFn: () => changelogApi.getByObject(objectId, { limit, offset: 0 }),
  });

  if (isLoading) {
    return (
      <div className="space-y-4 py-4">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="flex gap-4">
            <Skeleton className="h-3 w-3 shrink-0 rounded-full" />
            <div className="flex-1 space-y-2">
              <Skeleton className="h-4 w-32" />
              <Skeleton className="h-3 w-48" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  const entries = data?.items ?? [];
  const total = data?.total ?? 0;
  const hasMore = entries.length < total;

  if (entries.length === 0) {
    return (
      <p className="py-8 text-center text-sm text-muted-foreground">No history entries found.</p>
    );
  }

  return (
    <div className="py-4">
      <div className="relative">
        {/* Vertical timeline line */}
        <div className="absolute left-[5px] top-2 bottom-2 w-px bg-border" />

        <div className="space-y-6">
          {entries.map((entry) => {
            const actionStyle = ACTION_STYLES[entry.action] ?? {
              label: entry.action,
              className: "bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200",
            };

            return (
              <div key={entry.id} className="relative flex gap-4 pl-0">
                {/* Timeline dot */}
                <div
                  className={cn(
                    "relative z-10 mt-1.5 h-3 w-3 shrink-0 rounded-full border-2 border-background",
                    entry.action === "created" && "bg-green-500",
                    entry.action === "updated" && "bg-blue-500",
                    entry.action === "deleted" && "bg-red-500",
                    !["created", "updated", "deleted"].includes(entry.action) && "bg-gray-500",
                  )}
                />

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className={cn("inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium", actionStyle.className)}>
                      {actionStyle.label}
                    </span>
                    <span className="text-xs text-muted-foreground">
                      {entry.event_type}
                    </span>
                  </div>
                  <div className="mt-1 flex items-center gap-2 text-xs text-muted-foreground">
                    <time>{new Date(entry.timestamp).toLocaleString()}</time>
                    {entry.user_id && (
                      <>
                        <span>by</span>
                        <span className="font-medium text-foreground">{entry.user_id}</span>
                      </>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {hasMore && (
        <div className="mt-4 text-center">
          <Button variant="outline" size="sm" onClick={() => setLimit((prev) => prev + 10)}>
            Load more
          </Button>
        </div>
      )}
    </div>
  );
}
