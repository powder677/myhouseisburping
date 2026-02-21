#!/usr/bin/env python3
"""
MyHouseIsBurping.com - Technical SEO Fix Script
Run from the ROOT of your site directory: python3 fix_site.py
Creates backups before making any changes.
"""

import os
import re
import shutil
import glob
from datetime import datetime

# ─────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────
SITE_ROOT = "."  # Run from site root
BASE_URL = "https://www.myhouseisburping.com"
BACKUP_DIR = f"_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

# ─────────────────────────────────────────
# URL FIXES: wrong slug → correct slug
# (used for canonicals, internal links, sitemap)
# ─────────────────────────────────────────
URL_FIXES = {
    # Canonical mismatches (file exists under different name)
    "house-burping-truss-uplift.html":    "roof-truss-uplift-noises.html",
    "water-heater-popping.html":          "water-heater-popping-noise.html",
    "structural-damage-vs-settling.html": "structural-or-normal.html",
    "is-house-burping-normal.html":       "house-burping-allergies-ventilation.html",  # only for allergies page canonical
    # Phantom pages in sitemap / internal links
    "pest-noises-vs-house-settling.html": "house-burping-or-mice.html",
}

# ─────────────────────────────────────────
# CORRECT METADATA for pages with wrong title/description
# ─────────────────────────────────────────
METADATA_FIXES = {
    "pages/house-burping-allergies-ventilation.html": {
        "title": "House Burping & Allergies: Ventilation Guide | MyHouseIsBurping.com",
        "description": "Can house burping improve air quality? Learn how to 'burp' your home for better ventilation, reduce allergens, and improve indoor air quality.",
        "og_title": "House Burping & Allergies: Ventilation & Air Quality",
        "og_description": "Learn how deliberate home ventilation ('burping') can reduce allergens and improve indoor air quality.",
        "canonical": "https://www.myhouseisburping.com/pages/house-burping-allergies-ventilation.html",
        "h1": "House Burping for Better Ventilation & Allergy Relief",
    },
    "pages/roof-truss-uplift-noises.html": {
        "canonical": "https://www.myhouseisburping.com/pages/roof-truss-uplift-noises.html",
    },
    "pages/water-heater-popping-noise.html": {
        "canonical": "https://www.myhouseisburping.com/pages/water-heater-popping-noise.html",
    },
    "pages/structural-or-normal.html": {
        "canonical": "https://www.myhouseisburping.com/pages/structural-or-normal.html",
    },
}

# ─────────────────────────────────────────
# SITEMAP: correct URLs for all existing pages
# ─────────────────────────────────────────
SITEMAP_PAGES = [
    ("",                                                    "1.00", "2026-02-20"),
    ("pages/house-burping-causes.html",                     "0.90", "2026-02-20"),
    ("pages/is-house-burping-normal.html",                  "0.90", "2026-02-20"),
    ("pages/how-to-stop-house-burping.html",                "0.90", "2026-02-20"),
    ("pages/when-to-call-a-professional.html",              "0.85", "2026-02-20"),
    ("pages/what-is-house-burping.html",                    "0.85", "2026-02-20"),
    ("pages/house-burping-hvac.html",                       "0.85", "2026-02-20"),
    ("pages/house-burping-at-night.html",                   "0.80", "2026-02-20"),
    ("pages/house-burping-cold-weather.html",               "0.80", "2026-02-20"),
    ("pages/wind-noises-in-house.html",                     "0.80", "2026-02-20"),
    ("pages/water-heater-popping-noise.html",               "0.80", "2026-02-20"),
    ("pages/roof-truss-uplift-noises.html",                 "0.80", "2026-02-20"),
    ("pages/structural-or-normal.html",                     "0.80", "2026-02-20"),
    ("pages/house-burping-and-mold.html",                   "0.75", "2026-02-20"),
    ("pages/house-burping-new-vs-old-house.html",           "0.75", "2026-02-20"),
    ("pages/house-burping-or-mice.html",                    "0.75", "2026-02-20"),
    ("pages/house-burping-allergies-ventilation.html",      "0.75", "2026-02-20"),
]


# ─────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────
def backup_file(path):
    dest = os.path.join(BACKUP_DIR, path)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    if os.path.exists(path):
        shutil.copy2(path, dest)

