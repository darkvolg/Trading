import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Live Bot Stats — Real-Time Dry-Run Results | TrendRider",
  description:
    "Real-time stats from the TrendRider crypto trading bot. Unfiltered sqlite data: balance, P&L, win rate, recent trades, exit reasons. Updated hourly.",
  alternates: { canonical: "https://trendrider.net/live" },
  openGraph: {
    title: "TrendRider — Live Bot Stats",
    description:
      "Unfiltered real-time paper-trading results. No marketing, just raw numbers from the bot.",
    type: "website",
    url: "https://trendrider.net/live",
  },
  twitter: { card: "summary_large_image", title: "TrendRider — Live Bot Stats" },
};

export default function LiveLayout({ children }: { children: React.ReactNode }) {
  return children;
}
