"use client";

import Link from "next/link";

export default function CustomersPage() {
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
            Our Customers
          </h1>
          <p className="text-[#515f74] text-lg leading-relaxed mb-8">
            Join thousands of companies worldwide who are using AuraRecruiting to transform their hiring process.
          </p>
          
          <div className="space-y-8">
            <section>
              <h2 className="text-2xl font-bold text-[#1d1b19] mb-4">Featured Customers</h2>
              <p className="text-[#515f74] leading-relaxed">
                From startups to Fortune 500 companies, organizations across industries trust AuraRecruiting to streamline their recruiting workflows.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-[#1d1b19] mb-4">Customer Success</h2>
              <p className="text-[#515f74] leading-relaxed">
                Our customers report an average of 40% reduction in time-to-hire and 60% improvement in candidate quality.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-[#1d1b19] mb-4">Customer Support</h2>
              <p className="text-[#515f74] leading-relaxed">
                We provide 24/7 support through multiple channels including email, chat, and phone to ensure your success.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-[#1d1b19] mb-4">Ready to Join?</h2>
              <p className="text-[#515f74] leading-relaxed">
                Start a free trial today and see how AuraRecruiting can transform your hiring process. No credit card required.
              </p>
            </section>
          </div>
        </div>
      </section>
    </div>
  );
}
