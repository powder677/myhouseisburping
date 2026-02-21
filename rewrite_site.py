#!/usr/bin/env python3
"""
MyHouseIsBurping.com — AEO Site Rewriter
Rewrites existing pages to add:
  - Answer Engine Optimization (AEO) for AI search (Perplexity, ChatGPT, Gemini)
  - Stronger internal linking to hub pages
  - Richer schema markup (FAQPage, HowTo, Article)
  - Better direct-answer boxes
  - Radon hub cross-links where relevant
  - Hub index links on every page

Run from site root:
  python3 rewrite_site.py

Uses claude-haiku for speed/cost. Switch to claude-sonnet-4-6 for quality.
Cost: ~$0.01-0.015 per page rewrite.
"""

import anthropic
import os
import json
import shutil
import glob
from datetime import datetime

# ─────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────
MODEL = "claude-haiku-4-5-20251001"  # ~$0.01/page
BASE_URL = "https://www.myhouseisburping.com"
BACKUP_DIR = f"_rewrite_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
COST_LOG = "rewrite_cost_log.json"

INPUT_COST_PER_M  = 0.80   # Haiku pricing
OUTPUT_COST_PER_M = 4.00

# ─────────────────────────────────────────
# PAGES TO REWRITE + their context
# ─────────────────────────────────────────
PAGES = [
    {
        "file": "pages/house-burping-causes.html",
        "keyword": "what causes house burping",
        "add_links": [
            ("/pages/radon-hub.html", "radon as a reason to ventilate your home"),
            ("/pages/index.html", "all house noise guides"),
        ],
        "aeo_questions": [
            "What causes house burping?",
            "Why does my house make loud popping sounds?",
            "Is thermal expansion dangerous?",
        ],
        "schema": "FAQPage",
    },
    {
        "file": "pages/is-house-burping-normal.html",
        "keyword": "is house burping normal",
        "add_links": [
            ("/pages/radon-hub.html", "radon — the invisible risk in your home"),
            ("/pages/index.html", "browse all house noise guides by topic"),
        ],
        "aeo_questions": [
            "Is it normal for a house to make popping sounds?",
            "When should I worry about house noises?",
            "What house sounds are dangerous?",
        ],
        "schema": "FAQPage",
    },
    {
        "file": "pages/house-burping-hvac.html",
        "keyword": "why does my heating system pop and bang",
        "add_links": [
            ("/pages/radon-hub.html", "HVAC and radon: how your heating system affects indoor air"),
            ("/pages/index.html", "all house noise guides"),
        ],
        "aeo_questions": [
            "Why does my furnace make a banging noise?",
            "Why do my vents pop when heating turns on?",
            "Is a banging furnace dangerous?",
        ],
        "schema": "FAQPage",
    },
    {
        "file": "pages/water-heater-popping-noise.html",
        "keyword": "why is my water heater making a popping noise",
        "add_links": [
            ("/pages/index.html", "all appliance noise guides"),
            ("/pages/when-to-call-a-professional.html", "when to call a plumber"),
        ],
        "aeo_questions": [
            "Why is my water heater popping?",
            "Is a popping water heater dangerous?",
            "How do I stop my water heater from popping?",
        ],
        "schema": "HowTo",
    },
    {
        "file": "pages/wind-noises-in-house.html",
        "keyword": "why does my house creak in the wind",
        "add_links": [
            ("/pages/radon-hub.html", "wind and radon: how air pressure affects indoor radon levels"),
            ("/pages/index.html", "all weather and structural noise guides"),
        ],
        "aeo_questions": [
            "Why does my house moan in high winds?",
            "Is it normal for a house to creak in the wind?",
            "How do I stop my windows from whistling in the wind?",
        ],
        "schema": "FAQPage",
    },
    {
        "file": "pages/house-burping-at-night.html",
        "keyword": "why does my house pop at night",
        "add_links": [
            ("/pages/index.html", "all house noise guides by topic"),
            ("/pages/house-burping-or-mice.html", "is it a pest or the house settling?"),
        ],
        "aeo_questions": [
            "Why does my house make noise at night?",
            "Why do houses pop and crack at night?",
            "Is it normal for a house to make noise when it's quiet?",
        ],
        "schema": "FAQPage",
    },
    {
        "file": "pages/house-burping-cold-weather.html",
        "keyword": "why does my house crack in cold weather",
        "add_links": [
            ("/pages/radon-hub.html", "cold weather and radon: why winter increases radon levels"),
            ("/pages/index.html", "all seasonal house noise guides"),
        ],
        "aeo_questions": [
            "Why does my house crack in cold weather?",
            "What is the Stack Effect in a house?",
            "Why are houses louder in winter?",
        ],
        "schema": "FAQPage",
    },
    {
        "file": "pages/structural-or-normal.html",
        "keyword": "is it structural damage or normal settling",
        "add_links": [
            ("/pages/index.html", "all structural noise and safety guides"),
            ("/pages/when-to-call-a-professional.html", "when to call a structural engineer"),
        ],
        "aeo_questions": [
            "How do I know if my house has structural damage?",
            "What do structural cracks look like?",
            "Is my house settling or is it dangerous?",
        ],
        "schema": "FAQPage",
    },
    {
        "file": "pages/house-burping-or-mice.html",
        "keyword": "is it house settling or mice",
        "add_links": [
            ("/pages/index.html", "all pest and structural noise guides"),
            ("/pages/house-burping-and-mold.html", "pests and moisture — the mold connection"),
        ],
        "aeo_questions": [
            "How do I know if I have mice in my walls?",
            "Does house settling sound like scratching?",
            "What does a mouse in the wall sound like?",
        ],
        "schema": "FAQPage",
    },
    {
        "file": "pages/how-to-stop-house-burping.html",
        "keyword": "how to stop house burping noises",
        "add_links": [
            ("/pages/radon-hub.html", "fixing house noises and reducing radon at the same time"),
            ("/pages/index.html", "all DIY house noise fix guides"),
        ],
        "aeo_questions": [
            "How do I stop my house from making popping noises?",
            "What stops house creaking?",
            "How do I quiet HVAC duct banging?",
        ],
        "schema": "HowTo",
    },
    {
        "file": "pages/when-to-call-a-professional.html",
        "keyword": "when to call a professional for house noises",
        "add_links": [
            ("/pages/radon-hub.html", "radon mitigation professionals"),
            ("/pages/index.html", "all house noise and safety guides"),
        ],
        "aeo_questions": [
            "When should I call a structural engineer?",
            "What house noises require a professional?",
            "Who do I call for water heater noises?",
        ],
        "schema": "FAQPage",
    },
    {
        "file": "pages/house-burping-allergies-ventilation.html",
        "keyword": "how to ventilate your house",
        "add_links": [
            ("/pages/radon-hub.html", "ventilation and radon — the critical connection"),
            ("/pages/indoor-air-quality-improvement.html", "complete indoor air quality guide"),
            ("/pages/index.html", "all air quality and ventilation guides"),
        ],
        "aeo_questions": [
            "How do I ventilate my house?",
            "Does opening windows help with allergies?",
            "What is burping a house?",
        ],
        "schema": "HowTo",
    },
    {
        "file": "pages/house-burping-and-mold.html",
        "keyword": "can house noises indicate mold",
        "add_links": [
            ("/pages/radon-hub.html", "mold, moisture, and radon — overlapping hidden risks"),
            ("/pages/index.html", "all house noise and air quality guides"),
        ],
        "aeo_questions": [
            "Can house noises mean I have mold?",
            "What does water damage sound like in walls?",
            "How do I know if I have a hidden leak?",
        ],
        "schema": "FAQPage",
    },
    {
        "file": "pages/roof-truss-uplift-noises.html",
        "keyword": "why does my ceiling crack in winter",
        "add_links": [
            ("/pages/index.html", "all structural and seasonal noise guides"),
            ("/pages/structural-or-normal.html", "structural damage vs. normal settling"),
        ],
        "aeo_questions": [
            "Why does my ceiling crack in winter?",
            "Is roof truss uplift dangerous?",
            "Why do cracks appear at the wall-ceiling junction?",
        ],
        "schema": "FAQPage",
    },
]

