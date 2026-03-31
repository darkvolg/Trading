#!/usr/bin/env python3
"""
Cross-monitoring script for two servers.

Each server runs this script via cron to check if the OTHER server is alive.
If a server is down, sends a Telegram alert. Includes recovery notifications
and a daily health summary report.

Servers:
    - Senko Digital: 144.31.135.97 (main — landing, bots, marketing)
    - Yandex Cloud:  84.201.178.73 (VPN server, backup)

Cron entries (on both servers):
    */5 * * * * /usr/bin/python3 /opt/freqtrade/scripts/marketing/server_monitor.py
    0 8 * * *   /usr/bin/python3 /opt/freqtrade/scripts/marketing/server_monitor.py --daily-report

Environment variables:
    TG_TOKEN        - Telegram bot token
    ADMIN_CHAT_ID   - Telegram admin chat ID for alerts
"""

import argparse
import json
import logging
import os
import socket
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

try:
    import requests
except ImportError:
    print("ERROR: 'requests' library is required. Install with: pip install requests")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

TG_TOKEN = os.environ.get("TG_TOKEN", "")
ADMIN_CHAT_ID = os.environ.get("ADMIN_CHAT_ID", "")

STATE_FILE = Path("/tmp/server_monitor_state.json")
LOG_DIR = Path.home() / "logs"
LOG_FILE = LOG_DIR / "server_monitor.log"

SOCKET_TIMEOUT = 10   # seconds
HTTP_TIMEOUT = 15     # seconds
ALERT_COOLDOWN = 3600 # 1 hour — don't repeat the same alert within this window

# Server definitions
SERVERS = {
    "senko": {
        "name": "Senko Digital",
        "ip": "144.31.135.97",
    },
    "yandex": {
        "name": "Yandex Cloud",
        "ip": "84.201.178.73",
    },
}

# Checks to run FROM each server (key = server running the script)
# Each check targets the OTHER server + self-health
CHECKS = {
    "senko": [
        # Remote checks — Yandex Cloud
        {"target": "yandex", "type": "tcp", "port": 22, "label": "SSH (22)"},
        {"target": "yandex", "type": "tcp", "port": 47779, "label": "X-UI (47779)"},
        # Self-health — Senko
        {"target": "senko", "type": "http", "url": "https://trendrider.net", "label": "HTTPS trendrider.net"},
        {"target": "senko", "type": "tcp", "port": 2222, "label": "SSH (2222)"},
        {"target": "senko", "type": "tcp", "port": 443, "label": "Nginx HTTPS (443)"},
        {"target": "senko", "type": "tcp", "port": 80, "label": "Nginx HTTP (80)"},
    ],
    "yandex": [
        # Remote checks — Senko Digital
        {"target": "senko", "type": "http", "url": "https://trendrider.net", "label": "HTTPS trendrider.net"},
        {"target": "senko", "type": "tcp", "port": 2222, "label": "SSH (2222)"},
        {"target": "senko", "type": "tcp", "port": 443, "label": "Nginx HTTPS (443)"},
        {"target": "senko", "type": "tcp", "port": 80, "label": "Nginx HTTP (80)"},
        # Self-health — Yandex
        {"target": "yandex", "type": "tcp", "port": 22, "label": "SSH (22)"},
        {"target": "yandex", "type": "tcp", "port": 47779, "label": "X-UI (47779)"},
    ],
}

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger("server_monitor")

# ---------------------------------------------------------------------------
# State management (deduplication / recovery tracking)
# ---------------------------------------------------------------------------


def load_state() -> dict:
    """Load persisted state from JSON file."""
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            log.warning("Corrupt state file, starting fresh")
    return {"alerts": {}, "incidents_24h": 0, "last_reset": ""}


def save_state(state: dict) -> None:
    """Persist state to JSON file."""
    try:
        STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
    except OSError as exc:
        log.error("Failed to save state: %s", exc)


def _check_key(check: dict) -> str:
    """Unique key for a check (used for dedup)."""
    target = check["target"]
    label = check["label"]
    return f"{target}:{label}"


def should_alert(state: dict, check: dict) -> bool:
    """Return True if we should send an alert (cooldown expired)."""
    key = _check_key(check)
    alerts = state.get("alerts", {})
    entry = alerts.get(key)
    if entry is None:
        return True
    last_alert = entry.get("last_alert_ts", 0)
    return (time.time() - last_alert) >= ALERT_COOLDOWN


