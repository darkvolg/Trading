---
name: Server access for deploy
description: Senko VPS (144.31.63.133) — SSH через ProxyJump vpn-b, для деплоя лендинга и ботов
type: reference
---

## Прод-сервер: Senko Digital (144.31.63.133)

- **IP**: 144.31.63.133
- **SSH порт**: 2222
- **User**: root
- **Key**: ~/.ssh/senko-144
- **Хостинг**: senko.digital (логин: darkvolg@gmail.com / hf0sx3eHylM8)

### SSH подключение (ТОЛЬКО через ProxyJump!)

Прямой SSH не работает. Только через vpn-b:

```bash
ssh -o ProxyCommand="ssh -i ~/.ssh/yc-vpn -p 2222 -o StrictHostKeyChecking=no -W %h:%p yc-user@84.201.178.73" \
  -i ~/.ssh/senko-144 -p 2222 -o StrictHostKeyChecking=no root@144.31.63.133
```

### VPN прокси (vpn-b)
- **IP**: 84.201.178.73
- **SSH порт**: 2222
- **User**: yc-user
- **Key**: ~/.ssh/yc-vpn
- **Тип**: Яндекс Cloud, preemptible VM (может сбрасывать ключи!)

### Что стоит на Senko
- paseka-bot, lekarek-bot, klyov-bot, inventory-bot (все systemd)
- Порты занятые: 22, 2222 (SSH), 47779 (X-UI), 7070 (Monitor), 8082 (InventoryBot)
- Nginx скорее всего уже установлен

### Cloudflare
- Email: darkvolg@gmail.com
- Account ID: b730cc4b2cc17c9578e96cae8965dd83
- Домен vzik-tech.ru уже есть, можно добавить trendrider.pro

**How to apply:** Для деплоя лендинга — собрать `out/`, загрузить через SSH цепочку, настроить Nginx vhost + SSL.
