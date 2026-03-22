"use client";

import { useEffect, useRef, useState, useCallback, type ReactNode } from "react";

/* ──────────────────────────── constants ──────────────────────────── */

const TELEGRAM_URL = "https://t.me/TrendRiderSignals";
const SHEETS_URL =
  "https://docs.google.com/spreadsheets/d/1ZWRJ0PcBSk910MZv426PrleriBnInykr3OebWXJPm-g";

/* ──────────────────────────── translations ──────────────────────────── */

const T = {
  en: {
    // navbar
    navPerformance: "Performance",
    navHowItWorks: "How It Works",
    navFeatures: "Features",
    navPricing: "Pricing",
    navFaq: "FAQ",
    joinTelegram: "Join Telegram",
    joinTelegramChannel: "Join Telegram Channel",
    viewLiveResults: "View Live Results",

    // hero
    liveSince: "Live since March 2026",
    paperVerified: "Paper-trading verified",
    tagline: "Algorithmic Signals.",
    taglineHighlight: "Verified Results.",
    heroDesc: (
      <>AI-powered crypto trading signals with a{" "}
      <span className="text-primary font-semibold">71% win rate</span> and{" "}
      <span className="text-primary font-semibold">1.81% max drawdown</span>.
      Multi-timeframe analysis across BTC, ETH, SOL, and BNB.</>
    ),
    winRate: "Win Rate",
    profitFactor: "Profit Factor",
    maxDD: "Max DD",
    publicTrack: "Public track record",
    algoTrading: "Algorithmic trading",
    openSource: "Open-source strategy",

    // metrics section
    metricsTag: "Performance",
    metricsTitle: "Numbers Don't Lie",
    metricsSubtitle: "Backtested on real market data. Every metric verified and publicly available.",
    metricsFooter: "Based on backtests with real market data",
    updatedMonthly: "Updated monthly",
    viewFullResults: "View full results",
    maxDrawdown: "Max Drawdown",
    sqnScore: "SQN Score",

    // how it works
    howTag: "Process",
    howTitle: "How It Works",
    howSubtitle: "Three simple steps to start receiving algorithmic trading signals.",
    step1Title: "Subscribe to Telegram",
    step1Desc: "Join our channel and start receiving algorithmic signals in real-time.",
    step2Title: "Auto-Trade via Cornix",
    step2Desc: "Connect Cornix bot for hands-free execution on Bybit, Binance, or OKX.",
    step3Title: "Track in Google Sheets",
    step3Desc: "Every trade is logged publicly. Full transparency, verifiable results.",

    // signal preview
    previewTag: "Preview",
    previewTitle: "What You'll Receive",
    previewSubtitle: "Every signal comes with entry zones, targets, stop-loss, and confidence rating.",

    // features
    featTag: "Features",
    featTitle: "Built for Serious Traders",
    featSubtitle: "Every detail engineered for consistent, risk-managed performance.",
    feat1Title: "Confidence Scoring",
    feat1Desc: "Every signal rated 1-10 based on multi-factor analysis. Only high-confidence trades.",
    feat2Title: "On-Chain Data",
    feat2Desc: "Fear & Greed Index, funding rates, open interest integrated into every decision.",
    feat3Title: "Cornix Auto-Trade",
    feat3Desc: "One-click setup. Signals execute automatically on your exchange account.",
    feat4Title: "Verified Track Record",
    feat4Desc: "Public Google Sheet with every trade. No cherry-picking, no hidden losses.",
    feat5Title: "Ultra-Low Drawdown",
    feat5Desc: "1.81% max drawdown. Conservative risk management with 6% stop-loss per trade.",
    feat6Title: "Real-Time Alerts",
    feat6Desc: "Instant Telegram notifications. Never miss an entry or exit signal.",

    // pricing
    priceTag: "Pricing",
    priceTitle: "Choose Your Plan",
    priceSubtitle: "Start free. Upgrade when you're ready.",
    free: "Free",
    forever: "forever",
    perMonth: "/month",
    mostPopular: "Most Popular",
    joinFree: "Join Free",
    subscribe: "Subscribe",
    getVip: "Go VIP",
    // Free features
    freeF1: "Delayed signals (3h)",
    freeF2: "Monthly performance report",
    freeF3: "Public results access",
    freeF4: "Community chat",
    // Basic features
    basicF1: "Real-time signals",
    basicF2: "Cornix auto-trade ready",
    basicF3: "Weekly performance recap",
    basicF4: "4 pairs: BTC/ETH/SOL/BNB",
    basicF5: "Priority support",
    // VIP features
    vipF1: "Everything in Basic",
    vipF2: "Post-trade review & analysis",
    vipF3: "Daily market brief",
    vipF4: "Priority support",
    vipF5: "Early access to new features",

    // faq
    faqTag: "FAQ",
    faqTitle: "Frequently Asked Questions",
    faq1Q: "What is TrendRider?",
    faq1A: "TrendRider is an AI-powered algorithmic trading system built on Freqtrade. It analyzes BTC, ETH, SOL, and BNB across multiple timeframes using 15+ technical indicators combined with on-chain data to generate high-confidence trade signals.",
    faq2Q: "How are signals generated?",
    faq2A: "Our algorithm combines 15+ technical indicators (RSI, MACD, Bollinger Bands, EMA crossovers, etc.), multi-timeframe analysis (5m, 15m, 1h, 4h), and on-chain metrics (Fear & Greed Index, funding rates, open interest) to identify high-probability setups.",
    faq3Q: "What's the track record?",
    faq3A: "All trades are logged in a public Google Sheet with full transparency. Our backtested results show a 71.1% win rate, 2.09 profit factor, and just 1.81% max drawdown. We also maintain a Strat Ninja verified profile.",
    faq4Q: "How do I auto-trade?",
    faq4A: "Connect the Cornix bot to our Telegram channel and link it to your exchange (Bybit, Binance, or OKX). Cornix will automatically execute trades based on our signals with your configured position sizing.",
    faq5Q: "Is it safe?",
    faq5A: "We use strict risk management: 6% stop-loss per trade, never risking more than 2% of portfolio per position. The system has been paper-trading since March 2026 with verified results. However, all trading involves risk and past performance does not guarantee future results.",

    // cta
    ctaTag: "Get Started",
    ctaTitle: "Ready to Trade",
    ctaTitleHighlight: "Smarter",
    ctaDesc: "Join traders receiving algorithmic signals powered by verified algorithms.",
    ctaSubDesc: "Free tier available. No credit card required.",
    getStarted: "Get Started on Telegram",
    viewAllResults: "View all results",

    // footer
    footerTagline: "Algorithmic Signals. Verified Results.",
    telegramChannel: "Telegram Channel",
    liveResults: "Live Results",
    riskDisclaimer: "Trading cryptocurrencies involves substantial risk of loss and is not suitable for every investor. Past performance is not indicative of future results. Never invest more than you can afford to lose. This is not financial advice.",
    poweredBy: "Powered by Freqtrade",
  },
  ru: {
    navPerformance: "Результаты",
    navHowItWorks: "Как это работает",
    navFeatures: "Возможности",
    navPricing: "Тарифы",
    navFaq: "FAQ",
    joinTelegram: "Telegram",
    joinTelegramChannel: "Подписаться на Telegram",
    viewLiveResults: "Смотреть результаты",

    liveSince: "Работает с марта 2026",
    paperVerified: "Paper-trading подтверждён",
    tagline: "Алгоритмические сигналы.",
    taglineHighlight: "Проверенные результаты.",
    heroDesc: (
      <>Крипто-сигналы на основе ИИ с{" "}
      <span className="text-primary font-semibold">винрейтом 71%</span> и{" "}
      <span className="text-primary font-semibold">просадкой 1.81%</span>.
      Мультитаймфрейм анализ BTC, ETH, SOL и BNB.</>
    ),
    winRate: "Винрейт",
    profitFactor: "Профит-фактор",
    maxDD: "Макс. просадка",
    publicTrack: "Публичный трек-рекорд",
    algoTrading: "Алгоритмический трейдинг",
    openSource: "Открытая стратегия",

    metricsTag: "Результаты",
    metricsTitle: "Цифры говорят сами",
    metricsSubtitle: "Бэктесты на реальных данных. Все метрики проверяемы и публичны.",
    metricsFooter: "На основе бэктестов с реальными данными",
    updatedMonthly: "Обновляется ежемесячно",
    viewFullResults: "Все результаты",
    maxDrawdown: "Макс. просадка",
    sqnScore: "SQN",

    howTag: "Процесс",
    howTitle: "Как это работает",
    howSubtitle: "Три простых шага для получения алгоритмических торговых сигналов.",
    step1Title: "Подпишитесь на Telegram",
    step1Desc: "Присоединяйтесь к каналу и получайте сигналы в реальном времени.",
    step2Title: "Авто-трейд через Cornix",
    step2Desc: "Подключите Cornix для автоматического исполнения на Bybit, Binance или OKX.",
    step3Title: "Отслеживайте в Google Sheets",
    step3Desc: "Каждая сделка записывается публично. Полная прозрачность и проверяемость.",

    previewTag: "Превью",
    previewTitle: "Что вы получите",
    previewSubtitle: "Каждый сигнал содержит зоны входа, цели, стоп-лосс и рейтинг уверенности.",

    featTag: "Возможности",
    featTitle: "Для серьёзных трейдеров",
    featSubtitle: "Каждая деталь спроектирована для стабильных результатов с управлением рисками.",
    feat1Title: "Оценка уверенности",
    feat1Desc: "Каждый сигнал оценивается от 1 до 10 на основе мультифакторного анализа.",
    feat2Title: "Данные on-chain",
    feat2Desc: "Fear & Greed Index, funding rates, open interest интегрированы в каждое решение.",
    feat3Title: "Авто-трейд Cornix",
    feat3Desc: "Настройка в один клик. Сигналы исполняются автоматически на вашей бирже.",
    feat4Title: "Проверяемый трек-рекорд",
    feat4Desc: "Публичная Google Таблица с каждой сделкой. Без подтасовок и скрытых убытков.",
    feat5Title: "Минимальная просадка",
    feat5Desc: "Просадка 1.81%. Консервативный риск-менеджмент со стоп-лоссом 6% на сделку.",
    feat6Title: "Уведомления в реальном времени",
    feat6Desc: "Мгновенные Telegram-уведомления. Не пропустите ни одного входа или выхода.",

    priceTag: "Тарифы",
    priceTitle: "Выберите план",
    priceSubtitle: "Начните бесплатно. Перейдите на платный, когда будете готовы.",
    free: "Бесплатно",
    forever: "навсегда",
    perMonth: "/мес",
    mostPopular: "Популярный",
    joinFree: "Начать бесплатно",
    subscribe: "Подписаться",
    getVip: "Получить VIP",
    freeF1: "Сигналы с задержкой (3ч)",
    freeF2: "Ежемесячный отчёт",
    freeF3: "Доступ к результатам",
    freeF4: "Общий чат",
    basicF1: "Сигналы в реальном времени",
    basicF2: "Формат для Cornix",
    basicF3: "Еженедельный отчёт",
    basicF4: "4 пары: BTC/ETH/SOL/BNB",
    basicF5: "Приоритетная поддержка",
    vipF1: "Всё из Basic",
    vipF2: "Пост-трейд анализ",
    vipF3: "Ежедневный брифинг",
    vipF4: "Приоритетная поддержка",
    vipF5: "Ранний доступ к фичам",

    faqTag: "FAQ",
    faqTitle: "Частые вопросы",
    faq1Q: "Что такое TrendRider?",
    faq1A: "TrendRider — это алгоритмическая торговая система на базе ИИ, построенная на Freqtrade. Она анализирует BTC, ETH, SOL и BNB на нескольких таймфреймах, используя 15+ технических индикаторов и данные on-chain для генерации высокоточных торговых сигналов.",
    faq2Q: "Как генерируются сигналы?",
    faq2A: "Наш алгоритм объединяет 15+ технических индикаторов (RSI, MACD, Bollinger Bands, пересечения EMA и др.), мультитаймфрейм анализ (5м, 15м, 1ч, 4ч) и метрики on-chain (Fear & Greed Index, funding rates, open interest) для определения высоковероятных сетапов.",
    faq3Q: "Какой трек-рекорд?",
    faq3A: "Все сделки записываются в публичную Google Таблицу с полной прозрачностью. Результаты бэктестов: винрейт 71.1%, профит-фактор 2.09 и просадка всего 1.81%. Также ведётся верифицированный профиль на Strat Ninja.",
    faq4Q: "Как настроить авто-трейд?",
    faq4A: "Подключите бота Cornix к нашему Telegram-каналу и привяжите его к вашей бирже (Bybit, Binance или OKX). Cornix будет автоматически исполнять сделки на основе наших сигналов с вашими настройками размера позиции.",
    faq5Q: "Безопасно ли это?",
    faq5A: "Мы используем строгий риск-менеджмент: стоп-лосс 6% на сделку, риск не более 2% портфеля на позицию. Система работает в режиме paper-trading с марта 2026 с верифицированными результатами. Однако любая торговля сопряжена с рисками, и прошлые результаты не гарантируют будущих.",

    ctaTag: "Начать",
    ctaTitle: "Готовы торговать",
    ctaTitleHighlight: "умнее",
    ctaDesc: "Присоединяйтесь к трейдерам, получающим алгоритмические сигналы.",
    ctaSubDesc: "Бесплатный тариф. Без привязки карты.",
    getStarted: "Начать в Telegram",
    viewAllResults: "Все результаты",

    footerTagline: "Алгоритмические сигналы. Проверенные результаты.",
    telegramChannel: "Telegram-канал",
    liveResults: "Результаты",
    riskDisclaimer: "Торговля криптовалютами сопряжена со значительным риском убытков и подходит не каждому инвестору. Прошлые результаты не гарантируют будущих. Никогда не инвестируйте больше, чем можете позволить себе потерять. Это не финансовая рекомендация.",
    poweredBy: "На базе Freqtrade",
  },
} as const;

