"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const navItems = [
  {
    href: "/dashboard",
    label: "Dashboard",
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/>
        <rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/>
      </svg>
    ),
  },
  {
    href: "/jobs",
    label: "Jobs",
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 7V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v2"/>
      </svg>
    ),
  },
  {
    href: "/resumes",
    label: "Candidates",
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/>
        <path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>
      </svg>
    ),
  },
  {
    href: "/linkedin-generator",
    label: "LinkedIn Generator",
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/>
        <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>
      </svg>
    ),
  },
  {
    href: "/analytics",
    label: "Analytics",
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/>
        <line x1="6" y1="20" x2="6" y2="14"/>
      </svg>
    ),
  },
  {
    href: "/settings",
    label: "Settings",
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="3"/>
        <path d="M19.07 4.93a10 10 0 0 1 0 14.14M4.93 4.93a10 10 0 0 0 0 14.14"/>
        <path d="M12 2v2m0 16v2M2 12h2m16 0h2"/>
      </svg>
    ),
  },
];

export function Sidebar() {
  const pathname = usePathname() ?? "";

  return (
    <aside
      style={{
        width: "240px",
        minHeight: "100vh",
        height: "100vh",
        position: "sticky",
        top: 0,
        display: "flex",
        flexDirection: "column",
        background: "linear-gradient(180deg, #1e1b4b 0%, #2d2a6e 60%, #3525cd 100%)",
        flexShrink: 0,
      }}
    >
      {/* Brand */}
      <div
        style={{
          padding: "28px 24px 24px",
          borderBottom: "1px solid rgba(255,255,255,0.08)",
          display: "flex",
          alignItems: "center",
          gap: "12px",
        }}
      >
        <div
          style={{
            width: "38px",
            height: "38px",
            borderRadius: "12px",
            background: "rgba(255,255,255,0.15)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            color: "white",
            fontWeight: 800,
            fontSize: "16px",
            flexShrink: 0,
            border: "1px solid rgba(255,255,255,0.2)",
          }}
        >
          A
        </div>
        <div>
          <p
            style={{
              fontSize: "10px",
              fontWeight: 600,
              color: "rgba(255,255,255,0.5)",
              letterSpacing: "0.12em",
              textTransform: "uppercase",
              lineHeight: 1,
              marginBottom: "3px",
            }}
          >
            Aura
          </p>
          <p style={{ fontSize: "14px", fontWeight: 700, color: "white", lineHeight: 1 }}>
            Recruiting
          </p>
        </div>
      </div>

      {/* Nav Label */}
      <div style={{ padding: "20px 24px 8px" }}>
        <p
          style={{
            fontSize: "10px",
            fontWeight: 700,
            color: "rgba(255,255,255,0.35)",
            letterSpacing: "0.12em",
            textTransform: "uppercase",
          }}
        >
          Main Menu
        </p>
      </div>

      {/* Nav Items */}
      <nav
        style={{
          flex: 1,
          padding: "4px 12px",
          display: "flex",
          flexDirection: "column",
          gap: "2px",
        }}
      >
        {navItems.map((item) => {
          const active =
            pathname === item.href || pathname.startsWith(item.href + "/");

          return (
            <Link
              key={item.href}
              href={item.href}
              aria-current={active ? "page" : undefined}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "12px",
                padding: "10px 12px",
                borderRadius: "12px",
                fontSize: "14px",
                fontWeight: active ? 600 : 500,
                textDecoration: "none",
                transition: "all 0.15s",
                background: active ? "rgba(255,255,255,0.18)" : "transparent",
                color: active ? "white" : "rgba(255,255,255,0.6)",
                boxShadow: active ? "0 2px 12px rgba(0,0,0,0.2)" : "none",
                borderLeft: active ? "3px solid rgba(255,255,255,0.8)" : "3px solid transparent",
              }}
              onMouseEnter={(e) => {
                if (!active) {
                  (e.currentTarget as HTMLAnchorElement).style.background = "rgba(255,255,255,0.08)";
                  (e.currentTarget as HTMLAnchorElement).style.color = "white";
                }
              }}
              onMouseLeave={(e) => {
                if (!active) {
                  (e.currentTarget as HTMLAnchorElement).style.background = "transparent";
                  (e.currentTarget as HTMLAnchorElement).style.color = "rgba(255,255,255,0.6)";
                }
              }}
            >
              <span style={{ opacity: active ? 1 : 0.7, flexShrink: 0 }}>
                {item.icon}
              </span>
              {item.label}
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div style={{ padding: "16px 12px", borderTop: "1px solid rgba(255,255,255,0.08)" }}>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "10px",
            padding: "12px",
            borderRadius: "12px",
            background: "rgba(255,255,255,0.08)",
            border: "1px solid rgba(255,255,255,0.10)",
          }}
        >
          <div
            style={{
              width: "32px",
              height: "32px",
              borderRadius: "8px",
              background: "linear-gradient(135deg, rgba(255,255,255,0.3), rgba(255,255,255,0.1))",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              flexShrink: 0,
            }}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2">
              <path d="M12 2L2 7l10 5 10-5-10-5z"/>
              <path d="M2 17l10 5 10-5"/>
              <path d="M2 12l10 5 10-5"/>
            </svg>
          </div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <p style={{ fontSize: "12px", fontWeight: 600, color: "white", marginBottom: "1px" }}>
              Pro Plan
            </p>
            <p style={{ fontSize: "10px", color: "rgba(255,255,255,0.45)" }}>
              All features active
            </p>
          </div>
          <div
            style={{
              width: "7px",
              height: "7px",
              borderRadius: "50%",
              background: "#4ade80",
              flexShrink: 0,
              boxShadow: "0 0 6px #4ade80",
            }}
          />
        </div>
      </div>
    </aside>
  );
}