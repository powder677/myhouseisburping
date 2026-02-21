#!/usr/bin/env python3
"""
MyHouseIsBurping.com — Article Generator
Uses Claude API (Haiku = cheapest, ~$0.007/article) to generate
full, SEO-ready HTML articles matching your site's template.

Budget estimate:
  claude-haiku-4-5:  ~650 articles per $5
  claude-sonnet-4-6: ~175 articles per $5

Usage:
  pip install anthropic
  export ANTHROPIC_API_KEY=sk-ant-...
  python3 generate_articles.py
"""

import anthropic
import os
import json
import time
from datetime import datetime

# ─────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────
MODEL = "claude-haiku-4-5-20251001"  # Cheapest — use for bulk generation
# MODEL = "claude-sonnet-4-6"        # Smarter — use for highest-priority pages

PAGES_DIR = "pages"
BASE_URL = "https://www.myhouseisburping.com"
TODAY = datetime.now().strftime("%Y-%m-%d")

# Track spend
COST_LOG_FILE = "api_cost_log.json"
# Haiku pricing (per million tokens)
INPUT_COST_PER_M  = 0.80
OUTPUT_COST_PER_M = 4.00


# ─────────────────────────────────────────
# CONTENT PLAN: Priority articles to generate
# Format: (slug, title, target_keyword, search_intent, notes)
# Ordered by SEO priority (GSC data + keyword research)
# ─────────────────────────────────────────
ARTICLES = [
    # ── TIER 1: High-impression, low-ranking (quick wins) ──
    {
        "slug": "water-heater-popping-sounds-fix",
        "title": "Water Heater Popping Noise: Causes, Fixes & When to Replace",
        "keyword": "why does my water heater make a popping noise",
        "intent": "The user hears popping from their water heater and wants to know if it's dangerous and how to fix it. They want a definitive answer and step-by-step DIY instructions.",
        "internal_links": [
            ("/pages/house-burping-hvac.html", "HVAC and furnace noises"),
            ("/pages/when-to-call-a-professional.html", "when to call a plumber"),
            ("/pages/how-to-stop-house-burping.html", "how to stop house noises"),
        ],
        "word_count": 1800,
        "schema_type": "HowTo",  # Google loves HowTo for fix-it articles
    },
    {
        "slug": "house-shaking-in-wind",
        "title": "Is It Normal for My House to Shake in High Winds?",
        "keyword": "is it normal for house to shake in wind",
        "intent": "User is scared their house is shaking during a storm. They want reassurance or to know when it's dangerous.",
        "internal_links": [
            ("/pages/wind-noises-in-house.html", "wind noises in houses"),
            ("/pages/structural-or-normal.html", "structural damage vs settling"),
            ("/pages/when-to-call-a-professional.html", "structural engineer"),
        ],
        "word_count": 1400,
        "schema_type": "FAQPage",
    },
    {
        "slug": "why-do-old-houses-creak",
        "title": "Why Do Old Houses Creak So Much? (And Is It a Problem?)",
        "keyword": "why do old houses creak",
        "intent": "Curious homeowner in an old home wants to understand the physics of creaking, whether it's normal, and if their old house is safe.",
        "internal_links": [
            ("/pages/house-burping-causes.html", "causes of house noises"),
            ("/pages/house-burping-new-vs-old-house.html", "new vs old house noises"),
            ("/pages/structural-or-normal.html", "structural damage vs settling"),
        ],
        "word_count": 1500,
        "schema_type": "FAQPage",
    },
    {
        "slug": "house-creaking-at-night-causes",
        "title": "Why Does My House Creak at Night? 6 Causes Explained",
        "keyword": "why does my house creak at night",
        "intent": "Homeowner is being woken up by creaking. Wants specific causes and how to stop it from disturbing sleep.",
        "internal_links": [
            ("/pages/house-burping-at-night.html", "house burping at night"),
            ("/pages/house-burping-cold-weather.html", "cold weather house noises"),
            ("/pages/how-to-stop-house-burping.html", "how to stop house creaking"),
        ],
        "word_count": 1600,
        "schema_type": "FAQPage",
    },
    {
        "slug": "vinyl-siding-noise-when-windy",
        "title": "Vinyl Siding Noise When Windy: Why It Happens & How to Stop It",
        "keyword": "vinyl siding noise when windy",
        "intent": "Homeowner is hearing clattering, popping, or slapping from vinyl siding during wind. Wants to know if it's damage or normal and how to fix it.",
        "internal_links": [
            ("/pages/wind-noises-in-house.html", "wind noises in house"),
            ("/pages/how-to-stop-house-burping.html", "how to stop house noises"),
            ("/pages/is-house-burping-normal.html", "is it normal"),
        ],
        "word_count": 1300,
        "schema_type": "HowTo",
    },

    # ── TIER 2: New keyword clusters ──
    {
        "slug": "house-popping-sound-cold-weather",
        "title": "House Making Loud Popping Sounds in Cold Weather? Here's Why",
        "keyword": "house loud popping noises causes",
        "intent": "User woke up to a loud gunshot-like bang from their house in winter. Panicked and wants immediate explanation.",
        "internal_links": [
            ("/pages/house-burping-cold-weather.html", "cold weather house noises"),
            ("/pages/house-burping-causes.html", "causes of house popping"),
            ("/pages/roof-truss-uplift-noises.html", "roof truss uplift"),
        ],
        "word_count": 1400,
        "schema_type": "FAQPage",
    },
    {
        "slug": "creaking-windows-when-windy",
        "title": "Why Do My Windows Creak and Whistle in the Wind?",
        "keyword": "creaking windows when windy",
        "intent": "User hears noise specifically from windows during wind. Wants to know if it's a seal problem, structural, or normal — and how to fix it.",
        "internal_links": [
            ("/pages/wind-noises-in-house.html", "wind noises in house"),
            ("/pages/house-burping-allergies-ventilation.html", "home ventilation and air leaks"),
            ("/pages/how-to-stop-house-burping.html", "solutions to stop house noises"),
        ],
        "word_count": 1200,
        "schema_type": "HowTo",
    },
    {
        "slug": "how-to-burp-your-house-ventilation",
        "title": "How to Burp Your House: The 10-Minute Ventilation Technique",
        "keyword": "how to burp your house",
        "intent": "User has heard the term 'burping your house' for ventilation and wants to know the correct technique, when to do it, and benefits.",
        "internal_links": [
            ("/pages/what-is-house-burping.html", "what is house burping"),
            ("/pages/house-burping-allergies-ventilation.html", "allergies and ventilation"),
            ("/pages/house-burping-and-mold.html", "preventing mold with ventilation"),
        ],
        "word_count": 1400,
        "schema_type": "HowTo",
    },
    {
        "slug": "water-heater-rumbling-noise",
        "title": "Water Heater Rumbling Noise: Sediment Buildup Explained",
        "keyword": "water heater gurgles and pops",
        "intent": "User hears a deep rumbling or gurgling from water heater. Wants to understand sediment buildup and whether the tank needs replacing.",
        "internal_links": [
            ("/pages/water-heater-popping-noise.html", "water heater popping sounds"),
            ("/pages/how-to-stop-house-burping.html", "how to flush a water heater"),
            ("/pages/when-to-call-a-professional.html", "when to call a plumber"),
        ],
        "word_count": 1300,
        "schema_type": "FAQPage",
    },
    {
        "slug": "foundation-settling-noises",
        "title": "Foundation Settling Noises: Normal vs. Dangerous Signs",
        "keyword": "house settling noises dangerous",
        "intent": "User is worried their foundation is failing due to noises. Wants a clear checklist of normal vs. dangerous signs.",
        "internal_links": [
            ("/pages/structural-or-normal.html", "structural damage vs settling"),
            ("/pages/is-house-burping-normal.html", "is house burping normal"),
            ("/pages/when-to-call-a-professional.html", "when to call a structural engineer"),
        ],
        "word_count": 1600,
        "schema_type": "FAQPage",
    },
]


