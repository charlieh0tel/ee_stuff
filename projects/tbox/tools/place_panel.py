#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = []
# ///
"""Place footprints on the panel: every part onto its own board, panel parts
at the positions the panel drawings give them.

Run after "Update PCB from Schematic" has put the footprints on the board.

  - Each footprint's board comes from its schematic sheet path (Front /
    Control / Rear Board), so nothing can land on the wrong board.
  - Panel-edge parts (jacks, DE-9, toggles, trims) get their x from
    panel-front.svg / panel-rear.svg and sit on their board's panel edge,
    rotated to face it.  The front panel is drawn as seen from the front
    and the board is viewed from above with that edge at the top, so
    x_pcb = 300 - x_panel; the rear panel is drawn as seen from the rear,
    which matches the top view, so x_pcb = x_panel.
  - Everything else that is still at the origin is spread on a grid
    inside its board, grouped by sub-sheet, as a starting point for hand
    layout.  Already-placed parts are left alone (--all moves them too).

Usage:
    tools/place_panel.py [--all]
"""

import argparse
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PCB = os.path.join(ROOT, "kicad", "tbox.kicad_pcb")
W = 300.0
BOARDS = {
    "Front Board": (0.0, 50.0),
    "Control Board": (50.0, 180.0),
    "Rear Board": (180.0, 250.0),
}

# panel label -> reference, per panel drawing (labels as they appear in the SVGs)
FRONT = {  # (channel, label) in left-to-right order of the front drawing
    ("A", "MIC 1/4"): "J1102",
    ("A", "MIC 3.5"): "J1101",
    ("A", "HEADSET"): "J1103",
    ("A", "PH 3.5"): "J1001",
    ("A", "PH 1/4"): "J1002",
    ("B", "PH 1/4"): "J1004",
    ("B", "PH 3.5"): "J1003",
    ("B", "HEADSET"): "J1303",
    ("B", "MIC 3.5"): "J1301",
    ("B", "MIC 1/4"): "J1302",
}
REAR = {
    'B/PTT 1/4"': "J3204",
    "B/PTT 3.5": "J3203",
    "B/BIAS": "SW3204",
    "B/GAIN": "SW3202",
    "RIG  DE-9": "J3206",
    "LINE OUT": "J3303",
    "RX L": "RV3401",
    "RX R": "RV3402",
    "MIC": "RV3301",
    "LINE L": "RV3302",
    "LINE R": "RV3303",
    "A/GAIN": "SW3201",
    "A/BIAS": "SW3203",
    "A/PTT 3.5": "J3201",
    'A/PTT 1/4"': "J3202",
}


def front_positions():
    """x of each front-panel jack, left to right, from the circles in panel-front.svg."""
    t = open(os.path.join(ROOT, "panel-front.svg")).read()
    xs = sorted(
        {
            float(x)
            for x in re.findall(r'<circle class="(?:qjack|mjack)" cx="([\d.]+)"', t)
        }
    )
    order = [
        ("A", "MIC 1/4"),
        ("A", "MIC 3.5"),
        ("A", "HEADSET"),
        ("A", "PH 3.5"),
        ("A", "PH 1/4"),
        ("B", "PH 1/4"),
        ("B", "PH 3.5"),
        ("B", "HEADSET"),
        ("B", "MIC 3.5"),
        ("B", "MIC 1/4"),
    ]
    assert len(xs) == len(order), (xs, order)
    return {FRONT[k]: W - x for k, x in zip(order, xs)}


