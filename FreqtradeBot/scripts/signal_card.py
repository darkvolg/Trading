#!/usr/bin/env python3
"""
Signal Card Generator — produces premium dark-themed PNG cards for trading signals.
Designed for Instagram (1080x1350) and Telegram sharing.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Optional

from PIL import Image, ImageDraw, ImageFont


# ── Branding palette ────────────────────────────────────────────────
BG          = "#0D1117"
PRIMARY     = "#00D4AA"
ACCENT      = "#FFD700"
DANGER      = "#FF4757"
TEXT        = "#E6EDF3"
TEXT_DIM    = "#8B949E"
CARD_BG     = "#1E2A3A"
CARD_BORDER = "#2D3A4A"

WIDTH, HEIGHT = 1080, 1350


# ── Font helpers ────────────────────────────────────────────────────

_font_cache: dict[tuple[str, int], ImageFont.FreeTypeFont] = {}

FONT_CANDIDATES = [
    # Linux
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/TTF/DejaVuSans.ttf",
    # Windows
    "C:/Windows/Fonts/segoeui.ttf",
    "C:/Windows/Fonts/segoeuib.ttf",
    "C:/Windows/Fonts/arial.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
    # macOS
    "/System/Library/Fonts/Helvetica.ttc",
    "/Library/Fonts/Arial.ttf",
]

BOLD_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
    "C:/Windows/Fonts/segoeuib.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
]


def _resolve_font(candidates: list[str]) -> Optional[str]:
    for path in candidates:
        if os.path.isfile(path):
            return path
    return None


def _get_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    key = ("bold" if bold else "regular", size)
    if key in _font_cache:
        return _font_cache[key]

    candidates = BOLD_CANDIDATES if bold else FONT_CANDIDATES
    path = _resolve_font(candidates)
    if path is None:
        path = _resolve_font(FONT_CANDIDATES)  # fallback to any font

    if path:
        font = ImageFont.truetype(path, size)
    else:
        font = ImageFont.load_default()

    _font_cache[key] = font
    return font


# ── Drawing helpers ─────────────────────────────────────────────────

def _rounded_rect(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int, int, int],
    radius: int,
    fill: Optional[str] = None,
    outline: Optional[str] = None,
    width: int = 1,
) -> None:
    """Draw a rounded rectangle (Pillow >=8.2 has built-in, but we keep compat)."""
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def _draw_badge(
    draw: ImageDraw.ImageDraw,
    text: str,
    center_x: int,
    y: int,
    color: str,
    font: ImageFont.FreeTypeFont,
    pad_x: int = 28,
    pad_y: int = 10,
) -> int:
    """Draw a pill-shaped badge and return its bottom y."""
    bbox = font.getbbox(text)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x0 = center_x - tw // 2 - pad_x
    y0 = y
    x1 = center_x + tw // 2 + pad_x
    y1 = y + th + pad_y * 2
    _rounded_rect(draw, (x0, y0, x1, y1), radius=(y1 - y0) // 2, fill=color)
    draw.text(
        (center_x - tw // 2, y0 + pad_y - bbox[1]),
        text,
        fill="#FFFFFF" if color == DANGER else "#000000",
        font=font,
    )
    return y1


def _draw_confidence_bar(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    value: int,
    total: int = 10,
    block_w: int = 52,
    block_h: int = 22,
    gap: int = 8,
) -> None:
    """Draw a segmented confidence bar."""
    for i in range(total):
        bx = x + i * (block_w + gap)
        filled = i < value
        color = PRIMARY if filled else "#2D3A4A"
        _rounded_rect(draw, (bx, y, bx + block_w, y + block_h), radius=5, fill=color)


def _text_right(
    draw: ImageDraw.ImageDraw,
    text: str,
    x_right: int,
    y: int,
    font: ImageFont.FreeTypeFont,
    fill: str,
) -> None:
    bbox = font.getbbox(text)
    tw = bbox[2] - bbox[0]
    draw.text((x_right - tw, y), text, fill=fill, font=font)


# ── Main generator ──────────────────────────────────────────────────

def generate_signal_card(
    signal_number: int,
    direction: str,          # "LONG" or "SHORT"
    pair: str,               # "BTC/USDT"
    entry_low: float,
    entry_high: float,
    stop_loss: float,
    sl_pct: float,
    tp1: float, tp1_pct: float,
    tp2: float, tp2_pct: float,
    tp3: float, tp3_pct: float,
    confidence: int,         # 1-10
    setup: str,              # "Trend Pullback"
    regime: str,             # "Trending Bull"
    leverage: str = "3x",
    output_path: str | None = None,
) -> str:
    """Generate a premium dark-themed signal card PNG and return its path."""

    img = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(img, "RGBA")

    # Margins
    mx = 60
    content_w = WIDTH - 2 * mx

    # ── Fonts ───────────────────────────────────────────────────────
    f_logo      = _get_font(48, bold=True)
    f_signal_no = _get_font(36, bold=True)
    f_badge     = _get_font(32, bold=True)
    f_pair      = _get_font(64, bold=True)
    f_label     = _get_font(28, bold=False)
    f_value     = _get_font(32, bold=True)
    f_pct       = _get_font(26, bold=True)
    f_section   = _get_font(24, bold=True)
    f_info_val  = _get_font(28, bold=True)
    f_info_lbl  = _get_font(24, bold=False)
    f_footer    = _get_font(22, bold=False)
    f_conf_txt  = _get_font(30, bold=True)

    y = 50

    # ── Top bar: logo + signal number ───────────────────────────────
    draw.text((mx, y), "TrendRider", fill=PRIMARY, font=f_logo)

    sig_text = f"#{signal_number:03d}"
    _text_right(draw, sig_text, WIDTH - mx, y + 6, f_signal_no, ACCENT)

    y += 70

    # ── Direction badge ─────────────────────────────────────────────
    badge_color = PRIMARY if direction.upper() == "LONG" else DANGER
    badge_bottom = _draw_badge(draw, direction.upper(), WIDTH // 2, y, badge_color, f_badge)
    y = badge_bottom + 30

    # ── Pair name ───────────────────────────────────────────────────
    pair_bbox = f_pair.getbbox(pair)
    pair_tw = pair_bbox[2] - pair_bbox[0]
    draw.text(((WIDTH - pair_tw) // 2, y), pair, fill=TEXT, font=f_pair)
    y += pair_bbox[3] - pair_bbox[1] + 40

    # ── Price card ──────────────────────────────────────────────────
    card_top = y
    card_pad = 30
    card_x0, card_x1 = mx, WIDTH - mx

    # Pre-calculate card height
    row_h = 56
    num_rows = 5  # entry, SL, TP1, TP2, TP3
    section_title_h = 40
    card_h = card_pad * 2 + section_title_h + num_rows * row_h + 20
    card_y1 = card_top + card_h

    _rounded_rect(
        draw,
        (card_x0, card_top, card_x1, card_y1),
        radius=20,
        fill=CARD_BG,
        outline=CARD_BORDER,
        width=2,
    )

    cy = card_top + card_pad
    inner_left = card_x0 + card_pad
    inner_right = card_x1 - card_pad

    # Section title
    draw.text((inner_left, cy), "PRICE LEVELS", fill=TEXT_DIM, font=f_section)
    cy += section_title_h

    # Helper for price rows
    def _price_row(label: str, value_str: str, pct_str: str | None, color: str, alloc: str | None = None):
        nonlocal cy
        draw.text((inner_left, cy + 4), label, fill=TEXT_DIM, font=f_label)

        # Value (right-aligned before pct)
        if pct_str:
            # pct + allocation block
            extra = ""
            if alloc:
                extra = f"  {alloc}"
            pct_full = f"{pct_str}{extra}"
            pct_bbox = f_pct.getbbox(pct_full)
            pct_w = pct_bbox[2] - pct_bbox[0]
            pct_x = inner_right - pct_w
            draw.text((pct_x, cy + 8), pct_full, fill=color, font=f_pct)
            val_right = pct_x - 16
        else:
            val_right = inner_right

        _text_right(draw, value_str, val_right, cy + 2, f_value, TEXT)
        cy += row_h

    def _fmt_price(v: float) -> str:
        if v >= 1000:
            return f"${v:,.0f}"
        elif v >= 1:
            return f"${v:,.2f}"
        else:
            return f"${v:.6f}"

    _price_row(
        "Entry Zone",
        f"{_fmt_price(entry_low)} — {_fmt_price(entry_high)}",
        None,
        TEXT,
    )
    _price_row(
        "Stop Loss",
        _fmt_price(stop_loss),
        f"({sl_pct:+.1f}%)" if sl_pct < 0 else f"(—{abs(sl_pct):.1f}%)",
        DANGER,
    )
    _price_row("TP1", _fmt_price(tp1), f"(+{tp1_pct:.1f}%)", PRIMARY, "30%")
    _price_row("TP2", _fmt_price(tp2), f"(+{tp2_pct:.1f}%)", PRIMARY, "40%")
    _price_row("TP3", _fmt_price(tp3), f"(+{tp3_pct:.1f}%)", PRIMARY, "30%")

    y = card_y1 + 40

    # ── Confidence bar ──────────────────────────────────────────────
    draw.text((mx, y), "CONFIDENCE", fill=TEXT_DIM, font=f_section)
    conf_label = f"{confidence}/10"
    _text_right(draw, conf_label, WIDTH - mx, y - 2, f_conf_txt, ACCENT)
    y += 40

    bar_total_w = 10 * 52 + 9 * 8  # blocks + gaps
    bar_x = (WIDTH - bar_total_w) // 2
    _draw_confidence_bar(draw, bar_x, y, confidence)
    y += 50

    # ── Info card ───────────────────────────────────────────────────
    info_card_top = y
    info_card_h = 200
    _rounded_rect(
        draw,
        (mx, info_card_top, WIDTH - mx, info_card_top + info_card_h),
        radius=20,
        fill=CARD_BG,
        outline=CARD_BORDER,
        width=2,
    )

    # Three columns: Setup | Regime | Leverage
    col_w = content_w // 3
    cols = [
        ("Setup", setup),
        ("Regime", regime),
        ("Leverage", leverage),
    ]
    for i, (lbl, val) in enumerate(cols):
        cx = mx + col_w * i + col_w // 2

        # Label
        lbl_bbox = f_info_lbl.getbbox(lbl)
        lbl_tw = lbl_bbox[2] - lbl_bbox[0]
        draw.text((cx - lbl_tw // 2, info_card_top + 40), lbl, fill=TEXT_DIM, font=f_info_lbl)

        # Value
        val_bbox = f_info_val.getbbox(val)
        val_tw = val_bbox[2] - val_bbox[0]
        draw.text((cx - val_tw // 2, info_card_top + 85), val, fill=TEXT, font=f_info_val)

        # Divider (not after last)
        if i < len(cols) - 1:
            div_x = mx + col_w * (i + 1)
            draw.line(
                [(div_x, info_card_top + 30), (div_x, info_card_top + info_card_h - 30)],
                fill=CARD_BORDER,
                width=2,
            )

    y = info_card_top + info_card_h + 40

    # ── Decorative line ─────────────────────────────────────────────
    draw.line([(mx, y), (WIDTH - mx, y)], fill=CARD_BORDER, width=2)
    y += 30

    # ── Footer ──────────────────────────────────────────────────────
    footer_lines = [
        ("@TrendRiderSignals", PRIMARY),
        ("t.me/TrendRiderSignals", TEXT_DIM),
        (datetime.now(timezone.utc).strftime("%Y-%m-%d  %H:%M UTC"), TEXT_DIM),
    ]
    for text, color in footer_lines:
        bbox = f_footer.getbbox(text)
        tw = bbox[2] - bbox[0]
        draw.text(((WIDTH - tw) // 2, y), text, fill=color, font=f_footer)
        y += 36

    # ── Save ────────────────────────────────────────────────────────
    if output_path is None:
        out_dir = os.path.dirname(os.path.abspath(__file__))
        output_path = os.path.join(
            out_dir,
            f"signal_{signal_number:03d}_{pair.replace('/', '_')}_{direction.lower()}.png",
        )

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    img.save(output_path, "PNG", optimize=True)
    return output_path


# ── Demo ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    path = generate_signal_card(
        signal_number=42,
        direction="LONG",
        pair="BTC/USDT",
        entry_low=64200,
        entry_high=64580,
        stop_loss=60350,
        sl_pct=-6.0,
        tp1=66126, tp1_pct=3.0,
        tp2=67410, tp2_pct=5.0,
        tp3=70620, tp3_pct=10.0,
        confidence=8,
        setup="Trend Pullback",
        regime="Trending Bull",
        leverage="3x",
    )
    print(f"Signal card saved: {path}")
