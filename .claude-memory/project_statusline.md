---
name: StatusLine context indicator setup
description: Configured statusLine for context window usage display; built-in circle indicator is a known bug (#36180)
type: project
---

Настроен statusLine в `~/.claude/settings.json` для отображения процента использования контекстного окна.

**Что сделано:**
- Установлен скрипт `~/.claude/statusline.py` (парсит JSON, выводит модель + % контекста)
- В `settings.json` добавлена секция `statusLine` с командой `C:\Python314\python.exe C:\Users\Exploed\.claude\statusline.py`
- CLI Claude Code обновлён с 2.1.63 до 2.1.81 (`npm update -g @anthropic-ai/claude-code`)

**Итог:**
- StatusLine НЕ работает в native UI (panel/sidebar) — только в terminal mode (`claudeCode.useTerminal: true`)
- Пользователь выбрал оставить native UI и ждать фикс бага #36180
- StatusLine конфиг оставлен в settings.json — заработает если переключить на terminal mode

**Контекст:**
- Встроенный кружочек контекста — известный баг GitHub #36180 (пропал в новых версиях)
- Дома (user Dark) кружочек есть — возможно кэш старой версии UI
- `jq` не установлен на рабочем ПК, поэтому используем Python

**Why:** Пользователю важно видеть заполнение контекстного окна во время работы.
**How to apply:** Ждём фикс #36180. Если срочно нужно — включить `claudeCode.useTerminal: true`.
