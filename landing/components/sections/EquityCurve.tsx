export function EquityCurve({ label, visible }: { label: string; visible: boolean }) {
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
