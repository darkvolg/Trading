import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "The 6% Stop-Loss Rule — TrendRider Blog",
  description: "Learn TrendRider's exact risk management framework: 6% stop-loss per trade, 2% portfolio risk, and how we maintain 1.81% max drawdown.",
};

export default function Article() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <article className="max-w-3xl mx-auto px-4 py-20">
        <a href="/blog" className="text-primary text-sm hover:underline mb-8 inline-block">&larr; Back to blog</a>
        <div className="flex items-center gap-3 mb-4">
          <span className="px-3 py-1 text-[10px] font-mono uppercase tracking-widest text-primary border border-primary/30 rounded-full">Risk Management</span>
          <span className="text-xs text-muted">March 10, 2026</span>
          <span className="text-xs text-muted">&bull; 6 min read</span>
        </div>
        <h1 className="text-3xl md:text-4xl font-bold mb-8 tracking-tight">The 6% Stop-Loss Rule: How We Keep Drawdown at 1.81%</h1>

        <div className="space-y-6 text-muted leading-relaxed">
          <p>The number one reason traders blow their accounts isn&apos;t bad entries — it&apos;s poor risk management. A single trade without a stop-loss can wipe out months of profits. Here&apos;s the exact framework TrendRider uses to protect capital.</p>

          <h2 className="text-xl font-semibold text-foreground mt-8 mb-3">Rule 1: 6% Maximum Stop-Loss Per Trade</h2>
          <p>Every TrendRider signal includes a predefined stop-loss that never exceeds 6% from entry. This means even in the worst-case scenario, a single trade can only lose 6% of the position size. Most of our stops are tighter — the 6% is the absolute maximum.</p>

          <h2 className="text-xl font-semibold text-foreground mt-8 mb-3">Rule 2: 2% Portfolio Risk Per Position</h2>
          <p>We never risk more than 2% of total portfolio value on any single trade. If your portfolio is $10,000, no trade risks more than $200. This means even a string of 5 consecutive losses only costs 10% — painful but recoverable.</p>

          <h2 className="text-xl font-semibold text-foreground mt-8 mb-3">Rule 3: Multi-Target Take Profits</h2>
          <p>Every signal has 3 take-profit levels with position scaling:</p>
          <ul className="list-disc pl-6 space-y-2">
            <li><strong className="text-foreground">TP1 (30% of position)</strong> — Conservative target, usually 3-4% above entry. Locks in profit early.</li>
            <li><strong className="text-foreground">TP2 (40% of position)</strong> — Mid-range target, 5-7%. Where most of the profit comes from.</li>
            <li><strong className="text-foreground">TP3 (30% of position)</strong> — Aggressive target, 8-12%. Captures extended moves.</li>
          </ul>

          <h2 className="text-xl font-semibold text-foreground mt-8 mb-3">Rule 4: No Averaging Down</h2>
          <p>TrendRider never adds to losing positions. If a trade hits the stop-loss, it closes. No exceptions. No &ldquo;dollar-cost averaging into a trade.&rdquo; This single rule prevents the catastrophic losses that destroy accounts.</p>

          <h2 className="text-xl font-semibold text-foreground mt-8 mb-3">The Result: 1.81% Max Drawdown</h2>
          <p>These four rules combined produce a maximum drawdown of just 1.81% across all backtested trades. For comparison, the average retail trader experiences 20-40% drawdowns. Professional hedge funds target 10-15%. Our 1.81% is in a different league entirely.</p>

          <h2 className="text-xl font-semibold text-foreground mt-8 mb-3">Why This Matters for You</h2>
          <p>With Cornix auto-trade, these risk management rules are enforced automatically. You don&apos;t need discipline — the algorithm handles it. Every stop-loss is placed before the trade opens. Every take-profit scales exactly as designed.</p>

          <div className="mt-10 p-6 rounded-2xl border border-primary/20 bg-primary/5 text-center">
            <p className="text-foreground font-medium mb-3">Trade with institutional risk management</p>
            <a href="https://t.me/TrendRiderSignals" className="inline-block px-6 py-3 rounded-xl font-semibold text-sm" style={{ background: "linear-gradient(135deg, #00D4AA, #00B894)", color: "#0D1117" }}>
              Start with TrendRider &rarr;
            </a>
          </div>
        </div>
      </article>
    </div>
  );
}
