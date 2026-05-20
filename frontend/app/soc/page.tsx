import LegalLayout from "@/components/ui/LegalLayout";

export default function SOCReports() {
  return (
    <LegalLayout
      title="SOC Reports & Compliance"
      description="Information regarding our SOC 2 Type II attestation and continuous monitoring."
    >
      <section className="space-y-6">
        <div>
          <h2>SOC 2 Type II Certification</h2>
          <div className="bg-slate-50 p-6 rounded-2xl border border-slate-200 shadow-sm mt-4">
            <p className="mb-4">
              AuraRecruiting has successfully completed a SOC 2 Type II audit,
              performed by an independent third-party firm. This report verifies
              that our information security practices, policies, procedures, and
              operations meet the rigorous SOC 2 standards for security,
              availability, and confidentiality.
            </p>

            <div className="p-5 bg-white rounded-xl border border-blue-100 shadow-sm mt-6">
              <h3 className="text-base font-bold text-slate-900 mb-2 mt-0">
                Requesting our SOC Report
              </h3>
              <p className="text-sm text-slate-600 mb-0">
                Our full SOC 2 Type II report is available under NDA. Please
                contact your account executive or email{" "}
                <a
                  href="mailto:security@aurarecruiting.com"
                  className="font-semibold text-blue-600 hover:text-blue-700 underline underline-offset-2"
                >
                  security@aurarecruiting.com
                </a>{" "}
                to request a copy.
              </p>
            </div>
          </div>
        </div>
      </section>
    </LegalLayout>
  );
}
