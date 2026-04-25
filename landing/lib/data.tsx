import type { ReactNode } from "react";
import type { TStrings } from "./i18n";
import { TELEGRAM_URL, TELEGRAM_BOT_URL } from "./constants";

/* ──────────────────────────── dynamic data builders ──────────────────────────── */

// Numbers are illustrative; verified backtest + live stats are published on /live.
export const getMetrics = (t: TStrings) => [
  { label: t.winRate, value: 53, suffix: "%", decimals: 1, barWidth: 53 },
  { label: t.maxDrawdown, value: 4.5, suffix: "%", decimals: 2, barWidth: 45 },
  { label: t.profitFactor, value: 1.6, suffix: "x", decimals: 2, barWidth: 53 },
  { label: t.sqnScore, value: 2.1, suffix: "", decimals: 2, barWidth: 52 },
];

export const getStepIcons = () => [
  <svg key="s1" className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M6 12 3.269 3.125A59.769 59.769 0 0 1 21.485 12 59.768 59.768 0 0 1 3.27 20.875L5.999 12Zm0 0h7.5" />
  </svg>,
  <svg key="s2" className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.325.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 0 1 1.37.49l1.296 2.247a1.125 1.125 0 0 1-.26 1.431l-1.003.827c-.293.241-.438.613-.43.992a7.723 7.723 0 0 1 0 .255c-.008.378.137.75.43.991l1.004.827c.424.35.534.955.26 1.43l-1.298 2.247a1.125 1.125 0 0 1-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.47 6.47 0 0 1-.22.128c-.331.183-.581.495-.644.869l-.213 1.281c-.09.543-.56.94-1.11.94h-2.594c-.55 0-1.019-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 0 1-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 0 1-1.369-.49l-1.297-2.247a1.125 1.125 0 0 1 .26-1.431l1.004-.827c.292-.24.437-.613.43-.991a6.932 6.932 0 0 1 0-.255c.007-.38-.138-.751-.43-.992l-1.004-.827a1.125 1.125 0 0 1-.26-1.43l1.297-2.247a1.125 1.125 0 0 1 1.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.086.22-.128.332-.183.582-.495.644-.869l.214-1.28Z" />
    <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" />
  </svg>,
  <svg key="s3" className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 0 1 3 19.875v-6.75ZM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V8.625ZM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V4.125Z" />
  </svg>,
];

export const getSteps = (t: TStrings) => {
  const icons = getStepIcons();
  return [
    { num: "01", icon: icons[0], title: t.step1Title, desc: t.step1Desc },
    { num: "02", icon: icons[1], title: t.step2Title, desc: t.step2Desc },
    { num: "03", icon: icons[2], title: t.step3Title, desc: t.step3Desc },
  ];
};

export const featureIcons: ReactNode[] = [
  // Confidence Scoring — target/crosshair icon, unique blue-cyan tint
  <div key="f1" className="w-14 h-14 flex items-center justify-center rounded-2xl bg-gradient-to-br from-cyan-500/15 to-primary/10 text-cyan-400 mb-4 group-hover:from-cyan-500/25 group-hover:to-primary/15 group-hover:scale-110 transition-all duration-300">
    <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 12m-9 0a9 9 0 1 0 18 0 9 9 0 1 0-18 0" />
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 12m-5 0a5 5 0 1 0 10 0 5 5 0 1 0-10 0" />
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 12m-1 0a1 1 0 1 0 2 0 1 1 0 1 0-2 0" />
    </svg>
  </div>,
  // On-Chain Data — bar chart icon, purple tint
  <div key="f2" className="w-14 h-14 flex items-center justify-center rounded-2xl bg-gradient-to-br from-violet-500/15 to-purple-500/10 text-violet-400 mb-4 group-hover:from-violet-500/25 group-hover:to-purple-500/15 group-hover:scale-110 transition-all duration-300">
    <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 0 1 3 19.875v-6.75ZM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V8.625ZM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V4.125Z" />
    </svg>
  </div>,
  // Cornix Auto-Trade — gear icon, amber/orange tint
  <div key="f3" className="w-14 h-14 flex items-center justify-center rounded-2xl bg-gradient-to-br from-amber-500/15 to-orange-500/10 text-amber-400 mb-4 group-hover:from-amber-500/25 group-hover:to-orange-500/15 group-hover:scale-110 transition-all duration-300">
    <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.325.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 0 1 1.37.49l1.296 2.247a1.125 1.125 0 0 1-.26 1.431l-1.003.827c-.293.241-.438.613-.43.992a7.723 7.723 0 0 1 0 .255c-.008.378.137.75.43.991l1.004.827c.424.35.534.955.26 1.43l-1.298 2.247a1.125 1.125 0 0 1-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.47 6.47 0 0 1-.22.128c-.331.183-.581.495-.644.869l-.213 1.281c-.09.543-.56.94-1.11.94h-2.594c-.55 0-1.019-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 0 1-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 0 1-1.369-.49l-1.297-2.247a1.125 1.125 0 0 1 .26-1.431l1.004-.827c.292-.24.437-.613.43-.991a6.932 6.932 0 0 1 0-.255c.007-.38-.138-.751-.43-.992l-1.004-.827a1.125 1.125 0 0 1-.26-1.43l1.297-2.247a1.125 1.125 0 0 1 1.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.086.22-.128.332-.183.582-.495.644-.869l.214-1.28Z" />
      <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" />
    </svg>
  </div>,
  // Verified Track Record — trending up, green tint
  <div key="f4" className="w-14 h-14 flex items-center justify-center rounded-2xl bg-gradient-to-br from-emerald-500/15 to-green-500/10 text-emerald-400 mb-4 group-hover:from-emerald-500/25 group-hover:to-green-500/15 group-hover:scale-110 transition-all duration-300">
    <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 18 9 11.25l4.306 4.306a11.95 11.95 0 0 1 5.814-5.518l2.74-1.22m0 0-5.94-2.281m5.94 2.28-2.28 5.941" />
    </svg>
  </div>,
  // Ultra-Low Drawdown — shield, blue tint
  <div key="f5" className="w-14 h-14 flex items-center justify-center rounded-2xl bg-gradient-to-br from-blue-500/15 to-indigo-500/10 text-blue-400 mb-4 group-hover:from-blue-500/25 group-hover:to-indigo-500/15 group-hover:scale-110 transition-all duration-300">
    <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75m-3-7.036A11.959 11.959 0 0 1 3.598 6 11.99 11.99 0 0 0 3 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285Z" />
    </svg>
  </div>,
  // Real-Time Alerts — bell, rose/red tint
  <div key="f6" className="w-14 h-14 flex items-center justify-center rounded-2xl bg-gradient-to-br from-rose-500/15 to-red-500/10 text-rose-400 mb-4 group-hover:from-rose-500/25 group-hover:to-red-500/15 group-hover:scale-110 transition-all duration-300">
    <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M14.857 17.082a23.848 23.848 0 0 0 5.454-1.31A8.967 8.967 0 0 1 18 9.75V9A6 6 0 0 0 6 9v.75a8.967 8.967 0 0 1-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 0 1-5.714 0m5.714 0a3 3 0 1 1-5.714 0" />
    </svg>
  </div>,
];

