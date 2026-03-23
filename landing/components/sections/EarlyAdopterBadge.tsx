"use client";

export function EarlyAdopterBadge({ label, daysLeftLabel }: { label: string; daysLeftLabel: string }) {
  const launchDate = new Date("2026-04-15T00:00:00");
  const now = new Date();
  const daysRemaining = Math.max(0, Math.ceil((launchDate.getTime() - now.getTime()) / (1000 * 60 * 60 * 24)));
  return (
    <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-accent/30 bg-accent/5">
      <span className="relative flex h-2 w-2">
        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-accent opacity-75" />
        <span className="relative inline-flex rounded-full h-2 w-2 bg-accent" />
      </span>
      <span className="text-xs text-accent/80 font-medium">
        {label} · {daysRemaining} {daysLeftLabel}
      </span>
    </div>
  );
}
