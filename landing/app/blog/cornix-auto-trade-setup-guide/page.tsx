import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "How to Set Up Cornix Auto-Trade with TrendRider Signals — TrendRider Blog",
  description: "Step-by-step Cornix setup guide: connect to Bybit, Binance, or OKX, configure position sizing, and auto-trade TrendRider crypto signals hands-free.",
  alternates: {
    canonical: "https://trendrider.net/blog/cornix-auto-trade-setup-guide",
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
            "headline": "How to Set Up Cornix Auto-Trade with TrendRider Signals — TrendRider Blog",
            "description": "Step-by-step Cornix setup guide: connect to Bybit, Binance, or OKX, configure position sizing, and auto-trade TrendRider crypto signals hands-free.",
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
              "@id": "https://trendrider.net/blog/cornix-auto-trade-setup-guide"
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
              { "@type": "ListItem", "position": 3, "name": "How to Set Up Cornix Auto-Trade with TrendRider Signals — TrendRider Blog" }
            ]
          })
        }}
      />
    <div className="min-h-screen bg-background text-foreground">
      <article className="max-w-3xl mx-auto px-4 py-20">
        <a href="/blog" className="text-primary text-sm hover:underline mb-8 inline-block">&larr; Back to blog</a>
        <div className="flex items-center gap-3 mb-4">
          <span className="px-3 py-1 text-[10px] font-mono uppercase tracking-widest text-primary border border-primary/30 rounded-full">Guide</span>
          <span className="text-xs text-muted">March 19, 2026</span>
          <span className="text-xs text-muted">&bull; 7 min read</span>
        </div>
        <h1 className="text-3xl md:text-4xl font-bold mb-8 tracking-tight">How to Set Up Cornix Auto-Trade with TrendRider Signals</h1>

        <div className="space-y-6 text-muted leading-relaxed">
          <p>Getting great trading signals is only half the equation. The other half is <em>executing</em> those signals quickly, accurately, and without emotional interference. That&apos;s where <strong className="text-foreground">Cornix</strong> comes in &mdash; a Telegram-based auto-trading bot that reads signals from channels and executes them directly on your exchange account.</p>
          <p>This guide walks you through connecting Cornix with TrendRider signals on <strong className="text-foreground">Bybit</strong>, <strong className="text-foreground">Binance</strong>, or <strong className="text-foreground">OKX</strong> in about 10 minutes.</p>

          <h2 className="text-xl font-semibold text-foreground mt-8 mb-3">What Is Cornix?</h2>
          <p>Cornix is an automated trading bot that operates through Telegram. It monitors signal channels for trade messages, parses them automatically, and executes the trades on your connected exchange. It handles entries, take-profits, stop-losses, trailing stops, and position sizing &mdash; all without you touching your exchange.</p>
          <p>Key benefits:</p>
          <ul className="list-disc pl-6 space-y-2">
            <li><strong className="text-foreground">Speed</strong> &mdash; Executes within seconds of a signal being posted. No more missing entries because you were asleep or busy.</li>
            <li><strong className="text-foreground">Consistency</strong> &mdash; Follows every signal exactly as specified. No emotional overrides, no skipped trades.</li>
            <li><strong className="text-foreground">Risk management</strong> &mdash; Applies your predefined position sizing rules to every trade automatically.</li>
          </ul>

          <h2 className="text-xl font-semibold text-foreground mt-8 mb-3">Prerequisites</h2>
          <p>Before you start, make sure you have:</p>
          <ul className="list-disc pl-6 space-y-2">
            <li>A <strong className="text-foreground">Telegram account</strong></li>
            <li>An active <strong className="text-foreground">Cornix subscription</strong> (they offer a free trial) &mdash; visit <strong className="text-foreground">cornix.io</strong></li>
            <li>A verified account on <strong className="text-foreground">Bybit</strong>, <strong className="text-foreground">Binance</strong>, or <strong className="text-foreground">OKX</strong> with funds deposited</li>
            <li>Membership in the <strong className="text-foreground">TrendRider Signals</strong> Telegram channel</li>
          </ul>

          <h2 className="text-xl font-semibold text-foreground mt-8 mb-3">Step 1: Create API Keys on Your Exchange</h2>
          <p>API keys let Cornix place trades on your behalf without having access to withdraw funds. Always keep &ldquo;Withdraw&rdquo; permission disabled.</p>

          <h3 className="text-lg font-semibold text-foreground mt-6 mb-2">Bybit</h3>
          <ul className="list-disc pl-6 space-y-2">
            <li>Go to <strong className="text-foreground">Account &amp; Security &rarr; API Management</strong></li>
            <li>Click &ldquo;Create New Key&rdquo; &rarr; select &ldquo;System-generated API Keys&rdquo;</li>
            <li>Name it &ldquo;Cornix&rdquo; and set permissions: <strong className="text-foreground">Read + Trade</strong> (no Withdraw)</li>
            <li>Whitelist Cornix IP addresses (listed in Cornix docs) for extra security</li>
            <li>Save your API Key and Secret &mdash; you won&apos;t see the secret again</li>
          </ul>

          <h3 className="text-lg font-semibold text-foreground mt-6 mb-2">Binance</h3>
          <ul className="list-disc pl-6 space-y-2">
            <li>Go to <strong className="text-foreground">Profile &rarr; API Management</strong></li>
            <li>Create a new API key labeled &ldquo;Cornix&rdquo;</li>
            <li>Enable <strong className="text-foreground">Spot &amp; Margin Trading</strong> and/or <strong className="text-foreground">Futures Trading</strong></li>
            <li>Disable &ldquo;Enable Withdrawals&rdquo;</li>
            <li>Restrict to trusted IPs if possible</li>
          </ul>

          <h3 className="text-lg font-semibold text-foreground mt-6 mb-2">OKX</h3>
          <ul className="list-disc pl-6 space-y-2">
            <li>Go to <strong className="text-foreground">Settings &rarr; API</strong></li>
            <li>Create a new API key with <strong className="text-foreground">Trade</strong> permission</li>
            <li>You&apos;ll also get a passphrase &mdash; save this along with the key and secret</li>
            <li>Do not enable withdrawal permission</li>
          </ul>

          <h2 className="text-xl font-semibold text-foreground mt-8 mb-3">Step 2: Connect Your Exchange to Cornix</h2>
          <ul className="list-disc pl-6 space-y-2">
            <li>Open Telegram and start a chat with <strong className="text-foreground">@CornixTradingBot</strong></li>
            <li>Tap <strong className="text-foreground">/start</strong> and follow the onboarding flow</li>
            <li>Go to <strong className="text-foreground">Exchanges &rarr; Add Exchange</strong></li>
            <li>Select your exchange (Bybit / Binance / OKX)</li>
            <li>Paste your API Key, Secret, and passphrase (OKX only)</li>
            <li>Cornix will verify the connection with a test call &mdash; you should see a green checkmark</li>
          </ul>

          <h2 className="text-xl font-semibold text-foreground mt-8 mb-3">Step 3: Link TrendRider Channel</h2>
          <ul className="list-disc pl-6 space-y-2">
            <li>In Cornix, go to <strong className="text-foreground">Channels &rarr; Add Channel</strong></li>
            <li>Search for <strong className="text-foreground">TrendRider</strong> or paste the channel link</li>
            <li>Cornix will detect the signal format automatically &mdash; TrendRider signals are already formatted for Cornix compatibility</li>
            <li>Enable auto-trading for the channel</li>
          </ul>

          <h2 className="text-xl font-semibold text-foreground mt-8 mb-3">Step 4: Configure Position Sizing</h2>
          <p>This is the most important step for risk management. In Cornix settings:</p>
          <ul className="list-disc pl-6 space-y-2">
            <li><strong className="text-foreground">Position size method</strong> &mdash; We recommend &ldquo;Percentage of balance&rdquo; set to 1-3% per trade. This aligns with TrendRider&apos;s risk management philosophy.</li>
            <li><strong className="text-foreground">Leverage</strong> &mdash; TrendRider signals specify leverage. You can set Cornix to &ldquo;Follow signal&rdquo; or cap it at your comfort level (we suggest 3-5x max for beginners).</li>
            <li><strong className="text-foreground">Stop-loss</strong> &mdash; Set to &ldquo;Follow signal&rdquo; so Cornix uses TrendRider&apos;s built-in 6% stop-loss levels.</li>
            <li><strong className="text-foreground">Take-profit</strong> &mdash; Set to &ldquo;Follow signal&rdquo; to use TrendRider&apos;s multi-level TP targets.</li>
          </ul>

          <h2 className="text-xl font-semibold text-foreground mt-8 mb-3">Step 5: Test with a Small Amount</h2>
          <p>Before going live with your full allocation:</p>
          <ul className="list-disc pl-6 space-y-2">
            <li>Set position size to the minimum (e.g., $10-20 per trade)</li>
            <li>Wait for the next TrendRider signal to come through</li>
            <li>Verify in Cornix that the trade was detected and executed</li>
            <li>Check your exchange to confirm the position is open with the correct entry, SL, and TP levels</li>
            <li>Once confirmed, scale up to your target position size</li>
          </ul>

          <h2 className="text-xl font-semibold text-foreground mt-8 mb-3">Common Issues and Fixes</h2>
          <ul className="list-disc pl-6 space-y-2">
            <li><strong className="text-foreground">&ldquo;Insufficient balance&rdquo;</strong> &mdash; Make sure you have enough margin in your futures wallet, not just spot. Transfer funds if needed.</li>
            <li><strong className="text-foreground">&ldquo;API key invalid&rdquo;</strong> &mdash; Double-check you copied the full key and secret. Regenerate if necessary.</li>
            <li><strong className="text-foreground">&ldquo;Order not placed&rdquo;</strong> &mdash; Check that the trading pair is available on your exchange and that you have the correct permissions enabled on the API key.</li>
            <li><strong className="text-foreground">Trades not being detected</strong> &mdash; Ensure Cornix is added to the TrendRider channel and that auto-trading is enabled for that specific channel.</li>
          </ul>

          <h2 className="text-xl font-semibold text-foreground mt-8 mb-3">Security Best Practices</h2>
          <ul className="list-disc pl-6 space-y-2">
            <li><strong className="text-foreground">Never enable withdrawal permissions</strong> on API keys used for trading bots.</li>
            <li><strong className="text-foreground">Use IP whitelisting</strong> whenever your exchange supports it.</li>
            <li><strong className="text-foreground">Enable 2FA</strong> on both your Telegram account and exchange accounts.</li>
            <li><strong className="text-foreground">Review open positions regularly</strong> &mdash; automation doesn&apos;t mean you should stop monitoring entirely.</li>
          </ul>

          <div className="mt-10 p-6 rounded-2xl border border-primary/20 bg-primary/5 text-center">
            <p className="text-foreground font-medium mb-3">Get Cornix-ready signals delivered to Telegram</p>
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
              <p className="text-sm font-medium text-foreground mt-2">The 6% Stop-Loss Rule: How We Keep Drawdown at 1.42%</p>
            </a>
            <a href="/blog/paper-trading-vs-live-trading-when-to-switch" className="p-4 rounded-xl border border-border/50 bg-card/30 hover:border-primary/30 hover:bg-card/50 transition-all">
              <span className="text-xs text-primary font-mono uppercase tracking-widest">Education</span>
              <p className="text-sm font-medium text-foreground mt-2">Paper Trading vs Live Trading: When Is the Right Time to Go Live?</p>
            </a>
            <a href="/blog/position-sizing-and-risk-per-trade" className="p-4 rounded-xl border border-border/50 bg-card/30 hover:border-primary/30 hover:bg-card/50 transition-all">
              <span className="text-xs text-primary font-mono uppercase tracking-widest">Risk Management</span>
              <p className="text-sm font-medium text-foreground mt-2">Position Sizing &amp; Risk Per Trade: The 2% Rule Explained</p>
            </a>
          </div>
        </div>
      </article>
    </div>
    </>
  );
}
