"""Analyze Derpemon sprite file sizes and resolutions.

Scans the Sprites directory and reports files that may cause
rendering performance issues in Pokepelago due to large file
sizes or high resolutions.
"""

import sys
from pathlib import Path
from PIL import Image

SPRITES_DIR = Path(__file__).parent / "Derpemon" / "Sprites"

# Thresholds for flagging problematic sprites
SIZE_WARN_KB = 500
SIZE_CRIT_KB = 1000
RES_WARN_PX = 1000  # flag if width or height exceeds this
RES_CRIT_PX = 2000


def analyze_sprites():
    if not SPRITES_DIR.exists():
        print(f"Error: Sprites directory not found at {SPRITES_DIR}")
        sys.exit(1)

    entries = []
    errors = []

    for filepath in sorted(SPRITES_DIR.rglob("*.png")):
        rel = filepath.relative_to(SPRITES_DIR)
        size_bytes = filepath.stat().st_size
        size_kb = size_bytes / 1024

        try:
            with Image.open(filepath) as img:
                width, height = img.size
                megapixels = (width * height) / 1_000_000
        except Exception as e:
            errors.append((rel, str(e)))
            continue

        entries.append({
            "path": rel,
            "size_bytes": size_bytes,
            "size_kb": size_kb,
            "width": width,
            "height": height,
            "megapixels": megapixels,
        })

    if not entries:
        print("No PNG files found.")
        sys.exit(1)

    # Summary stats
    total_files = len(entries)
    total_size_mb = sum(e["size_kb"] for e in entries) / 1024
    avg_size_kb = sum(e["size_kb"] for e in entries) / total_files
    max_entry = max(entries, key=lambda e: e["size_kb"])
    avg_w = sum(e["width"] for e in entries) / total_files
    avg_h = sum(e["height"] for e in entries) / total_files

    print("=" * 70)
    print("DERPEMON SPRITE ANALYSIS")
    print("=" * 70)
    print(f"Total sprites:       {total_files}")
    print(f"Total size:          {total_size_mb:.1f} MB")
    print(f"Average file size:   {avg_size_kb:.1f} KB")
    print(f"Largest file:        {max_entry['path']} ({max_entry['size_kb']:.0f} KB)")
    print(f"Average resolution:  {avg_w:.0f} x {avg_h:.0f}")
    print()

    # Size distribution
    size_buckets = {"< 50 KB": 0, "50-100 KB": 0, "100-500 KB": 0,
                    "500 KB - 1 MB": 0, "> 1 MB": 0}
    for e in entries:
        kb = e["size_kb"]
        if kb < 50:
            size_buckets["< 50 KB"] += 1
        elif kb < 100:
            size_buckets["50-100 KB"] += 1
        elif kb < 500:
            size_buckets["100-500 KB"] += 1
        elif kb < 1024:
            size_buckets["500 KB - 1 MB"] += 1
        else:
            size_buckets["> 1 MB"] += 1

    print("FILE SIZE DISTRIBUTION")
    print("-" * 40)
    for label, count in size_buckets.items():
        bar = "#" * (count * 40 // total_files)
        print(f"  {label:<16} {count:>5}  {bar}")
    print()

    # Resolution distribution
    res_buckets = {"< 256px": 0, "256-512px": 0, "512-1024px": 0,
                   "1024-2048px": 0, "> 2048px": 0}
    for e in entries:
        max_dim = max(e["width"], e["height"])
        if max_dim < 256:
            res_buckets["< 256px"] += 1
        elif max_dim < 512:
            res_buckets["256-512px"] += 1
        elif max_dim < 1024:
            res_buckets["512-1024px"] += 1
        elif max_dim < 2048:
            res_buckets["1024-2048px"] += 1
        else:
            res_buckets["> 2048px"] += 1

    print("RESOLUTION DISTRIBUTION (max dimension)")
    print("-" * 40)
    for label, count in res_buckets.items():
        bar = "#" * (count * 40 // total_files)
        print(f"  {label:<16} {count:>5}  {bar}")
    print()

    # Flag problematic files
    large_files = [e for e in entries if e["size_kb"] >= SIZE_WARN_KB]
    high_res = [e for e in entries if e["width"] >= RES_WARN_PX or e["height"] >= RES_WARN_PX]

    if large_files:
        large_files.sort(key=lambda e: e["size_kb"], reverse=True)
        print(f"LARGE FILES (>= {SIZE_WARN_KB} KB) — {len(large_files)} found")
        print("-" * 70)
        print(f"  {'File':<50} {'Size':>8} {'Resolution':>12}")
        print(f"  {'----':<50} {'----':>8} {'----------':>12}")
        for e in large_files:
            flag = " !!!" if e["size_kb"] >= SIZE_CRIT_KB else ""
            print(f"  {str(e['path']):<50} {e['size_kb']:>7.0f}KB {e['width']}x{e['height']:>5}{flag}")
        print()

    if high_res:
        high_res.sort(key=lambda e: e["width"] * e["height"], reverse=True)
        print(f"HIGH RESOLUTION (>= {RES_WARN_PX}px) — {len(high_res)} found")
        print("-" * 70)
        print(f"  {'File':<50} {'Size':>8} {'Resolution':>12} {'MP':>6}")
        print(f"  {'----':<50} {'----':>8} {'----------':>12} {'--':>6}")
        for e in high_res:
            flag = " !!!" if e["width"] >= RES_CRIT_PX or e["height"] >= RES_CRIT_PX else ""
            print(f"  {str(e['path']):<50} {e['size_kb']:>7.0f}KB"
                  f" {e['width']}x{e['height']:>5} {e['megapixels']:>5.2f}{flag}")
        print()

    if errors:
        print(f"ERRORS ({len(errors)} files could not be read)")
        print("-" * 70)
        for path, err in errors:
            print(f"  {path}: {err}")
        print()

    # Overall assessment
    print("=" * 70)
    crit_size = sum(1 for e in entries if e["size_kb"] >= SIZE_CRIT_KB)
    crit_res = sum(1 for e in entries if e["width"] >= RES_CRIT_PX or e["height"] >= RES_CRIT_PX)
    print(f"SUMMARY: {crit_size} files over {SIZE_CRIT_KB} KB, "
          f"{crit_res} files over {RES_CRIT_PX}px — these are likely causing UI lag")
    print("=" * 70)


if __name__ == "__main__":
    analyze_sprites()
