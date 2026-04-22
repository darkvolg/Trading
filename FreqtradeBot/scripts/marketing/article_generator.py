#!/usr/bin/env python3
"""
TrendRider Article Generator
- Picks next topic from topics_queue.json
- Generates article via GLM-4.6 (Z.AI Anthropic-compatible API)
- Generates hero image via Gemini Nano Banana (Composio)
- Writes landing/app/blog/<slug>/page.tsx
- Commits + pushes to GitHub
- Rebuilds landing via npm + deploys to /var/www/trendrider
- Appends slug to blog_manifest.json for cross-posting
- Sends Telegram report

ENV required: GLM_API_KEY, GLM_BASE_URL, GLM_MODEL, COMPOSIO_API_KEY, TG_TOKEN, ADMIN_CHAT_ID
"""
import os
import sys
import json
try:
    import json_repair
except ImportError:
    json_repair = None
import logging
import subprocess
import re
from pathlib import Path
from datetime import datetime, timezone

import requests

try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# ---------- Config ----------
REPO_ROOT = Path("/opt/trendrider-repo")
LANDING = REPO_ROOT / "landing"
BLOG_DIR = LANDING / "app" / "blog"
HEROES_DIR = LANDING / "public" / "blog-heroes"
TOPICS_FILE = Path("/opt/freqtrade/scripts/marketing/topics_queue.json")
MANIFEST_FILE = Path("/opt/freqtrade/scripts/marketing/blog_manifest.json")
WEB_ROOT = Path("/var/www/trendrider")
LOG_FILE = Path("/var/log/article_generator.log")

GLM_API_KEY = os.environ.get("GLM_API_KEY", "")
GLM_BASE_URL = os.environ.get("GLM_BASE_URL", "https://api.z.ai/api/anthropic")
GLM_MODEL = os.environ.get("GLM_MODEL", "glm-4.6")

COMPOSIO_API_KEY = os.environ.get("COMPOSIO_API_KEY", "")
TG_TOKEN = os.environ.get("TG_TOKEN", "")
ADMIN_CHAT_ID = os.environ.get("ADMIN_CHAT_ID", "")

# ---------- Logging ----------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()],
)
log = logging.getLogger("article_gen")


def tg_notify(message: str) -> None:
    if not TG_TOKEN or not ADMIN_CHAT_ID:
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
            data={"chat_id": ADMIN_CHAT_ID, "parse_mode": "HTML", "text": message},
            timeout=10,
        )
    except Exception as e:
        log.warning(f"Telegram notify failed: {e}")


def run(cmd, cwd=None, check=True, capture=True):
    log.info(f"$ {cmd}")
    result = subprocess.run(
        cmd, shell=True, cwd=cwd, check=check,
        capture_output=capture, text=True,
    )
    if capture and result.stdout:
        log.info(result.stdout.strip()[-500:])
    if capture and result.stderr:
        log.info(result.stderr.strip()[-500:])
    return result


# ---------- Step 1: Pick next topic ----------
def pick_topic() -> dict | None:
    if not TOPICS_FILE.exists():
        log.error(f"Topics file not found: {TOPICS_FILE}")
        return None
    with open(TOPICS_FILE, encoding="utf-8") as f:
        topics = json.load(f)
    if not topics:
        log.error("Topics queue is empty!")
        return None
    # Skip slugs that already exist
    for i, topic in enumerate(topics):
        slug_dir = BLOG_DIR / topic["slug"]
        if not slug_dir.exists():
            return {"index": i, "topic": topic}
    log.error("All topics already have articles — add more topics!")
    return None


def remove_topic(index: int) -> None:
    with open(TOPICS_FILE, encoding="utf-8") as f:
        topics = json.load(f)
    topics.pop(index)
    with open(TOPICS_FILE, "w", encoding="utf-8") as f:
        json.dump(topics, f, ensure_ascii=False, indent=2)