# ─────────────────────────────────────────
# PROMPT TEMPLATE
# ─────────────────────────────────────────
SYSTEM_PROMPT = """You are an expert home inspector and SEO content writer for MyHouseIsBurping.com.

Your writing style:
- Direct, reassuring, and authoritative (like a knowledgeable neighbor, not a textbook)
- Always lead with the answer immediately — no fluff preambles
- Use "you" and "your house" to stay personal
- Short paragraphs (2-4 sentences max)
- Explain the physics simply but don't dumb it down

The site's design system uses these HTML patterns you MUST follow exactly:
1. A `.direct-answer` div at the top with the key answer in bold
2. Numbered or bulleted lists for causes/steps
3. A `.comparison-table` for diagnosis tables
4. `.callout-box.warning-border` for safety warnings (red left border)
5. `.question-card` links at the bottom for related questions

The site monetizes via Google AdSense so articles need depth (1200+ words) to justify ad placement."""


def build_prompt(article):
    internal_links_str = "\n".join(
        f'  - <a href="{url}">{anchor_text}</a>'
        for url, anchor_text in article["internal_links"]
    )
    
    return f"""Write a complete, SEO-optimized HTML article for MyHouseIsBurping.com.

TARGET KEYWORD: "{article['keyword']}"
PAGE TITLE: {article['title']}
SLUG: /pages/{article['slug']}.html
CANONICAL URL: {BASE_URL}/pages/{article['slug']}.html
TARGET WORD COUNT: ~{article['word_count']} words
SCHEMA TYPE: {article['schema_type']}
SEARCH INTENT: {article['intent']}

REQUIRED INTERNAL LINKS (use all of them naturally in the body):
{internal_links_str}

OUTPUT REQUIREMENTS:
1. Output ONLY the content inside <main>...</main> plus the <head> metadata block
2. Follow the exact HTML structure of the existing site pages
3. Include proper Schema.org JSON-LD for {article['schema_type']}
4. Include a breadcrumb: Home > Causes > {article['title']}
5. Include a `.direct-answer` box immediately after h1
6. Include at least one `.comparison-table` with thead/tbody
7. End with a `.related-questions` section with 3 question cards
8. Include one `.ad-slot` div (just placeholder text: <span>Advertisement Space</span>)
9. The <title> tag must contain the target keyword
10. The meta description must be 150-160 chars and contain the keyword

Start your output with the complete <head> block, then the <body> content.
Do NOT include <html>, <header nav>, or <footer> — those are added by the template system.
DO include the full <head> with all meta tags, canonical, og tags, and schema JSON-LD."""


