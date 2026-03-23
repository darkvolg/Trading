"use client";

import { useEffect, useRef, useState, useCallback } from "react";

/* ──────────────────────────── imports from extracted modules ──────────────────────────── */

import { TELEGRAM_URL, SHEETS_URL } from "@/lib/constants";
import { T } from "@/lib/i18n";
import type { Locale } from "@/lib/i18n";
import { getMetrics, getSteps, getFeatures, getPricing, getFaqItems } from "@/lib/data";

import {
  useInView,
  useScrollProgress,
  useFloatingVisible,
  useNavVisible,
} from "@/hooks";

import {
  SocialCounter,
  LanguageToggle,
  MetricCard,
  FAQItem,
  SectionHeading,
  SectionDivider,
} from "@/components/ui";
import type { Theme } from "@/components/ui";

import {
  CandlestickChart,
  Particles,
  LiveTicker,
  SignalPreview,
  DashboardMockup,
  RatingSummary,
  TestimonialCard,
  ExchangeLogos,
  EquityCurve,
  EarlyAdopterBadge,
  TechStackLogos,
  ComparisonTable,
  BenefitsStrip,
  EmailCapture,
  CookieConsent,
} from "@/components/sections";

/* ──────────────────────────── Home component ──────────────────────────── */

export default function Home() {
  const [locale, setLocale] = useState<Locale>("en");
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [exitPopupShown, setExitPopupShown] = useState(false);
  const [exitPopupDismissed, setExitPopupDismissed] = useState(false);
  const [deposit, setDeposit] = useState(1000);
  const theme: Theme = "dark";
  const t = T[locale];

  const socialProofSection = useInView(0.2);
  const mediaSection = useInView(0.1);
  const securitySection = useInView(0.2);
  const dashboardSection = useInView(0.15);
  const metricsSection = useInView(0.2);
  const roiSection = useInView(0.1);
  const howItWorks = useInView(0.15);
  const signalSection = useInView(0.2);
  const featuresSection = useInView(0.1);
  const comparisonSection = useInView(0.1);
  const testimonialsSection = useInView(0.1);
  const pricingSection = useInView(0.1);
  const faqSection = useInView(0.1);
  const ctaSection = useInView(0.2);

  const scrollProgress = useScrollProgress();
  const floatingVisible = useFloatingVisible();
  const navVisible = useNavVisible();
  const parallaxRef = useRef<HTMLDivElement>(null);

  // Parallax effect for floating orbs
  useEffect(() => {
    const onScroll = () => {
      if (parallaxRef.current) {
        parallaxRef.current.style.transform = `translateY(${window.scrollY * 0.05}px)`;
      }
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  const cursorGlowRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (cursorGlowRef.current) {
        cursorGlowRef.current.style.left = `${e.clientX}px`;
        cursorGlowRef.current.style.top = `${e.clientY}px`;
      }
    };
    window.addEventListener('mousemove', handler);
    return () => window.removeEventListener('mousemove', handler);
  }, []);

  const scrollTo = useCallback((ref: React.RefObject<HTMLDivElement | null>) => {
    if (ref.current) {
      const offset = 80; // navbar height
      const top = ref.current.getBoundingClientRect().top + window.scrollY - offset;
      window.scrollTo({ top, behavior: "smooth" });
    }
  }, []);

  // Exit-intent popup: show once when cursor leaves viewport top
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (e.clientY <= 0 && !exitPopupDismissed) {
        setExitPopupShown(true);
      }
    };
    document.documentElement.addEventListener('mouseleave', handler);
    return () => document.documentElement.removeEventListener('mouseleave', handler);
  }, [exitPopupDismissed]);

  const metrics = getMetrics(t);
  const steps = getSteps(t);
  const features = getFeatures(t);
  const pricing = getPricing(t, locale);
  const faqItems = getFaqItems(t);

  return (
    <div className="grid-bg relative">
      {/* Cursor glow effect */}
      <div
        ref={cursorGlowRef}
        className="pointer-events-none fixed w-[300px] h-[300px] rounded-full opacity-[0.04] bg-primary blur-[100px] -translate-x-1/2 -translate-y-1/2 z-0 hidden md:block"
        aria-hidden="true"
      />

      {/* Skip to main content — accessibility */}
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:top-4 focus:left-4 focus:z-[100] focus:px-4 focus:py-2 focus:bg-primary focus:text-background focus:rounded-lg focus:text-sm focus:font-semibold"
      >
        Skip to main content
      </a>

      {/* Scroll progress bar */}
      <div
        className="scroll-line"
        style={{ width: `${scrollProgress}%` }}
        aria-hidden="true"
      />

      {/* ─── STICKY NAVBAR ─── */}
      <nav
        aria-label="Main navigation"
        className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
          navVisible
            ? "translate-y-0 opacity-100"
            : "-translate-y-full opacity-0 pointer-events-none"
        } bg-background/80 backdrop-blur-xl border-b border-border/50`}
      >
        <div className="max-w-5xl mx-auto flex items-center justify-between px-4 py-3">
          <span className="text-lg font-bold gradient-text">TrendRider</span>
          <div className="hidden md:flex items-center gap-6">
            {[
              { label: t.navPerformance, ref: metricsSection.ref },
              { label: t.navHowItWorks, ref: howItWorks.ref },
              { label: t.navFeatures, ref: featuresSection.ref },
              { label: t.navPricing, ref: pricingSection.ref },
              { label: t.navFaq, ref: faqSection.ref },
            ].map((item) => (
              <button
                key={item.label}
                onClick={() => scrollTo(item.ref)}
                className="text-sm text-muted hover:text-foreground transition-colors cursor-pointer"
              >
                {item.label}
              </button>
            ))}
          </div>
          <div className="flex items-center gap-2">
            <LanguageToggle locale={locale} setLocale={setLocale} />
            {/* Mobile burger */}
            <button
              className="md:hidden flex flex-col gap-1.5 p-3 min-w-[44px] min-h-[44px] items-center justify-center rounded-lg hover:bg-card/50 transition-colors"
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
              className="hidden md:flex btn-primary btn-press items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold"
            >
              <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="currentColor">
                <path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z" />
              </svg>
              {t.joinTelegram}
            </a>
          </div>
        </div>

        {/* Mobile dropdown menu */}
        <div className={`md:hidden overflow-hidden transition-all duration-300 ${mobileMenuOpen ? "max-h-96 opacity-100" : "max-h-0 opacity-0"}`}>
          <div className="px-4 pb-4 space-y-1 border-t border-border/30">
            {[
              { label: t.navPerformance, ref: metricsSection.ref },
              { label: t.navHowItWorks, ref: howItWorks.ref },
              { label: t.navFeatures, ref: featuresSection.ref },
              { label: t.navPricing, ref: pricingSection.ref },
              { label: t.navFaq, ref: faqSection.ref },
            ].map((item) => (
              <button
                key={item.label}
                onClick={() => { scrollTo(item.ref); setMobileMenuOpen(false); }}
                className="block w-full text-left py-4 px-3 text-sm text-muted hover:text-foreground hover:bg-card/30 rounded-lg transition-colors"
              >
                {item.label}
              </button>
            ))}
            <a
              href={TELEGRAM_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="btn-primary btn-press flex items-center justify-center gap-2 w-full py-3 rounded-lg text-sm font-semibold mt-2"
            >
              {t.joinTelegram}
            </a>
          </div>
        </div>
      </nav>

      {/* Floating CTA */}
      <div className={`floating-btn ${floatingVisible ? "visible" : ""}`}>
        <a
          href={TELEGRAM_URL}
          target="_blank"
          rel="noopener noreferrer"
          className="btn-primary btn-press flex items-center gap-2.5 px-5 py-3 rounded-2xl shadow-2xl text-sm font-semibold"
          aria-label={t.joinTelegramChannel}
        >
          <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
            <path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z" />
          </svg>
          {t.joinTelegram}
        </a>
      </div>

      <main id="main-content">
      {/* ─── HERO ─── */}
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

        {/* Language toggle in hero — visible before navbar appears */}
        <div className="absolute top-10 right-6 sm:top-8 sm:right-8 z-20 flex items-center gap-2">
          <LanguageToggle
            locale={locale}
            setLocale={setLocale}
            className="bg-background/80 backdrop-blur-xl"
          />
        </div>

        {/* Live badge — positioned at top of hero, above candles */}
        <div
          className="absolute top-8 left-1/2 -translate-x-1/2 z-20 inline-flex items-center gap-2 px-5 py-2.5 rounded-full border border-primary/40 bg-background/90 backdrop-blur-xl shadow-lg shadow-black/30"
          style={{ animation: "fadeInDown 0.6s ease-out forwards" }}
        >
          <span className="w-2 h-2 rounded-full bg-primary animate-pulse" />
          <span className="text-sm font-mono text-primary font-medium">{t.liveSince}</span>
          <span className="w-px h-3 bg-primary/30" />
          <span className="text-xs font-mono text-foreground/60">{t.paperVerified}</span>
        </div>

        <div className="relative text-center max-w-4xl mx-auto z-10">
          {/* Logo icon */}
          <div className="flex items-center justify-center gap-3 mb-2" style={{ animation: "fadeInUp 0.7s 0.15s cubic-bezier(0.16, 1, 0.3, 1) both" }}>
            <svg width="40" height="40" viewBox="0 0 40 40" fill="none" className="text-primary">
              <rect x="16" y="8" width="8" height="20" rx="1" fill="currentColor" opacity="0.9" />
              <line x1="20" y1="4" x2="20" y2="8" stroke="currentColor" strokeWidth="2" opacity="0.6" />
              <line x1="20" y1="28" x2="20" y2="34" stroke="currentColor" strokeWidth="2" opacity="0.6" />
              <rect x="16" y="8" width="8" height="20" rx="1" fill="currentColor" opacity="0.15">
                <animate attributeName="opacity" values="0.15;0.4;0.15" dur="3s" repeatCount="indefinite" />
              </rect>
            </svg>
          </div>

          {/* Headline — animated letter reveal */}
          <h1 className="text-3xl sm:text-4xl md:text-6xl lg:text-8xl font-bold tracking-tight mb-4"
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
            className="text-lg sm:text-xl md:text-2xl lg:text-3xl text-foreground/80 font-light mb-3 tracking-wide"
            style={{ animation: "fadeInUp 0.7s 0.35s cubic-bezier(0.16, 1, 0.3, 1) both" }}
          >
            {t.tagline}{" "}
            <span className="text-primary font-normal">{t.taglineHighlight}</span>
          </p>

          <p
            className="text-muted max-w-xl mx-auto mb-10 leading-relaxed text-base md:text-lg"
            style={{ animation: "fadeInUp 0.7s 0.5s cubic-bezier(0.16, 1, 0.3, 1) both" }}
          >
            {t.heroDesc}
          </p>

          {/* Quick stats row */}
          <div
            className="flex items-center justify-center gap-6 md:gap-10 mb-10 text-sm"
            style={{ animation: "fadeInUp 0.7s 0.6s cubic-bezier(0.16, 1, 0.3, 1) both" }}
          >
            {[
              { v: "71.1%", l: t.winRate },
              { v: "2.09x", l: t.profitFactor },
              { v: "1.81%", l: t.maxDD },
            ].map(stat => (
              <div key={stat.l} className="text-center">
                <div className="font-mono font-bold text-xl text-primary">{stat.v}</div>
                <div className="text-muted text-xs uppercase tracking-wider mt-0.5">{stat.l}</div>
              </div>
            ))}
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
              <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
                <path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z" />
              </svg>
              {t.joinTelegramChannel}
              <svg
                className="w-4 h-4 transition-transform group-hover:translate-x-1"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
              >
                <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5 21 12m0 0-7.5 7.5M21 12H3" />
              </svg>
            </a>
            <a
              href={SHEETS_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="btn-press flex items-center gap-3 px-8 py-4 border border-border text-foreground font-medium rounded-xl hover:bg-card/50 hover:border-primary/30 transition-all text-sm md:text-base"
            >
              <svg className="w-5 h-5 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 0 1 3 19.875v-6.75ZM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V8.625ZM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V4.125Z" />
              </svg>
              {t.viewLiveResults}
            </a>
          </div>

          {/* Social proof */}
          <div className="flex items-center justify-center gap-6 mt-12 opacity-60" style={{ animation: "fadeInUp 0.7s 0.9s cubic-bezier(0.16, 1, 0.3, 1) both" }}>
            <div className="flex items-center gap-2 text-xs text-muted font-mono">
              <svg className="w-4 h-4 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" /></svg>
              {t.publicTrack}
            </div>
            <div className="w-px h-4 bg-border/50" />
            <div className="flex items-center gap-2 text-xs text-muted font-mono">
              <svg className="w-4 h-4 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
              {t.algoTrading}
            </div>
            <div className="w-px h-4 bg-border/50" />
            <div className="flex items-center gap-2 text-xs text-muted font-mono">
              <svg className="w-4 h-4 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" /></svg>
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

      {/* ─── LIVE TICKER ─── */}
      <LiveTicker />

      {/* ─── SOCIAL PROOF STRIP ─── */}
      <section ref={socialProofSection.ref} className="py-16 px-4">
        <div className="max-w-5xl mx-auto">
          <p className={`reveal ${socialProofSection.visible ? "visible" : ""} text-center text-muted text-sm uppercase tracking-widest font-mono mb-10`}>
            {t.trustedBy}
          </p>

          {/* Animated social proof counters */}
          <div className={`reveal reveal-delay-1 ${socialProofSection.visible ? "visible" : ""} grid grid-cols-2 md:grid-cols-4 gap-6 mb-12`}>
            {[
              { target: 150, decimals: 0, suffix: "+", label: t.socialTrades },
              { target: 71.1, decimals: 1, suffix: "%", label: t.socialWinRate },
              { target: 99.9, decimals: 1, suffix: "%", label: t.socialUptime },
              { target: 200, decimals: 0, suffix: "+", label: t.socialSignals },
            ].map((stat) => (
              <SocialCounter key={stat.label} {...stat} active={socialProofSection.visible} />
            ))}
          </div>

          {/* Tech metrics row */}
          <div className={`reveal reveal-delay-2 ${socialProofSection.visible ? "visible" : ""} flex flex-wrap items-center justify-center gap-6 md:gap-10 mb-12 text-sm`}>
            {[
              { value: "4", label: t.metricPairs },
              { value: "4", label: t.metricTimeframes },
              { value: "15+", label: t.metricIndicators },
              { value: "3", label: t.metricExchanges },
            ].map((stat) => (
              <div key={stat.label} className="text-center">
                <div className="font-mono text-xl font-bold text-foreground/70 mb-0.5">{stat.value}</div>
                <div className="text-[10px] text-muted uppercase tracking-wider">{stat.label}</div>
              </div>
            ))}
          </div>

          {/* Exchange logos */}
          <ExchangeLogos visible={socialProofSection.visible} />
        </div>
      </section>

      {/* ─── AS SEEN IN (Media) ─── */}
      <div ref={mediaSection.ref}>
        <TechStackLogos visible={mediaSection.visible} label={t.asSeenIn} />
      </div>

      {/* ─── BENEFITS STRIP ─── */}
      <BenefitsStrip t={t} visible={mediaSection.visible} />

      <SectionDivider variant="glow" />

      {/* ─── SECURITY & TRUST BADGES ─── */}
      <section ref={securitySection.ref} className="py-16 px-4">
        <div className="max-w-5xl mx-auto">
          <p className={`reveal ${securitySection.visible ? "visible" : ""} text-center text-muted text-sm uppercase tracking-widest font-mono mb-10`}>
            {t.securityTag}
          </p>
          <div className={`reveal reveal-delay-1 ${securitySection.visible ? "visible" : ""} grid grid-cols-2 md:grid-cols-4 gap-4 md:gap-6`}>
            {[
              { icon: (
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 1 0-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 0 0 2.25-2.25v-6.75a2.25 2.25 0 0 0-2.25-2.25H6.75a2.25 2.25 0 0 0-2.25 2.25v6.75a2.25 2.25 0 0 0 2.25 2.25Z" />
                </svg>
              ), title: t.secBadge1, desc: t.secBadge1Desc },
              { icon: (
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M17.25 6.75 22.5 12l-5.25 5.25m-10.5 0L1.5 12l5.25-5.25m7.5-3-4.5 16.5" />
                </svg>
              ), title: t.secBadge2, desc: t.secBadge2Desc },
              { icon: (
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9.75 3.104v5.714a2.25 2.25 0 0 1-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 0 1 4.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0 1 12 15a9.065 9.065 0 0 0-6.23.693L5 14.5m14.8.8 1.402 1.402c1.232 1.232.65 3.318-1.067 3.611A48.309 48.309 0 0 1 12 21c-2.773 0-5.491-.235-8.135-.687-1.718-.293-2.3-2.379-1.067-3.61L5 14.5" />
                </svg>
              ), title: t.secBadge3, desc: t.secBadge3Desc },
              { icon: (
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 3v11.25A2.25 2.25 0 0 0 6 16.5h2.25M3.75 3h-1.5m1.5 0h16.5m0 0h1.5m-1.5 0v11.25A2.25 2.25 0 0 1 18 16.5h-2.25m-7.5 0h7.5m-7.5 0-1 3m8.5-3 1 3m0 0 .5 1.5m-.5-1.5h-9.5m0 0-.5 1.5m.75-9 3-3 2.148 2.148A12.061 12.061 0 0 1 16.5 7.605" />
                </svg>
              ), title: t.secBadge4, desc: t.secBadge4Desc },
            ].map((badge) => (
              <div key={badge.title} className="security-badge text-center p-5 rounded-xl border border-border/50 bg-card/30 hover:border-primary/30 transition-all group">
                <div className="w-12 h-12 mx-auto mb-3 rounded-full bg-primary/10 flex items-center justify-center text-primary group-hover:bg-primary/15 transition-colors">
                  {badge.icon}
                </div>
                <h4 className="font-semibold text-sm mb-1">{badge.title}</h4>
                <p className="text-muted text-xs leading-relaxed">{badge.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── DASHBOARD MOCKUP ─── */}
      <section ref={dashboardSection.ref} className="py-20 px-4">
        <div className="max-w-5xl mx-auto">
          <SectionHeading
            tag={t.dashboardTag}
            title={t.dashboardTitle}
            subtitle={t.dashboardSubtitle}
            visible={dashboardSection.visible}
          />
          <DashboardMockup t={t} visible={dashboardSection.visible} />
        </div>
      </section>

      <SectionDivider variant="dots" />

      {/* ─── METRICS ─── */}
      <section ref={metricsSection.ref} className="py-24 px-4">
        <div className="max-w-5xl mx-auto">
          <SectionHeading
            tag={t.metricsTag}
            title={t.metricsTitle}
            subtitle={t.metricsSubtitle}
            visible={metricsSection.visible}
          />
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 md:gap-6">
            {metrics.map((m, i) => (
              <MetricCard key={m.label} {...m} active={metricsSection.visible} delay={i + 1} />
            ))}
          </div>
          <EquityCurve label={t.equityCurveLabel} visible={metricsSection.visible} />

          <p
            className={`reveal reveal-delay-6 ${metricsSection.visible ? "visible" : ""} text-center text-muted text-sm mt-8`}
          >
            {t.metricsFooter} &bull; {t.updatedMonthly} &bull;{" "}
            <a
              href={SHEETS_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="text-primary hover:underline underline-offset-4"
            >
              {t.viewFullResults}
            </a>
          </p>
        </div>
      </section>

      <SectionDivider variant="dots" />


      {/* ─── ROI CALCULATOR ─── */}
      <section ref={roiSection.ref} className="py-24 px-4">
        <div className="max-w-4xl mx-auto">
          <SectionHeading
            tag={t.roiTag}
            title={t.roiTitle}
            subtitle={t.roiSubtitle}
            visible={roiSection.visible}
          />

          {/* Deposit slider */}
          <div
            className={`reveal reveal-delay-1 ${roiSection.visible ? "visible" : ""} max-w-xl mx-auto mb-12`}
          >
            <label className="block text-sm font-mono uppercase tracking-wider text-muted mb-3 text-center">
              {t.roiDeposit}
            </label>
            <div className="text-4xl font-bold text-center mb-4 text-primary">
              {"$"}{deposit.toLocaleString("en-US")}
            </div>
            <input
              type="range"
              min={100}
              max={50000}
              step={100}
              value={deposit}
              onChange={(e) => setDeposit(Number(e.target.value))}
              className="w-full h-2 rounded-full appearance-none cursor-pointer"
              style={{
                background: `linear-gradient(to right, #00D4AA ${((deposit - 100) / (50000 - 100)) * 100}%, rgba(255,255,255,0.1) ${((deposit - 100) / (50000 - 100)) * 100}%)`,
              }}
            />
            <div className="flex justify-between text-xs text-muted mt-2 font-mono">
              <span>$100</span>
              <span>$50,000</span>
            </div>
          </div>

          {/* Result cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {([
              { label: t.roiMonth1, months: 1 },
              { label: t.roiMonth3, months: 3 },
              { label: t.roiMonth6, months: 6 },
              { label: t.roiMonth12, months: 12 },
            ] as const).map((item, i) => {
              const result = deposit * Math.pow(1.1357, item.months);
              const profit = result - deposit;
              const pctGain = ((result / deposit - 1) * 100).toFixed(1);
              return (
                <div
                  key={item.months}
                  className={`reveal reveal-delay-${i + 2} ${roiSection.visible ? "visible" : ""} relative p-4 md:p-6 rounded-2xl border border-border/50 bg-background/50 backdrop-blur-sm hover:border-primary/30 transition-all text-center`}
                >
                  <p className="text-xs font-mono uppercase tracking-wider text-muted mb-2">
                    {item.label}
                  </p>
                  <p className="text-xl sm:text-2xl md:text-3xl font-bold mb-1 truncate" style={{ color: "#00D4AA" }}>
                    {"$"}{result.toLocaleString("en-US", { maximumFractionDigits: 0 })}
                  </p>
                  <p className="text-xs sm:text-sm font-semibold truncate" style={{ color: "#FFD700" }}>
                    {`+$${profit.toLocaleString("en-US", { maximumFractionDigits: 0 })} (${pctGain}%)`}
                  </p>
                </div>
              );
            })}
          </div>

          {/* Disclaimer */}
          <p
            className={`reveal reveal-delay-6 ${roiSection.visible ? "visible" : ""} text-center text-xs text-muted/70 mt-8 max-w-lg mx-auto`}
          >
            {t.roiDisclaimer}
          </p>
        </div>
      </section>

      <SectionDivider variant="dots" />
      {/* ─── HOW IT WORKS ─── */}
      <section ref={howItWorks.ref} className="py-24 px-4 bg-card/20">
        <div className="max-w-5xl mx-auto">
          <SectionHeading
            tag={t.howTag}
            title={t.howTitle}
            subtitle={t.howSubtitle}
            visible={howItWorks.visible}
          />
          <div className="grid md:grid-cols-3 gap-8 relative">
            {steps.map((step, i) => (
              <div
                key={step.num}
                className={`reveal reveal-delay-${i + 1} ${howItWorks.visible ? "visible" : ""} step-card relative p-8 rounded-2xl border border-border/50 bg-background/50 backdrop-blur-sm hover:border-primary/30 transition-all group`}
              >
                <span className="absolute top-4 right-4 font-mono text-6xl font-bold text-primary/8 group-hover:text-primary/15 transition-colors select-none">
                  {step.num}
                </span>
                <div className="w-14 h-14 flex items-center justify-center rounded-xl bg-primary/10 text-primary mb-6 group-hover:bg-primary/15 transition-colors">
                  {step.icon}
                </div>
                <h3 className="text-xl font-semibold mb-3">{step.title}</h3>
                <p className="text-muted leading-relaxed text-sm">{step.desc}</p>

                {/* Connector line (desktop only, between cards) */}
                {i < steps.length - 1 && (
                  <div
                    className="hidden md:block absolute top-[44px] left-[calc(100%-12px)] w-8 h-px opacity-30"
                    style={{ background: "linear-gradient(90deg, #00D4AA, transparent)" }}
                    aria-hidden="true"
                  />
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      <SectionDivider variant="glow" />

      {/* ─── SIGNAL PREVIEW ─── */}
      <section ref={signalSection.ref} className="py-24 px-4">
        <div className="max-w-5xl mx-auto">
          <SectionHeading
            tag={t.previewTag}
            title={t.previewTitle}
            subtitle={t.previewSubtitle}
            visible={signalSection.visible}
          />
          <div
            className={`reveal reveal-delay-3 ${signalSection.visible ? "visible" : ""}`}
          >
            <SignalPreview visible={signalSection.visible} />
          </div>
        </div>
      </section>

      <SectionDivider variant="dots" />

      {/* ─── FEATURES ─── */}
      <section ref={featuresSection.ref} className="py-24 px-4 bg-card/20">
        <div className="max-w-5xl mx-auto">
          <SectionHeading
            tag={t.featTag}
            title={t.featTitle}
            subtitle={t.featSubtitle}
            visible={featuresSection.visible}
          />
          <div className="grid md:grid-cols-3 gap-6">
            {features.map((f, i) => (
              <div
                key={f.title}
                className={`reveal reveal-delay-${i + 1} ${featuresSection.visible ? "visible" : ""} feature-card group p-6 rounded-xl border border-border/50 bg-background/50`}
              >
                {f.icon}
                <h3 className="text-lg font-semibold mb-2">{f.title}</h3>
                <p className="text-muted text-sm leading-relaxed">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <SectionDivider variant="dots" />

      {/* ─── COMPARISON TABLE ─── */}
      <section ref={comparisonSection.ref} className="py-24 px-4">
        <div className="max-w-5xl mx-auto">
          <SectionHeading
            tag={t.comparisonTag}
            title={t.comparisonTitle}
            subtitle={t.comparisonSubtitle}
            visible={comparisonSection.visible}
          />
          <ComparisonTable t={t} visible={comparisonSection.visible} />
        </div>
      </section>

      <SectionDivider variant="glow" />

      {/* ─── TRANSPARENCY / VERIFIED ON ─── */}
      <section className="py-24 px-4">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-16">
            <span className="inline-block px-4 py-1.5 text-xs font-mono uppercase tracking-widest text-primary border border-primary/30 rounded-full mb-5">
              {t.transparencyTag}
            </span>
            <h2 className="text-3xl md:text-4xl lg:text-5xl font-bold mb-4 tracking-tight">
              {t.transparencyTitle}
            </h2>
            <p className="text-muted max-w-2xl mx-auto text-lg leading-relaxed">
              {t.transparencySubtitle}
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-6 mb-10">
            {/* Public Trade Log */}
            <a
              href={SHEETS_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="transparency-card group p-6 rounded-2xl border border-primary/20 bg-primary/[0.03] hover:bg-primary/[0.06] hover:border-primary/40"
            >
              <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center text-primary mb-4 group-hover:scale-110 transition-transform">
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M3.375 19.5h17.25m-17.25 0a1.125 1.125 0 0 1-1.125-1.125M3.375 19.5h7.5c.621 0 1.125-.504 1.125-1.125m-9.75 0V5.625m0 12.75v-1.5c0-.621.504-1.125 1.125-1.125m18.375 2.625V5.625m0 12.75c0 .621-.504 1.125-1.125 1.125m1.125-1.125v-1.5c0-.621-.504-1.125-1.125-1.125m0 3.75h-7.5A1.125 1.125 0 0 1 12 18.375m9.75-12.75c0-.621-.504-1.125-1.125-1.125H3.375c-.621 0-1.125.504-1.125 1.125m19.5 0v1.5c0 .621-.504 1.125-1.125 1.125M2.25 5.625v1.5c0 .621.504 1.125 1.125 1.125m0 0h17.25m-17.25 0h7.5c.621 0 1.125.504 1.125 1.125M3.375 8.25c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125m17.25-3.75h-7.5c-.621 0-1.125.504-1.125 1.125m8.625-1.125c.621 0 1.125.504 1.125 1.125v1.5c0 .621-.504 1.125-1.125 1.125m-17.25 0h7.5m-7.5 0c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125M12 10.875v-1.5m0 1.5c0 .621-.504 1.125-1.125 1.125M12 10.875c0 .621.504 1.125 1.125 1.125m-2.25 0c.621 0 1.125.504 1.125 1.125M13.125 12h7.5m-7.5 0c-.621 0-1.125.504-1.125 1.125M20.625 12c.621 0 1.125.504 1.125 1.125v1.5c0 .621-.504 1.125-1.125 1.125m-17.25 0h7.5M12 14.625v-1.5m0 1.5c0 .621-.504 1.125-1.125 1.125M12 14.625c0 .621.504 1.125 1.125 1.125m-2.25 0c.621 0 1.125.504 1.125 1.125m0 0v1.5c0 .621-.504 1.125-1.125 1.125" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold mb-2">{t.transparencySheet}</h3>
              <p className="text-muted text-sm leading-relaxed">{t.transparencySheetDesc}</p>
              <span className="inline-flex items-center gap-1.5 mt-4 text-primary text-sm font-medium group-hover:gap-2.5 transition-all">
                {t.verifyYourself}
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5 21 12m0 0-7.5 7.5M21 12H3" />
                </svg>
              </span>
            </a>

            {/* Open-Source Strategy */}
            <div className="transparency-card p-6 rounded-2xl border border-border/50 bg-card/30 hover:border-primary/20">
              <div className="w-12 h-12 rounded-xl bg-violet-500/10 flex items-center justify-center text-violet-400 mb-4">
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M17.25 6.75 22.5 12l-5.25 5.25m-10.5 0L1.5 12l5.25-5.25m7.5-3-4.5 16.5" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold mb-2">{t.transparencyGithub}</h3>
              <p className="text-muted text-sm leading-relaxed">{t.transparencyGithubDesc}</p>
            </div>

            {/* Paper-Trading Phase */}
            <div className="transparency-card p-6 rounded-2xl border border-border/50 bg-card/30 hover:border-primary/20">
              <div className="w-12 h-12 rounded-xl bg-amber-500/10 flex items-center justify-center text-amber-400 mb-4">
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75m-3-7.036A11.959 11.959 0 0 1 3.598 6 11.99 11.99 0 0 0 3 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285Z" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold mb-2">{t.transparencyPaper}</h3>
              <p className="text-muted text-sm leading-relaxed">{t.transparencyPaperDesc}</p>
            </div>
          </div>
        </div>
      </section>

      <SectionDivider variant="dots" />

      {/* ─── TESTIMONIALS ─── */}
      <section ref={testimonialsSection.ref} className="py-24 px-4 bg-card/20">
        <div className="max-w-5xl mx-auto">
          <SectionHeading
            tag={t.testimonialsTag}
            title={t.testimonialsTitle}
            subtitle={t.testimonialsSubtitle}
            visible={testimonialsSection.visible}
          />
          <RatingSummary t={t} visible={testimonialsSection.visible} />
          <div className="grid md:grid-cols-3 gap-6 mb-6">
            <TestimonialCard quote={t.testimonial1} author={t.testimonial1Author} role={t.testimonial1Role} delay={1} visible={testimonialsSection.visible} />
            <TestimonialCard quote={t.testimonial2} author={t.testimonial2Author} role={t.testimonial2Role} delay={2} visible={testimonialsSection.visible} />
            <TestimonialCard quote={t.testimonial3} author={t.testimonial3Author} role={t.testimonial3Role} delay={3} visible={testimonialsSection.visible} />
          </div>
          <div className="grid md:grid-cols-2 gap-6 max-w-2xl mx-auto">
            <TestimonialCard quote={t.testimonial4} author={t.testimonial4Author} role={t.testimonial4Role} delay={4} visible={testimonialsSection.visible} />
            <TestimonialCard quote={t.testimonial5} author={t.testimonial5Author} role={t.testimonial5Role} delay={5} visible={testimonialsSection.visible} />
          </div>
        </div>
      </section>

      <SectionDivider variant="glow" />

      {/* ─── PRICING ─── */}
      <section ref={pricingSection.ref} className="py-24 px-4">
        <div className="max-w-5xl mx-auto">
          <SectionHeading
            tag={t.priceTag}
            title={t.priceTitle}
            subtitle={t.priceSubtitle}
            visible={pricingSection.visible}
          />
          <div className={`reveal reveal-delay-1 ${pricingSection.visible ? "visible" : ""} flex justify-center mb-8`}>
            <EarlyAdopterBadge label={t.earlyAdopterLabel} daysLeftLabel={t.daysLeft} />
          </div>

          <div className="grid md:grid-cols-3 gap-6 max-w-4xl mx-auto items-start">
            {pricing.map((plan, i) => {
              const isPopular = plan.highlight;
              const isVip = plan.name === "VIP";
              const cardContent = (
                <div
                  className={`${isVip ? "vip-card-inner" : ""} ${
                    isVip ? "animate-pulse-glow-gold" : ""
                  } pricing-card reveal reveal-delay-${i + 1} ${pricingSection.visible ? "visible" : ""} relative p-8 rounded-2xl h-full ${
                    isVip
                      ? "bg-[#0f1a0f]"
                      : isPopular
                        ? "glass border-primary/30 shadow-[0_0_20px_rgba(0,212,170,0.1)]"
                        : "glass hover:border-primary/20"
                  }`}
                >
                  {isPopular && (
                    <div className="absolute -top-3 left-1/2 -translate-x-1/2 z-10">
                      <span className="px-4 py-1 bg-primary text-background text-xs font-bold rounded-full uppercase tracking-wider">
                        {t.mostPopular}
                      </span>
                    </div>
                  )}
                  <div className="mb-6">
                    <h3
                      className={`text-lg font-semibold mb-2 ${isVip ? "gold-gradient-text" : "text-foreground"}`}
                    >
                      {plan.name}
                    </h3>
                    <div className="flex items-baseline gap-1">
                      <span className={`font-mono text-4xl font-bold ${isVip ? "gold-gradient-text" : ""}`}>
                        {plan.price}
                      </span>
                      <span className="text-muted text-sm">{plan.period}</span>
                    </div>
                  </div>
                  <ul className="space-y-3 mb-8">
                    {plan.features.map((feat) => (
                      <li key={feat} className="flex items-start gap-3 text-sm">
                        <svg
                          className={`w-5 h-5 shrink-0 mt-0.5 ${isVip ? "text-accent" : "text-primary"}`}
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                          strokeWidth={2}
                        >
                          <path strokeLinecap="round" strokeLinejoin="round" d="m4.5 12.75 6 6 9-13.5" />
                        </svg>
                        <span className="text-muted">{feat}</span>
                      </li>
                    ))}
                  </ul>
                  <a
                    href={plan.href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className={`btn-press block w-full text-center py-3.5 rounded-xl font-semibold transition-all ${
                      isVip
                        ? "bg-accent text-background hover:brightness-110"
                        : isPopular
                          ? "bg-primary text-background hover:brightness-110"
                          : "border border-border text-foreground hover:bg-card/50 hover:border-primary/30"
                    }`}
                  >
                    {plan.cta}
                  </a>
                  {plan.cryptoHref && (
                    <a
                      href={plan.cryptoHref}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="block text-center text-xs text-muted hover:text-primary transition-colors mt-2"
                    >
                      💎 {t.payWithCrypto}
                    </a>
                  )}
                </div>
              );

              return isVip ? (
                <div key={plan.name} className="vip-card-wrapper">
                  {cardContent}
                </div>
              ) : (
                <div key={plan.name} className="h-full">
                  {cardContent}
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* ─── FAQ ─── */}
      <section ref={faqSection.ref} className="py-24 px-4 bg-card/20">
        <div className="max-w-3xl mx-auto">
          <SectionHeading
            tag={t.faqTag}
            title={t.faqTitle}
            visible={faqSection.visible}
          />
          <div
            className={`reveal reveal-delay-2 ${faqSection.visible ? "visible" : ""} space-y-3`}
          >
            {faqItems.map((item) => (
              <FAQItem key={item.q} {...item} />
            ))}
          </div>
        </div>
      </section>

      {/* ─── CTA BANNER ─── */}
      <section ref={ctaSection.ref} className="py-28 px-4">
        <div
          className={`reveal ${ctaSection.visible ? "visible" : ""} cta-glow max-w-3xl mx-auto text-center p-12 rounded-3xl border border-primary/10 bg-primary/3`}
        >
          <div className="mb-2">
            <span className="inline-block px-4 py-1.5 text-xs font-mono uppercase tracking-widest text-primary border border-primary/30 rounded-full">
              {t.ctaTag}
            </span>
          </div>
          <h2
            className={`reveal reveal-delay-1 ${ctaSection.visible ? "visible" : ""} text-3xl md:text-5xl font-bold mt-6 mb-4 tracking-tight`}
          >
            {t.ctaTitle}{" "}
            <span className="gradient-text">{t.ctaTitleHighlight}</span>?
          </h2>
          <p
            className={`reveal reveal-delay-2 ${ctaSection.visible ? "visible" : ""} text-muted mb-10 text-lg leading-relaxed`}
          >
            {t.ctaDesc}
            <br />
            <span className="text-foreground/60 text-base">{t.ctaSubDesc}</span>
          </p>
          <div
            className={`reveal reveal-delay-3 ${ctaSection.visible ? "visible" : ""} flex flex-col sm:flex-row items-center justify-center gap-4`}
          >
            <a
              href={TELEGRAM_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="btn-primary btn-press inline-flex items-center gap-3 px-10 py-4 rounded-xl font-semibold text-lg animate-pulse-glow"
            >
              <svg className="w-6 h-6" viewBox="0 0 24 24" fill="currentColor">
                <path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z" />
              </svg>
              {t.getStarted}
            </a>
            <a
              href={SHEETS_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="btn-press flex items-center gap-2 px-6 py-4 text-muted hover:text-foreground transition-colors text-sm font-medium"
            >
              {t.viewAllResults}
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5 21 12m0 0-7.5 7.5M21 12H3" />
              </svg>
            </a>
          </div>
        </div>
      </section>
      {/* ─── EMAIL CAPTURE ─── */}
      <EmailCapture t={t} />

      </main>

      {/* ─── FOOTER ─── */}
      <footer className="border-t border-border/40 py-16 px-4">
        <div className="max-w-5xl mx-auto">
          {/* Top row: brand + nav columns */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-10 mb-12">
            {/* Brand */}
            <div className="md:col-span-1">
              <span className="text-xl font-bold gradient-text">TrendRider</span>
              <p className="text-muted text-sm mt-2 leading-relaxed">{t.footerTagline}</p>
              {/* Social icons */}
              <div className="flex items-center gap-3 mt-4">
                {/* Telegram */}
                <a href={TELEGRAM_URL} target="_blank" rel="noopener noreferrer" className="w-9 h-9 rounded-lg bg-card border border-border/50 flex items-center justify-center text-muted hover:text-primary hover:border-primary/30 transition-all" aria-label="Telegram">
                  <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z" />
                  </svg>
                </a>
                {/* X/Twitter */}
                <a href="https://x.com/TrendRiderBot" target="_blank" rel="noopener noreferrer" className="w-9 h-9 rounded-lg bg-card border border-border/50 flex items-center justify-center text-muted hover:text-primary hover:border-primary/30 transition-all" aria-label="X / Twitter">
                  <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
                  </svg>
                </a>
                {/* Discord */}
                <a href="https://discord.gg/trendrider" target="_blank" rel="noopener noreferrer" className="w-9 h-9 rounded-lg bg-card border border-border/50 flex items-center justify-center text-muted hover:text-primary hover:border-primary/30 transition-all" aria-label="Discord">
                  <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0 12.64 12.64 0 0 0-.617-1.25.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057 19.9 19.9 0 0 0 5.993 3.03.078.078 0 0 0 .084-.028 14.09 14.09 0 0 0 1.226-1.994.076.076 0 0 0-.041-.106 13.107 13.107 0 0 1-1.872-.892.077.077 0 0 1-.008-.128 10.2 10.2 0 0 0 .372-.292.074.074 0 0 1 .077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127 12.299 12.299 0 0 1-1.873.892.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028 19.839 19.839 0 0 0 6.002-3.03.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.03zM8.02 15.33c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.956-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.956 2.418-2.157 2.418zm7.975 0c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.955-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.946 2.418-2.157 2.418z" />
                  </svg>
                </a>
              </div>
            </div>

            {/* Product column */}
            <div>
              <h4 className="text-sm font-semibold text-foreground mb-4">Product</h4>
              <ul className="space-y-2.5">
                <li><a href={TELEGRAM_URL} target="_blank" rel="noopener noreferrer" className="text-muted text-sm hover:text-primary transition-colors">{t.telegramChannel}</a></li>
                <li><a href={SHEETS_URL} target="_blank" rel="noopener noreferrer" className="text-muted text-sm hover:text-primary transition-colors">{t.liveResults}</a></li>
              </ul>
            </div>

            {/* Legal column */}
            <div>
              <h4 className="text-sm font-semibold text-foreground mb-4">Legal</h4>
              <ul className="space-y-2.5">
                <li><a href="/terms" className="text-muted text-sm hover:text-primary transition-colors">{t.termsOfService}</a></li>
                <li><a href="/privacy" className="text-muted text-sm hover:text-primary transition-colors">{t.privacyPolicy}</a></li>
              </ul>
            </div>

            {/* Contact column */}
            <div>
              <h4 className="text-sm font-semibold text-foreground mb-4">{t.contactUs}</h4>
              <ul className="space-y-2.5">
                <li><a href="mailto:support@trendrider.net" className="text-muted text-sm hover:text-primary transition-colors">support@trendrider.net</a></li>
                <li><a href={TELEGRAM_URL} target="_blank" rel="noopener noreferrer" className="text-muted text-sm hover:text-primary transition-colors">@TrendRiderSupport</a></li>
              </ul>
            </div>
          </div>

          {/* Disclaimer + bottom bar */}
          <div className="flex flex-col md:flex-row items-center justify-between gap-4 pt-8 border-t border-border/30">
            <p className="text-muted text-xs leading-relaxed max-w-2xl text-center md:text-left">
              <span className="font-semibold text-danger/80">Risk Disclaimer:</span> {t.riskDisclaimer}
            </p>
            <div className="flex items-center gap-4 shrink-0">
              <span className="text-muted/50 text-xs font-mono">{t.poweredBy}</span>
              <span className="text-muted/30">|</span>
              <span className="text-muted/50 text-xs">&copy; 2026 TrendRider</span>
            </div>
          </div>
        </div>
      </footer>

      {/* ─── COOKIE CONSENT ─── */}
      <CookieConsent t={t} />

      {/* ─── EXIT-INTENT POPUP ─── */}
      {exitPopupShown && !exitPopupDismissed && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm" onClick={() => { setExitPopupShown(false); setExitPopupDismissed(true); }}>
          <div className="relative max-w-md mx-4 p-8 rounded-2xl glass border border-primary/30 text-center" onClick={e => e.stopPropagation()}>
            <button onClick={() => { setExitPopupShown(false); setExitPopupDismissed(true); }} className="absolute top-3 right-3 text-muted hover:text-foreground text-xl">&times;</button>
            <div className="text-4xl mb-4">{"\u{1F4E1}"}</div>
            <h3 className="text-xl font-bold text-foreground mb-2">{t.exitTitle}</h3>
            <p className="text-muted mb-6">{t.exitText}</p>
            <a href="https://t.me/TrendRiderSignals" target="_blank" rel="noopener noreferrer" className="inline-block px-6 py-3 bg-primary text-background font-semibold rounded-xl hover:brightness-110 transition-all">
              {t.exitCta}
            </a>
          </div>
        </div>
      )}
    </div>
  );
}