# ─────────────────────────────────────────
# SYSTEM PROMPT
# ─────────────────────────────────────────
SYSTEM_PROMPT = """You are an expert SEO and AEO (Answer Engine Optimization) specialist 
rewriting pages for MyHouseIsBurping.com.

AEO means optimizing for AI search engines (Perplexity, ChatGPT, Gemini, Google SGE) 
that pull direct quotes and structured answers from web pages.

Your rewrite goals:
1. Keep the existing page structure and content — do NOT gut the article
2. Strengthen the direct-answer box at the top (concise, confident, quotable by AI)
3. Add a Q&A section at the bottom with 3-4 precise questions and crisp answers
4. Add provided internal links naturally in the body text
5. Upgrade schema markup to be richer and more complete
6. Make sure every factual claim is in a crisp, quotable sentence structure
7. Add a "Quick Answer" summary box near the top if not already present

AEO writing rules:
- Every H2 should be a full question (e.g. "What Causes House Burping?" not "Causes")
- First sentence of each section should answer that section's question directly
- Use numbered lists for processes, bulleted lists for options
- Comparison tables should have clear headers AI can parse
- The direct-answer div should be under 60 words and highly quotable

Output the COMPLETE rewritten HTML page. Keep the existing design/CSS classes.
Do not change filenames, canonical URLs, or the site's nav/footer structure."""


