"use client";

import Link from "next/link";

export default function AboutPage() {
  return (
    <div className="min-h-screen bg-[#fdf8f3] font-['Plus_Jakarta_Sans',sans-serif]">
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
            About AuraRecruiting
          </h1>
          <p className="text-[#515f74] text-lg leading-relaxed mb-8">
            We're transforming the way companies hire by combining artificial intelligence with human expertise.
          </p>
          
          <div className="space-y-8">
            <section>
              <h2 className="text-2xl font-bold text-[#1d1b19] mb-4">Our Mission</h2>
              <p className="text-[#515f74] leading-relaxed">
                To empower organizations to build exceptional teams by making hiring faster, smarter, and more fair through AI-powered recruiting technology.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-[#1d1b19] mb-4">Our Vision</h2>
              <p className="text-[#515f74] leading-relaxed">
                We envision a future where every organization, regardless of size, has access to world-class recruiting capabilities.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-[#1d1b19] mb-4">Our Values</h2>
              <p className="text-[#515f74] leading-relaxed mb-4">
                <strong className="text-[#1d1b19]">Innovation:</strong> We continuously push the boundaries of what's possible in recruiting technology.
              </p>
              <p className="text-[#515f74] leading-relaxed mb-4">
                <strong className="text-[#1d1b19]">Integrity:</strong> We operate with transparency and fairness in all our interactions.
              </p>
              <p className="text-[#515f74] leading-relaxed">
                <strong className="text-[#1d1b19]">Impact:</strong> We measure our success by the success of our customers.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-[#1d1b19] mb-4">Get in Touch</h2>
              <p className="text-[#515f74] leading-relaxed">
                Want to learn more about AuraRecruiting? Contact us at hello@aurarecruiting.com
              </p>
            </section>
          </div>
        </div>
      </section>
    </div>
  );
}
