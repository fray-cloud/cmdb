"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter, useParams } from "next/navigation";
import type { VRF } from "@cmdb/shared";
import { vrfApi } from "@cmdb/shared";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardAction,
} from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
  DialogTrigger,
  DialogClose,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Skeleton } from "@/components/ui/skeleton";
import { ArrowLeft, Pencil, Trash2 } from "lucide-react";
import { useState } from "react";

export default function VRFDetailPage() {
  const router = useRouter();
  const params = useParams<{ id: string }>();
  const queryClient = useQueryClient();
  const [editing, setEditing] = useState(false);
  const [editData, setEditData] = useState<Partial<VRF & { import_targets_str: string; export_targets_str: string }>>({});

  const { data: vrf, isLoading } = useQuery({
    queryKey: ["vrf", params.id],
    queryFn: () => vrfApi.get(params.id),
  });

  const updateMutation = useMutation({
    mutationFn: (data: Partial<VRF>) => vrfApi.update(params.id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["vrf", params.id] });
      queryClient.invalidateQueries({ queryKey: ["vrfs"] });
      setEditing(false);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: () => vrfApi.delete(params.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["vrfs"] });
      router.push("/ipam/vrfs");
    },
  });

  function startEditing() {
    if (!vrf) return;
    setEditData({
      name: vrf.name,
      rd: vrf.rd,
      tenant_id: vrf.tenant_id,
      description: vrf.description,
      import_targets_str: vrf.import_targets.join(", "),
      export_targets_str: vrf.export_targets.join(", "),
    });
    setEditing(true);
  }

  function handleSubmit() {
    const importStr = (editData as { import_targets_str?: string }).import_targets_str ?? "";
    const exportStr = (editData as { export_targets_str?: string }).export_targets_str ?? "";
    updateMutation.mutate({
      name: editData.name,
      rd: editData.rd,
      import_targets: importStr ? importStr.split(",").map((s) => s.trim()) : [],
      export_targets: exportStr ? exportStr.split(",").map((s) => s.trim()) : [],
      tenant_id: editData.tenant_id,
      description: editData.description,
    });
  }

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (!vrf) {
    return <p className="text-muted-foreground">VRF not found.</p>;
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="sm" onClick={() => router.push("/ipam/vrfs")}>
          <ArrowLeft />
          Back
        </Button>
        <h1 className="text-2xl font-bold tracking-tight">{vrf.name}</h1>
      </div>

      {editing ? (
        <Card>
          <CardHeader>
            <CardTitle>Edit VRF</CardTitle>
          </CardHeader>
          <CardContent>
            <form
              className="grid gap-4 sm:grid-cols-2"
              onSubmit={(e) => {
                e.preventDefault();
                handleSubmit();
              }}
            >
              <div className="space-y-2">
                <Label htmlFor="name">Name</Label>
                <Input
                  id="name"
                  value={editData.name ?? ""}
                  onChange={(e) => setEditData({ ...editData, name: e.target.value })}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="rd">RD</Label>
                <Input
                  id="rd"
                  value={editData.rd ?? ""}
                  onChange={(e) => setEditData({ ...editData, rd: e.target.value || null })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="import_targets">Import Targets (comma separated)</Label>
                <Input
                  id="import_targets"
                  value={(editData as { import_targets_str?: string }).import_targets_str ?? ""}
                  onChange={(e) =>
                    setEditData({ ...editData, import_targets_str: e.target.value })
                  }
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="export_targets">Export Targets (comma separated)</Label>
                <Input
                  id="export_targets"
                  value={(editData as { export_targets_str?: string }).export_targets_str ?? ""}
                  onChange={(e) =>
                    setEditData({ ...editData, export_targets_str: e.target.value })
                  }
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="tenant_id">Tenant ID</Label>
                <Input
                  id="tenant_id"
                  value={editData.tenant_id ?? ""}
                  onChange={(e) =>
                    setEditData({ ...editData, tenant_id: e.target.value || null })
                  }
                />
              </div>
              <div className="space-y-2 sm:col-span-2">
                <Label htmlFor="description">Description</Label>
                <Textarea
                  id="description"
                  value={editData.description ?? ""}
                  onChange={(e) => setEditData({ ...editData, description: e.target.value })}
                />
              </div>
              <div className="flex gap-2 sm:col-span-2">
                <Button type="submit" disabled={updateMutation.isPending}>
                  {updateMutation.isPending ? "Saving..." : "Save"}
                </Button>
                <Button type="button" variant="outline" onClick={() => setEditing(false)}>
                  Cancel
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardHeader>
            <CardTitle>VRF Details</CardTitle>
            <CardAction>
              <div className="flex gap-2">
                <Button variant="outline" size="sm" onClick={startEditing}>
                  <Pencil />
                  Edit
                </Button>
                <Dialog>
                  <DialogTrigger
                    render={
                      <Button variant="destructive" size="sm">
                        <Trash2 />
                        Delete
                      </Button>
                    }
                  />
                  <DialogContent>
                    <DialogHeader>
                      <DialogTitle>Delete VRF</DialogTitle>
                      <DialogDescription>
                        Are you sure you want to delete {vrf.name}? This action cannot be
                        undone.
                      </DialogDescription>
                    </DialogHeader>
                    <DialogFooter>
                      <DialogClose render={<Button variant="outline" />}>Cancel</DialogClose>
                      <Button
                        variant="destructive"
                        onClick={() => deleteMutation.mutate()}
                        disabled={deleteMutation.isPending}
                      >
                        {deleteMutation.isPending ? "Deleting..." : "Delete"}
                      </Button>
                    </DialogFooter>
                  </DialogContent>
                </Dialog>
              </div>
            </CardAction>
          </CardHeader>
          <CardContent>
            <dl className="grid gap-4 sm:grid-cols-2">
              <div>
                <dt className="text-sm font-medium text-muted-foreground">Name</dt>
                <dd className="mt-1">{vrf.name}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-muted-foreground">RD</dt>
                <dd className="mt-1">{vrf.rd ?? "-"}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-muted-foreground">Import Targets</dt>
                <dd className="mt-1">{vrf.import_targets.join(", ") || "-"}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-muted-foreground">Export Targets</dt>
                <dd className="mt-1">{vrf.export_targets.join(", ") || "-"}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-muted-foreground">Tenant</dt>
                <dd className="mt-1">{vrf.tenant_id ?? "-"}</dd>
              </div>
              <div className="sm:col-span-2">
                <dt className="text-sm font-medium text-muted-foreground">Description</dt>
                <dd className="mt-1">{vrf.description || "-"}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-muted-foreground">Created</dt>
                <dd className="mt-1">{new Date(vrf.created_at).toLocaleString()}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-muted-foreground">Updated</dt>
                <dd className="mt-1">{new Date(vrf.updated_at).toLocaleString()}</dd>
              </div>
            </dl>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
