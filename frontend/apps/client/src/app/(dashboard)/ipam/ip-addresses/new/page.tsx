"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { ipAddressApi } from "@cmdb/shared";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
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
import { ArrowLeft } from "lucide-react";

export default function NewIPAddressPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [form, setForm] = useState({
    address: "",
    status: "active",
    vrf_id: "",
    dns_name: "",
    tenant_id: "",
    description: "",
  });

  const mutation = useMutation({
    mutationFn: () =>
      ipAddressApi.create({
        address: form.address,
        status: form.status,
        vrf_id: form.vrf_id || null,
        dns_name: form.dns_name,
        tenant_id: form.tenant_id || null,
        description: form.description,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["ip-addresses"] });
      router.push("/ipam/ip-addresses");
    },
  });

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="sm" onClick={() => router.push("/ipam/ip-addresses")}>
          <ArrowLeft />
          Back
        </Button>
        <h1 className="text-2xl font-bold tracking-tight">New IP Address</h1>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Create IP Address</CardTitle>
        </CardHeader>
        <CardContent>
          <form
            className="grid gap-4 sm:grid-cols-2"
            onSubmit={(e) => {
              e.preventDefault();
              mutation.mutate();
            }}
          >
            <div className="space-y-2">
              <Label htmlFor="address">Address *</Label>
              <Input
                id="address"
                placeholder="e.g. 10.0.0.1/32"
                value={form.address}
                onChange={(e) => setForm({ ...form, address: e.target.value })}
                required
              />
            </div>
            <div className="space-y-2">
              <Label>Status</Label>
              <Select
                value={form.status}
                onValueChange={(val) => val && setForm({ ...form, status: val })}
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
                value={form.vrf_id}
                onChange={(e) => setForm({ ...form, vrf_id: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="dns_name">DNS Name</Label>
              <Input
                id="dns_name"
                value={form.dns_name}
                onChange={(e) => setForm({ ...form, dns_name: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="tenant_id">Tenant ID</Label>
              <Input
                id="tenant_id"
                value={form.tenant_id}
                onChange={(e) => setForm({ ...form, tenant_id: e.target.value })}
              />
            </div>
            <div className="space-y-2 sm:col-span-2">
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                value={form.description}
                onChange={(e) => setForm({ ...form, description: e.target.value })}
              />
            </div>
            <div className="flex gap-2 sm:col-span-2">
              <Button type="submit" disabled={mutation.isPending}>
                {mutation.isPending ? "Creating..." : "Create IP Address"}
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={() => router.push("/ipam/ip-addresses")}
              >
                Cancel
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
