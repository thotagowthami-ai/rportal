import Link from "next/link";

export default function CookiePolicyPage() {
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
            Cookie Policy
          </h1>
          <p className="text-[#515f74] text-lg leading-relaxed mb-8">
            This policy explains how AuraRecruiting uses cookies and similar technologies to enhance your experience.
          </p>
          
          <div className="space-y-8">
            <section>
              <h2 className="text-2xl font-bold text-[#1d1b19] mb-4">What Are Cookies?</h2>
              <p className="text-[#515f74] leading-relaxed">
                Cookies are small text files stored on your device that help us remember your preferences and improve your browsing experience.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-[#1d1b19] mb-4">Types of Cookies We Use</h2>
              <p className="text-[#515f74] leading-relaxed mb-4">
                <strong className="text-[#1d1b19]">Essential Cookies:</strong> Required for core functionality and security.
              </p>
              <p className="text-[#515f74] leading-relaxed">
                <strong className="text-[#1d1b19]">Analytics Cookies:</strong> Help us understand how users interact with our platform.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-[#1d1b19] mb-4">Managing Cookies</h2>
              <p className="text-[#515f74] leading-relaxed">
                You can control cookie settings through your browser. Please note that disabling cookies may affect the functionality of our platform.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-[#1d1b19] mb-4">Questions?</h2>
              <p className="text-[#515f74] leading-relaxed">
                For more information about our cookie practices, please contact us at cookies@aurarecruiting.com
              </p>
            </section>
          </div>
        </div>
      </section>
    </div>
  );
}
