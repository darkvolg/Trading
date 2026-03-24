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
    canonical: "/",
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

const faqJsonLd = {
  "@context": "https://schema.org",
  "@type": "FAQPage",
  mainEntity: [
    {
      "@type": "Question",
      name: "What is TrendRider?",
      acceptedAnswer: {
        "@type": "Answer",
        text: "TrendRider is an AI-powered algorithmic trading system built on Freqtrade. It analyzes BTC, ETH, SOL, BNB, and DOGE across multiple timeframes using 15+ technical indicators combined with on-chain data to generate high-confidence trade signals.",
      },
    },
    {
      "@type": "Question",
      name: "How are signals generated?",
      acceptedAnswer: {
        "@type": "Answer",
        text: "Our algorithm combines 15+ technical indicators (RSI, MACD, Bollinger Bands, EMA crossovers, etc.), multi-timeframe analysis (5m, 15m, 1h, 4h), and on-chain metrics (Fear & Greed Index, funding rates, open interest) to identify high-probability setups.",
      },
    },
    {
      "@type": "Question",
      name: "What's the track record?",
      acceptedAnswer: {
        "@type": "Answer",
        text: "All trades are logged in a public Google Sheet with full transparency. Our backtested results show a 67.9% win rate, 2.12 profit factor, and just 1.42% max drawdown.",
      },
    },
    {
      "@type": "Question",
      name: "How do I auto-trade?",
      acceptedAnswer: {
        "@type": "Answer",
        text: "Connect the Cornix bot to our Telegram channel and link it to your exchange (Bybit, Binance, or OKX). Cornix will automatically execute trades based on our signals with your configured position sizing.",
      },
    },
    {
      "@type": "Question",
      name: "Is it safe?",
      acceptedAnswer: {
        "@type": "Answer",
        text: "We use strict risk management: 6% stop-loss per trade, never risking more than 2% of portfolio per position. The system has been paper-trading since March 2026 with verified results. However, all trading involves risk and past performance does not guarantee future results.",
      },
    },
  ],
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
          dangerouslySetInnerHTML={{ __html: JSON.stringify(faqJsonLd) }}
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