def read(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def write(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def fix_urls_in_content(content, filename):
    """Replace all wrong URLs with correct ones in HTML content."""
    changes = []
    for wrong, correct in URL_FIXES.items():
        # Skip the canonical fix for allergies page (handled in metadata fixes)
        # because is-house-burping-normal.html is a VALID page, just wrong for that one canonical
        if wrong == "is-house-burping-normal.html" and "allergies-ventilation" not in filename:
            continue

        patterns = [
            f"/pages/{wrong}",
            f"pages/{wrong}",
        ]
        for pattern in patterns:
            replacement = pattern.replace(wrong, correct)
            if pattern in content:
                content = content.replace(pattern, replacement)
                changes.append(f"  Link: {pattern} → {replacement}")

    return content, changes


def fix_canonical(content, correct_url):
    """Replace canonical href with correct URL."""
    pattern = r'<link rel="canonical" href="[^"]*"'
    replacement = f'<link rel="canonical" href="{correct_url}"'
    new_content, count = re.subn(pattern, replacement, content)
    return new_content, count > 0


def fix_og_url(content, correct_url):
    """Replace og:url with correct URL."""
    pattern = r'(<meta property="og:url" content=")[^"]*(")'
    replacement = rf'\g<1>{correct_url}\g<2>'
    new_content, count = re.subn(pattern, replacement, content)
    return new_content, count > 0


def fix_title(content, new_title):
    pattern = r'<title>[^<]*</title>'
    replacement = f'<title>{new_title}</title>'
    return re.sub(pattern, replacement, content)


def fix_meta_description(content, new_desc):
    pattern = r'(<meta name="description" content=")[^"]*(")'
    replacement = rf'\g<1>{new_desc}\g<2>'
    return re.sub(pattern, replacement, content)


def fix_og_title(content, new_title):
    pattern = r'(<meta property="og:title" content=")[^"]*(")'
    replacement = rf'\g<1>{new_title}\g<2>'
    return re.sub(pattern, replacement, content)


def fix_og_description(content, new_desc):
    pattern = r'(<meta property="og:description" content=")[^"]*(")'
    replacement = rf'\g<1>{new_desc}\g<2>'
    return re.sub(pattern, replacement, content)


def generate_sitemap():
    entries = []
    for path, priority, lastmod in SITEMAP_PAGES:
        url = f"{BASE_URL}/{path}" if path else BASE_URL + "/"
        entries.append(f"""<url>
  <loc>{url}</loc>
  <lastmod>{lastmod}T00:00:00+00:00</lastmod>
  <priority>{priority}</priority>
</url>""")
    
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
        xsi:schemaLocation="http://www.sitemaps.org/schemas/sitemap/0.9
        http://www.sitemaps.org/schemas/sitemap/0.9/sitemap.xsd">
{"".join(chr(10) + e for e in entries)}
</urlset>
"""


# ─────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────
def main():
    print("=" * 60)
    print("MyHouseIsBurping.com — Technical SEO Fix Script")
    print("=" * 60)

    if not os.path.exists("index.html"):
        print("\n❌ ERROR: Run this script from your site's ROOT directory.")
        print("   Expected to find index.html in the current folder.")
        return

    os.makedirs(BACKUP_DIR, exist_ok=True)
    print(f"\n✅ Backup directory created: {BACKUP_DIR}/")

    # ── 1. Fix all HTML files ──────────────────────────────
    html_files = glob.glob("*.html") + glob.glob("pages/*.html")
    print(f"\n📄 Processing {len(html_files)} HTML files...\n")

    total_changes = 0

    for filepath in sorted(html_files):
        backup_file(filepath)
        content = read(filepath)
        original = content
        file_changes = []

        # Fix broken internal links in ALL files
        content, link_changes = fix_urls_in_content(content, filepath)
        file_changes.extend(link_changes)

        # Apply per-file metadata fixes
        if filepath in METADATA_FIXES:
            fixes = METADATA_FIXES[filepath]
            
            if "canonical" in fixes:
                content, changed = fix_canonical(content, fixes["canonical"])
                if changed:
                    file_changes.append(f"  Canonical → {fixes['canonical']}")
            
            if "title" in fixes:
                new = fix_title(content, fixes["title"])
                if new != content:
                    content = new
                    file_changes.append(f"  Title → {fixes['title']}")
            
            if "description" in fixes:
                new = fix_meta_description(content, fixes["description"])
                if new != content:
                    content = new
                    file_changes.append(f"  Meta description updated")
            
            if "og_title" in fixes:
                new = fix_og_title(content, fixes["og_title"])
                if new != content:
                    content = new
                    file_changes.append(f"  OG title updated")
            
            if "og_description" in fixes:
                new = fix_og_description(content, fixes["og_description"])
                if new != content:
                    content = new
                    file_changes.append(f"  OG description updated")

        # Always fix og:url to match canonical for metadata-listed pages
        if filepath in METADATA_FIXES and "canonical" in METADATA_FIXES[filepath]:
            canonical_url = METADATA_FIXES[filepath]["canonical"]
            new, changed = fix_og_url(content, canonical_url)
            if changed:
                content = new
                file_changes.append(f"  OG URL → {canonical_url}")

        if content != original:
            write(filepath, content)
            total_changes += len(file_changes)
            print(f"✅ Fixed: {filepath}")
            for change in file_changes:
                print(change)
        else:
            print(f"   OK:    {filepath} (no changes needed)")

    # ── 2. Rebuild sitemap.xml ─────────────────────────────
    print("\n🗺️  Rebuilding sitemap.xml...")
    backup_file("sitemap.xml")
    sitemap_content = generate_sitemap()
    write("sitemap.xml", sitemap_content)
    print(f"✅ sitemap.xml rebuilt with {len(SITEMAP_PAGES)} correct URLs")

    # ── 3. Fix robots.txt ─────────────────────────────────
    if os.path.exists("robots.txt"):
        backup_file("robots.txt")
        robots = read("robots.txt")
        # Ensure sitemap URL is www version
        if "myhouseisburping.com/sitemap.xml" in robots and "www." not in robots.split("Sitemap:")[1]:
            robots = robots.replace(
                "Sitemap: https://myhouseisburping.com/sitemap.xml",
                "Sitemap: https://www.myhouseisburping.com/sitemap.xml"
            )
            write("robots.txt", robots)
            print("✅ robots.txt: Fixed sitemap URL to www version")

    # ── 4. Summary ─────────────────────────────────────────
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Files scanned:    {len(html_files) + 1}")
    print(f"  Total fixes made: {total_changes}")
    print(f"  Sitemap entries:  {len(SITEMAP_PAGES)}")
    print(f"  Backup saved to:  {BACKUP_DIR}/")
    print("""
NEXT STEPS:
  1. Upload all changed files to your host
  2. Go to Google Search Console → Sitemaps
  3. Submit: https://www.myhouseisburping.com/sitemap.xml
  4. Request indexing on the 4 pages with fixed canonicals
  5. Run generate_articles.py to start content expansion
""")


if __name__ == "__main__":
    main()