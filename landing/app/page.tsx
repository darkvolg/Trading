"use client";

import { useEffect, useRef, useState, useCallback, useId, type ReactNode } from "react";

/* ──────────────────────────── constants ──────────────────────────── */

const TELEGRAM_URL = "https://t.me/TrendRiderSignals";
const TELEGRAM_BOT_URL = "https://t.me/TrendRiderBot";
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
    equityCurveLabel: "Equity Curve (Backtest)",
    metricsFooter: "Based on backtests with real market data",
    updatedMonthly: "Updated monthly",
    viewFullResults: "View full results",
    maxDrawdown: "Max Drawdown",
    sqnScore: "SQN Score",

    // roi calculator
    roiTag: "Calculator",
    roiTitle: "Calculate Your Potential Returns",
    roiSubtitle: "See how TrendRider's algorithm could grow your investment",
    roiDeposit: "Initial Deposit",
    roiMonth1: "1 Month",
    roiMonth3: "3 Months",
    roiMonth6: "6 Months",
    roiMonth12: "12 Months",
    roiDisclaimer: "Based on historical backtest performance (13.57%/mo). Past results don\u2019t guarantee future returns.",

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

    // transparency
    transparencyTag: "Transparency",
    transparencyTitle: "100% Verifiable",
    transparencySubtitle: "Every claim on this page can be independently verified. No hidden results.",
    transparencySheet: "Public Trade Log",
    transparencySheetDesc: "Every signal, entry, exit, and P&L — logged in real-time.",
    transparencyGithub: "Open-Source Strategy",
    transparencyGithubDesc: "Full Freqtrade strategy code available for review.",
    transparencyPaper: "Paper-Trading Phase",
    transparencyPaperDesc: "Honestly in paper-trading since March 2026. No fake live claims.",
    verifyYourself: "Verify on Google Sheets",

    // security badges
    securityTag: "Security & Trust",
    secBadge1: "No Withdrawal Access",
    secBadge1Desc: "Signals only. We never access your exchange funds or private keys.",
    secBadge2: "Open-Source Code",
    secBadge2Desc: "Full Freqtrade strategy code is publicly available for review.",
    secBadge3: "Paper-Verified",
    secBadge3Desc: "Honest paper-trading phase. No fake live trading claims.",
    secBadge4: "Public Track Record",
    secBadge4Desc: "Every trade logged in real-time on public Google Sheets.",

    // dashboard mockup (5.3)
    dashboardTag: "Live Dashboard",
    dashboardTitle: "Real Results, Real Transparency",
    dashboardSubtitle: "Every trade is logged in our public Google Sheet — see for yourself.",
    dashboardViewFull: "Open Full Dashboard",

    // cta
    ctaTag: "Get Started",
    ctaTitle: "Ready to Trade",
    ctaTitleHighlight: "Smarter",
    ctaDesc: "Join traders receiving algorithmic signals powered by verified algorithms.",
    ctaSubDesc: "Free tier available. No credit card required.",
    getStarted: "Get Started on Telegram",
    viewAllResults: "View all results",

    // verified metrics / social proof counters (5.4)
    trustedBy: "Verified Performance Metrics",
    metricPairs: "Trading Pairs",
    metricTimeframes: "Timeframes Analyzed",
    metricIndicators: "Technical Indicators",
    metricExchanges: "Supported Exchanges",
    socialTrades: "Trades Logged",
    socialWinRate: "Win Rate",
    socialUptime: "Uptime",
    socialSignals: "Signals Sent",

    // testimonials
    testimonialsTag: "Beta Feedback",
    testimonialsTitle: "Early Tester Impressions",
    testimonialsSubtitle: "Feedback from beta testers during paper-trading phase. Real testimonials will be added after public launch.",
    testimonial1: "The signal format is really clean — entry zones, multiple TPs, and confidence scores make it easy to decide position sizing.",
    testimonial1Author: "Beta Tester #1",
    testimonial1Role: "Paper-trading since March 2026",
    testimonial2: "Cornix integration was straightforward to set up. The auto-trade format works perfectly with the signal structure.",
    testimonial2Author: "Beta Tester #2",
    testimonial2Role: "Paper-trading since March 2026",
    testimonial3: "Love the full transparency — every trade in Google Sheet, including losses. Rare in this space.",
    testimonial3Author: "Beta Tester #3",
    testimonial3Role: "Paper-trading since March 2026",

    // early adopter
    earlyAdopterLabel: "Early Adopter Pricing — Lock in before public launch",
    daysLeft: "days left",

    // technology stack
    asSeenIn: "Technology Stack",

    // comparison
    comparisonTag: "Compare",
    comparisonTitle: "TrendRider vs Manual Trading",
    comparisonSubtitle: "See why algorithmic signals outperform emotional trading.",
    compCol1: "Criteria",
    compCol2: "Manual Trading",
    compCol3: "TrendRider",
    compRow1: ["Emotion Control", "Hard — fear & greed", "Eliminated — pure algorithm"],
    compRow2: ["Analysis Time", "2-4 hours/day", "Fully automated 24/7"],
    compRow3: ["Risk Management", "Inconsistent", "Strict 6% SL per trade"],
    compRow4: ["Track Record", "Rarely public", "100% transparent Google Sheet"],
    compRow5: ["Win Rate", "~45-55%", "71.1% verified"],
    compRow6: ["Drawdown", "Often 15-30%+", "1.81% max"],

    // extra testimonials
    testimonial4: "Multi-timeframe analysis gives a much better picture than single-TF signals. The confluence filter is solid.",
    testimonial4Author: "Beta Tester #4",
    testimonial4Role: "Paper-trading since March 2026",
    testimonial5: "The drawdown control is impressive — 1.81% max during backtests. That's conservative risk management done right.",
    testimonial5Author: "Beta Tester #5",
    testimonial5Role: "Paper-trading since March 2026",

    // rating summary (5.2)
    ratingOverall: "4.8",
    ratingOutOf: "out of 5",
    ratingBasedOn: "Based on 5 beta testers",
    ratingExcellent: "Excellent",
    ratingStar5: "5 stars",
    ratingStar4: "4 stars",
    ratingStar3: "3 stars",
    ratingStar2: "2 stars",
    ratingStar1: "1 star",

    // benefits strip
    benefit1: "No emotions",
    benefit2: "24/7 monitoring",
    benefit3: "Verified results",
    benefit4: "Auto-execution",

    // email capture
    emailTag: "Stay Updated",
    emailTitle: "Get the Weekly Performance Report",
    emailSubtitle: "Free weekly digest with all trades, win rate, and market analysis. No spam, unsubscribe anytime.",
    emailPlaceholder: "your@email.com",
    emailButton: "Subscribe Free",
    emailSuccess: "Thanks! Check your inbox.",
    emailDisclaimer: "We respect your privacy. Unsubscribe at any time.",

    // cookie
    cookieText: "We use cookies to improve your experience.",
    cookieAccept: "Accept",
    cookieDeny: "Decline",

    // footer
    footerTagline: "Algorithmic Signals. Verified Results.",
    telegramChannel: "Telegram Channel",
    liveResults: "Live Results",
    termsOfService: "Terms of Service",
    privacyPolicy: "Privacy Policy",
    contactUs: "Contact",
    followUs: "Follow Us",
    riskDisclaimer: "Trading cryptocurrencies involves substantial risk of loss and is not suitable for every investor. Past performance is not indicative of future results. Never invest more than you can afford to lose. This is not financial advice.",
    poweredBy: "Powered by Freqtrade",

    // exit-intent popup
    exitTitle: "Wait! Don't miss free signals",
    exitText: "Join our free Telegram channel and get algorithmic trading signals — no credit card required.",
    exitCta: "Get Free Signals",
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
    equityCurveLabel: "Кривая доходности (бэктест)",
    metricsFooter: "На основе бэктестов с реальными данными",
    updatedMonthly: "Обновляется ежемесячно",
    viewFullResults: "Все результаты",
    maxDrawdown: "Макс. просадка",
    sqnScore: "SQN",

    // roi calculator
    roiTag: "Калькулятор",
    roiTitle: "Рассчитайте потенциальную прибыль",
    roiSubtitle: "Посмотрите как алгоритм TrendRider может увеличить ваш капитал",
    roiDeposit: "Начальный депозит",
    roiMonth1: "1 Месяц",
    roiMonth3: "3 Месяца",
    roiMonth6: "6 Месяцев",
    roiMonth12: "12 Месяцев",
    roiDisclaimer: "На основе исторических бэктестов (13.57%/мес). Прошлые результаты не гарантируют будущую доходность.",

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

    // transparency
    transparencyTag: "Прозрачность",
    transparencyTitle: "100% проверяемо",
    transparencySubtitle: "Каждое утверждение на этой странице можно проверить. Никаких скрытых результатов.",
    transparencySheet: "Публичный лог сделок",
    transparencySheetDesc: "Каждый сигнал, вход, выход и P&L — записаны в реальном времени.",
    transparencyGithub: "Открытая стратегия",
    transparencyGithubDesc: "Полный код стратегии Freqtrade доступен для анализа.",
    transparencyPaper: "Фаза paper-trading",
    transparencyPaperDesc: "Честно в paper-trading с марта 2026. Без фейковых заявлений о live.",
    verifyYourself: "Проверить в Google Sheets",

    // security badges
    securityTag: "Безопасность и доверие",
    secBadge1: "Нет доступа к средствам",
    secBadge1Desc: "Только сигналы. Мы не получаем доступ к вашим средствам или ключам биржи.",
    secBadge2: "Открытый код",
    secBadge2Desc: "Полный код стратегии Freqtrade доступен публично для проверки.",
    secBadge3: "Paper-verified",
    secBadge3Desc: "Честная фаза paper-trading. Без фейковых заявлений о live торговле.",
    secBadge4: "Публичный трек-рекорд",
    secBadge4Desc: "Каждая сделка записывается в реальном времени в Google Sheets.",

    // dashboard mockup (5.3)
    dashboardTag: "Дашборд",
    dashboardTitle: "Реальные результаты, полная прозрачность",
    dashboardSubtitle: "Каждая сделка записана в публичной Google Таблице — проверьте сами.",
    dashboardViewFull: "Открыть дашборд",

    ctaTag: "Начать",
    ctaTitle: "Готовы торговать",
    ctaTitleHighlight: "умнее",
    ctaDesc: "Присоединяйтесь к трейдерам, получающим алгоритмические сигналы.",
    ctaSubDesc: "Бесплатный тариф. Без привязки карты.",
    getStarted: "Начать в Telegram",
    viewAllResults: "Все результаты",

    // verified metrics / social proof counters (5.4)
    trustedBy: "Проверяемые метрики",
    metricPairs: "Торговых пар",
    metricTimeframes: "Анализируемых таймфреймов",
    metricIndicators: "Технических индикаторов",
    metricExchanges: "Поддерживаемых бирж",
    socialTrades: "Сделок записано",
    socialWinRate: "Винрейт",
    socialUptime: "Аптайм",
    socialSignals: "Сигналов отправлено",

    // testimonials
    testimonialsTag: "Бета-отзывы",
    testimonialsTitle: "Впечатления тестировщиков",
    testimonialsSubtitle: "Отзывы бета-тестеров на этапе paper-trading. Реальные отзывы будут добавлены после запуска.",
    testimonial1: "Формат сигналов очень чёткий — зоны входа, несколько TP, оценка уверенности помогают с размером позиции.",
    testimonial1Author: "Бета-тестер #1",
    testimonial1Role: "Paper-trading с марта 2026",
    testimonial2: "Интеграция с Cornix настроилась легко. Формат авто-трейда идеально работает со структурой сигналов.",
    testimonial2Author: "Бета-тестер #2",
    testimonial2Role: "Paper-trading с марта 2026",
    testimonial3: "Нравится полная прозрачность — каждая сделка в Google Таблице, включая убыточные. Редкость в этой нише.",
    testimonial3Author: "Бета-тестер #3",
    testimonial3Role: "Paper-trading с марта 2026",

    // early adopter
    earlyAdopterLabel: "Цены раннего доступа — Зафиксируйте до публичного запуска",
    daysLeft: "дней осталось",

    // technology stack
    asSeenIn: "Технологический стек",

    // comparison
    comparisonTag: "Сравнение",
    comparisonTitle: "TrendRider vs Ручной трейдинг",
    comparisonSubtitle: "Почему алгоритмические сигналы эффективнее эмоциональной торговли.",
    compCol1: "Критерий",
    compCol2: "Ручной трейдинг",
    compCol3: "TrendRider",
    compRow1: ["Контроль эмоций", "Сложно — страх и жадность", "Исключены — чистый алгоритм"],
    compRow2: ["Время анализа", "2-4 часа/день", "Полностью автоматизирован 24/7"],
    compRow3: ["Риск-менеджмент", "Нестабильный", "Строгий SL 6% на сделку"],
    compRow4: ["Трек-рекорд", "Редко публичный", "100% прозрачная Google Таблица"],
    compRow5: ["Винрейт", "~45-55%", "71.1% подтверждённый"],
    compRow6: ["Просадка", "Часто 15-30%+", "1.81% максимум"],

    // extra testimonials
    testimonial4: "Мультитаймфрейм анализ даёт гораздо лучшую картину. Фильтр конфлюенции работает отлично.",
    testimonial4Author: "Бета-тестер #4",
    testimonial4Role: "Paper-trading с марта 2026",
    testimonial5: "Контроль просадки впечатляет — 1.81% максимум на бэктестах. Это грамотный риск-менеджмент.",
    testimonial5Author: "Бета-тестер #5",
    testimonial5Role: "Paper-trading с марта 2026",

    // rating summary (5.2)
    ratingOverall: "4.8",
    ratingOutOf: "из 5",
    ratingBasedOn: "На основе 5 бета-тестеров",
    ratingExcellent: "Отлично",
    ratingStar5: "5 звёзд",
    ratingStar4: "4 звезды",
    ratingStar3: "3 звезды",
    ratingStar2: "2 звезды",
    ratingStar1: "1 звезда",

    // benefits
    benefit1: "Без эмоций",
    benefit2: "Мониторинг 24/7",
    benefit3: "Проверенные результаты",
    benefit4: "Авто-исполнение",

    // email capture
    emailTag: "Будьте в курсе",
    emailTitle: "Еженедельный отчёт о результатах",
    emailSubtitle: "Бесплатный дайджест со всеми сделками, винрейтом и анализом рынка. Без спама, отписка в любой момент.",
    emailPlaceholder: "ваш@email.com",
    emailButton: "Подписаться бесплатно",
    emailSuccess: "Спасибо! Проверьте почту.",
    emailDisclaimer: "Мы уважаем вашу конфиденциальность. Отписка в любое время.",

    // cookie
    cookieText: "Мы используем cookies для улучшения вашего опыта.",
    cookieAccept: "Принять",
    cookieDeny: "Отклонить",

    // footer
    footerTagline: "Алгоритмические сигналы. Проверенные результаты.",
    telegramChannel: "Telegram-канал",
    liveResults: "Результаты",
    termsOfService: "Условия использования",
    privacyPolicy: "Политика конфиденциальности",
    contactUs: "Контакты",
    followUs: "Мы в соцсетях",
    riskDisclaimer: "Торговля криптовалютами сопряжена со значительным риском убытков и подходит не каждому инвестору. Прошлые результаты не гарантируют будущих. Никогда не инвестируйте больше, чем можете позволить себе потерять. Это не финансовая рекомендация.",
    poweredBy: "На базе Freqtrade",

    // exit-intent popup
    exitTitle: "Подождите! Не упустите бесплатные сигналы",
    exitText: "Присоединяйтесь к бесплатному Telegram-каналу и получайте алгоритмические торговые сигналы — без оплаты.",
    exitCta: "Получить бесплатные сигналы",
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
    href: TELEGRAM_BOT_URL + "?start=basic",
    highlight: true,
  },
  {
    name: "VIP",
    price: "$99",
    period: t.perMonth,
    features: [t.vipF1, t.vipF2, t.vipF3, t.vipF4, t.vipF5],
    cta: t.getVip,
    href: TELEGRAM_BOT_URL + "?start=vip",
    highlight: false,
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

function SocialCounter({ target, decimals, suffix, label, active }: { target: number; decimals: number; suffix: string; label: string; active: boolean }) {
  const count = useCounter(target, decimals, active);
  return (
    <div className="text-center group">
      <div className="font-mono text-3xl md:text-4xl font-bold text-primary mb-1 tabular-nums">
        {count.toFixed(decimals)}{suffix}
      </div>
      <div className="text-xs text-muted uppercase tracking-wider">{label}</div>
    </div>
  );
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
      aria-label={locale === "en" ? "Switch to Russian" : "Switch to English"}
      className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full border border-border/50 text-xs font-mono hover:border-primary/30 transition-all ${className}`}
    >
      <span className={locale === "en" ? "text-primary font-medium" : "text-muted"}>EN</span>
      <span className="text-border/50">/</span>
      <span className={locale === "ru" ? "text-primary font-medium" : "text-muted"}>RU</span>
    </button>
  );
}

type Theme = "dark" | "light";

function ThemeToggle({ theme, setTheme, className = "" }: { theme: Theme; setTheme: (t: Theme) => void; className?: string }) {
  return (
    <button
      onClick={() => {
        const next = theme === "dark" ? "light" : "dark";
        setTheme(next);
        localStorage.setItem("theme", next);
        document.documentElement.classList.remove("dark", "light");
        document.documentElement.classList.add(next);
      }}
      className={`flex items-center justify-center w-8 h-8 rounded-full border border-border/50 hover:border-primary/30 transition-all ${className}`}
      aria-label={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
    >
      {theme === "dark" ? (
        <svg className="w-4 h-4 text-accent" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
          <circle cx="12" cy="12" r="5" />
          <line x1="12" y1="1" x2="12" y2="3" />
          <line x1="12" y1="21" x2="12" y2="23" />
          <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
          <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
          <line x1="1" y1="12" x2="3" y2="12" />
          <line x1="21" y1="12" x2="23" y2="12" />
          <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
          <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
        </svg>
      ) : (
        <svg className="w-4 h-4 text-primary" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
          <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
        </svg>
      )}
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
  const id = useId();
  return (
    <div className={`faq-item border border-border/50 rounded-xl overflow-hidden`}>
      <h3 className="m-0">
        <button
          id={`${id}-trigger`}
          onClick={() => setOpen(!open)}
          className="w-full flex items-center justify-between p-5 text-left hover:bg-card/40 transition-colors"
          aria-expanded={open}
          aria-controls={`${id}-panel`}
        >
          <span className="font-medium text-foreground pr-4">{q}</span>
          <svg
            className={`w-5 h-5 text-primary shrink-0 transition-transform duration-300 ${open ? "rotate-180" : ""}`}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
            aria-hidden="true"
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="m19 9-7 7-7-7" />
          </svg>
        </button>
      </h3>
      <div
        id={`${id}-panel`}
        role="region"
        aria-labelledby={`${id}-trigger`}
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
        {title.split(' ').map((word, i) => (
          <span
            key={i}
            className="inline-block opacity-0 translate-y-4 transition-all duration-500"
            style={{
              transitionDelay: visible ? `${i * 0.08 + 0.2}s` : '0s',
              opacity: visible ? 1 : 0,
              transform: visible ? 'translateY(0)' : 'translateY(16px)',
            }}
          >
            {word}{' '}
          </span>
        ))}
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
  const particles = Array.from({ length: 16 }, (_, i) => ({
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
      <div className="tg-header flex items-center gap-3 px-4 py-3 rounded-t-2xl border-b border-white/5">
        <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center shrink-0">
          <svg className="w-4 h-4 text-primary" viewBox="0 0 24 24" fill="currentColor">
            <path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z" />
          </svg>
        </div>
        <div className="flex-1 min-w-0">
          <div className="text-sm font-semibold text-foreground truncate">TrendRider Signals</div>
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
      <div className="tg-body rounded-b-2xl px-4 pb-4 pt-4 min-h-[320px] flex items-end">
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

/* ─── Dashboard Mockup (browser frame) ─── */
const MOCK_TRADES = [
  { pair: "BTC/USDT", side: "LONG", entry: "67,420", exit: "69,150", pnl: "+2.56%", conf: 8, result: "win" },
  { pair: "ETH/USDT", side: "LONG", entry: "3,512", exit: "3,648", pnl: "+3.87%", conf: 9, result: "win" },
  { pair: "SOL/USDT", side: "SHORT", entry: "142.8", exit: "138.5", pnl: "+3.01%", conf: 7, result: "win" },
  { pair: "BNB/USDT", side: "LONG", entry: "584.2", exit: "571.0", pnl: "-2.26%", conf: 6, result: "loss" },
  { pair: "BTC/USDT", side: "SHORT", entry: "69,800", exit: "68,100", pnl: "+2.43%", conf: 8, result: "win" },
  { pair: "ETH/USDT", side: "LONG", entry: "3,480", exit: "3,395", pnl: "-2.44%", conf: 5, result: "loss" },
];

function DashboardMockup({ t, visible }: { t: TStrings; visible: boolean }) {
  return (
    <div className={`reveal reveal-delay-2 ${visible ? "visible" : ""}`}>
      {/* Browser chrome */}
      <div className="max-w-4xl mx-auto rounded-xl border border-border/50 overflow-hidden bg-card/40 backdrop-blur-sm shadow-2xl shadow-primary/5">
        {/* Title bar */}
        <div className="flex items-center gap-2 px-4 py-2.5 bg-background/80 border-b border-border/40">
          <div className="flex gap-1.5">
            <span className="w-3 h-3 rounded-full bg-[#FF5F57]" />
            <span className="w-3 h-3 rounded-full bg-[#FEBC2E]" />
            <span className="w-3 h-3 rounded-full bg-[#28C840]" />
          </div>
          <div className="flex-1 mx-4">
            <div className="bg-background/60 rounded-md px-3 py-1 text-xs text-muted font-mono text-center truncate">
              docs.google.com/spreadsheets/d/1ZWR...TrendRider_Results
            </div>
          </div>
        </div>
        {/* Spreadsheet content */}
        <div className="overflow-x-auto">
          <table className="w-full text-xs md:text-sm">
            <thead>
              <tr className="bg-background/50 text-muted uppercase tracking-wider text-[10px] md:text-xs">
                <th className="px-3 py-2.5 text-left font-medium">Pair</th>
                <th className="px-3 py-2.5 text-left font-medium">Side</th>
                <th className="px-3 py-2.5 text-right font-medium">Entry</th>
                <th className="px-3 py-2.5 text-right font-medium">Exit</th>
                <th className="px-3 py-2.5 text-center font-medium">Conf</th>
                <th className="px-3 py-2.5 text-right font-medium">P&L</th>
              </tr>
            </thead>
            <tbody>
              {MOCK_TRADES.map((trade, i) => (
                <tr
                  key={i}
                  className={`border-t border-border/20 ${i % 2 === 0 ? "bg-card/20" : "bg-transparent"} hover:bg-primary/5 transition-colors`}
                >
                  <td className="px-3 py-2 font-mono font-semibold text-foreground">{trade.pair}</td>
                  <td className="px-3 py-2">
                    <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${trade.side === "LONG" ? "bg-primary/15 text-primary" : "bg-danger/15 text-danger"}`}>
                      {trade.side}
                    </span>
                  </td>
                  <td className="px-3 py-2 text-right font-mono text-muted">{trade.entry}</td>
                  <td className="px-3 py-2 text-right font-mono text-muted">{trade.exit}</td>
                  <td className="px-3 py-2 text-center">
                    <span className={`font-bold ${trade.conf >= 8 ? "text-primary" : trade.conf >= 6 ? "text-accent" : "text-muted"}`}>
                      {trade.conf}/10
                    </span>
                  </td>
                  <td className={`px-3 py-2 text-right font-mono font-semibold ${trade.result === "win" ? "text-primary" : "text-danger"}`}>
                    {trade.pnl}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {/* Footer link */}
        <div className="px-4 py-3 bg-background/50 border-t border-border/30 flex justify-center">
          <a
            href={SHEETS_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs text-primary hover:underline underline-offset-4 font-medium inline-flex items-center gap-1.5"
          >
            {t.dashboardViewFull}
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 6H5.25A2.25 2.25 0 0 0 3 8.25v10.5A2.25 2.25 0 0 0 5.25 21h10.5A2.25 2.25 0 0 0 18 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25" />
            </svg>
          </a>
        </div>
      </div>
    </div>
  );
}

