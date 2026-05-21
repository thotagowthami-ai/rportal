"use client";

import { ReactNode } from "react";
import { AuthProvider } from "../src/lib/auth-context";
import { SidebarLayout } from "./sidebar-layout";

export function Providers({ children }: { children: ReactNode }) {
  return (
    <AuthProvider>
      <SidebarLayout>{children}</SidebarLayout>
    </AuthProvider>
  );
}