def rear_positions():
    """x of each rear-panel part from panel-rear.svg: <use ... x=> or <g transform=translate()> nearest a label."""
    t = open(os.path.join(ROOT, "panel-rear.svg")).read()
    parts = [
        (float(x), float(y))
        for x, y in re.findall(r'<use href="#\w+" x="([\d.]+)" y="([\d.]+)"/>', t)
    ]
    parts += [
        (float(x), float(y))
        for x, y in re.findall(
            r'<g transform="translate\(([\d.]+),([\d.]+)\)">\s*\n\s*<rect class="de9"',
            t,
        )
    ]
    labels = [
        (float(x), s)
        for x, s in re.findall(
            r'<text class="lbl" x="([\d.]+)" y="[\d.]+">([^<]+)</text>', t
        )
    ]
    groups = [
        (float(x), float(w), s)
        for x, w, s in re.findall(
            r'<rect class="grp" x="([\d.]+)" y="10" width="([\d.]+)"[^>]*/>\s*\n\s*<rect[^>]*/>\s*\n\s*<text class="gt"[^>]*>([^<]+)</text>',
            t,
        )
    ]

    def channel(x):
        for gx, gw, name in groups:
            if gx <= x <= gx + gw and name.startswith("CHANNEL"):
                return name[-1]
        return None

    out = {}
    for x, y in parts:
        lab = min(labels, key=lambda lb: abs(lb[0] - x))[1]
        ch = channel(x)
        key = (
            f"{ch}/{lab}"
            if ch and lab in ('PTT 1/4"', "PTT 3.5", "BIAS", "GAIN")
            else lab
        )
        if key in REAR:
            out[REAR[key]] = x
    missing = set(REAR.values()) - set(out)
    assert not missing, missing
    return out


def main():
    ap = argparse.ArgumentParser(description="Place TBox footprints on the panel.")
    ap.add_argument(
        "--all", action="store_true", help="re-place parts that were already moved"
    )
    args = ap.parse_args()
    try:
        import pcbnew
    except ImportError:
        sys.exit(subprocess.call(["/usr/bin/python3", __file__] + sys.argv[1:]))
    import pcbnew

    def mm(v):
        return int(round(v * 1_000_000))

    board = pcbnew.LoadBoard(PCB)
    fps = list(board.GetFootprints())
    if not fps:
        sys.exit(
            "no footprints on the board yet: run Update PCB from Schematic (F8) in KiCad and save first"
        )
    fx, rx = front_positions(), rear_positions()
    placed, gridded, unknown = 0, 0, []
    grid = {}  # (board, sheet) -> [refs]
    for fp in fps:
        ref = fp.GetReference()
        sheet = fp.GetSheetname()
        top = sheet.strip("/").split("/")[0] if sheet else ""
        if top not in BOARDS:
            unknown.append((ref, sheet))
            continue
        y0, y1 = BOARDS[top]
        if ref in fx:
            fp.SetPosition(pcbnew.VECTOR2I(mm(fx[ref]), mm(y0 + 0.0)))
            fp.SetOrientationDegrees(180)  # jack opening toward the panel edge (top)
            placed += 1
        elif ref in rx:
            fp.SetPosition(pcbnew.VECTOR2I(mm(rx[ref]), mm(y1 - 0.0)))
            fp.SetOrientationDegrees(0)  # opening toward the bottom edge
            placed += 1
        else:
            if fp.GetPosition() == pcbnew.VECTOR2I(0, 0) or args.all:
                grid.setdefault((top, sheet), []).append(fp)
    # spread the rest: one column band per sub-sheet, 6 mm pitch, inside the board
    for (top, sheet), items in sorted(grid.items()):
        y0, y1 = BOARDS[top]
        bands = sorted({s for (t, s) in grid if t == top})
        k = bands.index(sheet)
        x0 = 15 + k * (W - 30) / max(1, len(bands))
        cols = max(1, int(((W - 30) / max(1, len(bands))) // 6))
        for i, fp in enumerate(sorted(items, key=lambda f: f.GetReference())):
            fp.SetPosition(
                pcbnew.VECTOR2I(mm(x0 + (i % cols) * 6), mm(y0 + 15 + (i // cols) * 6))
            )
            gridded += 1
    pcbnew.SaveBoard(PCB, board)
    print(f"panel parts placed: {placed}; gridded: {gridded}; footprints: {len(fps)}")
    if unknown:
        print("no board for:", unknown)
    return 0


if __name__ == "__main__":
    sys.exit(main())
