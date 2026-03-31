#!/usr/bin/env python3
"""
Strategy Card Generator — TrendRider
Generates a shareable 1080x1920 PNG card with key strategy metrics.
"""

import os
from datetime import datetime
from typing import Optional

from PIL import Image, ImageDraw, ImageFont


# ── Branding ──────────────────────────────────────────────────────────────────
BG = "#0D1117"
PRIMARY = "#00D4AA"
ACCENT = "#FFD700"
DANGER = "#FF4757"
TEXT = "#E6EDF3"
TEXT_DIM = "#8B949E"
CARD_BG = "#1E2A3A"
CARD_BORDER = "#2D3A4A"

WIDTH = 1080
HEIGHT = 1920
PADDING = 50


# ── Font helpers ──────────────────────────────────────────────────────────────

def _load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Try DejaVu Sans, then Arial, then Pillow default."""
    candidates = []
    if bold:
        candidates += [
            "DejaVuSans-Bold.ttf",
            "DejaVuSans-Bold",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
            "arialbd.ttf",
            "C:/Windows/Fonts/segoeui.ttf",
        ]
    else:
        candidates += [
            "DejaVuSans.ttf",
            "DejaVuSans",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "C:/Windows/Fonts/arial.ttf",
            "arial.ttf",
            "C:/Windows/Fonts/segoeui.ttf",
        ]
    for name in candidates:
        try:
            return ImageFont.truetype(name, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


FONT_TITLE = _load_font(56, bold=True)
FONT_SUBTITLE = _load_font(30)
FONT_METRIC_VAL = _load_font(48, bold=True)
FONT_METRIC_LBL = _load_font(22)
FONT_SECTION = _load_font(32, bold=True)
FONT_BODY = _load_font(24)
FONT_BODY_BOLD = _load_font(24, bold=True)
FONT_SMALL = _load_font(20)
FONT_TINY = _load_font(16)
FONT_STAR = _load_font(36)


# ── Drawing helpers ───────────────────────────────────────────────────────────

def _rounded_rect(
    draw: ImageDraw.ImageDraw,
    xy: tuple,
    radius: int = 16,
    fill: str = CARD_BG,
    outline: Optional[str] = None,
):
    """Draw a rounded rectangle."""
    x0, y0, x1, y1 = xy
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline)


def _center_text(draw, text, font, y, color, width=WIDTH):
    """Draw text centred horizontally."""
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    x = (width - tw) // 2
    draw.text((x, y), text, font=font, fill=color)


def _metric_color(value: float, good_low: bool = False) -> str:
    """Return green for good values, red for bad."""
    if good_low:
        return PRIMARY if value < 5 else DANGER
    return PRIMARY if value > 0 else DANGER


# ── Main generator ────────────────────────────────────────────────────────────

def generate_strategy_card(
    win_rate: float = 71.1,
    max_dd: float = 1.81,
    profit_factor: float = 2.09,
    sqn: float = 3.02,
    total_trades: int = 103,
    total_profit: float = 13.57,
    pairs: dict = None,
    period: str = "March 2026",
    output_path: str = None,
) -> str:
    """Generate a strategy performance card and return the path to the PNG."""

    if pairs is None:
        pairs = {
            "BNB/USDT": 5.69,
            "ETH/USDT": 4.79,
            "SOL/USDT": 2.71,
            "BTC/USDT": 0.37,
        }

    if output_path is None:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(
            os.path.dirname(__file__), "..", "user_data", f"strategy_card_{ts}.png"
        )

    img = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(img)
    y = PADDING

    # ── Header ────────────────────────────────────────────────────────────
    _center_text(draw, "TrendRider", FONT_TITLE, y, PRIMARY)
    y += 70
    _center_text(draw, "Strategy Performance", FONT_SUBTITLE, y, TEXT_DIM)
    y += 45
    _center_text(draw, period, FONT_BODY, y, ACCENT)
    y += 55

    # thin separator
    draw.line([(PADDING, y), (WIDTH - PADDING, y)], fill=CARD_BORDER, width=2)
    y += 30

    # ── Metrics Grid (2x3) ────────────────────────────────────────────────
    metrics = [
        ("Win Rate", f"{win_rate:.1f}%", _metric_color(win_rate)),
        ("Max Drawdown", f"{max_dd:.2f}%", _metric_color(max_dd, good_low=True)),
        ("Profit Factor", f"{profit_factor:.2f}", _metric_color(profit_factor)),
        ("SQN Score", f"{sqn:.2f}", _metric_color(sqn)),
        ("Total Trades", str(total_trades), TEXT),
        ("Total Profit", f"+{total_profit:.2f}%", _metric_color(total_profit)),
    ]

    card_w = (WIDTH - PADDING * 2 - 20) // 2  # 2 columns, 20px gap
    card_h = 130
    gap = 20

    for i, (label, value, color) in enumerate(metrics):
        col = i % 2
        row = i // 2
        cx = PADDING + col * (card_w + gap)
        cy = y + row * (card_h + gap)

        _rounded_rect(draw, (cx, cy, cx + card_w, cy + card_h), radius=16,
                       fill=CARD_BG, outline=CARD_BORDER)

        # label
        draw.text((cx + 24, cy + 16), label, font=FONT_METRIC_LBL, fill=TEXT_DIM)
        # value
        draw.text((cx + 24, cy + 50), value, font=FONT_METRIC_VAL, fill=color)

    y += 3 * (card_h + gap) + 10

    # ── Pairs Breakdown ───────────────────────────────────────────────────
    draw.line([(PADDING, y), (WIDTH - PADDING, y)], fill=CARD_BORDER, width=2)
    y += 25
    draw.text((PADDING, y), "Pairs Breakdown", font=FONT_SECTION, fill=TEXT)
    y += 50

    sorted_pairs = sorted(pairs.items(), key=lambda x: x[1], reverse=True)
    max_val = max(abs(v) for v in pairs.values()) if pairs else 1
    WIDTH - PADDING * 2 - 260  # space for label + value

    for pair_name, pct in sorted_pairs:
        color = PRIMARY if pct >= 0 else DANGER
        sign = "+" if pct >= 0 else ""

        # pair name
        draw.text((PADDING, y + 4), pair_name, font=FONT_BODY, fill=TEXT)

        # percentage value
        val_text = f"{sign}{pct:.2f}%"
        bbox = draw.textbbox((0, 0), val_text, font=FONT_BODY_BOLD)
        val_w = bbox[2] - bbox[0]
        draw.text((PADDING + 180, y + 4), val_text, font=FONT_BODY_BOLD, fill=color)

        # bar
        bar_x = PADDING + 180 + val_w + 20
        bar_max_w = WIDTH - PADDING - bar_x - 10
        bar_w = max(4, int((abs(pct) / max_val) * bar_max_w))
        bar_y = y + 8
        bar_h = 22
        _rounded_rect(draw, (bar_x, bar_y, bar_x + bar_w, bar_y + bar_h),
                       radius=6, fill=color)

        y += 46

    y += 15

    # ── Strategy Info ─────────────────────────────────────────────────────
    draw.line([(PADDING, y), (WIDTH - PADDING, y)], fill=CARD_BORDER, width=2)
    y += 25
    draw.text((PADDING, y), "Strategy Info", font=FONT_SECTION, fill=TEXT)
    y += 50

    info_left = [
        ("Timeframe", "1H"),
        ("Leverage", "3x Isolated"),
        ("Stoploss", "-6% + Trailing"),
    ]
    info_right = [
        ("Pairs", "BTC, ETH, SOL, BNB"),
        ("Max Open", "4 positions"),
    ]

    col_w = (WIDTH - PADDING * 2) // 2
    info_y_start = y

    for label, val in info_left:
        draw.text((PADDING, y), f"{label}:", font=FONT_BODY, fill=TEXT_DIM)
        draw.text((PADDING + 160, y), val, font=FONT_BODY_BOLD, fill=TEXT)
        y += 38

    ry = info_y_start
    for label, val in info_right:
        draw.text((PADDING + col_w, ry), f"{label}:", font=FONT_BODY, fill=TEXT_DIM)
        draw.text((PADDING + col_w + 140, ry), val, font=FONT_BODY_BOLD, fill=TEXT)
        ry += 38

    y = max(y, ry) + 20

    # ── Rating ────────────────────────────────────────────────────────────
    draw.line([(PADDING, y), (WIDTH - PADDING, y)], fill=CARD_BORDER, width=2)
    y += 25
    draw.text((PADDING, y), "Rating", font=FONT_SECTION, fill=TEXT)
    y += 50

    # Star rating based on SQN: 0-1.6 = 1*, 1.7-2.4 = 2*, 2.5-3.9 = 3*, 4-5.0 = 4*, >5 = 5*
    if sqn >= 5.0:
        stars = 5
    elif sqn >= 4.0:
        stars = 4
    elif sqn >= 2.5:
        stars = 3
    elif sqn >= 1.7:
        stars = 2
    else:
        stars = 1

    star_text = "\u2605" * stars + "\u2606" * (5 - stars)
    _center_text(draw, star_text, FONT_STAR, y, ACCENT)
    y += 55

    _center_text(draw, "Backtested on 6 months of data", FONT_BODY, y, TEXT_DIM)
    y += 36
    _center_text(draw, "Paper trading since March 21, 2026", FONT_BODY, y, TEXT_DIM)
    y += 55

    # ── Footer ────────────────────────────────────────────────────────────
    draw.line([(PADDING, y), (WIDTH - PADDING, y)], fill=CARD_BORDER, width=2)
    y += 30

    _center_text(draw, "@TrendRiderSignals", FONT_SECTION, y, PRIMARY)
    y += 45
    _center_text(draw, "t.me/TrendRiderSignals", FONT_BODY, y, ACCENT)
    y += 55

    # disclaimer
    _center_text(
        draw,
        "Past performance \u2260 future results. Not financial advice.",
        FONT_SMALL,
        y,
        TEXT_DIM,
    )

    # ── Save ──────────────────────────────────────────────────────────────
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    img.save(output_path, "PNG", optimize=True)
    return os.path.abspath(output_path)


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    path = generate_strategy_card()
    print(f"Strategy card generated: {path}")
