import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Trend-Following Crypto Strategy 2026: From -13% Donchian to +80% SuperTrend",
  description: "Honest backtest journey across 14 alts and 5 years. Donchian breakout failed -13% in bear markets. SuperTrend on daily timeframe earned +80% with 4-window walk-forward OOS validation. Real numbers, no marketing.",
  alternates: {
    canonical: "https://trendrider.net/blog/trend-following-crypto-strategy-supertrend-2026",
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
            "headline": "Trend-Following Crypto Strategy 2026: From -13% Donchian to +80% SuperTrend",
            "description": "Honest backtest journey across 14 alts and 5 years. Donchian failed; SuperTrend on daily timeframe earned +80% with walk-forward OOS validation.",
            "author": { "@type": "Person", "name": "TrendRider Team", "url": "https://trendrider.net" },
            "publisher": {
              "@type": "Organization",
              "name": "TrendRider",
              "url": "https://trendrider.net",
              "logo": { "@type": "ImageObject", "url": "https://trendrider.net/icon.svg" }
            },
            "datePublished": "2026-05-01",
            "dateModified": "2026-05-01",
            "image": "https://trendrider.net/opengraph-image",
            "mainEntityOfPage": {
              "@type": "WebPage",
              "@id": "https://trendrider.net/blog/trend-following-crypto-strategy-supertrend-2026"
            }
          })
        }}
      />
      <div className="min-h-screen bg-background text-foreground">
        <article className="max-w-3xl mx-auto px-4 py-20">
          <a href="/blog" className="text-primary text-sm hover:underline mb-8 inline-block">&larr; Back to blog</a>
          <div className="flex items-center gap-3 mb-4">
            <span className="px-3 py-1 text-[10px] font-mono uppercase tracking-widest text-primary border border-primary/30 rounded-full">Build in public</span>
            <span className="text-xs text-muted">May 1, 2026</span>
            <span className="text-xs text-muted">&bull; 14 min read</span>
          </div>
          <h1 className="text-3xl md:text-4xl font-bold mb-6 tracking-tight">
            Trend-Following Crypto Strategy 2026: From −13% Donchian to +80% SuperTrend
          </h1>
          <p className="text-muted leading-relaxed mb-8 italic">
            One day, four strategy variants, eleven failed backtests, and one critical insight that reframed the whole project. Real numbers, real failures, all code on <a href="https://github.com/darkvolg/trendrider-strategy" className="text-primary hover:underline" target="_blank" rel="noopener">GitHub</a>.
          </p>

          <div className="space-y-6 text-muted leading-relaxed">
            <h2 className="text-xl font-semibold text-foreground mt-8 mb-3">Where we started — a bot stuck at +2%/month</h2>
            <p>
              For the last 30 days the TrendRider bot has been running on a 1-hour timeframe across 14 crypto-alt pairs (XRP, DOGE, SOL, ETH, NEAR, OP, ATOM, AVAX, SUI, LINK, POL, BNB, DOT, ADA), earning a steady but small <strong className="text-foreground">~$10 / month on a $500 dry-run wallet</strong>. That works out to about +2% per month, or +24% annualised. Not bad — it&apos;s positive, the drawdowns are tiny (max 4.78% over 28 months), and the strategy never blew up.
            </p>
            <p>
              But also: not great. We tried 11 different optimisations in April — five hyperopt configurations and six structural modifications (loose exits, confidence sizing, MTF gates, chase guards, short-side variants, bear-only filters). Every single one regressed on the 480-day out-of-sample backtest. The pattern was clear: any modification to <em>this</em> strategy on <em>this</em> timeframe just made it worse.
            </p>
            <p>
              We were stuck at a local optimum. Time for a fundamental redesign.
            </p>

            <h2 className="text-xl font-semibold text-foreground mt-8 mb-3">The plan — go to daily timeframe, ride trends</h2>
            <p>
              The current bot trades hourly. Average trade duration was 9 hours 42 minutes — already longer than the candle. That&apos;s the signature of a chop-fighting system that gets prematurely exited by trailing stops every time a multi-day move happens. The fix, in theory, was straightforward: move to a daily timeframe, hold trades for weeks, ride sustained trends instead of micro-bounces.
            </p>
            <p>
              We picked Donchian breakout — Curtis Faith&apos;s original Turtle system, replicated in Andreas Clenow&apos;s <em>Following the Trend</em>. The most evidence-backed trend-following system in the public quant literature. Two parameters only (Donchian period and ATR multiplier), so minimal overfitting risk. Long when close prints a new 50-day high, exit on a 3×ATR Chandelier trail.
            </p>

            <h2 className="text-xl font-semibold text-foreground mt-8 mb-3">Donchian failed — and the diagnosis was instructive</h2>
            <div className="bg-card/50 border border-border/50 rounded-xl p-4 my-4">
              <table className="w-full text-sm font-mono">
                <thead className="text-foreground text-xs">
                  <tr className="border-b border-border/40">
                    <th className="text-left pb-2">Variant</th>
                    <th className="text-right pb-2">Bull period<br/>(market +149%)</th>
                  </tr>
                </thead>
                <tbody>
                  <tr className="border-b border-border/30">
                    <td className="py-2">Donchian v1</td>
                    <td className="text-right text-red-400">−13.59% / WR 21%</td>
                  </tr>
                  <tr className="border-b border-border/30">
                    <td className="py-2">v2 with BTC SMA(200) regime gate</td>
                    <td className="text-right text-red-400">−11.10% / WR 5.4%</td>
                  </tr>
                  <tr className="border-b border-border/30">
                    <td className="py-2">v3 with widened −50% hard floor</td>
                    <td className="text-right text-red-400">−11.31% / WR 14.8%</td>
                  </tr>
                  <tr>
                    <td className="py-2">v3-tight (2×ATR Chandelier)</td>
                    <td className="text-right text-red-400">−14.69% / WR 11.1%</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <p>
              All four variants <strong className="text-foreground">lost money during a bull rally</strong>. That&apos;s mathematically impossible if the strategy were working as designed — a +149% market should produce big winners trailing through ATR Chandelier. So what was going wrong?
            </p>
            <p>
              We exported every trade and looked at them individually. Pattern: ~85% of breakout entries land on <em>rally tops</em>. Donchian fires when close prints a new 50-day high — but on crypto alts, that high is often the local peak before an immediate pullback of 15-25%. Then the Chandelier trail trips on the giveback, and we exit at a smaller profit (or loss).
            </p>
            <p>
              The math: profit/loss ratio of 0.74 (winners are smaller than losers in percent terms). Combined with 14.8% win rate, that&apos;s an expected value of <strong className="text-foreground">−9.7% per trade</strong>. The system was structurally negative.
            </p>
            <p>
              Tightening the Chandelier (2×ATR instead of 3×) made it worse, not better — fewer winners, more whipsaws. Loosening it kept the giveback. The mismatch was at <em>concept level</em>, not parameter level. Donchian breakouts on crypto alts buy the rally top, period. We parked it.
            </p>

            <h2 className="text-xl font-semibold text-foreground mt-8 mb-3">The critical insight — V6A is a chop-feeder, not a trend-rider</h2>
            <p>
              Before trying another trend system, we ran a sanity check. The current TrendRider strategy on the same +149% bull period: <strong className="text-foreground">−1.89% / 26.6% win rate</strong>. The bot we&apos;ve been running for months <em>also</em> loses on bull markets.
            </p>
            <p>
              Re-reading the 836-day baseline (+4.99% during a −24% market) in this light: TrendRider isn&apos;t a trend-following system at all. It&apos;s a <strong className="text-foreground">chop-feeder</strong> — it harvests hourly micro-bounces in sideways and mild-bear conditions. During strong bulls it stagnates. During strong bears it edge-grinds upward.
            </p>
            <p>
              That reframes everything. A trend-following redesign isn&apos;t a <em>replacement</em> for the current bot — it&apos;s a <strong className="text-foreground">complement</strong>. They fish in different waters:
            </p>
            <ul className="list-disc pl-6 space-y-1.5">
              <li><strong className="text-foreground">Chop leg (current TrendRider)</strong>: high Sharpe, low drawdown, modest return in sideways/mild-bear (~80% of crypto-alt time).</li>
              <li><strong className="text-foreground">Trend leg (TBD)</strong>: high absolute return, accepts deeper drawdown, captures sustained bulls (~20% of time).</li>
            </ul>
            <p>
              Combine them via a regime classifier (BTC above 200-day SMA → trend leg active; else chop leg only) and you get the best of both. But first we need a working trend leg.
            </p>

            <h2 className="text-xl font-semibold text-foreground mt-8 mb-3">SuperTrend — entries on flips, not on highs</h2>
            <p>
              The Donchian post-mortem pointed at one thing: any system that <em>enters at a price extreme</em> will get whipsawed in crypto. We needed entries that fire on <strong className="text-foreground">trend direction changes</strong>, not on price levels.
            </p>
            <p>
              SuperTrend is the textbook answer. It uses ATR-based bands above and below price; when the indicator line flips from above price to below, that&apos;s a trend change to up. The flip often fires on a pullback or a recovery — not at a peak. The line itself becomes the trailing stop. Two parameters: ATR period (10) and ATR multiplier (3.0). Implementation: one call to <code className="text-xs bg-card px-2 py-0.5 rounded font-mono">pandas_ta.supertrend()</code>.
            </p>
            <p>
              Same daily timeframe, same 14-alt whitelist, same $500 wallet. We backtested across three windows:
            </p>
            <div className="bg-card/50 border border-border/50 rounded-xl p-4 my-4">
              <table className="w-full text-sm font-mono">
                <thead className="text-foreground text-xs">
                  <tr className="border-b border-border/40">
                    <th className="text-left pb-2">Window</th>
                    <th className="text-right pb-2">Days</th>
                    <th className="text-right pb-2">Market</th>
                    <th className="text-right pb-2">SuperTrend</th>
                    <th className="text-right pb-2">MaxDD</th>
                    <th className="text-right pb-2">WR</th>
                  </tr>
                </thead>
                <tbody>
                  <tr className="border-b border-border/30">
                    <td className="py-2">Bull rally Oct 2023 → May 2024</td>
                    <td className="text-right">213</td>
                    <td className="text-right text-emerald-400">+149%</td>
                    <td className="text-right text-emerald-400">+67.91%</td>
                    <td className="text-right">1.46%</td>
                    <td className="text-right">68.8%</td>
                  </tr>
                  <tr className="border-b border-border/30">
                    <td className="py-2">Same window as TrendRider baseline (836d)</td>
                    <td className="text-right">837</td>
                    <td className="text-right text-red-400">−20.6%</td>
                    <td className="text-right text-emerald-400">+10.98%</td>
                    <td className="text-right">24.23%</td>
                    <td className="text-right">27.4%</td>
                  </tr>
                  <tr>
                    <td className="py-2">Full 5 years 2021 → 2026</td>
                    <td className="text-right">1915</td>
                    <td className="text-right text-red-400">−46.5%</td>
                    <td className="text-right text-emerald-400">+80.68%</td>
                    <td className="text-right">16.88%</td>
                    <td className="text-right">34.1%</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <p>
              Every period positive. On the 836-day baseline window, SuperTrend doubles TrendRider&apos;s absolute return (+10.98% vs +4.99%). On the 5-year window, +80% return while the market dropped 46% — a 127-percentage-point spread vs buy-and-hold.
            </p>
            <p>
              The trade-off is visible: Sharpe and drawdown are worse than TrendRider on the same window. SuperTrend takes 24% drawdown vs 4.78% for TrendRider. That&apos;s the price for the upside. Trend systems live with deeper drawdowns; the question is whether you accept them in exchange for the rally capture.
            </p>

            <h2 className="text-xl font-semibold text-foreground mt-8 mb-3">Walk-forward OOS — is this overfit?</h2>
            <p>
              A single full-period backtest can hide overfitting. The honest test is walk-forward: split history into non-overlapping windows, run the strategy on each, see whether the edge survives across regimes. We split 2021-2026 into four windows of ~1.25-1.5 years each:
            </p>
            <div className="bg-card/50 border border-border/50 rounded-xl p-4 my-4">
              <table className="w-full text-sm font-mono">
                <thead className="text-foreground text-xs">
                  <tr className="border-b border-border/40">
                    <th className="text-left pb-2">Window</th>
                    <th className="text-right pb-2">Market</th>
                    <th className="text-right pb-2">SuperTrend</th>
                    <th className="text-right pb-2">Sortino</th>
                    <th className="text-right pb-2">MaxDD</th>
                  </tr>
                </thead>
                <tbody>
                  <tr className="border-b border-border/30">
                    <td className="py-2">2021-01 → 2022-04 (whipsaw bull)</td>
                    <td className="text-right">+12%</td>
                    <td className="text-right text-red-400">−0.88%</td>
                    <td className="text-right">−0.04</td>
                    <td className="text-right">16.19%</td>
                  </tr>
                  <tr className="border-b border-border/30">
                    <td className="py-2">2022-04 → 2023-07 (bear)</td>
                    <td className="text-right text-red-400">−58%</td>
                    <td className="text-right text-emerald-400">+14.84%</td>
                    <td className="text-right">0.98</td>
                    <td className="text-right">8.57%</td>
                  </tr>
                  <tr className="border-b border-border/30">
                    <td className="py-2">2023-07 → 2024-10 (bull)</td>
                    <td className="text-right text-emerald-400">+103%</td>
                    <td className="text-right text-emerald-400">+40.22%</td>
                    <td className="text-right">2.88</td>
                    <td className="text-right">16.37%</td>
                  </tr>
                  <tr>
                    <td className="py-2">2024-10 → 2026-04 (chop/bear)</td>
                    <td className="text-right text-red-400">−31%</td>
                    <td className="text-right text-emerald-400">+45.00%</td>
                    <td className="text-right">1.59</td>
                    <td className="text-right">20.51%</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <p>
              Three of four windows positive. The 2021-2022 minor loss is the well-known trend-system failure mode in vertical bull-with-rapid-corrections regimes (whipsaw) — and even there, MaxDD is bounded at 16% with only −0.88% return, survivable not catastrophic. Crucially, SuperTrend earns a positive return in <strong className="text-foreground">both</strong> bull AND bear windows, validating the trend-rider thesis.
            </p>
            <p>
              No period-specific overfit. The edge is genuine.
            </p>

            <h2 className="text-xl font-semibold text-foreground mt-8 mb-3">What we&apos;re doing now — parallel dry-run</h2>
            <p>
              SuperTrend is now running as a <strong className="text-foreground">parallel dry-run</strong> on our server, alongside the production TrendRider bot. Same whitelist, same $500 wallet, separate sqlite database, separate API port. Both bots see the same live market in real time. Telegram off (no notification spam). Both as <code className="text-xs bg-card px-2 py-0.5 rounded font-mono">systemd</code> services so they survive reboots.
            </p>
            <p>
              The decision date is <strong className="text-foreground">May 15, 2026</strong> — 14 days of live data. At that point we compare:
            </p>
            <ol className="list-decimal pl-6 space-y-1.5">
              <li>SuperTrend live vs SuperTrend backtest priors (catch live-vs-backtest divergence — the sanity check that catches data-leakage and look-ahead bugs).</li>
              <li>SuperTrend vs TrendRider on the same 14-day window (real side-by-side).</li>
            </ol>
            <p>
              If SuperTrend matches its backtest profile and beats TrendRider, we promote it — either solo or as a regime-switched ensemble (TrendRider on chop, SuperTrend on bulls). If it doesn&apos;t, we iterate.
            </p>
            <p>
              No live capital change today. The production bot stays on TrendRider v2.12.1 ExitFix until SuperTrend proves itself in real conditions.
            </p>

            <h2 className="text-xl font-semibold text-foreground mt-8 mb-3">What you can take away from this</h2>
            <ul className="list-disc pl-6 space-y-2">
              <li><strong className="text-foreground">Parameter tuning ≠ redesign.</strong> When eleven optimisations regress, you&apos;re at a local optimum. Stop tuning, change the regime.</li>
              <li><strong className="text-foreground">Backtest your strategy on the OPPOSITE market.</strong> If your &quot;trend system&quot; loses on a +149% bull, it&apos;s not a trend system. We thought TrendRider was a trend rider for two years — it isn&apos;t.</li>
              <li><strong className="text-foreground">Breakout entries are dangerous in crypto.</strong> ~85% of breakouts on alts buy the rally top. Use entries that fire on direction changes (SuperTrend, MA-cross with retracement, channel-midline buys).</li>
              <li><strong className="text-foreground">Walk-forward OOS is non-negotiable.</strong> A single full-period backtest can hide period-specific overfit. Four non-overlapping windows is the minimum honest test.</li>
              <li><strong className="text-foreground">Different strategies fish in different waters.</strong> Don&apos;t throw out a chop system because it loses on bulls; combine it with a trend system gated by regime.</li>
            </ul>

            <h2 className="text-xl font-semibold text-foreground mt-8 mb-3">Run the same bot yourself</h2>
            <p>
              Everything in this post — strategy code, configs, backtest exports — is on <a href="https://github.com/darkvolg/trendrider-strategy" className="text-primary hover:underline" target="_blank" rel="noopener">GitHub under MIT</a>. The live bot stats update every 60 seconds at <a href="/live" className="text-primary hover:underline">/live</a>, including the parallel SuperTrend dry-run once it accumulates trades. If you want to run it yourself you need a Bybit account (the exchange we test on), Freqtrade installed (see our <a href="/blog/freqtrade-setup-tutorial-beginners-2026" className="text-primary hover:underline">Freqtrade setup tutorial</a>), and <code className="text-xs bg-card px-2 py-0.5 rounded font-mono">pandas_ta</code> for the SuperTrend indicator.
            </p>

            <div className="mt-10 grid gap-4 sm:grid-cols-2">
              <div className="p-6 rounded-2xl border border-[#F7A600]/30 bg-[#F7A600]/5">
                <p className="text-foreground font-medium mb-1">No Bybit account yet?</p>
                <p className="text-muted text-sm mb-4">Register through our partner link — same exchange this whole article runs on. Fee discount + welcome bonus on signup.</p>
                <a href="https://www.bybit.com/invite?ref=0GDX5JR&utm_source=trendrider&utm_medium=blog_supertrend" target="_blank" rel="noopener nofollow sponsored" className="inline-block px-6 py-3 rounded-xl font-semibold text-sm" style={{ background: "linear-gradient(135deg, #F7A600, #FF9500)", color: "#0D1117" }}>
                  Open Bybit account &rarr;
                </a>
              </div>
              <div className="p-6 rounded-2xl border border-primary/20 bg-primary/5">
                <p className="text-foreground font-medium mb-1">Want updates as we ship?</p>
                <p className="text-muted text-sm mb-4">Telegram channel posts every signal and weekly performance updates. Free, no spam, unsubscribe any time.</p>
                <a href="https://t.me/TrendRiderSignals" className="inline-block px-6 py-3 rounded-xl font-semibold text-sm" style={{ background: "linear-gradient(135deg, #00D4AA, #00B894)", color: "#0D1117" }}>
                  Join on Telegram &rarr;
                </a>
              </div>
            </div>

            <p className="mt-10 text-xs text-muted/70">
              <strong>Disclaimer:</strong> Backtests and dry-runs are not guarantees of future live performance. Crypto markets are volatile and capital can be lost. Past returns are model-priors only. The numbers in this post are reproducible from public code; verify them yourself before acting on anything.
            </p>
          </div>

          <div className="mt-16 pt-10 border-t border-border/30">
            <h2 className="text-xl font-semibold text-foreground mb-6">Related Articles</h2>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              <a href="/blog/best-crypto-trading-strategies-2026" className="p-4 rounded-xl border border-border/50 bg-card/30 hover:border-primary/30 hover:bg-card/50 transition-all">
                <span className="text-xs text-primary font-mono uppercase tracking-widest">Strategy</span>
                <p className="text-sm font-medium text-foreground mt-2">7 Best Crypto Trading Strategies 2026</p>
              </a>
              <a href="/blog/freqtrade-setup-tutorial-beginners-2026" className="p-4 rounded-xl border border-border/50 bg-card/30 hover:border-primary/30 hover:bg-card/50 transition-all">
                <span className="text-xs text-primary font-mono uppercase tracking-widest">Tutorial</span>
                <p className="text-sm font-medium text-foreground mt-2">Freqtrade Setup 2026: Live Bot in 30 Minutes</p>
              </a>
              <a href="/blog/how-to-avoid-overfitting-crypto-trading" className="p-4 rounded-xl border border-border/50 bg-card/30 hover:border-primary/30 hover:bg-card/50 transition-all">
                <span className="text-xs text-primary font-mono uppercase tracking-widest">Backtesting</span>
                <p className="text-sm font-medium text-foreground mt-2">How to Avoid Overfitting in Crypto Backtests</p>
              </a>
            </div>
          </div>
        </article>
      </div>
    </>
  );
}
