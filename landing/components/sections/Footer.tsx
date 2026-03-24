import type { TStrings } from "@/lib/i18n";
import { TELEGRAM_URL, TELEGRAM_CHAT_URL, SHEETS_URL } from "@/lib/constants";

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
              <a href={TELEGRAM_URL} target="_blank" rel="noopener noreferrer" className="w-9 h-9 rounded-lg bg-card border border-border/50 flex items-center justify-center text-muted hover:text-primary hover:border-primary/30 transition-all" aria-label="Telegram">
                <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z" />
                </svg>
              </a>
              {/* X/Twitter */}
              <a href="https://x.com/TrendRiderPro" target="_blank" rel="noopener noreferrer" className="w-9 h-9 rounded-lg bg-card border border-border/50 flex items-center justify-center text-muted hover:text-primary hover:border-primary/30 transition-all" aria-label="X / Twitter">
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
              <li><a href={TELEGRAM_CHAT_URL} target="_blank" rel="noopener noreferrer" className="text-muted text-sm hover:text-primary transition-colors">{t.communityChat}</a></li>
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
  );
}
