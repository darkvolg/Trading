import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
  display: "swap",
});

const jetbrainsMono = JetBrains_Mono({
  variable: "--font-jetbrains",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "Crypto Trading Signals — Verified Backtest & Live Stats | TrendRider",
  description:
    "Join 500+ traders getting AI crypto signals for BTC, ETH & SOL. Documented backtest stats on /live. Auto-trade on Bybit via Cornix. Start free.",
  keywords: [
    "crypto signals",
    "trading bot",
    "algorithmic trading",
    "BTC signals",
    "Telegram crypto",
    "Cornix",
    "Freqtrade",
    "crypto trading signals telegram",
    "automated crypto trading",
    "bybit signals",
  ],
  metadataBase: new URL("https://trendrider.net"),
  alternates: {
    canonical: "https://trendrider.net",
  },
  openGraph: {
    title: "Crypto Trading Signals — Verified Backtest & Live Stats | TrendRider",
    description:
      "Join 500+ traders getting AI crypto signals. Real backtest + live numbers on /live. Start free on Telegram.",
    type: "website",
    url: "https://trendrider.net",
    siteName: "TrendRider",
    locale: "en_US",
    images: [{ url: "/opengraph-image", width: 1200, height: 630 }],
  },
  twitter: {
    card: "summary_large_image",
    title: "Crypto Trading Signals — Verified Backtest & Live Stats | TrendRider",
    description:
      "Join 500+ traders getting AI crypto signals. Real backtest + live numbers on /live. Start free on Telegram.",
    creator: "@TrendRiderPro",
  },
  other: {
    'theme-color': '#0D1117',
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
    },
  },
};

const organizationJsonLd = {
  "@context": "https://schema.org",
  "@type": "Organization",
  "name": "TrendRider",
  "url": "https://trendrider.net",
  "logo": "https://trendrider.net/icon.svg",
  "description": "AI-powered crypto trading signals",
  "contactPoint": {
    "@type": "ContactPoint",
    "contactType": "customer support",
    "url": "https://t.me/TrendRider_Support",
  },
  "sameAs": [
    "https://t.me/TrendRiderSignals",
    "https://x.com/TrendRiderPro",
  ],
};

const jsonLd = {
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  name: "TrendRider",
  applicationCategory: "FinanceApplication",
  description:
    "AI-powered algorithmic crypto trading signals with documented backtest stats published on /live. BTC, ETH, SOL, BNB, DOGE signals via Telegram.",
  url: "https://trendrider.net",
  operatingSystem: "Telegram",
  offers: [
    {
      "@type": "Offer",
      name: "Free",
      price: "0",
      priceCurrency: "USD",
      description: "Delayed signals, monthly report, public results",
    },
    {
      "@type": "Offer",
      name: "Basic",
      price: "39",
      priceCurrency: "USD",
      description: "Real-time signals, Cornix auto-trade, 5 pairs",
    },
    {
      "@type": "Offer",
      name: "VIP",
      price: "99",
      priceCurrency: "USD",
      description: "Everything in Basic + post-trade analysis, daily brief",
    },
  ],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`dark ${inter.variable} ${jetbrainsMono.variable} antialiased`}
    >
      <head>
        {/* Preconnect to critical origins */}
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link rel="dns-prefetch" href="https://www.googletagmanager.com" />
        {/* Google Analytics — deferred to not block rendering */}
        <script
          dangerouslySetInnerHTML={{
            __html: `window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}gtag('js',new Date());gtag('config','G-TJBTZ0Y6DL');
(function(){var s=document.createElement('script');s.async=true;s.src='https://www.googletagmanager.com/gtag/js?id=G-TJBTZ0Y6DL';document.head.appendChild(s);})();`,
          }}
        />
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
        />
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(organizationJsonLd) }}
        />
      </head>
      <body className="min-h-screen bg-background text-foreground font-sans">
        {children}
      </body>
    </html>
  );
}
