"""Resize Derpemon sprites to a maximum dimension while preserving aspect ratios.

Usage:
    python resize_sprites.py [--max-size 400] [--dry-run] [--output-dir DIR]

By default, resizes sprites in-place within Derpemon/Sprites/.
"""

import argparse
import sys
from pathlib import Path
from PIL import Image

SPRITES_DIR = Path(__file__).parent / "Derpemon" / "Sprites"


def resize_sprite(filepath, max_size, dry_run=False, output_dir=None):
    """Resize a single sprite. Returns (original_size, new_size, saved_bytes) or None if skipped."""
    try:
        img = Image.open(filepath)
    except Exception as e:
        print(f"  ERROR: {filepath}: {e}")
        return None

    width, height = img.size
    max_dim = max(width, height)

    if max_dim <= max_size:
        img.close()
        return None  # already within limits

    scale = max_size / max_dim
    new_width = round(width * scale)
    new_height = round(height * scale)

    original_bytes = filepath.stat().st_size

    if dry_run:
        img.close()
        # Estimate new size proportional to pixel reduction
        pixel_ratio = (new_width * new_height) / (width * height)
        estimated_bytes = round(original_bytes * pixel_ratio)
        return (width, height), (new_width, new_height), original_bytes - estimated_bytes

    resized = img.resize((new_width, new_height), Image.LANCZOS)

    if output_dir:
        dest = output_dir / filepath.relative_to(SPRITES_DIR)
        dest.parent.mkdir(parents=True, exist_ok=True)
    else:
        dest = filepath

    # Save to a temp file next to the original to compare sizes
    tmp_path = filepath.with_suffix(".tmp.png")
    resized.save(tmp_path, "PNG", optimize=True)
    resized.close()
    img.close()

    new_bytes = tmp_path.stat().st_size
    if new_bytes >= original_bytes:
        # Resized version is larger — keep the original
        tmp_path.unlink()
        return None

    # Replace with the smaller resized version
    dest_path = dest if output_dir else filepath
    tmp_path.replace(dest_path)

    return (width, height), (new_width, new_height), original_bytes - new_bytes


def main():
    parser = argparse.ArgumentParser(description="Resize Derpemon sprites to a max dimension.")
    parser.add_argument("--max-size", type=int, default=400,
                        help="Maximum width or height in pixels (default: 400)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be resized without making changes")
    parser.add_argument("--output-dir", type=str, default=None,
                        help="Write resized sprites to a separate directory instead of in-place")
    args = parser.parse_args()

    if not SPRITES_DIR.exists():
        print(f"Error: Sprites directory not found at {SPRITES_DIR}")
        sys.exit(1)

    output_dir = Path(args.output_dir) if args.output_dir else None

    if args.dry_run:
        print(f"DRY RUN — showing what would be resized (max {args.max_size}px)")
    elif output_dir:
        print(f"Resizing sprites to max {args.max_size}px -> {output_dir}")
    else:
        print(f"Resizing sprites in-place to max {args.max_size}px")
    print()

    files = sorted(SPRITES_DIR.rglob("*.png"))
    resized_count = 0
    skipped_count = 0
    total_saved = 0

    for filepath in files:
        rel = filepath.relative_to(SPRITES_DIR)
        result = resize_sprite(filepath, args.max_size, args.dry_run, output_dir)

        if result is None:
            skipped_count += 1
            continue

        (ow, oh), (nw, nh), saved = result
        resized_count += 1
        total_saved += saved
        label = "estimated" if args.dry_run else "saved"
        print(f"  {rel}: {ow}x{oh} -> {nw}x{nh} ({label} {saved / 1024:.1f} KB)")

    print()
    print(f"Done. {resized_count} resized, {skipped_count} already within {args.max_size}px.")
    saved_mb = total_saved / (1024 * 1024)
    label = "Estimated savings" if args.dry_run else "Total saved"
    print(f"{label}: {saved_mb:.1f} MB")


if __name__ == "__main__":
    main()
