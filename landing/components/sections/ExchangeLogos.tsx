import type { ReactNode } from "react";

const exchangeLogosMap: Record<string, ReactNode> = {
  Bybit: (
    <svg viewBox="0 0 80 24" fill="currentColor" className="h-5 w-auto" aria-hidden="true">
      <path d="M5.2 4h5.6c2.8 0 4.6 1.6 4.6 4.1 0 1.7-.9 3-2.4 3.5 1.8.5 2.9 2 2.9 3.8 0 2.7-1.9 4.6-5 4.6H5.2V4zm5.3 6.4c1.2 0 1.9-.7 1.9-1.7s-.7-1.7-1.9-1.7H8.3v3.4h2.2zm.3 6.6c1.3 0 2.1-.7 2.1-1.9s-.8-1.9-2.1-1.9H8.3V17h2.5zM19.2 15.5l-4.8-8h3.5l3 5.3 3-5.3h3.4l-4.8 8V20h-3.3v-4.5zM29.5 4h5.6c2.8 0 4.6 1.6 4.6 4.1 0 1.7-.9 3-2.4 3.5 1.8.5 2.9 2 2.9 3.8 0 2.7-1.9 4.6-5 4.6h-5.7V4zm5.3 6.4c1.2 0 1.9-.7 1.9-1.7s-.7-1.7-1.9-1.7h-2.2v3.4h2.2zm.3 6.6c1.3 0 2.1-.7 2.1-1.9s-.8-1.9-2.1-1.9h-2.5V17h2.5zM42.5 4h3.3v16h-3.3V4zm7.8 0h13v3h-4.8v13h-3.3V7h-4.9V4z" />
    </svg>
  ),
  Binance: (
    <svg viewBox="0 0 24 24" fill="currentColor" className="h-6 w-6" aria-hidden="true">
      <path d="M12 1.5L5.5 8l2.4 2.4L12 6.3l4.1 4.1L18.5 8 12 1.5zM3.1 10.4l2.4 2.4-2.4 2.4L.7 12.8l2.4-2.4zm8.9 0L9.6 12.8l2.4 2.4 2.4-2.4-2.4-2.4zm8.9 0l-2.4 2.4 2.4 2.4 2.4-2.4-2.4-2.4zM12 17.7l-4.1-4.1-2.4 2.4L12 22.5l6.5-6.5-2.4-2.4L12 17.7z" />
    </svg>
  ),
  OKX: (
    <svg viewBox="0 0 80 24" fill="currentColor" className="h-5 w-auto" aria-hidden="true">
      <path d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10 10-4.5 10-10S17.5 2 12 2zm0 16.5c-3.6 0-6.5-2.9-6.5-6.5S8.4 5.5 12 5.5s6.5 2.9 6.5 6.5-2.9 6.5-6.5 6.5zM30.5 4h3.5v16h-3.5V4zm7.5 0h3.8l3.5 6.2L48.8 4h3.8l-5.5 8.5L52.8 21H49l-3.7-6.6L41.6 21h-3.8l5.7-8.5L38 4zm17 0h3.5v16H55V4z" />
    </svg>
  ),
  Cornix: (
    <svg viewBox="0 0 24 24" fill="currentColor" className="h-6 w-6" aria-hidden="true">
      <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 15.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 13v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z" />
    </svg>
  ),
  Freqtrade: (
    <svg viewBox="0 0 24 24" fill="currentColor" className="h-6 w-6" aria-hidden="true">
      <path d="M3.5 18.49l6-6.01 4 4L22 6.92l-1.41-1.41-7.09 7.97-4-4L2 16.99z" />
      <path d="M3.5 18.49l6-6.01 4 4L22 6.92" fill="none" stroke="currentColor" strokeWidth="1.5" />
    </svg>
  ),
};

export function ExchangeLogos({ visible }: { visible: boolean }) {
  const exchanges = ["Bybit", "Binance", "OKX", "Cornix", "Freqtrade"];
  return (
    <div className={`reveal reveal-delay-2 ${visible ? "visible" : ""} flex flex-wrap items-center justify-center gap-8 md:gap-12`}>
      {exchanges.map((name, i) => (
        <div
          key={name}
          className={`logo-glow-${i} flex items-center gap-2.5 hover:opacity-100 transition-all duration-300 hover:drop-shadow-[0_0_12px_rgba(0,212,170,0.6)] cursor-default`}
        >
          <div className="text-primary/80">
            {exchangeLogosMap[name]}
          </div>
          <span className="font-mono text-xs text-foreground/80 tracking-widest uppercase">{name}</span>
        </div>
      ))}
    </div>
  );
}