def record_alert(state: dict, check: dict) -> None:
    """Record that we just sent an alert for this check."""
    key = _check_key(check)
    alerts = state.setdefault("alerts", {})
    if key not in alerts:
        alerts[key] = {}
    alerts[key]["last_alert_ts"] = time.time()
    alerts[key]["status"] = "down"
    if "down_since" not in alerts[key]:
        alerts[key]["down_since"] = time.time()


def record_recovery(state: dict, check: dict) -> float:
    """Record recovery. Returns downtime in seconds, or 0 if wasn't tracked."""
    key = _check_key(check)
    alerts = state.get("alerts", {})
    entry = alerts.get(key)
    downtime = 0.0
    if entry and entry.get("status") == "down":
        down_since = entry.get("down_since", 0)
        if down_since:
            downtime = time.time() - down_since
    # Clear alert state
    if key in alerts:
        del alerts[key]
    return downtime


def is_currently_down(state: dict, check: dict) -> bool:
    """Check if a service is currently tracked as down."""
    key = _check_key(check)
    entry = state.get("alerts", {}).get(key)
    return entry is not None and entry.get("status") == "down"


def reset_daily_counters(state: dict) -> None:
    """Reset 24h incident counter if a new day started."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if state.get("last_reset") != today:
        state["incidents_24h"] = 0
        state["last_reset"] = today


# ---------------------------------------------------------------------------
# Server identification
# ---------------------------------------------------------------------------


def detect_server() -> str:
    """Detect which server we're running on by checking local IPs or public IP."""
    # Method 1: check local IPs
    local_ips = ""
    try:
        result = subprocess.run(
            ["hostname", "-I"],
            capture_output=True, text=True, timeout=5,
        )
        local_ips = result.stdout.strip()
    except (subprocess.SubprocessError, FileNotFoundError):
        try:
            result = subprocess.run(
                ["ip", "-4", "addr", "show"],
                capture_output=True, text=True, timeout=5,
            )
            local_ips = result.stdout
        except (subprocess.SubprocessError, FileNotFoundError):
            pass

    for key, server in SERVERS.items():
        if server["ip"] in local_ips:
            return key

    # Method 2: check public IP (for cloud VMs with internal IPs)
    try:
        resp = requests.get("https://ifconfig.me/ip", timeout=5)
        public_ip = resp.text.strip()
        for key, server in SERVERS.items():
            if server["ip"] == public_ip:
                return key
    except Exception:
        pass

    # Method 3: check if known paths exist
    if Path("/opt/freqtrade/scripts/marketing").exists():
        return "senko"
    if Path("/opt/scripts/marketing").exists():
        return "yandex"

    log.error("Cannot detect server identity. Local IPs: %s", local_ips)
    log.error("Expected one of: %s", ", ".join(s["ip"] for s in SERVERS.values()))
    sys.exit(1)


# ---------------------------------------------------------------------------
# Health checks
# ---------------------------------------------------------------------------


def check_tcp(host: str, port: int) -> dict:
    """Check TCP connectivity. Returns {ok, response_ms, error}."""
    start = time.time()
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(SOCKET_TIMEOUT)
        sock.connect((host, port))
        sock.close()
        elapsed = (time.time() - start) * 1000
        return {"ok": True, "response_ms": round(elapsed), "error": None}
    except socket.timeout:
        return {"ok": False, "response_ms": None, "error": f"Connection timeout after {SOCKET_TIMEOUT}s"}
    except ConnectionRefusedError:
        return {"ok": False, "response_ms": None, "error": "Connection refused"}
    except OSError as exc:
        return {"ok": False, "response_ms": None, "error": str(exc)}


def check_http(url: str) -> dict:
    """Check HTTP endpoint. Returns {ok, status_code, response_ms, error}."""
    start = time.time()
    try:
        resp = requests.get(url, timeout=HTTP_TIMEOUT, allow_redirects=True)
        elapsed = (time.time() - start) * 1000
        ok = 200 <= resp.status_code < 400
        return {
            "ok": ok,
            "status_code": resp.status_code,
            "response_ms": round(elapsed),
            "error": None if ok else f"HTTP {resp.status_code}",
        }
    except requests.exceptions.Timeout:
        return {"ok": False, "status_code": None, "response_ms": None, "error": f"Connection timeout after {HTTP_TIMEOUT}s"}
    except requests.exceptions.ConnectionError as exc:
        return {"ok": False, "status_code": None, "response_ms": None, "error": f"Connection error: {exc}"}
    except requests.exceptions.RequestException as exc:
        return {"ok": False, "status_code": None, "response_ms": None, "error": str(exc)}


