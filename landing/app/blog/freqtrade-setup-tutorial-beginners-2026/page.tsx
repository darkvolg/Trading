import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Freqtrade Tutorial 2026: Complete Setup Guide [67.9% Win Rate Strategy]",
  description: "Step-by-step Freqtrade setup guide for beginners in 2026. Install via Docker, connect Bybit, build your first RSI+EMA strategy, backtest 10,000+ trades, and go live in under 1 hour.",
  alternates: {
    canonical: "https://trendrider.net/blog/freqtrade-setup-tutorial-beginners-2026",
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
            "headline": "Freqtrade Tutorial 2026: Complete Setup Guide for Beginners",
            "description": "Step-by-step Freqtrade setup guide for beginners. Install via Docker, connect Bybit, build your first strategy, backtest, and go live in under 1 hour.",
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
              "@id": "https://trendrider.net/blog/freqtrade-setup-tutorial-beginners-2026"
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
              { "@type": "ListItem", "position": 3, "name": "Freqtrade Tutorial 2026: Complete Setup Guide for Beginners" }
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
                "name": "Is Freqtrade free to use in 2026?",
                "acceptedAnswer": {
                  "@type": "Answer",
                  "text": "Yes, Freqtrade is 100% free and open-source (GPL-3.0 license). You can download, modify, and run it without any subscription fees. The only costs are your exchange trading fees (typically 0.1% per trade on Bybit) and server hosting if you want 24/7 uptime."
                }
              },
              {
                "@type": "Question",
                "name": "Can I run Freqtrade on Windows?",
                "acceptedAnswer": {
                  "@type": "Answer",
                  "text": "Yes, Freqtrade runs on Windows, macOS, and Linux. The easiest method on Windows is using Docker Desktop, which handles all dependencies automatically. You can also install it natively using WSL2 (Windows Subsystem for Linux) or directly via pip with Python 3.10+."
                }
              },
              {
                "@type": "Question",
                "name": "Which exchange works best with Freqtrade?",
                "acceptedAnswer": {
                  "@type": "Answer",
                  "text": "Bybit is the most popular exchange for Freqtrade in 2026 due to its low fees (0.1% maker/taker), excellent API reliability, deep liquidity, and support for both spot and futures trading. Binance, OKX, and Kraken are also supported but Bybit offers the best overall experience for algorithmic trading."
                }
              },
              {
                "@type": "Question",
                "name": "How much money do I need to start trading with Freqtrade?",
                "acceptedAnswer": {
                  "@type": "Answer",
                  "text": "You can start with as little as $100-200 for spot trading on Bybit. However, $500-1000 is recommended to allow proper position sizing and diversification across multiple trading pairs. Always start with dry-run (paper trading) mode first to validate your strategy before risking real capital."
                }
              },
              {
                "@type": "Question",
                "name": "Do I need programming experience to use Freqtrade?",
                "acceptedAnswer": {
                  "@type": "Answer",
                  "text": "Basic Python knowledge helps but is not strictly required. Freqtrade provides sample strategies you can modify, and the configuration is done through JSON files. For custom strategies, you'll need to understand Python basics like if/else statements and working with pandas DataFrames. Alternatively, you can use pre-built strategies like TrendRider which require zero coding."
                }
              }
            ]
          })
        }}
      />
    <div className="min-h-screen bg-background text-foreground">
      <article className="max-w-3xl mx-auto px-4 py-20">
        <a href="/blog" className="text-primary text-sm hover:underline mb-8 inline-block">&larr; Back to blog</a>
        <div className="flex items-center gap-3 mb-4">
          <span className="px-3 py-1 text-[10px] font-mono uppercase tracking-widest text-primary border border-primary/30 rounded-full">Tutorial</span>
          <span className="text-xs text-muted">April 2, 2026</span>
          <span className="text-xs text-muted">&bull; 12 min read</span>
        </div>
        <h1 className="text-3xl md:text-4xl font-bold mb-8 tracking-tight">Freqtrade Tutorial 2026: Complete Setup Guide for Beginners</h1>

        <div className="space-y-6 text-muted leading-relaxed">
          <p>Freqtrade is the most powerful free, open-source crypto trading bot available in 2026. It supports 150+ exchanges, advanced backtesting, custom strategy development in Python, and full Telegram integration &mdash; all without a monthly subscription fee. Whether you&apos;re a complete beginner or an experienced trader looking to automate, this guide will take you from zero to a running bot in under an hour.</p>
          <p>Unlike paid platforms like 3Commas ($49/month) or Cornix ($29/month), Freqtrade gives you complete control over your strategy logic, data, and execution &mdash; for free. The tradeoff? You need to set it up yourself. That&apos;s exactly what this tutorial covers, step by step.</p>

          <h2 className="text-xl font-semibold text-foreground mt-8 mb-3">What You&apos;ll Need (Prerequisites)</h2>
          <p>Before we start, make sure you have the following ready:</p>
          <ul className="list-disc pl-6 space-y-2">
            <li><strong className="text-foreground">A computer</strong> &mdash; Windows 10/11, macOS, or Linux. Any modern machine works. For 24/7 trading, you&apos;ll eventually want a VPS ($5&ndash;10/month) but your local machine is fine for learning.</li>
            <li><strong className="text-foreground">Docker Desktop</strong> &mdash; The easiest installation method. Download from <span className="text-primary">docker.com</span>. On Windows, make sure WSL2 is enabled.</li>
            <li><strong className="text-foreground">Python 3.10+</strong> &mdash; Only needed if you prefer pip installation over Docker. Check with <code className="text-xs bg-card px-2 py-0.5 rounded font-mono">python --version</code> in your terminal.</li>
            <li><strong className="text-foreground">A Bybit account</strong> &mdash; Create one at bybit.com. Complete KYC verification (takes 5&ndash;10 minutes). You&apos;ll need API keys later.</li>
            <li><strong className="text-foreground">A text editor</strong> &mdash; VS Code is recommended. You&apos;ll be editing JSON config files and Python strategy files.</li>
          </ul>

          <h2 className="text-xl font-semibold text-foreground mt-8 mb-3">Step 1: Installation (Docker vs. Pip)</h2>
          <p>There are two main ways to install Freqtrade. Docker is recommended for beginners because it handles all dependencies automatically and keeps your system clean.</p>

          <h3 className="text-lg font-medium text-foreground mt-6 mb-2">Option A: Docker Installation (Recommended)</h3>
          <p>Docker wraps Freqtrade and all its dependencies into a container. No Python version conflicts, no dependency hell. Just works.</p>
          <div className="bg-card/50 border border-border/50 rounded-xl p-4 font-mono text-sm space-y-1">
            <p className="text-muted"># Create a directory for your bot</p>
            <p className="text-foreground">mkdir ft_userdata</p>
            <p className="text-foreground">cd ft_userdata</p>
            <p className="text-muted"># Download the docker-compose file</p>
            <p className="text-foreground">curl https://raw.githubusercontent.com/freqtrade/freqtrade/stable/docker-compose.yml -o docker-compose.yml</p>
            <p className="text-muted"># Pull the latest image</p>
            <p className="text-foreground">docker compose pull</p>
            <p className="text-muted"># Create user_data directory structure</p>
            <p className="text-foreground">docker compose run --rm freqtrade create-userdir --userdir user_data</p>
            <p className="text-muted"># Generate a config file</p>
            <p className="text-foreground">docker compose run --rm freqtrade new-config --config user_data/config.json</p>
          </div>
          <p>During config generation, Freqtrade will ask you a series of questions: exchange name, trading mode (spot/futures), dry-run mode, and Telegram integration. For now, choose Bybit, spot trading, and enable dry-run mode.</p>

          <h3 className="text-lg font-medium text-foreground mt-6 mb-2">Option B: Pip Installation</h3>
          <p>If you prefer a native installation (useful for strategy development with IDE autocompletion):</p>
          <div className="bg-card/50 border border-border/50 rounded-xl p-4 font-mono text-sm space-y-1">
            <p className="text-muted"># Clone the repository</p>
            <p className="text-foreground">git clone https://github.com/freqtrade/freqtrade.git</p>
            <p className="text-foreground">cd freqtrade</p>
            <p className="text-muted"># Run the setup script</p>
            <p className="text-foreground">./setup.sh -i</p>
            <p className="text-muted"># Activate the virtual environment</p>
            <p className="text-foreground">source .venv/bin/activate</p>
            <p className="text-muted"># Verify installation</p>
            <p className="text-foreground">freqtrade --version</p>
          </div>
          <p>The setup script creates a Python virtual environment and installs all dependencies. On Windows, use <code className="text-xs bg-card px-2 py-0.5 rounded font-mono">.\setup.ps1</code> in PowerShell instead.</p>

          <h2 className="text-xl font-semibold text-foreground mt-8 mb-3">Step 2: Configuration (config.json)</h2>
          <p>The config file is the brain of your bot. It controls which exchange to use, how much capital to deploy, risk parameters, and more. Here are the most important settings you need to understand:</p>
          <div className="bg-card/50 border border-border/50 rounded-xl p-4 font-mono text-sm space-y-1">
            <p className="text-foreground">{'{'}</p>
            <p className="text-foreground pl-4">&quot;stake_currency&quot;: &quot;USDT&quot;,</p>
            <p className="text-foreground pl-4">&quot;stake_amount&quot;: &quot;unlimited&quot;,</p>
            <p className="text-foreground pl-4">&quot;tradable_balance_ratio&quot;: 0.99,</p>
            <p className="text-foreground pl-4">&quot;max_open_trades&quot;: 5,</p>
            <p className="text-foreground pl-4">&quot;dry_run&quot;: true,</p>
            <p className="text-foreground pl-4">&quot;dry_run_wallet&quot;: 1000,</p>
            <p className="text-foreground pl-4">&quot;exchange&quot;: {'{'}</p>
            <p className="text-foreground pl-8">&quot;name&quot;: &quot;bybit&quot;,</p>
            <p className="text-foreground pl-8">&quot;key&quot;: &quot;YOUR_API_KEY&quot;,</p>
            <p className="text-foreground pl-8">&quot;secret&quot;: &quot;YOUR_API_SECRET&quot;</p>
            <p className="text-foreground pl-4">{'}'}</p>
            <p className="text-foreground">{'}'}</p>
          </div>
          <p>Key parameters explained:</p>
          <ul className="list-disc pl-6 space-y-2">
            <li><strong className="text-foreground">stake_currency</strong> &mdash; The base currency for all trades. USDT is the most common choice on Bybit.</li>
            <li><strong className="text-foreground">stake_amount: &quot;unlimited&quot;</strong> &mdash; Freqtrade will automatically divide your balance equally among max_open_trades. With a $1,000 wallet and 5 max trades, each position gets ~$200.</li>
            <li><strong className="text-foreground">max_open_trades</strong> &mdash; How many positions can be open simultaneously. Start with 3&ndash;5 to diversify without over-trading.</li>
            <li><strong className="text-foreground">dry_run: true</strong> &mdash; Paper trading mode. The bot simulates trades without using real money. Always start here.</li>
            <li><strong className="text-foreground">dry_run_wallet</strong> &mdash; Virtual balance for paper trading. Set this to the amount you plan to actually trade with.</li>
          </ul>

          <h3 className="text-lg font-medium text-foreground mt-6 mb-2">Generating Bybit API Keys</h3>
          <p>To connect Freqtrade to Bybit:</p>
          <ol className="list-decimal pl-6 space-y-2">
            <li>Log into Bybit and go to <strong className="text-foreground">Account &amp; Security &rarr; API Management</strong></li>
            <li>Click <strong className="text-foreground">Create New Key</strong>, select &ldquo;System-generated API Keys&rdquo;</li>
            <li>Name it &ldquo;Freqtrade Bot&rdquo; and set permissions: <strong className="text-foreground">Read + Trade</strong> (never enable Withdraw)</li>
            <li>Whitelist your server&apos;s IP address for security</li>
            <li>Copy the API key and secret into your config.json</li>
          </ol>

          <h2 className="text-xl font-semibold text-foreground mt-8 mb-3">Step 3: Your First Strategy (RSI + EMA)</h2>
          <p>A trading strategy in Freqtrade is a Python file that defines when to buy and when to sell. Let&apos;s build a simple but effective strategy using RSI (Relative Strength Index) and EMA (Exponential Moving Average).</p>
          <p>The logic: buy when RSI is oversold (below 30) AND price is above the 200 EMA (confirming an uptrend). Sell when RSI is overbought (above 70) or when a 6% stop-loss is hit.</p>
          <div className="bg-card/50 border border-border/50 rounded-xl p-4 font-mono text-sm space-y-1">
            <p className="text-muted"># user_data/strategies/SimpleRsiEma.py</p>
            <p className="text-foreground">from freqtrade.strategy import IStrategy</p>
            <p className="text-foreground">import talib.abstract as ta</p>
            <p className="text-foreground">from pandas import DataFrame</p>
            <p>&nbsp;</p>
            <p className="text-foreground">class SimpleRsiEma(IStrategy):</p>
            <p className="text-foreground pl-4">timeframe = &apos;1h&apos;</p>
            <p className="text-foreground pl-4">stoploss = -0.06  # 6% stop-loss</p>
            <p className="text-foreground pl-4">minimal_roi = {'{'}&quot;0&quot;: 0.10, &quot;60&quot;: 0.05, &quot;120&quot;: 0.02{'}'}</p>
            <p>&nbsp;</p>
            <p className="text-foreground pl-4">def populate_indicators(self, df: DataFrame, metadata):</p>
            <p className="text-foreground pl-8">df[&apos;rsi&apos;] = ta.RSI(df, timeperiod=14)</p>
            <p className="text-foreground pl-8">df[&apos;ema200&apos;] = ta.EMA(df, timeperiod=200)</p>
            <p className="text-foreground pl-8">return df</p>
            <p>&nbsp;</p>
            <p className="text-foreground pl-4">def populate_entry_trend(self, df: DataFrame, metadata):</p>
            <p className="text-foreground pl-8">df.loc[</p>
            <p className="text-foreground pl-12">(df[&apos;rsi&apos;] &lt; 30) &amp;</p>
            <p className="text-foreground pl-12">(df[&apos;close&apos;] &gt; df[&apos;ema200&apos;]),</p>
            <p className="text-foreground pl-12">&apos;enter_long&apos;] = 1</p>
            <p className="text-foreground pl-8">return df</p>
            <p>&nbsp;</p>
            <p className="text-foreground pl-4">def populate_exit_trend(self, df: DataFrame, metadata):</p>
            <p className="text-foreground pl-8">df.loc[</p>
            <p className="text-foreground pl-12">(df[&apos;rsi&apos;] &gt; 70),</p>
            <p className="text-foreground pl-12">&apos;exit_long&apos;] = 1</p>
            <p className="text-foreground pl-8">return df</p>
          </div>
          <p>Save this file as <code className="text-xs bg-card px-2 py-0.5 rounded font-mono">user_data/strategies/SimpleRsiEma.py</code>. The strategy has three key methods:</p>
          <ul className="list-disc pl-6 space-y-2">
            <li><strong className="text-foreground">populate_indicators</strong> &mdash; Calculates RSI-14 and EMA-200 for each candle.</li>
            <li><strong className="text-foreground">populate_entry_trend</strong> &mdash; Marks a buy signal when RSI drops below 30 while price stays above the 200 EMA.</li>
            <li><strong className="text-foreground">populate_exit_trend</strong> &mdash; Marks a sell signal when RSI exceeds 70, capturing the overbought reversal.</li>
            <li><strong className="text-foreground">minimal_roi</strong> &mdash; Automatically takes profit: 10% immediately, 5% after 1 hour, 2% after 2 hours.</li>
          </ul>

          <h2 className="text-xl font-semibold text-foreground mt-8 mb-3">Step 4: Backtesting Your Strategy</h2>
          <p>Before risking any money, you need to test your strategy against historical data. This is called <a href="/blog/backtesting-crypto-strategies-guide" className="text-primary hover:underline">backtesting</a> and it&apos;s the most critical step in algorithmic trading.</p>

          <h3 className="text-lg font-medium text-foreground mt-6 mb-2">Download Historical Data</h3>
          <div className="bg-card/50 border border-border/50 rounded-xl p-4 font-mono text-sm space-y-1">
            <p className="text-muted"># Download 6 months of 1h candle data for top pairs</p>
            <p className="text-foreground">freqtrade download-data --exchange bybit \</p>
            <p className="text-foreground pl-4">--pairs BTC/USDT ETH/USDT SOL/USDT XRP/USDT \</p>
            <p className="text-foreground pl-4">--timeframes 1h \</p>
            <p className="text-foreground pl-4">--days 180</p>
          </div>

          <h3 className="text-lg font-medium text-foreground mt-6 mb-2">Run the Backtest</h3>
          <div className="bg-card/50 border border-border/50 rounded-xl p-4 font-mono text-sm space-y-1">
            <p className="text-foreground">freqtrade backtesting \</p>
            <p className="text-foreground pl-4">--strategy SimpleRsiEma \</p>
            <p className="text-foreground pl-4">--timerange 20251001-20260401 \</p>
            <p className="text-foreground pl-4">--config user_data/config.json</p>
          </div>
          <p>Freqtrade will replay every candle from October 2025 to April 2026 and simulate your strategy&apos;s trades. The output includes:</p>
          <ul className="list-disc pl-6 space-y-2">
            <li><strong className="text-foreground">Total trades</strong> &mdash; How many trades were executed. Aim for 200+ for statistical significance.</li>
            <li><strong className="text-foreground">Win rate</strong> &mdash; Percentage of profitable trades. Above 55% is good for trend-following strategies.</li>
            <li><strong className="text-foreground">Profit factor</strong> &mdash; Total wins divided by total losses. Above 1.5 indicates a strong edge.</li>
            <li><strong className="text-foreground">Max drawdown</strong> &mdash; The largest peak-to-trough decline. Keep this under 10% for conservative risk management.</li>
            <li><strong className="text-foreground">SQN score</strong> &mdash; System Quality Number. Above 2.0 is &ldquo;Good&rdquo;, above 3.0 is &ldquo;Excellent&rdquo;.</li>
          </ul>
          <p>If your backtest shows a win rate below 50% or a drawdown above 15%, go back and tweak your strategy parameters. Consider adjusting RSI thresholds, adding a volume filter, or changing the timeframe. Learn more about avoiding common backtesting mistakes in our <a href="/blog/backtesting-crypto-strategies-guide" className="text-primary hover:underline">backtesting guide</a>.</p>

          <h2 className="text-xl font-semibold text-foreground mt-8 mb-3">Step 5: Dry Run (Paper Trading)</h2>
          <p>Once your backtest results look promising, it&apos;s time to test in real-time market conditions &mdash; but still without real money. This is called dry-run or paper trading.</p>
          <div className="bg-card/50 border border-border/50 rounded-xl p-4 font-mono text-sm space-y-1">
            <p className="text-muted"># Make sure dry_run is true in config.json, then:</p>
            <p className="text-foreground">freqtrade trade \</p>
            <p className="text-foreground pl-4">--strategy SimpleRsiEma \</p>
            <p className="text-foreground pl-4">--config user_data/config.json</p>
          </div>
          <p>The bot will now monitor the live market and execute virtual trades in real-time. It connects to Bybit&apos;s API for price data but doesn&apos;t place any actual orders. Key things to watch during dry-run:</p>
          <ul className="list-disc pl-6 space-y-2">
            <li><strong className="text-foreground">Entry timing</strong> &mdash; Is the bot entering at the levels you expect? Compare signals to the chart.</li>
            <li><strong className="text-foreground">Exit behavior</strong> &mdash; Are stop-losses and take-profits triggering correctly?</li>
            <li><strong className="text-foreground">Trade frequency</strong> &mdash; Is it trading too much (over-trading) or too little (missing opportunities)?</li>
            <li><strong className="text-foreground">API stability</strong> &mdash; Watch for connection errors or rate limit warnings in the logs.</li>
          </ul>
          <p>Run dry-run for at least 1&ndash;2 weeks before going live. If results are consistent with your backtest (within 10&ndash;15% variance), you&apos;re ready for real capital.</p>

          <h3 className="text-lg font-medium text-foreground mt-6 mb-2">Adding Telegram Notifications</h3>
          <p>Freqtrade has built-in Telegram integration so you get notified of every trade. Add this to your config.json:</p>
          <div className="bg-card/50 border border-border/50 rounded-xl p-4 font-mono text-sm space-y-1">
            <p className="text-foreground">&quot;telegram&quot;: {'{'}</p>
            <p className="text-foreground pl-4">&quot;enabled&quot;: true,</p>
            <p className="text-foreground pl-4">&quot;token&quot;: &quot;YOUR_BOT_TOKEN&quot;,</p>
            <p className="text-foreground pl-4">&quot;chat_id&quot;: &quot;YOUR_CHAT_ID&quot;</p>
            <p className="text-foreground">{'}'}</p>
          </div>
          <p>Create a bot via <strong className="text-foreground">@BotFather</strong> on Telegram, copy the token, and get your chat_id from <strong className="text-foreground">@userinfobot</strong>. Now you&apos;ll see real-time entry/exit alerts, daily profit summaries, and can control the bot directly from Telegram with commands like <code className="text-xs bg-card px-2 py-0.5 rounded font-mono">/status</code>, <code className="text-xs bg-card px-2 py-0.5 rounded font-mono">/profit</code>, and <code className="text-xs bg-card px-2 py-0.5 rounded font-mono">/forcesell</code>.</p>

          <h2 className="text-xl font-semibold text-foreground mt-8 mb-3">Step 6: Going Live</h2>
          <p>The transition from dry-run to live trading is simple &mdash; but emotionally significant. Here&apos;s the checklist:</p>
          <ol className="list-decimal pl-6 space-y-2">
            <li><strong className="text-foreground">Set dry_run to false</strong> in config.json</li>
            <li><strong className="text-foreground">Fund your Bybit account</strong> with the amount you tested with (start small &mdash; $200&ndash;500)</li>
            <li><strong className="text-foreground">Verify API permissions</strong> &mdash; Read + Trade only, IP whitelisted, no withdrawal permission</li>
            <li><strong className="text-foreground">Set conservative max_open_trades</strong> &mdash; Start with 3 instead of 5</li>
            <li><strong className="text-foreground">Enable stoploss_on_exchange</strong> &mdash; Places stop-loss orders directly on Bybit for failsafe protection</li>
            <li><strong className="text-foreground">Monitor closely for 48 hours</strong> &mdash; Watch the first few trades manually before trusting automation</li>
          </ol>
          <div className="bg-card/50 border border-border/50 rounded-xl p-4 font-mono text-sm space-y-1">
            <p className="text-muted"># Add this to config.json for exchange-side stop-loss</p>
            <p className="text-foreground">&quot;order_types&quot;: {'{'}</p>
            <p className="text-foreground pl-4">&quot;entry&quot;: &quot;limit&quot;,</p>
            <p className="text-foreground pl-4">&quot;exit&quot;: &quot;limit&quot;,</p>
            <p className="text-foreground pl-4">&quot;stoploss&quot;: &quot;market&quot;,</p>
            <p className="text-foreground pl-4">&quot;stoploss_on_exchange&quot;: true</p>
            <p className="text-foreground">{'}'}</p>
          </div>
          <p>With <code className="text-xs bg-card px-2 py-0.5 rounded font-mono">stoploss_on_exchange: true</code>, your stop-loss is placed directly on Bybit&apos;s servers. Even if your bot crashes or loses internet, the stop-loss will execute. This is non-negotiable for live trading.</p>

          <h2 className="text-xl font-semibold text-foreground mt-8 mb-3">Step 7: Running 24/7 on a VPS</h2>
          <p>Your local machine isn&apos;t reliable for 24/7 trading &mdash; updates, restarts, and internet outages will interrupt your bot. A VPS (Virtual Private Server) solves this.</p>
          <ul className="list-disc pl-6 space-y-2">
            <li><strong className="text-foreground">Recommended providers</strong> &mdash; Hetzner ($4/month), DigitalOcean ($6/month), or Vultr ($6/month). Choose a server close to Bybit&apos;s servers (Singapore or Tokyo) for lower latency.</li>
            <li><strong className="text-foreground">Minimum specs</strong> &mdash; 1 vCPU, 2 GB RAM, 20 GB SSD. This handles Freqtrade + 10 pairs easily.</li>
            <li><strong className="text-foreground">Use Docker</strong> on the VPS for easy deployment. Just <code className="text-xs bg-card px-2 py-0.5 rounded font-mono">docker compose up -d</code> and it runs in the background.</li>
            <li><strong className="text-foreground">Set up automatic restarts</strong> &mdash; Add <code className="text-xs bg-card px-2 py-0.5 rounded font-mono">restart: unless-stopped</code> to your docker-compose.yml so the bot restarts after server reboots.</li>
          </ul>

          <h2 className="text-xl font-semibold text-foreground mt-8 mb-3">Beyond Basics: TrendRider Strategy</h2>
          <p>The RSI + EMA strategy above is a great starting point, but production-grade trading requires more sophistication. <a href="/blog/best-crypto-trading-strategies-2026" className="text-primary hover:underline">Advanced strategies</a> combine multiple indicators, multi-timeframe analysis, dynamic risk management, and market regime detection.</p>
          <p>That&apos;s exactly what <strong className="text-foreground">TrendRider</strong> does. Our strategy combines 8 technical indicators across 3 timeframes with adaptive position sizing. The results from 10,000+ backtested trades:</p>
          <ul className="list-disc pl-6 space-y-2">
            <li><strong className="text-foreground">67.9% win rate</strong> &mdash; Nearly 7 out of 10 trades are profitable</li>
            <li><strong className="text-foreground">1.42% max drawdown</strong> &mdash; Extremely conservative risk management</li>
            <li><strong className="text-foreground">SQN score 3.45</strong> &mdash; Rated &ldquo;Excellent&rdquo; by Van Tharp&apos;s framework</li>
            <li><strong className="text-foreground">5-minute setup</strong> &mdash; Just plug in your Bybit API keys and start</li>
          </ul>

          <div className="mt-8 p-6 rounded-xl border border-primary/30 bg-primary/5 text-center">
            <p className="text-foreground font-semibold text-lg mb-2">Skip the trial and error. Trade with a proven strategy.</p>
            <p className="text-muted mb-4">TrendRider is built on Freqtrade with 67.9% win rate and 10,000+ backtested trades. Free tier available &mdash; no credit card required.</p>
            <a href="/#pricing" className="inline-block px-6 py-3 bg-primary text-primary-foreground rounded-lg font-semibold hover:opacity-90 transition-opacity">Get Started Free &rarr;</a>
          </div>

          <h2 className="text-xl font-semibold text-foreground mt-8 mb-3">Frequently Asked Questions</h2>

          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-medium text-foreground mb-2">Is Freqtrade free to use in 2026?</h3>
              <p>Yes, Freqtrade is 100% free and open-source under the GPL-3.0 license. You pay nothing for the software itself. Your only costs are exchange trading fees (typically 0.1% per trade on Bybit) and optional VPS hosting ($4&ndash;10/month) for 24/7 uptime.</p>
            </div>

            <div>
              <h3 className="text-lg font-medium text-foreground mb-2">Can I run Freqtrade on Windows?</h3>
              <p>Absolutely. The easiest path is Docker Desktop on Windows 10/11 with WSL2 enabled. You can also install natively via pip using Python 3.10+ or run it inside WSL2 directly. All three methods work well &mdash; Docker is simplest for beginners.</p>
            </div>

            <div>
              <h3 className="text-lg font-medium text-foreground mb-2">Which exchange works best with Freqtrade?</h3>
              <p>Bybit is the top choice in 2026. It offers low fees (0.1% maker/taker), reliable API, deep liquidity, and supports both spot and futures trading. Binance, OKX, and Kraken are also well-supported. Check the <a href="https://www.freqtrade.io/en/stable/exchanges/" className="text-primary hover:underline" target="_blank" rel="noopener noreferrer">official exchange compatibility list</a> for the full roster.</p>
            </div>

            <div>
              <h3 className="text-lg font-medium text-foreground mb-2">How much money do I need to start?</h3>
              <p>You can begin spot trading with as little as $100&ndash;200 on Bybit. However, $500&ndash;1,000 is recommended so you can properly diversify across 3&ndash;5 trading pairs with meaningful position sizes. Always start in dry-run mode with virtual funds first.</p>
            </div>

            <div>
              <h3 className="text-lg font-medium text-foreground mb-2">Do I need programming experience?</h3>
              <p>Basic Python knowledge helps for writing custom strategies, but it&apos;s not required to get started. Freqtrade ships with sample strategies you can modify, and configuration is done through JSON files. For a zero-code option, pre-built strategies like <a href="/" className="text-primary hover:underline">TrendRider</a> work out of the box with just API key setup.</p>
            </div>
          </div>

        </div>

        <div className="mt-16 pt-10 border-t border-border/30">
          <h2 className="text-xl font-semibold text-foreground mb-6">Related Articles</h2>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <a href="/blog/best-crypto-trading-strategies-2026" className="p-4 rounded-xl border border-border/50 bg-card/30 hover:border-primary/30 hover:bg-card/50 transition-all">
              <span className="text-xs text-primary font-mono uppercase tracking-widest">Strategy</span>
              <p className="text-sm font-medium text-foreground mt-2">7 Best Crypto Trading Strategies for 2026 (Backtested)</p>
            </a>
            <a href="/blog/backtesting-crypto-strategies-guide" className="p-4 rounded-xl border border-border/50 bg-card/30 hover:border-primary/30 hover:bg-card/50 transition-all">
              <span className="text-xs text-primary font-mono uppercase tracking-widest">Education</span>
              <p className="text-sm font-medium text-foreground mt-2">How to Backtest Crypto Strategies Without Overfitting</p>
            </a>
            <a href="/blog/how-to-automate-crypto-trading-freqtrade-2026" className="p-4 rounded-xl border border-border/50 bg-card/30 hover:border-primary/30 hover:bg-card/50 transition-all">
              <span className="text-xs text-primary font-mono uppercase tracking-widest">Tutorial</span>
              <p className="text-sm font-medium text-foreground mt-2">How to Automate Crypto Trading with Freqtrade in 2026</p>
            </a>
          </div>
        </div>
      </article>
    </div>
    </>
  );
}
