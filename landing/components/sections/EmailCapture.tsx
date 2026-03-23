"use client";

import { useState } from "react";
import type { TStrings } from "@/lib/i18n";

export function EmailCapture({ t }: { t: TStrings }) {
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState<"idle" | "loading" | "success" | "error">("idle");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !email.includes("@")) return;
    setStatus("loading");
    try {
      const res = await fetch("https://connect.mailerlite.com/api/subscribers", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${process.env.NEXT_PUBLIC_MAILERLITE_TOKEN}`,
        },
        body: JSON.stringify({ email }),
      });
      if (!res.ok) throw new Error("API error");
      setStatus("success");
      setEmail("");
    } catch {
      setStatus("error");
    }
  };

  return (
    <section className="py-20 px-4 border-y border-border/20 bg-card/10">
      <div className="max-w-xl mx-auto text-center">
        <span className="inline-block px-4 py-1.5 text-xs font-mono uppercase tracking-widest text-primary border border-primary/30 rounded-full mb-5">
          {t.emailTag}
        </span>
        <h2 className="text-2xl md:text-3xl font-bold mb-3 tracking-tight">{t.emailTitle}</h2>
        <p className="text-muted mb-8 text-sm leading-relaxed">{t.emailSubtitle}</p>

        {status === "success" ? (
          <div className="flex items-center justify-center gap-2 text-primary font-medium py-4">
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="m4.5 12.75 6 6 9-13.5" />
            </svg>
            {t.emailSuccess}
          </div>
        ) : (
          <>
            <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row gap-3 max-w-md mx-auto">
              <input
                type="email"
                value={email}
                onChange={(e) => { setEmail(e.target.value); if (status === "error") setStatus("idle"); }}
                placeholder={t.emailPlaceholder}
                required
                disabled={status === "loading"}
                className="flex-1 px-4 py-3 rounded-xl bg-background border border-border/50 text-foreground placeholder:text-muted/50 focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/20 transition-all text-sm font-mono disabled:opacity-50"
              />
              <button
                type="submit"
                disabled={status === "loading"}
                className="btn-primary btn-press px-6 py-3 rounded-xl text-sm font-semibold whitespace-nowrap disabled:opacity-50"
              >
                {status === "loading" ? t.emailSending : t.emailButton}
              </button>
            </form>
            {status === "error" && (
              <p className="text-red-400 text-sm mt-3">{t.emailError}</p>
            )}
          </>
        )}

        <p className="text-muted/50 text-xs mt-4">{t.emailDisclaimer}</p>
      </div>
    </section>
  );
}
