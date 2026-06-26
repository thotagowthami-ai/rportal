// frontend/src/lib/protected-route.tsx
"use client";

import { ReactNode, useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";

export function ProtectedRoute({ children }: { children: ReactNode }) {
  const { user, loading, isExchangingCode } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const publicPaths = ["/"];

  // isExchangingCode: OAuth callback is mid-flight — never redirect during exchange
  const isAuthPending = loading || isExchangingCode;

  useEffect(() => {
    if (!isAuthPending && !user && !publicPaths.includes(pathname || "")) {
      router.replace("/login");
    }
  }, [isAuthPending, user, router, pathname]);

  if (isAuthPending) {
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
