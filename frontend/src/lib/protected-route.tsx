// frontend/src/lib/protected-route.tsx
"use client";

import { ReactNode, useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";

export function ProtectedRoute({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const publicPaths = ["/"];

  useEffect(() => {
    if (!loading && !user && !publicPaths.includes(pathname || "")) {
      router.replace("/login");
    }
  }, [loading, user, router, pathname]);

  if (loading) {
    return null;
  }

  if (!user && !publicPaths.includes(pathname || "")) {
    return null;
  }

  return <>{children}</>;
}

export function PublicOnlyRoute({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && user) {
      router.replace("/dashboard");
    }
  }, [loading, user, router]);

  if (loading) {
    return null;
  }

  return <>{children}</>;
}
