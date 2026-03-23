import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Privacy Policy — TrendRider",
  description: "Privacy Policy for TrendRider algorithmic crypto trading signals.",
};

export default function PrivacyPage() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <div className="max-w-3xl mx-auto px-4 py-20">
        <a href="/" className="text-primary text-sm hover:underline mb-8 inline-block">&larr; Back to home</a>
        <h1 className="text-4xl font-bold mb-8 gradient-text">Privacy Policy</h1>
        <p className="text-muted text-sm mb-12">Last updated: March 22, 2026</p>

        <div className="prose prose-invert max-w-none space-y-8">
          <section>
            <h2 className="text-xl font-semibold text-foreground mb-3">1. Information We Collect</h2>
            <p className="text-muted leading-relaxed text-sm">
              We collect minimal information necessary to provide the Service: your Telegram username when you join our channel, email address if you subscribe to a paid plan, and payment information processed securely through third-party payment providers.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-foreground mb-3">2. How We Use Your Information</h2>
            <p className="text-muted leading-relaxed text-sm">
              We use your information to: deliver trading signals via Telegram, process subscription payments, send service-related communications, and improve our algorithms and user experience. We do not sell your personal data to third parties.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-foreground mb-3">3. Cookies</h2>
            <p className="text-muted leading-relaxed text-sm">
              Our website uses essential cookies to remember your preferences (language, cookie consent). We do not use tracking cookies or third-party analytics that collect personal data. You can disable cookies in your browser settings.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-foreground mb-3">4. Data Security</h2>
            <p className="text-muted leading-relaxed text-sm">
              We implement industry-standard security measures to protect your data. Payment processing is handled by PCI-compliant third-party providers. We never store credit card numbers on our servers.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-foreground mb-3">5. Third-Party Services</h2>
            <p className="text-muted leading-relaxed text-sm">
              We use the following third-party services: Telegram (signal delivery), Cornix (auto-trade execution — optional), and payment processors (subscription billing). Each service has its own privacy policy that governs their use of your data.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-foreground mb-3">6. Your Rights</h2>
            <p className="text-muted leading-relaxed text-sm">
              You have the right to: access your personal data, request correction or deletion, withdraw consent at any time, and export your data. To exercise these rights, contact us at the email below.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-foreground mb-3">7. Data Retention</h2>
            <p className="text-muted leading-relaxed text-sm">
              We retain your data only as long as necessary to provide the Service. If you cancel your subscription, we will delete your personal data within 30 days, except where retention is required by law.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-foreground mb-3">8. Contact</h2>
            <p className="text-muted leading-relaxed text-sm">
              For privacy-related inquiries, contact us at{" "}
              <a href="mailto:support@trendrider.net" className="text-primary hover:underline">support@trendrider.net</a>.
            </p>
          </section>
        </div>
      </div>
    </div>
  );
}
