"use client";

import { useState, useEffect, useRef, useCallback, type RefObject } from "react";
import { SectionHeading } from "../ui";
import type { TStrings } from "@/lib/i18n";

/* ─── Types ─────────────────────────────────────────────────────────── */

interface PerformanceDashboardProps {
  t: TStrings;
  visible: boolean;
  sectionRef: RefObject<HTMLDivElement | null>;
}

interface PeriodData {
  roi: number;
  winRate: number;
  maxDD: number;
  sqn: number;
  trades: number;
  pf: number;
}

/* ─── Constants ─────────────────────────────────────────────────────── */

const PERIODS = ["allTime", "12m", "6m", "3m"] as const;
type Period = (typeof PERIODS)[number];

const PERIOD_DATA: Record<Period, PeriodData> = {
  allTime: { roi: 14.49, winRate: 67.9, maxDD: 1.42, sqn: 3.45, trades: 112, pf: 2.12 },
  "12m": { roi: 9.8, winRate: 69.2, maxDD: 1.18, sqn: 3.21, trades: 78, pf: 2.31 },
  "6m": { roi: 5.1, winRate: 71.4, maxDD: 0.95, sqn: 2.87, trades: 42, pf: 2.48 },
  "3m": { roi: 2.3, winRate: 68.5, maxDD: 0.82, sqn: 2.15, trades: 19, pf: 1.95 },
};

const TR_POINTS = [
  0, 0.8, 1.5, 2.8, 3.2, 4.1, 3.8, 5.2, 6.1, 6.8, 7.5, 8.2, 9.0, 9.8, 10.2, 9.5, 10.8,
  11.2, 11.8, 12.1, 12.8, 13.0, 13.5, 13.8, 14.2, 14.49,
];

const BTC_POINTS = [
  0, 5, 12, 18, 25, 35, 48, 52, 45, 38, 30, 22, 15, 8, 2, -5, -12, -18, -22, -25, -28, -30,
  -32, -35, -37, -38.88,
];

const MONTH_LABELS = ["Jan 24", "Jul 24", "Jan 25", "Jul 25", "Jan 26", "Mar 26"];
const MONTH_LABEL_INDICES = [0, 6, 12, 18, 24, 25];

const CHART_W = 800;
const CHART_H = 400;
const CHART_PAD = { top: 30, right: 20, bottom: 40, left: 60 };
const PLOT_W = CHART_W - CHART_PAD.left - CHART_PAD.right;
const PLOT_H = CHART_H - CHART_PAD.top - CHART_PAD.bottom;

const Y_MIN = -50;
const Y_MAX = 60;
const Y_RANGE = Y_MAX - Y_MIN;

const GRID_LINES = [-40, -20, 0, 20, 40];

/* ─── Helpers ───────────────────────────────────────────────────────── */

function easeOutCubic(x: number): number {
  return 1 - Math.pow(1 - x, 3);
}

function formatNum(n: number, decimals = 2): string {
  return n.toLocaleString("en-US", { minimumFractionDigits: decimals, maximumFractionDigits: decimals });
}

/** Convert data points to SVG coordinates within the plot area */
function toSVG(index: number, value: number, totalPoints: number): [number, number] {
  const x = CHART_PAD.left + (index / (totalPoints - 1)) * PLOT_W;
  const y = CHART_PAD.top + PLOT_H - ((value - Y_MIN) / Y_RANGE) * PLOT_H;
  return [x, y];
}

/** Catmull-Rom to cubic bezier conversion for smooth curves */
function catmullRomToBezierPath(points: [number, number][], tension = 0.5): string {
  if (points.length < 2) return "";
  const n = points.length;
  let d = `M${points[0][0].toFixed(1)},${points[0][1].toFixed(1)}`;

  for (let i = 0; i < n - 1; i++) {
    const p0 = points[Math.max(0, i - 1)];
    const p1 = points[i];
    const p2 = points[i + 1];
    const p3 = points[Math.min(n - 1, i + 2)];

    const cp1x = p1[0] + ((p2[0] - p0[0]) / 6) * tension;
    const cp1y = p1[1] + ((p2[1] - p0[1]) / 6) * tension;
    const cp2x = p2[0] - ((p3[0] - p1[0]) / 6) * tension;
    const cp2y = p2[1] - ((p3[1] - p1[1]) / 6) * tension;

    d += ` C${cp1x.toFixed(1)},${cp1y.toFixed(1)} ${cp2x.toFixed(1)},${cp2y.toFixed(1)} ${p2[0].toFixed(1)},${p2[1].toFixed(1)}`;
  }
  return d;
}

