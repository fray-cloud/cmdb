"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter, useParams } from "next/navigation";
import type { Prefix } from "@cmdb/shared";
import { prefixApi } from "@cmdb/shared";
import { StatusBadge } from "@/components/status-badge";
import { ChangelogTimeline } from "@/components/history/changelog-timeline";
import { JournalEntries } from "@/components/journal/journal-entries";
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
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { ArrowLeft, Pencil, Trash2 } from "lucide-react";
import { useState } from "react";

export default function PrefixDetailPage() {
  const router = useRouter();
  const params = useParams<{ id: string }>();
  const queryClient = useQueryClient();
  const [editing, setEditing] = useState(false);
  const [editData, setEditData] = useState<Partial<Prefix>>({});

  const { data: prefix, isLoading } = useQuery({
    queryKey: ["prefix", params.id],
    queryFn: () => prefixApi.get(params.id),
  });

  const updateMutation = useMutation({
    mutationFn: (data: Partial<Prefix>) => prefixApi.update(params.id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["prefix", params.id] });
      queryClient.invalidateQueries({ queryKey: ["prefixes"] });
      setEditing(false);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: () => prefixApi.delete(params.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["prefixes"] });
      router.push("/ipam/prefixes");
    },
  });

  function startEditing() {
    if (!prefix) return;
    setEditData({
      network: prefix.network,
      status: prefix.status,
      vrf_id: prefix.vrf_id,
      vlan_id: prefix.vlan_id,
      role: prefix.role,
      tenant_id: prefix.tenant_id,
      description: prefix.description,
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

  if (!prefix) {
    return <p className="text-muted-foreground">Prefix not found.</p>;
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="sm" onClick={() => router.push("/ipam/prefixes")}>
          <ArrowLeft />
          Back
        </Button>
        <h1 className="text-2xl font-bold tracking-tight">{prefix.network}</h1>
        <StatusBadge status={prefix.status} />
      </div>

      <Tabs defaultValue="details">
        <TabsList>
          <TabsTrigger value="details">Details</TabsTrigger>
          <TabsTrigger value="history">History</TabsTrigger>
          <TabsTrigger value="journal">Journal</TabsTrigger>
        </TabsList>

        <TabsContent value="details">
          {editing ? (
            <Card>
              <CardHeader>
                <CardTitle>Edit Prefix</CardTitle>
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
                    <Label htmlFor="network">Network</Label>
                    <Input
                      id="network"
                      value={editData.network ?? ""}
                      onChange={(e) => setEditData({ ...editData, network: e.target.value })}
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
                        <SelectItem value="container">Container</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="vrf_id">VRF ID</Label>
                    <Input
                      id="vrf_id"
                      value={editData.vrf_id ?? ""}
                      onChange={(e) =>
                        setEditData({ ...editData, vrf_id: e.target.value || null })
                      }
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="vlan_id">VLAN ID</Label>
                    <Input
                      id="vlan_id"
                      value={editData.vlan_id ?? ""}
                      onChange={(e) =>
                        setEditData({ ...editData, vlan_id: e.target.value || null })
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
                <CardTitle>Prefix Details</CardTitle>
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
                          <DialogTitle>Delete Prefix</DialogTitle>
                          <DialogDescription>
                            Are you sure you want to delete {prefix.network}? This action cannot be
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
                    <dt className="text-sm font-medium text-muted-foreground">Network</dt>
                    <dd className="mt-1">{prefix.network}</dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-muted-foreground">Status</dt>
                    <dd className="mt-1">
                      <StatusBadge status={prefix.status} />
                    </dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-muted-foreground">VRF</dt>
                    <dd className="mt-1">{prefix.vrf_id ?? "-"}</dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-muted-foreground">VLAN</dt>
                    <dd className="mt-1">{prefix.vlan_id ?? "-"}</dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-muted-foreground">Role</dt>
                    <dd className="mt-1">{prefix.role ?? "-"}</dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-muted-foreground">Tenant</dt>
                    <dd className="mt-1">{prefix.tenant_id ?? "-"}</dd>
                  </div>
                  <div className="sm:col-span-2">
                    <dt className="text-sm font-medium text-muted-foreground">Description</dt>
                    <dd className="mt-1">{prefix.description || "-"}</dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-muted-foreground">Created</dt>
                    <dd className="mt-1">{new Date(prefix.created_at).toLocaleString()}</dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-muted-foreground">Updated</dt>
                    <dd className="mt-1">{new Date(prefix.updated_at).toLocaleString()}</dd>
                  </div>
                </dl>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="history">
          <Card>
            <CardHeader>
              <CardTitle>Change History</CardTitle>
            </CardHeader>
            <CardContent>
              <ChangelogTimeline objectId={params.id} />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="journal">
          <Card>
            <CardHeader>
              <CardTitle>Journal</CardTitle>
            </CardHeader>
            <CardContent>
              <JournalEntries objectType="prefix" objectId={params.id} />
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
