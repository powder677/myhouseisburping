#!/usr/bin/env python3
# MyHouseIsBurping.com - TARGETED FIX SCRIPT
# Run from site root (where index.html lives):
#   python fix_final.py
#
# What this does:
#   1. Moves radon/ files into pages/ with correct slugs
#   2. Creates house-burping-or-mice.html from pest-noises file
#   3. Fixes ALL internal links across every HTML file
#   4. Fixes radon/ path refs to /pages/ throughout
#   5. Rebuilds sitemap.xml with correct paths

import os, re, shutil, glob
from datetime import datetime

BACKUP = f"_fix_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

# ── Radon file mapping: radon/source → pages/destination ─────────────────────
# Based on your actual /radon/ folder contents
RADON_MOVES = {
    "radon/index.html":                  "pages/radon-hub.html",
    "radon/radon-gas-in-house-signs.html":"pages/radon-gas-in-house-signs.html",
    "radon/best-radon-test-kits.html":   "pages/best-radon-test-kits.html",
    "radon/how-to-reduce-radon-in-house.html":"pages/how-to-reduce-radon-in-house.html",
    "radon/radon-mitigation-fan-guide.html":"pages/radon-mitigation-fan-guide.html",
    "radon/radon-levels-by-state.html":  "pages/radon-levels-by-state.html",
}

# ── All URL fixes: wrong href → correct href ──────────────────────────────────
LINK_FIXES = {
    # Radon folder → pages folder
    '"/radon/"':                           '"/pages/radon-hub.html"',
    '"/radon/index.html"':                 '"/pages/radon-hub.html"',
    '"/radon/radon-gas-in-house-signs.html"': '"/pages/radon-gas-in-house-signs.html"',
    '"/radon/best-radon-test-kits.html"': '"/pages/best-radon-test-kits.html"',
    '"/radon/how-to-reduce-radon-in-house.html"': '"/pages/how-to-reduce-radon-in-house.html"',
    '"/radon/radon-mitigation-fan-guide.html"': '"/pages/radon-mitigation-fan-guide.html"',
    '"/radon/radon-levels-by-state.html"': '"/pages/radon-levels-by-state.html"',

    # Relative radon links (from inside pages/ folder)
    '"../radon/"':                          '"radon-hub.html"',
    '"../radon/index.html"':               '"radon-hub.html"',
    '"../radon/radon-gas-in-house-signs.html"': '"radon-gas-in-house-signs.html"',
    '"../radon/best-radon-test-kits.html"': '"best-radon-test-kits.html"',
    '"../radon/how-to-reduce-radon-in-house.html"': '"how-to-reduce-radon-in-house.html"',
    '"../radon/radon-mitigation-fan-guide.html"': '"radon-mitigation-fan-guide.html"',
    '"../radon/radon-levels-by-state.html"': '"radon-levels-by-state.html"',

    # Wrong page slugs → correct slugs
    '"/pages/water-heater-popping.html"':      '"/pages/water-heater-popping-noise.html"',
    '"water-heater-popping.html"':             '"water-heater-popping-noise.html"',
    '"/pages/structural-damage-vs-settling.html"': '"/pages/structural-or-normal.html"',
    '"structural-damage-vs-settling.html"':    '"structural-or-normal.html"',
    '"/pages/house-burping-truss-uplift.html"': '"/pages/roof-truss-uplift-noises.html"',
    '"house-burping-truss-uplift.html"':       '"roof-truss-uplift-noises.html"',
    '"/pages/pest-noises-vs-house-settling.html"': '"/pages/house-burping-or-mice.html"',
    '"pest-noises-vs-house-settling.html"':    '"house-burping-or-mice.html"',

    # carbon-monoxide page may be missing from radon folder
    '"/radon/carbon-monoxide-vs-radon-home.html"': '"/pages/carbon-monoxide-vs-radon-home.html"',
    '"../radon/carbon-monoxide-vs-radon-home.html"': '"carbon-monoxide-vs-radon-home.html"',
}

