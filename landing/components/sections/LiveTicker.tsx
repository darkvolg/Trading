import { TICKER_TRADES } from "@/lib/data";

export function LiveTicker() {
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
