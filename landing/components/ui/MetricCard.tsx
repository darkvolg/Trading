"use client";

import React from "react";
import { useCounter } from "@/hooks/useCounter";

export function MetricCard({
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
