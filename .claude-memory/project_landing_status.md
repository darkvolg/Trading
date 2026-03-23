---
name: Landing page status
description: TrendRider landing — deployed on trendrider.net, Phase 5 Trust DONE, moving to Phase 7 SEO
type: project
---

## TrendRider Landing — Status as of 2026-03-23

**Tech:** Next.js 16.2.1, Tailwind CSS 4, `output: "export"`, path: `landing/`
**Build:** 21 static pages, 0 errors
**Theme:** Dark only (light mode removed 23.03.2026)
**Dev server:** `npm run dev` → http://localhost:3000

### Deploy — LIVE
- https://trendrider.net — работает с SSL (сертификат до 20.06.2026)
- trendrider.ru — DNS ещё не пропагировался (NXDOMAIN на 23.03), ждём + certbot

### Phase 1-4 — DONE (ранее)
- Hero, CTA, i18n EN/RU, Signal Preview, Candlestick bg, Equity Curve
- Pricing (Free/Basic/VIP), FAQ, Blog (10 статей), Sitemap (21 URL)
- Transparency, Exchange Logos, Tech Stack, Benefits, Cookie Consent

### Phase 5 (Trust) — DONE
- [x] 5.1 Security Badges strip (4 карточки с SVG)
- [x] 5.2 Trustpilot-style рейтинг (4.8/5 с bar breakdown, в секции Testimonials)
- [x] 5.3 Dashboard mockup (browser chrome + таблица сделок, между Security и Metrics)
- [x] 5.4 Social proof animated counters (150+ trades, 71.1% WR, 99.9% uptime, 200+ signals)

### Решения принятые:
- Light mode убран — слишком много проблем с контрастом, крипто-сайты обычно dark
- ThemeToggle удалён, тема зафиксирована как "dark"

### После Phase 5 — Phases 6-10:
See [project_landing_audit.md](project_landing_audit.md) for full task list.

### После деплоя — TODO:
- [ ] SSL для trendrider.ru (ждём DNS)
- [ ] Stripe (Basic/VIP оплата)
- [ ] Email сервис (MailerLite/Resend)
- [ ] Google Analytics
- [ ] Самозанятость для приёма платежей

**Why:** Phase 1-5 полностью готовы. Следующий шаг — Phase 7 (SEO).
**How to apply:** Продолжать Phase 7 (SEO), затем 6 (Конверсия), 8 (Визуал), 9 (Mobile), 10 (Speed).