function buildAreaPath(linePath: string, points: [number, number][]): string {
  const first = points[0];
  const last = points[points.length - 1];
  const baseY = CHART_PAD.top + PLOT_H - ((0 - Y_MIN) / Y_RANGE) * PLOT_H;
  return `${linePath} L${last[0].toFixed(1)},${baseY.toFixed(1)} L${first[0].toFixed(1)},${baseY.toFixed(1)} Z`;
}

/* ─── Animated Counter Hook ─────────────────────────────────────────── */

function useAnimatedValue(target: number, active: boolean, duration = 1500, decimals = 2): number {
  const [value, setValue] = useState(0);
  const rafRef = useRef<number>(0);

  useEffect(() => {
    if (!active) {
      setValue(0);
      return;
    }
    const start = performance.now();
    const animate = (now: number) => {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      const eased = easeOutCubic(progress);
      setValue(parseFloat((target * eased).toFixed(decimals)));
      if (progress < 1) {
        rafRef.current = requestAnimationFrame(animate);
      }
    };
    rafRef.current = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(rafRef.current);
  }, [target, active, duration, decimals]);

  return value;
}

/* ─── Sub-components ────────────────────────────────────────────────── */

function HeroMetricCard({
  label,
  value,
  suffix,
  prefix,
  color,
  visible,
  delay,
}: {
  label: string;
  value: number;
  suffix?: string;
  prefix?: string;
  color: string;
  visible: boolean;
  delay: number;
}) {
  const animated = useAnimatedValue(value, visible, 1500, value % 1 === 0 ? 0 : 2);
  const glowColor = color === "#00D4AA" ? "rgba(0,212,170,0.3)" : "rgba(255,215,0,0.3)";

  return (
    <div
      className="reveal bg-card/50 border border-border/50 rounded-2xl p-6 backdrop-blur-sm transition-all duration-300 hover:scale-[1.02] group"
      style={{
        opacity: visible ? 1 : 0,
        transform: visible ? "translateY(0)" : "translateY(20px)",
        transitionDelay: `${delay}s`,
      }}
      onMouseEnter={(e) => {
        (e.currentTarget as HTMLElement).style.boxShadow = `0 0 30px ${glowColor}`;
      }}
      onMouseLeave={(e) => {
        (e.currentTarget as HTMLElement).style.boxShadow = "none";
      }}
    >
      <span className="block font-mono uppercase tracking-wider text-muted text-xs mb-2">
        {label}
      </span>
      <span
        className="block text-3xl md:text-4xl font-bold font-mono transition-colors duration-300"
        style={{ color }}
      >
        {prefix}
        {value % 1 === 0 ? animated.toFixed(0) : animated.toFixed(2)}
        {suffix}
      </span>
    </div>
  );
}

/* ─── Main Component ────────────────────────────────────────────────── */

