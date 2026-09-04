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
  - Top-panel parts (pots, buttons, override toggle, LEDs) get their
    positions from panel-top.svg: the control board lies 10 mm inside
    each end of the 150 mm slope, drawn with the rear at y=0, so
    x_pcb = 300 - x_panel and y_pcb = 190 - y_panel.
  - Everything else is clustered by sub-sheet around a hand-chosen anchor
    (near the panel parts it serves), placed nearest-first by netlist
    distance from the cluster's anchored parts, on a 1 mm occupancy grid
    that keeps clusters from overlapping each other or the edge zones.
    A rough but purposeful start for hand layout; --all re-places parts
    that were already moved.

Usage:
    tools/place_panel.py [--all]
"""

import argparse
import math
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
# top panel: (x_panel, y_panel) of each control-board panel part, from panel-top.svg (operator's view, rear at y=0)
TOP = {
    "RV2201": (70, 32),
    "RV2402": (70, 65),
    "RV2401": (70, 100),
    "SW2104": (70, 131.5),
    "D2108": (86, 131),
    "RV2202": (230, 32),
    "RV2403": (230, 65),
    "RV2404": (230, 100),
    "SW2105": (230, 131.5),
    "D2117": (214, 131),
    "SW2101": (30, 131.5),
    "D2102": (46, 131),
    "SW2102": (270, 131.5),
    "D2107": (254, 131),
    "SW2201": (150, 131.5),
    "D2201": (169, 131),
    "SW2103": (150, 72.67),
    "D2101": (150, 24),
    "D2118": (288, 12),
}
# cluster anchors (board x, y) for the free parts of each sub-sheet
ANCHOR = {
    "Front Board/Preamp A": (247, 30),
    "Front Board/Preamp B": (53, 30),
    "Front Board": (150, 36),
    "Control Board/Keying Logic": (150, 74),
    "Control Board/TX Sum / Intercom": (110, 128),
    "Control Board/Monitor / Phones": (195, 112),
    "Control Board/Supply": (150, 160),
    "Control Board": (100, 66),
    "Rear Board/Rear I/O": (96, 222),
    "Rear Board/Rig Out": (175, 214),
    "Rear Board/RX In": (140, 234),
    "Rear Board": (260, 190),
}
COHESION = 0.15  # weight of the cluster anchor vs. the connection centroid in refinement
POWER_NETS = ("GND", "+9V", "VREF", "RAW_13V8", "BIAS_5V", "CHASSIS")


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
    ap.add_argument(
        "--refine",
        type=int,
        default=4,
        help="connectivity refinement passes (0 = none)",
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
    # ribbon headers along the inner (V-cut) edges, in gaps between the top-panel parts: front/control pair between
    # INTERCOM and MUTE A, control/rear pair right of LEVEL A
    INNER = {
        "J1005": (50.0, "bottom", 188.0),
        "J2001": (50.0, "top", 188.0),
        "J2002": (180.0, "bottom", 275.0),
        "J3001": (180.0, "top", 275.0),
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
    free = {}  # (board, sheet) -> [fp]
    anchored = set()

    def ribbon_header(fp, ref):
        ey, side, x = INNER[ref]
        fp.SetOrientationDegrees(90)  # long axis along the edge
        c, _pd = bboxes(fp)
        cx = (c[0] + c[2]) / 2
        pos = fp.GetPosition()
        dy = (ey + 1.5) - c[1] if side == "top" else (ey - 1.5) - c[3]
        fp.SetPosition(pcbnew.VECTOR2I(pos.x + mm(x - cx), pos.y + mm(dy)))

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
        elif ref in rx:
            place_edge(fp, rx[ref], y1, "bottom")
        elif ref in INNER:
            ribbon_header(fp, ref)
        elif ref in TOP:
            px, py = TOP[ref]
            fp.SetOrientationDegrees(0)
            fp.SetPosition(pcbnew.VECTOR2I(mm(W - px), mm(min(190 - py, y1 - 4.0))))
        else:
            if fp.GetPosition() == pcbnew.VECTOR2I(0, 0) or args.all:
                free.setdefault((top, sheet.strip("/")), []).append(fp)
            continue
        anchored.add(ref)
        placed += 1

    # ---- clustered placement of the free parts on an occupancy grid ----------------------
    import numpy as np

    H = max(y1 for _y0, y1 in BOARDS.values())
    RES = 0.5  # mm per cell
    occ = np.zeros((int(H / RES) + 2, int(W / RES) + 2), dtype=bool)

    def unmark(lf, tp, r, b, margin=0.6):
        x1, y1_, x2, y2 = (
            max(0, lf - margin),
            max(0, tp - margin),
            min(W, r + margin),
            min(H, b + margin),
        )
        occ[int(y1_ / RES) : int(y2 / RES) + 1, int(x1 / RES) : int(x2 / RES) + 1] = (
            False
        )

    def mark(lf, tp, r, b, margin=0.6):
        x1, y1_, x2, y2 = (
            max(0, lf - margin),
            max(0, tp - margin),
            min(W, r + margin),
            min(H, b + margin),
        )
        occ[int(y1_ / RES) : int(y2 / RES) + 1, int(x1 / RES) : int(x2 / RES) + 1] = (
            True
        )

    # forbidden zones: outside each board's free region (edge strips), and the V-cut lines
    keep = {
        "Front Board": (EDGE_KEEP, 50.0 - 2.0),
        "Control Board": (50.0 + 2.0, 180.0 - 2.0),
        "Rear Board": (180.0 + 2.0, 270.0 - EDGE_KEEP),
    }
    occ[:, : int(6 / RES)] = True
    occ[:, int((W - 6) / RES) :] = True
    for top, (y0, y1) in BOARDS.items():
        ya, yb = keep[top]
        occ[int(y0 / RES) : int(ya / RES) + 1, :] = True
        occ[int(yb / RES) : int(y1 / RES) + 1, :] = True
    for fp in fps:
        if fp.GetReference() in anchored:
            c, _pd = bboxes(fp)
            mark(*c)

    # netlist distance from the cluster's anchored parts, through non-power nets
    nets_of = {}
    for fp in fps:
        for pad in fp.Pads():
            n = pad.GetNetname()
            if (
                n
                and not n.startswith("unconnected")
                and not any(n.split("/")[-1] == pn for pn in POWER_NETS)
            ):
                nets_of.setdefault(fp.GetReference(), set()).add(n)
    ref_of_net = {}
    for r, ns in nets_of.items():
        for n in ns:
            ref_of_net.setdefault(n, set()).add(r)

    def bfs_rank(refs, seeds):
        dist = {s: 0 for s in seeds}
        frontier = list(seeds)
        while frontier:
            nxt = []
            for r in frontier:
                for n in nets_of.get(r, ()):
                    for r2 in ref_of_net.get(n, ()):
                        if r2 not in dist:
                            dist[r2] = dist[r] + 1
                            nxt.append(r2)
            frontier = nxt
        return {r: dist.get(r, 99) for r in refs}

    def fits(lf, tp, r, b):
        if lf < 0 or tp < 0 or r > W or b > H:
            return False
        return not occ[
            int(tp / RES) : int(b / RES) + 1, int(lf / RES) : int(r / RES) + 1
        ].any()

    def spiral(ax, ay, w, h, step=1.0, rmax=140):
        """Candidate top-left corners for a w x h box, nearest to (ax, ay) first."""
        yield ax - w / 2, ay - h / 2
        rr = step
        while rr < rmax:
            n = max(8, int(2 * 3.1416 * rr / step))
            for k in range(n):
                a = 2 * 3.1416 * k / n
                yield ax + rr * math.cos(a) - w / 2, ay + rr * math.sin(a) - h / 2
            rr += step

    for (top, sheet), items in sorted(free.items()):
        ax, ay = ANCHOR.get(sheet, ANCHOR[top])
        seeds = [
            r
            for r in anchored
            if any(
                f.GetReference() == r and f.GetSheetname().strip("/") == sheet
                for f in fps
            )
        ]
        rank = bfs_rank([f.GetReference() for f in items], seeds)
        for fp in sorted(
            items,
            key=lambda f: (
                rank[f.GetReference()],
                not f.GetReference().startswith("U"),
                f.GetReference(),
            ),
        ):
            fp.SetOrientationDegrees(0)
            c, _pd = bboxes(fp)
            w, h = c[2] - c[0], c[3] - c[1]
            for cx, cy in spiral(ax, ay, w, h):
                cx, cy = round(cx), round(cy)
                if fits(cx, cy, cx + w, cy + h):
                    pos = fp.GetPosition()
                    fp.SetPosition(
                        pcbnew.VECTOR2I(pos.x + mm(cx - c[0]), pos.y + mm(cy - c[1]))
                    )
                    mark(cx, cy, cx + w, cy + h)
                    gridded += 1
                    break
            else:
                print("could not place", fp.GetReference())

    # ---- refinement: pull each free part toward what it connects to -------------------------
    def signal_pads():
        """net -> [(ref, x, y)] for signal nets (power and unconnected nets excluded)."""
        out = {}
        for fp in fps:
            for pad in fp.Pads():
                n = pad.GetNetname()
                if (
                    not n
                    or n.startswith("unconnected")
                    or n.split("/")[-1] in POWER_NETS
                ):
                    continue
                q = pad.GetPosition()
                out.setdefault(n, []).append((fp.GetReference(), q.x / 1e6, q.y / 1e6))
        return out

    def ratsnest_length():
        total = 0.0
        for n, pads in signal_pads().items():
            cx = sum(x for _r, x, _y in pads) / len(pads)
            cy = sum(y for _r, _x, y in pads) / len(pads)
            total += sum(math.hypot(x - cx, y - cy) for _r, x, y in pads)
        return total

    free_fps = [fp for items in free.values() for fp in items]
    fp_by_ref = {fp.GetReference(): fp for fp in fps}
    boxes = {fp.GetReference(): bboxes(fp)[0] for fp in fps}
    before = ratsnest_length()
    for _pass in range(args.refine):
        sp = signal_pads()
        # connections per part: other parts sharing a signal net
        conn = {}
        for n, pads in sp.items():
            refs = {r for r, _x, _y in pads}
            for r in refs:
                conn.setdefault(r, {}).update(
                    {o: conn.get(r, {}).get(o, 0) + 1 for o in refs if o != r}
                )
        for fp in sorted(free_fps, key=lambda f: -len(conn.get(f.GetReference(), {}))):
            ref = fp.GetReference()
            if not conn.get(ref):
                continue
            # target: centroid of connected parts, weighted by shared nets
            tx = ty = wsum = 0.0
            for o, w in conn[ref].items():
                q = fp_by_ref[o].GetPosition()
                tx += w * q.x / 1e6
                ty += w * q.y / 1e6
                wsum += w
            tx, ty = tx / wsum, ty / wsum
            # keep sub-circuits together: blend with the part's own cluster anchor
            ax_, ay_ = ANCHOR.get(
                fp.GetSheetname().strip("/"),
                ANCHOR[fp.GetSheetname().strip("/").split("/")[0]],
            )
            tx, ty = (
                (1 - COHESION) * tx + COHESION * ax_,
                (1 - COHESION) * ty + COHESION * ay_,
            )
            # lift the part off the grid, then try its orientations nearest the target
            c, _pd = bboxes(fp)
            unmark(*c)
            for o in fps:  # neighbours whose margin the unmark cleared
                if o is fp:
                    continue
                oc = boxes.get(o.GetReference())
                if (
                    oc
                    and oc[0] < c[2] + 1.5
                    and oc[2] > c[0] - 1.5
                    and oc[1] < c[3] + 1.5
                    and oc[3] > c[1] - 1.5
                ):
                    mark(*oc)
            best = None
            for ang in (
                (0, 90) if len(list(fp.Pads())) == 2 else (fp.GetOrientationDegrees(),)
            ):
                fp.SetOrientationDegrees(ang)
                c, _pd = bboxes(fp)
                w, h = c[2] - c[0], c[3] - c[1]
                for cx, cy in spiral(tx, ty, w, h, step=0.5, rmax=60):
                    cx, cy = round(cx * 2) / 2, round(cy * 2) / 2
                    if fits(cx, cy, cx + w, cy + h):
                        d = math.hypot(cx + w / 2 - tx, cy + h / 2 - ty)
                        if best is None or d < best[0]:
                            best = (d, ang, cx, cy, w, h)
                        break
            if best is None:
                c, _pd = bboxes(fp)
                mark(*c)
                continue
            _d, ang, cx, cy, w, h = best
            fp.SetOrientationDegrees(ang)
            c, _pd = bboxes(fp)
            pos = fp.GetPosition()
            fp.SetPosition(
                pcbnew.VECTOR2I(pos.x + mm(cx - c[0]), pos.y + mm(cy - c[1]))
            )
            mark(cx, cy, cx + w, cy + h)
            boxes[ref] = bboxes(fp)[0]
    after = ratsnest_length()
    if args.refine:
        print(
            f"ratsnest star length: {before:.0f} mm -> {after:.0f} mm after {args.refine} pass(es)"
        )

    pcbnew.SaveBoard(PCB, board)
    print(f"panel parts placed: {placed}; gridded: {gridded}; footprints: {len(fps)}")
    if unknown:
        print("no board for:", unknown)
    return 0


if __name__ == "__main__":
    sys.exit(main())
