---
name: Landing page status
description: TrendRider landing — ALL 10 Phases DONE, score ~96/100, deployed on trendrider.net
type: project
---

## TrendRider Landing — Status as of 2026-03-23

**Tech:** Next.js 16.2.1, Tailwind CSS 4, `output: "export"`, path: `landing/`
**Build:** 21 static pages, 0 errors
**Theme:** Dark only (light mode removed 23.03.2026)
**Version:** v3.1.0 (commit 8555aa0)
**Score:** ~96/100

### Deploy — LIVE
- https://trendrider.net — работает с SSL (сертификат до 20.06.2026)
- trendrider.ru — DNS ещё не пропагировался, ждём + certbot
- **v3.1.0 НЕ задеплоен** — нужен scp landing/out/ → сервер

### ALL Landing Phases — DONE

| Phase | What | Version |
|-------|------|---------|
| 1-4 | Hero, CTA, i18n, Blog, Sitemap, Trust, Pricing, FAQ | v2.9.0 |
| 5 | Security badges, ratings, dashboard mockup, counters | v3.0.0 |
| 6 | ROI calculator, countdown timer, exit popup, Most Popular→Basic | v3.1.0 |
| 7 | .pro→.net, Article JSON-LD (10 posts), BreadcrumbList | v3.1.0 |
| 8 | Parallax orbs, gradient mesh, word reveal, cursor glow | v3.1.0 |
| 9 | Responsive hero, 44px touch targets, safe-area, table scroll | v3.1.0 |
| 10 | 404 page, focus-visible, theme-color, contrast fix | v3.1.0 |

### Remaining TODO:
- [ ] Деплой v3.1.0 на сервер
- [ ] SSL для trendrider.ru (ждём DNS)
- [ ] Stripe (Basic/VIP оплата)
- [ ] Email сервис (MailerLite/Resend)
- [ ] Google Analytics
- [ ] Signal Preview — починить Telegram mockup
- [ ] Синхронизировать метрики hero vs metrics секция
