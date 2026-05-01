export const TELEGRAM_URL = "https://t.me/TrendRiderSignals";
export const TELEGRAM_BOT_URL = "https://t.me/dtrade_signals_bot";
export const TELEGRAM_CHAT_URL = "https://t.me/TrendRiderChat";
export const BYBIT_AFFILIATE_URL = "https://www.bybit.com/invite?ref=0GDX5JR";

// Per-surface affiliate links so we can attribute signups in analytics
// (Bybit ignores extra params; GA4 captures the outbound `utm_source`).
export const bybitRef = (source: string) =>
  `${BYBIT_AFFILIATE_URL}&utm_source=trendrider&utm_medium=${encodeURIComponent(source)}`;
