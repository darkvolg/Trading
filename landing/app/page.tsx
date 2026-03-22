"use client";

import { useEffect, useRef, useState, type ReactNode } from "react";

/* ──────────────────────────── constants ──────────────────────────── */

const TELEGRAM_URL = "https://t.me/TrendRiderSignals";
const SHEETS_URL =
  "https://docs.google.com/spreadsheets/d/1ZWRJ0PcBSk910MZv426PrleriBnInykr3OebWXJPm-g";

const METRICS = [
  { label: "Win Rate", value: 71.1, suffix: "%", decimals: 1 },
  { label: "Max Drawdown", value: 1.81, suffix: "%", decimals: 2 },
  { label: "Profit Factor", value: 2.09, suffix: "x", decimals: 2 },
  { label: "SQN Score", value: 3.02, suffix: "", decimals: 2 },
];

const STEPS = [
  {
    num: "01",
    icon: (
      <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M6 12 3.269 3.125A59.769 59.769 0 0 1 21.485 12 59.768 59.768 0 0 1 3.27 20.875L5.999 12Zm0 0h7.5" />
      </svg>
    ),
    title: "Subscribe to Telegram",
    desc: "Join our channel and start receiving algorithmic signals in real-time.",
  },
  {
    num: "02",
    icon: (
      <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.325.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 0 1 1.37.49l1.296 2.247a1.125 1.125 0 0 1-.26 1.431l-1.003.827c-.293.241-.438.613-.43.992a7.723 7.723 0 0 1 0 .255c-.008.378.137.75.43.991l1.004.827c.424.35.534.955.26 1.43l-1.298 2.247a1.125 1.125 0 0 1-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.47 6.47 0 0 1-.22.128c-.331.183-.581.495-.644.869l-.213 1.281c-.09.543-.56.94-1.11.94h-2.594c-.55 0-1.019-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 0 1-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 0 1-1.369-.49l-1.297-2.247a1.125 1.125 0 0 1 .26-1.431l1.004-.827c.292-.24.437-.613.43-.991a6.932 6.932 0 0 1 0-.255c.007-.38-.138-.751-.43-.992l-1.004-.827a1.125 1.125 0 0 1-.26-1.43l1.297-2.247a1.125 1.125 0 0 1 1.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.086.22-.128.332-.183.582-.495.644-.869l.214-1.28Z" />
        <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" />
      </svg>
    ),
    title: "Auto-Trade via Cornix",
    desc: "Connect Cornix bot for hands-free execution on Bybit, Binance, or OKX.",
  },
  {
    num: "03",
    icon: (
      <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 0 1 3 19.875v-6.75ZM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V8.625ZM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V4.125Z" />
      </svg>
    ),
    title: "Track in Google Sheets",
    desc: "Every trade is logged publicly. Full transparency, verifiable results.",
  },
];

const FEATURES = [
  {
    icon: "\uD83C\uDFAF",
    title: "Confidence Scoring",
    desc: "Every signal rated 1-10 based on multi-factor analysis. Only high-confidence trades.",
  },
  {
    icon: "\uD83D\uDCCA",
    title: "On-Chain Data",
    desc: "Fear & Greed Index, funding rates, open interest integrated into every decision.",
  },
  {
    icon: "\uD83E\uDD16",
    title: "Cornix Auto-Trade",
    desc: "One-click setup. Signals execute automatically on your exchange account.",
  },
  {
    icon: "\uD83D\uDCC8",
    title: "Verified Track Record",
    desc: "Public Google Sheet with every trade. No cherry-picking, no hidden losses.",
  },
  {
    icon: "\uD83D\uDEE1\uFE0F",
    title: "Ultra-Low Drawdown",
    desc: "1.81% max drawdown. Conservative risk management with 6% stop-loss per trade.",
  },
  {
    icon: "\uD83D\uDCF1",
    title: "Real-Time Alerts",
    desc: "Instant Telegram notifications. Never miss an entry or exit signal.",
  },
];

const PRICING = [
  {
    name: "Free",
    price: "$0",
    period: "forever",
    features: [
      "Delayed signals (3h)",
      "Monthly performance report",
      "Public results access",
      "Community chat",
    ],
    cta: "Join Free",
    href: TELEGRAM_URL,
    highlight: false,
  },
  {
    name: "Basic",
    price: "$39",
    period: "/month",
    features: [
      "Real-time signals",
      "Cornix auto-trade ready",
      "Weekly performance recap",
      "4 pairs: BTC/ETH/SOL/BNB",
    ],
    cta: "Subscribe",
    href: TELEGRAM_URL,
    highlight: false,
  },
  {
    name: "VIP",
    price: "$99",
    period: "/month",
    features: [
      "Everything in Basic",
      "Post-trade review & analysis",
      "Daily market brief",
      "Priority support",
      "Early access to new features",
    ],
    cta: "Go VIP",
    href: TELEGRAM_URL,
    highlight: true,
  },
];

