"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter, useParams } from "next/navigation";
import type { VLAN } from "@cmdb/shared";
import { vlanApi } from "@cmdb/shared";
import { StatusBadge } from "@/components/status-badge";
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { ArrowLeft, Pencil, Trash2 } from "lucide-react";
import { useState } from "react";

export default function VLANDetailPage() {
  const router = useRouter();
  const params = useParams<{ id: string }>();
  const queryClient = useQueryClient();
  const [editing, setEditing] = useState(false);
  const [editData, setEditData] = useState<Partial<VLAN>>({});

  const { data: vlan, isLoading } = useQuery({
    queryKey: ["vlan", params.id],
    queryFn: () => vlanApi.get(params.id),
  });

  const updateMutation = useMutation({
    mutationFn: (data: Partial<VLAN>) => vlanApi.update(params.id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["vlan", params.id] });
      queryClient.invalidateQueries({ queryKey: ["vlans"] });
      setEditing(false);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: () => vlanApi.delete(params.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["vlans"] });
      router.push("/ipam/vlans");
    },
  });

  function startEditing() {
    if (!vlan) return;
    setEditData({
      vid: vlan.vid,
      name: vlan.name,
      status: vlan.status,
      group_id: vlan.group_id,
      role: vlan.role,
      tenant_id: vlan.tenant_id,
      description: vlan.description,
    });
    setEditing(true);
  }

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (!vlan) {
    return <p className="text-muted-foreground">VLAN not found.</p>;
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="sm" onClick={() => router.push("/ipam/vlans")}>
          <ArrowLeft />
          Back
        </Button>
        <h1 className="text-2xl font-bold tracking-tight">
          VLAN {vlan.vid} - {vlan.name}
        </h1>
        <StatusBadge status={vlan.status} />
      </div>

      {editing ? (
        <Card>
          <CardHeader>
            <CardTitle>Edit VLAN</CardTitle>
          </CardHeader>
          <CardContent>
            <form
              className="grid gap-4 sm:grid-cols-2"
              onSubmit={(e) => {
                e.preventDefault();
                updateMutation.mutate(editData);
              }}
            >
              <div className="space-y-2">
                <Label htmlFor="vid">VID</Label>
                <Input
                  id="vid"
                  type="number"
                  value={editData.vid ?? ""}
                  onChange={(e) =>
                    setEditData({ ...editData, vid: parseInt(e.target.value) || 0 })
                  }
                  required
                />
              </div>
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
                <Label>Status</Label>
                <Select
                  value={editData.status}
                  onValueChange={(val) => val && setEditData({ ...editData, status: val })}
                >
                  <SelectTrigger className="w-full">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="active">Active</SelectItem>
                    <SelectItem value="reserved">Reserved</SelectItem>
                    <SelectItem value="deprecated">Deprecated</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="group_id">Group ID</Label>
                <Input
                  id="group_id"
                  value={editData.group_id ?? ""}
                  onChange={(e) =>
                    setEditData({ ...editData, group_id: e.target.value || null })
                  }
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="role">Role</Label>
                <Input
                  id="role"
                  value={editData.role ?? ""}
                  onChange={(e) =>
                    setEditData({ ...editData, role: e.target.value || null })
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
            <CardTitle>VLAN Details</CardTitle>
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
                      <DialogTitle>Delete VLAN</DialogTitle>
                      <DialogDescription>
                        Are you sure you want to delete VLAN {vlan.vid} ({vlan.name})? This
                        action cannot be undone.
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
                <dt className="text-sm font-medium text-muted-foreground">VID</dt>
                <dd className="mt-1">{vlan.vid}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-muted-foreground">Name</dt>
                <dd className="mt-1">{vlan.name}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-muted-foreground">Status</dt>
                <dd className="mt-1">
                  <StatusBadge status={vlan.status} />
                </dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-muted-foreground">Group</dt>
                <dd className="mt-1">{vlan.group_id ?? "-"}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-muted-foreground">Role</dt>
                <dd className="mt-1">{vlan.role ?? "-"}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-muted-foreground">Tenant</dt>
                <dd className="mt-1">{vlan.tenant_id ?? "-"}</dd>
              </div>
              <div className="sm:col-span-2">
                <dt className="text-sm font-medium text-muted-foreground">Description</dt>
                <dd className="mt-1">{vlan.description || "-"}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-muted-foreground">Created</dt>
                <dd className="mt-1">{new Date(vlan.created_at).toLocaleString()}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-muted-foreground">Updated</dt>
                <dd className="mt-1">{new Date(vlan.updated_at).toLocaleString()}</dd>
              </div>
            </dl>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
