import LegalLayout from "@/components/ui/LegalLayout";

export default function GDPRCompliance() {
  return (
    <LegalLayout
      title="GDPR Compliance"
      description="Our commitment to European data protection standards."
    >
      <section className="space-y-6">
        <div>
          <h2>Commitment to GDPR</h2>
          <p>
            AuraRecruiting is fully aligned with the General Data Protection
            Regulation (GDPR). We are committed to ensuring the security and
            protection of the personal information that we process, and to
            provide a compliant and consistent approach to data protection.
          </p>
        </div>

        <hr className="border-t border-[#e8dfd6] my-8" />

        <div>
          <h2>Data Subject Rights</h2>
          <p>
            Our platform provides built-in mechanisms to help you honor data
            subject requests, including:
          </p>
          <ul>
            <li><strong>Right to erasure</strong> (Right to be forgotten)</li>
            <li><strong>Right to access</strong> (Data portability exports)</li>
            <li><strong>Right to rectification</strong> (Updating candidate profiles)</li>
          </ul>
        </div>
        
        <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-xl mt-6">
           <p className="text-sm text-yellow-800 m-0">
             <strong>Note:</strong> As a platform provider, AuraRecruiting acts as the <em>Data Processor</em>, while your organization acts as the <em>Data Controller</em>.
           </p>
        </div>
      </section>
    </LegalLayout>
  );
}
