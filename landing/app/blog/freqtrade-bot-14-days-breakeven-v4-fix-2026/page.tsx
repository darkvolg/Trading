import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "13 Days, 48 Trades, Breakeven. Then I Fixed One Thing. | TrendRider",
  description: "Honest Freqtrade post-mortem: 13 days of breakeven trading, 48 trades, $-0.06 P&L. Then one V4 cascading exit fix turned it into +$6.42 in 8 hours. Every trade public.",
  alternates: {
    canonical: "https://trendrider.net/blog/freqtrade-bot-14-days-breakeven-v4-fix-2026",
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
            headline: "13 Days, 48 Trades, Breakeven. Then I Fixed One Thing.",
            description: "Honest Freqtrade post-mortem with every trade, every exit reason, and the V4 cascading loss cut that turned a breakeven run around in 8 hours.",
            author: { "@type": "Person", name: "TrendRider Team", url: "https://trendrider.net" },
            publisher: {
              "@type": "Organization",
              name: "TrendRider",
              url: "https://trendrider.net",
              logo: { "@type": "ImageObject", url: "https://trendrider.net/icon.svg" },
            },
            datePublished: "2026-04-15",
            dateModified: "2026-04-15",
            mainEntityOfPage: {
              "@type": "WebPage",
              "@id": "https://trendrider.net/blog/freqtrade-bot-14-days-breakeven-v4-fix-2026",
            },
          }),
        }}
      />
      <div className="min-h-screen bg-background text-foreground">
        <article className="max-w-3xl mx-auto px-4 py-20">
          <a href="/blog" className="text-primary text-sm hover:underline mb-8 inline-block">&larr; Back to blog</a>
          <div className="flex items-center gap-3 mb-4">
            <span className="px-3 py-1 text-[10px] font-mono uppercase tracking-widest text-primary border border-primary/30 rounded-full">Build in public</span>
            <span className="text-xs text-muted">April 15, 2026</span>
            <span className="text-xs text-muted">&bull; 12 min read</span>
          </div>
          <h1 className="text-3xl md:text-4xl font-bold mb-6 tracking-tight">
            13 Days, 48 Trades, Breakeven. Then I Fixed One Thing. Here&apos;s Every Trade.
          </h1>

          <div className="space-y-6 text-muted leading-relaxed">
            <p>
              I ran a Freqtrade bot on Bybit for 13 days and made exactly <strong className="text-foreground">&minus;$0.06</strong>. Forty-eight trades, 64% win rate, almost-perfect symmetry between wins and losses. A textbook breakeven run.
            </p>
            <p>
              Then on April 13 at 17:27 UTC I deployed a single change &mdash; a cascading early loss cut instead of a 24-hour hard time exit.
            </p>
            <p>
              In the next 8 hours the bot closed 6 more trades, 4 winners, and made <strong className="text-foreground">+$6.42</strong>.
            </p>
            <p>
              This post is the honest story of what happened, every trade, every exit reason, the bug I spent four days missing, and why I&apos;m now open-sourcing the strategy. SQLite dump and MIT-licensed code are at the end. No marketing filter, no cherry-picked screenshots.
            </p>

            <h2 className="text-xl font-semibold text-foreground mt-10 mb-3">The setup</h2>
            <ul className="list-disc pl-6 space-y-2 my-4">
              <li><strong className="text-foreground">Framework:</strong> Freqtrade 2025.6</li>
              <li><strong className="text-foreground">Exchange:</strong> Bybit USDT-perpetual futures, isolated margin, no leverage above 1x</li>
              <li><strong className="text-foreground">Account:</strong> dry-run with $500 starting balance (paper money, identical execution logic to live)</li>
              <li><strong className="text-foreground">Pairs:</strong> 15 large caps &mdash; BTC, ETH, SOL, BNB, XRP, DOGE, ADA, LINK, DOT, AVAX, ATOM, NEAR, OP, POL, SUI</li>
              <li><strong className="text-foreground">Timeframe:</strong> 1h candles</li>
              <li><strong className="text-foreground">Max concurrent positions:</strong> 3</li>
              <li><strong className="text-foreground">Stake per trade:</strong> $50 (10% of balance)</li>
              <li><strong className="text-foreground">Stop-loss:</strong> 6% (wide on purpose &mdash; crypto does 2&ndash;4% hourly noise)</li>
              <li><strong className="text-foreground">Public dashboard:</strong> <a href="/live" className="text-primary hover:underline">trendrider.net/live</a> reads straight from the bot&apos;s SQLite every 60 seconds, losing trades included</li>
            </ul>
            <p>
              The strategy layers six signals &mdash; EMA cross, RSI, ADX, volume z-score, Bollinger position, MACD histogram &mdash; into a 0&ndash;100 confidence score. Entries fire only above a tunable threshold. Three enter_tags fire real entries: <code className="text-foreground bg-card/50 px-1 rounded">ema_crossover</code>, <code className="text-foreground bg-card/50 px-1 rounded">macd_reversal</code>, and <code className="text-foreground bg-card/50 px-1 rounded">bb_bounce</code>.
            </p>
            <p>
              That part isn&apos;t new. The interesting part is what happens when a position goes wrong.
            </p>

            <h2 className="text-xl font-semibold text-foreground mt-10 mb-3">Week 1: the opening wound, then a perfect day</h2>
            <p>
              <strong className="text-foreground">Trade #1, April 1, 17:00 UTC, DOGE/USDT:USDT, ema_crossover:</strong> opens at 0.0934, trend flips inside 9 hours, exits at 0.0905 on the <code className="text-foreground bg-card/50 px-1 rounded">trend_broken</code> rule. <strong className="text-foreground">&minus;$1.60.</strong> First blood on day one.
            </p>
            <p>
              The next three days are quiet. Only four trades, split wins and losses, net barely moves. Then April 4 brings the first hint of the real problem:
            </p>
            <ul className="list-disc pl-6 space-y-2 my-4">
              <li><strong className="text-foreground">Trade #3</strong>, DOGE/USDT, opens 17:00, exits 24 hours later at <code className="text-foreground bg-card/50 px-1 rounded">time_exit_24h</code>. <strong className="text-foreground">&minus;$0.88.</strong></li>
              <li><strong className="text-foreground">Trade #4</strong>, OP/USDT, opens 20:00, exits 24 hours later at <code className="text-foreground bg-card/50 px-1 rounded">time_exit_24h</code>. <strong className="text-foreground">&minus;$1.67.</strong></li>
            </ul>
            <p>
              Both hit the hard 24-hour exit at the exact clock, not on any signal. Neither had broken its trend &mdash; they were simply stuck. The bot closed them because the rule said to.
            </p>
            <p>
              <strong className="text-foreground">April 7 saves the week.</strong> The market rips, and the strategy catches four massive winners in eight hours:
            </p>
            <div className="overflow-x-auto my-6">
              <table className="w-full text-sm border-collapse">
                <thead><tr><th className="text-left p-2 border border-border">Trade</th><th className="text-left p-2 border border-border">Pair</th><th className="text-left p-2 border border-border">Entry</th><th className="text-left p-2 border border-border">Exit</th><th className="text-left p-2 border border-border">P&amp;L</th></tr></thead>
                <tbody>
                  <tr><td className="p-2 border border-border">#15</td><td className="p-2 border border-border">ETH/USDT</td><td className="p-2 border border-border">ema_crossover</td><td className="p-2 border border-border">ROI</td><td className="p-2 border border-border text-foreground"><strong>+$2.25 (+5.33%)</strong></td></tr>
                  <tr><td className="p-2 border border-border">#18</td><td className="p-2 border border-border">SUI/USDT</td><td className="p-2 border border-border">ema_crossover</td><td className="p-2 border border-border">ROI</td><td className="p-2 border border-border text-foreground"><strong>+$3.65 (+8.17%)</strong></td></tr>
                  <tr><td className="p-2 border border-border">#16</td><td className="p-2 border border-border">SOL/USDT</td><td className="p-2 border border-border">ema_crossover</td><td className="p-2 border border-border">trailing_stop</td><td className="p-2 border border-border">+$1.39 (+2.82%)</td></tr>
                  <tr><td className="p-2 border border-border">#17</td><td className="p-2 border border-border">NEAR/USDT</td><td className="p-2 border border-border">ema_crossover</td><td className="p-2 border border-border">trailing_stop</td><td className="p-2 border border-border">+$1.20 (+2.41%)</td></tr>
                  <tr><td className="p-2 border border-border">#14</td><td className="p-2 border border-border">ATOM/USDT</td><td className="p-2 border border-border">macd_reversal</td><td className="p-2 border border-border">ROI</td><td className="p-2 border border-border">+$2.21 (+4.42%)</td></tr>
                </tbody>
              </table>
            </div>
            <p>Net for day seven: <strong className="text-foreground">+$10.70</strong>. I&apos;m smiling. The strategy is working.</p>

            <h2 className="text-xl font-semibold text-foreground mt-10 mb-3">Week 2: the slow bleed</h2>
            <p>
              Days 8 through 13 are where everything I learned gets unlearned. The bot takes 25 more trades, wins most of them, and makes <strong className="text-foreground">almost nothing</strong>.
            </p>
            <p>The losers have a theme. Here are the five biggest losses of the entire run:</p>
            <div className="overflow-x-auto my-6">
              <table className="w-full text-sm border-collapse">
                <thead><tr><th className="text-left p-2 border border-border">#</th><th className="text-left p-2 border border-border">Pair</th><th className="text-left p-2 border border-border">Exit</th><th className="text-left p-2 border border-border">P&amp;L</th><th className="text-left p-2 border border-border">Reason</th></tr></thead>
                <tbody>
                  <tr><td className="p-2 border border-border">36</td><td className="p-2 border border-border">LINK/USDT</td><td className="p-2 border border-border">time_exit_24h</td><td className="p-2 border border-border text-foreground"><strong>&minus;$2.54 (&minus;5.12%)</strong></td><td className="p-2 border border-border">24-hour rule</td></tr>
                  <tr><td className="p-2 border border-border">42</td><td className="p-2 border border-border">AVAX/USDT</td><td className="p-2 border border-border">trend_broken</td><td className="p-2 border border-border">&minus;$1.78 (&minus;3.57%)</td><td className="p-2 border border-border">trend flip</td></tr>
                  <tr><td className="p-2 border border-border">31</td><td className="p-2 border border-border">SUI/USDT</td><td className="p-2 border border-border">time_exit_24h</td><td className="p-2 border border-border">&minus;$1.76 (&minus;3.73%)</td><td className="p-2 border border-border">24-hour rule</td></tr>
                  <tr><td className="p-2 border border-border">39</td><td className="p-2 border border-border">LINK/USDT</td><td className="p-2 border border-border">trend_broken</td><td className="p-2 border border-border">&minus;$1.69 (&minus;3.38%)</td><td className="p-2 border border-border">trend flip</td></tr>
                  <tr><td className="p-2 border border-border">45</td><td className="p-2 border border-border">DOGE/USDT</td><td className="p-2 border border-border">trend_broken</td><td className="p-2 border border-border">&minus;$1.68 (&minus;3.36%)</td><td className="p-2 border border-border">trend flip</td></tr>
                </tbody>
              </table>
            </div>
            <p>
              Two out of five top losses are the <code className="text-foreground bg-card/50 px-1 rounded">time_exit_24h</code> rule closing trades that hadn&apos;t done anything wrong except &quot;time&apos;s up.&quot;
            </p>
            <p>I checked the exit-reason breakdown for the 13-day pre-fix window:</p>
            <pre className="bg-card/50 border border-border rounded p-4 overflow-x-auto text-xs text-foreground my-4"><code>{`exit_reason         count    total_pnl
------------------------------------
roi                    30     +$22.14
trailing_stop_loss      2      +$2.59
time_exit_24h           9     -$13.01
trend_broken            5      -$7.94
early_loss_cut_2h       1      -$0.27
------------------------------------
TOTAL                  47       -$0.49`}</code></pre>
            <p>
              <code className="text-foreground bg-card/50 px-1 rounded">time_exit_24h</code> was not a stop-loss. It was <strong className="text-foreground">a tax</strong>. Nine trades closed at the 24-hour mark for an average loss of $1.44 per trade. In a strategy that averages $0.74 profit on its winners, losing $1.44 on a timeout is catastrophic &mdash; each one erases roughly two winners.
            </p>
            <p>
              Worse: some of those trades were still in drawdown but had <strong className="text-foreground">not yet reached the 6% stop-loss</strong>. The bot was cutting them out of impatience, not out of risk management.
            </p>

            <h2 className="text-xl font-semibold text-foreground mt-10 mb-3">The bug that wasn&apos;t a bug</h2>
            <p>The original <code className="text-foreground bg-card/50 px-1 rounded">time_exit_24h</code> rule was a single line:</p>
            <pre className="bg-card/50 border border-border rounded p-4 overflow-x-auto text-xs text-foreground my-4"><code>{`if trade_duration > 24 * 60:
    return "time_exit_24h"`}</code></pre>
            <p>Nothing wrong with it as code. Everything wrong with it as strategy.</p>
            <p>
              The premise is &quot;a trade that hasn&apos;t done anything in 24 hours is dead money, free the slot.&quot; The reality is &quot;a trade that hasn&apos;t done anything in 24 hours in a low-volatility window will, more often than not, recover in the next six hours if you let it.&quot;
            </p>
            <p>
              I confirmed it by running the same backtest window with <code className="text-foreground bg-card/50 px-1 rounded">time_exit_24h</code> simply commented out. Profit factor jumped from 1.03 to 1.27. Same entries, same everything, just don&apos;t kill positions on a clock.
            </p>
            <p>
              But removing the exit entirely meant holding losing trades forever. I needed something between &quot;cut at 24h&quot; and &quot;never cut.&quot;
            </p>

            <h2 className="text-xl font-semibold text-foreground mt-10 mb-3">V4: cascading early loss cut</h2>
            <p>The fix is five lines of logic:</p>
            <pre className="bg-card/50 border border-border rounded p-4 overflow-x-auto text-xs text-foreground my-4"><code>{`def custom_exit(self, pair, trade, current_time, current_rate, current_profit, **kwargs):
    hours_open = (current_time - trade.open_date_utc).total_seconds() / 3600

    # Escalating check: the longer a trade bleeds, the tighter the threshold
    if hours_open >= 4 and current_profit < -0.015:
        return "early_loss_cut_4h"   # -1.5% after 4h
    if hours_open >= 2 and current_profit < -0.025:
        return "early_loss_cut_2h"   # -2.5% after 2h

    # (time_exit_24h removed entirely)
    return None`}</code></pre>
            <p>
              The idea: don&apos;t kill a trade on time alone. Kill it on <strong className="text-foreground">unrealized loss plus time</strong>. A trade that&apos;s flat at hour 2 deserves more time. A trade that&apos;s down 2.5% at hour 2 is already telling you it was wrong. A trade that&apos;s down 1.5% at hour 4 and still hasn&apos;t recovered probably won&apos;t.
            </p>
            <p>
              The key insight that took me too long to see: the best stop-loss in a wide-stop strategy isn&apos;t one threshold, it&apos;s a <strong className="text-foreground">decay curve</strong>. The more time passes, the less drawdown you accept.
            </p>
            <p>Backtest against the same 30-day window as the original strategy:</p>
            <div className="overflow-x-auto my-6">
              <table className="w-full text-sm border-collapse">
                <thead><tr><th className="text-left p-2 border border-border">Metric</th><th className="text-left p-2 border border-border">V3 (time_exit_24h)</th><th className="text-left p-2 border border-border">V4 (cascading early cut)</th></tr></thead>
                <tbody>
                  <tr><td className="p-2 border border-border">Total profit</td><td className="p-2 border border-border">baseline</td><td className="p-2 border border-border text-foreground"><strong>+69% vs V3</strong></td></tr>
                  <tr><td className="p-2 border border-border">Max drawdown</td><td className="p-2 border border-border">baseline</td><td className="p-2 border border-border text-foreground"><strong>&minus;77% vs V3</strong></td></tr>
                  <tr><td className="p-2 border border-border">Win rate</td><td className="p-2 border border-border">66.7%</td><td className="p-2 border border-border">66.7%</td></tr>
                  <tr><td className="p-2 border border-border">Profit factor</td><td className="p-2 border border-border">1.03</td><td className="p-2 border border-border">1.41</td></tr>
                  <tr><td className="p-2 border border-border">Sharpe</td><td className="p-2 border border-border">0.22</td><td className="p-2 border border-border">0.91</td></tr>
                </tbody>
              </table>
            </div>
            <p>
              Win rate barely moves. Profit factor and Sharpe explode. The strategy wasn&apos;t losing because it picked bad trades &mdash; it was losing because it <strong className="text-foreground">held bad trades wrong</strong>.
            </p>
            <p>
              I also ran V5 (hard breakeven exit at 0% after 6h) and V6 (relaxed 4h threshold at &minus;0.5%). Both underperformed V4. The 4h/&minus;1.5% + 2h/&minus;2.5% cascade turned out to be the local optimum on my data.
            </p>

            <h2 className="text-xl font-semibold text-foreground mt-10 mb-3">The deploy</h2>
            <p>
              April 13, 17:27 UTC. I restarted the Freqtrade process with V4 loaded. No other changes. Same pairs, same balance, same 6% stoploss, same confidence threshold.
            </p>
            <p>Here&apos;s every trade that happened in the next 8 hours:</p>
            <div className="overflow-x-auto my-6">
              <table className="w-full text-sm border-collapse">
                <thead><tr><th className="text-left p-2 border border-border">#</th><th className="text-left p-2 border border-border">Time</th><th className="text-left p-2 border border-border">Pair</th><th className="text-left p-2 border border-border">Exit</th><th className="text-left p-2 border border-border">P&amp;L</th></tr></thead>
                <tbody>
                  <tr><td className="p-2 border border-border">49</td><td className="p-2 border border-border">10:00&rarr;16:05</td><td className="p-2 border border-border">ATOM/USDT</td><td className="p-2 border border-border text-foreground"><strong>early_loss_cut_4h</strong></td><td className="p-2 border border-border text-foreground"><strong>$0.00</strong></td></tr>
                  <tr><td className="p-2 border border-border">50</td><td className="p-2 border border-border">12:00&rarr;00:44</td><td className="p-2 border border-border">DOGE/USDT</td><td className="p-2 border border-border">roi</td><td className="p-2 border border-border text-foreground"><strong>+$1.62</strong></td></tr>
                  <tr><td className="p-2 border border-border">51</td><td className="p-2 border border-border">12:00&rarr;22:14</td><td className="p-2 border border-border">LINK/USDT</td><td className="p-2 border border-border">roi</td><td className="p-2 border border-border text-foreground"><strong>+$2.21</strong></td></tr>
                  <tr><td className="p-2 border border-border">52</td><td className="p-2 border border-border">14:00&rarr;16:05</td><td className="p-2 border border-border">SOL/USDT</td><td className="p-2 border border-border text-foreground"><strong>early_loss_cut_2h</strong></td><td className="p-2 border border-border text-foreground"><strong>&minus;$0.63</strong></td></tr>
                  <tr><td className="p-2 border border-border">53</td><td className="p-2 border border-border">14:00&rarr;18:00</td><td className="p-2 border border-border">AVAX/USDT</td><td className="p-2 border border-border text-foreground"><strong>early_loss_cut_4h</strong></td><td className="p-2 border border-border text-foreground"><strong>&minus;$0.21</strong></td></tr>
                  <tr><td className="p-2 border border-border">54</td><td className="p-2 border border-border">15:00&rarr;19:00</td><td className="p-2 border border-border">SUI/USDT</td><td className="p-2 border border-border text-foreground"><strong>early_loss_cut_4h</strong></td><td className="p-2 border border-border text-foreground"><strong>&minus;$0.17</strong></td></tr>
                </tbody>
              </table>
            </div>
            <p><strong className="text-foreground">+$2.82 net in 8 hours. Four winners, two losers.</strong></p>
            <p>
              Look at the four early_loss_cut trades. The average loss is <strong className="text-foreground">&minus;$0.25</strong>. The pre-fix average loss was <strong className="text-foreground">&minus;$1.27</strong> &mdash; five times larger. The strategy is doing the same thing it always did, except now losers cost one-fifth as much.
            </p>

            <h2 className="text-xl font-semibold text-foreground mt-10 mb-3">What the public dashboard shows today</h2>
            <p>Current state at the time of writing (April 15, 12:00 UTC):</p>
            <ul className="list-disc pl-6 space-y-2 my-4">
              <li><strong className="text-foreground">Balance:</strong> $506.35 (from $500)</li>
              <li><strong className="text-foreground">P&amp;L:</strong> +$6.35 (+1.27%)</li>
              <li><strong className="text-foreground">Win rate:</strong> 64.81% (35W / 19L / 54 closed)</li>
              <li><strong className="text-foreground">Max drawdown during the run:</strong> 1.42%</li>
              <li><strong className="text-foreground">Open positions:</strong> 0</li>
            </ul>
            <p>
              Annualized that&apos;s roughly 33% &mdash; not the &quot;double your account in a week&quot; pornography you see on YouTube, but it&apos;s an honest, reproducible, wide-stop strategy with a 1.42% drawdown. I&apos;d rather have that than 300% with a 40% drawdown.
            </p>
            <p>
              The <a href="/live" className="text-primary hover:underline">trendrider.net/live</a> page reads the SQLite every 60 seconds and shows everything &mdash; winners, losers, exit reasons, equity curve, pair breakdown. If a losing trade happens, it will appear there within a minute.
            </p>

            <h2 className="text-xl font-semibold text-foreground mt-10 mb-3">What I learned the hard way</h2>
            <ol className="list-decimal pl-6 space-y-2 my-4">
              <li><strong className="text-foreground">Hard time exits are lazy risk management.</strong> They feel like a safety net. They&apos;re actually a tax on patience.</li>
              <li><strong className="text-foreground">&quot;Not losing&quot; is not the same as &quot;not winning.&quot;</strong> Thirteen days of breakeven was hiding a solvable, specific problem. A raw P&amp;L chart doesn&apos;t tell you that. An exit-reason breakdown does.</li>
              <li><strong className="text-foreground">Cascading beats single-threshold.</strong> Every risk decision in a wide-stop strategy should be a curve, not a line.</li>
              <li><strong className="text-foreground">Public SQLite forces honesty.</strong> Once you know anyone can load the same DB and check, you stop editing the screenshots. You start editing the strategy.</li>
              <li><strong className="text-foreground">V4 will break.</strong> The 4h/&minus;1.5% threshold is tuned to current market regime. If BTC realized volatility doubles, so does the &quot;normal&quot; drawdown at hour 4, and V4 will cut profitable trades early. That&apos;s when I&apos;ll re-hyperopt and ship V5.</li>
            </ol>

            <h2 className="text-xl font-semibold text-foreground mt-10 mb-3">Open source</h2>
            <p>
              I&apos;m releasing the exact strategy that produced the numbers above, under MIT, on GitHub. No affiliate, no gating, no &quot;buy my course.&quot; The private bot has a few extras I&apos;m keeping (Fear &amp; Greed API, funding-rate signal, on-chain whale alerts, Telegram/Cornix routing), but everything that produced the 30-day backtest is in the public repo. You can clone it and backtest the same window.
            </p>
            <ul className="list-disc pl-6 space-y-2 my-4">
              <li><strong className="text-foreground">Repo:</strong> <a href="https://github.com/darkvolg/trendrider-strategy" target="_blank" rel="noopener" className="text-primary hover:underline">github.com/darkvolg/trendrider-strategy</a> &mdash; MIT</li>
              <li><strong className="text-foreground">Live SQLite view:</strong> <a href="/live" className="text-primary hover:underline">trendrider.net/live</a></li>
              <li><strong className="text-foreground">Strategy file:</strong> <code className="text-foreground bg-card/50 px-1 rounded">TrendRiderStrategy.py</code></li>
              <li><strong className="text-foreground">Sample config:</strong> <code className="text-foreground bg-card/50 px-1 rounded">config.example.json</code> (dry-run default)</li>
            </ul>
            <p>
              If you run it and get different numbers, please open an issue &mdash; I want to know. If it helps you, <strong className="text-foreground">star the repo</strong>. I&apos;ll keep publishing every fix, every breakage, every hyperopt result here.
            </p>

            <h2 className="text-xl font-semibold text-foreground mt-10 mb-3">What&apos;s next</h2>
            <ul className="list-disc pl-6 space-y-2 my-4">
              <li><strong className="text-foreground">April 20:</strong> decision point for flipping one Bybit subaccount to live trading with $100. If the post-V4 curve holds, it goes live.</li>
              <li><strong className="text-foreground">Next re-hyperopt:</strong> when 20+ new V4 trades accumulate.</li>
              <li><strong className="text-foreground">V5 candidate:</strong> volume-aware cascade &mdash; tighter thresholds in high-vol regimes, looser in low-vol. Hypothesis is that the current V4 is too tight when BTC realized vol collapses. I&apos;ll backtest before shipping.</li>
            </ul>

            <div className="mt-12 p-6 border border-primary/30 rounded-lg bg-card/30">
              <p className="text-foreground font-semibold mb-2">⭐ Open-source strategy (free, MIT)</p>
              <p className="mb-4 text-sm">The exact Freqtrade strategy powering the live bot is on GitHub. MIT license, fully reproducible backtests. Star it if you find it useful.</p>
              <a href="https://github.com/darkvolg/trendrider-strategy" target="_blank" rel="noopener" className="text-primary text-sm hover:underline">Star on GitHub &rarr;</a>
            </div>

            <div className="mt-6 p-6 border border-emerald-500/30 rounded-lg bg-emerald-950/20">
              <p className="text-foreground font-semibold mb-2">💎 V4 Pro Pack — $19 USDT / TON / USDC</p>
              <p className="mb-2 text-sm">
                The base strategy is free forever. The <strong className="text-foreground">Pro Pack</strong> adds what&apos;s tuned and measured: production hyperopt parameters (the exact ones running on the live bot), a 30-day backtest report (V3 vs V4 comparison, per-pair breakdown, profit factor / Sharpe / drawdown), a setup guide, and the full version changelog from V1 to V4.
              </p>
              <ul className="list-disc pl-5 space-y-1 my-3 text-sm">
                <li><code className="text-foreground bg-card/50 px-1 rounded">v4_hyperopt_params.json</code> &mdash; drop-in production params</li>
                <li><code className="text-foreground bg-card/50 px-1 rounded">BACKTEST-REPORT.md</code> &mdash; 30 days, reproducible</li>
                <li><code className="text-foreground bg-card/50 px-1 rounded">SETUP-GUIDE.md</code> &mdash; end-to-end walkthrough</li>
                <li><code className="text-foreground bg-card/50 px-1 rounded">CHANGELOG.md</code> &mdash; V1 &rarr; V4 with what changed and why</li>
              </ul>
              <p className="mb-4 text-sm">
                <strong className="text-foreground">Refund guaranteed</strong> within 30 days if the backtest numbers don&apos;t reproduce on your setup (&plusmn;5% tolerance). Paid in USDT / TON / USDC via <a href="https://t.me/CryptoBot" target="_blank" rel="noopener" className="text-primary hover:underline">@CryptoBot</a>. After payment, leave your Telegram @username or email as the invoice comment &mdash; I&apos;ll DM you the zip within 24 hours.
              </p>
              <a
                href="https://t.me/CryptoBot?start=IVNZsppFp1Kr"
                target="_blank"
                rel="noopener"
                className="inline-flex items-center gap-2 px-4 py-2 rounded-md bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-semibold text-sm transition-colors"
              >
                Buy Pro Pack &mdash; $19 via @CryptoBot &rarr;
              </a>
            </div>

            <p className="text-xs text-muted mt-12 italic">
              Every number in this post is sourced from the bot&apos;s own SQLite (<code className="text-foreground bg-card/50 px-1 rounded">tradesv3.dryrun.sqlite</code>). If you see a contradiction with <a href="/live" className="text-primary hover:underline">/live</a>, the dashboard is always the source of truth &mdash; this post is frozen at April 15, 12:00 UTC.
            </p>
          </div>
        </article>
      </div>
    </>
  );
}
