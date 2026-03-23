---
name: TrendRider domains
description: Registered domains trendrider.ru and trendrider.net — expiry dates, registrar, DNS setup status
type: project
---

## Домены TrendRider

Зарегистрированы **23.03.2026** на SpaceWeb (sweb.ru), аккаунт: trendridru

| Домен | Оплачен до | Назначение |
|-------|:----------:|------------|
| **trendrider.ru** | **23.03.2027** | Русскоязычная аудитория (РФ/СНГ) |
| **trendrider.net** | **23.03.2027** | Международная аудитория |

**Стоимость:** trendrider.ru — 179₽, trendrider.net — 1 590₽ (итого 1 769₽)
**Продление:** .ru — 299₽/год, .net — 1 590₽/год

**Why:** .ru для российского рынка, .net для международного. trendrider.com занят с 2000 года, .pro тоже занят.
**How to apply:** Напоминание о продлении — март 2027. DNS нужно направить A-записью на Senko (144.31.63.133).

### DNS — DONE (23.03.2026)
- [x] A-запись @ → 144.31.63.133 (trendrider.net) — через DNS-записи SpaceWeb
- [x] A-запись www → 144.31.63.133 (trendrider.net)
- [x] A-запись @ → 144.31.63.133 (trendrider.ru) — через DNS-записи SpaceWeb
- [x] A-запись www → 144.31.63.133 (trendrider.ru)
- Примечание: .ru показывает "делегирован на сторонние DNS", но записи уже стоят. Ждём до 24ч.
- Примечание: "IP-адрес для A-записи" в SpaceWeb НЕ позволяет вписать свой IP — только их серверы. Используем раздел DNS → Записи DNS.

### Деплой — DONE (23.03.2026)
- [x] Собрать сайт — `npm run build` → `out/` (3.9MB)
- [x] Nginx конфиг: `deploy/nginx-trendrider.conf`
- [x] Залить `out/` на Senko → `/var/www/trendrider/`
- [x] Nginx конфиг → `/etc/nginx/sites-available/trendrider` + симлинк
- [x] `nginx -t && systemctl reload nginx` — OK
- [x] UFW: открыты порты 80/tcp и 443/tcp
- [x] Certbot установлен через pip (`/usr/local/bin/certbot` v5.4.0)
- [x] **SSL trendrider.net** — HTTPS работает! Сертификат до 20.06.2026, автопродление
- [ ] **SSL trendrider.ru** — ждём DNS пропагацию (домен ещё не резолвится), потом: `certbot --nginx -d trendrider.ru -d www.trendrider.ru`
- [ ] **Проверить** — открыть https://trendrider.ru после DNS

### После деплоя — TODO
- [ ] Stripe подключение для Basic/VIP оплаты
- [ ] Email сервис (MailerLite/Resend) для capture формы
- [ ] Google Analytics
- [ ] Самозанятость для приёма платежей
