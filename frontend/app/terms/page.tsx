import LegalLayout from "@/src/components/ui/LegalLayout";

export default function TermsOfService() {
  return (
    <LegalLayout
      title="Terms of Service"
      description="Please read these terms carefully before using AuraRecruiting."
    >
      <section className="space-y-6">
        <div>
          <h2>Agreement to Terms</h2>
          <p>
            By accessing or using AuraRecruiting, you agree to be bound by these
            Terms. If you disagree with any part of the terms, you may not
            access the service.
          </p>
        </div>

        <hr className="border-t border-[#e8dfd6] my-8" />

        <div>
          <h2>Use License</h2>
          <p>
            Permission is granted to temporarily use our cloud-based platform
            for recruiting purposes. This is the grant of a license, not a
            transfer of title. Under this license, you may not reverse engineer
            any software contained on the platform.
          </p>
        </div>

        <hr className="border-t border-[#e8dfd6] my-8" />

        <div>
          <h2>User Content</h2>
          <p>
            You retain all rights to the data you upload to the platform,
            including your candidates' information. You grant us a license to
            process and display this data solely for the purpose of providing
            the service to you.
          </p>
        </div>
      </section>
    </LegalLayout>
  );
}