def run_check(check: dict) -> dict:
    """Run a single health check. Returns result dict."""
    target_server = SERVERS[check["target"]]
    host = target_server["ip"]

    if check["type"] == "tcp":
        result = check_tcp(host, check["port"])
    elif check["type"] == "http":
        result = check_http(check["url"])
    else:
        result = {"ok": False, "error": f"Unknown check type: {check['type']}"}

    result["check"] = check
    result["target_server"] = target_server
    return result


# ---------------------------------------------------------------------------
# Telegram notifications
# ---------------------------------------------------------------------------


def send_telegram(text: str) -> bool:
    """Send a message via Telegram bot API."""
    if not TG_TOKEN or not ADMIN_CHAT_ID:
        log.error("TG_TOKEN or ADMIN_CHAT_ID not configured")
        return False

    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    payload = {
        "chat_id": ADMIN_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    try:
        resp = requests.post(url, json=payload, timeout=10)
        if resp.status_code == 200:
            log.info("Telegram alert sent successfully")
            return True
        else:
            log.error("Telegram API error %s: %s", resp.status_code, resp.text)
            return False
    except requests.exceptions.RequestException as exc:
        log.error("Failed to send Telegram message: %s", exc)
        return False


def format_down_alert(result: dict, checker_server: dict) -> str:
    """Format a server-down alert message."""
    target = result["target_server"]
    check = result["check"]
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    error = result.get("error", "Unknown error")

    return (
        "\U0001f534 <b>СЕРВЕР НЕДОСТУПЕН</b>\n"
        "\n"
        f"<b>Сервер:</b> {target['name']} ({target['ip']})\n"
        f"<b>Проверка:</b> {check['label']}\n"
        f"<b>Ошибка:</b> {error}\n"
        f"<b>Время:</b> {now}\n"
        "\n"
        f"<b>Проверено с:</b> {checker_server['name']} ({checker_server['ip']})"
    )


def format_recovery_alert(result: dict, checker_server: dict, downtime_seconds: float) -> str:
    """Format a recovery notification."""
    target = result["target_server"]
    check = result["check"]

    # Format downtime
    if downtime_seconds > 0:
        minutes = int(downtime_seconds / 60)
        if minutes < 1:
            downtime_str = f"~{int(downtime_seconds)} сек"
        elif minutes < 60:
            downtime_str = f"~{minutes} мин"
        else:
            hours = minutes // 60
            remaining = minutes % 60
            downtime_str = f"~{hours}ч {remaining}мин"
    else:
        downtime_str = "неизвестно"

    # Status text
    status = "200 OK" if check["type"] == "http" else "OK"
    if result.get("status_code"):
        status = f"{result['status_code']} OK"

    return (
        "\u2705 <b>СЕРВЕР ВОССТАНОВЛЕН</b>\n"
        "\n"
        f"<b>Сервер:</b> {target['name']} ({target['ip']})\n"
        f"<b>Проверка:</b> {check['label']}\n"
        f"<b>Статус:</b> {status}\n"
        f"<b>Простой:</b> {downtime_str}\n"
        "\n"
        f"<b>Проверено с:</b> {checker_server['name']} ({checker_server['ip']})"
    )


# ---------------------------------------------------------------------------
# Main monitoring loop
# ---------------------------------------------------------------------------


def run_monitoring(server_key: str) -> None:
    """Run all checks for the current server and handle alerts."""
    checker_server = SERVERS[server_key]
    checks = CHECKS[server_key]
    state = load_state()
    reset_daily_counters(state)

    log.info("Running checks from %s (%s)", checker_server["name"], checker_server["ip"])

    for check in checks:
        result = run_check(check)
        label = check["label"]
        target_name = result["target_server"]["name"]

        if result["ok"]:
            ms = result.get("response_ms", "?")
            log.info("OK: %s / %s (%sms)", target_name, label, ms)

            # Recovery notification if it was previously down
            if is_currently_down(state, check):
                downtime = record_recovery(state, check)
                msg = format_recovery_alert(result, checker_server, downtime)
                send_telegram(msg)
                log.info("RECOVERED: %s / %s (downtime: %.0fs)", target_name, label, downtime)
        else:
            log.warning("FAIL: %s / %s — %s", target_name, label, result.get("error"))

            if should_alert(state, check):
                msg = format_down_alert(result, checker_server)
                send_telegram(msg)
                record_alert(state, check)
                state["incidents_24h"] = state.get("incidents_24h", 0) + 1
                log.info("Alert sent for %s / %s", target_name, label)
            else:
                log.info("Alert suppressed (cooldown) for %s / %s", target_name, label)
                # Still update the alert timestamp tracking
                record_alert(state, check)

    save_state(state)
    log.info("Monitoring cycle complete")


# ---------------------------------------------------------------------------
# Daily health report
# ---------------------------------------------------------------------------


def run_daily_report(server_key: str) -> None:
    """Generate and send a daily health summary."""
    checker_server = SERVERS[server_key]
    state = load_state()
    reset_daily_counters(state)

    log.info("Generating daily health report from %s", checker_server["name"])

    # Run ALL checks (both servers' perspectives merged)
    # Senko checks
    senko_checks = [
        {"target": "senko", "type": "http", "url": "https://trendrider.net", "label": "HTTPS trendrider.net"},
        {"target": "senko", "type": "tcp", "port": 2222, "label": "SSH (2222)"},
        {"target": "senko", "type": "tcp", "port": 443, "label": "Nginx HTTPS (443)"},
        {"target": "senko", "type": "tcp", "port": 80, "label": "Nginx HTTP (80)"},
    ]
    # Yandex checks
    yandex_checks = [
        {"target": "yandex", "type": "tcp", "port": 22, "label": "SSH (22)"},
        {"target": "yandex", "type": "tcp", "port": 47779, "label": "X-UI (47779)"},
    ]

    # Run Senko checks
    senko_results = []
    for check in senko_checks:
        result = run_check(check)
        senko_results.append(result)

    # Run Yandex checks
    yandex_results = []
    for check in yandex_checks:
        result = run_check(check)
        yandex_results.append(result)

    # Determine overall status
    senko_up = all(r["ok"] for r in senko_results)
    yandex_up = all(r["ok"] for r in yandex_results)

    incidents = state.get("incidents_24h", 0)

    # Calculate uptime (simplified — based on incidents)
    if incidents == 0:
        uptime = "100%"
    elif incidents <= 2:
        uptime = "~99%"
    elif incidents <= 5:
        uptime = "~95%"
    else:
        uptime = "<90%"

    # Build report
    senko_status = "\u2705 UP" if senko_up else "\u274c DOWN"
    yandex_status = "\u2705 UP" if yandex_up else "\u274c DOWN"

    lines = [
        "\U0001f4ca <b>Ежедневный отчёт серверов</b>",
        "",
        f"<b>Senko Digital</b> (144.31.135.97): {senko_status}",
    ]

    for r in senko_results:
        check = r["check"]
        if r["ok"]:
            ms = r.get("response_ms", "?")
            if check["type"] == "http":
                code = r.get("status_code", 200)
                lines.append(f"  \u2022 {check['label']}: {code} OK ({ms}ms)")
            else:
                lines.append(f"  \u2022 {check['label']}: OK ({ms}ms)")
        else:
            lines.append(f"  \u2022 {check['label']}: \u274c {r.get('error', 'FAIL')}")

    lines.append("")
    lines.append(f"<b>Yandex Cloud</b> (84.201.178.73): {yandex_status}")

    for r in yandex_results:
        check = r["check"]
        if r["ok"]:
            ms = r.get("response_ms", "?")
            lines.append(f"  \u2022 {check['label']}: OK ({ms}ms)")
        else:
            lines.append(f"  \u2022 {check['label']}: \u274c {r.get('error', 'FAIL')}")

    lines.append("")
    lines.append(f"<b>За 24ч:</b> {incidents} инцидентов")
    lines.append(f"<b>Аптайм:</b> {uptime}")
    lines.append("")
    lines.append(f"<i>Проверено с: {checker_server['name']} ({checker_server['ip']})</i>")

    report = "\n".join(lines)
    send_telegram(report)

    # Reset daily counter after report
    state["incidents_24h"] = 0
    state["last_reset"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    save_state(state)

    log.info("Daily health report sent")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(description="Cross-server monitoring with Telegram alerts")
    parser.add_argument(
        "--daily-report",
        action="store_true",
        help="Send daily health summary instead of regular checks",
    )
    args = parser.parse_args()

    # Detect which server we're on
    server_key = detect_server()
    log.info("Detected server: %s (%s)", SERVERS[server_key]["name"], SERVERS[server_key]["ip"])

    if args.daily_report:
        run_daily_report(server_key)
    else:
        run_monitoring(server_key)


if __name__ == "__main__":
    main()
