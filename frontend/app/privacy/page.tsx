import LegalLayout from "@/components/ui/LegalLayout";

export default function PrivacyPolicy() {
  return (
    <LegalLayout
      title="Privacy Policy"
      description="How we collect, use, and handle your data."
    >
      <section className="space-y-6">
        <div>
          <h2>Information We Collect</h2>
          <p>
            We collect information you provide directly to us, such as when you
            create or modify your account, request on-demand services, contact
            customer support, or otherwise communicate with us.
          </p>
          <ul>
            <li>Name and contact data</li>
            <li>Credentials (passwords and security info)</li>
            <li>Payment data</li>
            <li>Candidate resume and extracted profile data</li>
          </ul>
        </div>

        <hr className="border-t border-[#e8dfd6] my-8" />

        <div>
          <h2>How We Use Information</h2>
          <p>
            We use the information we collect to provide, maintain, and improve
            our services, specifically focusing on powering our AI matching
            engine and streamlining the recruitment lifecycle for our clients.
          </p>
        </div>
      </section>
    </LegalLayout>
  );
}
