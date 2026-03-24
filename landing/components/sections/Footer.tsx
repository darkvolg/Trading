import type { TStrings } from "@/lib/i18n";
import { TELEGRAM_URL, TELEGRAM_CHAT_URL, SHEETS_URL, BYBIT_AFFILIATE_URL } from "@/lib/constants";

export function Footer({ t }: { t: TStrings }) {
  return (
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
              <a href={TELEGRAM_URL} target="_blank" rel="noopener noreferrer" className="w-9 h-9 rounded-lg bg-card border border-border/50 flex items-center justify-center text-muted hover:text-primary hover:border-primary/30 transition-all" aria-label="Join our Telegram channel">
                <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                  <path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z" />
                </svg>
              </a>
              {/* X/Twitter */}
              <a href="https://x.com/TrendRiderPro" target="_blank" rel="noopener noreferrer" className="w-9 h-9 rounded-lg bg-card border border-border/50 flex items-center justify-center text-muted hover:text-primary hover:border-primary/30 transition-all" aria-label="Follow us on X">
                <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                  <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
                </svg>
              </a>
            </div>
          </div>

          {/* Product column */}
          <div>
            <h4 className="text-sm font-semibold text-foreground mb-4">Product</h4>
            <ul className="space-y-2.5">
              <li><a href={TELEGRAM_URL} target="_blank" rel="noopener noreferrer" className="text-muted text-sm hover:text-primary transition-colors">{t.telegramChannel}</a></li>
              <li><a href={TELEGRAM_CHAT_URL} target="_blank" rel="noopener noreferrer" className="text-muted text-sm hover:text-primary transition-colors">{t.communityChat}</a></li>
              <li><a href={SHEETS_URL} target="_blank" rel="noopener noreferrer" className="text-muted text-sm hover:text-primary transition-colors">{t.liveResults}</a></li>
              <li><a href="/blog" className="text-muted text-sm hover:text-primary transition-colors">Blog</a></li>
              <li><a href={BYBIT_AFFILIATE_URL} target="_blank" rel="noopener noreferrer" className="text-muted text-sm hover:text-[#F7A600] transition-colors">{t.tradeOnBybit}</a></li>
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

        {/* Risk disclaimer */}
        <div className="pt-8 border-t border-border/40">
          <p className="text-muted text-sm leading-relaxed max-w-3xl text-center md:text-left mb-6">
            <span className="font-semibold text-danger/80">Risk Disclaimer:</span> {t.riskDisclaimer}
          </p>
        </div>

        {/* Bottom bar */}
        <div className="flex flex-col md:flex-row items-center justify-between gap-4 pt-4 border-t border-border/20">
          <div className="flex items-center gap-4 shrink-0">
            <span className="text-muted/50 text-xs font-mono">{t.poweredBy}</span>
            <span className="text-muted/30">|</span>
            <span className="text-muted/50 text-xs">&copy; 2026 TrendRider</span>
          </div>
          <a href="/sitemap.xml" className="text-muted/50 text-xs hover:text-muted transition-colors">Sitemap</a>
        </div>
      </div>
    </footer>
  );
}
