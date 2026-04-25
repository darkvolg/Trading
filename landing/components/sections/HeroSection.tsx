"use client";

import type { RefObject } from "react";
import type { TStrings, Locale } from "@/lib/i18n";
import { TELEGRAM_URL, BYBIT_AFFILIATE_URL } from "@/lib/constants";
import { LanguageToggle } from "@/components/ui";
import { CandlestickChart } from "./CandlestickChart";
import { Particles } from "./Particles";

interface HeroSectionProps {
  t: TStrings;
  locale: Locale;
  setLocale: (fn: (l: Locale) => Locale) => void;
  parallaxRef: RefObject<HTMLDivElement | null>;
}

export function HeroSection({ t, locale, setLocale, parallaxRef }: HeroSectionProps) {
  return (
    <section className="relative min-h-screen flex items-center justify-center px-4 overflow-hidden">
      {/* Deep atmospheric glow */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_80%_60%_at_50%_-10%,rgba(0,212,170,0.08)_0%,transparent_70%)] pointer-events-none" />
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_40%_40%_at_75%_70%,rgba(255,215,0,0.04)_0%,transparent_60%)] pointer-events-none" />

      {/* Animated gradient mesh blob */}
      <div className="gradient-mesh top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/4 opacity-60" aria-hidden="true" />

      {/* Floating gradient orbs — parallax wrapper */}
      <div ref={parallaxRef} className="absolute inset-0 pointer-events-none" aria-hidden="true">
        <div className="absolute top-1/4 left-1/4 w-[500px] h-[500px] rounded-full bg-primary/[0.03] blur-[120px] animate-orb-1" />
        <div className="absolute bottom-1/3 right-1/5 w-[400px] h-[400px] rounded-full bg-accent/[0.02] blur-[100px] animate-orb-2" />
        <div className="absolute top-2/3 left-2/3 w-[300px] h-[300px] rounded-full bg-danger/[0.02] blur-[80px] animate-orb-3" />
      </div>

      {/* Candlestick chart background — faded in center so text is readable */}
      <div className="absolute inset-0 pointer-events-none" style={{
        maskImage: "radial-gradient(ellipse 65% 75% at 50% 50%, transparent 25%, black 85%)",
        WebkitMaskImage: "radial-gradient(ellipse 65% 75% at 50% 50%, transparent 25%, black 85%)",
      }}>
        <CandlestickChart />
      </div>

      {/* Floating particles */}
      <Particles />

      {/* Animated scan line */}
      <div className="absolute left-0 right-0 h-px scan-line-animate" style={{
        background: "linear-gradient(90deg, transparent, rgba(0,212,170,0.2), transparent)",
      }} />

      {/* Language toggle + GitHub in hero — visible before navbar appears */}
      <div className="absolute top-6 right-6 sm:top-8 sm:right-8 z-20 flex items-center gap-2">
        <a
          href="https://github.com/darkvolg/Trading"
          target="_blank"
          rel="noopener noreferrer"
          aria-label="GitHub repository"
          className="flex items-center justify-center w-9 h-9 rounded-lg text-muted hover:text-foreground bg-background/80 backdrop-blur-xl border border-border/50 hover:border-primary/40 transition-colors focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-none"
        >
          <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
            <path d="M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.4 3-.405 1.02.005 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12" />
          </svg>
        </a>
        <LanguageToggle
          locale={locale}
          setLocale={setLocale}
          className="bg-background/80 backdrop-blur-xl"
        />
      </div>

      {/* Live badge — positioned at top of hero, below nav area on mobile */}
      <div
        className="absolute top-16 sm:top-8 left-1/2 -translate-x-1/2 z-20 inline-flex items-center gap-1.5 sm:gap-2 px-3 sm:px-5 py-2 sm:py-2.5 rounded-full border border-primary-700/40 bg-primary-900/20 backdrop-blur-xl shadow-lg shadow-black/30 max-w-[calc(100vw-2rem)]"
        style={{ animation: "fadeInDown 0.6s ease-out forwards" }}
      >
        <span className="w-2 h-2 shrink-0 rounded-full bg-primary-400 animate-pulse" />
        <span className="text-xs sm:text-sm font-mono text-primary-100 font-medium whitespace-nowrap">{t.liveSince}</span>
        <span className="w-px h-3 bg-primary-700/40 hidden sm:block" />
        <span className="text-[10px] sm:text-xs font-mono text-primary-200/70 hidden sm:block">{t.paperVerified}</span>
      </div>

      <div className="relative text-center max-w-4xl mx-auto z-10">
        {/* Headline — animated letter reveal */}
        <h1 className="text-[1.75rem] sm:text-4xl md:text-6xl lg:text-8xl font-bold tracking-tight mb-4 mt-24 sm:mt-0"
          style={{ animation: "fadeInUp 0.7s 0.2s cubic-bezier(0.16, 1, 0.3, 1) both" }}>
          {"TrendRider".split("").map((letter, i) => (
            <span
              key={i}
              className="gradient-text inline-block"
              style={{
                animation: `letterReveal 0.5s ${0.3 + i * 0.05}s cubic-bezier(0.16, 1, 0.3, 1) both`,
              }}
            >
              {letter}
            </span>
          ))}
        </h1>

        <p
          className="text-base sm:text-xl md:text-2xl lg:text-3xl text-foreground/80 font-light mb-3 tracking-wide px-2"
          style={{ animation: "fadeInUp 0.7s 0.35s cubic-bezier(0.16, 1, 0.3, 1) both" }}
        >
          {t.tagline}{" "}
          <span className="text-primary font-normal">{t.taglineHighlight}</span>
        </p>

        <p
          className="text-muted max-w-xl mx-auto mb-10 leading-relaxed text-sm sm:text-base md:text-lg px-2"
          style={{ animation: "fadeInUp 0.7s 0.5s cubic-bezier(0.16, 1, 0.3, 1) both" }}
        >
          {t.heroDesc}
        </p>

        {/* Quick stats row — BACKTEST numbers, with link to live */}
        <div
          className="flex flex-col items-center mb-10"
          style={{ animation: "fadeInUp 0.7s 0.6s cubic-bezier(0.16, 1, 0.3, 1) both" }}
        >
          <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 mb-3 rounded-full border border-muted/30 text-[10px] font-mono uppercase tracking-widest text-muted">
            {t.backtestLabel}
          </div>
          <div className="flex items-center justify-center text-sm text-muted">
            <span className="font-mono">Real numbers (backtest + live) published on </span>
            <a href="/live" className="font-mono font-bold text-primary ml-1 hover:underline">/live</a>
          </div>
          <a href="/live" className="mt-3 text-xs text-primary/80 hover:text-primary transition-colors underline-offset-4 hover:underline">
            {t.seeLivePerformance}
          </a>
        </div>

        <div
          className="flex flex-col sm:flex-row items-center justify-center gap-4"
          style={{ animation: "fadeInUp 0.7s 0.7s cubic-bezier(0.16, 1, 0.3, 1) both" }}
        >
          <a
            href={TELEGRAM_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="btn-primary btn-press group flex items-center gap-3 px-8 py-4 rounded-xl text-sm md:text-base animate-pulse-glow"
          >
            <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
              <path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z" />
            </svg>
            {t.joinTelegramChannel}
            <svg
              className="w-4 h-4 transition-transform group-hover:translate-x-1"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
              aria-hidden="true"
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5 21 12m0 0-7.5 7.5M21 12H3" />
            </svg>
          </a>
          <a
            href="/live"
            className="btn-press flex items-center gap-3 px-8 py-4 border border-border text-foreground font-medium rounded-xl hover:bg-card/50 hover:border-primary/30 transition-all text-sm md:text-base"
          >
            <svg className="w-5 h-5 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5} aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 0 1 3 19.875v-6.75ZM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V8.625ZM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V4.125Z" />
            </svg>
            {t.viewLiveResults}
          </a>
        </div>

        {/* Bybit affiliate CTA */}
        <div
          className="flex justify-center mt-4"
          style={{ animation: "fadeInUp 0.7s 0.8s cubic-bezier(0.16, 1, 0.3, 1) both" }}
        >
          <a
            href={BYBIT_AFFILIATE_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="btn-press group flex items-center gap-3 px-6 py-3 rounded-xl text-sm border border-[#F7A600]/30 bg-[#F7A600]/10 hover:bg-[#F7A600]/20 hover:border-[#F7A600]/50 transition-all"
          >
            <svg className="w-5 h-5 text-[#F7A600]" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
              <path d="M12.028 2L7.25 6.776h3.163v5.063h3.23V6.776h3.163L12.028 2zM7.25 12.16L2.472 16.937h3.163V22h3.23v-5.063h3.163L7.25 12.16zM16.806 12.16l-4.778 4.777h3.163V22h3.23v-5.063h3.163L16.806 12.16z" />
            </svg>
            <span className="flex flex-col items-start leading-tight">
              <span className="font-medium text-[#F7A600]">{t.tradeOnBybit}</span>
              <span className="text-[10px] text-muted">{t.bybitBonus}</span>
            </span>
            <svg
              className="w-3.5 h-3.5 text-[#F7A600]/60 transition-transform group-hover:translate-x-0.5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
              aria-hidden="true"
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5 21 12m0 0-7.5 7.5M21 12H3" />
            </svg>
          </a>
        </div>

        {/* Social proof */}
        <div className="flex flex-wrap items-center justify-center gap-3 sm:gap-6 mt-12 opacity-60 px-2" style={{ animation: "fadeInUp 0.7s 0.9s cubic-bezier(0.16, 1, 0.3, 1) both" }}>
          <div className="flex items-center gap-1.5 sm:gap-2 text-[10px] sm:text-xs text-muted font-mono">
            <svg className="w-3.5 h-3.5 sm:w-4 sm:h-4 text-primary shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" /></svg>
            {t.publicTrack}
          </div>
          <div className="w-px h-4 bg-border/50 hidden sm:block" />
          <div className="flex items-center gap-1.5 sm:gap-2 text-[10px] sm:text-xs text-muted font-mono">
            <svg className="w-3.5 h-3.5 sm:w-4 sm:h-4 text-primary shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
            {t.algoTrading}
          </div>
          <div className="w-px h-4 bg-border/50 hidden sm:block" />
          <div className="flex items-center gap-1.5 sm:gap-2 text-[10px] sm:text-xs text-muted font-mono">
            <svg className="w-3.5 h-3.5 sm:w-4 sm:h-4 text-primary shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" /></svg>
            {t.openSource}
          </div>
        </div>
      </div>

      {/* Scroll hint */}
      <div className="absolute bottom-8 left-1/2 -translate-x-1/2 animate-bounce opacity-40" aria-hidden="true">
        <svg className="w-6 h-6 text-muted" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="m19 9-7 7-7-7" />
        </svg>
      </div>
    </section>
  );
}