export function PerformanceDashboard({ t, visible, sectionRef }: PerformanceDashboardProps) {
  const [period, setPeriod] = useState<Period>("allTime");
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);
  const [lineAnimated, setLineAnimated] = useState(false);
  const svgRef = useRef<SVGSVGElement>(null);

  const data = PERIOD_DATA[period];

  // Trigger line animation when visible
  useEffect(() => {
    if (visible) {
      const timer = setTimeout(() => setLineAnimated(true), 300);
      return () => clearTimeout(timer);
    } else {
      setLineAnimated(false);
    }
  }, [visible]);

  // Period label map
  const periodLabels: Record<Period, string> = {
    allTime: t.perfAllTime ?? "All Time",
    "12m": t.perf12m ?? "12 Months",
    "6m": t.perf6m ?? "6 Months",
    "3m": t.perf3m ?? "3 Months",
  };

  /* ── Chart computations ── */
  const trSVGPoints: [number, number][] = TR_POINTS.map((v, i) => toSVG(i, v, TR_POINTS.length));
  const btcSVGPoints: [number, number][] = BTC_POINTS.map((v, i) => toSVG(i, v, BTC_POINTS.length));

  const trPath = catmullRomToBezierPath(trSVGPoints);
  const btcPath = catmullRomToBezierPath(btcSVGPoints);

  const trAreaPath = buildAreaPath(trPath, trSVGPoints);
  const btcAreaPath = buildAreaPath(btcPath, btcSVGPoints);

  // Stroke lengths for draw animation
  const totalLen = 2000;

  /* ── Mouse handlers for chart tooltip ── */
  const handleMouseMove = useCallback(
    (e: React.MouseEvent<SVGSVGElement>) => {
      const svg = svgRef.current;
      if (!svg) return;
      const rect = svg.getBoundingClientRect();
      const mouseX = ((e.clientX - rect.left) / rect.width) * CHART_W;
      const relX = mouseX - CHART_PAD.left;
      if (relX < 0 || relX > PLOT_W) {
        setHoverIndex(null);
        return;
      }
      const idx = Math.round((relX / PLOT_W) * (TR_POINTS.length - 1));
      setHoverIndex(Math.max(0, Math.min(TR_POINTS.length - 1, idx)));
    },
    [],
  );

  const handleMouseLeave = useCallback(() => setHoverIndex(null), []);

  /* ── Capital Protection scenario ── */
  const MARKET_DROP = 0.3888;
  const DEPOSIT = 10000;
  const marketValue = DEPOSIT * (1 - MARKET_DROP);
  const trValue = DEPOSIT * (1 - data.maxDD / 100);
  const saved = trValue - marketValue;
  const marketBarWidth = (marketValue / trValue) * 100;
  const trBarWidth = 100;

  const animatedMarketValue = useAnimatedValue(marketValue, visible, 1500, 0);
  const animatedTrValue = useAnimatedValue(trValue, visible, 1500, 0);
  const animatedSaved = useAnimatedValue(saved, visible, 1500, 0);
  const animatedMarketLoss = useAnimatedValue(DEPOSIT - marketValue, visible, 1500, 0);
  const animatedTrLoss = useAnimatedValue(DEPOSIT - trValue, visible, 1500, 0);

  /* ── Radar chart ── */
  const radarSize = 300;
  const radarCenter = radarSize / 2;
  const radarRadius = 110;

  const radarAxes = [
    { label: t.perfProfitability ?? "Profitability", angle: -90 },
    { label: t.perfConsistency ?? "Consistency", angle: 30 },
    { label: t.perfRiskMgmt ?? "Risk Management", angle: 150 },
  ];

  const trRadar = [0.85, 0.78, 0.95];
  const avgRadar = [0.5, 0.45, 0.4];

  function radarPoint(value: number, angleDeg: number): [number, number] {
    const rad = (angleDeg * Math.PI) / 180;
    return [radarCenter + value * radarRadius * Math.cos(rad), radarCenter + value * radarRadius * Math.sin(rad)];
  }

  function radarPolygon(values: number[]): string {
    return values
      .map((v, i) => {
        const [x, y] = radarPoint(v, radarAxes[i].angle);
        return `${x.toFixed(1)},${y.toFixed(1)}`;
      })
      .join(" ");
  }

  /* ── Month name for tooltip ── */
  const monthNames = [
    "Jan 24", "Feb 24", "Mar 24", "Apr 24", "May 24", "Jun 24",
    "Jul 24", "Aug 24", "Sep 24", "Oct 24", "Nov 24", "Dec 24",
    "Jan 25", "Feb 25", "Mar 25", "Apr 25", "May 25", "Jun 25",
    "Jul 25", "Aug 25", "Sep 25", "Oct 25", "Nov 25", "Dec 25",
    "Jan 26", "Feb 26", "Mar 26",
  ];

  return (
    <section
      ref={sectionRef}
      id="performance"
      className="relative py-24 px-4 overflow-hidden"
      aria-label="Performance Dashboard"
    >
      {/* Background glow */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_60%_40%_at_50%_30%,rgba(0,212,170,0.05)_0%,transparent_70%)] pointer-events-none" />

      <div className="max-w-6xl mx-auto relative z-10">
        <SectionHeading
          tag={t.perfTag ?? "Performance"}
          title={t.perfTitle ?? "Verified Backtest Results"}
          subtitle={t.perfSubtitle ?? "26 months of real data across all market conditions"}
          visible={visible}
        />

        {/* ════════════════════════════════════════════════════════════
            SECTION 1: Period Tabs + Hero Metrics
           ════════════════════════════════════════════════════════════ */}

        {/* Period selector */}
        <div
          className="flex justify-center gap-2 mb-10"
          style={{
            opacity: visible ? 1 : 0,
            transform: visible ? "translateY(0)" : "translateY(12px)",
            transition: "all 0.5s ease 0.3s",
          }}
          role="tablist"
          aria-label="Performance period"
        >
          {PERIODS.map((p) => (
            <button
              key={p}
              role="tab"
              aria-selected={period === p}
              onClick={() => setPeriod(p)}
              className={`px-4 py-2 rounded-full text-sm font-mono transition-all duration-300 border ${
                period === p
                  ? "bg-primary/20 border-primary text-primary"
                  : "border-border/50 text-muted hover:text-foreground hover:border-border"
              }`}
            >
              {periodLabels[p]}
            </button>
          ))}
        </div>

        {/* Hero metric cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-20">
          <HeroMetricCard
            label={t.perfRoi ?? "ROI"}
            value={data.roi}
            prefix="+"
            suffix="%"
            color="#00D4AA"
            visible={visible}
            delay={0.4}
          />
          <HeroMetricCard
            label={t.perfWinRate ?? "Win Rate"}
            value={data.winRate}
            suffix="%"
            color="#00D4AA"
            visible={visible}
            delay={0.5}
          />
          <HeroMetricCard
            label={t.perfMaxDD ?? "Max Drawdown"}
            value={data.maxDD}
            suffix="%"
            color="#FFD700"
            visible={visible}
            delay={0.6}
          />
          <HeroMetricCard
            label={t.perfSQN ?? "SQN"}
            value={data.sqn}
            color="#FFD700"
            visible={visible}
            delay={0.7}
          />
        </div>

        {/* ════════════════════════════════════════════════════════════
            SECTION 2: Interactive Equity Curve
           ════════════════════════════════════════════════════════════ */}

        <div
          className="mb-20"
          style={{
            opacity: visible ? 1 : 0,
            transform: visible ? "translateY(0)" : "translateY(24px)",
            transition: "all 0.7s ease 0.5s",
          }}
        >
          {/* Legend */}
          <div className="flex justify-end gap-6 mb-4 pr-2">
            <span className="flex items-center gap-2 text-xs font-mono text-muted">
              <span className="w-3 h-3 rounded-full bg-[#00D4AA] inline-block" />
              {t.perfTrendRider ?? "TrendRider"}
            </span>
            <span className="flex items-center gap-2 text-xs font-mono text-muted/60">
              <span className="w-3 h-3 rounded-full bg-[#8B95A5]/50 inline-block" />
              {t.perfBTC ?? "BTC Buy & Hold"}
            </span>
          </div>

          {/* SVG Chart — lazy-rendered when scrolled into view */}
          <div className="relative rounded-2xl border border-border/50 bg-card/30 backdrop-blur-sm p-4 overflow-hidden">
            {visible ? (
            <svg
              ref={svgRef}
              viewBox={`0 0 ${CHART_W} ${CHART_H}`}
              className="w-full h-auto cursor-crosshair"
              preserveAspectRatio="xMidYMid meet"
              onMouseMove={handleMouseMove}
              onMouseLeave={handleMouseLeave}
              aria-label="Equity curve chart comparing TrendRider vs BTC Buy and Hold"
              role="img"
            >
              <title>TrendRider Performance Chart</title>
              <desc>Equity curve comparing TrendRider strategy returns vs BTC buy-and-hold over time</desc>
              <defs>
                {/* TrendRider line gradient */}
                <linearGradient id="trLineGrad" x1="0" y1="0" x2="1" y2="0">
                  <stop offset="0%" stopColor="#00D4AA" />
                  <stop offset="100%" stopColor="#00FFD0" />
                </linearGradient>
                {/* TrendRider area gradient */}
                <linearGradient id="trAreaGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#00D4AA" stopOpacity="0.2" />
                  <stop offset="100%" stopColor="#00D4AA" stopOpacity="0" />
                </linearGradient>
                {/* BTC area gradient — dimmed */}
                <linearGradient id="btcAreaGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#8B95A5" stopOpacity="0.05" />
                  <stop offset="100%" stopColor="#8B95A5" stopOpacity="0" />
                </linearGradient>
              </defs>

              {/* Horizontal grid lines */}
              {GRID_LINES.map((val) => {
                const y = CHART_PAD.top + PLOT_H - ((val - Y_MIN) / Y_RANGE) * PLOT_H;
                return (
                  <g key={val}>
                    <line
                      x1={CHART_PAD.left}
                      y1={y}
                      x2={CHART_W - CHART_PAD.right}
                      y2={y}
                      stroke="#30363D"
                      strokeWidth="0.5"
                      strokeDasharray="4 6"
                    />
                    <text
                      x={CHART_PAD.left - 8}
                      y={y + 4}
                      textAnchor="end"
                      fill="#8B95A5"
                      fontSize="11"
                      fontFamily="monospace"
                    >
                      {val > 0 ? `+${val}%` : `${val}%`}
                    </text>
                  </g>
                );
              })}

              {/* X-axis labels */}
              {MONTH_LABEL_INDICES.map((idx, i) => {
                const x = CHART_PAD.left + (idx / (TR_POINTS.length - 1)) * PLOT_W;
                return (
                  <text
                    key={i}
                    x={x}
                    y={CHART_H - 8}
                    textAnchor="middle"
                    fill="#8B95A5"
                    fontSize="11"
                    fontFamily="monospace"
                  >
                    {MONTH_LABELS[i]}
                  </text>
                );
              })}

              {/* Zero line (slightly brighter) */}
              <line
                x1={CHART_PAD.left}
                y1={CHART_PAD.top + PLOT_H - ((0 - Y_MIN) / Y_RANGE) * PLOT_H}
                x2={CHART_W - CHART_PAD.right}
                y2={CHART_PAD.top + PLOT_H - ((0 - Y_MIN) / Y_RANGE) * PLOT_H}
                stroke="#484F58"
                strokeWidth="1"
              />

              {/* BTC area fill */}
              <path d={btcAreaPath} fill="url(#btcAreaGrad)" opacity={lineAnimated ? 1 : 0} style={{ transition: "opacity 1s ease 0.5s" }} />

              {/* TrendRider area fill */}
              <path d={trAreaPath} fill="url(#trAreaGrad)" opacity={lineAnimated ? 1 : 0} style={{ transition: "opacity 1s ease 0.5s" }} />

              {/* BTC line — dimmed reference */}
              <path
                d={btcPath}
                fill="none"
                stroke="#8B95A5"
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
                opacity="0.4"
                strokeDasharray={totalLen}
                strokeDashoffset={lineAnimated ? 0 : totalLen}
                style={{ transition: "stroke-dashoffset 2s ease-out 0.3s" }}
              />

              {/* TrendRider line — hero */}
              <path
                d={trPath}
                fill="none"
                stroke="url(#trLineGrad)"
                strokeWidth="3"
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeDasharray={totalLen}
                strokeDashoffset={lineAnimated ? 0 : totalLen}
                style={{ transition: "stroke-dashoffset 2s ease-out 0.3s" }}
              />

              {/* Hover crosshair + tooltip */}
              {hoverIndex !== null && (
                <>
                  <line
                    x1={trSVGPoints[hoverIndex][0]}
                    y1={CHART_PAD.top}
                    x2={trSVGPoints[hoverIndex][0]}
                    y2={CHART_PAD.top + PLOT_H}
                    stroke="#8B95A5"
                    strokeWidth="1"
                    strokeDasharray="4 4"
                    opacity="0.6"
                  />
                  {/* TR dot */}
                  <circle
                    cx={trSVGPoints[hoverIndex][0]}
                    cy={trSVGPoints[hoverIndex][1]}
                    r="5"
                    fill="#00D4AA"
                    stroke="#0D1117"
                    strokeWidth="2"
                  />
                  {/* BTC dot — dimmed */}
                  <circle
                    cx={btcSVGPoints[hoverIndex][0]}
                    cy={btcSVGPoints[hoverIndex][1]}
                    r="4"
                    fill="#8B95A5"
                    stroke="#0D1117"
                    strokeWidth="2"
                    opacity="0.6"
                  />
                  {/* Tooltip background */}
                  {(() => {
                    const tx = Math.min(trSVGPoints[hoverIndex][0] - 100, CHART_W - 230);
                    const ty = CHART_PAD.top - 5;
                    return (
                      <g>
                        <rect
                          x={Math.max(CHART_PAD.left, tx)}
                          y={ty - 18}
                          width={210}
                          height={24}
                          rx={6}
                          fill="#161B22"
                          stroke="#30363D"
                          strokeWidth="1"
                          opacity="0.95"
                        />
                        <text
                          x={Math.max(CHART_PAD.left + 6, tx + 6)}
                          y={ty - 1}
                          fill="#E6EDF3"
                          fontSize="10"
                          fontFamily="monospace"
                        >
                          {monthNames[hoverIndex] ?? `M${hoverIndex}`}
                          {" | "}
                          <tspan fill="#00D4AA">
                            TR: {TR_POINTS[hoverIndex] >= 0 ? "+" : ""}
                            {TR_POINTS[hoverIndex].toFixed(1)}%
                          </tspan>
                          {" | "}
                          <tspan fill="#8B95A5">
                            BTC: {BTC_POINTS[hoverIndex] >= 0 ? "+" : ""}
                            {BTC_POINTS[hoverIndex].toFixed(1)}%
                          </tspan>
                        </text>
                      </g>
                    );
                  })()}
                </>
              )}
            </svg>
            ) : (
              <div style={{ paddingBottom: `${(CHART_H / CHART_W) * 100}%` }} />
            )}
          </div>

          {/* Key insight banner */}
          <div
            className="mt-6 p-4 rounded-xl border-l-4 border-primary bg-gradient-to-r from-primary/10 to-transparent"
            style={{
              opacity: visible ? 1 : 0,
              transform: visible ? "translateX(0)" : "translateX(-20px)",
              transition: "all 0.6s ease 1.2s",
            }}
          >
            <p className="text-sm md:text-base font-medium text-foreground">
              {t.perfInsight ??
                "TrendRider generated +14.49% while protecting capital from a -38.88% market drop"}
            </p>
          </div>
        </div>

        {/* ════════════════════════════════════════════════════════════
            SECTION 3: Capital Protection
           ════════════════════════════════════════════════════════════ */}

        <div
          className="mb-20"
          style={{
            opacity: visible ? 1 : 0,
            transform: visible ? "translateY(0)" : "translateY(24px)",
            transition: "all 0.7s ease 0.8s",
          }}
        >
          {/* Section heading */}
          <div className="text-center mb-8">
            <h3 className="text-2xl md:text-3xl font-bold text-foreground mb-2">
              {t.perfCrashTitle ?? "What If the Market Crashes?"}
            </h3>
            <p className="text-sm text-muted">
              {t.perfCrashSubtitle ?? "Your capital stays protected while the market bleeds"}
            </p>
          </div>

          {/* Scenario text */}
          <p className="text-center text-base md:text-lg text-foreground/80 mb-10 font-mono">
            {t.perfCrashScenario ?? "Imagine: you invested $10,000. The market drops 40%."}
          </p>

          {/* Comparison bars */}
          <div className="max-w-2xl mx-auto space-y-8">
            {/* Without strategy bar */}
            <div>
              <div className="flex items-baseline justify-between mb-2">
                <span className="text-sm text-muted font-mono">{t.perfWithoutStrategy ?? "Without strategy"}</span>
                <div className="flex items-baseline gap-2">
                  <span className="text-xl md:text-2xl font-bold font-mono text-[#FF4757]">
                    ${animatedMarketValue.toLocaleString("en-US", { maximumFractionDigits: 0 })}
                  </span>
                  <span className="text-sm font-mono text-[#FF4757]/70">
                    (-${animatedMarketLoss.toLocaleString("en-US", { maximumFractionDigits: 0 })})
                  </span>
                </div>
              </div>
              <div className="relative h-3 rounded-full bg-[#1C1F26] overflow-hidden">
                <div
                  className="absolute inset-y-0 left-0 rounded-full bg-gradient-to-r from-[#FF4757] to-[#FF6B7A]"
                  style={{
                    width: visible ? `${marketBarWidth}%` : "0%",
                    transition: "width 1.5s cubic-bezier(0.22, 1, 0.36, 1) 0.3s",
                  }}
                />
              </div>
            </div>

            {/* With TrendRider bar */}
            <div>
              <div className="flex items-baseline justify-between mb-2">
                <span className="text-sm text-muted font-mono">{t.perfWithTrendRider ?? "With TrendRider"}</span>
                <div className="flex items-baseline gap-2">
                  <span className="text-xl md:text-2xl font-bold font-mono text-[#00D4AA]">
                    ${animatedTrValue.toLocaleString("en-US", { maximumFractionDigits: 0 })}
                  </span>
                  <span className="text-sm font-mono text-[#00D4AA]/70">
                    (-${animatedTrLoss.toLocaleString("en-US", { maximumFractionDigits: 0 })})
                  </span>
                </div>
              </div>
              <div className="relative h-3 rounded-full bg-[#1C1F26] overflow-hidden">
                <div
                  className="absolute inset-y-0 left-0 rounded-full bg-gradient-to-r from-[#00D4AA] to-[#00FFD0]"
                  style={{
                    width: visible ? `${trBarWidth}%` : "0%",
                    transition: "width 1.5s cubic-bezier(0.22, 1, 0.36, 1) 0.6s",
                  }}
                />
              </div>
            </div>

            {/* Saved amount */}
            <div
              className="text-center pt-2"
              style={{
                opacity: visible ? 1 : 0,
                transition: "opacity 0.6s ease 1.2s",
              }}
            >
              <span className="text-lg font-mono text-muted">
                {t.perfYouSaved ?? "You saved"}{" "}
              </span>
              <span className="text-2xl md:text-3xl font-bold font-mono text-[#FFD700]">
                ${animatedSaved.toLocaleString("en-US", { maximumFractionDigits: 0 })}
              </span>
            </div>
          </div>

          {/* Context metrics strip */}
          <div className="flex flex-wrap items-center justify-center gap-6 md:gap-10 mt-10">
            <div className="text-center">
              <span className="block text-2xl font-bold font-mono text-primary">{formatNum(data.maxDD)}%</span>
              <span className="text-xs text-muted font-mono uppercase tracking-wider">{t.perfMaxDD ?? "Max Drawdown"}</span>
            </div>
            <div className="w-px h-8 bg-border/30 hidden md:block" />
            <div className="text-center">
              <span className="block text-2xl font-bold font-mono text-primary">{formatNum(data.winRate, 1)}%</span>
              <span className="text-xs text-muted font-mono uppercase tracking-wider">{t.perfWinRate ?? "Win Rate"}</span>
            </div>
            <div className="w-px h-8 bg-border/30 hidden md:block" />
            <div className="text-center">
              <span className="block text-2xl font-bold font-mono text-primary">{formatNum(data.pf)}</span>
              <span className="text-xs text-muted font-mono uppercase tracking-wider">{t.perfProfitFactor ?? "Profit Factor"}</span>
            </div>
          </div>

          {/* Thesis */}
          <p
            className="text-center text-base md:text-lg font-medium text-foreground/90 mt-8 max-w-xl mx-auto"
            style={{
              opacity: visible ? 1 : 0,
              transition: "opacity 0.6s ease 1.4s",
            }}
          >
            {t.perfCrashTesis ?? "We don\u2019t promise extraordinary returns. We deliver extraordinary risk management."}
          </p>

          {/* Disclaimer */}
          <p className="text-center text-xs text-muted/60 mt-4 max-w-lg mx-auto leading-relaxed">
            {t.perfCrashDisclaimer ?? "Based on backtest max drawdown of 1.42%. Actual results may vary. Past performance does not guarantee future results."}
          </p>
        </div>

        {/* ════════════════════════════════════════════════════════════
            SECTION 4: Advanced Metrics (Expandable)
           ════════════════════════════════════════════════════════════ */}

        <div
          style={{
            opacity: visible ? 1 : 0,
            transition: "opacity 0.5s ease 1s",
          }}
        >
          <button
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="mx-auto flex items-center gap-2 px-6 py-3 rounded-xl border border-border/50 bg-card/30 text-muted hover:text-foreground hover:border-border transition-all duration-300 font-mono text-sm"
            aria-expanded={showAdvanced}
            aria-controls="advanced-metrics"
          >
            {t.perfAdvanced ?? "Advanced Metrics"}
            <svg
              width="14"
              height="14"
              viewBox="0 0 14 14"
              fill="none"
              className={`transition-transform duration-300 ${showAdvanced ? "rotate-180" : ""}`}
              aria-hidden="true"
            >
              <path d="M3 5L7 9L11 5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </button>

          <div
            id="advanced-metrics"
            className="overflow-hidden transition-all duration-500 ease-in-out"
            style={{
              maxHeight: showAdvanced ? "800px" : "0px",
              opacity: showAdvanced ? 1 : 0,
              marginTop: showAdvanced ? "2rem" : "0",
            }}
          >
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-10">
              {[
                { label: t.perfProfitFactor ?? "Profit Factor", value: "2.12", color: "#00D4AA" },
                { label: t.perfTotalTrades ?? "Total Trades", value: "112", color: "#E6EDF3" },
                { label: t.perfAvgTrade ?? "Avg Trade", value: "+0.13%", color: "#00D4AA" },
                { label: t.perfAvgDuration ?? "Avg Duration", value: "18h", color: "#E6EDF3" },
                { label: t.perfBestTrade ?? "Best Trade", value: "+4.2%", color: "#00D4AA" },
                { label: t.perfWorstTrade ?? "Worst Trade", value: "-1.8%", color: "#FF4757" },
              ].map((metric) => (
                <div
                  key={metric.label}
                  className="bg-card/50 border border-border/50 rounded-xl p-4 text-center transition-all duration-300 hover:border-border"
                >
                  <span className="block text-xs font-mono text-muted uppercase tracking-wider mb-1">
                    {metric.label}
                  </span>
                  <span
                    className="block text-xl font-bold font-mono"
                    style={{ color: metric.color }}
                  >
                    {metric.value}
                  </span>
                </div>
              ))}
            </div>

            {/* Radar Chart */}
            <div className="flex flex-col items-center">
              <svg
                width={radarSize}
                height={radarSize}
                viewBox={`0 0 ${radarSize} ${radarSize}`}
                className="mb-4"
                aria-label="Radar chart comparing TrendRider to average bot performance"
                role="img"
              >
                {/* Grid rings */}
                {[0.25, 0.5, 0.75, 1].map((scale) => (
                  <polygon
                    key={scale}
                    points={radarAxes
                      .map((a) => {
                        const [x, y] = radarPoint(scale, a.angle);
                        return `${x.toFixed(1)},${y.toFixed(1)}`;
                      })
                      .join(" ")}
                    fill="none"
                    stroke="#30363D"
                    strokeWidth="0.5"
                    opacity="0.6"
                  />
                ))}

                {/* Axis lines */}
                {radarAxes.map((a, i) => {
                  const [x, y] = radarPoint(1, a.angle);
                  return (
                    <line
                      key={i}
                      x1={radarCenter}
                      y1={radarCenter}
                      x2={x}
                      y2={y}
                      stroke="#30363D"
                      strokeWidth="0.5"
                    />
                  );
                })}

                {/* Average Bot polygon */}
                <polygon
                  points={radarPolygon(avgRadar)}
                  fill="rgba(255,255,255,0.05)"
                  stroke="rgba(255,255,255,0.3)"
                  strokeWidth="1.5"
                />

                {/* TrendRider polygon */}
                <polygon
                  points={radarPolygon(trRadar)}
                  fill="rgba(0,212,170,0.15)"
                  stroke="#00D4AA"
                  strokeWidth="2"
                />

                {/* Vertex dots - TrendRider */}
                {trRadar.map((v, i) => {
                  const [x, y] = radarPoint(v, radarAxes[i].angle);
                  return <circle key={i} cx={x} cy={y} r="4" fill="#00D4AA" stroke="#0D1117" strokeWidth="2" />;
                })}

                {/* Axis labels */}
                {radarAxes.map((a, i) => {
                  const labelDist = 1.2;
                  const [x, y] = radarPoint(labelDist, a.angle);
                  return (
                    <text
                      key={i}
                      x={x}
                      y={y}
                      textAnchor="middle"
                      dominantBaseline="middle"
                      fill="#8B95A5"
                      fontSize="11"
                      fontFamily="monospace"
                    >
                      {a.label}
                    </text>
                  );
                })}
              </svg>

              {/* Radar legend */}
              <div className="flex gap-6 text-xs font-mono text-muted">
                <span className="flex items-center gap-2">
                  <span className="w-3 h-3 rounded-full bg-[#00D4AA] inline-block" />
                  {t.perfTrendRider ?? "TrendRider"}
                </span>
                <span className="flex items-center gap-2">
                  <span className="w-3 h-3 rounded-full bg-white/30 inline-block" />
                  {t.perfAvgBot ?? "Average Bot"}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* ════════════════════════════════════════════════════════════
            DISCLAIMER
           ════════════════════════════════════════════════════════════ */}

        <p
          className="text-center text-xs text-muted/60 mt-16 max-w-2xl mx-auto leading-relaxed"
          style={{
            opacity: visible ? 1 : 0,
            transition: "opacity 0.5s ease 1.2s",
          }}
        >
          {t.perfDisclaimer ??
            "Past performance does not guarantee future results. All data shown is based on backtested results from January 2024 to March 2026. Actual trading involves risk of loss. Always do your own research before making investment decisions."}
        </p>
      </div>
    </section>
  );
}
