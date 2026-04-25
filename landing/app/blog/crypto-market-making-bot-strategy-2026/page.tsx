import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Crypto Market Making Bot Strategy: How Market Makers Profit in 2026",
  description: "Market making bots sound profitable but most retail traders lose money. See real spread data, Hummingbot setup, and why trend following wins.",
  alternates: {
    canonical: "https://trendrider.net/blog/crypto-market-making-bot-strategy-2026",
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
            "headline": "Crypto Market Making Bot Strategy: How Market Makers Profit in 2026",
            "description": "Learn how crypto market making bots capture spread profit in 2026. Covers bid-ask mechanics, inventory risk, and comparison to trend following strategies.",
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
            "datePublished": "2026-04-02",
            "dateModified": "2026-04-02",
            "image": "https://trendrider.net/opengraph-image",
            "mainEntityOfPage": {
              "@type": "WebPage",
              "@id": "https://trendrider.net/blog/crypto-market-making-bot-strategy-2026"
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
              { "@type": "ListItem", "position": 3, "name": "Crypto Market Making Bot Strategy [2026]" }
            ]
          })
        }}
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify({
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": [
              {
                "@type": "Question",
                "name": "Is crypto market making profitable for retail traders in 2026?",
                "acceptedAnswer": {
                  "@type": "Answer",
                  "text": "Market making is extremely difficult for retail traders. Professional market makers use co-located servers, $100K+ capital, and custom low-latency infrastructure. Retail traders face wider spreads, higher latency, and inventory risk that institutional players manage with sophisticated hedging. Most retail market making bots lose money after fees. Trend-following strategies are generally more accessible and profitable for retail traders."
                }
              },
              {
                "@type": "Question",
                "name": "What is the difference between market making and trend following?",
                "acceptedAnswer": {
                  "@type": "Answer",
                  "text": "Market making profits from the bid-ask spread by simultaneously placing buy and sell orders, earning small amounts on each completed round trip. It works best in sideways markets. Trend following profits from directional price movements by entering positions when a trend is confirmed and riding it until reversal signals appear. It works best in trending markets. Market making requires high capital and low latency; trend following requires good indicators and risk management."
                }
              },
              {
                "@type": "Question",
                "name": "What is inventory risk in market making?",
                "acceptedAnswer": {
                  "@type": "Answer",
                  "text": "Inventory risk is the primary danger in market making. When you place buy and sell orders, one side often fills before the other. If you accumulate a large long position and the market drops, your unrealized losses can vastly exceed the spread income you earned. Professional market makers hedge inventory risk using derivatives, delta-neutral strategies, and dynamic order adjustment. Unhedged inventory risk is the #1 reason retail market making bots fail."
                }
              },
              {
                "@type": "Question",
                "name": "What software do crypto market makers use?",
                "acceptedAnswer": {
                  "@type": "Answer",
                  "text": "Open-source options include Hummingbot (most popular, supports 20+ exchanges), Tribeca, and custom Python bots using ccxt. Professional firms build proprietary systems in C++ or Rust for sub-millisecond execution. For testing, Hummingbot is the best starting point as it provides pre-built market making strategies with configurable spread, order size, and inventory management parameters."
                }
              },
              {
                "@type": "Question",
                "name": "How much capital do you need for crypto market making?",
                "acceptedAnswer": {
                  "@type": "Answer",
                  "text": "Serious market making requires $10,000-50,000 minimum to maintain meaningful order book depth and handle inventory risk. On low-liquidity pairs (which offer wider spreads), you might start with $5,000. However, the capital efficiency is much lower than trend following — market making might earn 0.5-2% monthly on large capital, while trend following systems can target 2-10% monthly on smaller accounts. For most retail traders, $1,000-5,000 in a trend-following bot is a better use of capital."
                }
              }
            ]
          })
        }}
      />

      <main className="min-h-screen bg-[#0a0a0f] text-gray-200">
        <article className="mx-auto max-w-3xl px-4 py-16 sm:px-6">
          <a
            href="/blog"
            className="mb-8 inline-flex items-center text-sm text-cyan-400 hover:text-cyan-300"
          >
            &larr; Back to Blog
          </a>

          <div className="mb-6 flex items-center gap-3">
            <span className="rounded-full bg-cyan-500/10 px-3 py-1 text-xs font-medium text-cyan-400">
              Strategy
            </span>
            <span className="text-sm text-gray-500">April 2, 2026</span>
            <span className="text-sm text-gray-500">&middot;</span>
            <span className="text-sm text-gray-500">11 min read</span>
          </div>

          <h1 className="bg-gradient-to-r from-white to-gray-400 bg-clip-text text-3xl font-bold tracking-tight text-transparent sm:text-4xl">
            Crypto Market Making Bot Strategy: How Market Makers Profit in 2026
          </h1>

          <p className="mt-6 mb-4 leading-relaxed text-gray-300">
            Market making is one of the oldest and most misunderstood strategies in trading. While trend followers wait for directional moves, market makers profit from the <strong className="text-white">bid-ask spread</strong> &mdash; the gap between the highest price a buyer will pay and the lowest price a seller will accept.
          </p>
          <p className="mb-4 leading-relaxed text-gray-300">
            In crypto, where spreads can be 5&ndash;50x wider than in traditional markets, market making bots have become a $2+ billion industry. But is this strategy viable for retail traders, or is it reserved for institutions with co-located servers and seven-figure capital? This guide breaks down the mechanics, the math, and the honest reality.
          </p>

          <img
            src="/opengraph-image"
            alt="Diagram showing how a market making bot places simultaneous buy and sell orders around the mid-price to capture spread profit"
            className="my-8 w-full rounded-xl border border-gray-800"
          />

          <h2 className="mt-12 mb-4 text-2xl font-semibold text-white">
            How Market Making Works: The Basics
          </h2>
          <p className="mb-4 leading-relaxed text-gray-300">
            A market maker continuously places limit orders on both sides of the order book. For example, if BTC/USDT is trading at $65,000:
          </p>
          <ul className="mb-6 list-disc space-y-2 pl-6 text-gray-300">
            <li>
              <strong className="text-white">Buy order (bid):</strong> $64,980 &mdash; willing to buy at $20 below mid-price
            </li>
            <li>
              <strong className="text-white">Sell order (ask):</strong> $65,020 &mdash; willing to sell at $20 above mid-price
            </li>
          </ul>
          <p className="mb-4 leading-relaxed text-gray-300">
            If both orders fill, the market maker earns the <strong className="text-white">$40 spread</strong> (0.06% on $65,000). This sounds small, but market makers execute hundreds or thousands of these round trips per day. At 500 round trips per day with a $40 average spread on $65,000 positions, the daily gross profit is $20,000.
          </p>
          <p className="mb-4 leading-relaxed text-gray-300">
            Of course, this simplified example ignores the two forces that eat market making profits alive: <strong className="text-white">fees and inventory risk</strong>.
          </p>

          <h2 className="mt-12 mb-4 text-2xl font-semibold text-white">
            The Math Behind Spread Capture
          </h2>
          <p className="mb-4 leading-relaxed text-gray-300">
            Let us work through a realistic example on Bybit perpetual futures:
          </p>
          <div className="mb-6 overflow-x-auto rounded-lg border border-gray-800">
            <table className="w-full text-left text-sm text-gray-300">
              <thead className="border-b border-gray-800 bg-gray-900/50 text-xs uppercase text-gray-400">
                <tr>
                  <th className="px-4 py-3">Parameter</th>
                  <th className="px-4 py-3">Value</th>
                </tr>
              </thead>
              <tbody>
                <tr className="border-b border-gray-800/50">
                  <td className="px-4 py-3 font-medium text-white">Trading pair</td>
                  <td className="px-4 py-3">BTC/USDT perpetual</td>
                </tr>
                <tr className="border-b border-gray-800/50">
                  <td className="px-4 py-3 font-medium text-white">Spread target</td>
                  <td className="px-4 py-3">0.05% ($32.50 on $65,000)</td>
                </tr>
                <tr className="border-b border-gray-800/50">
                  <td className="px-4 py-3 font-medium text-white">Maker fee</td>
                  <td className="px-4 py-3">0.01% (Bybit VIP tier)</td>
                </tr>
                <tr className="border-b border-gray-800/50">
                  <td className="px-4 py-3 font-medium text-white">Round-trip fees</td>
                  <td className="px-4 py-3">0.02% ($13.00)</td>
                </tr>
                <tr className="border-b border-gray-800/50">
                  <td className="px-4 py-3 font-medium text-white">Net per round trip</td>
                  <td className="px-4 py-3 text-green-400">$19.50 (0.03%)</td>
                </tr>
                <tr>
                  <td className="px-4 py-3 font-medium text-white">Round trips per day</td>
                  <td className="px-4 py-3">50&ndash;200</td>
                </tr>
              </tbody>
            </table>
          </div>
          <p className="mb-4 leading-relaxed text-gray-300">
            At 100 successful round trips per day, the daily gross is $1,950 before inventory risk. But here is the problem: <strong className="text-white">not every round trip completes</strong>. In trending markets, one side fills and the other does not, leaving you with a directional position that can lose far more than the spread income.
          </p>

          <h2 className="mt-12 mb-4 text-2xl font-semibold text-white">
            Inventory Risk: The Market Maker&apos;s Nemesis
          </h2>
          <p className="mb-4 leading-relaxed text-gray-300">
            Inventory risk is why market making is far harder than it looks. Consider this scenario:
          </p>
          <ol className="mb-6 list-decimal space-y-3 pl-6 text-gray-300">
            <li>
              Your bot places a buy at $64,980 and a sell at $65,020.
            </li>
            <li>
              A sudden sell-off hits. Your buy order fills at $64,980. The sell order does not fill because price is dropping.
            </li>
            <li>
              Price drops to $64,500. You now hold a position with $480 unrealized loss &mdash; equivalent to <strong className="text-white">24 successful spread captures</strong> wiped out in seconds.
            </li>
            <li>
              Your bot places a new sell order at $64,520. But the market keeps falling. More inventory accumulates.
            </li>
            <li>
              By the time price stabilizes, you have absorbed $2,000+ in losses that would take 100+ successful round trips to recover.
            </li>
          </ol>
          <p className="mb-4 leading-relaxed text-gray-300">
            Professional market makers manage inventory risk through several mechanisms:
          </p>
          <ul className="mb-6 list-disc space-y-2 pl-6 text-gray-300">
            <li>
              <strong className="text-white">Dynamic spread adjustment</strong> &mdash; Widen the spread when inventory is imbalanced. If you are holding too much long exposure, make your buy price less attractive and your sell price more competitive.
            </li>
            <li>
              <strong className="text-white">Inventory limits</strong> &mdash; Hard caps on maximum position size. Once reached, the bot only places orders to reduce inventory.
            </li>
            <li>
              <strong className="text-white">Delta hedging</strong> &mdash; Using options or correlated assets to offset directional exposure. For example, shorting ETH futures to hedge accumulated BTC long inventory.
            </li>
            <li>
              <strong className="text-white">Volatility-based pausing</strong> &mdash; Detect high-volatility regimes (via ATR or Bollinger Band width) and stop quoting until conditions normalize.
            </li>
          </ul>

          <img
            src="/opengraph-image"
            alt="Chart showing inventory accumulation during a downtrend with unrealized losses exceeding cumulative spread profits"
            className="my-8 w-full rounded-xl border border-gray-800"
          />

          <h2 className="mt-12 mb-4 text-2xl font-semibold text-white">
            Market Making vs Trend Following: Honest Comparison
          </h2>
          <p className="mb-4 leading-relaxed text-gray-300">
            Understanding when each strategy excels is crucial for choosing the right approach:
          </p>
          <div className="mb-6 overflow-x-auto rounded-lg border border-gray-800">
            <table className="w-full text-left text-sm text-gray-300">
              <thead className="border-b border-gray-800 bg-gray-900/50 text-xs uppercase text-gray-400">
                <tr>
                  <th className="px-4 py-3">Factor</th>
                  <th className="px-4 py-3">Market Making</th>
                  <th className="px-4 py-3">Trend Following</th>
                </tr>
              </thead>
              <tbody>
                <tr className="border-b border-gray-800/50">
                  <td className="px-4 py-3 font-medium text-white">Best market condition</td>
                  <td className="px-4 py-3">Sideways, low volatility</td>
                  <td className="px-4 py-3">Trending, moderate volatility</td>
                </tr>
                <tr className="border-b border-gray-800/50">
                  <td className="px-4 py-3 font-medium text-white">Minimum capital</td>
                  <td className="px-4 py-3 text-red-400">$10,000&ndash;50,000</td>
                  <td className="px-4 py-3 text-green-400">$500&ndash;5,000</td>
                </tr>
                <tr className="border-b border-gray-800/50">
                  <td className="px-4 py-3 font-medium text-white">Latency requirements</td>
                  <td className="px-4 py-3 text-red-400">Critical (&lt;10ms)</td>
                  <td className="px-4 py-3 text-green-400">Not critical (seconds OK)</td>
                </tr>
                <tr className="border-b border-gray-800/50">
                  <td className="px-4 py-3 font-medium text-white">Trades per day</td>
                  <td className="px-4 py-3">100&ndash;1,000+</td>
                  <td className="px-4 py-3">2&ndash;20</td>
                </tr>
                <tr className="border-b border-gray-800/50">
                  <td className="px-4 py-3 font-medium text-white">Fee sensitivity</td>
                  <td className="px-4 py-3 text-red-400">Extremely high</td>
                  <td className="px-4 py-3 text-green-400">Moderate</td>
                </tr>
                <tr className="border-b border-gray-800/50">
                  <td className="px-4 py-3 font-medium text-white">Retail-friendly?</td>
                  <td className="px-4 py-3 text-red-400">Difficult</td>
                  <td className="px-4 py-3 text-green-400">Yes</td>
                </tr>
                <tr>
                  <td className="px-4 py-3 font-medium text-white">Expected monthly return</td>
                  <td className="px-4 py-3">0.5&ndash;3% (on large capital)</td>
                  <td className="px-4 py-3">2&ndash;10% (on moderate capital)</td>
                </tr>
              </tbody>
            </table>
          </div>
          <p className="mb-4 leading-relaxed text-gray-300">
            The comparison is stark. Market making requires <strong className="text-white">10&ndash;20x more capital</strong>, generates lower percentage returns, and demands infrastructure that most retail traders cannot afford. The advantage is consistency in sideways markets where trend followers get whipsawed &mdash; but crypto spends the majority of time in trending phases, which favors trend-following approaches.
          </p>
          <p className="mb-4 leading-relaxed text-gray-300">
            For a deeper understanding of trend following strategies,{" "}
            <a
              href="/blog/best-crypto-trading-strategies-2026"
              className="text-cyan-400 underline decoration-cyan-400/30 hover:text-cyan-300"
            >
              our guide to the best crypto trading strategies in 2026
            </a>{" "}
            covers trend following, mean reversion, breakout, and momentum approaches with real performance data.
          </p>

          <h2 className="mt-12 mb-4 text-2xl font-semibold text-white">
            Building a Market Making Bot: Tools and Framework
          </h2>
          <p className="mb-4 leading-relaxed text-gray-300">
            If you want to experiment with market making, <strong className="text-white">Hummingbot</strong> is the most accessible open-source framework. It provides pre-built market making strategies with configurable parameters:
          </p>
          <pre className="mb-6 overflow-x-auto rounded-lg bg-gray-900 p-4 text-sm text-gray-300">
{`# Hummingbot pure market making configuration
strategy: pure_market_making
exchange: bybit
market: BTC-USDT
bid_spread: 0.05%        # Buy 0.05% below mid price
ask_spread: 0.05%        # Sell 0.05% above mid price
order_amount: 0.01       # BTC per order
order_levels: 3          # 3 orders on each side
inventory_skew: true     # Adjust prices based on inventory
inventory_target: 0.5    # Target 50/50 base/quote balance`}
          </pre>
          <p className="mb-4 leading-relaxed text-gray-300">
            Key configuration parameters to tune:
          </p>
          <ul className="mb-6 list-disc space-y-2 pl-6 text-gray-300">
            <li>
              <strong className="text-white">Spread width</strong> &mdash; Wider spreads mean fewer fills but higher profit per fill. Start at 0.05&ndash;0.1% and adjust based on the pair&apos;s typical spread.
            </li>
            <li>
              <strong className="text-white">Order levels</strong> &mdash; Multiple orders at different prices increase fill probability. 3&ndash;5 levels on each side is typical.
            </li>
            <li>
              <strong className="text-white">Inventory skew</strong> &mdash; Essential for risk management. When holding excess inventory, the bot shifts prices to incentivize trades that reduce exposure.
            </li>
            <li>
              <strong className="text-white">Order refresh time</strong> &mdash; How often to cancel and replace orders. 10&ndash;30 seconds for volatile pairs, 30&ndash;60 seconds for stable ones.
            </li>
          </ul>

          <h2 className="mt-12 mb-4 text-2xl font-semibold text-white">
            Which Pairs Work Best for Market Making?
          </h2>
          <p className="mb-4 leading-relaxed text-gray-300">
            Not all pairs are suitable for market making. The ideal characteristics are:
          </p>
          <ol className="mb-6 list-decimal space-y-2 pl-6 text-gray-300">
            <li>
              <strong className="text-white">Moderate liquidity</strong> &mdash; Too liquid (BTC/USDT) and you compete with institutional market makers using co-located servers. Too illiquid and you face large slippage and unreliable fills. Mid-cap pairs like SOL/USDT or AVAX/USDT often hit the sweet spot.
            </li>
            <li>
              <strong className="text-white">Wide natural spreads</strong> &mdash; Pairs with 0.05&ndash;0.3% natural spreads give you room to capture profit after fees. BTC/USDT on Bybit has 0.01% spreads &mdash; impossible to profit after 0.02% round-trip fees.
            </li>
            <li>
              <strong className="text-white">Low volatility periods</strong> &mdash; Market making during news events or high volatility is extremely dangerous. Filter by ATR or Bollinger Band width and reduce or stop quoting during volatile periods.
            </li>
            <li>
              <strong className="text-white">High funding rates</strong> &mdash; If funding rates are highly positive, market makers can earn additional income from short positions while providing liquidity. This adds a directional edge to an otherwise neutral strategy.
            </li>
          </ol>
          <p className="mb-4 leading-relaxed text-gray-300">
            For a thorough analysis of pair selection criteria,{" "}
            <a
              href="/blog/best-crypto-trading-pairs-for-bots-2026"
              className="text-cyan-400 underline decoration-cyan-400/30 hover:text-cyan-300"
            >
              see our guide to choosing the best crypto trading pairs for bots
            </a>.
          </p>

          <h2 className="mt-12 mb-4 text-2xl font-semibold text-white">
            3 Reasons Most Retail Market Making Bots Fail
          </h2>
          <p className="mb-4 leading-relaxed text-gray-300">
            After analyzing hundreds of retail market making setups, these are the dominant failure modes:
          </p>
          <ol className="mb-6 list-decimal space-y-3 pl-6 text-gray-300">
            <li>
              <strong className="text-white">Competing against professionals</strong> &mdash; On high-liquidity pairs, you are competing against firms with $10M+ capital, co-located servers (&lt;1ms latency vs your 50ms), and teams of quantitative researchers. Your 0.05% spread target gets undercut by firms offering 0.02%.
            </li>
            <li>
              <strong className="text-white">Unhedged inventory exposure</strong> &mdash; Most retail market makers do not hedge. When the market trends strongly in one direction, accumulated inventory generates losses that dwarf months of spread income. A 5% move against your inventory on a $10,000 position is $500 &mdash; potentially more than a week of spread profits.
            </li>
            <li>
              <strong className="text-white">Fee structure disadvantage</strong> &mdash; Institutional market makers negotiate 0.00&ndash;0.01% maker fees through volume agreements. Retail traders pay 0.02&ndash;0.04% maker fees, which can consume 30&ndash;60% of spread income. At standard Bybit rates (0.02% maker), a 0.05% spread yields only 0.01% net per round trip &mdash; razor-thin margins where a single bad trade erases 50+ good ones.
            </li>
          </ol>

          <h2 className="mt-12 mb-4 text-2xl font-semibold text-white">
            When Market Making Makes Sense for Retail
          </h2>
          <p className="mb-4 leading-relaxed text-gray-300">
            Despite the challenges, there are specific scenarios where retail market making can work:
          </p>
          <ul className="mb-6 list-disc space-y-2 pl-6 text-gray-300">
            <li>
              <strong className="text-white">New token launches</strong> &mdash; When a token first lists, spreads are wide (0.5&ndash;2%) and professional market makers have not arrived yet. Early retail market makers can capture significant spread for the first hours or days.
            </li>
            <li>
              <strong className="text-white">DEX liquidity provision</strong> &mdash; Decentralized exchanges like Uniswap use automated market maker (AMM) pools. Providing liquidity earns fees from every swap. However, impermanent loss is the DEX equivalent of inventory risk and must be understood before committing capital.
            </li>
            <li>
              <strong className="text-white">Niche/low-cap pairs</strong> &mdash; Pairs with $1&ndash;10M daily volume often have no professional market makers. Spreads of 0.1&ndash;0.5% are common, and your $5,000 in liquidity can represent a meaningful portion of the order book.
            </li>
            <li>
              <strong className="text-white">Exchange incentive programs</strong> &mdash; Some exchanges offer maker fee rebates or liquidity mining rewards that make market making artificially profitable. Check if your exchange has an active maker incentive program.
            </li>
          </ul>

          <img
            src="/opengraph-image"
            alt="Comparison chart showing market making profitability on high-liquidity pairs versus low-liquidity niche pairs with wider spreads"
            className="my-8 w-full rounded-xl border border-gray-800"
          />

          <h2 className="mt-12 mb-4 text-2xl font-semibold text-white">
            The Verdict: Trend Following Wins for Most Traders
          </h2>
          <p className="mb-4 leading-relaxed text-gray-300">
            Market making is a fascinating strategy with elegant math, but the practical reality for retail traders in 2026 is clear: <strong className="text-white">trend-following strategies offer better risk-adjusted returns with lower capital requirements and simpler infrastructure</strong>.
          </p>
          <p className="mb-4 leading-relaxed text-gray-300">
            Consider the numbers: TrendRider&apos;s trend-following system achieves a{" "}
            <strong className="text-white">documented backtest win rate (current value on /live) with only low maximum drawdown (see /live)</strong>{" "}
            using multi-indicator scoring and strict risk management. This performance is achieved on a moderate capital base without co-located servers, custom firmware, or institutional fee arrangements.
          </p>
          <p className="mb-4 leading-relaxed text-gray-300">
            Market making can complement a trend-following approach for traders with larger accounts who want to monetize sideways market conditions. But as a primary strategy for retail traders, the infrastructure requirements and inventory risk make it a poor fit compared to{" "}
            <a
              href="/blog/ema-crossover-strategy-crypto-guide"
              className="text-cyan-400 underline decoration-cyan-400/30 hover:text-cyan-300"
            >
              proven EMA crossover strategies
            </a>{" "}
            or{" "}
            <a
              href="/blog/multi-indicator-scoring-system-crypto"
              className="text-cyan-400 underline decoration-cyan-400/30 hover:text-cyan-300"
            >
              multi-indicator scoring systems
            </a>.
          </p>

          <h2 className="mt-12 mb-4 text-2xl font-semibold text-white">
            Key Takeaways
          </h2>
          <ul className="mb-6 list-disc space-y-2 pl-6 text-gray-300">
            <li>
              Market making profits from the bid-ask spread, not directional moves &mdash; ideal for sideways markets but dangerous in trends.
            </li>
            <li>
              Inventory risk is the primary killer. Unhedged positions during trends can erase months of spread income in hours.
            </li>
            <li>
              Retail traders face structural disadvantages: higher fees, higher latency, and less capital than institutional competitors.
            </li>
            <li>
              Trend following offers better returns, lower capital requirements, and simpler infrastructure for 95% of retail traders.
            </li>
            <li>
              Market making can work in niche scenarios: new token launches, DEX liquidity pools, and low-cap pairs with wide spreads.
            </li>
          </ul>
          <p className="mb-4 leading-relaxed text-gray-300">
            If you want to see how a data-driven trend-following approach performs in real markets, explore{" "}
            <a
              href="/"
              className="text-cyan-400 underline decoration-cyan-400/30 hover:text-cyan-300"
            >
              TrendRider&apos;s performance dashboard
            </a>{" "}
            &mdash; transparent metrics including win rate, drawdown, SQN score, and trade-by-trade history.
          </p>

          {/* CTA Section */}
          <div className="mt-16 rounded-2xl border border-cyan-500/20 bg-gradient-to-br from-cyan-500/5 to-blue-500/5 p-8 text-center">
            <h3 className="mb-3 text-xl font-bold text-white">
              Trend Following That Actually Works
            </h3>
            <p className="mb-6 text-gray-400">
              documented backtest win rate (current value on /live), low max drawdown (see /live), and solid SQN (see /live) across thousands of simulated trades. Skip the market making complexity and start with a proven system.
            </p>
            <a
              href="https://trendrider.net/"
              className="inline-flex items-center gap-2 rounded-full bg-cyan-500 px-6 py-3 text-sm font-semibold text-black transition-all hover:bg-cyan-400 hover:shadow-lg hover:shadow-cyan-500/25"
            >
              View Live Performance &rarr;
            </a>
          </div>
        </article>
      </main>
    </>
  );
}
