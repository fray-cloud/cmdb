"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { journalApi } from "@cmdb/shared";
import type { JournalEntry } from "@cmdb/shared";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import { Plus, X } from "lucide-react";

const ENTRY_TYPE_STYLES: Record<string, { label: string; className: string }> = {
  info: { label: "Info", className: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200" },
  success: { label: "Success", className: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200" },
  warning: { label: "Warning", className: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200" },
  danger: { label: "Danger", className: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200" },
};

interface JournalEntriesProps {
  objectType: string;
  objectId: string;
}

export function JournalEntries({ objectType, objectId }: JournalEntriesProps) {
  const queryClient = useQueryClient();
  const [entryType, setEntryType] = useState<string>("info");
  const [comment, setComment] = useState("");

  const { data, isLoading } = useQuery({
    queryKey: ["journal", objectType, objectId],
    queryFn: () => journalApi.list({ object_type: objectType, object_id: objectId }),
  });

  const createMutation = useMutation({
    mutationFn: (data: { object_type: string; object_id: string; entry_type: string; comment: string }) =>
      journalApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["journal", objectType, objectId] });
      setComment("");
      setEntryType("info");
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => journalApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["journal", objectType, objectId] });
    },
  });

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!comment.trim()) return;
    createMutation.mutate({
      object_type: objectType,
      object_id: objectId,
      entry_type: entryType,
      comment: comment.trim(),
    });
  }

  if (isLoading) {
    return (
      <div className="space-y-4 py-4">
        <Skeleton className="h-24 w-full" />
        <Skeleton className="h-16 w-full" />
        <Skeleton className="h-16 w-full" />
      </div>
    );
  }

  const entries = data?.items ?? [];

  return (
    <div className="space-y-4 py-4">
      {/* Add Note Form */}
      <form onSubmit={handleSubmit} className="space-y-3 rounded-lg border p-4">
        <p className="text-sm font-medium">Add Note</p>
        <div className="flex gap-2">
          <Select value={entryType} onValueChange={(val) => val && setEntryType(val)}>
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="info">Info</SelectItem>
              <SelectItem value="success">Success</SelectItem>
              <SelectItem value="warning">Warning</SelectItem>
              <SelectItem value="danger">Danger</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <Textarea
          value={comment}
          onChange={(e) => setComment(e.target.value)}
          placeholder="Write a note..."
          rows={3}
        />
        <Button type="submit" size="sm" disabled={createMutation.isPending || !comment.trim()}>
          <Plus className="h-4 w-4" />
          {createMutation.isPending ? "Adding..." : "Add Note"}
        </Button>
      </form>

      {/* Entries List */}
      {entries.length === 0 ? (
        <p className="py-4 text-center text-sm text-muted-foreground">No journal entries yet.</p>
      ) : (
        <div className="space-y-3">
          {entries.map((entry: JournalEntry) => {
            const style = ENTRY_TYPE_STYLES[entry.entry_type] ?? ENTRY_TYPE_STYLES.info;

            return (
              <div
                key={entry.id}
                className="group relative flex gap-3 rounded-lg border p-3"
              >
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span
                      className={cn(
                        "inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium",
                        style.className,
                      )}
                    >
                      {style.label}
                    </span>
                    <span className="text-xs text-muted-foreground">
                      {new Date(entry.created_at).toLocaleString()}
                    </span>
                    {entry.user_id && (
                      <span className="text-xs text-muted-foreground">
                        by {entry.user_id}
                      </span>
                    )}
                  </div>
                  <p className="text-sm whitespace-pre-wrap">{entry.comment}</p>
                </div>
                <Button
                  variant="ghost"
                  size="icon-sm"
                  className="shrink-0 opacity-0 group-hover:opacity-100 transition-opacity"
                  onClick={() => deleteMutation.mutate(entry.id)}
                  disabled={deleteMutation.isPending}
                >
                  <X className="h-3 w-3" />
                  <span className="sr-only">Delete</span>
                </Button>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
