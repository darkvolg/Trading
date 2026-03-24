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
  title: "TrendRider — Algorithmic Crypto Trading Signals",
  description:
    "AI-powered crypto trading signals with 67.9% win rate, verified on-chain. BTC, ETH, SOL, BNB, DOGE signals delivered via Telegram with Cornix auto-trade support.",
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
    languages: {
      "en": "/",
      "ru": "/ru",
    },
  },
  openGraph: {
    title: "TrendRider — Algorithmic Crypto Trading Signals",
    description:
      "AI-powered crypto signals with 67.9% win rate. Verified results, ultra-low drawdown.",
    type: "website",
    url: "https://trendrider.net",
    siteName: "TrendRider",
    locale: "en_US",
    images: [{ url: "/opengraph-image", width: 1200, height: 630 }],
  },
  twitter: {
    card: "summary_large_image",
    title: "TrendRider — Algorithmic Crypto Trading Signals",
    description:
      "AI-powered crypto signals with 67.9% win rate. Verified results.",
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
    "AI-powered algorithmic crypto trading signals with 67.9% win rate. BTC, ETH, SOL, BNB, DOGE signals via Telegram.",
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
        {/* Google Analytics */}
        <script async src="https://www.googletagmanager.com/gtag/js?id=G-TJBTZ0Y6DL" />
        <script
          dangerouslySetInnerHTML={{
            __html: `window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}gtag('js',new Date());gtag('config','G-TJBTZ0Y6DL');`,
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
