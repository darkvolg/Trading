"use client";

import { useState } from "react";

type Props = {
  heading?: string;
  subheading?: string;
  ctaLabel?: string;
  tag?: string;
};

export function EmailCaptureInline({
  heading = "Get the sample backtest report",
  subheading = "Drop your email and I'll send you the first 3 pages of the Pro Pack's BACKTEST-REPORT.md — per-pair breakdown, V3 vs V4 exit-reason table, and the drawdown profile. Free, no spam. Unsubscribe any time.",
  ctaLabel = "Send me the sample",
  tag = "pro-pack-preview",
}: Props) {
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState<"idle" | "loading" | "success" | "error">("idle");
  const [errorMsg, setErrorMsg] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !email.includes("@")) return;
    setStatus("loading");
    setErrorMsg("");
    try {
      // Same-origin proxy via nginx — token stays server-side, no CORS issue
      const res = await fetch("/api/subscribe", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email,
          fields: { source: tag },
        }),
      });
      if (!res.ok) {
        const body = await res.text();
        throw new Error(body.slice(0, 120));
      }
      setStatus("success");
      setEmail("");
    } catch (err) {
      setStatus("error");
      setErrorMsg(err instanceof Error ? err.message : "Unknown error");
    }
  };

  return (
    <div className="mt-6 p-6 border border-primary/20 rounded-lg bg-card/20">
      <p className="text-foreground font-semibold mb-2">📨 {heading}</p>
      <p className="mb-4 text-sm">{subheading}</p>
      {status === "success" ? (
        <p className="text-emerald-400 text-sm font-medium">
          ✅ Got it — check your inbox in the next few minutes. If it doesn&apos;t arrive, check spam or email me directly from the GitHub repo.
        </p>
      ) : (
        <>
          <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row gap-2">
            <input
              type="email"
              value={email}
              onChange={(e) => { setEmail(e.target.value); if (status === "error") setStatus("idle"); }}
              placeholder="your@email.com"
              required
              disabled={status === "loading"}
              className="flex-1 px-3 py-2 rounded-md bg-background border border-border/50 text-foreground placeholder:text-muted/50 focus:outline-none focus:border-primary/50 text-sm font-mono disabled:opacity-50"
            />
            <button
              type="submit"
              disabled={status === "loading"}
              className="px-4 py-2 rounded-md bg-primary text-primary-foreground font-semibold text-sm hover:bg-primary/90 disabled:opacity-50 transition-colors"
            >
              {status === "loading" ? "Sending..." : ctaLabel}
            </button>
          </form>
          {status === "error" && (
            <p className="text-red-400 text-xs mt-2">Could not subscribe: {errorMsg}. Try again in a minute.</p>
          )}
          <p className="text-muted/60 text-xs mt-2">No spam. Unsubscribe in one click. Emails handled by MailerLite.</p>
        </>
      )}
    </div>
  );
}
