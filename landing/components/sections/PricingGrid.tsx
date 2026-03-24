import type { TStrings } from "@/lib/i18n";
import type { Locale } from "@/lib/i18n";
import { TELEGRAM_BOT_URL } from "@/lib/constants";
import { getPricing } from "@/lib/data";
import { SectionHeading } from "@/components/ui";
import { EarlyAdopterBadge } from "./EarlyAdopterBadge";

export function PricingGrid({
  t,
  locale,
  visible,
}: {
  t: TStrings;
  locale: Locale;
  visible: boolean;
}) {
  const pricing = getPricing(t, locale);

  return (
    <div className="max-w-5xl mx-auto">
      <SectionHeading
        tag={t.priceTag}
        title={t.priceTitle}
        subtitle={t.priceSubtitle}
        visible={visible}
      />
      <div className={`reveal reveal-delay-1 ${visible ? "visible" : ""} flex justify-center mb-8`}>
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
              } pricing-card reveal reveal-delay-${i + 1} ${visible ? "visible" : ""} relative p-8 rounded-2xl h-full ${
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
                {plan.features.map((feat: string, fi: number) => (
                  <li key={fi} className="flex items-start gap-3 text-sm">
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
              {plan.price !== "$0" && (
                <a
                  href={TELEGRAM_BOT_URL + "?start=pay_usdt"}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block text-center text-xs text-muted hover:text-primary transition-colors mt-2"
                >
                  {locale === "ru" ? "Или переведите USDT напрямую" : "Or send USDT directly"}
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
  );
}