# ---------- Step 2: Call GLM-4.6 for article ----------
GLM_SYSTEM_PROMPT = """You are an expert SEO content writer for TrendRider (trendrider.net), a crypto algorithmic trading platform. Write authoritative, technical, data-driven articles for serious traders and developers.

Style:
- Direct, no fluff, no generic AI phrases ("In today's fast-paced world", "Let's dive in", etc.)
- Technical depth — assume reader knows basic crypto trading
- Real numbers, exact rules, concrete examples
- Internal links to relevant TrendRider blog articles where natural

Output ONLY valid JSON. No markdown wrapper, no preamble. Schema:
{
  "intro_paragraphs": ["para1", "para2"],
  "sections": [
    {"heading": "Section Title", "paragraphs": ["p1", "p2"], "list": ["bullet1", "bullet2"] | null, "table": {"headers": ["Col1","Col2"], "rows": [["r1c1","r1c2"]]} | null},
    ...
  ],
  "faqs": [
    {"q": "Question?", "a": "Answer text"}
  ]
}

Paragraphs must be 2-4 sentences. Do NOT include any HTML tags, anchor links, or hyperlinks inside paragraph string values. Use plain text only. (HTML inside JSON string values breaks parsing). Escape apostrophes as &apos; and ampersands as &amp; and em-dash as &mdash;.

Minimum: 6-8 sections, 10+ total paragraphs, 5 FAQs. Aim for ~1800-2400 words total."""


def call_glm(topic: dict) -> dict:
    outline_str = "\n".join(f"- {s}" for s in topic.get("outline", []))
    user_prompt = f"""Write a comprehensive SEO article for TrendRider blog.

Title: {topic['title']}
Description: {topic['description']}
Category: {topic['category']}
Target keywords: {', '.join(topic.get('keywords', []))}

Outline (follow this structure):
{outline_str}

Current date: {datetime.now(timezone.utc).strftime('%B %Y')}

Return ONLY the JSON — no markdown, no ```json blocks, no preamble. Start with {{ and end with }}."""

    log.info(f"Calling GLM-4.6 for '{topic['slug']}'...")
    resp = requests.post(
        f"{GLM_BASE_URL}/v1/messages",
        headers={
            "x-api-key": GLM_API_KEY,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        },
        json={
            "model": GLM_MODEL,
            "max_tokens": 8000,
            "system": GLM_SYSTEM_PROMPT,
            "messages": [{"role": "user", "content": user_prompt}],
        },
        timeout=300,
    )
    resp.raise_for_status()
    data = resp.json()
    text = data["content"][0]["text"]
    # Save raw for debug
    debug_file = Path(f"/tmp/glm_raw_{topic['slug']}.txt")
    debug_file.write_text(text, encoding="utf-8")
    log.info(f"Saved raw response to {debug_file} ({len(text)} chars)")
    # Strip code fences if model added them
    text = re.sub(r"^```(?:json)?\s*", "", text.strip())
    text = re.sub(r"\s*```$", "", text)
    # Find first { and last } to extract JSON if there's wrapping text
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        text = text[start:end + 1]
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as e:
        # Try to fix common issues: unescaped newlines inside strings
        log.warning(f"First parse failed: {e}. Attempting cleanup...")
        # Replace literal newlines inside strings with spaces (naive but often works)
        cleaned = re.sub(r'(?<!\\)\n(?=(?:[^"]*"[^"]*")*[^"]*"[^"]*$)', ' ', text)
        try:
            parsed = json.loads(cleaned)
            log.info("Cleanup succeeded")
        except json.JSONDecodeError:
            # Last resort: strip all control chars and try again
            cleaned2 = re.sub(r'[\x00-\x1f\x7f](?![nrt"\\])', ' ', text)
            try:
                parsed = json.loads(cleaned2)
                log.info("Control char cleanup succeeded")
            except json.JSONDecodeError as e3:
                log.warning(f"Standard cleanup failed: {e3}. Trying json_repair library...")
                if json_repair is not None:
                    try:
                        parsed = json_repair.loads(text)
                        log.info("json_repair succeeded")
                    except Exception as e4:
                        log.error(f"json_repair also failed: {e4}")
                        log.error(f"Raw (last 800 chars near error): {text[max(0, e3.pos - 200):e3.pos + 200]}")
                        raise e3
                else:
                    log.error(f"GLM returned invalid JSON: {e3}")
                    log.error(f"Raw (last 800 chars near error): {text[max(0, e3.pos - 200):e3.pos + 200]}")
                    raise
    log.info(f"GLM returned: {len(parsed.get('sections', []))} sections, {len(parsed.get('faqs', []))} FAQs")
    return parsed


