#!/usr/bin/env python3
"""
Propagate shared components to all BTN network repos.
Reads components-manifest.json, clones each repo, patches, commits, pushes.
"""
import json
import os
import re
import subprocess
import sys
import time

DRY_RUN = os.environ.get("DRY_RUN", "false") == "true"
COMPONENT = os.environ.get("COMPONENT", "all")
BATCH_SIZE = int(os.environ.get("BATCH_SIZE", "50"))
GH_TOKEN = os.environ.get("GH_TOKEN", "")

def run(cmd, cwd=None):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
    return result.returncode, result.stdout.strip(), result.stderr.strip()

def load_component(path):
    with open(path, "r") as f:
        return f.read()

def patch_markers(html, marker, content):
    """Replace content between <!-- MARKER:START --> and <!-- MARKER:END -->"""
    pattern = rf'(<!-- {marker}:START -->).*?(<!-- {marker}:END -->)'
    replacement = f'<!-- {marker}:START -->\n{content}\n<!-- {marker}:END -->'
    new_html, count = re.subn(pattern, replacement, html, flags=re.DOTALL)
    return new_html, count

def process_repo(repo_name, org, components):
    url = f"https://x-access-token:{GH_TOKEN}@github.com/{org}/{repo_name}.git"
    work_dir = f"/tmp/btn_prop/{repo_name}"

    # Clone
    code, out, err = run(f"git clone --depth 1 {url} {work_dir}")
    if code != 0:
        print(f"  SKIP {repo_name}: clone failed -- {err[:80]}")
        return False

    changed = False

    # File copies (btn-engage.js, favicon.svg)
    for comp_name, comp in components.items():
        if comp.get("type") != "file-copy":
            continue
        if COMPONENT != "all" and COMPONENT != comp_name:
            continue
        src = comp["file"]
        dst = os.path.join(work_dir, os.path.basename(src))
        if os.path.exists(dst):
            with open(src) as f:
                new = f.read()
            with open(dst) as f:
                old = f.read()
            if new != old:
                with open(dst, "w") as f:
                    f.write(new)
                changed = True
                print(f"  {repo_name}: updated {os.path.basename(src)}")

    # Marker-based replacements (GA4, footer)
    index_path = os.path.join(work_dir, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r") as f:
            html = f.read()

        for comp_name, comp in components.items():
            marker = comp.get("marker")
            if not marker:
                continue
            if COMPONENT != "all" and COMPONENT != comp_name.replace("-", ""):
                continue
            content = load_component(comp["file"])
            new_html, count = patch_markers(html, marker, content)
            if count > 0:
                html = new_html
                changed = True
                print(f"  {repo_name}: patched {marker} ({count} replacements)")

        if changed:
            with open(index_path, "w") as f:
                f.write(html)

        # Also patch all other HTML files
        for fname in os.listdir(work_dir):
            if fname.endswith(".html") and fname != "index.html":
                fpath = os.path.join(work_dir, fname)
                with open(fpath, "r") as f:
                    page_html = f.read()
                page_changed = False
                for comp_name, comp in components.items():
                    marker = comp.get("marker")
                    if not marker:
                        continue
                    content = load_component(comp["file"])
                    new_page, count = patch_markers(page_html, marker, content)
                    if count > 0:
                        page_html = new_page
                        page_changed = True
                if page_changed:
                    with open(fpath, "w") as f:
                        f.write(page_html)
                    changed = True

    if not changed:
        print(f"  {repo_name}: no changes needed")
        return False

    if DRY_RUN:
        print(f"  {repo_name}: DRY RUN -- would commit and push")
        return True

    # Commit and push
    run("git add -A", cwd=work_dir)
    run('git config user.email "bot@openbankruptcyproject.org"', cwd=work_dir)
    run('git config user.name "BTN Bot"', cwd=work_dir)
    code, _, _ = run('git commit -m "Update shared components [automated]"', cwd=work_dir)
    if code != 0:
        return False
    code, _, err = run("git push", cwd=work_dir)
    if code != 0:
        print(f"  {repo_name}: push failed -- {err[:80]}")
        return False

    print(f"  {repo_name}: pushed")
    return True

def main():
    with open("components-manifest.json") as f:
        manifest = json.load(f)

    repos = manifest["repos"]
    components = manifest["components"]
    total = len(repos)

    print(f"Propagating to {total} repos (component={COMPONENT}, dry_run={DRY_RUN})")
    print(f"Batch size: {BATCH_SIZE}")
    print()

    os.makedirs("/tmp/btn_prop", exist_ok=True)
    updated = 0
    skipped = 0

    for i, repo in enumerate(repos):
        if process_repo(repo["name"], repo["org"], components):
            updated += 1
        else:
            skipped += 1

        # Rate limit: pause between batches
        if (i + 1) % BATCH_SIZE == 0 and i + 1 < total:
            print(f"\n  Batch complete ({i+1}/{total}). Pausing 60s...")
            time.sleep(60)

    print(f"\nDone: {updated} updated, {skipped} skipped, {total} total")

if __name__ == "__main__":
    main()
