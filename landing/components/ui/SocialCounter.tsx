"use client";

import { useCounter } from "@/hooks/useCounter";

export function SocialCounter({ target, decimals, suffix, label, active }: { target: number; decimals: number; suffix: string; label: string; active: boolean }) {
  const count = useCounter(target, decimals, active);
  return (
    <div className="text-center group">
      <div className="font-mono text-3xl md:text-4xl font-bold text-primary mb-1 tabular-nums">
        {count.toFixed(decimals)}{suffix}
      </div>
      <div className="text-xs text-muted uppercase tracking-wider">{label}</div>
    </div>
  );
}
