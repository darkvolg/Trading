import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Understanding Win Rate & Profit Factor — TrendRider Blog",
  description: "Learn how win rate, profit factor, drawdown, and SQN score work together to measure true trading performance.",
};

export default function Article() {
  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify({
            "@context": "https://schema.org",
            "@type": "BlogPosting",
            "headline": "Understanding Win Rate & Profit Factor — TrendRider Blog",
            "description": "Learn how win rate, profit factor, drawdown, and SQN score work together to measure true trading performance.",
            "author": {
              "@type": "Organization",
              "name": "TrendRider",
              "url": "https://trendrider.net"
            },
            "publisher": {
              "@type": "Organization",
              "name": "TrendRider",
              "url": "https://trendrider.net"
            },
            "datePublished": "2026-03-22",
            "mainEntityOfPage": {
              "@type": "WebPage",
              "@id": "https://trendrider.net/blog/understanding-win-rate-and-profit-factor"
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
              { "@type": "ListItem", "position": 3, "name": "Understanding Win Rate & Profit Factor — TrendRider Blog" }
            ]
          })
        }}
      />
    <div className="min-h-screen bg-background text-foreground">
      <article className="max-w-3xl mx-auto px-4 py-20">
        <a href="/blog" className="text-primary text-sm hover:underline mb-8 inline-block">&larr; Back to blog</a>
        <div className="flex items-center gap-3 mb-4">
          <span className="px-3 py-1 text-[10px] font-mono uppercase tracking-widest text-primary border border-primary/30 rounded-full">Education</span>
          <span className="text-xs text-muted">March 15, 2026</span>
          <span className="text-xs text-muted">&bull; 4 min read</span>
        </div>
        <h1 className="text-3xl md:text-4xl font-bold mb-8 tracking-tight">Understanding Win Rate &amp; Profit Factor: What Really Matters</h1>

        <div className="space-y-6 text-muted leading-relaxed">
          <p>A signal service claiming &ldquo;90% win rate&rdquo; sounds impressive — until you realize their average win is $10 and their average loss is $100. Win rate alone is meaningless without context. Here&apos;s what you should actually look at.</p>

          <h2 className="text-xl font-semibold text-foreground mt-8 mb-3">Win Rate: The Starting Point</h2>
          <p>Win rate is simply the percentage of trades that close in profit. TrendRider&apos;s 67.9% win rate means that roughly 7 out of 10 trades hit at least one take-profit target. But this number only tells part of the story.</p>

          <h2 className="text-xl font-semibold text-foreground mt-8 mb-3">Profit Factor: The Real Metric</h2>
          <p>Profit factor = gross profit / gross loss. A profit factor of 1.0 means you&apos;re breaking even. Anything above 2.0 is considered excellent. TrendRider&apos;s profit factor of <strong className="text-primary">2.12x</strong> means for every $1 lost, we make $2.12 in profit.</p>

          <h2 className="text-xl font-semibold text-foreground mt-8 mb-3">Maximum Drawdown: Risk Control</h2>
          <p>Drawdown measures the largest peak-to-trough decline in your account. Most retail traders experience 20-40% drawdowns. TrendRider&apos;s max drawdown of <strong className="text-primary">1.42%</strong> is exceptionally low because of strict 6% stop-loss per trade and never risking more than 2% of portfolio per position.</p>

          <h2 className="text-xl font-semibold text-foreground mt-8 mb-3">SQN Score: System Quality</h2>
          <p>The System Quality Number (SQN), developed by Van Tharp, rates trading systems on a scale. Scores above 2.5 are &ldquo;good,&rdquo; above 3.0 are &ldquo;excellent.&rdquo; TrendRider&apos;s SQN of <strong className="text-primary">3.45</strong> places it in the &ldquo;excellent&rdquo; category.</p>

          <h2 className="text-xl font-semibold text-foreground mt-8 mb-3">The Complete Picture</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm border-collapse">
              <thead>
                <tr className="border-b border-border/30">
                  <th className="text-left py-3 text-foreground">Metric</th>
                  <th className="text-center py-3 text-foreground">Industry Average</th>
                  <th className="text-center py-3 text-primary">TrendRider</th>
                </tr>
              </thead>
              <tbody>
                <tr className="border-b border-border/20"><td className="py-3">Win Rate</td><td className="text-center">45-55%</td><td className="text-center text-primary font-semibold">67.9%</td></tr>
                <tr className="border-b border-border/20"><td className="py-3">Profit Factor</td><td className="text-center">1.0-1.5x</td><td className="text-center text-primary font-semibold">2.12x</td></tr>
                <tr className="border-b border-border/20"><td className="py-3">Max Drawdown</td><td className="text-center">15-30%</td><td className="text-center text-primary font-semibold">1.42%</td></tr>
                <tr><td className="py-3">SQN Score</td><td className="text-center">1.5-2.5</td><td className="text-center text-primary font-semibold">3.45</td></tr>
              </tbody>
            </table>
          </div>

          <div className="mt-10 p-6 rounded-2xl border border-primary/20 bg-primary/5 text-center">
            <p className="text-foreground font-medium mb-3">See all our trades — fully transparent</p>
            <a href="https://docs.google.com/spreadsheets/d/1ZWRJ0PcBSk910MZv426PrleriBnInykr3OebWXJPm-g" className="inline-block px-6 py-3 rounded-xl font-semibold text-sm" style={{ background: "linear-gradient(135deg, #00D4AA, #00B894)", color: "#0D1117" }}>
              View Live Results &rarr;
            </a>
          </div>
        </div>
      </article>
    </div>
    </>
  );
}