const FAQ_ITEMS = [
  {
    q: "What is TrendRider?",
    a: "TrendRider is an AI-powered algorithmic trading system built on Freqtrade. It analyzes BTC, ETH, SOL, and BNB across multiple timeframes using 15+ technical indicators combined with on-chain data to generate high-confidence trade signals.",
  },
  {
    q: "How are signals generated?",
    a: "Our algorithm combines 15+ technical indicators (RSI, MACD, Bollinger Bands, EMA crossovers, etc.), multi-timeframe analysis (5m, 15m, 1h, 4h), and on-chain metrics (Fear & Greed Index, funding rates, open interest) to identify high-probability setups.",
  },
  {
    q: "What's the track record?",
    a: "All trades are logged in a public Google Sheet with full transparency. Our backtested results show a 71.1% win rate, 2.09 profit factor, and just 1.81% max drawdown. We also maintain a Strat Ninja verified profile.",
  },
  {
    q: "How do I auto-trade?",
    a: "Connect the Cornix bot to our Telegram channel and link it to your exchange (Bybit, Binance, or OKX). Cornix will automatically execute trades based on our signals with your configured position sizing.",
  },
  {
    q: "Is it safe?",
    a: "We use strict risk management: 6% stop-loss per trade, never risking more than 2% of portfolio per position. The system has been paper-trading since March 2026 with verified results. However, all trading involves risk and past performance does not guarantee future results.",
  },
];

/* ──────────────────────────── hooks ──────────────────────────── */

function useInView(threshold = 0.2) {
  const ref = useRef<HTMLDivElement>(null);
  const [visible, setVisible] = useState(false);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const obs = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setVisible(true);
          obs.disconnect();
        }
      },
      { threshold }
    );
    obs.observe(el);
    return () => obs.disconnect();
  }, [threshold]);
  return { ref, visible };
}

function useCounter(target: number, decimals: number, active: boolean) {
  const [value, setValue] = useState(0);
  useEffect(() => {
    if (!active) return;
    const duration = 1800;
    const steps = 60;
    const increment = target / steps;
    let current = 0;
    let step = 0;
    const timer = setInterval(() => {
      step++;
      current += increment;
      if (step >= steps) {
        setValue(target);
        clearInterval(timer);
      } else {
        setValue(parseFloat(current.toFixed(decimals)));
      }
    }, duration / steps);
    return () => clearInterval(timer);
  }, [target, decimals, active]);
  return value;
}

/* ──────────────────────────── small components ──────────────────────────── */

function MetricCard({
  label,
  value,
  suffix,
  decimals,
  active,
}: {
  label: string;
  value: number;
  suffix: string;
  decimals: number;
  active: boolean;
}) {
  const count = useCounter(value, decimals, active);
  return (
    <div className="text-center p-6 rounded-xl bg-card/50 border border-border/50 backdrop-blur-sm">
      <div className="font-mono text-4xl md:text-5xl font-bold text-primary mb-2">
        {count.toFixed(decimals)}
        <span className="text-2xl md:text-3xl text-muted ml-1">{suffix}</span>
      </div>
      <div className="text-sm text-muted uppercase tracking-wider">{label}</div>
    </div>
  );
}

function FAQItem({ q, a }: { q: string; a: string }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="border border-border/50 rounded-xl overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between p-5 text-left hover:bg-card/30 transition-colors"
      >
        <span className="font-medium text-foreground pr-4">{q}</span>
        <svg
          className={`w-5 h-5 text-muted shrink-0 transition-transform duration-300 ${
            open ? "rotate-180" : ""
          }`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="m19 9-7 7-7-7" />
        </svg>
      </button>
      <div
        className={`overflow-hidden transition-all duration-300 ${
          open ? "max-h-96 opacity-100" : "max-h-0 opacity-0"
        }`}
      >
        <p className="px-5 pb-5 text-muted leading-relaxed">{a}</p>
      </div>
    </div>
  );
}

