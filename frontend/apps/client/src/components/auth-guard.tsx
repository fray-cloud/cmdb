"use client";

import { useAuth } from "@cmdb/shared";
import { getSetupStatus } from "@cmdb/shared/lib/setup";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import type { ReactNode } from "react";

export function AuthGuard({ children }: { children: ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();
  const [checkingSetup, setCheckingSetup] = useState(true);

  useEffect(() => {
    async function checkSetup() {
      try {
        const status = await getSetupStatus();
        if (!status.initialized) {
          router.replace("/setup");
          return;
        }
      } catch {
        // Setup endpoint unavailable — assume initialized
      } finally {
        setCheckingSetup(false);
      }
    }
    checkSetup();
  }, [router]);

  useEffect(() => {
    if (!checkingSetup && !isLoading && !isAuthenticated) {
      router.replace("/login");
    }
  }, [isAuthenticated, isLoading, checkingSetup, router]);

  if (isLoading || checkingSetup) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="text-muted-foreground">Loading...</div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  return <>{children}</>;
}
