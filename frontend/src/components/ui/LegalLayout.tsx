"use client";

import type React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";

const navigation = [
  { name: "Trust Center", href: "/trust" },
  { name: "SOC Reports", href: "/soc" },
  { name: "GDPR Compliance", href: "/gdpr" },
  { name: "Privacy Policy", href: "/privacy" },
  { name: "Terms of Service", href: "/terms" },
  { name: "Cookie Policy", href: "/cookies" },
];

export default function LegalLayout({
  children,
  title,
  description,
}: {
  children: React.ReactNode;
  title: string;
  description: string;
}) {
  const pathname = usePathname();

  return (
    <div className="min-h-screen bg-[#fdf8f3] font-['Plus_Jakarta_Sans',sans-serif] selection:bg-[#3525cd] selection:text-white">
      {/* Dynamic Header */}
      <nav className="fixed top-0 left-0 right-0 z-50 h-14 flex items-center justify-between px-10 bg-[rgba(253,248,243,0.92)] backdrop-blur-2xl border-b border-[rgba(232,223,214,0.6)]">
        <Link href="/" className="flex items-center gap-2 hover:opacity-80 transition-opacity">
          <div className="w-2 h-2 rounded-full bg-[#3525cd]" />
          <span className="text-sm font-extrabold text-[#1d1b19] tracking-tight">
            AuraRecruiting
          </span>
        </Link>
        <Link
          href="/"
          className="text-[0.85rem] font-medium text-[#515f74] hover:text-[#1d1b19] transition-colors"
        >
          ← Back to Platform
        </Link>
      </nav>

      {/* Hero Section */}
      <div className="pt-24 pb-12 px-6 bg-white border-b border-[#e8dfd6]">
        <div className="max-w-5xl mx-auto flex flex-col pt-8">
          <div className="inline-flex items-center gap-2 mb-4 w-fit">
            <span className="w-1.5 h-1.5 rounded-full bg-[#10b981]" />
            <span className="text-[0.65rem] font-bold text-[#515f74] uppercase tracking-widest">
              Legal & Compliance
            </span>
          </div>
          <h1 className="text-[clamp(2.2rem,4vw,3.5rem)] font-extrabold text-[#1d1b19] tracking-tight leading-[1.1] mb-4">
            {title}
          </h1>
          <p className="text-lg text-[#515f74] max-w-2xl leading-relaxed">
            {description}
          </p>
        </div>
      </div>

      <main className="max-w-5xl mx-auto px-6 py-16 flex flex-col md:flex-row gap-12">
        {/* Sidebar Nav */}
        <aside className="w-full md:w-64 flex-shrink-0">
          <div className="sticky top-28 bg-white rounded-2xl border border-[#e8dfd6] p-4 shadow-[0_8px_30px_rgba(0,0,0,0.04)]">
            <nav className="space-y-1">
              {navigation.map((item) => {
                const isActive = pathname === item.href;
                return (
                  <Link
                    key={item.name}
                    href={item.href}
                    className={`block px-4 py-2.5 rounded-xl text-[0.85rem] font-bold transition-all ${
                      isActive
                        ? "bg-[rgba(53,37,205,0.06)] text-[#3525cd]"
                        : "text-[#515f74] hover:bg-[#f8f3ee] hover:text-[#1d1b19]"
                    }`}
                  >
                    {item.name}
                  </Link>
                );
              })}
            </nav>
            <div className="mt-8 pt-6 border-t border-[#e8dfd6] px-4">
              <p className="text-[0.7rem] text-[#515f74] mb-3">
                Have questions about our policies?
              </p>
              <a
                href="mailto:legal@aurarecruiting.com"
                className="inline-block text-[0.75rem] font-bold text-[#3525cd] hover:text-[#2c1eb3] transition-colors"
              >
                Contact Legal Team →
              </a>
            </div>
          </div>
        </aside>

        {/* Content Area */}
        <article className="flex-1 min-w-0 bg-white rounded-3xl border border-[#e8dfd6] p-8 md:p-12 shadow-sm prose prose-slate max-w-none prose-headings:text-[#1d1b19] prose-p:text-[#515f74] prose-p:leading-relaxed prose-a:text-[#3525cd] prose-li:text-[#515f74] prose-strong:text-[#1d1b19] prose-strong:font-bold">
          {children}
        </article>
      </main>

      {/* Light Footer */}
      <footer className="bg-white border-t border-[#e8dfd6] py-8 text-center">
        <p className="text-xs font-medium text-[#515f74] tracking-wide">
          © {new Date().getFullYear()} AuraRecruiting Inc. All rights reserved.
        </p>
      </footer>
    </div>
  );
}
