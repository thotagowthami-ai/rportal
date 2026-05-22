"use client";

import Link from "next/link";

export default function TrustCenterPage() {
  return (
    <div className="min-h-screen bg-[#fdf8f3] font-sans">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 h-14 flex items-center justify-between px-10 bg-[rgba(253,248,243,0.92)] backdrop-blur-2xl border-b border-[rgba(232,223,214,0.6)]">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-[#3525cd]" />
          <span className="text-sm font-extrabold text-[#1d1b19] tracking-tight">AuraRecruiting</span>
        </div>
        <Link href="/" className="text-[0.85rem] font-medium text-[#515f74] hover:text-[#1d1b19] transition-colors">
          ← Back to Home
        </Link>
      </nav>

      {/* Main Content */}
      <section className="pt-32 pb-20 px-6">
        <div className="max-w-3xl mx-auto">
          <h1 className="text-4xl font-extrabold tracking-[-0.035em] leading-tight text-[#1d1b19] mb-6">
            Trust Center
          </h1>
          <p className="text-[#515f74] text-lg leading-relaxed mb-8">
            We are committed to maintaining the highest standards of security, privacy, and compliance.
          </p>
          
          <div className="space-y-8">
            <section>
              <h2 className="text-2xl font-bold text-[#1d1b19] mb-4">Security</h2>
              <p className="text-[#515f74] leading-relaxed">
                AuraRecruiting implements enterprise-grade security measures including encryption, firewalls, and regular security audits to protect your data.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-[#1d1b19] mb-4">Compliance</h2>
              <p className="text-[#515f74] leading-relaxed">
                We comply with industry standards and regulations including GDPR, CCPA, and SOC 2 to ensure your data is handled responsibly.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-[#1d1b19] mb-4">Data Availability</h2>
              <p className="text-[#515f74] leading-relaxed">
                Our platform maintains 99.9% uptime through redundant infrastructure and continuous monitoring.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-[#1d1b19] mb-4">Security Reporting</h2>
              <p className="text-[#515f74] leading-relaxed">
                If you discover a security vulnerability, please report it responsibly to security@aurarecruiting.com
              </p>
            </section>
          </div>
        </div>
      </section>
    </div>
  );
}
