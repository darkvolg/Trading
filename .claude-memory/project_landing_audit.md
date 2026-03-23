---
name: Landing audit & improvement plan
description: TrendRider landing — audit 73→~82/100, Phase 5 Trust DONE, Phase 7 SEO next, Phases 6-10 pending
type: project
---

## TrendRider Landing — Аудит и план улучшений

**Стартовая оценка: 73/100**
**Текущая оценка: ~82/100** (Phase 5 полностью завершена)
**Целевая оценка: 95-98/100**
**Технологии:** Next.js 16.2.1, Tailwind CSS 4, static export, i18n EN/RU

### Цветовая палитра (только dark mode!)
- Primary: `#00D4AA` (мятно-зелёный) — CTA, glow, прогресс-бары
- Accent: `#FFD700` (золотой) — VIP, звёзды, premium
- Background: `#0D1117` (GitHub dark)
- Card: `#161B22` / Danger: `#FF4757` / Muted: `#8B949E`
- **Light mode УБРАН** — только dark theme (решено 23.03.2026)

### Phase 5 (Trust) — DONE (23.03.2026):

| # | Задача | Статус |
|---|--------|--------|
| 5.1 | Security Badges strip (4 SVG карточки) | DONE |
| 5.2 | Trustpilot-style рейтинг 4.8/5 + bar breakdown | DONE |
| 5.3 | Dashboard mockup (browser chrome + таблица 6 сделок) | DONE |
| 5.4 | Animated social proof counters (150+ trades, 71.1% WR, 99.9% uptime, 200+ signals) | DONE |

### Фазы 6-10 — TODO:

| Фаза | Что | Прирост | Статус |
|------|-----|---------|--------|
| 7. SEO | FAQ/Article JSON-LD, canonical, breadcrumbs | +2.5 | NEXT |
| 6. Конверсия | ROI калькулятор, countdown, sticky CTA, exit popup | +2.5 | TODO |
| 8. Визуал | Parallax, gradient mesh, micro-interactions, анимации | +3.0 | TODO |
| 9. Mobile | Hamburger, touch targets, pricing stack | +2.5 | TODO |
| 10. Speed | Font subsetting, critical CSS, a11y, 404 page | +3.6 | TODO |

### Порядок работы:
1. ~~**Фаза 5** (Trust)~~ — DONE
2. **Фаза 7** (SEO) — быстрые wins ← СЕЙЧАС
3. **Фаза 6** (Конверсия) — ROI калькулятор
4. **Фаза 8** (Визуал)
5. **Фаза 9** (Mobile)
6. **Фаза 10** (Speed)

**Оставшееся время: ~8-10 часов** (фазы 6-10)

**Why:** Код лендинга надо довести до 95+ перед публичным запуском.
**How to apply:** Начинать Phase 7 (SEO). Заметка: FAQ JSON-LD и SoftwareApplication JSON-LD уже есть в layout.tsx. Осталось: Article JSON-LD для блог-постов, canonical URLs (metadataBase стоит на trendrider.pro — обновить на .net), breadcrumbs JSON-LD. Также metadataBase и OG url в layout.tsx указывают на trendrider.pro — нужно обновить на trendrider.net.