# ─────────────────────────────────────────
# COST TRACKING
# ─────────────────────────────────────────
def load_cost_log():
    if os.path.exists(COST_LOG_FILE):
        with open(COST_LOG_FILE) as f:
            return json.load(f)
    return {"total_spent": 0.0, "articles_generated": [], "sessions": []}


def save_cost_log(log):
    with open(COST_LOG_FILE, "w") as f:
        json.dump(log, f, indent=2)


def calculate_cost(input_tokens, output_tokens):
    return (input_tokens / 1_000_000 * INPUT_COST_PER_M) + \
           (output_tokens / 1_000_000 * OUTPUT_COST_PER_M)


# ─────────────────────────────────────────
# PAGE WRAPPER (adds nav/footer around generated content)
# ─────────────────────────────────────────
def wrap_page(head_content, body_content, article):
    """Wraps generated content in the site's nav and footer."""
    return f"""<!DOCTYPE html>
<html lang="en">
{head_content}

<body>
   <header class="site-header">
      <div class="container nav-container" style="display: flex; justify-content: space-between; align-items: center;">
         <a href="/" class="logo" aria-label="MyHouseIsBurping Home">
            MyHouseIsBurping<span class="accent-orange">.com</span>
         </a>
         <button class="nav-toggle" aria-label="Toggle navigation" aria-expanded="false">
            <span class="sr-only">Menu</span>☰
         </button>
         <nav aria-label="Main navigation">
            <ul class="nav-menu">
               <li><a href="/">Home</a></li>
               <li><a href="/pages/house-burping-causes.html">Causes</a></li>
               <li><a href="/pages/is-house-burping-normal.html">Is It Normal?</a></li>
               <li><a href="/pages/how-to-stop-house-burping.html">Solutions</a></li>
               <li><a href="/pages/when-to-call-a-professional.html">Get Help</a></li>
            </ul>
         </nav>
      </div>
   </header>

{body_content}

   <footer style="background: #2c3e50; color: #fff; padding: 2rem 0; text-align: center;">
      <div class="container">
         <p>© 2024 MyHouseIsBurping.com. All rights reserved.</p>
         <p style="font-size: 0.8rem; opacity: 0.7;">Disclaimer: This website is for informational purposes only. Always consult a certified home inspector for structural concerns.</p>
         <nav style="margin-top: 1rem;">
            <a href="/" style="color: white; text-decoration: underline;">Home</a> |
            <a href="/pages/when-to-call-a-professional.html" style="color: white; text-decoration: underline;">Professional Help</a>
         </nav>
      </div>
   </footer>

   <script src="../js/main.js"></script>
</body>
</html>"""


