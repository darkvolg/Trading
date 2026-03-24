"use client";

import { useState, useEffect, useRef, useCallback, type RefObject } from "react";
import { SectionHeading } from "../ui";
import type { TStrings } from "@/lib/i18n";

/* ─── Types ─────────────────────────────────────────────────────────── */

interface SimulatedPerformanceProps {
  t: TStrings;
  visible: boolean;
  sectionRef: RefObject<HTMLDivElement | null>;
}

/* ─── Constants ─────────────────────────────────────────────────────── */

const CAPITAL_OPTIONS = [1_000, 5_000, 10_000, 25_000, 50_000] as const;

const TR_POINTS = [
  0, 0.8, 1.5, 2.8, 3.2, 4.1, 3.8, 5.2, 6.1, 6.8, 7.5, 8.2, 9.0, 9.8, 10.2, 9.5, 10.8,
  11.2, 11.8, 12.1, 12.8, 13.0, 13.5, 13.8, 14.2, 14.49,
];

const MONTH_LABELS = ["Jan 24", "Jul 24", "Jan 25", "Jul 25", "Mar 26"];
const MONTH_LABEL_INDICES = [0, 6, 12, 18, 25];

const CHART_W = 780;
const CHART_H = 380;
const CHART_PAD = { top: 30, right: 100, bottom: 48, left: 75 };
const CHART_FONT = "system-ui, sans-serif";
const PLOT_W = CHART_W - CHART_PAD.left - CHART_PAD.right;
const PLOT_H = CHART_H - CHART_PAD.top - CHART_PAD.bottom;

const METRICS = [
  { key: "simWinRate" as const, value: 67.9, suffix: "%", icon: "target" },
  { key: "simProfitFactor" as const, value: 2.12, suffix: "x", icon: "trending" },
  { key: "simMaxDD" as const, value: 1.42, suffix: "%", icon: "shield" },
  { key: "simSharpe" as const, value: 3.45, suffix: "", icon: "chart" },
];

const GREEN = "#00D4AA";
const LABEL_COLOR = "#ffffff";
const GRID_COLOR = "#ffffff";

/* ─── Helpers ───────────────────────────────────────────────────────── */

function catmullRomToBezier(points: [number, number][]): string {
  if (points.length < 2) return "";
  let d = `M${points[0][0]},${points[0][1]}`;
  for (let i = 0; i < points.length - 1; i++) {
    const p0 = points[Math.max(i - 1, 0)];
    const p1 = points[i];
    const p2 = points[i + 1];
    const p3 = points[Math.min(i + 2, points.length - 1)];
    const cp1x = p1[0] + (p2[0] - p0[0]) / 6;
    const cp1y = p1[1] + (p2[1] - p0[1]) / 6;
    const cp2x = p2[0] - (p3[0] - p1[0]) / 6;
    const cp2y = p2[1] - (p3[1] - p1[1]) / 6;
    d += ` C${cp1x},${cp1y} ${cp2x},${cp2y} ${p2[0]},${p2[1]}`;
  }
  return d;
}

function formatDollar(value: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(value);
}

function formatDollarShort(value: number): string {
  if (value >= 1_000) {
    return `$${(value / 1_000).toFixed(value % 1_000 === 0 ? 0 : 1)}K`;
  }
  return formatDollar(value);
}

/* ─── Animated Counter Hook ─────────────────────────────────────────── */

function useAnimatedValue(target: number, trigger: boolean, duration = 1200): number {
  const [value, setValue] = useState(0);

  useEffect(() => {
    if (!trigger) {
      setValue(0);
      return;
    }

    const start = performance.now();
    let raf: number;
    const animate = (now: number) => {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setValue(target * eased);
      if (progress < 1) raf = requestAnimationFrame(animate);
    };
    raf = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(raf);
  }, [target, trigger, duration]);

  return value;
}

/* ─── Metric Icons ──────────────────────────────────────────────────── */

function MetricIcon({ type }: { type: string }) {
  const cls = "w-6 h-6 text-primary";
  switch (type) {
    case "target":
      return (
        <svg className={cls} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
          <circle cx="12" cy="12" r="10" />
          <circle cx="12" cy="12" r="6" />
          <circle cx="12" cy="12" r="2" />
        </svg>
      );
    case "trending":
      return (
        <svg className={cls} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
          <polyline points="23 6 13.5 15.5 8.5 10.5 1 18" />
          <polyline points="17 6 23 6 23 12" />
        </svg>
      );
    case "shield":
      return (
        <svg className={cls} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
          <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
        </svg>
      );
    case "chart":
      return (
        <svg className={cls} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
          <line x1="18" y1="20" x2="18" y2="10" />
          <line x1="12" y1="20" x2="12" y2="4" />
          <line x1="6" y1="20" x2="6" y2="14" />
        </svg>
      );
    default:
      return null;
  }
}