export const getFeatures = (t: TStrings): { icon: ReactNode; title: string; desc: string }[] => [
  { icon: featureIcons[0], title: t.feat1Title, desc: t.feat1Desc },
  { icon: featureIcons[1], title: t.feat2Title, desc: t.feat2Desc },
  { icon: featureIcons[2], title: t.feat3Title, desc: t.feat3Desc },
  { icon: featureIcons[3], title: t.feat4Title, desc: t.feat4Desc },
  { icon: featureIcons[4], title: t.feat5Title, desc: t.feat5Desc },
  { icon: featureIcons[5], title: t.feat6Title, desc: t.feat6Desc },
];

export const getPricing = (t: TStrings, _locale?: string) => [
  {
    name: t.free,
    price: "$0",
    period: t.forever,
    features: [t.freeF1, t.freeF2, t.freeF3, t.freeF4],
    cta: t.joinFree,
    href: TELEGRAM_URL,
    cryptoHref: "",
    highlight: false,
  },
  {
    name: "Basic",
    price: "$39",
    period: t.perMonth,
    features: [t.basicF1, t.basicF2, t.basicF3, t.basicF4],
    cta: t.subscribe,
    href: TELEGRAM_BOT_URL + "?start=pay_basic",
    cryptoHref: "",
    highlight: true,
  },
  {
    name: "VIP",
    price: "$99",
    period: t.perMonth,
    features: [t.vipF1, t.vipF2, t.vipF3, t.vipF4, t.vipF5],
    cta: t.getVip,
    href: TELEGRAM_BOT_URL + "?start=pay_vip",
    cryptoHref: "",
    highlight: false,
  },
];

export const getFaqItems = (t: TStrings) => [
  { q: t.faq1Q, a: t.faq1A },
  { q: t.faq2Q, a: t.faq2A },
  { q: t.faq3Q, a: t.faq3A },
  { q: t.faq4Q, a: t.faq4A },
  { q: t.faq5Q, a: t.faq5A },
];

/* ─── Live Ticker Trades ─── */
export const TICKER_TRADES = [
  { pair: "BTC/USDT", dir: "LONG", pnl: "+3.2%", time: "2m ago" },
  { pair: "ETH/USDT", dir: "LONG", pnl: "+5.1%", time: "14m ago" },
  { pair: "SOL/USDT", dir: "LONG", pnl: "+7.4%", time: "31m ago" },
  { pair: "BNB/USDT", dir: "LONG", pnl: "+2.9%", time: "1h ago" },
  { pair: "BTC/USDT", dir: "LONG", pnl: "+4.6%", time: "2h ago" },
  { pair: "ETH/USDT", dir: "LONG", pnl: "+3.8%", time: "3h ago" },
  { pair: "SOL/USDT", dir: "LONG", pnl: "+9.2%", time: "4h ago" },
  { pair: "BNB/USDT", dir: "LONG", pnl: "+2.1%", time: "5h ago" },
  { pair: "BTC/USDT", dir: "LONG", pnl: "+6.0%", time: "6h ago" },
  { pair: "ETH/USDT", dir: "LONG", pnl: "+3.5%", time: "7h ago" },
];

