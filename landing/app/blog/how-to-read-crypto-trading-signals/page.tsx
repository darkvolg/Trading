import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Redirecting...",
  description: "This page has moved to /blog/how-to-read-crypto-trading-signals-2026",
  robots: { index: false, follow: true },
  alternates: {
    canonical: "https://trendrider.net/blog/how-to-read-crypto-trading-signals-2026",
  },
};

export default function Article() {
  return (
    <>
      <meta httpEquiv="refresh" content="0;url=/blog/how-to-read-crypto-trading-signals-2026" />
      <script
        dangerouslySetInnerHTML={{
          __html: `window.location.replace("/blog/how-to-read-crypto-trading-signals-2026");`,
        }}
      />
      <div className="min-h-screen bg-background text-foreground flex items-center justify-center">
        <p className="text-muted">
          Redirecting to{" "}
          <a href="/blog/how-to-read-crypto-trading-signals-2026" className="text-primary hover:underline">
            the updated guide
          </a>
          ...
        </p>
      </div>
    </>
  );
}
