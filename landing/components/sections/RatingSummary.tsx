import { RATING_DISTRIBUTION, RATING_TOTAL } from "@/lib/data";
import type { TStrings } from "@/lib/i18n";

export function RatingSummary({ t, visible }: { t: TStrings; visible: boolean }) {
  const starLabels = [t.ratingStar1, t.ratingStar2, t.ratingStar3, t.ratingStar4, t.ratingStar5];
  return (
    <div className={`reveal ${visible ? "visible" : ""} mb-12 max-w-2xl mx-auto`}>
      <div className="rounded-2xl border border-border/50 bg-card/30 backdrop-blur-sm p-6 md:p-8 flex flex-col md:flex-row gap-8 items-center">
        {/* Left: big score */}
        <div className="flex flex-col items-center gap-2 min-w-[140px]">
          <span className="text-5xl font-bold gradient-text">{t.ratingOverall}</span>
          <div className="flex gap-0.5">
            {[...Array(5)].map((_, i) => (
              <svg key={i} className={`w-5 h-5 ${i < 5 ? "text-accent" : "text-muted/30"}`} fill="currentColor" viewBox="0 0 20 20" aria-hidden="true">
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