# ── Canonical fixes per file ──────────────────────────────────────────────────
CANONICAL_FIXES = {
    "pages/roof-truss-uplift-noises.html":
        "https://www.myhouseisburping.com/pages/roof-truss-uplift-noises.html",
    "pages/water-heater-popping-noise.html":
        "https://www.myhouseisburping.com/pages/water-heater-popping-noise.html",
    "pages/structural-or-normal.html":
        "https://www.myhouseisburping.com/pages/structural-or-normal.html",
    "pages/house-burping-allergies-ventilation.html":
        "https://www.myhouseisburping.com/pages/house-burping-allergies-ventilation.html",
    "pages/radon-hub.html":
        "https://www.myhouseisburping.com/pages/radon-hub.html",
    "pages/radon-gas-in-house-signs.html":
        "https://www.myhouseisburping.com/pages/radon-gas-in-house-signs.html",
    "pages/best-radon-test-kits.html":
        "https://www.myhouseisburping.com/pages/best-radon-test-kits.html",
    "pages/how-to-reduce-radon-in-house.html":
        "https://www.myhouseisburping.com/pages/how-to-reduce-radon-in-house.html",
    "pages/radon-mitigation-fan-guide.html":
        "https://www.myhouseisburping.com/pages/radon-mitigation-fan-guide.html",
    "pages/radon-levels-by-state.html":
        "https://www.myhouseisburping.com/pages/radon-levels-by-state.html",
}

# ── Sitemap: all correct URLs ─────────────────────────────────────────────────
SITEMAP_URLS = [
    ("https://www.myhouseisburping.com/", "1.00"),
    ("https://www.myhouseisburping.com/pages/index.html", "0.90"),
    ("https://www.myhouseisburping.com/pages/what-is-house-burping.html", "0.85"),
    ("https://www.myhouseisburping.com/pages/house-burping-causes.html", "0.90"),
    ("https://www.myhouseisburping.com/pages/is-house-burping-normal.html", "0.90"),
    ("https://www.myhouseisburping.com/pages/how-to-stop-house-burping.html", "0.85"),
    ("https://www.myhouseisburping.com/pages/when-to-call-a-professional.html", "0.85"),
    ("https://www.myhouseisburping.com/pages/house-burping-hvac.html", "0.85"),
    ("https://www.myhouseisburping.com/pages/water-heater-popping-noise.html", "0.85"),
    ("https://www.myhouseisburping.com/pages/water-heater-popping-sounds-fix.html", "0.80"),
    ("https://www.myhouseisburping.com/pages/water-heater-rumbling-noise.html", "0.80"),
    ("https://www.myhouseisburping.com/pages/pipes-knocking-in-walls.html", "0.80"),
    ("https://www.myhouseisburping.com/pages/wind-noises-in-house.html", "0.85"),
    ("https://www.myhouseisburping.com/pages/house-burping-cold-weather.html", "0.80"),
    ("https://www.myhouseisburping.com/pages/house-burping-at-night.html", "0.80"),
    ("https://www.myhouseisburping.com/pages/roof-truss-uplift-noises.html", "0.80"),
    ("https://www.myhouseisburping.com/pages/structural-or-normal.html", "0.80"),
    ("https://www.myhouseisburping.com/pages/house-shaking-in-wind.html", "0.80"),
    ("https://www.myhouseisburping.com/pages/house-popping-sound-cold-weather.html", "0.75"),
    ("https://www.myhouseisburping.com/pages/vinyl-siding-noise-when-windy.html", "0.75"),
    ("https://www.myhouseisburping.com/pages/creaking-windows-when-windy.html", "0.75"),
    ("https://www.myhouseisburping.com/pages/foundation-settling-noises.html", "0.75"),
    ("https://www.myhouseisburping.com/pages/house-creaking-at-night-causes.html", "0.80"),
    ("https://www.myhouseisburping.com/pages/why-do-old-houses-creak.html", "0.80"),
    ("https://www.myhouseisburping.com/pages/floor-joist-creaking-fix.html", "0.75"),
    ("https://www.myhouseisburping.com/pages/house-burping-new-vs-old-house.html", "0.75"),
    ("https://www.myhouseisburping.com/pages/house-burping-or-mice.html", "0.75"),
    ("https://www.myhouseisburping.com/pages/attic-noises-at-night.html", "0.75"),
    ("https://www.myhouseisburping.com/pages/house-burping-and-mold.html", "0.75"),
    ("https://www.myhouseisburping.com/pages/house-burping-allergies-ventilation.html", "0.80"),
    ("https://www.myhouseisburping.com/pages/how-to-burp-your-house-ventilation.html", "0.80"),
    ("https://www.myhouseisburping.com/pages/indoor-air-quality-improvement.html", "0.80"),
    ("https://www.myhouseisburping.com/pages/radon-hub.html", "0.90"),
    ("https://www.myhouseisburping.com/pages/radon-gas-in-house-signs.html", "0.85"),
    ("https://www.myhouseisburping.com/pages/best-radon-test-kits.html", "0.85"),
    ("https://www.myhouseisburping.com/pages/how-to-reduce-radon-in-house.html", "0.85"),
    ("https://www.myhouseisburping.com/pages/radon-mitigation-fan-guide.html", "0.85"),
    ("https://www.myhouseisburping.com/pages/radon-levels-by-state.html", "0.80"),
    ("https://www.myhouseisburping.com/pages/carbon-monoxide-vs-radon-home.html", "0.80"),
]


