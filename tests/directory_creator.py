# directory_creator.py
from __future__ import annotations

import colorsys
import itertools
import random
from pathlib import Path
from typing import Iterator, Mapping

from PIL import Image

# ────────────────────────────────
# Config section – edit freely
# ────────────────────────────────
SETTINGS: dict[str, dict[str, int | str]] = {
    "tiny":   dict(count=5,     depth=1, fanout=1,
                   pattern="{idx:02}.png"),
    "small":  dict(count=25,    depth=2, fanout=3,
                   pattern="album_{d0}/{idx:02}.png"),
    "medium": dict(count=300,   depth=3, fanout=5,
                   pattern="genre_{d0}/artist_{d1}/img_{idx:04}.png"),
    "large":  dict(count=1_000, depth=4, fanout=10,
                   pattern="collection_{d0}/year_{d1}/month_{d2}/pic_{idx:05}.png"),
}
IMAGE_SIZE   = (128, 128)   # px
PALETTE_SEED = 42           # deterministic colours
# ────────────────────────────────


# ---------- Palette helpers ----------
def _make_palette(n: int) -> list[tuple[int, int, int]]:
    """Evenly-spaced HSV hues → RGB palette of *n* colours."""
    random.seed(PALETTE_SEED)
    return [
        tuple(int(c * 255) for c in colorsys.hsv_to_rgb(i / n, 1.0, 1.0))
        for i in range(n)
    ]


_PALETTE: list[tuple[int, int, int]]             = _make_palette(360)
_palette_iter: Iterator[tuple[int, int, int]]    = itertools.cycle(_PALETTE)
rand_colour:  callable[[], tuple[int, int, int]] = _palette_iter.__next__  # noqa: E501


# ---------- Image helpers ----------
def _write_png(path: Path, colour: tuple[int, int, int]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", IMAGE_SIZE, colour)
    img.save(path, "PNG")


def _build_tree(*, root: Path, pattern: str,
                total: int, fanout: int, depth: int) -> None:
    """Generate *total* images beneath *root* following the *pattern*."""
    counters = [0] * depth          # odometer for nested dirs

    for idx in range(total):
        # roll the “odometer”
        for i in reversed(range(depth)):
            counters[i] = (counters[i] + (1 if i == depth - 1 else 0)) % fanout
            if counters[i] != 0:
                break

        mapping = {f"d{i}": counters[i] for i in range(depth)} | {"idx": idx}
        rel_path = Path(pattern.format(**mapping))
        _write_png(root / rel_path, rand_colour())


# ────────────────────────────────
# PUBLIC API
# ────────────────────────────────
def generate_sets(root: Path | str = "sample_sets",
                  *,
                  overrides: Mapping[str, int] | None = None) -> None:
    """
    Build every data-set (tiny / small / medium / large) under *root*.

    Parameters
    ----------
    root : str | pathlib.Path
        Destination directory. Created if it doesn’t exist.
    overrides : dict[str, int], optional
        Per-set image counts, e.g. ``{'small': 100}``.
    """
    root = Path(root).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)

    overrides = overrides or {}
    for name, cfg in SETTINGS.items():
        cfg = cfg.copy()
        if name in overrides:
            cfg["count"] = overrides[name]

        print(f" → Building {name!r} ({cfg['count']} images)")
        _build_tree(root=root / name,
                    pattern=cfg["pattern"],
                    total=int(cfg["count"]),
                    fanout=int(cfg["fanout"]),
                    depth=int(cfg["depth"]))

    print("\n✓ All test sets generated.\n"
          "   – Tiny   : quick load test\n"
          "   – Small  : basic paging\n"
          "   – Medium : thumbnail caching, scroll perf\n"
          "   – Large  : stress-test async loaders & DB writes")


# ────────────────────────────────
# Backwards-compatible CLI entry-point
# ────────────────────────────────
if __name__ == "__main__":
    import argparse, sys

    if len(sys.argv) == 1:
        # Launched with “Run” button / no args → just use defaults
        generate_sets()
    else:
        # Classic CLI – still available if you want it
        p = argparse.ArgumentParser(description="Generate sample image sets")
        p.add_argument("--root", type=Path, default="sample_sets",
                       help="Destination directory (default: ./sample_sets)")
        for key in SETTINGS:
            p.add_argument(f"--{key}", type=int,
                           help=f"Override image count for the {key!r} set.")
        ns = p.parse_args()

        counts = {k: v for k, v in vars(ns).items() if k in SETTINGS and v is not None}
        generate_sets(ns.root, overrides=counts)