# ─────────────────────────────────────────
# MAIN GENERATOR
# ─────────────────────────────────────────
def main():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ Set your API key: export ANTHROPIC_API_KEY=sk-ant-...")
        return

    client = anthropic.Anthropic(api_key=api_key)
    os.makedirs(PAGES_DIR, exist_ok=True)

    cost_log = load_cost_log()
    session_cost = 0.0
    session_articles = []

    print("=" * 60)
    print("MyHouseIsBurping.com — Article Generator")
    print(f"Model: {MODEL}")
    print(f"Budget remaining: ${5.0 - cost_log['total_spent']:.3f}")
    print("=" * 60)

    # Filter out already-generated articles
    already_done = {a["slug"] for a in cost_log["articles_generated"]}
    todo = [a for a in ARTICLES if a["slug"] not in already_done]
    
    print(f"\n📝 {len(todo)} articles to generate ({len(already_done)} already done)\n")

    for i, article in enumerate(todo, 1):
        output_path = os.path.join(PAGES_DIR, f"{article['slug']}.html")
        
        # Budget check
        remaining = 5.0 - cost_log["total_spent"] - session_cost
        if remaining < 0.05:
            print(f"\n⚠️  Budget nearly exhausted (${remaining:.3f} left). Stopping.")
            break

        print(f"[{i}/{len(todo)}] Generating: {article['title']}")
        print(f"        Keyword: {article['keyword']}")

        try:
            prompt = build_prompt(article)
            
            message = client.messages.create(
                model=MODEL,
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            )

            content = message.content[0].text
            cost = calculate_cost(message.usage.input_tokens, message.usage.output_tokens)
            session_cost += cost
            
            # Save the file
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(content)

            # Log it
            log_entry = {
                "slug": article["slug"],
                "title": article["title"],
                "keyword": article["keyword"],
                "file": output_path,
                "cost": round(cost, 5),
                "input_tokens": message.usage.input_tokens,
                "output_tokens": message.usage.output_tokens,
                "generated_at": datetime.now().isoformat(),
            }
            cost_log["articles_generated"].append(log_entry)
            session_articles.append(log_entry)
            
            print(f"        ✅ Saved to {output_path}")
            print(f"        💰 Cost: ${cost:.5f} | Session total: ${session_cost:.4f}")
            print()

            # Rate limiting — be polite to the API
            time.sleep(1)

        except Exception as e:
            print(f"        ❌ Error: {e}")
            print()
            continue

    # Update cost log
    cost_log["total_spent"] = round(cost_log["total_spent"] + session_cost, 5)
    cost_log["sessions"].append({
        "date": datetime.now().isoformat(),
        "articles": len(session_articles),
        "cost": round(session_cost, 5),
    })
    save_cost_log(cost_log)

    print("=" * 60)
    print("SESSION COMPLETE")
    print("=" * 60)
    print(f"  Articles generated this session: {len(session_articles)}")
    print(f"  Session cost:                    ${session_cost:.4f}")
    print(f"  Total spent:                     ${cost_log['total_spent']:.4f}")
    print(f"  Budget remaining:                ${5.0 - cost_log['total_spent']:.4f}")
    print(f"\nGenerated files are in: ./{PAGES_DIR}/")
    print("Add them to your sitemap.xml and upload to your host.\n")


if __name__ == "__main__":
    main()
   