# ─────────────────────────────────────────────────────────────────────────────
def rread(path):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()

def wwrite(path, text):
    os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)

def backup(path):
    if os.path.exists(path):
        dest = os.path.join(BACKUP, path)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        shutil.copy2(path, dest)


# ─────────────────────────────────────────────────────────────────────────────
# STEP 1: Move radon/ files → pages/
# ─────────────────────────────────────────────────────────────────────────────
def step1_move_radon():
    print("\n── STEP 1: Move radon/ → pages/ ──────────────────────────")
    moved = 0
    for src, dst in RADON_MOVES.items():
        if not os.path.exists(src):
            print(f"  SKIP (not found): {src}")
            continue
        backup(dst)  # backup destination if it exists
        shutil.copy2(src, dst)
        moved += 1
        print(f"  ✅ {src} → {dst}")

    # Also handle carbon-monoxide if it's in radon/
    co_src = "radon/carbon-monoxide-vs-radon-home.html"
    co_dst = "pages/carbon-monoxide-vs-radon-home.html"
    if os.path.exists(co_src) and not os.path.exists(co_dst):
        shutil.copy2(co_src, co_dst)
        print(f"  ✅ {co_src} → {co_dst}")
        moved += 1
    elif os.path.exists(co_dst):
        print(f"  OK (already exists): {co_dst}")

    print(f"  Moved: {moved} files")


# ─────────────────────────────────────────────────────────────────────────────
# STEP 2: Create house-burping-or-mice.html from pest-noises file
# ─────────────────────────────────────────────────────────────────────────────
def step2_fix_mice_page():
    print("\n── STEP 2: Fix house-burping-or-mice.html ─────────────────")
    src = "pages/pest-noises-vs-house-settling.html"
    dst = "pages/house-burping-or-mice.html"

    if os.path.exists(dst):
        print(f"  OK (already exists): {dst}")
    elif os.path.exists(src):
        backup(dst)
        content = rread(src)
        # Fix canonical to point to correct URL
        content = re.sub(
            r'<link rel="canonical" href="[^"]*"',
            '<link rel="canonical" href="https://www.myhouseisburping.com/pages/house-burping-or-mice.html"',
            content
        )
        # Fix og:url
        content = re.sub(
            r'(<meta property="og:url" content=")[^"]*(")',
            r'\g<1>https://www.myhouseisburping.com/pages/house-burping-or-mice.html\g<2>',
            content
        )
        wwrite(dst, content)
        print(f"  ✅ Created: {dst} (from {src})")
    else:
        print(f"  ⚠️  Neither source file found — {dst} will need manual creation")


