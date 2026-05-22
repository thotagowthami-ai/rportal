import LegalLayout from "@/components/ui/LegalLayout";

export default function TrustCenter() {
  return (
    <LegalLayout
      title="Trust Center"
      description="We take the security of your candidate and company data seriously."
    >
      <section className="space-y-8">
        <div>
          <h2>Our Commitment Profile</h2>
          <p>
            AuraRecruiting is built on a foundation of trust. We understand that
            recruiting involves handling highly sensitive personal data, and
            preserving the confidentiality, integrity, and availability of that
            data is our top priority.
          </p>
          <p>
            As a cloud-centric platform, our security posture is designed across
            physical, network, and application layers to provide defense-in-depth
            against emerging threats.
          </p>
        </div>

        <hr className="border-t border-[#e8dfd6]" />

        <div>
          <h2>Platform Infrastructure Security</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">
            <div className="bg-slate-50 p-6 rounded-2xl border border-slate-200">
              <div className="w-10 h-10 bg-indigo-100 text-indigo-600 rounded-xl flex items-center justify-center mb-4">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
              </div>
              <h3 className="font-bold text-slate-900 mt-0 mb-2">Data Encryption</h3>
              <p className="text-sm mb-0">
                All data stored on AuraRecruiting is encrypted at rest using AES-256
                encryption. All communication between our clients and servers is
                encrypted in transit using industry-standard TLS 1.3.
              </p>
            </div>

            <div className="bg-slate-50 p-6 rounded-2xl border border-slate-200">
              <div className="w-10 h-10 bg-indigo-100 text-indigo-600 rounded-xl flex items-center justify-center mb-4">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="2" y="2" width="20" height="8" rx="2" ry="2"/><rect x="2" y="14" width="20" height="8" rx="2" ry="2"/><line x1="6" y1="6" x2="6.01" y2="6"/><line x1="6" y1="18" x2="6.01" y2="18"/></svg>
              </div>
              <h3 className="font-bold text-slate-900 mt-0 mb-2">Secure Hosting</h3>
              <p className="text-sm mb-0">
                Our architecture is hosted on leading enterprise-grade cloud
                providers (AWS/GCP) in geographically distributed, highly secure
                data centers enforcing biometric access controls.
              </p>
            </div>
          </div>
        </div>
      </section>
    </LegalLayout>
  );
}