type Locale = "en" | "ru";
// eslint-disable-next-line @typescript-eslint/no-explicit-any
type TStrings = Record<string, any>;

/* ──────────────────────────── dynamic data builders ──────────────────────────── */

const getMetrics = (t: TStrings) => [
  { label: t.winRate, value: 71.1, suffix: "%", decimals: 1, barWidth: 71.1 },
  { label: t.maxDrawdown, value: 1.81, suffix: "%", decimals: 2, barWidth: 18.1 },
  { label: t.profitFactor, value: 2.09, suffix: "x", decimals: 2, barWidth: 69.7 },
  { label: t.sqnScore, value: 3.02, suffix: "", decimals: 2, barWidth: 75.5 },
];

const getStepIcons = () => [
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

const getSteps = (t: TStrings) => {
  const icons = getStepIcons();
  return [
    { num: "01", icon: icons[0], title: t.step1Title, desc: t.step1Desc },
    { num: "02", icon: icons[1], title: t.step2Title, desc: t.step2Desc },
    { num: "03", icon: icons[2], title: t.step3Title, desc: t.step3Desc },
  ];
};

const featureIcons: ReactNode[] = [
  <div key="f1" className="w-12 h-12 flex items-center justify-center rounded-xl bg-primary/10 text-primary mb-4 group-hover:bg-primary/15 transition-colors">
    <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 12m-9 0a9 9 0 1 0 18 0 9 9 0 1 0-18 0" />
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 12m-5 0a5 5 0 1 0 10 0 5 5 0 1 0-10 0" />
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 12m-1 0a1 1 0 1 0 2 0 1 1 0 1 0-2 0" />
    </svg>
  </div>,
  <div key="f2" className="w-12 h-12 flex items-center justify-center rounded-xl bg-primary/10 text-primary mb-4 group-hover:bg-primary/15 transition-colors">
    <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 0 1 3 19.875v-6.75ZM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V8.625ZM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V4.125Z" />
    </svg>
  </div>,
  <div key="f3" className="w-12 h-12 flex items-center justify-center rounded-xl bg-primary/10 text-primary mb-4 group-hover:bg-primary/15 transition-colors">
    <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.325.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 0 1 1.37.49l1.296 2.247a1.125 1.125 0 0 1-.26 1.431l-1.003.827c-.293.241-.438.613-.43.992a7.723 7.723 0 0 1 0 .255c-.008.378.137.75.43.991l1.004.827c.424.35.534.955.26 1.43l-1.298 2.247a1.125 1.125 0 0 1-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.47 6.47 0 0 1-.22.128c-.331.183-.581.495-.644.869l-.213 1.281c-.09.543-.56.94-1.11.94h-2.594c-.55 0-1.019-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 0 1-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 0 1-1.369-.49l-1.297-2.247a1.125 1.125 0 0 1 .26-1.431l1.004-.827c.292-.24.437-.613.43-.991a6.932 6.932 0 0 1 0-.255c.007-.38-.138-.751-.43-.992l-1.004-.827a1.125 1.125 0 0 1-.26-1.43l1.297-2.247a1.125 1.125 0 0 1 1.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.086.22-.128.332-.183.582-.495.644-.869l.214-1.28Z" />
      <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" />
    </svg>
  </div>,
  <div key="f4" className="w-12 h-12 flex items-center justify-center rounded-xl bg-primary/10 text-primary mb-4 group-hover:bg-primary/15 transition-colors">
    <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 18 9 11.25l4.306 4.306a11.95 11.95 0 0 1 5.814-5.518l2.74-1.22m0 0-5.94-2.281m5.94 2.28-2.28 5.941" />
    </svg>
  </div>,
  <div key="f5" className="w-12 h-12 flex items-center justify-center rounded-xl bg-primary/10 text-primary mb-4 group-hover:bg-primary/15 transition-colors">
    <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75m-3-7.036A11.959 11.959 0 0 1 3.598 6 11.99 11.99 0 0 0 3 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285Z" />
    </svg>
  </div>,
  <div key="f6" className="w-12 h-12 flex items-center justify-center rounded-xl bg-primary/10 text-primary mb-4 group-hover:bg-primary/15 transition-colors">
    <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M14.857 17.082a23.848 23.848 0 0 0 5.454-1.31A8.967 8.967 0 0 1 18 9.75V9A6 6 0 0 0 6 9v.75a8.967 8.967 0 0 1-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 0 1-5.714 0m5.714 0a3 3 0 1 1-5.714 0" />
    </svg>
  </div>,
];

const getFeatures = (t: TStrings): { icon: ReactNode; title: string; desc: string }[] => [
  { icon: featureIcons[0], title: t.feat1Title, desc: t.feat1Desc },
  { icon: featureIcons[1], title: t.feat2Title, desc: t.feat2Desc },
  { icon: featureIcons[2], title: t.feat3Title, desc: t.feat3Desc },
  { icon: featureIcons[3], title: t.feat4Title, desc: t.feat4Desc },
  { icon: featureIcons[4], title: t.feat5Title, desc: t.feat5Desc },
  { icon: featureIcons[5], title: t.feat6Title, desc: t.feat6Desc },
];

const getPricing = (t: TStrings) => [
  {
    name: t.free,
    price: "$0",
    period: t.forever,
    features: [t.freeF1, t.freeF2, t.freeF3, t.freeF4],
    cta: t.joinFree,
    href: TELEGRAM_URL,
    highlight: false,
  },
  {
    name: "Basic",
    price: "$39",
    period: t.perMonth,
    features: [t.basicF1, t.basicF2, t.basicF3, t.basicF4],
    cta: t.subscribe,
    href: TELEGRAM_URL,
    highlight: false,
  },
  {
    name: "VIP",
    price: "$99",
    period: t.perMonth,
    features: [t.vipF1, t.vipF2, t.vipF3, t.vipF4, t.vipF5],
    cta: t.getVip,
    href: TELEGRAM_URL,
    highlight: true,
  },
];

const getFaqItems = (t: TStrings) => [
  { q: t.faq1Q, a: t.faq1A },
  { q: t.faq2Q, a: t.faq2A },
  { q: t.faq3Q, a: t.faq3A },
  { q: t.faq4Q, a: t.faq4A },
  { q: t.faq5Q, a: t.faq5A },
];

// Live ticker trades
const TICKER_TRADES = [
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

/* ──────────────────────────── hooks ──────────────────────────── */

function useInView(threshold = 0.15) {
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

function useScrollProgress() {
  const [pct, setPct] = useState(0);
  useEffect(() => {
    const onScroll = () => {
      const el = document.documentElement;
      const scrolled = el.scrollTop;
      const total = el.scrollHeight - el.clientHeight;
      setPct(total > 0 ? (scrolled / total) * 100 : 0);
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);
  return pct;
}

function useFloatingVisible() {
  const [show, setShow] = useState(false);
  useEffect(() => {
    const onScroll = () => setShow(window.scrollY > window.innerHeight * 0.8);
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);
  return show;
}

function useNavVisible() {
  const [show, setShow] = useState(false);
  useEffect(() => {
    const onScroll = () => setShow(window.scrollY > 100);
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);
  return show;
}

/* ──────────────────────────── small components ──────────────────────────── */

function LanguageToggle({ locale, setLocale, className = "" }: { locale: Locale; setLocale: (fn: (l: Locale) => Locale) => void; className?: string }) {
  return (
    <button
      onClick={() => setLocale(l => l === "en" ? "ru" : "en")}
      className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full border border-border/50 text-xs font-mono hover:border-primary/30 transition-all ${className}`}
    >
      <span className={locale === "en" ? "text-primary font-medium" : "text-muted"}>EN</span>
      <span className="text-border/50">/</span>
      <span className={locale === "ru" ? "text-primary font-medium" : "text-muted"}>RU</span>
    </button>
  );
}

function MetricCard({
  label,
  value,
  suffix,
  decimals,
  barWidth,
  active,
  delay,
}: {
  label: string;
  value: number;
  suffix: string;
  decimals: number;
  barWidth: number;
  active: boolean;
  delay: number;
}) {
  const count = useCounter(value, decimals, active);
  return (
    <div
      className={`metric-card reveal ${active ? "visible" : ""} text-center p-6 rounded-2xl bg-card/50 border border-border/50 backdrop-blur-sm reveal-delay-${delay}`}
    >
      <div className="font-mono text-4xl md:text-5xl font-bold text-primary mb-1">
        {count.toFixed(decimals)}
        <span className="text-xl md:text-2xl text-muted ml-1">{suffix}</span>
      </div>
      <div className="text-xs text-muted uppercase tracking-widest mb-4">{label}</div>
      <div className="h-1 w-full bg-border/50 rounded-full overflow-hidden">
        <div
          className="progress-bar-fill"
          style={
            {
              "--target-width": `${barWidth}%`,
              width: active ? `${barWidth}%` : "0%",
              transition: active ? `width 1.8s cubic-bezier(0.16, 1, 0.3, 1) ${delay * 0.1}s` : "none",
            } as React.CSSProperties
          }
        />
      </div>
    </div>
  );
}

function FAQItem({ q, a }: { q: string; a: string }) {
  const [open, setOpen] = useState(false);
  return (
    <div className={`faq-item border border-border/50 rounded-xl overflow-hidden`}>
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between p-5 text-left hover:bg-card/40 transition-colors"
        aria-expanded={open}
      >
        <span className="font-medium text-foreground pr-4">{q}</span>
        <svg
          className={`w-5 h-5 text-primary shrink-0 transition-transform duration-300 ${open ? "rotate-180" : ""}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="m19 9-7 7-7-7" />
        </svg>
      </button>
      <div
        className={`overflow-hidden transition-all duration-300 ${open ? "max-h-96 opacity-100" : "max-h-0 opacity-0"}`}
      >
        <p className="px-5 pb-5 text-muted leading-relaxed text-sm">{a}</p>
      </div>
    </div>
  );
}

function SectionHeading({
  tag,
  title,
  subtitle,
  visible,
}: {
  tag: string;
  title: string;
  subtitle?: string;
  visible?: boolean;
}) {
  return (
    <div className="text-center mb-16">
      <span
        className={`reveal ${visible ? "visible" : ""} inline-block px-4 py-1.5 text-xs font-mono uppercase tracking-widest text-primary border border-primary/30 rounded-full mb-5`}
      >
        {tag}
      </span>
      <h2
        className={`reveal reveal-delay-1 ${visible ? "visible" : ""} text-3xl md:text-4xl lg:text-5xl font-bold mb-4 tracking-tight`}
      >
        {title}
      </h2>
      {subtitle && (
        <p
          className={`reveal reveal-delay-2 ${visible ? "visible" : ""} text-muted max-w-2xl mx-auto text-lg leading-relaxed`}
        >
          {subtitle}
        </p>
      )}
    </div>
  );
}

/* ─── Candlestick SVG background ─── */

function CandlestickChart() {
  const candles = [
    { x: 20,  open: 130, close: 110, high: 100, low: 145 },
    { x: 50,  open: 112, close:  90, high:  82, low: 125 },
    { x: 80,  open:  92, close: 108, high:  78, low: 115 },
    { x: 110, open: 106, close:  88, high:  80, low: 118 },
    { x: 140, open:  90, close:  72, high:  65, low: 100 },
    { x: 170, open:  74, close:  95, high:  60, low: 102 },
    { x: 200, open:  93, close:  78, high:  70, low: 105 },
    { x: 230, open:  80, close:  60, high:  52, low:  90 },
    { x: 260, open:  62, close:  48, high:  40, low:  72 },
    { x: 290, open:  50, close:  70, high:  38, low:  78 },
    { x: 320, open:  68, close:  52, high:  44, low:  80 },
    { x: 350, open:  54, close:  36, high:  28, low:  62 },
    { x: 380, open:  38, close:  55, high:  25, low:  62 },
    { x: 410, open:  53, close:  40, high:  32, low:  60 },
    { x: 440, open:  42, close:  28, high:  20, low:  50 },
    { x: 470, open:  30, close:  48, high:  18, low:  55 },
    { x: 500, open:  46, close:  62, high:  35, low:  68 },
    { x: 530, open:  60, close:  45, high:  38, low:  70 },
    { x: 560, open:  47, close:  30, high:  22, low:  55 },
    { x: 590, open:  32, close:  50, high:  20, low:  58 },
  ];

  const linePoints = candles.map(c => `${c.x},${Math.min(c.open, c.close)}`).join(" ");

  // Pseudo-random shuffle for glow order (deterministic, SSR-safe)
  const glowOrder = [14, 3, 17, 7, 11, 0, 19, 5, 13, 9, 2, 16, 8, 4, 18, 10, 1, 15, 6, 12];

  return (
    <svg
      className="absolute inset-0 w-full h-full"
      viewBox="0 0 620 200"
      preserveAspectRatio="xMidYMid slice"
      aria-hidden="true"
    >
      {/* Glow filters */}
      <defs>
        <filter id="glowGreen" x="-50%" y="-50%" width="200%" height="200%">
          <feGaussianBlur stdDeviation="4" result="blur" />
          <feFlood floodColor="#00D4AA" floodOpacity="0.8" />
          <feComposite in2="blur" operator="in" />
          <feMerge>
            <feMergeNode />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
        <filter id="glowRed" x="-50%" y="-50%" width="200%" height="200%">
          <feGaussianBlur stdDeviation="4" result="blur" />
          <feFlood floodColor="#FF4757" floodOpacity="0.8" />
          <feComposite in2="blur" operator="in" />
          <feMerge>
            <feMergeNode />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>
      {/* Trend line */}
      <polyline
        points={linePoints}
        fill="none"
        stroke="#00D4AA"
        strokeWidth="1.5"
        strokeDasharray="1000"
        strokeDashoffset="0"
        opacity="0.07"
        style={{ animation: "chartLine 2s ease-out forwards" }}
      />
      {/* Candles */}
      {candles.map((c, i) => {
        const isGreen = c.close < c.open;
        const color = isGreen ? "#00D4AA" : "#FF4757";
        const filterId = isGreen ? "glowGreen" : "glowRed";
        const bodyTop = Math.min(c.open, c.close);
        const bodyH = Math.abs(c.open - c.close);
        const glowSlot = glowOrder[i] ?? i;
        const glowDelay = glowSlot * 0.5;
        const totalCycle = candles.length * 0.5 + 3;
        return (
          <g
            key={i}
            style={{
              animation: `candleRise 0.5s ease-out ${i * 0.06}s forwards, candleGlowPulse ${totalCycle}s ease-in-out ${glowDelay}s infinite`,
              opacity: 0,
              "--glow-filter": `url(#${filterId})`,
            } as React.CSSProperties}
            className="candle-group"
          >
            {/* Wick */}
            <line x1={c.x} y1={c.high} x2={c.x} y2={c.low} stroke={color} strokeWidth="1" />
            {/* Body */}
            <rect x={c.x - 7} y={bodyTop} width="14" height={Math.max(bodyH, 2)} fill={color} rx="1" />
          </g>
        );
      })}
      {/* Grid lines */}
      {[50, 100, 150].map(y => (
        <line key={y} x1="0" y1={y} x2="620" y2={y} stroke="#00D4AA" strokeWidth="0.5" opacity="0.05" strokeDasharray="4 8" />
      ))}
    </svg>
  );
}

/* ─── Particles ─── */

function Particles() {
  const particles = Array.from({ length: 24 }, (_, i) => ({
    id: i,
    x: Math.random() * 100,
    y: 20 + Math.random() * 80,
    size: 1 + Math.random() * 2,
    delay: Math.random() * 6,
    duration: 4 + Math.random() * 5,
    alt: i % 2 === 0,
  }));

  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none" aria-hidden="true">
      {particles.map(p => (
        <div
          key={p.id}
          className="absolute rounded-full"
          style={{
            left: `${p.x}%`,
            top: `${p.y}%`,
            width: `${p.size}px`,
            height: `${p.size}px`,
            background: p.id % 3 === 0 ? "#FFD700" : "#00D4AA",
            animation: `${p.alt ? "floatParticleAlt" : "floatParticle"} ${p.duration}s ${p.delay}s ease-in-out infinite`,
            opacity: 0,
          }}
        />
      ))}
    </div>
  );
}

/* ─── Live Ticker ─── */

function LiveTicker() {
  const doubled = [...TICKER_TRADES, ...TICKER_TRADES];
  return (
    <div className="w-full overflow-hidden border-y border-border/40 bg-card/30 backdrop-blur-sm py-3 relative">
      {/* Fade edges */}
      <div className="absolute left-0 top-0 bottom-0 w-16 z-10 bg-gradient-to-r from-card/80 to-transparent pointer-events-none" />
      <div className="absolute right-0 top-0 bottom-0 w-16 z-10 bg-gradient-to-l from-card/80 to-transparent pointer-events-none" />

      <div className="marquee-track gap-0">
        {doubled.map((t, i) => (
          <div
            key={i}
            className="flex items-center gap-3 px-6 shrink-0 border-r border-border/20"
          >
            <span className="font-mono text-xs text-muted">{t.time}</span>
            <span
              className={`w-1.5 h-1.5 rounded-full shrink-0 ${t.dir === "LONG" ? "bg-primary" : "bg-danger"}`}
            />
            <span className="font-mono text-xs font-semibold text-foreground">{t.pair}</span>
            <span
              className={`font-mono text-xs font-bold px-2 py-0.5 rounded ${
                t.dir === "LONG"
                  ? "bg-primary/10 text-primary"
                  : "bg-danger/10 text-danger"
              }`}
            >
              {t.dir}
            </span>
            <span className="font-mono text-xs font-bold text-primary">{t.pnl}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ─── Telegram Signal Preview ─── */

function SignalPreview({ visible }: { visible: boolean }) {
  const [showTyping, setShowTyping] = useState(true);
  const [showMessage, setShowMessage] = useState(false);
  const [justReceived, setJustReceived] = useState(false);

  useEffect(() => {
    if (!visible) return;
    const t1 = setTimeout(() => {
      setShowTyping(false);
      setShowMessage(true);
      setJustReceived(true);
    }, 1800);
    const t2 = setTimeout(() => setJustReceived(false), 4500);
    return () => { clearTimeout(t1); clearTimeout(t2); };
  }, [visible]);

  return (
    <div className="max-w-sm mx-auto">
      {/* Telegram-style chat header */}
      <div className="flex items-center gap-3 px-4 py-3 bg-[#17212b] rounded-t-2xl border-b border-white/5">
        <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center shrink-0">
          <svg className="w-4 h-4 text-primary" viewBox="0 0 24 24" fill="currentColor">
            <path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z" />
          </svg>
        </div>
        <div className="flex-1 min-w-0">
          <div className="text-sm font-semibold text-white truncate">TrendRider Signals</div>
          <div className="text-xs text-[#8B949E]">
            {showTyping && visible ? (
              <span className="flex items-center gap-1">
                <span>typing</span>
                <span className="flex items-center gap-0.5 ml-1">
                  <span className="typing-dot" />
                  <span className="typing-dot" />
                  <span className="typing-dot" />
                </span>
              </span>
            ) : (
              "subscribers"
            )}
          </div>
        </div>
        <div className="flex items-center gap-1.5 shrink-0">
          {justReceived && (
            <span
              className="text-xs font-mono px-2 py-0.5 bg-primary/20 text-primary rounded-full border border-primary/30"
              style={{ animation: "slideInRight 0.3s ease-out" }}
            >
              Just now
            </span>
          )}
          <div className="w-2 h-2 rounded-full bg-primary animate-pulse" />
        </div>
      </div>

      {/* Chat body */}
      <div className="bg-[#0e1621] rounded-b-2xl px-4 pb-4 pt-4 min-h-[320px] flex items-end">
        {showTyping && visible && !showMessage && (
          <div className="tg-bubble px-4 py-3 inline-flex items-center gap-1.5">
            <span className="typing-dot" />
            <span className="typing-dot" />
            <span className="typing-dot" />
          </div>
        )}

        {showMessage && (
          <div
            className="tg-bubble px-4 py-3 font-mono text-sm leading-relaxed w-full"
            style={{ animation: "scaleIn 0.35s cubic-bezier(0.16, 1, 0.3, 1) forwards" }}
          >
            <div className="space-y-1">
              <p>
                <span className="text-muted">📊</span>{" "}
                <span className="text-foreground font-semibold">TrendRider Signal #042</span>
              </p>
              <p>
                <span className="text-primary font-bold">🟢 LONG BTC/USDT</span>
              </p>
            </div>

            <div className="my-3 h-px bg-border/40" />

            <div className="space-y-1.5 text-xs">
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
                <span className="text-muted">— 30%</span>
              </p>
              <p>
                <span className="text-muted">TP2:</span>{" "}
                <span className="text-primary">$67,410 (+5.0%)</span>{" "}
                <span className="text-muted">— 40%</span>
              </p>
              <p>
                <span className="text-muted">TP3:</span>{" "}
                <span className="text-primary">$70,620 (+10.0%)</span>{" "}
                <span className="text-muted">— 30%</span>
              </p>
            </div>

            <div className="my-3 h-px bg-border/40" />

            <div className="space-y-1 text-xs">
              <p>
                <span className="text-muted">Confidence:</span>{" "}
                <span className="text-primary">████████</span>
                <span className="text-border">██</span>{" "}
                <span className="text-accent font-bold">8/10</span>
              </p>
              <p>
                <span className="text-muted">Setup:</span>{" "}
                <span className="text-foreground">Trend Pullback</span>
              </p>
              <p>
                <span className="text-muted">Regime:</span>{" "}
                <span className="text-primary">Trending Bull 📈</span>
              </p>
            </div>

            <div className="flex items-center justify-end gap-1 mt-2 opacity-50">
              <span className="text-[10px] font-mono text-muted">12:34</span>
              <svg className="w-3.5 h-3.5 text-primary" fill="currentColor" viewBox="0 0 16 16">
                <path d="M12.354 4.354a.5.5 0 0 0-.708-.708L5 10.293 1.854 7.146a.5.5 0 1 0-.708.708l3.5 3.5a.5.5 0 0 0 .708 0l7-7zm-4.208 7-.896-.897.707-.707.543.543 6.646-6.647a.5.5 0 0 1 .708.708l-7 7a.5.5 0 0 1-.708 0z"/>
              </svg>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

/* ──────────────────────────── main page ──────────────────────────── */

export default function Home() {
  const [locale, setLocale] = useState<Locale>("en");
  const t = T[locale];

  const metricsSection = useInView(0.2);
  const howItWorks = useInView(0.15);
  const signalSection = useInView(0.2);
  const featuresSection = useInView(0.1);
  const pricingSection = useInView(0.1);
  const faqSection = useInView(0.1);
  const ctaSection = useInView(0.2);

  const scrollProgress = useScrollProgress();
  const floatingVisible = useFloatingVisible();
  const navVisible = useNavVisible();

  const scrollTo = useCallback((ref: React.RefObject<HTMLDivElement | null>) => {
    if (ref.current) {
      const offset = 80; // navbar height
      const top = ref.current.getBoundingClientRect().top + window.scrollY - offset;
      window.scrollTo({ top, behavior: "smooth" });
    }
  }, []);

  const metrics = getMetrics(t);
  const steps = getSteps(t);
  const features = getFeatures(t);
  const pricing = getPricing(t);
  const faqItems = getFaqItems(t);

  return (
    <div className="grid-bg relative">
      {/* Scroll progress bar */}
      <div
        className="scroll-line"
        style={{ width: `${scrollProgress}%` }}
        aria-hidden="true"
      />

      {/* ─── STICKY NAVBAR ─── */}
      <nav
        className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
          navVisible
            ? "translate-y-0 opacity-100"
            : "-translate-y-full opacity-0 pointer-events-none"
        } bg-background/80 backdrop-blur-xl border-b border-border/50`}
      >
        <div className="max-w-5xl mx-auto flex items-center justify-between px-4 py-3">
          <span className="text-lg font-bold gradient-text">TrendRider</span>
          <div className="hidden md:flex items-center gap-6">
            {[
              { label: t.navPerformance, ref: metricsSection.ref },
              { label: t.navHowItWorks, ref: howItWorks.ref },
              { label: t.navFeatures, ref: featuresSection.ref },
              { label: t.navPricing, ref: pricingSection.ref },
              { label: t.navFaq, ref: faqSection.ref },
            ].map((item) => (
              <button
                key={item.label}
                onClick={() => scrollTo(item.ref)}
                className="text-sm text-muted hover:text-foreground transition-colors cursor-pointer"
              >
                {item.label}
              </button>
            ))}
          </div>
          <div className="flex items-center gap-3">
            <LanguageToggle locale={locale} setLocale={setLocale} />
            <a
              href={TELEGRAM_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="btn-primary btn-press flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold"
            >
              <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="currentColor">
                <path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z" />
              </svg>
              {t.joinTelegram}
            </a>
          </div>
        </div>
      </nav>

      {/* Floating CTA */}
      <div className={`floating-btn ${floatingVisible ? "visible" : ""}`}>
        <a
          href={TELEGRAM_URL}
          target="_blank"
          rel="noopener noreferrer"
          className="btn-primary btn-press flex items-center gap-2.5 px-5 py-3 rounded-2xl shadow-2xl text-sm font-semibold"
          aria-label={t.joinTelegramChannel}
        >
          <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
            <path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z" />
          </svg>
          {t.joinTelegram}
        </a>
      </div>

      {/* ─── HERO ─── */}
      <section className="relative min-h-screen flex items-center justify-center px-4 overflow-hidden">
        {/* Deep atmospheric glow */}
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_80%_60%_at_50%_-10%,rgba(0,212,170,0.08)_0%,transparent_70%)] pointer-events-none" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_40%_40%_at_75%_70%,rgba(255,215,0,0.04)_0%,transparent_60%)] pointer-events-none" />

        {/* Floating gradient orbs */}
        <div className="absolute top-1/4 left-1/4 w-[500px] h-[500px] rounded-full bg-primary/[0.03] blur-[120px] animate-orb-1" />
        <div className="absolute bottom-1/3 right-1/5 w-[400px] h-[400px] rounded-full bg-accent/[0.02] blur-[100px] animate-orb-2" />
        <div className="absolute top-2/3 left-2/3 w-[300px] h-[300px] rounded-full bg-danger/[0.02] blur-[80px] animate-orb-3" />

        {/* Candlestick chart background — faded in center so text is readable */}
        <div className="absolute inset-0 pointer-events-none" style={{
          maskImage: "radial-gradient(ellipse 65% 75% at 50% 50%, transparent 25%, black 85%)",
          WebkitMaskImage: "radial-gradient(ellipse 65% 75% at 50% 50%, transparent 25%, black 85%)",
        }}>
          <CandlestickChart />
        </div>

        {/* Floating particles */}
        <Particles />

        {/* Animated scan line */}
        <div className="absolute left-0 right-0 h-px scan-line-animate" style={{
          background: "linear-gradient(90deg, transparent, rgba(0,212,170,0.2), transparent)",
        }} />

        {/* Language toggle in hero — visible before navbar appears */}
        <LanguageToggle
          locale={locale}
          setLocale={setLocale}
          className="absolute top-8 right-8 z-20 bg-background/80 backdrop-blur-xl"
        />

        {/* Live badge — positioned at top of hero, above candles */}
        <div
          className="absolute top-8 left-1/2 -translate-x-1/2 z-20 inline-flex items-center gap-2 px-5 py-2.5 rounded-full border border-primary/40 bg-background/90 backdrop-blur-xl shadow-lg shadow-black/30"
          style={{ animation: "fadeInDown 0.6s ease-out forwards" }}
        >
          <span className="w-2 h-2 rounded-full bg-primary animate-pulse" />
          <span className="text-sm font-mono text-primary font-medium">{t.liveSince}</span>
          <span className="w-px h-3 bg-primary/30" />
          <span className="text-xs font-mono text-foreground/60">{t.paperVerified}</span>
        </div>

        <div className="relative text-center max-w-4xl mx-auto z-10">
          {/* Logo icon */}
          <div className="flex items-center justify-center gap-3 mb-2" style={{ animation: "fadeInUp 0.7s 0.15s cubic-bezier(0.16, 1, 0.3, 1) both" }}>
            <svg width="40" height="40" viewBox="0 0 40 40" fill="none" className="text-primary">
              <rect x="16" y="8" width="8" height="20" rx="1" fill="currentColor" opacity="0.9" />
              <line x1="20" y1="4" x2="20" y2="8" stroke="currentColor" strokeWidth="2" opacity="0.6" />
              <line x1="20" y1="28" x2="20" y2="34" stroke="currentColor" strokeWidth="2" opacity="0.6" />
              <rect x="16" y="8" width="8" height="20" rx="1" fill="currentColor" opacity="0.15">
                <animate attributeName="opacity" values="0.15;0.4;0.15" dur="3s" repeatCount="indefinite" />
              </rect>
            </svg>
          </div>

          {/* Headline — animated letter reveal */}
          <h1 className="text-6xl md:text-8xl font-bold tracking-tight mb-4"
            style={{ animation: "fadeInUp 0.7s 0.2s cubic-bezier(0.16, 1, 0.3, 1) both" }}>
            {"TrendRider".split("").map((letter, i) => (
              <span
                key={i}
                className="gradient-text inline-block"
                style={{
                  animation: `letterReveal 0.5s ${0.3 + i * 0.05}s cubic-bezier(0.16, 1, 0.3, 1) both`,
                }}
              >
                {letter}
              </span>
            ))}
          </h1>

          <p
            className="text-xl md:text-3xl text-foreground/80 font-light mb-3 tracking-wide"
            style={{ animation: "fadeInUp 0.7s 0.35s cubic-bezier(0.16, 1, 0.3, 1) both" }}
          >
            {t.tagline}{" "}
            <span className="text-primary font-normal">{t.taglineHighlight}</span>
          </p>

          <p
            className="text-muted max-w-xl mx-auto mb-10 leading-relaxed text-base md:text-lg"
            style={{ animation: "fadeInUp 0.7s 0.5s cubic-bezier(0.16, 1, 0.3, 1) both" }}
          >
            {t.heroDesc}
          </p>

          {/* Quick stats row */}
          <div
            className="flex items-center justify-center gap-6 md:gap-10 mb-10 text-sm"
            style={{ animation: "fadeInUp 0.7s 0.6s cubic-bezier(0.16, 1, 0.3, 1) both" }}
          >
            {[
              { v: "71.1%", l: t.winRate },
              { v: "2.09x", l: t.profitFactor },
              { v: "1.81%", l: t.maxDD },
            ].map(stat => (
              <div key={stat.l} className="text-center">
                <div className="font-mono font-bold text-xl text-primary">{stat.v}</div>
                <div className="text-muted text-xs uppercase tracking-wider mt-0.5">{stat.l}</div>
              </div>
            ))}
          </div>

          <div
            className="flex flex-col sm:flex-row items-center justify-center gap-4"
            style={{ animation: "fadeInUp 0.7s 0.7s cubic-bezier(0.16, 1, 0.3, 1) both" }}
          >
            <a
              href={TELEGRAM_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="btn-primary btn-press group flex items-center gap-3 px-8 py-4 rounded-xl text-sm md:text-base animate-pulse-glow"
            >
              <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
                <path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z" />
              </svg>
              {t.joinTelegramChannel}
              <svg
                className="w-4 h-4 transition-transform group-hover:translate-x-1"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
              >
                <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5 21 12m0 0-7.5 7.5M21 12H3" />
              </svg>
            </a>
            <a
              href={SHEETS_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="btn-press flex items-center gap-3 px-8 py-4 border border-border text-foreground font-medium rounded-xl hover:bg-card/50 hover:border-primary/30 transition-all text-sm md:text-base"
            >
              <svg className="w-5 h-5 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 0 1 3 19.875v-6.75ZM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V8.625ZM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V4.125Z" />
              </svg>
              {t.viewLiveResults}
            </a>
          </div>

          {/* Social proof */}
          <div className="flex items-center justify-center gap-6 mt-12 opacity-60" style={{ animation: "fadeInUp 0.7s 0.9s cubic-bezier(0.16, 1, 0.3, 1) both" }}>
            <div className="flex items-center gap-2 text-xs text-muted font-mono">
              <svg className="w-4 h-4 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" /></svg>
              {t.publicTrack}
            </div>
            <div className="w-px h-4 bg-border/50" />
            <div className="flex items-center gap-2 text-xs text-muted font-mono">
              <svg className="w-4 h-4 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
              {t.algoTrading}
            </div>
            <div className="w-px h-4 bg-border/50" />
            <div className="flex items-center gap-2 text-xs text-muted font-mono">
              <svg className="w-4 h-4 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" /></svg>
              {t.openSource}
            </div>
          </div>
        </div>

        {/* Scroll hint */}
        <div className="absolute bottom-8 left-1/2 -translate-x-1/2 animate-bounce opacity-40" aria-hidden="true">
          <svg className="w-6 h-6 text-muted" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="m19 9-7 7-7-7" />
          </svg>
        </div>
      </section>

      {/* ─── LIVE TICKER ─── */}
      <LiveTicker />

      {/* ─── METRICS ─── */}
      <section ref={metricsSection.ref} className="py-24 px-4">
        <div className="max-w-5xl mx-auto">
          <SectionHeading
            tag={t.metricsTag}
            title={t.metricsTitle}
            subtitle={t.metricsSubtitle}
            visible={metricsSection.visible}
          />
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 md:gap-6">
            {metrics.map((m, i) => (
              <MetricCard key={m.label} {...m} active={metricsSection.visible} delay={i + 1} />
            ))}
          </div>
          <p
            className={`reveal reveal-delay-5 ${metricsSection.visible ? "visible" : ""} text-center text-muted text-sm mt-8`}
          >
            {t.metricsFooter} &bull; {t.updatedMonthly} &bull;{" "}
            <a
              href={SHEETS_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="text-primary hover:underline underline-offset-4"
            >
              {t.viewFullResults}
            </a>
          </p>
        </div>
      </section>

      {/* ─── HOW IT WORKS ─── */}
      <section ref={howItWorks.ref} className="py-24 px-4 bg-card/20">
        <div className="max-w-5xl mx-auto">
          <SectionHeading
            tag={t.howTag}
            title={t.howTitle}
            subtitle={t.howSubtitle}
            visible={howItWorks.visible}
          />
          <div className="grid md:grid-cols-3 gap-8 relative">
            {steps.map((step, i) => (
              <div
                key={step.num}
                className={`reveal reveal-delay-${i + 1} ${howItWorks.visible ? "visible" : ""} relative p-8 rounded-2xl border border-border/50 bg-background/50 backdrop-blur-sm hover:border-primary/30 transition-all group`}
              >
                <span className="absolute top-4 right-4 font-mono text-6xl font-bold text-primary/8 group-hover:text-primary/15 transition-colors select-none">
                  {step.num}
                </span>
                <div className="w-14 h-14 flex items-center justify-center rounded-xl bg-primary/10 text-primary mb-6 group-hover:bg-primary/15 transition-colors">
                  {step.icon}
                </div>
                <h3 className="text-xl font-semibold mb-3">{step.title}</h3>
                <p className="text-muted leading-relaxed text-sm">{step.desc}</p>

                {/* Connector line (desktop only, between cards) */}
                {i < steps.length - 1 && (
                  <div
                    className="hidden md:block absolute top-[44px] left-[calc(100%-12px)] w-8 h-px opacity-30"
                    style={{ background: "linear-gradient(90deg, #00D4AA, transparent)" }}
                    aria-hidden="true"
                  />
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── SIGNAL PREVIEW ─── */}
      <section ref={signalSection.ref} className="py-24 px-4">
        <div className="max-w-5xl mx-auto">
          <SectionHeading
            tag={t.previewTag}
            title={t.previewTitle}
            subtitle={t.previewSubtitle}
            visible={signalSection.visible}
          />
          <div
            className={`reveal reveal-delay-3 ${signalSection.visible ? "visible" : ""}`}
          >
            <SignalPreview visible={signalSection.visible} />
          </div>
        </div>
      </section>

      {/* ─── FEATURES ─── */}
      <section ref={featuresSection.ref} className="py-24 px-4 bg-card/20">
        <div className="max-w-5xl mx-auto">
          <SectionHeading
            tag={t.featTag}
            title={t.featTitle}
            subtitle={t.featSubtitle}
            visible={featuresSection.visible}
          />
          <div className="grid md:grid-cols-3 gap-6">
            {features.map((f, i) => (
              <div
                key={f.title}
                className={`reveal reveal-delay-${i + 1} ${featuresSection.visible ? "visible" : ""} feature-card group p-6 rounded-xl border border-border/50 bg-background/50`}
              >
                {f.icon}
                <h3 className="text-lg font-semibold mb-2">{f.title}</h3>
                <p className="text-muted text-sm leading-relaxed">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── PRICING ─── */}
      <section ref={pricingSection.ref} className="py-24 px-4">
        <div className="max-w-5xl mx-auto">
          <SectionHeading
            tag={t.priceTag}
            title={t.priceTitle}
            subtitle={t.priceSubtitle}
            visible={pricingSection.visible}
          />
          <div className="grid md:grid-cols-3 gap-6 max-w-4xl mx-auto items-start">
            {pricing.map((plan, i) => {
              const isVip = plan.highlight;
              const cardContent = (
                <div
                  className={`${isVip ? "vip-card-inner" : ""} ${
                    isVip ? "animate-pulse-glow-gold" : ""
                  } reveal reveal-delay-${i + 1} ${pricingSection.visible ? "visible" : ""} relative p-8 rounded-2xl transition-all h-full ${
                    isVip
                      ? "bg-[#0f1a0f]"
                      : "glass hover:border-primary/20"
                  }`}
                >
                  {isVip && (
                    <div className="absolute -top-3 left-1/2 -translate-x-1/2 z-10">
                      <span className="px-4 py-1 bg-accent text-background text-xs font-bold rounded-full uppercase tracking-wider">
                        {t.mostPopular}
                      </span>
                    </div>
                  )}
                  <div className="mb-6">
                    <h3
                      className={`text-lg font-semibold mb-2 ${isVip ? "gold-gradient-text" : "text-foreground"}`}
                    >
                      {plan.name}
                    </h3>
                    <div className="flex items-baseline gap-1">
                      <span className={`font-mono text-4xl font-bold ${isVip ? "gold-gradient-text" : ""}`}>
                        {plan.price}
                      </span>
                      <span className="text-muted text-sm">{plan.period}</span>
                    </div>
                  </div>
                  <ul className="space-y-3 mb-8">
                    {plan.features.map((feat) => (
                      <li key={feat} className="flex items-start gap-3 text-sm">
                        <svg
                          className={`w-5 h-5 shrink-0 mt-0.5 ${isVip ? "text-accent" : "text-primary"}`}
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
                    className={`btn-press block w-full text-center py-3.5 rounded-xl font-semibold transition-all ${
                      isVip
                        ? "bg-accent text-background hover:brightness-110"
                        : "border border-border text-foreground hover:bg-card/50 hover:border-primary/30"
                    }`}
                  >
                    {plan.cta}
                  </a>
                </div>
              );

              return isVip ? (
                <div key={plan.name} className="vip-card-wrapper">
                  {cardContent}
                </div>
              ) : (
                <div key={plan.name} className="h-full">
                  {cardContent}
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* ─── FAQ ─── */}
      <section ref={faqSection.ref} className="py-24 px-4 bg-card/20">
        <div className="max-w-3xl mx-auto">
          <SectionHeading
            tag={t.faqTag}
            title={t.faqTitle}
            visible={faqSection.visible}
          />
          <div
            className={`reveal reveal-delay-2 ${faqSection.visible ? "visible" : ""} space-y-3`}
          >
            {faqItems.map((item) => (
              <FAQItem key={item.q} {...item} />
            ))}
          </div>
        </div>
      </section>

      {/* ─── CTA BANNER ─── */}
      <section ref={ctaSection.ref} className="py-28 px-4">
        <div
          className={`reveal ${ctaSection.visible ? "visible" : ""} cta-glow max-w-3xl mx-auto text-center p-12 rounded-3xl border border-primary/10 bg-primary/3`}
        >
          <div className="mb-2">
            <span className="inline-block px-4 py-1.5 text-xs font-mono uppercase tracking-widest text-primary border border-primary/30 rounded-full">
              {t.ctaTag}
            </span>
          </div>
          <h2
            className={`reveal reveal-delay-1 ${ctaSection.visible ? "visible" : ""} text-3xl md:text-5xl font-bold mt-6 mb-4 tracking-tight`}
          >
            {t.ctaTitle}{" "}
            <span className="gradient-text">{t.ctaTitleHighlight}</span>?
          </h2>
          <p
            className={`reveal reveal-delay-2 ${ctaSection.visible ? "visible" : ""} text-muted mb-10 text-lg leading-relaxed`}
          >
            {t.ctaDesc}
            <br />
            <span className="text-foreground/60 text-base">{t.ctaSubDesc}</span>
          </p>
          <div
            className={`reveal reveal-delay-3 ${ctaSection.visible ? "visible" : ""} flex flex-col sm:flex-row items-center justify-center gap-4`}
          >
            <a
              href={TELEGRAM_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="btn-primary btn-press inline-flex items-center gap-3 px-10 py-4 rounded-xl font-semibold text-lg animate-pulse-glow"
            >
              <svg className="w-6 h-6" viewBox="0 0 24 24" fill="currentColor">
                <path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z" />
              </svg>
              {t.getStarted}
            </a>
            <a
              href={SHEETS_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="btn-press flex items-center gap-2 px-6 py-4 text-muted hover:text-foreground transition-colors text-sm font-medium"
            >
              {t.viewAllResults}
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5 21 12m0 0-7.5 7.5M21 12H3" />
              </svg>
            </a>
          </div>
        </div>
      </section>

      {/* ─── FOOTER ─── */}
      <footer className="border-t border-border/40 py-12 px-4">
        <div className="max-w-5xl mx-auto">
          <div className="flex flex-col md:flex-row items-center justify-between gap-6 mb-8">
            <div>
              <span className="text-xl font-bold gradient-text">TrendRider</span>
              <p className="text-muted text-sm mt-1">{t.footerTagline}</p>
            </div>
            <div className="flex items-center gap-6">
              <a
                href={TELEGRAM_URL}
                target="_blank"
                rel="noopener noreferrer"
                className="text-muted hover:text-primary transition-colors text-sm relative after:absolute after:bottom-0 after:left-0 after:w-0 after:h-px after:bg-primary after:transition-all hover:after:w-full"
              >
                {t.telegramChannel}
              </a>
              <a
                href={SHEETS_URL}
                target="_blank"
                rel="noopener noreferrer"
                className="text-muted hover:text-primary transition-colors text-sm relative after:absolute after:bottom-0 after:left-0 after:w-0 after:h-px after:bg-primary after:transition-all hover:after:w-full"
              >
                {t.liveResults}
              </a>
            </div>
          </div>

          <div className="flex flex-col md:flex-row items-center justify-between gap-4 pt-8 border-t border-border/30">
            <p className="text-muted text-xs leading-relaxed max-w-2xl text-center md:text-left">
              <span className="font-semibold text-danger/80">Risk Disclaimer:</span> {t.riskDisclaimer}
            </p>
            <div className="flex items-center gap-4 shrink-0">
              <span className="text-muted/50 text-xs font-mono">{t.poweredBy}</span>
              <span className="text-muted/30">|</span>
              <span className="text-muted/50 text-xs">&copy; 2026 TrendRider</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
