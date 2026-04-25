import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Position Sizing Formula: The 2% Rule Explained (2026)",
  description: "Risk over 2% per trade? You'll blow your account. Get the exact position sizing formula by account size — free calculator and 3 worked examples.",
  alternates: {
    canonical: "https://trendrider.net/blog/position-sizing-and-risk-per-trade",
  },
};

export default function Article() {
  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify({
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": "Position Sizing Formula: The 2% Rule Explained (2026)",
            "description": "Risk over 2% per trade? You'll blow your account. Get the exact position sizing formula by account size — free calculator and 3 worked examples.",
            "author": {
              "@type": "Person",
              "name": "TrendRider Team",
              "url": "https://trendrider.net"
            },
            "publisher": {
              "@type": "Organization",
              "name": "TrendRider",
              "url": "https://trendrider.net",
              "logo": {
                "@type": "ImageObject",
                "url": "https://trendrider.net/icon.svg"
              }
            },
            "datePublished": "2026-03-22",
            "dateModified": "2026-03-24",
            "image": "https://trendrider.net/opengraph-image",
            "mainEntityOfPage": {
              "@type": "WebPage",
              "@id": "https://trendrider.net/blog/position-sizing-and-risk-per-trade"
            }
          })
        }}
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify({
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": [
              { "@type": "ListItem", "position": 1, "name": "Home", "item": "https://trendrider.net" },
              { "@type": "ListItem", "position": 2, "name": "Blog", "item": "https://trendrider.net/blog" },
              { "@type": "ListItem", "position": 3, "name": "Position Sizing: The 2% Rule That Saves Accounts" }
            ]
          })
        }}
      />
    <div className="min-h-screen bg-background text-foreground">
      <article className="max-w-3xl mx-auto px-4 py-20">
        <a href="/blog" className="text-primary text-sm hover:underline mb-8 inline-block">&larr; Back to blog</a>
        <div className="flex items-center gap-3 mb-4">
          <span className="px-3 py-1 text-[10px] font-mono uppercase tracking-widest text-primary border border-primary/30 rounded-full">Risk Management</span>
          <span className="text-xs text-muted">March 23, 2026</span>
          <span className="text-xs text-muted">&bull; 6 min read</span>
        </div>
        <h1 className="text-3xl md:text-4xl font-bold mb-8 tracking-tight">Position Sizing &amp; Risk Per Trade: The 2% Rule Explained</h1>

        <div className="space-y-6 text-muted leading-relaxed">
          <p>You can have the best strategy in the world and still blow your account with poor position sizing. It&apos;s not an exaggeration — position sizing is the single most important factor in long-term trading survival. A great system with bad sizing loses money. A mediocre system with smart sizing survives. Here&apos;s why the 2% rule exists and how to apply it correctly.</p>

          <h2 className="text-xl font-semibold text-foreground mt-8 mb-3">The Math of Ruin</h2>
          <p>Before discussing position sizing, you need to understand why it matters so deeply. Consider this: a 10% loss requires an 11.1% gain to recover. A 25% loss requires a 33.3% gain. A 50% loss requires a 100% gain — you need to <em>double</em> your remaining capital just to get back to where you started.</p>
          <p>This asymmetry is the reason traders go broke. Large losses don&apos;t just hurt — they create a mathematical hole that becomes exponentially harder to climb out of.</p>
          <div className="overflow-x-auto">
            <table className="w-full text-sm border-collapse">
              <thead>
                <tr className="border-b border-border/30">
                  <th className="text-center py-3 text-foreground">Loss</th>
                  <th className="text-center py-3 text-foreground">Gain Needed to Recover</th>
                </tr>
              </thead>
              <tbody>
                <tr className="border-b border-border/20"><td className="text-center py-3">5%</td><td className="text-center py-3">5.3%</td></tr>
                <tr className="border-b border-border/20"><td className="text-center py-3">10%</td><td className="text-center py-3">11.1%</td></tr>
                <tr className="border-b border-border/20"><td className="text-center py-3">20%</td><td className="text-center py-3">25.0%</td></tr>
                <tr className="border-b border-border/20"><td className="text-center py-3">33%</td><td className="text-center py-3">50.0%</td></tr>
                <tr className="border-b border-border/20"><td className="text-center py-3">50%</td><td className="text-center py-3">100.0%</td></tr>
                <tr><td className="text-center py-3">75%</td><td className="text-center py-3">300.0%</td></tr>
              </tbody>
            </table>
          </div>

          <h2 className="text-xl font-semibold text-foreground mt-8 mb-3">What Is the 2% Rule?</h2>
          <p>The 2% rule states: <strong className="text-foreground">never risk more than 2% of your total trading capital on a single trade</strong>. This is not the same as investing 2% of your capital. It means that if your stop-loss is hit, the maximum you lose is 2% of your account.</p>
          <p>If your account is $10,000, your maximum risk per trade is $200. If your stop-loss is 5% below your entry, you can take a position worth $4,000. If your stop-loss is 2% below entry, you can take a $10,000 position.</p>

          <h2 className="text-xl font-semibold text-foreground mt-8 mb-3">The Position Sizing Formula</h2>
          <div className="p-4 rounded-xl border border-border/30 bg-card/50 font-mono text-sm">
            <p className="text-foreground mb-2">Position Size = (Account Size &times; Risk %) / Stop-Loss Distance</p>
            <p className="text-xs mt-3">Example:</p>
            <p className="text-xs">Account: $10,000 | Risk: 2% ($200) | Stop: 4% from entry</p>
            <p className="text-xs">Position Size = $200 / 0.04 = <strong className="text-primary">$5,000</strong></p>
          </div>
          <p>This formula automatically adjusts your position size based on the volatility of the trade. A tight stop means a larger position; a wide stop means a smaller position. The dollar risk stays constant.</p>

          <h2 className="text-xl font-semibold text-foreground mt-8 mb-3">Why 2% Specifically?</h2>
          <p>The 2% figure comes from decades of quantitative research and real-world trading experience. Here&apos;s the logic:</p>
          <ul className="list-disc pl-6 space-y-2">
            <li><strong className="text-foreground">Surviving losing streaks</strong> — Even a system with a 70% win rate can experience 5-7 consecutive losses. At 2% risk per trade, seven losses in a row costs you about 13.5% of your account — painful but very survivable.</li>
            <li><strong className="text-foreground">Psychological sustainability</strong> — Losing 2% per trade doesn&apos;t trigger panic. Losing 10% per trade triggers emotional decision-making, which leads to revenge trading and further losses.</li>
            <li><strong className="text-foreground">Compounding protection</strong> — Because your risk is percentage-based, it shrinks automatically as your account shrinks, creating a natural brake against drawdowns.</li>
          </ul>

          <h2 className="text-xl font-semibold text-foreground mt-8 mb-3">Common Mistakes with Position Sizing</h2>
          <p><strong className="text-foreground">Mistake 1: Using a fixed dollar amount instead of a percentage.</strong> Risking $500 per trade sounds consistent, but as your account grows to $50,000, that&apos;s only 1% risk — you&apos;re leaving returns on the table. If your account drops to $5,000, that&apos;s 10% risk — you&apos;re gambling.</p>
          <p><strong className="text-foreground">Mistake 2: Ignoring correlation.</strong> If you have three open BTC, ETH, and SOL longs, and crypto sells off, all three hit their stop-losses simultaneously. You didn&apos;t risk 2% — you risked 6%. Correlated positions must be counted together.</p>
          <p><strong className="text-foreground">Mistake 3: Moving the stop-loss.</strong> Your position size was calculated for a specific stop distance. If you widen the stop &ldquo;to give it room,&rdquo; you&apos;ve just increased your risk beyond 2% without adjusting the position size.</p>

          <h2 className="text-xl font-semibold text-foreground mt-8 mb-3">How TrendRider Manages Position Sizing</h2>
          <p>Every TrendRider signal includes a recommended stop-loss and position size calculated against the 2% rule. The system goes further with additional safeguards:</p>
          <ul className="list-disc pl-6 space-y-2">
            <li><strong className="text-foreground">6% maximum stop-loss</strong> — No trade is entered with a stop wider than 6%, keeping position sizes meaningful even on volatile assets.</li>
            <li><strong className="text-foreground">Portfolio heat limit</strong> — TrendRider tracks the total risk across all open positions. If combined exposure exceeds a threshold, new signals are held until existing trades close.</li>
            <li><strong className="text-foreground">Confidence-adjusted sizing</strong> — Higher confidence signals receive slightly larger allocations (up to 2%), while lower confidence signals are sized down to 1-1.5%. This tilts capital toward the highest-probability setups.</li>
          </ul>
          <p>The result is a maximum drawdown of just <strong className="text-primary">low single-digit (see /live)</strong> across all tracked trades — proof that disciplined sizing works alongside the <a href="/blog/best-crypto-trading-strategies-2026" className="text-primary hover:underline">profitable crypto trading strategies</a> TrendRider deploys.</p>

          <h2 className="text-xl font-semibold text-foreground mt-8 mb-3">Quick Reference: Position Sizing by Account Size</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm border-collapse">
              <thead>
                <tr className="border-b border-border/30">
                  <th className="text-center py-3 text-foreground">Account Size</th>
                  <th className="text-center py-3 text-foreground">2% Risk ($)</th>
                  <th className="text-center py-3 text-foreground">Position (4% stop)</th>
                  <th className="text-center py-3 text-foreground">Position (6% stop)</th>
                </tr>
              </thead>
              <tbody>
                <tr className="border-b border-border/20"><td className="text-center py-3">$1,000</td><td className="text-center py-3">$20</td><td className="text-center py-3">$500</td><td className="text-center py-3">$333</td></tr>
                <tr className="border-b border-border/20"><td className="text-center py-3">$5,000</td><td className="text-center py-3">$100</td><td className="text-center py-3">$2,500</td><td className="text-center py-3">$1,667</td></tr>
                <tr className="border-b border-border/20"><td className="text-center py-3">$10,000</td><td className="text-center py-3">$200</td><td className="text-center py-3">$5,000</td><td className="text-center py-3">$3,333</td></tr>
                <tr className="border-b border-border/20"><td className="text-center py-3">$25,000</td><td className="text-center py-3">$500</td><td className="text-center py-3">$12,500</td><td className="text-center py-3">$8,333</td></tr>
                <tr><td className="text-center py-3">$50,000</td><td className="text-center py-3">$1,000</td><td className="text-center py-3">$25,000</td><td className="text-center py-3">$16,667</td></tr>
              </tbody>
            </table>
          </div>

          <h2 className="text-xl font-semibold text-foreground mt-8 mb-3">The Bottom Line</h2>
          <p>Position sizing isn&apos;t glamorous. Nobody brags about it on Twitter. But it&apos;s the difference between traders who last 10 years and traders who last 10 weeks. The 2% rule is not a suggestion — it&apos;s a survival mechanism. Master it, and you give your strategy the runway it needs to compound over time.</p>

          <div className="mt-10 p-6 rounded-2xl border border-primary/20 bg-primary/5 text-center">
            <p className="text-foreground font-medium mb-3">Every TrendRider signal includes pre-calculated position sizes and stop-losses</p>
            <a href="https://t.me/TrendRiderSignals" className="inline-block px-6 py-3 rounded-xl font-semibold text-sm" style={{ background: "linear-gradient(135deg, #00D4AA, #00B894)", color: "#0D1117" }}>
              Join TrendRider on Telegram &rarr;
            </a>
          </div>
        </div>

        <div className="mt-16 pt-10 border-t border-border/30">
          <h2 className="text-xl font-semibold text-foreground mb-6">Related Articles</h2>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <a href="/blog/risk-management-6-percent-stop-loss" className="p-4 rounded-xl border border-border/50 bg-card/30 hover:border-primary/30 hover:bg-card/50 transition-all">
              <span className="text-xs text-primary font-mono uppercase tracking-widest">Risk Management</span>
              <p className="text-sm font-medium text-foreground mt-2">The 6% Stop-Loss Rule: How We Keep Drawdown at low single-digit (see /live)</p>
            </a>
            <a href="/blog/understanding-win-rate-and-profit-factor" className="p-4 rounded-xl border border-border/50 bg-card/30 hover:border-primary/30 hover:bg-card/50 transition-all">
              <span className="text-xs text-primary font-mono uppercase tracking-widest">Education</span>
              <p className="text-sm font-medium text-foreground mt-2">Understanding Win Rate &amp; Profit Factor: What Really Matters</p>
            </a>
            <a href="/blog/paper-trading-vs-live-trading-when-to-switch" className="p-4 rounded-xl border border-border/50 bg-card/30 hover:border-primary/30 hover:bg-card/50 transition-all">
              <span className="text-xs text-primary font-mono uppercase tracking-widest">Education</span>
              <p className="text-sm font-medium text-foreground mt-2">Paper Trading vs Live Trading: When Is the Right Time to Go Live?</p>
            </a>
          </div>
        </div>
      </article>
    </div>
    </>
  );
}
