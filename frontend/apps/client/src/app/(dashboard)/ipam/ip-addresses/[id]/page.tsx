"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter, useParams } from "next/navigation";
import type { IPAddress } from "@cmdb/shared";
import { ipAddressApi } from "@cmdb/shared";
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

export default function IPAddressDetailPage() {
  const router = useRouter();
  const params = useParams<{ id: string }>();
  const queryClient = useQueryClient();
  const [editing, setEditing] = useState(false);
  const [editData, setEditData] = useState<Partial<IPAddress>>({});

  const { data: ipAddress, isLoading } = useQuery({
    queryKey: ["ip-address", params.id],
    queryFn: () => ipAddressApi.get(params.id),
  });

  const updateMutation = useMutation({
    mutationFn: (data: Partial<IPAddress>) => ipAddressApi.update(params.id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["ip-address", params.id] });
      queryClient.invalidateQueries({ queryKey: ["ip-addresses"] });
      setEditing(false);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: () => ipAddressApi.delete(params.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["ip-addresses"] });
      router.push("/ipam/ip-addresses");
    },
  });

  function startEditing() {
    if (!ipAddress) return;
    setEditData({
      address: ipAddress.address,
      status: ipAddress.status,
      vrf_id: ipAddress.vrf_id,
      dns_name: ipAddress.dns_name,
      tenant_id: ipAddress.tenant_id,
      description: ipAddress.description,
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

  if (!ipAddress) {
    return <p className="text-muted-foreground">IP Address not found.</p>;
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="sm" onClick={() => router.push("/ipam/ip-addresses")}>
          <ArrowLeft />
          Back
        </Button>
        <h1 className="text-2xl font-bold tracking-tight">{ipAddress.address}</h1>
        <StatusBadge status={ipAddress.status} />
      </div>

      {editing ? (
        <Card>
          <CardHeader>
            <CardTitle>Edit IP Address</CardTitle>
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
                <Label htmlFor="address">Address</Label>
                <Input
                  id="address"
                  value={editData.address ?? ""}
                  onChange={(e) => setEditData({ ...editData, address: e.target.value })}
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
                <Label htmlFor="dns_name">DNS Name</Label>
                <Input
                  id="dns_name"
                  value={editData.dns_name ?? ""}
                  onChange={(e) => setEditData({ ...editData, dns_name: e.target.value })}
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
            <CardTitle>IP Address Details</CardTitle>
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
                      <DialogTitle>Delete IP Address</DialogTitle>
                      <DialogDescription>
                        Are you sure you want to delete {ipAddress.address}? This action cannot
                        be undone.
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
                <dt className="text-sm font-medium text-muted-foreground">Address</dt>
                <dd className="mt-1">{ipAddress.address}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-muted-foreground">Status</dt>
                <dd className="mt-1">
                  <StatusBadge status={ipAddress.status} />
                </dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-muted-foreground">VRF</dt>
                <dd className="mt-1">{ipAddress.vrf_id ?? "-"}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-muted-foreground">DNS Name</dt>
                <dd className="mt-1">{ipAddress.dns_name || "-"}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-muted-foreground">Tenant</dt>
                <dd className="mt-1">{ipAddress.tenant_id ?? "-"}</dd>
              </div>
              <div className="sm:col-span-2">
                <dt className="text-sm font-medium text-muted-foreground">Description</dt>
                <dd className="mt-1">{ipAddress.description || "-"}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-muted-foreground">Created</dt>
                <dd className="mt-1">{new Date(ipAddress.created_at).toLocaleString()}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-muted-foreground">Updated</dt>
                <dd className="mt-1">{new Date(ipAddress.updated_at).toLocaleString()}</dd>
              </div>
            </dl>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
