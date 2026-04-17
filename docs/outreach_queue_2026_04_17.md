# Backlink Outreach Queue — 2026-04-17

**Goal**: 3-5 referring domains в ближайшие 14 дней → сдвинуть индексацию (0/50 → 20+/50).

**Approach**: высокая персонализация, короткие письма, value-first.

**Success metrics**:
- Reply rate: 15%+ (industry avg ~8%)
- Backlinks secured: 3-5 (of 12 outreach)
- Time: 5 min per email

---

## Priority 1 — Guest Post Pitches (DA 60+)

### 1. CryptoPotato — crypto news + technical analysis
- **URL**: https://cryptopotato.com
- **DA**: 76
- **Contact**: editor@cryptopotato.com (guest post form: /write-for-us)
- **Angle**: "Open-source Freqtrade strategy case study — 13 days to V4 fix"
- **Email template**:
```
Subject: Guest post pitch: Open-source Freqtrade trading bot — 13-day breakeven fix

Hi CryptoPotato editors,

I run TrendRider, an open-source Freqtrade trading bot. My
live bot sat breakeven for 13 days, then I shipped a "cascading
exit" fix that turned it profitable in 8 hours.

I've written up the post-mortem with:
- SQLite trade dump (every exit reason)
- The exact strategy code change (MIT license, on GitHub)
- Before/after backtest (+69% profit, -77% drawdown)
- Live stats dashboard (public): https://trendrider.net/live

Would this work as a guest post for your technical analysis
section? Full article is here — happy to re-edit for your
style guide: https://trendrider.net/blog/freqtrade-bot-14-days-breakeven-v4-fix-2026

Best,
[Your name]
TrendRider — open-source Freqtrade strategy
https://github.com/darkvolg/trendrider-strategy
```

---

### 2. Altcoin Buzz — altcoin analysis
- **URL**: https://altcoinbuzz.io
- **DA**: 62
- **Contact**: contact@altcoinbuzz.io
- **Angle**: "7 altcoin trading strategies that actually backtest"
- **Email template**:
```
Subject: Original content pitch: 7 altcoin trading strategies (with backtest data)

Hi Altcoin Buzz team,

Noticed your altcoin strategy coverage — I've got a data-backed
piece that might fit: 7 altcoin trading strategies for 2026,
each backtested on BTC dominance gating, alt season momentum,
volume divergence, catalyst plays, and oversold mean reversion.

Real numbers from 500+ trades on SOL, BNB, DOGE, OP. No hype.

Article: https://trendrider.net/blog/altcoin-trading-strategies-2026

Happy to rewrite/trim for your audience. In return, a link
back to our open-source strategy repo would be appreciated:
https://github.com/darkvolg/trendrider-strategy

Best,
[Your name]
```

---

### 3. BeInCrypto — news + education
- **URL**: https://beincrypto.com/write-for-us
- **DA**: 75
- **Contact**: Submit via form at /write-for-us
- **Angle**: "Backtesting crypto strategies — complete guide"
- **Pitch** (submit via form):
```
Title: Backtesting Crypto Trading Strategies in 2026 — What I Learned From 10,000 Trades

Summary:
Most crypto traders skip backtesting. I backtested 10,000+ trades
across 7 different strategies and found that 5 of them fail
out-of-sample. Here's the 3-step protocol that kept me from
deploying a losing strategy live.

Includes Freqtrade code examples, walk-forward validation setup,
and real SQN scores for each strategy. Article ready.

Bio: Run TrendRider — open-source Freqtrade strategy
(github.com/darkvolg/trendrider-strategy), 65% live win rate.
```

---

### 4. HackerNoon — tech blog (crypto section)
- **URL**: https://hackernoon.com
- **DA**: 85
- **Contact**: https://hackernoon.com/write (self-publish)
- **Angle**: Technical deep-dive on cascading exit logic
- **Action**: User signs up → copies killer article (freqtrade-bot-14-days-breakeven-v4-fix-2026)
  → publishes with canonical tag pointing to trendrider.net
- **Win**: DA 85 backlink, guaranteed publish, 5 min work

---

### 5. Dev.to — additional article push
- **URL**: https://dev.to (already have account)
- **DA**: 91
- **Action**: We publish 2x/week. ADDITIONAL manual push: submit the
  killer article with NEW headline + intro re-written for devs,
  include prominent ⭐ CTA for github.com/darkvolg/trendrider-strategy
- **Status**: Can automate — I'll add option to autopilot

---

## Priority 2 — Directory Submissions (DA 40-70, fast)

### 6. CryptoJobsList Directory — trading tools listing
- **URL**: https://cryptojobslist.com/submit-project
- **DA**: 52
- **Type**: Free listing
- **Listing text**:
```
TrendRider — Open-source Freqtrade strategy
65% live win rate, MIT license, cascading exit logic.
Live stats: trendrider.net/live
GitHub: github.com/darkvolg/trendrider-strategy
```

### 7. Product Hunt — already launched? If not, relaunch "V3"
- **URL**: https://www.producthunt.com/posts/new
- **DA**: 91
- **Action**: Check if launched. If yes, skip. If no, launch Monday 00:01 PST for max exposure.

### 8. AlternativeTo — alternative to CryptoHopper/3Commas
- **URL**: https://alternativeto.net/software/trendrider
- **DA**: 78
- **Action**: Add TrendRider as alternative to 3Commas, Cryptohopper, Pionex bot

### 9. GetApp / Capterra / G2 — business software directories
- **DA**: 90+
- **Action**: Submit as "Crypto Trading Bot" category, free tier.
- **Email**: vendor-signup@[site].com

### 10. awesome-freqtrade (GitHub) — already PR'd
- **URL**: https://github.com/just-nilux/awesome-freqtrade
- **Status**: PR #1 already open (from 2026-04-14 outreach session)
- **Action**: Nothing, monitor (already in pr_monitor cron)

---

## Priority 3 — Community seeding (no direct backlink but referral traffic)

### 11. r/freqtrade (Reddit)
- **URL**: https://reddit.com/r/freqtrade
- **Status**: BLOCKED — u/TrendRiderPro karma=1, posts auto-removed.
- **Workaround**: Comment on existing posts 3-5x/day for 7 days to build karma, then post.

### 12. Freqtrade Discord — #strategies channel
- **URL**: https://discord.gg/freqtrade (find official invite)
- **Action**: Share GitHub repo link in #strategies or #showcase channel.
- **Rules**: Read the channel rules first, no spam.

---

## Execution Plan (user)

**Day 1 (today, 17 Apr)** — 30 min work:
- [ ] Send email #1 (CryptoPotato)
- [ ] Send email #2 (Altcoin Buzz)
- [ ] Submit #3 (BeInCrypto form)
- [ ] Submit HackerNoon (#4) — 5 min

**Day 2 (18 Apr)** — 20 min:
- [ ] Submit CryptoJobsList (#6)
- [ ] AlternativeTo (#8)
- [ ] GetApp/Capterra (#9)
- [ ] Discord share (#12)

**Day 3-7**: Monitor replies, respond, follow up after 5 days of no reply.

**Expected result**: 2-4 backlinks within 14 days (conservative).
Combined with IndexNow pushing Bing/Yandex daily → indexing crisis resolved in ~21 days.
