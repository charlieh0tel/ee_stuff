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
    # ribbon headers along the inner (V-cut) edges: front/control pair at the left, control/rear pair at the right
    INNER = {
        "J1005": (50.0, "bottom", 40.0),
        "J2001": (50.0, "top", 40.0),
        "J2002": (180.0, "bottom", 260.0),
        "J3001": (180.0, "top", 260.0),
    }
    EDGE_KEEP = 26.0  # panel parts reach this far in from the panel edge
    INSET = 2.0  # pads this far inside the panel edge; the nose overhangs

    def bboxes(fp):
        """((l, t, r, b) of the footprint incl. courtyard, (l, t, r, b) of its pads), in mm."""
        c = fp.GetBoundingBox(False, False)
        cb = (
            c.GetLeft() / 1e6,
            c.GetTop() / 1e6,
            c.GetRight() / 1e6,
            c.GetBottom() / 1e6,
        )
        pb = None
        for pad in fp.Pads():
            b = pad.GetBoundingBox()
            q = (
                b.GetLeft() / 1e6,
                b.GetTop() / 1e6,
                b.GetRight() / 1e6,
                b.GetBottom() / 1e6,
            )
            pb = (
                q
                if pb is None
                else (
                    min(pb[0], q[0]),
                    min(pb[1], q[1]),
                    max(pb[2], q[2]),
                    max(pb[3], q[3]),
                )
            )
        return cb, pb

    def orient_nose(fp, want):
        """Rotate so the side where the courtyard overhangs the pads most faces `want` ('top'/'bottom')."""
        best = None
        for ang in (0, 90, 180, 270):
            fp.SetOrientationDegrees(ang)
            c, pd = bboxes(fp)
            over = {
                "left": pd[0] - c[0],
                "right": c[2] - pd[2],
                "top": pd[1] - c[1],
                "bottom": c[3] - pd[3],
            }
            if best is None or over[want] > best[0]:
                best = (over[want], ang)
        fp.SetOrientationDegrees(best[1])

    def place_edge(fp, x, edge_y, side):
        orient_nose(fp, side)
        c, pd = bboxes(fp)
        cx = (c[0] + c[2]) / 2
        pos = fp.GetPosition()
        dx = x - cx
        dy = (edge_y + INSET) - pd[1] if side == "top" else (edge_y - INSET) - pd[3]
        fp.SetPosition(pcbnew.VECTOR2I(pos.x + mm(dx), pos.y + mm(dy)))

    placed, gridded, unknown = 0, 0, []
    grid = {}  # (board, sheet) -> [fp]
    for fp in fps:
        ref = fp.GetReference()
        sheet = fp.GetSheetname()
        top = sheet.strip("/").split("/")[0] if sheet else ""
        if top not in BOARDS:
            unknown.append((ref, sheet))
            continue
        y0, y1 = BOARDS[top]
        if ref in fx:
            place_edge(fp, fx[ref], y0, "top")
            placed += 1
        elif ref in rx:
            place_edge(fp, rx[ref], y1, "bottom")
            placed += 1
        elif ref in INNER:
            ey, side, x = INNER[ref]
            fp.SetOrientationDegrees(90)  # long axis along the edge
            c, _pd = bboxes(fp)
            cx = (c[0] + c[2]) / 2
            pos = fp.GetPosition()
            dy = (ey + 1.5) - c[1] if side == "top" else (ey - 1.5) - c[3]
            fp.SetPosition(pcbnew.VECTOR2I(pos.x + mm(x - cx), pos.y + mm(dy)))
            placed += 1
        else:
            if fp.GetPosition() == pcbnew.VECTOR2I(0, 0) or args.all:
                grid.setdefault((top, sheet), []).append(fp)
    # pack the rest row-major across the whole board, sub-sheet by sub-sheet, clear of the edge parts
    region = {
        "Front Board": (EDGE_KEEP, 50.0 - 14.0),
        "Control Board": (50.0 + 16.0, 180.0 - 16.0),
        "Rear Board": (180.0 + 14.0, 250.0 - EDGE_KEEP),
    }
    by_board = {}
    for (top, sheet), items in grid.items():
        by_board.setdefault(top, []).extend((sheet, fp) for fp in items)
    for top, items in by_board.items():
        ya, yb = region[top]
        x, y, rowh = 12.0, ya, 0.0
        for _sheet, fp in sorted(items, key=lambda s: (s[0], s[1].GetReference())):
            fp.SetOrientationDegrees(0)
            c, _pd = bboxes(fp)
            w, h = c[2] - c[0] + 1.0, c[3] - c[1] + 1.0
            if x + w > W - 12.0:
                x, y, rowh = 12.0, y + rowh, 0.0
            pos = fp.GetPosition()
            fp.SetPosition(pcbnew.VECTOR2I(pos.x + mm(x - c[0]), pos.y + mm(y - c[1])))
            x += w
            rowh = max(rowh, h)
            gridded += 1
        if y + rowh > yb:
            print(
                f"warning: {top} starting spread runs {y + rowh - yb:.0f} mm past its region"
            )
    pcbnew.SaveBoard(PCB, board)
    print(f"panel parts placed: {placed}; gridded: {gridded}; footprints: {len(fps)}")
    if unknown:
        print("no board for:", unknown)
    return 0


if __name__ == "__main__":
    sys.exit(main())