# ---------- Step 3: Generate hero image locally with PIL ----------
def generate_hero_image(topic: dict) -> str | None:
    """Generates a branded hero banner locally via PIL. 1600x900, TrendRider theme."""
    if not PIL_AVAILABLE:
        log.warning("PIL not installed — skipping hero image")
        return None
    slug = topic["slug"]
    try:
        W, H = 1600, 900
        # Dark navy base (matches site bg #0D1117)
        img = Image.new("RGB", (W, H), (13, 17, 23))
        draw = ImageDraw.Draw(img)

        # Radial gradient from center-left (subtle glow effect)
        for y in range(H):
            for x in range(0, W, 4):  # skip pixels for speed
                cx, cy = W * 0.35, H * 0.5
                dist = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
                max_d = (W * W + H * H) ** 0.5 / 2
                t = max(0, 1 - dist / max_d) ** 2
                r = int(13 + t * 15)
                g = int(17 + t * 40)
                b = int(23 + t * 35)
                draw.rectangle([x, y, x + 4, y + 1], fill=(r, g, b))

        # Geometric grid overlay (cyan subtle lines)
        for i in range(0, W, 80):
            draw.line([(i, 0), (i, H)], fill=(6, 60, 80), width=1)
        for i in range(0, H, 80):
            draw.line([(0, i), (W, i)], fill=(6, 60, 80), width=1)

        # Animated-looking candlesticks on the right half
        import random
        rng = random.Random(hash(slug) & 0xFFFFFFFF)
        cx = 900
        base_y = 500
        for i in range(18):
            x = cx + i * 35
            direction = rng.choice([-1, 1])
            height = rng.randint(30, 120)
            width = 18
            color = (34, 197, 94) if direction > 0 else (239, 68, 68)
            top = base_y + rng.randint(-60, 60)
            bottom = top + height * direction
            y1, y2 = min(top, bottom), max(top, bottom)
            draw.rectangle([x, y1, x + width, y2], fill=color)
            # Wick
            wick_top = y1 - rng.randint(5, 20)
            wick_bot = y2 + rng.randint(5, 20)
            mid = x + width // 2
            draw.line([(mid, wick_top), (mid, wick_bot)], fill=color, width=2)

        # Blur the candlesticks slightly for aesthetic
        img = img.filter(ImageFilter.GaussianBlur(radius=1))
        draw = ImageDraw.Draw(img)

        # Left text block
        # Try to load a system font, fall back to default
        font_big = None
        font_small = None
        font_tag = None
        for font_path in [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
        ]:
            if Path(font_path).exists():
                font_big = ImageFont.truetype(font_path, 56)
                font_small = ImageFont.truetype(font_path.replace("-Bold", ""), 22)
                font_tag = ImageFont.truetype(font_path, 18)
                break
        if not font_big:
            font_big = ImageFont.load_default()
            font_small = ImageFont.load_default()
            font_tag = ImageFont.load_default()

        # Category pill
        cat = topic.get("category", "Article").upper()
        pill_pad = 14
        try:
            bbox = draw.textbbox((0, 0), cat, font=font_tag)
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]
        except AttributeError:
            tw, th = draw.textsize(cat, font=font_tag)
        pill_x, pill_y = 80, 180
        draw.rounded_rectangle(
            [pill_x, pill_y, pill_x + tw + pill_pad * 2, pill_y + th + pill_pad],
            radius=20,
            outline=(34, 197, 94),
            width=2,
        )
        draw.text((pill_x + pill_pad, pill_y + pill_pad // 2), cat, font=font_tag, fill=(34, 197, 94))

        # Title — wrap to 2-3 lines
        title = topic["title"]
        max_width_px = 880
        words = title.split()
        lines = []
        cur = []
        for w in words:
            test = " ".join(cur + [w])
            try:
                bbox = draw.textbbox((0, 0), test, font=font_big)
                width_px = bbox[2] - bbox[0]
            except AttributeError:
                width_px, _ = draw.textsize(test, font=font_big)
            if width_px > max_width_px and cur:
                lines.append(" ".join(cur))
                cur = [w]
            else:
                cur.append(w)
        if cur:
            lines.append(" ".join(cur))
        lines = lines[:3]

        y_cursor = 260
        for line in lines:
            draw.text((80, y_cursor), line, font=font_big, fill=(255, 255, 255))
            y_cursor += 72

        # Footer branding
        draw.text((80, 780), "TRENDRIDER.NET", font=font_small, fill=(34, 197, 94))
        draw.text((80, 820), "AI Crypto Trading Signals  •  67.9% Win Rate", font=font_small, fill=(156, 163, 175))

        # Save as webp
        HEROES_DIR.mkdir(parents=True, exist_ok=True)
        img_path = HEROES_DIR / f"{slug}.webp"
        img.save(img_path, "WEBP", quality=88, method=6)
        log.info(f"Hero image generated locally: {img_path}")
        return str(img_path)
    except Exception as e:
        log.error(f"Local image generation failed: {e}")
        return None


# ---------- Step 4: Render page.tsx ----------
def _jsx_escape(s):
    """Escape JSX-dangerous chars in text content. Preserves pre-escaped entities."""
    if s is None:
        return ""
    out = str(s)
    # Escape & first but keep existing entities (e.g., &amp;, &mdash;, &quot;)
    out = re.sub(r"&(?!(?:amp|lt|gt|quot|apos|mdash|ndash|hellip|#\d+|#x[0-9a-fA-F]+);)", "&amp;", out)
    out = out.replace("<", "&lt;").replace(">", "&gt;")
    # Curly braces would be parsed as JSX expression boundaries
    out = out.replace("{", "&#123;").replace("}", "&#125;")
    return out


def render_page_tsx(topic: dict, article: dict, image_filename: str | None) -> str:
    slug = topic["slug"]
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    today_human = datetime.now(timezone.utc).strftime("%B %-d, %Y")
    image_url = (
        f"https://trendrider.net/blog-heroes/{image_filename}"
        if image_filename else
        "https://trendrider.net/icon.svg"
    )

    # Build section JSX
    sections_jsx = []
    for s in article.get("sections", []):
        heading = s.get("heading", "").replace('"', '&quot;')
        block = f'\n          <h2 className="text-xl font-semibold text-foreground mt-8 mb-3">{_jsx_escape(heading)}</h2>'
        for p in s.get("paragraphs", []):
            block += f'\n          <p>{_jsx_escape(p)}</p>'
        lst = s.get("list")
        if lst:
            items = "\n".join(f'            <li>{_jsx_escape(li)}</li>' for li in lst)
            block += f'\n          <ul className="list-disc pl-6 space-y-2 my-4">\n{items}\n          </ul>'
        tbl = s.get("table")
        if tbl:
            headers = "".join(f'<th className="text-left p-2 border border-border">{_jsx_escape(h)}</th>' for h in tbl.get("headers", []))
            rows_html = ""
            for row in tbl.get("rows", []):
                cells = "".join(f'<td className="p-2 border border-border">{_jsx_escape(c)}</td>' for c in row)
                rows_html += f'                <tr>{cells}</tr>'
            block += (
                '\n          <div className="overflow-x-auto my-6">'
                '\n            <table className="w-full text-sm border-collapse">'
                f'\n              <thead><tr>{headers}</tr></thead>'
                f'\n              <tbody>{rows_html}</tbody>'
                '\n            </table>'
                '\n          </div>'
            )
        sections_jsx.append(block)
    sections_str = "".join(sections_jsx)

    intro_paragraphs = "\n".join(
        f'          <p>{_jsx_escape(p)}</p>' for p in article.get("intro_paragraphs", [])
    )

    # FAQs JSON-LD
    faqs_jsonld = [
        {"@type": "Question", "name": f["q"], "acceptedAnswer": {"@type": "Answer", "text": f["a"]}}
        for f in article.get("faqs", [])
    ]
    # FAQs visual
    faq_jsx_items = []
    for f in article.get("faqs", []):
        faq_jsx_items.append(
            f'\n          <div className="border-l-2 border-primary/40 pl-4 my-4">'
            f'\n            <p className="font-semibold text-foreground mb-2">{_jsx_escape(f["q"])}</p>'
            f'\n            <p>{_jsx_escape(f["a"])}</p>'
            f'\n          </div>'
        )
    faqs_str = "".join(faq_jsx_items)

    title_escaped = topic['title'].replace('"', '\\"')
    desc_escaped = topic['description'].replace('"', '\\"')
    title_jsx = _jsx_escape(topic['title'])
    category_jsx = _jsx_escape(topic['category'])
    title_attr = _jsx_escape(topic['title']).replace('"', '&quot;')

    article_jsonld = json.dumps({
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": topic['title'],
        "description": topic['description'],
        "author": {"@type": "Person", "name": "TrendRider Team", "url": "https://trendrider.net"},
        "publisher": {
            "@type": "Organization",
            "name": "TrendRider",
            "url": "https://trendrider.net",
            "logo": {"@type": "ImageObject", "url": "https://trendrider.net/icon.svg"},
        },
        "datePublished": today,
        "dateModified": today,
        "image": image_url,
        "mainEntityOfPage": {"@type": "WebPage", "@id": f"https://trendrider.net/blog/{slug}"},
    })
    breadcrumb_jsonld = json.dumps({
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": "https://trendrider.net"},
            {"@type": "ListItem", "position": 2, "name": "Blog", "item": "https://trendrider.net/blog"},
            {"@type": "ListItem", "position": 3, "name": topic['title']},
        ],
    })
    faq_jsonld = json.dumps({
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": faqs_jsonld,
    })

    page = f'''import type {{ Metadata }} from "next";

export const metadata: Metadata = {{
  title: "{title_escaped}",
  description: "{desc_escaped}",
  alternates: {{
    canonical: "https://trendrider.net/blog/{slug}",
  }},
}};

export default function Article() {{
  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{{{
          __html: {json.dumps(article_jsonld)}
        }}}}
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{{{
          __html: {json.dumps(breadcrumb_jsonld)}
        }}}}
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{{{
          __html: {json.dumps(faq_jsonld)}
        }}}}
      />
      <div className="min-h-screen bg-background text-foreground">
        <article className="max-w-3xl mx-auto px-4 py-20">
          <a href="/blog" className="text-primary text-sm hover:underline mb-8 inline-block">&larr; Back to blog</a>
          <div className="flex items-center gap-3 mb-4">
            <span className="px-3 py-1 text-[10px] font-mono uppercase tracking-widest text-primary border border-primary/30 rounded-full">{category_jsx}</span>
            <span className="text-xs text-muted">{today_human}</span>
            <span className="text-xs text-muted">&bull; {topic.get('read_min', 11)} min read</span>
          </div>
          <h1 className="text-3xl md:text-4xl font-bold mb-6 tracking-tight">{title_jsx}</h1>
          <img src="/blog-heroes/{slug}.webp" alt="{title_attr}" className="w-full rounded-xl border border-border mb-8" loading="eager" />

          <div className="space-y-6 text-muted leading-relaxed">
{intro_paragraphs}
{sections_str}

            <h2 className="text-xl font-semibold text-foreground mt-10 mb-3">Frequently Asked Questions</h2>
{faqs_str}

            <div className="mt-12 p-6 border border-border rounded-lg bg-card/50">
              <p className="text-foreground font-semibold mb-2">Ready to automate your crypto trading?</p>
              <p className="mb-4 text-sm">TrendRider runs a 67.9% win-rate algorithmic strategy on Bybit futures. Free Telegram signals, optional paid tiers.</p>
              <a href="/" className="text-primary text-sm hover:underline">Get free signals &rarr;</a>
            </div>

            <div className="mt-6 p-6 border border-primary/30 rounded-lg bg-card/30">
              <p className="text-foreground font-semibold mb-2">⭐ Open-source strategy</p>
              <p className="mb-4 text-sm">The exact Freqtrade strategy powering the live bot is on GitHub. MIT license, fully reproducible backtests. Star it if you find it useful.</p>
              <a href="https://github.com/darkvolg/trendrider-strategy" target="_blank" rel="noopener" className="text-primary text-sm hover:underline">Star on GitHub &rarr;</a>
            </div>
          </div>
        </article>
      </div>
    </>
  );
}}
'''
    return page


# ---------- Step 5: Write files + git push + build + deploy ----------
def save_and_deploy(topic: dict, page_content: str, image_saved: bool) -> bool:
    slug = topic["slug"]

    # Ensure we're on latest master
    run("git pull --rebase", cwd=str(REPO_ROOT))

    # Write page.tsx
    slug_dir = BLOG_DIR / slug
    slug_dir.mkdir(parents=True, exist_ok=True)
    page_path = slug_dir / "page.tsx"
    page_path.write_text(page_content, encoding="utf-8")
    log.info(f"Wrote {page_path}")

    # Git add + commit + push
    rel_page = page_path.relative_to(REPO_ROOT)
    run(f"git add {rel_page}", cwd=str(REPO_ROOT))
    if image_saved:
        rel_img = (HEROES_DIR / f"{slug}.webp").relative_to(REPO_ROOT)
        run(f"git add {rel_img}", cwd=str(REPO_ROOT))
    msg = f"feat(blog): auto-publish article — {topic['title'][:60]}"
    try:
        run(f'git commit -m "{msg}"', cwd=str(REPO_ROOT))
    except subprocess.CalledProcessError:
        log.warning("Nothing to commit (maybe re-run on same slug)")
    run("git push", cwd=str(REPO_ROOT))

    # Build Next.js
    log.info("Running npm run build...")
    build_result = subprocess.run(
        "npm run build",
        shell=True,
        cwd=str(LANDING),
        capture_output=True,
        text=True,
        timeout=600,
    )
    if build_result.returncode != 0:
        log.error(f"Build FAILED:\n{build_result.stdout[-1500:]}\n{build_result.stderr[-1500:]}")
        return False
    log.info("Build succeeded")

    # Deploy: rsync out/ to /var/www/trendrider
    run(f"rsync -a --delete {LANDING}/out/ {WEB_ROOT}/")
    run("systemctl reload nginx")
    log.info(f"Deployed to {WEB_ROOT}")
    return True


# ---------- Step 6: Update manifest ----------
def update_manifest(topic: dict) -> None:
    if not MANIFEST_FILE.exists():
        return
    try:
        with open(MANIFEST_FILE, encoding="utf-8") as f:
            manifest = json.load(f)
        # Skip if already in
        if any(m.get("slug") == topic["slug"] for m in manifest):
            return
        manifest.append({
            "slug": topic["slug"],
            "title": topic["title"],
            "summary": topic["description"],
            "tags": ["crypto", "trading", "algotrading", "bots"],
        })
        with open(MANIFEST_FILE, "w", encoding="utf-8") as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)
        log.info(f"Appended to manifest: {topic['slug']}")
    except Exception as e:
        log.warning(f"Manifest update failed: {e}")


