"use client";

export type Locale = "en" | "ru";

export function LanguageToggle({ locale, setLocale, className = "" }: { locale: Locale; setLocale: (fn: (l: Locale) => Locale) => void; className?: string }) {
  return (
    <button
      onClick={() => setLocale(l => l === "en" ? "ru" : "en")}
      aria-label={locale === "en" ? "Switch to Russian" : "Switch to English"}
      className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full border border-border/50 text-xs font-mono hover:border-primary/30 transition-all ${className}`}
    >
      <span className={locale === "en" ? "text-primary font-medium" : "text-muted"}>EN</span>
      <span className="text-border/50">/</span>
      <span className={locale === "ru" ? "text-primary font-medium" : "text-muted"}>RU</span>
    </button>
  );
}