def build_rewrite_prompt(page_info, current_html):
    links_str = "\n".join(
        f'  - <a href="{url}">{anchor}</a>'
        for url, anchor in page_info["add_links"]
    )
    questions_str = "\n".join(f"  - {q}" for q in page_info["aeo_questions"])

    return f"""Rewrite this page for AEO (Answer Engine Optimization).

TARGET KEYWORD: {page_info['keyword']}
SCHEMA TYPE TO USE: {page_info['schema']}

INTERNAL LINKS TO ADD (weave these naturally into the body):
{links_str}

AEO QUESTIONS TO ADD (add a Q&A section near the bottom before related-questions):
{questions_str}

CURRENT PAGE HTML:
{current_html}

OUTPUT: Complete rewritten HTML page. Keep all existing classes, nav, footer unchanged.
Strengthen the direct-answer box, convert H2s to questions where not already, 
add the Q&A section, add the internal links, upgrade the JSON-LD schema."""


# ─────────────────────────────────────────
# COST TRACKING
# ─────────────────────────────────────────
def load_log():
    if os.path.exists(COST_LOG):
        with open(COST_LOG) as f:
            return json.load(f)
    return {"total_spent": 0.0, "rewrites": [], "sessions": []}

def save_log(log):
    with open(COST_LOG, "w") as f:
        json.dump(log, f, indent=2)

def cost(inp, out):
    return (inp / 1_000_000 * INPUT_COST_PER_M) + (out / 1_000_000 * OUTPUT_COST_PER_M)