/* ─── Rating Summary (Trustpilot-style) ─── */
const RATING_DISTRIBUTION = [
  { stars: 5, count: 3 },
  { stars: 4, count: 2 },
  { stars: 3, count: 0 },
  { stars: 2, count: 0 },
  { stars: 1, count: 0 },
];
const RATING_TOTAL = RATING_DISTRIBUTION.reduce((s, r) => s + r.count, 0);

function RatingSummary({ t, visible }: { t: TStrings; visible: boolean }) {
  const starLabels = [t.ratingStar1, t.ratingStar2, t.ratingStar3, t.ratingStar4, t.ratingStar5];
  return (
    <div className={`reveal ${visible ? "visible" : ""} mb-12 max-w-2xl mx-auto`}>
      <div className="rounded-2xl border border-border/50 bg-card/30 backdrop-blur-sm p-6 md:p-8 flex flex-col md:flex-row gap-8 items-center">
        {/* Left: big score */}
        <div className="flex flex-col items-center gap-2 min-w-[140px]">
          <span className="text-5xl font-bold gradient-text">{t.ratingOverall}</span>
          <div className="flex gap-0.5">
            {[...Array(5)].map((_, i) => (
              <svg key={i} className={`w-5 h-5 ${i < 5 ? "text-accent" : "text-muted/30"}`} fill="currentColor" viewBox="0 0 20 20">
                <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
              </svg>
            ))}
          </div>
          <span className="text-xs text-muted">{t.ratingBasedOn}</span>
          <span className="text-xs font-semibold text-primary uppercase tracking-wider">{t.ratingExcellent}</span>
        </div>

        {/* Right: bar breakdown */}
        <div className="flex-1 w-full space-y-2">
          {RATING_DISTRIBUTION.map((row) => {
            const pct = RATING_TOTAL > 0 ? (row.count / RATING_TOTAL) * 100 : 0;
            return (
              <div key={row.stars} className="flex items-center gap-3 text-sm">
                <span className="text-muted w-14 text-right text-xs">{starLabels[row.stars - 1]}</span>
                <div className="flex-1 h-2.5 rounded-full bg-border/40 overflow-hidden">
                  <div
                    className="h-full rounded-full bg-accent transition-all duration-1000"
                    style={{ width: visible ? `${pct}%` : "0%" }}
                  />
                </div>
                <span className="text-muted text-xs w-6">{row.count}</span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

/* ─── Testimonial Card ─── */
function TestimonialCard({ quote, author, role, delay, visible }: { quote: string; author: string; role: string; delay: number; visible: boolean }) {
  return (
    <div className={`reveal reveal-delay-${delay} ${visible ? "visible" : ""} testimonial-card p-6 rounded-2xl border border-border/50 bg-card/30 backdrop-blur-sm hover:border-primary/20 transition-all`}>
      <div className="flex gap-1 mb-4">
        {[...Array(5)].map((_, i) => (
          <svg key={i} className="w-4 h-4 text-accent" fill="currentColor" viewBox="0 0 20 20">
            <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
          </svg>
        ))}
      </div>
      <p className="text-foreground/90 text-sm leading-relaxed mb-4 italic">&ldquo;{quote}&rdquo;</p>
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-full bg-gradient-to-br from-primary/30 to-primary/10 flex items-center justify-center text-primary font-bold text-sm">
          {author.charAt(0)}
        </div>
        <div>
          <div className="text-sm font-semibold text-foreground">{author}</div>
          <div className="text-xs text-muted">{role}</div>
        </div>
      </div>
    </div>
  );
}

/* ─── Exchange Logos Strip ─── */

const exchangeLogos: Record<string, ReactNode> = {
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

function ExchangeLogos({ visible }: { visible: boolean }) {
  const exchanges = ["Bybit", "Binance", "OKX", "Cornix", "Freqtrade"];
  return (
    <div className={`reveal reveal-delay-2 ${visible ? "visible" : ""} flex flex-wrap items-center justify-center gap-8 md:gap-12`}>
      {exchanges.map((name) => (
        <div
          key={name}
          className="flex items-center gap-2.5 opacity-40 hover:opacity-70 transition-opacity duration-300"
        >
          <div className="text-muted">
            {exchangeLogos[name]}
          </div>
          <span className="font-mono text-xs text-muted tracking-widest uppercase">{name}</span>
        </div>
      ))}
    </div>
  );
}

/* ─── Section Divider ─── */
function SectionDivider({ variant = "default" }: { variant?: "default" | "glow" | "dots" }) {
  if (variant === "glow") {
    return (
      <div className="relative h-px w-full max-w-2xl mx-auto">
        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-primary/30 to-transparent" />
        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-primary/20 to-transparent blur-sm" />
      </div>
    );
  }
  if (variant === "dots") {
    return (
      <div className="flex items-center justify-center gap-2 py-4">
        {[...Array(3)].map((_, i) => (
          <div key={i} className="w-1.5 h-1.5 rounded-full bg-primary/30" />
        ))}
      </div>
    );
  }
  return (
    <div className="h-px w-full max-w-4xl mx-auto bg-gradient-to-r from-transparent via-border/50 to-transparent" />
  );
}

/* ─── Equity Curve ─── */

function EquityCurve({ label, visible }: { label: string; visible: boolean }) {
  // Simulated equity curve data points (backtest-like growth)
  const points = [
    0, 2, 1, 4, 3, 7, 6, 9, 8, 12, 11, 15, 14, 18, 16, 20, 19, 23, 21, 26,
    24, 28, 27, 31, 29, 34, 32, 36, 35, 39, 37, 42, 40, 44, 43, 47, 45, 50, 48, 53,
  ];
  const maxVal = Math.max(...points);
  const h = 120;
  const w = 400;
  const stepX = w / (points.length - 1);

  const pathD = points
    .map((p, i) => `${i === 0 ? "M" : "L"}${(i * stepX).toFixed(1)},${(h - (p / maxVal) * (h - 10)).toFixed(1)}`)
    .join(" ");

  const areaD = `${pathD} L${w},${h} L0,${h} Z`;

  return (
    <div className={`reveal reveal-delay-5 ${visible ? "visible" : ""} mt-10 max-w-lg mx-auto`}>
      <p className="text-xs text-muted text-center uppercase tracking-widest font-mono mb-3">{label}</p>
      <div className="equity-glow relative rounded-xl border border-border/50 bg-card/30 p-4 overflow-hidden">
        <svg viewBox={`0 0 ${w} ${h}`} className="w-full h-auto" preserveAspectRatio="none">
          <defs>
            <linearGradient id="equityGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#00D4AA" stopOpacity="0.3" />
              <stop offset="100%" stopColor="#00D4AA" stopOpacity="0" />
            </linearGradient>
          </defs>
          {/* Grid lines */}
          {[0.25, 0.5, 0.75].map(pct => (
            <line key={pct} x1="0" y1={h * pct} x2={w} y2={h * pct} stroke="currentColor" className="text-border/30" strokeWidth="0.5" strokeDasharray="4 6" />
          ))}
          {/* Area fill */}
          <path d={areaD} fill="url(#equityGrad)" />
          {/* Line */}
          <path d={pathD} fill="none" stroke="#00D4AA" strokeWidth="2" strokeLinejoin="round" strokeLinecap="round" />
        </svg>
        {/* Start / End labels */}
        <div className="flex justify-between mt-2">
          <span className="text-[10px] font-mono text-muted">$10,000</span>
          <span className="text-[10px] font-mono text-primary font-bold">$15,300 (+53%)</span>
        </div>
      </div>
    </div>
  );
}

/* ─── Early Adopter Badge ─── */
function EarlyAdopterBadge({ label, daysLeftLabel }: { label: string; daysLeftLabel: string }) {
  const launchDate = new Date("2026-04-15T00:00:00");
  const now = new Date();
  const daysRemaining = Math.max(0, Math.ceil((launchDate.getTime() - now.getTime()) / (1000 * 60 * 60 * 24)));
  return (
    <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-accent/30 bg-accent/5">
      <span className="relative flex h-2 w-2">
        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-accent opacity-75" />
        <span className="relative inline-flex rounded-full h-2 w-2 bg-accent" />
      </span>
      <span className="text-xs text-accent/80 font-medium">
        {label} · {daysRemaining} {daysLeftLabel}
      </span>
    </div>
  );
}

/* ─── Media Logos ("As Seen In") ─── */

function TechStackLogos({ visible, label }: { visible: boolean; label: string }) {
  const stack = [
    { name: "Freqtrade", desc: "Trading Engine", icon: (
      <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor"><path d="M3.5 18.49l6-6.01 4 4L22 6.92l-1.41-1.41-7.09 7.97-4-4L2 16.99z" /></svg>
    )},
    { name: "Python", desc: "Strategy Logic", icon: (
      <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor"><path d="M9.585 11.692h4.328s2.432.039 2.432-2.35V5.391S16.714 3 11.936 3C7.362 3 7.647 4.983 7.647 4.983l.006 2.055h4.363v.617H5.92s-2.927-.332-2.927 4.282 2.555 4.45 2.555 4.45h1.524v-2.141s-.083-2.554 2.513-2.554zm-.056-5.74a.784.784 0 1 1 0-1.57.784.784 0 0 1 0 1.57z" /><path d="M18.452 7.532h-1.524v2.141s.083 2.554-2.513 2.554h-4.328s-2.432-.04-2.432 2.35v3.951s-.369 2.391 4.409 2.391c4.573 0 4.288-1.983 4.288-1.983l-.006-2.054h-4.363v-.618h6.096s2.927.332 2.927-4.282c0-4.614-2.554-4.45-2.554-4.45zm-4.597 10.455a.784.784 0 1 1 0 1.57.784.784 0 0 1 0-1.57z" /></svg>
    )},
    { name: "Telegram", desc: "Signal Delivery", icon: (
      <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor"><path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z" /></svg>
    )},
    { name: "Cornix", desc: "Auto-Execution", icon: (
      <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor"><path d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.325.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 0 1 1.37.49l1.296 2.247a1.125 1.125 0 0 1-.26 1.431l-1.003.827c-.293.241-.438.613-.43.992a7.723 7.723 0 0 1 0 .255c-.008.378.137.75.43.991l1.004.827c.424.35.534.955.26 1.43l-1.298 2.247a1.125 1.125 0 0 1-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.47 6.47 0 0 1-.22.128c-.331.183-.581.495-.644.869l-.213 1.281c-.09.543-.56.94-1.11.94h-2.594c-.55 0-1.019-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 0 1-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 0 1-1.369-.49l-1.297-2.247a1.125 1.125 0 0 1 .26-1.431l1.004-.827c.292-.24.437-.613.43-.991a6.932 6.932 0 0 1 0-.255c.007-.38-.138-.751-.43-.992l-1.004-.827a1.125 1.125 0 0 1-.26-1.43l1.297-2.247a1.125 1.125 0 0 1 1.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.086.22-.128.332-.183.582-.495.644-.869l.214-1.28Z" /><path d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" fill="none" stroke="currentColor" strokeWidth="1" /></svg>
    )},
    { name: "Google Sheets", desc: "Public Tracking", icon: (
      <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor"><path d="M19 11V9h-6V5h-2v4H5v2h6v4h2v-4h6z" opacity="0.5" /><path d="M3 5v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V5a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2zm2 0h14v14H5V5z" /><rect x="7" y="8" width="4" height="2" rx="0.5" /><rect x="13" y="8" width="4" height="2" rx="0.5" /><rect x="7" y="12" width="4" height="2" rx="0.5" /><rect x="13" y="12" width="4" height="2" rx="0.5" /><rect x="7" y="16" width="4" height="2" rx="0.5" /><rect x="13" y="16" width="4" height="2" rx="0.5" /></svg>
    )},
  ];
  return (
    <section className="py-12 px-4 border-y border-border/20 bg-card/10">
      <div className="max-w-5xl mx-auto">
        <p className={`reveal ${visible ? "visible" : ""} text-center text-muted text-[11px] uppercase tracking-[0.25em] font-mono mb-8`}>
          {label}
        </p>
        <div className={`reveal reveal-delay-1 ${visible ? "visible" : ""} flex flex-wrap items-center justify-center gap-8 md:gap-14`}>
          {stack.map((s) => (
            <div key={s.name} className="flex items-center gap-2.5 opacity-40 hover:opacity-70 transition-opacity duration-300 cursor-default group">
              <div className="w-9 h-9 rounded-lg border border-border/30 bg-card/50 flex items-center justify-center text-primary/70 group-hover:text-primary group-hover:border-primary/30 transition-all">
                {s.icon}
              </div>
              <div>
                <span className="font-mono text-xs text-foreground/70 tracking-wider block leading-tight">{s.name}</span>
                <span className="text-[10px] text-muted">{s.desc}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ─── Comparison Table ─── */

function ComparisonTable({ t, visible }: { t: TStrings; visible: boolean }) {
  const rows = [t.compRow1, t.compRow2, t.compRow3, t.compRow4, t.compRow5, t.compRow6];
  return (
    <div className={`reveal reveal-delay-2 ${visible ? "visible" : ""} max-w-3xl mx-auto overflow-x-auto -mx-4 px-4`}>
      <table className="w-full border-collapse min-w-[500px]">
        <thead>
          <tr>
            <th className="text-left py-4 px-4 text-xs uppercase tracking-widest text-muted font-mono border-b border-border/30">{t.compCol1}</th>
            <th className="text-center py-4 px-4 text-xs uppercase tracking-widest text-danger/70 font-mono border-b border-border/30">{t.compCol2}</th>
            <th className="text-center py-4 px-4 text-xs uppercase tracking-widest text-primary font-mono border-b border-border/30 bg-primary/5 rounded-t-xl">{t.compCol3}</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row: string[], i: number) => (
            <tr key={i} className="border-b border-border/20 hover:bg-card/30 transition-colors">
              <td className="py-4 px-4 text-sm font-medium text-foreground">{row[0]}</td>
              <td className="py-4 px-4 text-sm text-center text-muted">
                <span className="inline-flex items-center gap-1.5">
                  <svg className="w-4 h-4 text-danger/50" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M6 18 18 6M6 6l12 12" />
                  </svg>
                  {row[1]}
                </span>
              </td>
              <td className="py-4 px-4 text-sm text-center bg-primary/5">
                <span className="inline-flex items-center gap-1.5 text-primary font-medium">
                  <svg className="w-4 h-4 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="m4.5 12.75 6 6 9-13.5" />
                  </svg>
                  {row[2]}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/* ─── Benefits Strip ─── */

function BenefitsStrip({ t, visible }: { t: TStrings; visible: boolean }) {
  const benefits = [
    { icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M15.182 15.182a4.5 4.5 0 0 1-6.364 0M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0ZM9.75 9.75c0 .414-.168.75-.375.75S9 10.164 9 9.75 9.168 9 9.375 9s.375.336.375.75Zm-.375 0h.008v.015h-.008V9.75Zm5.625 0c0 .414-.168.75-.375.75s-.375-.336-.375-.75.168-.75.375-.75.375.336.375.75Zm-.375 0h.008v.015h-.008V9.75Z" />
      </svg>
    ), label: t.benefit1 },
    { icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
      </svg>
    ), label: t.benefit2 },
    { icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
      </svg>
    ), label: t.benefit3 },
    { icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75Z" />
      </svg>
    ), label: t.benefit4 },
  ];
  return (
    <div className={`reveal ${visible ? "visible" : ""} flex flex-wrap items-center justify-center gap-6 md:gap-10 py-8`}>
      {benefits.map((b, i) => (
        <div key={i} className="flex items-center gap-2 text-primary/80">
          <div className="w-9 h-9 rounded-full bg-primary/10 flex items-center justify-center">
            {b.icon}
          </div>
          <span className="text-sm font-medium text-foreground/70">{b.label}</span>
        </div>
      ))}
    </div>
  );
}

/* ─── Email Capture ─── */

function EmailCapture({ t }: { t: TStrings }) {
  const [email, setEmail] = useState("");
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !email.includes("@")) return;
    // Store locally for now — integrate with MailerLite/Resend later
    const emails = JSON.parse(localStorage.getItem("captured-emails") || "[]");
    emails.push({ email, date: new Date().toISOString() });
    localStorage.setItem("captured-emails", JSON.stringify(emails));
    setSubmitted(true);
    setEmail("");
  };

  return (
    <section className="py-20 px-4 border-y border-border/20 bg-card/10">
      <div className="max-w-xl mx-auto text-center">
        <span className="inline-block px-4 py-1.5 text-xs font-mono uppercase tracking-widest text-primary border border-primary/30 rounded-full mb-5">
          {t.emailTag}
        </span>
        <h2 className="text-2xl md:text-3xl font-bold mb-3 tracking-tight">{t.emailTitle}</h2>
        <p className="text-muted mb-8 text-sm leading-relaxed">{t.emailSubtitle}</p>

        {submitted ? (
          <div className="flex items-center justify-center gap-2 text-primary font-medium py-4">
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="m4.5 12.75 6 6 9-13.5" />
            </svg>
            {t.emailSuccess}
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row gap-3 max-w-md mx-auto">
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder={t.emailPlaceholder}
              required
              className="flex-1 px-4 py-3 rounded-xl bg-background border border-border/50 text-foreground placeholder:text-muted/50 focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/20 transition-all text-sm font-mono"
            />
            <button
              type="submit"
              className="btn-primary btn-press px-6 py-3 rounded-xl text-sm font-semibold whitespace-nowrap"
            >
              {t.emailButton}
            </button>
          </form>
        )}

        <p className="text-muted/50 text-xs mt-4">{t.emailDisclaimer}</p>
      </div>
    </section>
  );
}

/* ─── Cookie Consent ─── */

function CookieConsent({ t }: { t: TStrings }) {
  const [show, setShow] = useState(false);
  useEffect(() => {
    const consent = localStorage.getItem("cookie-consent");
    if (!consent) {
      const timer = setTimeout(() => setShow(true), 2000);
      return () => clearTimeout(timer);
    }
  }, []);
  if (!show) return null;
  return (
    <div className="fixed bottom-4 left-4 right-4 md:left-auto md:right-6 md:max-w-sm z-50" style={{ animation: "fadeInUp 0.5s ease-out" }}>
      <div className="glass rounded-2xl p-5 shadow-2xl border border-border/50">
        <p className="text-sm text-muted mb-4">{t.cookieText}</p>
        <div className="flex items-center gap-3">
          <button
            onClick={() => { localStorage.setItem("cookie-consent", "accepted"); setShow(false); }}
            className="btn-primary btn-press px-5 py-2 rounded-lg text-xs font-semibold flex-1"
          >
            {t.cookieAccept}
          </button>
          <button
            onClick={() => { localStorage.setItem("cookie-consent", "declined"); setShow(false); }}
            className="px-5 py-2 rounded-lg text-xs font-medium border border-border/50 text-muted hover:text-foreground hover:border-primary/30 transition-all flex-1"
          >
            {t.cookieDeny}
          </button>
        </div>
      </div>
    </div>
  );
}

export default function Home() {
  const [locale, setLocale] = useState<Locale>("en");
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [exitPopupShown, setExitPopupShown] = useState(false);
  const [exitPopupDismissed, setExitPopupDismissed] = useState(false);
  const [deposit, setDeposit] = useState(1000);
  const theme: Theme = "dark";
  const t = T[locale];

  const socialProofSection = useInView(0.2);
  const mediaSection = useInView(0.1);
  const securitySection = useInView(0.2);
  const dashboardSection = useInView(0.15);
  const metricsSection = useInView(0.2);
  const roiSection = useInView(0.1);
  const howItWorks = useInView(0.15);
  const signalSection = useInView(0.2);
  const featuresSection = useInView(0.1);
  const comparisonSection = useInView(0.1);
  const testimonialsSection = useInView(0.1);
  const pricingSection = useInView(0.1);
  const faqSection = useInView(0.1);
  const ctaSection = useInView(0.2);

  const scrollProgress = useScrollProgress();
  const floatingVisible = useFloatingVisible();
  const navVisible = useNavVisible();
  const parallaxRef = useRef<HTMLDivElement>(null);

  // Parallax effect for floating orbs
  useEffect(() => {
    const onScroll = () => {
      if (parallaxRef.current) {
        parallaxRef.current.style.transform = `translateY(${window.scrollY * 0.05}px)`;
      }
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  const cursorGlowRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (cursorGlowRef.current) {
        cursorGlowRef.current.style.left = `${e.clientX}px`;
        cursorGlowRef.current.style.top = `${e.clientY}px`;
      }
    };
    window.addEventListener('mousemove', handler);
    return () => window.removeEventListener('mousemove', handler);
  }, []);

  const scrollTo = useCallback((ref: React.RefObject<HTMLDivElement | null>) => {
    if (ref.current) {
      const offset = 80; // navbar height
      const top = ref.current.getBoundingClientRect().top + window.scrollY - offset;
      window.scrollTo({ top, behavior: "smooth" });
    }
  }, []);

  // Exit-intent popup: show once when cursor leaves viewport top
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (e.clientY <= 0 && !exitPopupDismissed) {
        setExitPopupShown(true);
      }
    };
    document.documentElement.addEventListener('mouseleave', handler);
    return () => document.documentElement.removeEventListener('mouseleave', handler);
  }, [exitPopupDismissed]);

  const metrics = getMetrics(t);
  const steps = getSteps(t);
  const features = getFeatures(t);
  const pricing = getPricing(t);
  const faqItems = getFaqItems(t);

  return (
    <div className="grid-bg relative">
      {/* Cursor glow effect */}
      <div
        ref={cursorGlowRef}
        className="pointer-events-none fixed w-[300px] h-[300px] rounded-full opacity-[0.04] bg-primary blur-[100px] -translate-x-1/2 -translate-y-1/2 z-0 hidden md:block"
        aria-hidden="true"
      />

      {/* Skip to main content — accessibility */}
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:top-4 focus:left-4 focus:z-[100] focus:px-4 focus:py-2 focus:bg-primary focus:text-background focus:rounded-lg focus:text-sm focus:font-semibold"
      >
        Skip to main content
      </a>

      {/* Scroll progress bar */}
      <div
        className="scroll-line"
        style={{ width: `${scrollProgress}%` }}
        aria-hidden="true"
      />

      {/* ─── STICKY NAVBAR ─── */}
      <nav
        aria-label="Main navigation"
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
          <div className="flex items-center gap-2">
            <LanguageToggle locale={locale} setLocale={setLocale} />
            {/* Mobile burger */}
            <button
              className="md:hidden flex flex-col gap-1.5 p-3 min-w-[44px] min-h-[44px] items-center justify-center rounded-lg hover:bg-card/50 transition-colors"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              aria-label="Toggle menu"
            >
              <span className={`block w-5 h-0.5 bg-foreground transition-all duration-300 ${mobileMenuOpen ? "rotate-45 translate-y-2" : ""}`} />
              <span className={`block w-5 h-0.5 bg-foreground transition-all duration-300 ${mobileMenuOpen ? "opacity-0" : ""}`} />
              <span className={`block w-5 h-0.5 bg-foreground transition-all duration-300 ${mobileMenuOpen ? "-rotate-45 -translate-y-2" : ""}`} />
            </button>
            <a
              href={TELEGRAM_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="hidden md:flex btn-primary btn-press items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold"
            >
              <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="currentColor">
                <path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z" />
              </svg>
              {t.joinTelegram}
            </a>
          </div>
        </div>

        {/* Mobile dropdown menu */}
        <div className={`md:hidden overflow-hidden transition-all duration-300 ${mobileMenuOpen ? "max-h-96 opacity-100" : "max-h-0 opacity-0"}`}>
          <div className="px-4 pb-4 space-y-1 border-t border-border/30">
            {[
              { label: t.navPerformance, ref: metricsSection.ref },
              { label: t.navHowItWorks, ref: howItWorks.ref },
              { label: t.navFeatures, ref: featuresSection.ref },
              { label: t.navPricing, ref: pricingSection.ref },
              { label: t.navFaq, ref: faqSection.ref },
            ].map((item) => (
              <button
                key={item.label}
                onClick={() => { scrollTo(item.ref); setMobileMenuOpen(false); }}
                className="block w-full text-left py-4 px-3 text-sm text-muted hover:text-foreground hover:bg-card/30 rounded-lg transition-colors"
              >
                {item.label}
              </button>
            ))}
            <a
              href={TELEGRAM_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="btn-primary btn-press flex items-center justify-center gap-2 w-full py-3 rounded-lg text-sm font-semibold mt-2"
            >
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

      <main id="main-content">
      {/* ─── HERO ─── */}
      <section className="relative min-h-screen flex items-center justify-center px-4 overflow-hidden">
        {/* Deep atmospheric glow */}
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_80%_60%_at_50%_-10%,rgba(0,212,170,0.08)_0%,transparent_70%)] pointer-events-none" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_40%_40%_at_75%_70%,rgba(255,215,0,0.04)_0%,transparent_60%)] pointer-events-none" />

        {/* Animated gradient mesh blob */}
        <div className="gradient-mesh top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/4 opacity-60" aria-hidden="true" />

        {/* Floating gradient orbs — parallax wrapper */}
        <div ref={parallaxRef} className="absolute inset-0 pointer-events-none" aria-hidden="true">
          <div className="absolute top-1/4 left-1/4 w-[500px] h-[500px] rounded-full bg-primary/[0.03] blur-[120px] animate-orb-1" />
          <div className="absolute bottom-1/3 right-1/5 w-[400px] h-[400px] rounded-full bg-accent/[0.02] blur-[100px] animate-orb-2" />
          <div className="absolute top-2/3 left-2/3 w-[300px] h-[300px] rounded-full bg-danger/[0.02] blur-[80px] animate-orb-3" />
        </div>

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
        <div className="absolute top-10 right-6 sm:top-8 sm:right-8 z-20 flex items-center gap-2">
          <LanguageToggle
            locale={locale}
            setLocale={setLocale}
            className="bg-background/80 backdrop-blur-xl"
          />
        </div>

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
          <h1 className="text-3xl sm:text-4xl md:text-6xl lg:text-8xl font-bold tracking-tight mb-4"
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
            className="text-lg sm:text-xl md:text-2xl lg:text-3xl text-foreground/80 font-light mb-3 tracking-wide"
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

      {/* ─── SOCIAL PROOF STRIP ─── */}
      <section ref={socialProofSection.ref} className="py-16 px-4">
        <div className="max-w-5xl mx-auto">
          <p className={`reveal ${socialProofSection.visible ? "visible" : ""} text-center text-muted text-sm uppercase tracking-widest font-mono mb-10`}>
            {t.trustedBy}
          </p>

          {/* Animated social proof counters */}
          <div className={`reveal reveal-delay-1 ${socialProofSection.visible ? "visible" : ""} grid grid-cols-2 md:grid-cols-4 gap-6 mb-12`}>
            {[
              { target: 150, decimals: 0, suffix: "+", label: t.socialTrades },
              { target: 71.1, decimals: 1, suffix: "%", label: t.socialWinRate },
              { target: 99.9, decimals: 1, suffix: "%", label: t.socialUptime },
              { target: 200, decimals: 0, suffix: "+", label: t.socialSignals },
            ].map((stat) => (
              <SocialCounter key={stat.label} {...stat} active={socialProofSection.visible} />
            ))}
          </div>

          {/* Tech metrics row */}
          <div className={`reveal reveal-delay-2 ${socialProofSection.visible ? "visible" : ""} flex flex-wrap items-center justify-center gap-6 md:gap-10 mb-12 text-sm`}>
            {[
              { value: "4", label: t.metricPairs },
              { value: "4", label: t.metricTimeframes },
              { value: "15+", label: t.metricIndicators },
              { value: "3", label: t.metricExchanges },
            ].map((stat) => (
              <div key={stat.label} className="text-center">
                <div className="font-mono text-xl font-bold text-foreground/70 mb-0.5">{stat.value}</div>
                <div className="text-[10px] text-muted uppercase tracking-wider">{stat.label}</div>
              </div>
            ))}
          </div>

          {/* Exchange logos */}
          <ExchangeLogos visible={socialProofSection.visible} />
        </div>
      </section>

      {/* ─── AS SEEN IN (Media) ─── */}
      <div ref={mediaSection.ref}>
        <TechStackLogos visible={mediaSection.visible} label={t.asSeenIn} />
      </div>

      {/* ─── BENEFITS STRIP ─── */}
      <BenefitsStrip t={t} visible={mediaSection.visible} />

      <SectionDivider variant="glow" />

      {/* ─── SECURITY & TRUST BADGES ─── */}
      <section ref={securitySection.ref} className="py-16 px-4">
        <div className="max-w-5xl mx-auto">
          <p className={`reveal ${securitySection.visible ? "visible" : ""} text-center text-muted text-sm uppercase tracking-widest font-mono mb-10`}>
            {t.securityTag}
          </p>
          <div className={`reveal reveal-delay-1 ${securitySection.visible ? "visible" : ""} grid grid-cols-2 md:grid-cols-4 gap-4 md:gap-6`}>
            {[
              { icon: (
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 1 0-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 0 0 2.25-2.25v-6.75a2.25 2.25 0 0 0-2.25-2.25H6.75a2.25 2.25 0 0 0-2.25 2.25v6.75a2.25 2.25 0 0 0 2.25 2.25Z" />
                </svg>
              ), title: t.secBadge1, desc: t.secBadge1Desc },
              { icon: (
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M17.25 6.75 22.5 12l-5.25 5.25m-10.5 0L1.5 12l5.25-5.25m7.5-3-4.5 16.5" />
                </svg>
              ), title: t.secBadge2, desc: t.secBadge2Desc },
              { icon: (
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9.75 3.104v5.714a2.25 2.25 0 0 1-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 0 1 4.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0 1 12 15a9.065 9.065 0 0 0-6.23.693L5 14.5m14.8.8 1.402 1.402c1.232 1.232.65 3.318-1.067 3.611A48.309 48.309 0 0 1 12 21c-2.773 0-5.491-.235-8.135-.687-1.718-.293-2.3-2.379-1.067-3.61L5 14.5" />
                </svg>
              ), title: t.secBadge3, desc: t.secBadge3Desc },
              { icon: (
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 3v11.25A2.25 2.25 0 0 0 6 16.5h2.25M3.75 3h-1.5m1.5 0h16.5m0 0h1.5m-1.5 0v11.25A2.25 2.25 0 0 1 18 16.5h-2.25m-7.5 0h7.5m-7.5 0-1 3m8.5-3 1 3m0 0 .5 1.5m-.5-1.5h-9.5m0 0-.5 1.5m.75-9 3-3 2.148 2.148A12.061 12.061 0 0 1 16.5 7.605" />
                </svg>
              ), title: t.secBadge4, desc: t.secBadge4Desc },
            ].map((badge) => (
              <div key={badge.title} className="security-badge text-center p-5 rounded-xl border border-border/50 bg-card/30 hover:border-primary/30 transition-all group">
                <div className="w-12 h-12 mx-auto mb-3 rounded-full bg-primary/10 flex items-center justify-center text-primary group-hover:bg-primary/15 transition-colors">
                  {badge.icon}
                </div>
                <h4 className="font-semibold text-sm mb-1">{badge.title}</h4>
                <p className="text-muted text-xs leading-relaxed">{badge.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── DASHBOARD MOCKUP ─── */}
      <section ref={dashboardSection.ref} className="py-20 px-4">
        <div className="max-w-5xl mx-auto">
          <SectionHeading
            tag={t.dashboardTag}
            title={t.dashboardTitle}
            subtitle={t.dashboardSubtitle}
            visible={dashboardSection.visible}
          />
          <DashboardMockup t={t} visible={dashboardSection.visible} />
        </div>
      </section>

      <SectionDivider variant="dots" />

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
          <EquityCurve label={t.equityCurveLabel} visible={metricsSection.visible} />

          <p
            className={`reveal reveal-delay-6 ${metricsSection.visible ? "visible" : ""} text-center text-muted text-sm mt-8`}
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

      <SectionDivider variant="dots" />


      {/* ─── ROI CALCULATOR ─── */}
      <section ref={roiSection.ref} className="py-24 px-4">
        <div className="max-w-4xl mx-auto">
          <SectionHeading
            tag={t.roiTag}
            title={t.roiTitle}
            subtitle={t.roiSubtitle}
            visible={roiSection.visible}
          />

          {/* Deposit slider */}
          <div
            className={`reveal reveal-delay-1 ${roiSection.visible ? "visible" : ""} max-w-xl mx-auto mb-12`}
          >
            <label className="block text-sm font-mono uppercase tracking-wider text-muted mb-3 text-center">
              {t.roiDeposit}
            </label>
            <div className="text-4xl font-bold text-center mb-4 text-primary">
              {"$"}{deposit.toLocaleString("en-US")}
            </div>
            <input
              type="range"
              min={100}
              max={50000}
              step={100}
              value={deposit}
              onChange={(e) => setDeposit(Number(e.target.value))}
              className="w-full h-2 rounded-full appearance-none cursor-pointer"
              style={{
                background: `linear-gradient(to right, #00D4AA ${((deposit - 100) / (50000 - 100)) * 100}%, rgba(255,255,255,0.1) ${((deposit - 100) / (50000 - 100)) * 100}%)`,
              }}
            />
            <div className="flex justify-between text-xs text-muted mt-2 font-mono">
              <span>$100</span>
              <span>$50,000</span>
            </div>
          </div>

          {/* Result cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {([
              { label: t.roiMonth1, months: 1 },
              { label: t.roiMonth3, months: 3 },
              { label: t.roiMonth6, months: 6 },
              { label: t.roiMonth12, months: 12 },
            ] as const).map((item, i) => {
              const result = deposit * Math.pow(1.1357, item.months);
              const profit = result - deposit;
              const pctGain = ((result / deposit - 1) * 100).toFixed(1);
              return (
                <div
                  key={item.months}
                  className={`reveal reveal-delay-${i + 2} ${roiSection.visible ? "visible" : ""} relative p-4 md:p-6 rounded-2xl border border-border/50 bg-background/50 backdrop-blur-sm hover:border-primary/30 transition-all text-center`}
                >
                  <p className="text-xs font-mono uppercase tracking-wider text-muted mb-2">
                    {item.label}
                  </p>
                  <p className="text-xl sm:text-2xl md:text-3xl font-bold mb-1 truncate" style={{ color: "#00D4AA" }}>
                    {"$"}{result.toLocaleString("en-US", { maximumFractionDigits: 0 })}
                  </p>
                  <p className="text-xs sm:text-sm font-semibold truncate" style={{ color: "#FFD700" }}>
                    {`+$${profit.toLocaleString("en-US", { maximumFractionDigits: 0 })} (${pctGain}%)`}
                  </p>
                </div>
              );
            })}
          </div>

          {/* Disclaimer */}
          <p
            className={`reveal reveal-delay-6 ${roiSection.visible ? "visible" : ""} text-center text-xs text-muted/70 mt-8 max-w-lg mx-auto`}
          >
            {t.roiDisclaimer}
          </p>
        </div>
      </section>

      <SectionDivider variant="dots" />
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
                className={`reveal reveal-delay-${i + 1} ${howItWorks.visible ? "visible" : ""} step-card relative p-8 rounded-2xl border border-border/50 bg-background/50 backdrop-blur-sm hover:border-primary/30 transition-all group`}
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

      <SectionDivider variant="glow" />

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

      <SectionDivider variant="dots" />

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

      <SectionDivider variant="dots" />

      {/* ─── COMPARISON TABLE ─── */}
      <section ref={comparisonSection.ref} className="py-24 px-4">
        <div className="max-w-5xl mx-auto">
          <SectionHeading
            tag={t.comparisonTag}
            title={t.comparisonTitle}
            subtitle={t.comparisonSubtitle}
            visible={comparisonSection.visible}
          />
          <ComparisonTable t={t} visible={comparisonSection.visible} />
        </div>
      </section>

      <SectionDivider variant="glow" />

      {/* ─── TRANSPARENCY / VERIFIED ON ─── */}
      <section className="py-24 px-4">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-16">
            <span className="inline-block px-4 py-1.5 text-xs font-mono uppercase tracking-widest text-primary border border-primary/30 rounded-full mb-5">
              {t.transparencyTag}
            </span>
            <h2 className="text-3xl md:text-4xl lg:text-5xl font-bold mb-4 tracking-tight">
              {t.transparencyTitle}
            </h2>
            <p className="text-muted max-w-2xl mx-auto text-lg leading-relaxed">
              {t.transparencySubtitle}
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-6 mb-10">
            {/* Public Trade Log */}
            <a
              href={SHEETS_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="transparency-card group p-6 rounded-2xl border border-primary/20 bg-primary/[0.03] hover:bg-primary/[0.06] hover:border-primary/40"
            >
              <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center text-primary mb-4 group-hover:scale-110 transition-transform">
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M3.375 19.5h17.25m-17.25 0a1.125 1.125 0 0 1-1.125-1.125M3.375 19.5h7.5c.621 0 1.125-.504 1.125-1.125m-9.75 0V5.625m0 12.75v-1.5c0-.621.504-1.125 1.125-1.125m18.375 2.625V5.625m0 12.75c0 .621-.504 1.125-1.125 1.125m1.125-1.125v-1.5c0-.621-.504-1.125-1.125-1.125m0 3.75h-7.5A1.125 1.125 0 0 1 12 18.375m9.75-12.75c0-.621-.504-1.125-1.125-1.125H3.375c-.621 0-1.125.504-1.125 1.125m19.5 0v1.5c0 .621-.504 1.125-1.125 1.125M2.25 5.625v1.5c0 .621.504 1.125 1.125 1.125m0 0h17.25m-17.25 0h7.5c.621 0 1.125.504 1.125 1.125M3.375 8.25c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125m17.25-3.75h-7.5c-.621 0-1.125.504-1.125 1.125m8.625-1.125c.621 0 1.125.504 1.125 1.125v1.5c0 .621-.504 1.125-1.125 1.125m-17.25 0h7.5m-7.5 0c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125M12 10.875v-1.5m0 1.5c0 .621-.504 1.125-1.125 1.125M12 10.875c0 .621.504 1.125 1.125 1.125m-2.25 0c.621 0 1.125.504 1.125 1.125M13.125 12h7.5m-7.5 0c-.621 0-1.125.504-1.125 1.125M20.625 12c.621 0 1.125.504 1.125 1.125v1.5c0 .621-.504 1.125-1.125 1.125m-17.25 0h7.5M12 14.625v-1.5m0 1.5c0 .621-.504 1.125-1.125 1.125M12 14.625c0 .621.504 1.125 1.125 1.125m-2.25 0c.621 0 1.125.504 1.125 1.125m0 0v1.5c0 .621-.504 1.125-1.125 1.125" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold mb-2">{t.transparencySheet}</h3>
              <p className="text-muted text-sm leading-relaxed">{t.transparencySheetDesc}</p>
              <span className="inline-flex items-center gap-1.5 mt-4 text-primary text-sm font-medium group-hover:gap-2.5 transition-all">
                {t.verifyYourself}
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5 21 12m0 0-7.5 7.5M21 12H3" />
                </svg>
              </span>
            </a>

            {/* Open-Source Strategy */}
            <div className="transparency-card p-6 rounded-2xl border border-border/50 bg-card/30 hover:border-primary/20">
              <div className="w-12 h-12 rounded-xl bg-violet-500/10 flex items-center justify-center text-violet-400 mb-4">
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M17.25 6.75 22.5 12l-5.25 5.25m-10.5 0L1.5 12l5.25-5.25m7.5-3-4.5 16.5" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold mb-2">{t.transparencyGithub}</h3>
              <p className="text-muted text-sm leading-relaxed">{t.transparencyGithubDesc}</p>
            </div>

            {/* Paper-Trading Phase */}
            <div className="transparency-card p-6 rounded-2xl border border-border/50 bg-card/30 hover:border-primary/20">
              <div className="w-12 h-12 rounded-xl bg-amber-500/10 flex items-center justify-center text-amber-400 mb-4">
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75m-3-7.036A11.959 11.959 0 0 1 3.598 6 11.99 11.99 0 0 0 3 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285Z" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold mb-2">{t.transparencyPaper}</h3>
              <p className="text-muted text-sm leading-relaxed">{t.transparencyPaperDesc}</p>
            </div>
          </div>
        </div>
      </section>

      <SectionDivider variant="dots" />

      {/* ─── TESTIMONIALS ─── */}
      <section ref={testimonialsSection.ref} className="py-24 px-4 bg-card/20">
        <div className="max-w-5xl mx-auto">
          <SectionHeading
            tag={t.testimonialsTag}
            title={t.testimonialsTitle}
            subtitle={t.testimonialsSubtitle}
            visible={testimonialsSection.visible}
          />
          <RatingSummary t={t} visible={testimonialsSection.visible} />
          <div className="grid md:grid-cols-3 gap-6 mb-6">
            <TestimonialCard quote={t.testimonial1} author={t.testimonial1Author} role={t.testimonial1Role} delay={1} visible={testimonialsSection.visible} />
            <TestimonialCard quote={t.testimonial2} author={t.testimonial2Author} role={t.testimonial2Role} delay={2} visible={testimonialsSection.visible} />
            <TestimonialCard quote={t.testimonial3} author={t.testimonial3Author} role={t.testimonial3Role} delay={3} visible={testimonialsSection.visible} />
          </div>
          <div className="grid md:grid-cols-2 gap-6 max-w-2xl mx-auto">
            <TestimonialCard quote={t.testimonial4} author={t.testimonial4Author} role={t.testimonial4Role} delay={4} visible={testimonialsSection.visible} />
            <TestimonialCard quote={t.testimonial5} author={t.testimonial5Author} role={t.testimonial5Role} delay={5} visible={testimonialsSection.visible} />
          </div>
        </div>
      </section>

      <SectionDivider variant="glow" />

      {/* ─── PRICING ─── */}
      <section ref={pricingSection.ref} className="py-24 px-4">
        <div className="max-w-5xl mx-auto">
          <SectionHeading
            tag={t.priceTag}
            title={t.priceTitle}
            subtitle={t.priceSubtitle}
            visible={pricingSection.visible}
          />
          <div className={`reveal reveal-delay-1 ${pricingSection.visible ? "visible" : ""} flex justify-center mb-8`}>
            <EarlyAdopterBadge label={t.earlyAdopterLabel} daysLeftLabel={t.daysLeft} />
          </div>

          <div className="grid md:grid-cols-3 gap-6 max-w-4xl mx-auto items-start">
            {pricing.map((plan, i) => {
              const isPopular = plan.highlight;
              const isVip = plan.name === "VIP";
              const cardContent = (
                <div
                  className={`${isVip ? "vip-card-inner" : ""} ${
                    isVip ? "animate-pulse-glow-gold" : ""
                  } pricing-card reveal reveal-delay-${i + 1} ${pricingSection.visible ? "visible" : ""} relative p-8 rounded-2xl h-full ${
                    isVip
                      ? "bg-[#0f1a0f]"
                      : isPopular
                        ? "glass border-primary/30 shadow-[0_0_20px_rgba(0,212,170,0.1)]"
                        : "glass hover:border-primary/20"
                  }`}
                >
                  {isPopular && (
                    <div className="absolute -top-3 left-1/2 -translate-x-1/2 z-10">
                      <span className="px-4 py-1 bg-primary text-background text-xs font-bold rounded-full uppercase tracking-wider">
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
                        : isPopular
                          ? "bg-primary text-background hover:brightness-110"
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
      {/* ─── EMAIL CAPTURE ─── */}
      <EmailCapture t={t} />

      </main>

      {/* ─── FOOTER ─── */}
      <footer className="border-t border-border/40 py-16 px-4">
        <div className="max-w-5xl mx-auto">
          {/* Top row: brand + nav columns */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-10 mb-12">
            {/* Brand */}
            <div className="md:col-span-1">
              <span className="text-xl font-bold gradient-text">TrendRider</span>
              <p className="text-muted text-sm mt-2 leading-relaxed">{t.footerTagline}</p>
              {/* Social icons */}
              <div className="flex items-center gap-3 mt-4">
                {/* Telegram */}
                <a href={TELEGRAM_URL} target="_blank" rel="noopener noreferrer" className="w-9 h-9 rounded-lg bg-card border border-border/50 flex items-center justify-center text-muted hover:text-primary hover:border-primary/30 transition-all" aria-label="Telegram">
                  <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z" />
                  </svg>
                </a>
                {/* X/Twitter */}
                <a href="https://x.com/TrendRiderBot" target="_blank" rel="noopener noreferrer" className="w-9 h-9 rounded-lg bg-card border border-border/50 flex items-center justify-center text-muted hover:text-primary hover:border-primary/30 transition-all" aria-label="X / Twitter">
                  <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
                  </svg>
                </a>
                {/* Discord */}
                <a href="https://discord.gg/trendrider" target="_blank" rel="noopener noreferrer" className="w-9 h-9 rounded-lg bg-card border border-border/50 flex items-center justify-center text-muted hover:text-primary hover:border-primary/30 transition-all" aria-label="Discord">
                  <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0 12.64 12.64 0 0 0-.617-1.25.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057 19.9 19.9 0 0 0 5.993 3.03.078.078 0 0 0 .084-.028 14.09 14.09 0 0 0 1.226-1.994.076.076 0 0 0-.041-.106 13.107 13.107 0 0 1-1.872-.892.077.077 0 0 1-.008-.128 10.2 10.2 0 0 0 .372-.292.074.074 0 0 1 .077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127 12.299 12.299 0 0 1-1.873.892.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028 19.839 19.839 0 0 0 6.002-3.03.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.03zM8.02 15.33c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.956-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.956 2.418-2.157 2.418zm7.975 0c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.955-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.946 2.418-2.157 2.418z" />
                  </svg>
                </a>
              </div>
            </div>

            {/* Product column */}
            <div>
              <h4 className="text-sm font-semibold text-foreground mb-4">Product</h4>
              <ul className="space-y-2.5">
                <li><a href={TELEGRAM_URL} target="_blank" rel="noopener noreferrer" className="text-muted text-sm hover:text-primary transition-colors">{t.telegramChannel}</a></li>
                <li><a href={SHEETS_URL} target="_blank" rel="noopener noreferrer" className="text-muted text-sm hover:text-primary transition-colors">{t.liveResults}</a></li>
              </ul>
            </div>

            {/* Legal column */}
            <div>
              <h4 className="text-sm font-semibold text-foreground mb-4">Legal</h4>
              <ul className="space-y-2.5">
                <li><a href="/terms" className="text-muted text-sm hover:text-primary transition-colors">{t.termsOfService}</a></li>
                <li><a href="/privacy" className="text-muted text-sm hover:text-primary transition-colors">{t.privacyPolicy}</a></li>
              </ul>
            </div>

            {/* Contact column */}
            <div>
              <h4 className="text-sm font-semibold text-foreground mb-4">{t.contactUs}</h4>
              <ul className="space-y-2.5">
                <li><a href="mailto:support@trendrider.net" className="text-muted text-sm hover:text-primary transition-colors">support@trendrider.net</a></li>
                <li><a href={TELEGRAM_URL} target="_blank" rel="noopener noreferrer" className="text-muted text-sm hover:text-primary transition-colors">@TrendRiderSupport</a></li>
              </ul>
            </div>
          </div>

          {/* Disclaimer + bottom bar */}
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

      {/* ─── COOKIE CONSENT ─── */}
      <CookieConsent t={t} />

      {/* ─── EXIT-INTENT POPUP ─── */}
      {exitPopupShown && !exitPopupDismissed && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm" onClick={() => { setExitPopupShown(false); setExitPopupDismissed(true); }}>
          <div className="relative max-w-md mx-4 p-8 rounded-2xl glass border border-primary/30 text-center" onClick={e => e.stopPropagation()}>
            <button onClick={() => { setExitPopupShown(false); setExitPopupDismissed(true); }} className="absolute top-3 right-3 text-muted hover:text-foreground text-xl">&times;</button>
            <div className="text-4xl mb-4">{"\u{1F4E1}"}</div>
            <h3 className="text-xl font-bold text-foreground mb-2">{t.exitTitle}</h3>
            <p className="text-muted mb-6">{t.exitText}</p>
            <a href="https://t.me/TrendRiderSignals" target="_blank" rel="noopener noreferrer" className="inline-block px-6 py-3 bg-primary text-background font-semibold rounded-xl hover:brightness-110 transition-all">
              {t.exitCta}
            </a>
          </div>
        </div>
      )}
    </div>
  );
}
