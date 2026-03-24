import { MOCK_TRADES } from "@/lib/data";
import type { TStrings } from "@/lib/i18n";

const SHEETS_URL =
  "https://docs.google.com/spreadsheets/d/1ZWRJ0PcBSk910MZv426PrleriBnInykr3OebWXJPm-g";

export function DashboardMockup({ t, visible }: { t: TStrings; visible: boolean }) {
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
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 6H5.25A2.25 2.25 0 0 0 3 8.25v10.5A2.25 2.25 0 0 0 5.25 21h10.5A2.25 2.25 0 0 0 18 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25" />
            </svg>
          </a>
        </div>
      </div>
    </div>
  );
}