/* ─── Component ─────────────────────────────────────────────────────── */

export function SimulatedPerformance({ t, visible, sectionRef }: SimulatedPerformanceProps) {
  const [capital, setCapital] = useState(10_000);
  const [pathLength, setPathLength] = useState(0);
  const pathRef = useRef<SVGPathElement>(null);

  /* ── Dollar data points ── */
  const dollarPoints = TR_POINTS.map((p) => capital * (1 + p / 100));
  const finalValue = Math.round(capital * 1.1449);
  const netProfit = finalValue - capital;
  const profitPct = ((netProfit / capital) * 100).toFixed(2);

  /* ── Chart scale: Y from 0 to dynamic max, fills chart nicely for any capital ── */
  const yMin = 0;
  const yMax = Math.ceil((finalValue * 1.35) / 1000) * 1000; // round up to nearest $1K
  const yRange = yMax - yMin;

  const scaleX = useCallback(
    (i: number) => CHART_PAD.left + (i / (TR_POINTS.length - 1)) * PLOT_W,
    [],
  );
  const scaleY = useCallback(
    (val: number) => CHART_PAD.top + PLOT_H - ((val - yMin) / yRange) * PLOT_H,
    [yRange],
  );

  /* ── SVG points for total value curve ── */
  const svgPoints: [number, number][] = dollarPoints.map((val, i) => [scaleX(i), scaleY(val)]);
  const curvePath = catmullRomToBezier(svgPoints);

  /* ── Capital baseline Y position ── */
  const capitalY = scaleY(capital);

  /* ── Profit area: between curve and capital baseline ── */
  const profitFillPath =
    curvePath +
    ` L${svgPoints[svgPoints.length - 1][0]},${capitalY}` +
    ` L${svgPoints[0][0]},${capitalY} Z`;

  /* ── Capital area: between capital baseline and bottom ── */
  const bottomY = CHART_PAD.top + PLOT_H;
  const capitalFillPath =
    `M${CHART_PAD.left},${capitalY}` +
    ` L${CHART_PAD.left + PLOT_W},${capitalY}` +
    ` L${CHART_PAD.left + PLOT_W},${bottomY}` +
    ` L${CHART_PAD.left},${bottomY} Z`;

  /* ── Y-axis grid values — always show exact capital amount ── */
  const gridValues = capital >= 10_000
    ? [0, Math.round(capital / 2), capital, finalValue]
    : [0, capital, finalValue];

  /* ── Measure path length for stroke animation ── */
  useEffect(() => {
    if (pathRef.current) {
      setPathLength(pathRef.current.getTotalLength());
    }
  }, [capital]);

  /* ── Animated metrics ── */
  const animWinRate = useAnimatedValue(67.9, visible);
  const animPF = useAnimatedValue(2.12, visible);
  const animDD = useAnimatedValue(1.42, visible);
  const animSharpe = useAnimatedValue(3.45, visible);
  const animatedMetrics = [animWinRate, animPF, animDD, animSharpe];

  return (
    <section
      ref={sectionRef}
      className="relative py-24 md:py-32 overflow-hidden"
    >
      <div className="max-w-6xl mx-auto px-4 sm:px-6">
        {/* ── Header ── */}
        <SectionHeading
          tag={t.simTag}
          title={t.simTitle}
          subtitle={t.simSubtitle}
          visible={visible}
        />

        {/* ── Capital Selector ── */}
        <div
          className={`reveal ${visible ? "visible" : ""} flex flex-wrap justify-center gap-2 sm:gap-3 mb-10`}
          style={{ transitionDelay: visible ? "0.3s" : "0s" }}
        >
          {CAPITAL_OPTIONS.map((opt) => (
            <button
              key={opt}
              onClick={() => setCapital(opt)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 focus:ring-2 focus:ring-primary/50 focus:outline-none ${
                capital === opt
                  ? "bg-primary text-black shadow-lg shadow-primary/25"
                  : "bg-card border border-border/50 text-muted hover:border-primary/30 hover:text-foreground"
              }`}
            >
              {formatDollarShort(opt)}
            </button>
          ))}
        </div>

        {/* ── Stacked Area Chart ── */}
        <div
          className={`reveal ${visible ? "visible" : ""} relative mx-auto max-w-3xl mb-10`}
          style={{ transitionDelay: visible ? "0.4s" : "0s" }}
        >
          <div className="bg-card/50 border border-border/50 rounded-2xl p-4 sm:p-6 backdrop-blur-sm">
            <svg
              key={capital}
              viewBox={`0 0 ${CHART_W} ${CHART_H}`}
              className="w-full h-auto"
              preserveAspectRatio="xMidYMid meet"
              role="img"
              aria-label="Equity curve chart"
            >
              <defs>
                <linearGradient id="sim-profit-gradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={GREEN} stopOpacity={0.35} />
                  <stop offset="100%" stopColor={GREEN} stopOpacity={0.08} />
                </linearGradient>
              </defs>

              {/* Grid lines + Y-axis labels */}
              {gridValues.map((val, i) => {
                const y = scaleY(val);
                return (
                  <g key={i}>
                    <line
                      x1={CHART_PAD.left}
                      y1={y}
                      x2={CHART_W - CHART_PAD.right}
                      y2={y}
                      stroke={GRID_COLOR}
                      strokeOpacity={0.08}
                      strokeDasharray="4 4"
                    />
                    <text
                      x={CHART_PAD.left - 10}
                      y={y + 4}
                      textAnchor="end"
                      fill={LABEL_COLOR}
                      fontSize={12}
                      fontWeight={500}
                      fontFamily={CHART_FONT}
                      opacity={0.7}
                    >
                      {formatDollar(Math.round(val))}
                    </text>
                  </g>
                );
              })}

              {/* X-axis labels */}
              {MONTH_LABEL_INDICES.map((idx, i) => (
                <text
                  key={i}
                  x={scaleX(idx)}
                  y={CHART_H - 12}
                  textAnchor="middle"
                  fill={LABEL_COLOR}
                  fontSize={12}
                  fontWeight={500}
                  fontFamily={CHART_FONT}
                  opacity={0.7}
                >
                  {MONTH_LABELS[i]}
                </text>
              ))}

              {/* Capital baseline area (gray) */}
              <path
                d={capitalFillPath}
                fill={LABEL_COLOR}
                opacity={visible ? 0.04 : 0}
                style={{ transition: "opacity 0.8s ease 0.3s" }}
              />

              {/* Capital baseline dashed line */}
              <line
                x1={CHART_PAD.left}
                y1={capitalY}
                x2={CHART_PAD.left + PLOT_W}
                y2={capitalY}
                stroke={LABEL_COLOR}
                strokeOpacity={visible ? 0.2 : 0}
                strokeWidth={1}
                strokeDasharray="6 4"
                style={{ transition: "stroke-opacity 0.6s ease 0.5s" }}
              />

              {/* Capital baseline label */}
              <text
                x={CHART_PAD.left + PLOT_W + 12}
                y={capitalY + 4}
                textAnchor="start"
                fill={LABEL_COLOR}
                fontSize={10}
                fontWeight={500}
                fontFamily={CHART_FONT}
                opacity={visible ? 0.4 : 0}
                style={{ transition: "opacity 0.6s ease 0.5s" }}
              >
                {t.simCapital}
              </text>

              {/* Profit area (green gradient) */}
              <path
                d={profitFillPath}
                fill="url(#sim-profit-gradient)"
                opacity={visible ? 1 : 0}
                style={{ transition: "opacity 0.8s ease 0.6s" }}
              />

              {/* Profit label on green zone */}
              <text
                x={(svgPoints[12][0] + svgPoints[20][0]) / 2}
                y={(svgPoints[16][1] + capitalY) / 2 + 5}
                textAnchor="middle"
                fill={GREEN}
                fontSize={16}
                fontWeight={700}
                fontFamily={CHART_FONT}
                opacity={visible ? 0.7 : 0}
                style={{ transition: "opacity 0.8s ease 1.5s" }}
              >
                +{formatDollar(netProfit)}
              </text>

              {/* Total value curve line */}
              <path
                ref={pathRef}
                d={curvePath}
                fill="none"
                stroke={GREEN}
                strokeWidth={2.5}
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeDasharray={pathLength || 1200}
                strokeDashoffset={visible ? 0 : pathLength || 1200}
                style={{
                  transition: visible
                    ? "stroke-dashoffset 2s cubic-bezier(0.4, 0, 0.2, 1) 0.5s"
                    : "none",
                }}
              />

              {/* Start point */}
              <circle
                cx={svgPoints[0][0]}
                cy={svgPoints[0][1]}
                r={3.5}
                fill={GREEN}
                opacity={visible ? 0.8 : 0}
                style={{ transition: "opacity 0.4s ease 1s" }}
              />

              {/* End point glow + dot */}
              <circle
                cx={svgPoints[svgPoints.length - 1][0]}
                cy={svgPoints[svgPoints.length - 1][1]}
                r={10}
                fill={GREEN}
                opacity={visible ? 0.15 : 0}
                style={{ transition: "opacity 0.4s ease 2.4s" }}
              />
              <circle
                cx={svgPoints[svgPoints.length - 1][0]}
                cy={svgPoints[svgPoints.length - 1][1]}
                r={4.5}
                fill={GREEN}
                opacity={visible ? 1 : 0}
                style={{ transition: "opacity 0.4s ease 2.4s" }}
              />

              {/* End annotation pill — positioned in right margin */}
              <g
                opacity={visible ? 1 : 0}
                style={{ transition: "opacity 0.5s ease 2.5s" }}
              >
                <rect
                  x={svgPoints[svgPoints.length - 1][0] + 12}
                  y={svgPoints[svgPoints.length - 1][1] - 16}
                  width={80}
                  height={28}
                  rx={14}
                  fill={GREEN}
                  fillOpacity={0.15}
                  stroke={GREEN}
                  strokeOpacity={0.5}
                  strokeWidth={1}
                />
                <text
                  x={svgPoints[svgPoints.length - 1][0] + 52}
                  y={svgPoints[svgPoints.length - 1][1] + 2}
                  textAnchor="middle"
                  fill={GREEN}
                  fontSize={13}
                  fontWeight={700}
                  fontFamily={CHART_FONT}
                >
                  {formatDollar(finalValue)}
                </text>
              </g>
            </svg>
          </div>
        </div>

        {/* ── Result Cards Row (3 cards) ── */}
        <div
          className={`reveal ${visible ? "visible" : ""} grid grid-cols-1 sm:grid-cols-3 gap-3 sm:gap-4 max-w-3xl mx-auto mb-10`}
          style={{ transitionDelay: visible ? "0.6s" : "0s" }}
        >
          {/* Starting Capital */}
          <div
            key={`start-${capital}`}
            className="bg-card/30 border border-border/50 rounded-xl p-5 text-center transition-all duration-300 hover:border-primary/30 animate-in fade-in duration-500"
          >
            <p className="text-xs text-muted uppercase tracking-wide mb-2">
              {t.simStarting}
            </p>
            <p className="text-xl sm:text-2xl font-bold text-foreground">
              {formatDollar(capital)}
            </p>
          </div>

          {/* Final Value - highlighted */}
          <div
            key={`final-${capital}`}
            className="bg-card/30 border border-primary/30 rounded-xl p-5 text-center transition-all duration-300 hover:border-primary/50 animate-in fade-in duration-500"
          >
            <p className="text-xs text-muted uppercase tracking-wide mb-2">
              {t.simFinalValue}
            </p>
            <p className="text-xl sm:text-2xl font-bold text-primary">
              {formatDollar(finalValue)}
            </p>
          </div>

          {/* Net Profit */}
          <div
            key={`profit-${capital}`}
            className="bg-card/30 border border-border/50 rounded-xl p-5 text-center transition-all duration-300 hover:border-primary/30 animate-in fade-in duration-500"
          >
            <p className="text-xs text-muted uppercase tracking-wide mb-2">
              {t.simNetProfit}
            </p>
            <p className="text-xl sm:text-2xl font-bold text-primary">
              <span className="inline-flex items-center gap-1">
                <svg className="w-4 h-4" viewBox="0 0 16 16" fill="none" aria-hidden="true">
                  <path d="M8 12V4M8 4L4 8M8 4L12 8" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" />
                </svg>
                +{formatDollar(netProfit)}
              </span>
              <span className="block text-sm font-medium text-primary/70 mt-0.5">
                +{profitPct}%
              </span>
            </p>
          </div>
        </div>

        {/* ── Metric Cards ── */}
        <div
          className={`reveal ${visible ? "visible" : ""} grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 max-w-3xl mx-auto mb-10`}
          style={{ transitionDelay: visible ? "0.7s" : "0s" }}
        >
          {METRICS.map((metric, i) => {
            const animVal = animatedMetrics[i];
            const decimals = metric.key === "simWinRate" ? 1 : 2;
            return (
              <div
                key={metric.key}
                className="bg-card/30 border border-border/50 rounded-xl p-4 text-center transition-all duration-300 hover:border-primary/30 hover:bg-card/50"
              >
                <div className="flex justify-center mb-2">
                  <MetricIcon type={metric.icon} />
                </div>
                <p className="text-2xl sm:text-3xl font-bold text-foreground mb-1">
                  {animVal.toFixed(decimals)}
                  {metric.suffix}
                </p>
                <p className="text-xs text-muted uppercase tracking-wide">
                  {t[metric.key]}
                </p>
              </div>
            );
          })}
        </div>

        {/* ── Disclaimer ── */}
        <p
          className={`reveal ${visible ? "visible" : ""} text-center text-xs text-muted/60 max-w-xl mx-auto leading-relaxed`}
          style={{ transitionDelay: visible ? "0.8s" : "0s" }}
        >
          {t.simDisclaimer}
        </p>
      </div>
    </section>
  );
}