# ─────────────────────────────────────────────────────────────────────────────
# STEP 3: Fix all links across all HTML files
# ─────────────────────────────────────────────────────────────────────────────
def step3_fix_links():
    print("\n── STEP 3: Fix all internal links ─────────────────────────")

    # All HTML files in root, pages/, and radon/
    all_files = (
        glob.glob("*.html") +
        glob.glob("pages/*.html") +
        glob.glob("radon/*.html")
    )

    total_changes = 0
    for filepath in sorted(all_files):
        original = rread(filepath)
        content  = original
        file_changes = []

        # Apply all link fixes
        for wrong, correct in LINK_FIXES.items():
            if wrong in content:
                content = content.replace(wrong, correct)
                file_changes.append(f"link: {wrong} → {correct}")

        # Fix canonical for files with known correct canonicals
        if filepath in CANONICAL_FIXES:
            correct_url = CANONICAL_FIXES[filepath]
            new = re.sub(
                r'<link rel="canonical" href="[^"]*"',
                f'<link rel="canonical" href="{correct_url}"',
                content
            )
            if new != content:
                content = new
                file_changes.append(f"canonical fixed")

            # Fix og:url to match
            new = re.sub(
                r'(<meta property="og:url" content=")[^"]*(")',
                rf'\g<1>{correct_url}\g<2>',
                content
            )
            if new != content:
                content = new
                file_changes.append("og:url fixed")

        # Ensure AdSense tag is present
        if 'ca-pub-3688809656284836' not in content and '</head>' in content:
            adsense = '\n  <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-3688809656284836" crossorigin="anonymous"></script>'
            content = content.replace('</head>', f'{adsense}\n</head>')
            file_changes.append("AdSense tag added")

        # Ensure hub nav link exists in nav
        if 'href="/pages/"' not in content and 'All Articles' not in content:
            # Try to inject after Home nav link
            for pattern in ['<li><a href="/">Home</a></li>', "<li><a href='/'>Home</a></li>"]:
                if pattern in content:
                    content = content.replace(
                        pattern,
                        pattern + '\n        <li><a href="/pages/">All Articles</a></li>'
                    )
                    file_changes.append("hub nav link added")
                    break

        if content != original:
            backup(filepath)
            wwrite(filepath, content)
            total_changes += len(file_changes)
            print(f"  ✅ {filepath}")
            for c in file_changes:
                print(f"     · {c}")

    print(f"\n  Total link fixes: {total_changes}")


# ─────────────────────────────────────────────────────────────────────────────
# STEP 4: Fix radon pages that now live in pages/ — update their relative links
# ─────────────────────────────────────────────────────────────────────────────
def step4_fix_radon_internal_links():
    print("\n── STEP 4: Fix radon pages' internal relative links ───────")
    # These files were in radon/ and used relative links like "index.html"
    # Now they're in pages/ and need to link correctly

    radon_in_pages = [
        "pages/radon-hub.html",
        "pages/radon-gas-in-house-signs.html",
        "pages/best-radon-test-kits.html",
        "pages/how-to-reduce-radon-in-house.html",
        "pages/radon-mitigation-fan-guide.html",
        "pages/radon-levels-by-state.html",
    ]

    # Relative links within radon cluster that might exist
    radon_relative_fixes = {
        '"index.html"':                          '"radon-hub.html"',
        '"radon-gas-in-house-signs.html"':       '"radon-gas-in-house-signs.html"',  # already correct
        '"best-radon-test-kits.html"':           '"best-radon-test-kits.html"',       # already correct
        '"how-to-reduce-radon-in-house.html"':   '"how-to-reduce-radon-in-house.html"', # correct
        '"radon-mitigation-fan-guide.html"':     '"radon-mitigation-fan-guide.html"', # correct
        '"radon-levels-by-state.html"':          '"radon-levels-by-state.html"',      # correct
        # Fix links back to main pages
        '"../pages/house-burping-hvac.html"':    '"house-burping-hvac.html"',
        '"../pages/structural-or-normal.html"':  '"structural-or-normal.html"',
        '"../index.html"':                       '"/"',
        # CSS and JS paths that may need updating
        '"../css/styles.css"':                   '"../css/styles.css"',  # correct for pages/
        '"css/styles.css"':                      '"../css/styles.css"',  # fix if missing ../
    }

    for filepath in radon_in_pages:
        if not os.path.exists(filepath):
            continue
        original = rread(filepath)
        content  = original
        changes  = []

        for wrong, correct in radon_relative_fixes.items():
            if wrong in content and wrong != correct:
                content = content.replace(wrong, correct)
                changes.append(f"{wrong} → {correct}")

        # Make sure CSS path is correct for pages/ location
        if '"css/styles.css"' in content:
            content = content.replace('"css/styles.css"', '"../css/styles.css"')
            changes.append("css path fixed")
        if '"js/main.js"' in content:
            content = content.replace('"js/main.js"', '"../js/main.js"')
            changes.append("js path fixed")

        if content != original:
            backup(filepath)
            wwrite(filepath, content)
            print(f"  ✅ {filepath}")
            for c in changes:
                print(f"     · {c}")
        else:
            print(f"     {filepath} (no changes)")


