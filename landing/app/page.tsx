"use client";

import { useEffect, useRef, useState, useCallback } from "react";

/* ──────────────────────────── imports from extracted modules ──────────────────────────── */

import { TELEGRAM_URL } from "@/lib/constants";
import { T } from "@/lib/i18n";
import type { Locale } from "@/lib/i18n";
import { getSteps, getFeatures, getFaqItems } from "@/lib/data";

import {
  useInView,
  useScrollProgress,
  useFloatingVisible,
} from "@/hooks";

import {
  SocialCounter,
  LanguageToggle,
  FAQItem,
  SectionHeading,
  SectionDivider,
  ScrollToTop,
} from "@/components/ui";
import type { Theme } from "@/components/ui";

import {
  HeroSection,
  LiveTicker,
  SignalPreview,
  DashboardMockup,
  RatingSummary,
  TestimonialCard,
  ExchangeLogos,
  Footer,
  PricingGrid,
  TechStackLogos,
  ComparisonTable,
  BenefitsStrip,
  EmailCapture,
  CookieConsent,
  StickyNav,
  PerformanceDashboard,
  SimulatedPerformance,
} from "@/components/sections";

/* ──────────────────────────── Home component ──────────────────────────── */

export default function Home() {
  const [locale, setLocale] = useState<Locale>("en");
  const [exitPopupShown, setExitPopupShown] = useState(false);
  const [exitPopupDismissed, setExitPopupDismissed] = useState(false);
  const theme: Theme = "dark";
  const t = T[locale];

  const socialProofSection = useInView(0.2);
  const mediaSection = useInView(0.1);
  const securitySection = useInView(0.2);
  const dashboardSection = useInView(0.15);
  const roiSection = useInView(0.1);
  const simSection = useInView(0.1);
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
  const rafRef = useRef<number>(0);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      cancelAnimationFrame(rafRef.current);
      rafRef.current = requestAnimationFrame(() => {
        if (cursorGlowRef.current) {
          cursorGlowRef.current.style.left = `${e.clientX}px`;
          cursorGlowRef.current.style.top = `${e.clientY}px`;
        }
      });
    };
    window.addEventListener('mousemove', handler);
    return () => {
      window.removeEventListener('mousemove', handler);
      cancelAnimationFrame(rafRef.current);
    };
  }, []);


  // Exit-intent popup: show once per 3 days (localStorage)
  useEffect(() => {
    const lastShown = localStorage.getItem('exitPopupLastShown');
    const threeDays = 3 * 24 * 60 * 60 * 1000;
    if (lastShown && Date.now() - Number(lastShown) < threeDays) {
      setExitPopupDismissed(true);
      return;
    }
    const handler = (e: MouseEvent) => {
      if (e.clientY <= 0 && !exitPopupDismissed) {
        setExitPopupShown(true);
        localStorage.setItem('exitPopupLastShown', String(Date.now()));
      }
    };
    document.documentElement.addEventListener('mouseleave', handler);
    return () => document.documentElement.removeEventListener('mouseleave', handler);
  }, [exitPopupDismissed]);


  const steps = getSteps(t);
  const features = getFeatures(t);
  const faqItems = getFaqItems(t);

  const faqJsonLd = JSON.stringify({
    "@context": "https://schema.org",
    "@type": "FAQPage",
    name: "TrendRider FAQ",
    mainEntity: faqItems.map((item) => ({
      "@type": "Question",
      name: item.q,
      acceptedAnswer: { "@type": "Answer", text: item.a },
    })),
  });

  return (
    <div className="grid-bg relative">
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: faqJsonLd }} />
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
      <StickyNav
        t={t}
        locale={locale}
        setLocale={setLocale}
        navLinks={[
          { label: t.navPerformance, ref: roiSection.ref },
          { label: t.navHowItWorks, ref: howItWorks.ref },
          { label: t.navFeatures, ref: featuresSection.ref },
          { label: t.navPricing, ref: pricingSection.ref },
          { label: t.navFaq, ref: faqSection.ref },
        ]}
        pageLinks={[
          { label: t.navLive, href: "/live" },
        ]}
        githubUrl="https://github.com/darkvolg/Trading"
      />

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
      <HeroSection t={t} locale={locale} setLocale={setLocale} parallaxRef={parallaxRef} />

      {/* ─── LIVE TICKER ─── */}
      <LiveTicker />

      {/* ─── SOCIAL PROOF STRIP ─── */}
      <section ref={socialProofSection.ref} className="py-20 px-4 bg-card/20 border-y border-border/10">
        <div className="max-w-5xl mx-auto">
          <p className={`reveal ${socialProofSection.visible ? "visible" : ""} text-center text-muted text-sm uppercase tracking-widest font-mono mb-10`}>
            {t.trustedBy}
          </p>

          {/* Animated social proof counters */}
          <div className={`reveal reveal-delay-1 ${socialProofSection.visible ? "visible" : ""} grid grid-cols-3 gap-6 mb-12`}>
            {[
              { target: 150, decimals: 0, suffix: "+", label: t.socialTrades },
              { target: 99.9, decimals: 1, suffix: "%", label: t.socialUptime },
              { target: 200, decimals: 0, suffix: "+", label: t.socialSignals },
            ].map((stat) => (
              <SocialCounter key={stat.label} {...stat} active={socialProofSection.visible} />
            ))}
          </div>

          {/* Tech metrics row */}
          <div className={`reveal reveal-delay-2 ${socialProofSection.visible ? "visible" : ""} flex flex-wrap items-center justify-center gap-6 md:gap-10 mb-12 text-sm`}>
            {[
              { value: "5", label: t.metricPairs },
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

      {/* ─── SECURITY & TRUST BADGES ─── */}
      <section ref={securitySection.ref} className="py-20 px-4 bg-card/20 border-y border-border/10">
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
      <section ref={dashboardSection.ref} className="py-24 px-4">
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

      <SectionDivider variant="glow" />

      {/* ─── PERFORMANCE DASHBOARD (replaces old Metrics + ROI Calculator) ─── */}
      <PerformanceDashboard t={t} visible={roiSection.visible} sectionRef={roiSection.ref} />

      {/* ─── SIMULATED PERFORMANCE (Investment Simulator) ─── */}
      <SimulatedPerformance t={t} visible={simSection.visible} sectionRef={simSection.ref} />

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
              href="/live"
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
        <PricingGrid t={t} locale={locale} visible={pricingSection.visible} />
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
              href="/live"
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
      <Footer t={t} />

      {/* ─── COOKIE CONSENT ─── */}
      <CookieConsent t={t} locale={locale} />

      {/* ─── SCROLL TO TOP ─── */}
      <ScrollToTop />

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