/* ─── Dashboard Mock Trades ─── */
export const MOCK_TRADES = [
  { pair: "BTC/USDT", side: "LONG", entry: "67,420", exit: "69,150", pnl: "+2.56%", conf: 8, result: "win" },
  { pair: "ETH/USDT", side: "LONG", entry: "3,512", exit: "3,648", pnl: "+3.87%", conf: 9, result: "win" },
  { pair: "SOL/USDT", side: "SHORT", entry: "142.8", exit: "138.5", pnl: "+3.01%", conf: 7, result: "win" },
  { pair: "BNB/USDT", side: "LONG", entry: "584.2", exit: "571.0", pnl: "-2.26%", conf: 6, result: "loss" },
  { pair: "BTC/USDT", side: "SHORT", entry: "69,800", exit: "68,100", pnl: "+2.43%", conf: 8, result: "win" },
  { pair: "ETH/USDT", side: "LONG", entry: "3,480", exit: "3,395", pnl: "-2.44%", conf: 5, result: "loss" },
];

/* ─── Rating Distribution ─── */
export const RATING_DISTRIBUTION = [
  { stars: 5, count: 3 },
  { stars: 4, count: 2 },
  { stars: 3, count: 0 },
  { stars: 2, count: 0 },
  { stars: 1, count: 0 },
];

export const RATING_TOTAL = RATING_DISTRIBUTION.reduce((s, r) => s + r.count, 0);

/* ─── Exchange Logos ─── */
export const exchangeLogos: Record<string, ReactNode> = {
  Bybit: (
    <svg viewBox="0 0 80 24" fill="currentColor" className="h-5 w-auto">
      <path d="M5.2 4h5.6c2.8 0 4.6 1.6 4.6 4.1 0 1.7-.9 3-2.4 3.5 1.8.5 2.9 2 2.9 3.8 0 2.7-1.9 4.6-5 4.6H5.2V4zm5.3 6.4c1.2 0 1.9-.7 1.9-1.7s-.7-1.7-1.9-1.7H8.3v3.4h2.2zm.3 6.6c1.3 0 2.1-.7 2.1-1.9s-.8-1.9-2.1-1.9H8.3V17h2.5zM19.2 15.5l-4.8-8h3.5l3 5.3 3-5.3h3.4l-4.8 8V20h-3.3v-4.5zM29.5 4h5.6c2.8 0 4.6 1.6 4.6 4.1 0 1.7-.9 3-2.4 3.5 1.8.5 2.9 2 2.9 3.8 0 2.7-1.9 4.6-5 4.6h-5.7V4zm5.3 6.4c1.2 0 1.9-.7 1.9-1.7s-.7-1.7-1.9-1.7h-2.2v3.4h2.2zm.3 6.6c1.3 0 2.1-.7 2.1-1.9s-.8-1.9-2.1-1.9h-2.5V17h2.5zM42.5 4h3.3v16h-3.3V4zm7.8 0h13v3h-4.8v13h-3.3V7h-4.9V4z" />
    </svg>
  ),
  Binance: (
    <svg viewBox="0 0 24 24" fill="currentColor" className="h-6 w-6">
      <path d="M12 1.5L5.5 8l2.4 2.4L12 6.3l4.1 4.1L18.5 8 12 1.5zM3.1 10.4l2.4 2.4-2.4 2.4L.7 12.8l2.4-2.4zm8.9 0L9.6 12.8l2.4 2.4 2.4-2.4-2.4-2.4zm8.9 0l-2.4 2.4 2.4 2.4 2.4-2.4-2.4-2.4zM12 17.7l-4.1-4.1-2.4 2.4L12 22.5l6.5-6.5-2.4-2.4L12 17.7z" />
    </svg>
  ),
  OKX: (
    <svg viewBox="0 0 80 24" fill="currentColor" className="h-5 w-auto">
      <path d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10 10-4.5 10-10S17.5 2 12 2zm0 16.5c-3.6 0-6.5-2.9-6.5-6.5S8.4 5.5 12 5.5s6.5 2.9 6.5 6.5-2.9 6.5-6.5 6.5zM30.5 4h3.5v16h-3.5V4zm7.5 0h3.8l3.5 6.2L48.8 4h3.8l-5.5 8.5L52.8 21H49l-3.7-6.6L41.6 21h-3.8l5.7-8.5L38 4zm17 0h3.5v16H55V4z" />
    </svg>
  ),
  Cornix: (
    <svg viewBox="0 0 24 24" fill="currentColor" className="h-6 w-6">
      <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 15.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 13v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z" />
    </svg>
  ),
  Freqtrade: (
    <svg viewBox="0 0 24 24" fill="currentColor" className="h-6 w-6">
      <path d="M3.5 18.49l6-6.01 4 4L22 6.92l-1.41-1.41-7.09 7.97-4-4L2 16.99z" />
      <path d="M3.5 18.49l6-6.01 4 4L22 6.92" fill="none" stroke="currentColor" strokeWidth="1.5" />
    </svg>
  ),
};
