"use client";

import { useEffect, useState } from "react";

type ExitBreakdown = {
  exit_reason: string;
  count: number;
  avg_pct: number;
  total_abs: number;
};

type Trade = {
  pair: string;
  open_date: string;
  close_date: string;
  close_profit_pct: number;
  close_profit_abs: number;
  exit_reason: string;
  enter_tag: string;
};

type OpenTrade = {
  pair: string;
  open_date: string;
  stake_amount: number;
  open_rate: number;
};

type EquityPoint = { day: string; balance: number };

type Stats = {
  generated_at: string;
  strategy: string;
  mode: string;
  starting_balance: number;
  current_balance: number;
  pnl_abs: number;
  pnl_pct: number;
  total_trades: number;
  closed_trades: number;
  open_trades_count: number;
  wins: number;
  losses: number;
  win_rate_pct: number;
  first_trade_date: string;
  exit_breakdown: ExitBreakdown[];
  recent_trades: Trade[];
  open_positions: OpenTrade[];
  equity_curve: EquityPoint[];
};

function Sparkline({ data, width = 600, height = 160 }: { data: EquityPoint[]; width?: number; height?: number }) {
  if (data.length < 2) return <div className="text-slate-500 text-sm">Not enough data yet</div>;
  const values = data.map((d) => d.balance);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  const stepX = width / (data.length - 1);
  const points = data
    .map((d, i) => `${i * stepX},${height - ((d.balance - min) / range) * height}`)
    .join(" ");
  const lastPct = ((values[values.length - 1] - values[0]) / values[0]) * 100;
  const color = lastPct >= 0 ? "#10b981" : "#ef4444";
  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-auto">
      <defs>
        <linearGradient id="grad" x1="0" x2="0" y1="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.4" />
          <stop offset="100%" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      <polygon
        fill="url(#grad)"
        points={`0,${height} ${points} ${width},${height}`}
      />
      <polyline fill="none" stroke={color} strokeWidth="2" points={points} />
    </svg>
  );
}

function fmtDate(iso: string) {
  try {
    return new Date(iso).toLocaleString("en-US", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      timeZone: "UTC",
    });
  } catch {
    return iso;
  }
}