# ─────────────────────────────────────────────────────────────────────────────
# STEP 5: Rebuild sitemap.xml
# ─────────────────────────────────────────────────────────────────────────────
def step5_rebuild_sitemap():
    print("\n── STEP 5: Rebuild sitemap.xml ─────────────────────────────")
    backup("sitemap.xml")
    today = datetime.now().strftime("%Y-%m-%d")

    entries = "\n".join(
        f"  <url>\n    <loc>{url}</loc>\n    <lastmod>{today}</lastmod>\n    <priority>{pri}</priority>\n  </url>"
        for url, pri in SITEMAP_URLS
    )

    sitemap = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{entries}
</urlset>
"""
    wwrite("sitemap.xml", sitemap)
    print(f"  ✅ sitemap.xml rebuilt with {len(SITEMAP_URLS)} URLs")


# ─────────────────────────────────────────────────────────────────────────────
# STEP 6: Verify — print any remaining issues
# ─────────────────────────────────────────────────────────────────────────────
def step6_verify():
    print("\n── STEP 6: Verification ────────────────────────────────────")

    expected_files = [
        "index.html",
        "pages/index.html",
        "pages/radon-hub.html",
        "pages/house-burping-or-mice.html",
        "pages/house-burping-causes.html",
        "pages/is-house-burping-normal.html",
        "pages/house-burping-hvac.html",
        "pages/water-heater-popping-noise.html",
        "pages/wind-noises-in-house.html",
        "pages/structural-or-normal.html",
        "pages/radon-gas-in-house-signs.html",
        "pages/best-radon-test-kits.html",
        "pages/how-to-reduce-radon-in-house.html",
        "pages/radon-mitigation-fan-guide.html",
        "pages/radon-levels-by-state.html",
        "pages/carbon-monoxide-vs-radon-home.html",
        "sitemap.xml",
    ]

    all_ok = True
    for f in expected_files:
        exists = os.path.exists(f)
        size   = os.path.getsize(f) if exists else 0
        status = "✅" if exists and size > 500 else ("⚠️ TINY" if exists else "❌ MISSING")
        if not exists or size < 500:
            all_ok = False
        print(f"  {status}  {f}  ({size:,} bytes)" if exists else f"  {status}  {f}")

    # Check for radon/ links still in pages/
    print("\n  Checking for leftover /radon/ links in pages/...")
    pages = glob.glob("pages/*.html")
    radon_link_found = False
    for filepath in pages:
        content = rread(filepath)
        if '/radon/' in content or '../radon/' in content:
            print(f"  ⚠️  Still has /radon/ link: {filepath}")
            radon_link_found = True
    if not radon_link_found:
        print("  ✅ No leftover /radon/ links found")

    if all_ok and not radon_link_found:
        print("\n  🎉 Everything looks good! Ready to commit and push.")
    else:
        print("\n  ⚠️  Some issues remain — see above.")

    print(f"\n  Backups saved at: {BACKUP}/")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("MyHouseIsBurping.com — Final Fix Script")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Confirm we're in the right folder
    if not os.path.exists("index.html") or not os.path.exists("pages"):
        print("\n❌ ERROR: Run from site root.")
        print(f"   Current folder: {os.getcwd()}")
        print("   Expected: index.html and pages/ folder here")
        print("\n   CMD:  cd C:\\Users\\elisa\\OneDrive\\Documents\\github\\myhouseisburping")
        print("          python fix_final.py")
        return

    os.makedirs(BACKUP, exist_ok=True)

    step1_move_radon()
    step2_fix_mice_page()
    step3_fix_links()
    step4_fix_radon_internal_links()
    step5_rebuild_sitemap()
    step6_verify()

    print("\n" + "=" * 60)
    print("DONE — Now run:")
    print()
    print("  git add .")
    print('  git commit -m "Fix: move radon to pages, fix all links, rebuild sitemap"')
    print("  git push")
    print()
    print("Then in Google Search Console:")
    print("  → Sitemaps → Submit: https://www.myhouseisburping.com/sitemap.xml")
    print("  → URL Inspection → Request indexing on radon-hub.html and pages/index.html")
    print("=" * 60)


if __name__ == "__main__":
    main()