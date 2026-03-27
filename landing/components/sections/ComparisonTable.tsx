import type { TStrings } from "@/lib/i18n";

export function ComparisonTable({ t, visible }: { t: TStrings; visible: boolean }) {
  const rows = [t.compRow1, t.compRow2, t.compRow3, t.compRow4, t.compRow5, t.compRow6];
  return (
    <div className={`reveal reveal-delay-2 ${visible ? "visible" : ""} max-w-3xl mx-auto overflow-x-auto -mx-4 px-4`}>
      <table className="w-full border-collapse min-w-[340px]">
        <thead>
          <tr>
            <th className="text-left py-3 px-2 sm:px-4 text-[10px] sm:text-xs uppercase tracking-widest text-muted font-mono border-b border-border/30">{t.compCol1}</th>
            <th className="text-center py-3 px-2 sm:px-4 text-[10px] sm:text-xs uppercase tracking-widest text-danger/70 font-mono border-b border-border/30 whitespace-nowrap">{t.compCol2}</th>
            <th className="text-center py-3 px-2 sm:px-4 text-[10px] sm:text-xs uppercase tracking-widest text-primary font-mono border-b border-border/30 bg-primary/5 rounded-t-xl whitespace-nowrap">{t.compCol3}</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row: string[], i: number) => (
            <tr key={i} className="border-b border-border/20 hover:bg-card/30 transition-colors">
              <td className="py-3 px-2 sm:px-4 text-xs sm:text-sm font-medium text-foreground">{row[0]}</td>
              <td className="py-3 px-2 sm:px-4 text-xs sm:text-sm text-center text-muted">
                <span className="inline-flex items-center justify-center gap-1 sm:gap-1.5">
                  <svg className="w-3.5 h-3.5 sm:w-4 sm:h-4 text-danger/50 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} aria-hidden="true">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M6 18 18 6M6 6l12 12" />
                  </svg>
                  <span className="hidden sm:inline">{row[1]}</span>
                </span>
              </td>
              <td className="py-3 px-2 sm:px-4 text-xs sm:text-sm text-center bg-primary/5">
                <span className="inline-flex items-center justify-center gap-1 sm:gap-1.5 text-primary font-medium">
                  <svg className="w-3.5 h-3.5 sm:w-4 sm:h-4 text-primary shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} aria-hidden="true">
                    <path strokeLinecap="round" strokeLinejoin="round" d="m4.5 12.75 6 6 9-13.5" />
                  </svg>
                  <span className="hidden sm:inline">{row[2]}</span>
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
