#!/usr/bin/env python3
"""
Downloads every image the site uses from Webflow's CDN into src/images,
so the site no longer depends on Webflow. Run it BEFORE you cancel Webflow,
then run `python build.py` again.

    python tools/download_images.py
"""
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LIST = ROOT / "tools" / "images.txt"
DEST = ROOT / "src" / "images"
DEST.mkdir(parents=True, exist_ok=True)

ok = failed = skipped = 0
for line in LIST.read_text(encoding="utf-8").splitlines():
    if not line.strip():
        continue
    url, name = line.split("\t")
    target = DEST / name
    if target.exists() and target.stat().st_size > 0:
        skipped += 1
        continue
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            target.write_bytes(r.read())
        ok += 1
        print("saved   ", name)
    except Exception as exc:  # keep going; report at the end
        failed += 1
        print("FAILED  ", name, "-", exc)

print(f"\n{ok} downloaded, {skipped} already present, {failed} failed")
print("Now run: python build.py")
