#!/usr/bin/env python3
"""
One-time script: inject BTN:GA4 and BTN:FOOTER markers into all site HTML files.
Run locally, then commit/push each repo.
"""
import os
import re
import sys

SITES_DIR = os.environ.get("SITES_DIR", "D:/Bankruptcy/statute-sites")
DRY_RUN = "--dry-run" in sys.argv

def inject_ga4_markers(html):
    """Wrap GA4 snippet with markers."""
    if "BTN:GA4:START" in html:
        return html, False
    pattern = r'(<script async src="https://www\.googletagmanager\.com.*?</script>\s*<script>.*?gtag.*?</script>)'
    match = re.search(pattern, html, re.DOTALL)
    if match:
        replacement = f'<!-- BTN:GA4:START -->\n{match.group(1)}\n<!-- BTN:GA4:END -->'
        return html.replace(match.group(1), replacement), True
    return html, False

def inject_footer_markers(html):
    """Wrap footer with markers."""
    if "BTN:FOOTER:START" in html:
        return html, False
    pattern = r'(<footer.*?</footer>)'
    match = re.search(pattern, html, re.DOTALL)
    if match:
        replacement = f'<!-- BTN:FOOTER:START -->\n{match.group(1)}\n<!-- BTN:FOOTER:END -->'
        return html.replace(match.group(1), replacement), True
    return html, False

def process_site(site_dir):
    changed_files = 0
    for fname in os.listdir(site_dir):
        if not fname.endswith(".html"):
            continue
        fpath = os.path.join(site_dir, fname)
        with open(fpath, "r", encoding="utf-8") as f:
            html = f.read()

        html, ga4_changed = inject_ga4_markers(html)
        html, footer_changed = inject_footer_markers(html)

        if ga4_changed or footer_changed:
            if not DRY_RUN:
                with open(fpath, "w", encoding="utf-8") as f:
                    f.write(html)
            markers = []
            if ga4_changed: markers.append("GA4")
            if footer_changed: markers.append("FOOTER")
            print(f"  {fname}: injected {', '.join(markers)}")
            changed_files += 1

    return changed_files

def main():
    total_sites = 0
    total_files = 0

    for d in sorted(os.listdir(SITES_DIR)):
        site_dir = os.path.join(SITES_DIR, d)
        if not os.path.isdir(site_dir):
            continue
        if not os.path.exists(os.path.join(site_dir, "index.html")):
            continue

        changed = process_site(site_dir)
        if changed > 0:
            total_sites += 1
            total_files += changed
            print(f"  {d}: {changed} files marked")

    print(f"\n{'DRY RUN -- ' if DRY_RUN else ''}Injected markers in {total_files} files across {total_sites} sites")

if __name__ == "__main__":
    main()