# ─────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────
def main():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ Set your API key first:")
        print("   Windows CMD:  set ANTHROPIC_API_KEY=sk-ant-...")
        print("   PowerShell:   $env:ANTHROPIC_API_KEY='sk-ant-...'")
        return

    if not os.path.exists("index.html"):
        print("❌ Run from your site root directory (where index.html lives)")
        return

    client = anthropic.Anthropic(api_key=api_key)
    os.makedirs(BACKUP_DIR, exist_ok=True)
    log = load_log()

    already_done = {r["file"] for r in log["rewrites"]}
    todo = [p for p in PAGES if p["file"] not in already_done]

    print("=" * 60)
    print("MyHouseIsBurping.com — AEO Site Rewriter")
    print(f"Model: {MODEL}")
    print(f"Pages to rewrite: {len(todo)} of {len(PAGES)}")
    print(f"Budget remaining: ${5.0 - log['total_spent']:.3f}")
    print("=" * 60)

    if not todo:
        print("\n✅ All pages already rewritten!")
        return

    # Preview costs
    print(f"\nEstimated cost: ~${len(todo) * 0.013:.3f} total")
    confirm = input(f"Rewrite {len(todo)} pages? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Cancelled.")
        return

    session_cost = 0.0
    session_rewrites = []

    for i, page in enumerate(todo, 1):
        filepath = page["file"]

        remaining = 5.0 - log["total_spent"] - session_cost
        if remaining < 0.05:
            print(f"\n⚠️  Budget nearly exhausted (${remaining:.3f} left). Stopping.")
            break

        if not os.path.exists(filepath):
            print(f"  ⚠️  SKIP: {filepath} (file not found — generate it first)")
            continue

        print(f"\n[{i}/{len(todo)}] {filepath}")

        # Backup
        backup_path = os.path.join(BACKUP_DIR, filepath)
        os.makedirs(os.path.dirname(backup_path), exist_ok=True)
        shutil.copy2(filepath, backup_path)

        # Read current HTML
        with open(filepath, "r", encoding="utf-8") as f:
            current_html = f.read()

        try:
            prompt = build_rewrite_prompt(page, current_html)
            
            message = client.messages.create(
                model=MODEL,
                max_tokens=8192,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            )

            new_html = message.content[0].text
            page_cost = cost(message.usage.input_tokens, message.usage.output_tokens)
            session_cost += page_cost

            # Sanity check — make sure we got real HTML back
            if "<html" not in new_html and "<!DOCTYPE" not in new_html:
                print(f"  ⚠️  Response doesn't look like HTML — skipping (backup kept)")
                continue

            # Write the rewritten file
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(new_html)

            entry = {
                "file": filepath,
                "cost": round(page_cost, 5),
                "tokens_in": message.usage.input_tokens,
                "tokens_out": message.usage.output_tokens,
                "date": datetime.now().isoformat(),
            }
            log["rewrites"].append(entry)
            session_rewrites.append(entry)

            print(f"  ✅ Rewritten | ${page_cost:.5f} | "
                  f"In: {message.usage.input_tokens} | Out: {message.usage.output_tokens}")

            import time
            time.sleep(0.5)

        except Exception as e:
            print(f"  ❌ Error: {e}")
            # Restore backup on error
            shutil.copy2(backup_path, filepath)
            print(f"  ↩️  Original restored from backup")
            continue

    # Save log
    log["total_spent"] = round(log["total_spent"] + session_cost, 5)
    log["sessions"].append({
        "date": datetime.now().isoformat(),
        "pages": len(session_rewrites),
        "cost": round(session_cost, 5),
    })
    save_log(log)

    print("\n" + "=" * 60)
    print("SESSION COMPLETE")
    print("=" * 60)
    print(f"  Pages rewritten:  {len(session_rewrites)}")
    print(f"  Session cost:     ${session_cost:.4f}")
    print(f"  Total spent:      ${log['total_spent']:.4f}")
    print(f"  Budget remaining: ${5.0 - log['total_spent']:.4f}")
    print(f"  Backups at:       {BACKUP_DIR}/")
    print("""
NEXT STEPS:
  1. Spot-check 2-3 rewritten pages in your browser
  2. Upload all changed files to your host
  3. Request re-indexing in Google Search Console
  4. Monitor rankings over 2-3 weeks
""")


if __name__ == "__main__":
    main()