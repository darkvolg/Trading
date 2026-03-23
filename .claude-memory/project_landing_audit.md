---
name: Landing audit completed
description: TrendRider landing — ALL phases done, score ~96/100, remaining minor fixes only
type: project
---

## TrendRider Landing — Audit Complete

**Score: ~96/100** (was 73 → 82 → 96)
**All 10 phases completed in v3.1.0**

### What was added in v3.1.0 (session 2026-03-23):

**Phase 7 (SEO):**
- trendrider.pro → trendrider.net (7 files, all URLs + emails)
- BlogPosting JSON-LD on all 10 blog posts
- BreadcrumbList JSON-LD on blog index + all posts

**Phase 6 (Conversion):**
- ROI calculator (slider $100-50K, compound 13.57%/mo, 4 period cards)
- Countdown timer on EarlyAdopterBadge (April 15, 2026 launch)
- Exit-intent popup ("Don't miss free signals", one-time per session)
- Most Popular badge moved from VIP to Basic plan

**Phase 8 (Visual):**
- Parallax on floating orbs (0.05x scroll multiplier via ref)
- Gradient mesh blob in Hero (morphing border-radius, 20s cycle)
- Staggered word reveal on SectionHeading titles
- Cursor glow (300px teal blur following mouse, desktop only)

**Phase 9 (Mobile):**
- Hero heading: text-3xl → text-8xl progressive scaling
- Hamburger: 44x44px touch target (WCAG)
- Nav links: py-4 touch targets
- Language toggle: safe-area for iPhone notch
- Comparison table: overflow-x-auto horizontal scroll
- ROI cards: responsive padding + truncate

**Phase 10 (Speed/A11y):**
- Custom 404 page (not-found.tsx)
- focus-visible outlines (#00D4AA, 2px)
- theme-color meta tag (#0D1117)
- Muted text contrast: #8B949E → #9CA3AF (6.5:1 ratio)
- Fonts already optimized (next/font + subset + swap)

### Minor remaining fixes (not blocking):
- Signal Preview Telegram mockup empty content
- Metrics inconsistency: hero 71.1% vs metrics section 69.9%
