import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Blog — TrendRider | Crypto Trading Insights",
  description: "Learn about algorithmic crypto trading, risk management, and signal analysis from the TrendRider team.",
};

const posts = [
  {
    slug: "why-algorithmic-trading-beats-manual",
    title: "Why Algorithmic Trading Beats Manual: Data Over Emotions",
    excerpt: "Discover why removing emotions from trading decisions leads to consistently better results. We break down the science behind algorithmic signals.",
    date: "March 20, 2026",
    readTime: "5 min read",
    tag: "Strategy",
  },
  {
    slug: "understanding-win-rate-and-profit-factor",
    title: "Understanding Win Rate & Profit Factor: What Really Matters",
    excerpt: "A 71% win rate means nothing without context. Learn how profit factor, drawdown, and SQN score work together to measure true performance.",
    date: "March 15, 2026",
    readTime: "4 min read",
    tag: "Education",
  },
  {
    slug: "risk-management-6-percent-stop-loss",
    title: "The 6% Stop-Loss Rule: How We Keep Drawdown at 1.42%",
    excerpt: "Most traders blow accounts because of poor risk management. Here's the exact framework TrendRider uses to protect capital on every trade.",
    date: "March 10, 2026",
    readTime: "6 min read",
    tag: "Risk Management",
  },
  {
    slug: "what-is-sqn-score-system-quality-number",
    title: "What Is SQN Score? Understanding System Quality Number in Trading",
    excerpt: "SQN measures how good your trading system really is. Learn what scores mean and how TrendRider achieves a 3.02 SQN.",
    date: "March 22, 2026",
    readTime: "5 min read",
    tag: "Education",
  },
  {
    slug: "multi-timeframe-analysis-explained",
    title: "Multi-Timeframe Analysis: How to Read Markets on 5m, 15m, 1h, and 4h",
    excerpt: "Combining multiple timeframes reduces false signals and increases trade confidence. Here's how TrendRider's MTF engine works.",
    date: "March 22, 2026",
    readTime: "6 min read",
    tag: "Strategy",
  },
  {
    slug: "fear-and-greed-index-crypto-trading",
    title: "Fear & Greed Index: How On-Chain Sentiment Drives Crypto Signals",
    excerpt: "Market sentiment is a powerful filter. Learn how the Fear & Greed Index integrates with technical analysis in our signals.",
    date: "March 21, 2026",
    readTime: "5 min read",
    tag: "On-Chain Data",
  },
  {
    slug: "cornix-auto-trade-setup-guide",
    title: "How to Set Up Cornix Auto-Trade with TrendRider Signals",
    excerpt: "Step-by-step guide to connecting Cornix bot with TrendRider on Bybit, Binance, or OKX for hands-free trading.",
    date: "March 21, 2026",
    readTime: "4 min read",
    tag: "Guide",
  },
  {
    slug: "funding-rates-open-interest-trading-signals",
    title: "Funding Rates & Open Interest: The On-Chain Edge in Crypto Trading",
    excerpt: "Funding rates and open interest reveal what the market is really doing. Here's how we use them in signal generation.",
    date: "March 20, 2026",
    readTime: "5 min read",
    tag: "On-Chain Data",
  },
  {
    slug: "paper-trading-vs-live-trading-when-to-switch",
    title: "Paper Trading vs Live Trading: When Is the Right Time to Go Live?",
    excerpt: "Paper trading validates your strategy without risking capital. We share our honest approach and when to transition to live.",
    date: "March 19, 2026",
    readTime: "5 min read",
    tag: "Education",
  },
  {
    slug: "position-sizing-and-risk-per-trade",
    title: "Position Sizing & Risk Per Trade: The 2% Rule Explained",
    excerpt: "How much to risk per trade? The 2% rule is the foundation of sustainable trading. Learn the math behind position sizing.",
    date: "March 18, 2026",
    readTime: "5 min read",
    tag: "Risk Management",
  },
];

export default function BlogPage() {
  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify({
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": [
              { "@type": "ListItem", "position": 1, "name": "Home", "item": "https://trendrider.net" },
              { "@type": "ListItem", "position": 2, "name": "Blog" }
            ]
          })
        }}
      />
    <div className="min-h-screen bg-background text-foreground">
      <div className="max-w-4xl mx-auto px-4 py-20">
        <a href="/" className="text-primary text-sm hover:underline mb-8 inline-block">&larr; Back to home</a>
        <h1 className="text-4xl font-bold mb-4 gradient-text">Blog</h1>
        <p className="text-muted mb-12 text-lg">Insights on algorithmic trading, risk management, and crypto signals.</p>

        <div className="space-y-6">
          {posts.map((post) => (
            <Link
              key={post.slug}
              href={`/blog/${post.slug}`}
              className="block p-6 rounded-2xl border border-border/50 bg-card/30 hover:border-primary/30 hover:bg-card/50 transition-all group"
            >
              <div className="flex items-center gap-3 mb-3">
                <span className="px-3 py-1 text-[10px] font-mono uppercase tracking-widest text-primary border border-primary/30 rounded-full">
                  {post.tag}
                </span>
                <span className="text-xs text-muted">{post.date}</span>
                <span className="text-xs text-muted">&bull; {post.readTime}</span>
              </div>
              <h2 className="text-xl font-semibold mb-2 group-hover:text-primary transition-colors">{post.title}</h2>
              <p className="text-muted text-sm leading-relaxed">{post.excerpt}</p>
            </Link>
          ))}
        </div>
      </div>
    </div>
    </>
  );
}
