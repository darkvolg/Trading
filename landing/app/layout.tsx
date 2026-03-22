import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

const jetbrainsMono = JetBrains_Mono({
  variable: "--font-jetbrains",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "TrendRider — Algorithmic Crypto Trading Signals",
  description:
    "AI-powered crypto trading signals with 71% win rate, verified on-chain. BTC, ETH, SOL, BNB signals delivered via Telegram with Cornix auto-trade support.",
  keywords: [
    "crypto signals",
    "trading bot",
    "algorithmic trading",
    "BTC signals",
    "Telegram crypto",
    "Cornix",
    "Freqtrade",
  ],
  openGraph: {
    title: "TrendRider — Algorithmic Crypto Trading Signals",
    description:
      "AI-powered crypto signals with 71% win rate. Verified results, ultra-low drawdown.",
    type: "website",
    url: "https://trendrider.pro",
    siteName: "TrendRider",
  },
  twitter: {
    card: "summary_large_image",
    title: "TrendRider — Algorithmic Crypto Trading Signals",
    description:
      "AI-powered crypto signals with 71% win rate. Verified results.",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${inter.variable} ${jetbrainsMono.variable} antialiased`}
    >
      <body className="min-h-screen bg-background text-foreground font-sans">
        {children}
      </body>
    </html>
  );
}