function SectionHeading({
  tag,
  title,
  subtitle,
}: {
  tag: string;
  title: string;
  subtitle?: string;
}) {
  return (
    <div className="text-center mb-16">
      <span className="inline-block px-4 py-1.5 text-xs font-mono uppercase tracking-widest text-primary border border-primary/30 rounded-full mb-4">
        {tag}
      </span>
      <h2 className="text-3xl md:text-4xl font-bold mb-4">{title}</h2>
      {subtitle && (
        <p className="text-muted max-w-2xl mx-auto text-lg">{subtitle}</p>
      )}
    </div>
  );
}

/* ──────────────────────────── main page ──────────────────────────── */

export default function Home() {
  const metrics = useInView(0.3);

  return (
    <div className="grid-bg">
      {/* ─── HERO ─── */}
      <section className="relative min-h-screen flex items-center justify-center px-4 overflow-hidden">
        {/* Glow orbs */}
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-primary/5 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-accent/5 rounded-full blur-3xl pointer-events-none" />

        <div className="relative text-center max-w-4xl mx-auto animate-fade-in-up">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-primary/30 bg-primary/5 mb-8">
            <span className="w-2 h-2 rounded-full bg-primary animate-pulse" />
            <span className="text-sm font-mono text-primary">Live since March 2026</span>
          </div>

          <h1 className="text-6xl md:text-8xl font-bold tracking-tight mb-4">
            <span className="gradient-text">TrendRider</span>
          </h1>

          <p className="text-xl md:text-2xl text-muted font-light mb-4">
            Algorithmic Signals. Verified Results.
          </p>

          <p className="text-muted max-w-xl mx-auto mb-10 leading-relaxed">
            AI-powered crypto trading signals with a{" "}
            <span className="text-primary font-semibold">71% win rate</span> and{" "}
            <span className="text-primary font-semibold">1.81% max drawdown</span>.
            Multi-timeframe analysis across BTC, ETH, SOL, and BNB.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <a
              href={TELEGRAM_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="group flex items-center gap-3 px-8 py-4 bg-primary text-background font-semibold rounded-xl hover:brightness-110 transition-all animate-pulse-glow"
            >
              <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
                <path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z" />
              </svg>
              Join Telegram Channel
              <svg className="w-4 h-4 transition-transform group-hover:translate-x-1" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5 21 12m0 0-7.5 7.5M21 12H3" />
              </svg>
            </a>
            <a
              href={SHEETS_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-3 px-8 py-4 border border-border text-foreground font-medium rounded-xl hover:bg-card/50 hover:border-primary/30 transition-all"
            >
              <svg className="w-5 h-5 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 0 1 3 19.875v-6.75ZM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V8.625ZM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V4.125Z" />
              </svg>
              View Live Results
            </a>
          </div>
        </div>

        {/* Scroll hint */}
        <div className="absolute bottom-8 left-1/2 -translate-x-1/2 animate-bounce">
          <svg className="w-6 h-6 text-muted" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="m19 9-7 7-7-7" />
          </svg>
        </div>
      </section>

      {/* ─── METRICS ─── */}
      <section ref={metrics.ref} className="py-24 px-4">
        <div className="max-w-5xl mx-auto">
          <SectionHeading
            tag="Performance"
            title="Numbers Don't Lie"
            subtitle="Backtested on real market data. Every metric verified and publicly available."
          />
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 md:gap-6">
            {METRICS.map((m) => (
              <MetricCard key={m.label} {...m} active={metrics.visible} />
            ))}
          </div>
          <p className="text-center text-muted text-sm mt-8">
            Based on backtests with real market data &bull; Updated monthly &bull;{" "}
            <a
              href={SHEETS_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="text-primary hover:underline"
            >
              View full results
            </a>
          </p>
        </div>
      </section>

      {/* ─── HOW IT WORKS ─── */}
      <section className="py-24 px-4 bg-card/30">
        <div className="max-w-5xl mx-auto">
          <SectionHeading
            tag="Process"
            title="How It Works"
            subtitle="Three simple steps to start receiving algorithmic trading signals."
          />
          <div className="grid md:grid-cols-3 gap-8">
            {STEPS.map((step) => (
              <div
                key={step.num}
                className="relative p-8 rounded-2xl border border-border/50 bg-background/50 backdrop-blur-sm hover:border-primary/30 transition-all group"
              >
                <span className="absolute top-4 right-4 font-mono text-6xl font-bold text-primary/10 group-hover:text-primary/20 transition-colors">
                  {step.num}
                </span>
                <div className="w-14 h-14 flex items-center justify-center rounded-xl bg-primary/10 text-primary mb-6">
                  {step.icon}
                </div>
                <h3 className="text-xl font-semibold mb-3">{step.title}</h3>
                <p className="text-muted leading-relaxed">{step.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── SIGNAL PREVIEW ─── */}
      <section className="py-24 px-4">
        <div className="max-w-5xl mx-auto">
          <SectionHeading
            tag="Preview"
            title="What You'll Receive"
            subtitle="Every signal comes with entry zones, targets, stop-loss, and confidence rating."
          />
          <div className="max-w-lg mx-auto">
            <div className="signal-card rounded-2xl p-6 md:p-8 font-mono text-sm md:text-base leading-relaxed animate-pulse-glow">
              <div className="flex items-center justify-between mb-4">
                <span className="text-muted text-xs uppercase tracking-wider">Signal Preview</span>
                <span className="px-2 py-0.5 bg-primary/10 text-primary rounded text-xs font-semibold">LIVE</span>
              </div>

              <div className="space-y-1">
                <p>
                  <span className="text-muted">{"\uD83D\uDCCA"}</span>{" "}
                  <span className="text-foreground font-semibold">TrendRider Signal #042</span>
                </p>
                <p>
                  <span className="text-primary font-bold">{"\uD83D\uDFE2"} LONG BTC/USDT</span>
                </p>
              </div>

              <div className="my-4 h-px bg-border/50" />

              <div className="space-y-1.5">
                <p>
                  <span className="text-muted">Entry Zone:</span>{" "}
                  <span className="text-foreground">$64,200 — $64,580</span>
                </p>
                <p>
                  <span className="text-muted">Stop Loss:</span>{" "}
                  <span className="text-danger">$60,350 (-6.0%)</span>
                </p>
                <p>
                  <span className="text-muted">TP1:</span>{" "}
                  <span className="text-primary">$66,126 (+3.0%)</span>{" "}
                  <span className="text-muted">— close 30%</span>
                </p>
                <p>
                  <span className="text-muted">TP2:</span>{" "}
                  <span className="text-primary">$67,410 (+5.0%)</span>{" "}
                  <span className="text-muted">— close 40%</span>
                </p>
                <p>
                  <span className="text-muted">TP3:</span>{" "}
                  <span className="text-primary">$70,620 (+10.0%)</span>{" "}
                  <span className="text-muted">— close 30%</span>
                </p>
              </div>

              <div className="my-4 h-px bg-border/50" />

              <div className="space-y-1.5">
                <p>
                  <span className="text-muted">Confidence:</span>{" "}
                  <span className="text-primary">{"\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588"}</span>
                  <span className="text-border">{"\u2591\u2591"}</span>{" "}
                  <span className="text-accent font-bold">8/10</span>
                </p>
                <p>
                  <span className="text-muted">Setup:</span>{" "}
                  <span className="text-foreground">Trend Pullback</span>
                </p>
                <p>
                  <span className="text-muted">Regime:</span>{" "}
                  <span className="text-primary">Trending Bull {"\uD83D\uDCC8"}</span>
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ─── FEATURES ─── */}
      <section className="py-24 px-4 bg-card/30">
        <div className="max-w-5xl mx-auto">
          <SectionHeading
            tag="Features"
            title="Built for Serious Traders"
            subtitle="Every detail engineered for consistent, risk-managed performance."
          />
          <div className="grid md:grid-cols-3 gap-6">
            {FEATURES.map((f) => (
              <div
                key={f.title}
                className="p-6 rounded-xl border border-border/50 bg-background/50 hover:border-primary/30 transition-all"
              >
                <div className="text-3xl mb-4">{f.icon}</div>
                <h3 className="text-lg font-semibold mb-2">{f.title}</h3>
                <p className="text-muted text-sm leading-relaxed">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── PRICING ─── */}
      <section className="py-24 px-4">
        <div className="max-w-5xl mx-auto">
          <SectionHeading
            tag="Pricing"
            title="Choose Your Plan"
            subtitle="Start free. Upgrade when you're ready."
          />
          <div className="grid md:grid-cols-3 gap-6 max-w-4xl mx-auto">
            {PRICING.map((plan) => (
              <div
                key={plan.name}
                className={`relative p-8 rounded-2xl border transition-all ${
                  plan.highlight
                    ? "border-accent/50 bg-accent/5 ring-1 ring-accent/20"
                    : "border-border/50 bg-card/30"
                }`}
              >
                {plan.highlight && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                    <span className="px-4 py-1 bg-accent text-background text-xs font-bold rounded-full uppercase tracking-wider">
                      Most Popular
                    </span>
                  </div>
                )}
                <div className="mb-6">
                  <h3
                    className={`text-lg font-semibold mb-2 ${
                      plan.highlight ? "gold-gradient-text" : ""
                    }`}
                  >
                    {plan.name}
                  </h3>
                  <div className="flex items-baseline gap-1">
                    <span className="font-mono text-4xl font-bold">{plan.price}</span>
                    <span className="text-muted text-sm">{plan.period}</span>
                  </div>
                </div>
                <ul className="space-y-3 mb-8">
                  {plan.features.map((feat) => (
                    <li key={feat} className="flex items-start gap-3 text-sm">
                      <svg
                        className={`w-5 h-5 shrink-0 mt-0.5 ${
                          plan.highlight ? "text-accent" : "text-primary"
                        }`}
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                        strokeWidth={2}
                      >
                        <path strokeLinecap="round" strokeLinejoin="round" d="m4.5 12.75 6 6 9-13.5" />
                      </svg>
                      <span className="text-muted">{feat}</span>
                    </li>
                  ))}
                </ul>
                <a
                  href={plan.href}
                  target="_blank"
                  rel="noopener noreferrer"
                  className={`block w-full text-center py-3 rounded-xl font-semibold transition-all ${
                    plan.highlight
                      ? "bg-accent text-background hover:brightness-110"
                      : "border border-border text-foreground hover:bg-card/50 hover:border-primary/30"
                  }`}
                >
                  {plan.cta}
                </a>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── FAQ ─── */}
      <section className="py-24 px-4 bg-card/30">
        <div className="max-w-3xl mx-auto">
          <SectionHeading
            tag="FAQ"
            title="Frequently Asked Questions"
          />
          <div className="space-y-3">
            {FAQ_ITEMS.map((item) => (
              <FAQItem key={item.q} {...item} />
            ))}
          </div>
        </div>
      </section>

      {/* ─── CTA BANNER ─── */}
      <section className="py-24 px-4">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-3xl md:text-4xl font-bold mb-4">
            Ready to Trade{" "}
            <span className="gradient-text">Smarter</span>?
          </h2>
          <p className="text-muted mb-8 text-lg">
            Join hundreds of traders receiving algorithmic signals daily.
          </p>
          <a
            href={TELEGRAM_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-3 px-10 py-4 bg-primary text-background font-semibold rounded-xl hover:brightness-110 transition-all text-lg"
          >
            <svg className="w-6 h-6" viewBox="0 0 24 24" fill="currentColor">
              <path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z" />
            </svg>
            Get Started on Telegram
          </a>
        </div>
      </section>

      {/* ─── FOOTER ─── */}
      <footer className="border-t border-border/50 py-12 px-4">
        <div className="max-w-5xl mx-auto">
          <div className="flex flex-col md:flex-row items-center justify-between gap-6 mb-8">
            <div>
              <span className="text-xl font-bold gradient-text">TrendRider</span>
              <p className="text-muted text-sm mt-1">Algorithmic Signals. Verified Results.</p>
            </div>
            <div className="flex items-center gap-6">
              <a
                href={TELEGRAM_URL}
                target="_blank"
                rel="noopener noreferrer"
                className="text-muted hover:text-primary transition-colors text-sm"
              >
                Telegram Channel
              </a>
              <a
                href={SHEETS_URL}
                target="_blank"
                rel="noopener noreferrer"
                className="text-muted hover:text-primary transition-colors text-sm"
              >
                Live Results
              </a>
            </div>
          </div>

          <div className="flex flex-col md:flex-row items-center justify-between gap-4 pt-8 border-t border-border/30">
            <p className="text-muted text-xs leading-relaxed max-w-2xl text-center md:text-left">
              <span className="font-semibold text-danger/80">Risk Disclaimer:</span> Trading
              cryptocurrencies involves substantial risk of loss and is not suitable for every
              investor. Past performance is not indicative of future results. Never invest more than
              you can afford to lose. This is not financial advice.
            </p>
            <div className="flex items-center gap-4 shrink-0">
              <span className="text-muted/50 text-xs font-mono">
                Powered by Freqtrade
              </span>
              <span className="text-muted/30">|</span>
              <span className="text-muted/50 text-xs">
                &copy; 2026 TrendRider
              </span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
