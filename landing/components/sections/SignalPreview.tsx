"use client";

import { useEffect, useState } from "react";

export function SignalPreview({ visible }: { visible: boolean }) {
  const [phase, setPhase] = useState<"typing" | "message" | "idle">("typing");

  useEffect(() => {
    if (!visible) return;
    const t1 = setTimeout(() => setPhase("message"), 1500);
    const t2 = setTimeout(() => setPhase("idle"), 4000);
    return () => { clearTimeout(t1); clearTimeout(t2); };
  }, [visible]);

  const showTyping = visible && phase === "typing";
  const showMessage = phase === "message" || phase === "idle";
  const justReceived = phase === "message";

  return (
    <div className="max-w-sm mx-auto">
      {/* Telegram-style chat header */}
      <div className="tg-header flex items-center gap-3 px-4 py-3 rounded-t-2xl border-b border-white/5">
        <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center shrink-0">
          <svg className="w-4 h-4 text-primary" viewBox="0 0 24 24" fill="currentColor">
            <path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z" />
          </svg>
        </div>
        <div className="flex-1 min-w-0">
          <div className="text-sm font-semibold text-foreground truncate">TrendRider Signals</div>
          <div className="text-xs text-[#8B949E]">
            {showTyping && visible ? (
              <span className="flex items-center gap-1">
                <span>typing</span>
                <span className="flex items-center gap-0.5 ml-1">
                  <span className="typing-dot" />
                  <span className="typing-dot" />
                  <span className="typing-dot" />
                </span>
              </span>
            ) : (
              "subscribers"
            )}
          </div>
        </div>
        <div className="flex items-center gap-1.5 shrink-0">
          {justReceived && (
            <span
              className="text-xs font-mono px-2 py-0.5 bg-primary/20 text-primary rounded-full border border-primary/30"
              style={{ animation: "slideInRight 0.3s ease-out" }}
            >
              Just now
            </span>
          )}
          <div className="w-2 h-2 rounded-full bg-primary animate-pulse" />
        </div>
      </div>

      {/* Chat body */}
      <div className="tg-body rounded-b-2xl px-4 pb-4 pt-4 min-h-[320px] flex items-end">
        {showTyping && visible && !showMessage && (
          <div className="tg-bubble px-4 py-3 inline-flex items-center gap-1.5">
            <span className="typing-dot" />
            <span className="typing-dot" />
            <span className="typing-dot" />
          </div>
        )}

        {showMessage && (
          <div
            className="tg-bubble px-4 py-3 font-mono text-sm leading-relaxed w-full"
            style={{ animation: "scaleIn 0.35s cubic-bezier(0.16, 1, 0.3, 1) forwards" }}
          >
            <div className="space-y-1">
              <p>
                <span className="text-muted">&#128202;</span>{" "}
                <span className="text-foreground font-semibold">TrendRider Signal #042</span>
              </p>
              <p>
                <span className="text-primary font-bold">&#x1F7E2; LONG BTC/USDT</span>
              </p>
            </div>

            <div className="my-3 h-px bg-border/40" />

            <div className="space-y-1.5 text-xs">
              <p>
                <span className="text-muted">Entry Zone:</span>{" "}
                <span className="text-foreground">$64,200 — $64,580</span>
              </p>
              <p>
                <span className="text-muted">Stop Loss:</span>{" "}
                <span className="text-danger">$60,350 (-6.0%)</span>
              </p>
              <p>
                <span className="text-muted">TP1:</span>{" "}
                <span className="text-primary">$66,126 (+3.0%)</span>{" "}
                <span className="text-muted">— 30%</span>
              </p>
              <p>
                <span className="text-muted">TP2:</span>{" "}
                <span className="text-primary">$67,410 (+5.0%)</span>{" "}
                <span className="text-muted">— 40%</span>
              </p>
              <p>
                <span className="text-muted">TP3:</span>{" "}
                <span className="text-primary">$70,620 (+10.0%)</span>{" "}
                <span className="text-muted">— 30%</span>
              </p>
            </div>

            <div className="my-3 h-px bg-border/40" />

            <div className="space-y-1 text-xs">
              <p>
                <span className="text-muted">AI Confidence:</span>{" "}
                <span className="text-primary">████████</span>
                <span className="text-border">██</span>{" "}
                <span className="text-accent font-bold">8/10</span>
              </p>
              <p>
                <span className="text-muted">Setup:</span>{" "}
                <span className="text-foreground">Trend Pullback</span>
              </p>
              <p>
                <span className="text-muted">Regime:</span>{" "}
                <span className="text-primary">Trending Bull &#x1F4C8;</span>
              </p>
            </div>

            <div className="flex items-center justify-end gap-1 mt-2 opacity-50">
              <span className="text-[10px] font-mono text-muted">12:34</span>
              <svg className="w-3.5 h-3.5 text-primary" fill="currentColor" viewBox="0 0 16 16">
                <path d="M12.354 4.354a.5.5 0 0 0-.708-.708L5 10.293 1.854 7.146a.5.5 0 1 0-.708.708l3.5 3.5a.5.5 0 0 0 .708 0l7-7zm-4.208 7-.896-.897.707-.707.543.543 6.646-6.647a.5.5 0 0 1 .708.708l-7 7a.5.5 0 0 1-.708 0z"/>
              </svg>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
