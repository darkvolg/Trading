"use client";

import { useEffect, useState } from "react";
import type { TStrings, Locale } from "@/lib/i18n";

export function CookieConsent({ t, locale }: { t: TStrings; locale: Locale }) {
  const [show, setShow] = useState(false);
  useEffect(() => {
    const consent = localStorage.getItem("cookie-consent");
    if (!consent) {
      const timer = setTimeout(() => setShow(true), 2000);
      return () => clearTimeout(timer);
    }
  }, []);
  if (!show) return null;
  return (
    <div className="fixed left-0 right-0 bottom-0 rounded-none md:left-4 md:right-auto md:bottom-4 md:rounded-xl md:max-w-sm z-50" style={{ animation: "fadeInUp 0.5s ease-out" }}>
      <div className="glass rounded-none md:rounded-2xl p-5 shadow-2xl border-t md:border border-border/50">
        <p className="text-sm text-muted mb-4">
          {t.cookieText}{" "}
          <a href="/privacy" className="underline hover:text-foreground transition-colors">
            {locale === "ru" ? "Подробнее" : "Learn more"}
          </a>
        </p>
        <div className="flex items-center gap-3">
          <button
            onClick={() => { localStorage.setItem("cookie-consent", "accepted"); setShow(false); }}
            className="btn-primary btn-press px-5 py-2 rounded-lg text-xs font-semibold flex-1"
            aria-label="Accept cookies"
          >
            {t.cookieAccept}
          </button>
          <button
            onClick={() => { localStorage.setItem("cookie-consent", "declined"); setShow(false); }}
            className="px-5 py-2 rounded-lg text-xs font-medium border border-border/50 text-muted hover:text-foreground hover:border-primary/30 transition-all flex-1"
            aria-label="Decline cookies"
          >
            {t.cookieDeny}
          </button>
        </div>
      </div>
    </div>
  );
}