function fmtRelative(iso: string) {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

export default function LivePage() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const res = await fetch(`/api/live-stats.json?t=${Date.now()}`, { cache: "no-store" });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = (await res.json()) as Stats;
        if (!cancelled) {
          setStats(data);
          setErr(null);
          setLoading(false);
        }
      } catch (e) {
        if (!cancelled) {
          setErr(e instanceof Error ? e.message : "Failed to load");
          setLoading(false);
        }
      }
    };
    load();
    const id = setInterval(load, 60_000);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, []);

  if (loading) {
    return (
      <main className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center">
        <div className="text-slate-400">Loading live stats…</div>
      </main>
    );
  }

  if (err || !stats) {
    return (
      <main className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center">
        <div className="text-red-400">Failed to load stats: {err}</div>
      </main>
    );
  }

  const pnlPositive = stats.pnl_abs >= 0;
  const pnlColor = pnlPositive ? "text-emerald-400" : "text-red-400";

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100 font-sans">
      <div className="max-w-5xl mx-auto px-4 py-8 sm:px-6 sm:py-12">
        <header className="mb-8">
          <div className="flex items-center justify-between flex-wrap gap-2">
            <a href="/" className="text-slate-400 hover:text-slate-200 text-sm">← trendrider.net</a>
            <div className="text-xs text-slate-500 font-mono">
              Updated {fmtRelative(stats.generated_at)} · refreshes every 60s
            </div>
          </div>
          <h1 className="mt-4 text-3xl sm:text-4xl font-bold tracking-tight">
            Live Bot Stats <span className="text-emerald-400">●</span>
          </h1>
          <p className="mt-2 text-slate-400 text-sm">
            {stats.strategy} · {stats.mode} · raw data from sqlite, no marketing filter
          </p>
          <a
            href="https://github.com/darkvolg/trendrider-strategy"
            target="_blank"
            rel="noopener"
            className="mt-4 inline-flex items-center gap-2 px-3 py-1.5 rounded-md bg-slate-900 border border-slate-700 hover:border-emerald-500/50 hover:bg-slate-800 text-sm text-slate-200 transition-colors"
          >
            <svg viewBox="0 0 16 16" width="16" height="16" fill="currentColor" aria-hidden="true">
              <path d="M8 .25a.75.75 0 0 1 .673.418l1.882 3.815 4.21.612a.75.75 0 0 1 .416 1.279l-3.046 2.97.719 4.192a.75.75 0 0 1-1.088.791L8 12.347l-3.766 1.98a.75.75 0 0 1-1.088-.79l.72-4.194L.818 6.374a.75.75 0 0 1 .416-1.28l4.21-.611L7.327.668A.75.75 0 0 1 8 .25Z" />
            </svg>
            <span className="font-medium">Star the strategy on GitHub</span>
            <span className="text-slate-500">— open-source, MIT</span>
          </a>
        </header>

        <section className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-8">
          <div className="bg-slate-900 border border-slate-800 rounded-lg p-4">
            <div className="text-xs uppercase tracking-wider text-slate-500">Balance</div>
            <div className="mt-1 text-2xl font-mono font-bold">${stats.current_balance.toFixed(2)}</div>
            <div className="text-xs text-slate-500 mt-0.5">from ${stats.starting_balance.toFixed(0)}</div>
          </div>
          <div className="bg-slate-900 border border-slate-800 rounded-lg p-4">
            <div className="text-xs uppercase tracking-wider text-slate-500">P&amp;L</div>
            <div className={`mt-1 text-2xl font-mono font-bold ${pnlColor}`}>
              {pnlPositive ? "+" : ""}${stats.pnl_abs.toFixed(2)}
            </div>
            <div className={`text-xs mt-0.5 ${pnlColor}`}>
              {pnlPositive ? "+" : ""}{stats.pnl_pct.toFixed(2)}%
            </div>
          </div>
          <div className="bg-slate-900 border border-slate-800 rounded-lg p-4">
            <div className="text-xs uppercase tracking-wider text-slate-500">Win Rate</div>
            <div className="mt-1 text-2xl font-mono font-bold">{stats.win_rate_pct.toFixed(1)}%</div>
            <div className="text-xs text-slate-500 mt-0.5">{stats.wins}W / {stats.losses}L</div>
          </div>
          <div className="bg-slate-900 border border-slate-800 rounded-lg p-4">
            <div className="text-xs uppercase tracking-wider text-slate-500">Trades</div>
            <div className="mt-1 text-2xl font-mono font-bold">{stats.closed_trades}</div>
            <div className="text-xs text-slate-500 mt-0.5">{stats.open_trades_count} open</div>
          </div>
        </section>

        <section className="bg-slate-900 border border-slate-800 rounded-lg p-5 mb-8">
          <h2 className="text-sm uppercase tracking-wider text-slate-500 mb-4">Equity Curve</h2>
          <Sparkline data={stats.equity_curve} />
        </section>

        <section className="grid md:grid-cols-2 gap-6 mb-8">
          <div className="bg-slate-900 border border-slate-800 rounded-lg p-5">
            <h2 className="text-sm uppercase tracking-wider text-slate-500 mb-4">Exit Reasons</h2>
            <table className="w-full text-sm font-mono">
              <thead className="text-slate-500 text-xs">
                <tr>
                  <th className="text-left pb-2">Reason</th>
                  <th className="text-right pb-2">N</th>
                  <th className="text-right pb-2">Avg %</th>
                  <th className="text-right pb-2">Total $</th>
                </tr>
              </thead>
              <tbody>
                {stats.exit_breakdown.map((e) => (
                  <tr key={e.exit_reason} className="border-t border-slate-800">
                    <td className="py-1.5">{e.exit_reason}</td>
                    <td className="text-right">{e.count}</td>
                    <td className={`text-right ${e.avg_pct >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                      {e.avg_pct >= 0 ? "+" : ""}{e.avg_pct.toFixed(2)}
                    </td>
                    <td className={`text-right ${e.total_abs >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                      {e.total_abs >= 0 ? "+" : ""}{e.total_abs.toFixed(2)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="bg-slate-900 border border-slate-800 rounded-lg p-5">
            <h2 className="text-sm uppercase tracking-wider text-slate-500 mb-4">
              Open Positions ({stats.open_positions.length})
            </h2>
            {stats.open_positions.length === 0 ? (
              <div className="text-slate-500 text-sm">No open positions — bot is waiting for signal.</div>
            ) : (
              <table className="w-full text-sm font-mono">
                <thead className="text-slate-500 text-xs">
                  <tr>
                    <th className="text-left pb-2">Pair</th>
                    <th className="text-right pb-2">Entry</th>
                    <th className="text-right pb-2">Stake</th>
                    <th className="text-right pb-2">Opened</th>
                  </tr>
                </thead>
                <tbody>
                  {stats.open_positions.map((p) => (
                    <tr key={p.pair + p.open_date} className="border-t border-slate-800">
                      <td className="py-1.5">{p.pair.replace(":USDT", "")}</td>
                      <td className="text-right">{p.open_rate.toFixed(4)}</td>
                      <td className="text-right">${p.stake_amount.toFixed(0)}</td>
                      <td className="text-right text-slate-400">{fmtRelative(p.open_date)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </section>

        <section className="bg-slate-900 border border-slate-800 rounded-lg p-5 mb-8">
          <h2 className="text-sm uppercase tracking-wider text-slate-500 mb-4">Recent Trades (last 20)</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm font-mono">
              <thead className="text-slate-500 text-xs">
                <tr>
                  <th className="text-left pb-2">Pair</th>
                  <th className="text-left pb-2 hidden sm:table-cell">Entry Tag</th>
                  <th className="text-left pb-2">Exit</th>
                  <th className="text-right pb-2">%</th>
                  <th className="text-right pb-2">$</th>
                  <th className="text-right pb-2 hidden sm:table-cell">Closed</th>
                </tr>
              </thead>
              <tbody>
                {stats.recent_trades.map((t) => (
                  <tr key={t.pair + t.close_date} className="border-t border-slate-800">
                    <td className="py-1.5">{t.pair.replace(":USDT", "")}</td>
                    <td className="hidden sm:table-cell text-slate-400">{t.enter_tag}</td>
                    <td className="text-slate-400">{t.exit_reason}</td>
                    <td className={`text-right ${t.close_profit_pct >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                      {t.close_profit_pct >= 0 ? "+" : ""}{t.close_profit_pct.toFixed(2)}
                    </td>
                    <td className={`text-right ${t.close_profit_abs >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                      {t.close_profit_abs >= 0 ? "+" : ""}{t.close_profit_abs.toFixed(2)}
                    </td>
                    <td className="hidden sm:table-cell text-right text-slate-500">{fmtDate(t.close_date)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <footer className="text-xs text-slate-600 border-t border-slate-800 pt-4 mt-8 space-y-1">
          <p>
            This page shows real-time data from a paper-trading bot running Freqtrade on Bybit futures.
            Numbers are unfiltered — losing trades included. Data updates hourly from bot sqlite.
            The strategy is open-source on <a href="https://github.com/darkvolg/trendrider-strategy" className="text-slate-400 hover:text-slate-200 underline" rel="noopener" target="_blank">GitHub</a>.
          </p>
          <p>First trade: {stats.first_trade_date ? fmtDate(stats.first_trade_date) : "n/a"}</p>
          <p>
            <a href="https://github.com/darkvolg/trendrider-strategy" className="text-slate-500 hover:text-slate-300" rel="noopener" target="_blank">Strategy on GitHub</a>{" "}
            ·{" "}
            <a href="/blog" className="text-slate-500 hover:text-slate-300">Blog</a>{" "}
            ·{" "}
            <a href="https://t.me/TrendRiderSignals" className="text-slate-500 hover:text-slate-300">Telegram</a>
          </p>
        </footer>
      </div>
    </main>
  );
}
