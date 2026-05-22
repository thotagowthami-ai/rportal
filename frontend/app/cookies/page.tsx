import LegalLayout from "@/components/ui/LegalLayout";

export default function CookiePolicy() {
  return (
    <LegalLayout
      title="Cookie Policy"
      description="Understanding how we use cookies and similar technologies."
    >
      <section className="space-y-6">
        <div>
          <h2>What are cookies?</h2>
          <p>
            Cookies are small data files that are placed on your computer or
            mobile device when you visit a website. Cookies are widely used
            by website owners to make their websites work, or to work more
            efficiently, as well as to provide reporting information.
          </p>
        </div>

        <hr className="border-t border-[#e8dfd6] my-8" />

        <div>
          <h2>How do we use cookies?</h2>
          <p>
            We use essential cookies strictly to provide you with the services
            available through our platform. These include session management
            and secure authentication cookies. We do not use third-party
            tracking cookies.
          </p>
        </div>
      </section>
    </LegalLayout>
  );
}
