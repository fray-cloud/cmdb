"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { vrfApi } from "@cmdb/shared";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { ArrowLeft } from "lucide-react";

export default function NewVRFPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [form, setForm] = useState({
    name: "",
    rd: "",
    import_targets: "",
    export_targets: "",
    tenant_id: "",
    description: "",
  });

  const mutation = useMutation({
    mutationFn: () =>
      vrfApi.create({
        name: form.name,
        rd: form.rd || null,
        import_targets: form.import_targets
          ? form.import_targets.split(",").map((s) => s.trim())
          : [],
        export_targets: form.export_targets
          ? form.export_targets.split(",").map((s) => s.trim())
          : [],
        tenant_id: form.tenant_id || null,
        description: form.description,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["vrfs"] });
      router.push("/ipam/vrfs");
    },
  });

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="sm" onClick={() => router.push("/ipam/vrfs")}>
          <ArrowLeft />
          Back
        </Button>
        <h1 className="text-2xl font-bold tracking-tight">New VRF</h1>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Create VRF</CardTitle>
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
              <Label htmlFor="name">Name *</Label>
              <Input
                id="name"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="rd">RD</Label>
              <Input
                id="rd"
                placeholder="e.g. 65000:1"
                value={form.rd}
                onChange={(e) => setForm({ ...form, rd: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="import_targets">Import Targets (comma separated)</Label>
              <Input
                id="import_targets"
                value={form.import_targets}
                onChange={(e) => setForm({ ...form, import_targets: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="export_targets">Export Targets (comma separated)</Label>
              <Input
                id="export_targets"
                value={form.export_targets}
                onChange={(e) => setForm({ ...form, export_targets: e.target.value })}
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
                {mutation.isPending ? "Creating..." : "Create VRF"}
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={() => router.push("/ipam/vrfs")}
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
