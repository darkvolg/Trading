"""carry_bot entrypoint.

Two run modes:
    --once             — run a single tick and exit (for cron-driven schedules)
    --loop             — run forever, sleeping until next funding tick (default)
    --signals-only     — observe and decide but skip order placement

Useful for testnet shake-down:
    python -m carry_bot.main --once --signals-only --testnet

Production cron entry (one per 8h, 5min after funding):
    5 0,8,16 * * *  /opt/freqtrade/venv/bin/python -m carry_bot.main --once
"""
from __future__ import annotations
import argparse
import logging
import os
import sys
import time

from .config import CarryConfig, from_env
from .exchange import BybitClient
from .funding_signal import SignalBook
from .positions import PositionStore
from .risk import RiskGate
from .scheduler import Scheduler


def setup_logging(log_path: str | None, verbose: bool) -> None:
    """Configure root logger.

    stdout-only by default. Cron / systemd handles file redirection — adding
    a FileHandler here would double-write every line (one via Python, one via
    shell redirect). log_path retained for explicit standalone runs where no
    external redirect exists; opt-in via CARRY_LOG_TO_FILE=true env.
    """
    level = logging.DEBUG if verbose else logging.INFO
    fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stdout)]
    if log_path and os.environ.get("CARRY_LOG_TO_FILE", "").lower() in ("1", "true", "yes"):
        try:
            handlers.append(logging.FileHandler(log_path))
        except (OSError, PermissionError) as e:
            print(f"warn: cannot open logfile {log_path}: {e}; stdout-only", file=sys.stderr)
    logging.basicConfig(level=level, format=fmt, handlers=handlers)


def build_components(cfg: CarryConfig) -> tuple[Scheduler, PositionStore]:
    exchange = BybitClient(cfg.api_key, cfg.api_secret, testnet=cfg.testnet)
    store = PositionStore(cfg.db_path)
    signals = SignalBook(cfg.whitelist)
    # Restore signal state from disk so persistence survives restarts
    saved = store.load_signal_state()
    if saved:
        signals.restore(saved)
        logging.info("restored signal state for %d pairs", len(saved))
    risk = RiskGate(
        kill_switch_path=cfg.kill_switch_path,
        stale_force_close_hours=cfg.stale_force_close_hours,
        daily_loss_alarm_pct=cfg.daily_loss_alarm_pct,
    )
    sched = Scheduler(cfg, exchange, store, signals, risk)
    return sched, store


def run_once(sched: Scheduler, signals_only: bool) -> int:
    report = sched.tick(dry_run_signals_only=signals_only)
    log = logging.getLogger("tick")
    log.info(
        "tick_done now=%d opens=%s closes=%s funding_accrued=%.4f fees=%.4f",
        report.now_ms, report.opens, report.closes,
        report.funding_accrued, report.fees_paid,
    )
    for msg in report.alarms:
        log.warning(msg)
    if report.skipped_reasons:
        log.info("skipped (%d): %s", len(report.skipped_reasons), report.skipped_reasons)
    return 0


def run_loop(sched: Scheduler, signals_only: bool) -> int:
    log = logging.getLogger("loop")
    log.info("starting loop; signals_only=%s", signals_only)
    while True:
        try:
            run_once(sched, signals_only)
        except KeyboardInterrupt:
            log.info("interrupted; exiting")
            return 0
        except Exception as e:
            log.exception("tick crashed: %s; sleeping 60s before retry", e)
            time.sleep(60)
            continue
        next_ms = sched.next_wake_ms()
        sleep_s = max(60, (next_ms - int(time.time() * 1000)) // 1000)
        log.info("next tick in %ds (epoch_ms=%d)", sleep_s, next_ms)
        time.sleep(sleep_s)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="carry_bot entrypoint")
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--once", action="store_true", help="run one tick and exit")
    mode.add_argument("--loop", action="store_true", help="run forever (default)")
    ap.add_argument("--signals-only", action="store_true",
                    help="observe + decide, skip order placement")
    ap.add_argument("--testnet", action="store_true",
                    help="force testnet mode (overrides env)")
    ap.add_argument("--mainnet", action="store_true",
                    help="force mainnet mode (overrides env, requires --confirm-mainnet)")
    ap.add_argument("--confirm-mainnet", action="store_true",
                    help="explicit confirmation required to run on mainnet")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args(argv)

    cfg = from_env()
    # CLI overrides
    if args.testnet or args.mainnet:
        from dataclasses import replace
        cfg = replace(cfg, testnet=args.testnet)

    # Mainnet safety gates — must trip BOTH:
    #   (a) explicit --confirm-mainnet on the command line
    #   (b) non-empty api_key + api_secret in env
    # Catches: typo of --testnet vs --mainnet, empty .env, key rotation drift.
    if not cfg.testnet:
        if not args.confirm_mainnet:
            print(
                "REFUSED: mainnet mode requires --confirm-mainnet. "
                "Re-run with --testnet or add the confirm flag.",
                file=sys.stderr,
            )
            return 2
        if not cfg.api_key or not cfg.api_secret:
            print(
                "REFUSED: mainnet mode requires CARRY_API_KEY + CARRY_API_SECRET env vars. "
                "Both must be non-empty.",
                file=sys.stderr,
            )
            return 2

    setup_logging(cfg.log_path, args.verbose)
    log = logging.getLogger("main")
    log.info(
        "carry_bot starting | testnet=%s n_slots=%d entry=%.5f exit=%.5f leverage=%dx",
        cfg.testnet, cfg.n_slots, cfg.entry_threshold,
        cfg.exit_threshold, cfg.perp_leverage,
    )

    sched, store = build_components(cfg)
    try:
        if args.once:
            return run_once(sched, args.signals_only)
        # default: loop
        return run_loop(sched, args.signals_only)
    finally:
        store.close_db()


if __name__ == "__main__":
    sys.exit(main())