# ---------- Main ----------
def main():
    log.info("=" * 60)
    log.info("Article Generator — starting")

    if not GLM_API_KEY:
        log.error("GLM_API_KEY missing")
        sys.exit(2)

    picked = pick_topic()
    if not picked:
        tg_notify("⚠️ <b>Article generator</b>: topics queue empty or all slugs taken")
        sys.exit(0)

    topic = picked["topic"]
    idx = picked["index"]
    log.info(f"Selected topic: {topic['slug']}")

    # 1. Generate article text
    try:
        article = call_glm(topic)
    except Exception as e:
        log.error(f"GLM failed: {e}")
        tg_notify(f"❌ <b>Article gen FAILED</b>\nGLM error for <code>{topic['slug']}</code>:\n<code>{str(e)[:300]}</code>")
        sys.exit(1)

    # 2. Generate hero image (non-critical — continue on failure)
    img_path = generate_hero_image(topic)
    img_filename = f"{topic['slug']}.webp" if img_path else None

    # 3. Render + save + git push + build + deploy
    page_tsx = render_page_tsx(topic, article, img_filename)
    try:
        ok = save_and_deploy(topic, page_tsx, bool(img_path))
    except Exception as e:
        log.error(f"Deploy failed: {e}")
        tg_notify(f"❌ <b>Article deploy FAILED</b>\n<code>{topic['slug']}</code>\n<code>{str(e)[:300]}</code>")
        sys.exit(1)

    if not ok:
        tg_notify(f"❌ <b>Build failed</b> for <code>{topic['slug']}</code>")
        sys.exit(1)

    # 4. Remove topic from queue + update manifest
    remove_topic(idx)
    update_manifest(topic)

    # 5. Report success
    url = f"https://trendrider.net/blog/{topic['slug']}"
    tg_notify(
        f"✅ <b>Новая статья опубликована</b>\n\n"
        f"📰 <b>{topic['title']}</b>\n\n"
        f"🔗 <a href=\"{url}\">{url}</a>\n\n"
        f"📊 Категория: {topic['category']}\n"
        f"⏱ {topic.get('read_min', 11)} min read\n"
        f"🖼 Hero image: {'✅' if img_path else '❌'}\n"
        f"📑 В очереди осталось тем: {idx if idx > 0 else 'неизвестно'}"
    )
    log.info(f"SUCCESS: {url}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log.exception("Unexpected error")
        tg_notify(f"💥 <b>Article generator CRASHED</b>\n<code>{str(e)[:400]}</code>")
        sys.exit(1)
