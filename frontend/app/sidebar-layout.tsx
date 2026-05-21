"use client";

import { usePathname } from "next/navigation";
import { Sidebar } from "@/components/Sidebar";
import { useEffect, useState } from "react";

// Pages that should NOT show the sidebar
const PUBLIC_PATHS = [
  "/", 
  "/login", 
  "/signup", 
  "/forgot-password", 
  "/privacy", 
  "/terms", 
  "/cookie-policy", 
  "/about", 
  "/careers", 
  "/customers", 
  "/trust-center"
];

function isPublicPath(pathname: string): boolean {
  return PUBLIC_PATHS.some(
    (p) => pathname === p || pathname.startsWith(p + "/")
  );
}

export function SidebarLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname() ?? "";
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const showSidebar = !isPublicPath(pathname);

  // Avoid hydration mismatch by waiting for mount
  if (!mounted) {
    return <>{children}</>;
  }

  if (!showSidebar) {
    return <>{children}</>;
  }

  return (
    <div style={{ display: "flex", minHeight: "100vh" }}>
      <Sidebar />
      <main style={{ flex: 1, minWidth: 0, overflowX: "hidden" }}>
        {children}
      </main>
    </div>
  );
}
