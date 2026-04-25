"use client";

import { useState, useCallback } from "react";
import { TELEGRAM_URL } from "@/lib/constants";
import type { TStrings, Locale } from "@/lib/i18n";
import { useNavVisible } from "@/hooks";
import { LanguageToggle } from "@/components/ui";

interface NavLink {
  label: string;
  ref: React.RefObject<HTMLDivElement | null>;
}

interface PageLink {
  label: string;
  href: string;
}

interface StickyNavProps {
  t: TStrings;
  locale: Locale;
  setLocale: (fn: (l: Locale) => Locale) => void;
  navLinks: NavLink[];
  pageLinks?: PageLink[];
  githubUrl?: string;
}

export function StickyNav({ t, locale, setLocale, navLinks, pageLinks = [], githubUrl }: StickyNavProps) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const navVisible = useNavVisible();

  const scrollTo = useCallback((ref: React.RefObject<HTMLDivElement | null>) => {
    if (ref.current) {
      const offset = 80; // navbar height
      const top = ref.current.getBoundingClientRect().top + window.scrollY - offset;
      window.scrollTo({ top, behavior: "smooth" });
    }
  }, []);

  return (
    <nav
      aria-label="Main navigation"
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        navVisible
          ? "translate-y-0 opacity-100"
          : "-translate-y-full opacity-0 pointer-events-none"
      } bg-background/80 backdrop-blur-xl border-b border-border/50`}
      style={{ paddingTop: "env(safe-area-inset-top)" }}
    >
      <div className="max-w-5xl mx-auto flex items-center justify-between px-4 py-3">
        <span className="text-lg font-bold gradient-text">TrendRider</span>
        <div className="hidden md:flex items-center gap-6">
          {navLinks.map((item) => (
            <button
              key={item.label}
              onClick={() => scrollTo(item.ref)}
              className="text-sm text-muted hover:text-foreground transition-colors cursor-pointer focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-none rounded"
            >
              {item.label}
            </button>
          ))}
          {pageLinks.map((item) => (
            <a
              key={item.label}
              href={item.href}
              className="text-sm text-muted hover:text-foreground transition-colors focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-none rounded"
            >
              {item.label}
            </a>
          ))}
        </div>
        <div className="flex items-center gap-2">
          {githubUrl && (
            <a
              href={githubUrl}
              target="_blank"
              rel="noopener noreferrer"
              aria-label="GitHub repository"
              className="hidden md:flex items-center justify-center w-9 h-9 rounded-lg text-muted hover:text-foreground hover:bg-card/50 transition-colors focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-none"
            >
              <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                <path d="M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.4 3-.405 1.02.005 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12" />
              </svg>
            </a>
          )}
          <LanguageToggle locale={locale} setLocale={setLocale} />
          {/* Mobile burger */}
          <button
            className="md:hidden flex flex-col gap-1.5 p-3 min-w-[44px] min-h-[44px] items-center justify-center rounded-lg hover:bg-card/50 transition-colors focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-none"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            aria-label="Toggle menu"
          >
            <span className={`block w-5 h-0.5 bg-foreground transition-all duration-300 ${mobileMenuOpen ? "rotate-45 translate-y-2" : ""}`} />
            <span className={`block w-5 h-0.5 bg-foreground transition-all duration-300 ${mobileMenuOpen ? "opacity-0" : ""}`} />
            <span className={`block w-5 h-0.5 bg-foreground transition-all duration-300 ${mobileMenuOpen ? "-rotate-45 -translate-y-2" : ""}`} />
          </button>
          <a
            href={TELEGRAM_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="hidden md:flex btn-primary btn-press items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-none"
          >
            <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
              <path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z" />
            </svg>
            {t.joinTelegram}
          </a>
        </div>
      </div>

      {/* Mobile dropdown menu */}
      <div className={`md:hidden overflow-hidden transition-all duration-300 ${mobileMenuOpen ? "max-h-96 opacity-100" : "max-h-0 opacity-0"}`}>
        <div className="px-4 pb-4 space-y-1 border-t border-border/30">
          {navLinks.map((item) => (
            <button
              key={item.label}
              onClick={() => { scrollTo(item.ref); setMobileMenuOpen(false); }}
              className="block w-full text-left py-4 px-3 text-sm text-muted hover:text-foreground hover:bg-card/30 rounded-lg transition-colors focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-none"
            >
              {item.label}
            </button>
          ))}
          {pageLinks.map((item) => (
            <a
              key={item.label}
              href={item.href}
              onClick={() => setMobileMenuOpen(false)}
              className="block w-full text-left py-4 px-3 text-sm text-muted hover:text-foreground hover:bg-card/30 rounded-lg transition-colors focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-none"
            >
              {item.label}
            </a>
          ))}
          {githubUrl && (
            <a
              href={githubUrl}
              target="_blank"
              rel="noopener noreferrer"
              onClick={() => setMobileMenuOpen(false)}
              className="block w-full text-left py-4 px-3 text-sm text-muted hover:text-foreground hover:bg-card/30 rounded-lg transition-colors focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-none"
            >
              GitHub
            </a>
          )}
          <a
            href={TELEGRAM_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="btn-primary btn-press flex items-center justify-center gap-2 w-full py-3 rounded-lg text-sm font-semibold mt-2 focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-none"
          >
            {t.joinTelegram}
          </a>
        </div>
      </div>
    </nav>
  );
}
