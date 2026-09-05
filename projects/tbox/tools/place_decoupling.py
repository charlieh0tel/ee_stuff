#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = []
# ///
"""Put every decoupling capacitor on the power pin it serves.

A decoupling cap is any C with one pad on a rail (+9V, BIAS_5V, RAW_13V8)
and the other on GND.  Each is paired with the nearest unclaimed rail pad
of an IC (U*) on the same sub-sheet and rail -- 100n first, then bulk -- and
placed just outside that pad: long axis along the pin's outward normal,
rail pad against the IC, GND pad outward, on the same occupancy grid the
placement tool respects so nothing overlaps.  Rerunnable.

Usage:
    tools/place_decoupling.py
    DEBUG=C2413 tools/place_decoupling.py   # print what blocks each slot
"""

import math
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.join(os.path.dirname(HERE), "kicad", "tbox.kicad_pcb")
RAILS = ("+9V", "BIAS_5V", "RAW_13V8")
W, H = 300.0, 270.0


def main():
    try:
        import pcbnew
    except ImportError:
        sys.exit(subprocess.call(["/usr/bin/python3", __file__] + sys.argv[1:]))
    import pcbnew

    def mm(v):
        return int(round(v * 1_000_000))

    board = pcbnew.LoadBoard(PCB)
    fps = list(board.GetFootprints())

    def bbox(fp):
        c = fp.GetBoundingBox(False, False)
        return (
            c.GetLeft() / 1e6,
            c.GetTop() / 1e6,
            c.GetRight() / 1e6,
            c.GetBottom() / 1e6,
        )

    GAP = 0.4  # clearance kept between courtyard-less bounding boxes
    boxes = {fp.GetReference(): bbox(fp) for fp in fps}
    # each board's y-range: a cap must not cross a V-score
    bands = [(0.0, 50.0), (50.0, 180.0), (180.0, 270.0)]

    def padbox(fp):
        bs = [p.GetBoundingBox() for p in fp.Pads()]
        return (
            min(b.GetLeft() for b in bs) / 1e6,
            min(b.GetTop() for b in bs) / 1e6,
            max(b.GetRight() for b in bs) / 1e6,
            max(b.GetBottom() for b in bs) / 1e6,
        )

    def blockers(nb, skip, host=None):
        """What stops a box going at nb: None if off the board, else refs.

        The host IC counts only by its pads (its silk and courtyard outline
        may be hugged) -- the cap goes right up against the pin."""
        band = next(b for b in bands if b[0] <= (nb[1] + nb[3]) / 2 < b[1])
        if nb[0] < 1 or nb[2] > W - 1 or nb[1] < band[0] + 1 or nb[3] > band[1] - 1:
            return None
        out = []
        for ref, b in boxes.items():
            if ref == skip:
                continue
            gap = GAP
            if ref == host:
                b, gap = padbox(host_fp), 0.3
            if (
                b[0] < nb[2] + gap
                and b[2] > nb[0] - gap
                and b[1] < nb[3] + gap
                and b[3] > nb[1] - gap
            ):
                out.append(ref)
        return out

    def free(nb, skip):
        return blockers(nb, skip) == []

    pinned = set()  # caps this pass has placed: never evicted

    def small(ref):
        b = boxes[ref]
        return (
            ref[0] in "RCDQ"
            and ref not in pinned
            and b[2] - b[0] <= 5.5
            and b[3] - b[1] <= 5.5
        )

    def evict(ref, avoid):
        """Move a small part to the nearest free spot clear of `avoid`."""
        fp = next(f for f in fps if f.GetReference() == ref)
        b = boxes[ref]
        cw, ch = b[2] - b[0], b[3] - b[1]
        cx0, cy0 = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
        for r in [0.5 * i for i in range(2, 40)]:
            for k in range(int(8 * r)):
                a = 2 * math.pi * k / int(8 * r)
                cx, cy = cx0 + r * math.cos(a), cy0 + r * math.sin(a)
                nb = (cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2)
                clear = (
                    nb[0] > avoid[2] + GAP
                    or nb[2] < avoid[0] - GAP
                    or nb[1] > avoid[3] + GAP
                    or nb[3] < avoid[1] - GAP
                )
                if clear and free(nb, ref):
                    pos = fp.GetPosition()
                    fp.SetPosition(
                        pcbnew.VECTOR2I(pos.x + mm(cx - cx0), pos.y + mm(cy - cy0))
                    )
                    boxes[ref] = bbox(fp)
                    return True
        return False

    # a cap serves an IC on its own sub-sheet -- the one it is drawn next to in
    # the schematic; the board-entry bulk caps at the ribbon headers have no IC
    # on their sheet and stay where they are
    sheet_of = {fp.GetReference(): fp.GetSheetname() for fp in fps}
    sch_pos = {}  # ref -> [(x, y) of every unit] in schematic mm
    for fp in fps:
        sf = fp.GetSheetfile()
        if not sf or sf in sch_pos:
            continue
        sch_pos[sf] = None
        with open(os.path.join(os.path.dirname(PCB), sf)) as f:
            for blk in f.read().split("\n\t(symbol\n")[1:]:
                at = re.search(r"\(at ([\d.-]+) ([\d.-]+)", blk)
                ref = re.search(r'\(property "Reference" "([^"]+)"', blk)
                if at and ref:
                    sch_pos.setdefault(ref.group(1), []).append(
                        (float(at.group(1)), float(at.group(2)))
                    )

    def sch_dist(a, b):
        return min(
            math.hypot(x1 - x2, y1 - y2)
            for x1, y1 in sch_pos.get(a, [(0, 0)])
            for x2, y2 in sch_pos.get(b, [(1e6, 1e6)])
        )

    def value_rank(fp):
        v = fp.GetValue().lower()
        m = re.match(r"([\d.]+)\s*([pnu])", v)
        if not m:
            return 9e9
        return float(m.group(1)) * {"p": 1e-12, "n": 1e-9, "u": 1e-6}[m.group(2)]

    caps, targets = [], []
    for fp in fps:
        ref = fp.GetReference()
        pads = list(fp.Pads())
        nets = [p.GetNetname() for p in pads]
        if (
            ref.startswith("C")
            and len(pads) == 2
            and "GND" in nets
            and any(n in RAILS for n in nets)
        ):
            caps.append(fp)
        elif ref.startswith("U"):
            for p in pads:
                if p.GetNetname() in RAILS:
                    targets.append((fp, p))
    caps.sort(key=value_rank)
    claimed = {}  # (ref, pad, bulk?) -> count

    def rail_of(cap):
        return next(p.GetNetname() for p in cap.Pads() if p.GetNetname() in RAILS)

    def load(fp):
        # max of a "typ" or "typ/max" Load_mA field
        m = re.findall(
            r"[\d.]+",
            fp.GetFieldText("Load_mA") if fp.HasField("Load_mA") else "",
        )
        return max(map(float, m)) if m else 0.0

    log = []
    host_fp = None

    def try_side(cap, ic, pad, nx, ny, rail, bulk, push, reach):
        nonlocal host_fp
        host_fp = ic
        pp = pad.GetPosition()
        for rot in (0, 180) if nx else (90, 270):
            cap.SetOrientationDegrees(rot)
            # the rail pad faces the IC (for a bulk cap on another side, either way)
            rail_pad = next(p for p in cap.Pads() if p.GetNetname() == rail)
            rp, cc = rail_pad.GetPosition(), cap.GetPosition()
            if (rp.x - cc.x) * (-nx) + (rp.y - cc.y) * (-ny) <= 0 and not bulk:
                continue
            b = bbox(cap)
            cw, ch = b[2] - b[0], b[3] - b[1]
            half = (cw if nx else ch) / 2
            slots = [
                (0.3 + 0.4 * i, 0.5 * j) for i in range(20) for j in range(-24, 25)
            ]
            for dist, lat in sorted(slots, key=lambda s: math.hypot(s[0], s[1])):
                if math.hypot(dist, lat) <= reach:
                    cx = pp.x / 1e6 + nx * (half + dist) + ny * lat
                    cy = pp.y / 1e6 + ny * (half + dist) + nx * lat
                    nb = (cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2)
                    bl = blockers(nb, cap.GetReference(), ic.GetReference())
                    if os.environ.get("DEBUG") == cap.GetReference():
                        print(nx, ny, dist, lat, bl)
                    if (
                        bl
                        and push
                        and dist <= 1.2
                        and abs(lat) <= 2
                        and all(map(small, bl))
                    ):
                        # a decoupling cap outranks a stray resistor: shove it aside
                        for ref in bl:
                            evict(ref, nb)
                        bl = blockers(nb, cap.GetReference(), ic.GetReference())
                        if bl:
                            log.append(
                                f"  ({cap.GetReference()}: could not clear {bl})"
                            )
                    if bl == []:
                        dx = cx - (b[0] + b[2]) / 2
                        dy = cy - (b[1] + b[3]) / 2
                        cap.SetPosition(pcbnew.VECTOR2I(cc.x + mm(dx), cc.y + mm(dy)))
                        return True
        return False

    placed = 0
    for cap in caps:
        rail = rail_of(cap)
        bulk = value_rank(cap) >= 1e-6
        cands = []
        for ic, pad in targets:
            if (
                pad.GetNetname() != rail
                or sheet_of[ic.GetReference()] != sheet_of[cap.GetReference()]
            ):
                continue
            key = (ic.GetReference(), pad.GetNumber(), bulk)
            # every IC gets its own 100n before any gets a second; bulk caps
            # go to the hungriest ICs first; ties by where it is drawn
            cands.append(
                (
                    claimed.get(key, 0),
                    -load(ic)
                    if bulk
                    else sch_dist(cap.GetReference(), ic.GetReference()),
                    ic,
                    pad,
                )
            )
        if not cands:
            log.append(
                f"  {cap.GetReference():6} {cap.GetValue():8} no IC on its sheet; left alone"
            )
            continue
        cands.sort(key=lambda c: (c[0], c[1]))
        orig_rot = cap.GetOrientationDegrees()
        done = None
        for _n, _d, ic, pad in cands[:4]:
            # outward normal from the IC centre through the pad; a bulk cap may
            # sit on any side of the IC (nearest the pad first)
            ic_c, pp = ic.GetPosition(), pad.GetPosition()
            dx, dy = pp.x - ic_c.x, pp.y - ic_c.y
            first = (
                (1.0 if dx > 0 else -1.0, 0.0)
                if abs(dx) >= abs(dy)
                else (0.0, 1.0 if dy > 0 else -1.0)
            )
            sides = [first] + [
                n for n in ((1, 0), (-1, 0), (0, 1), (0, -1)) if n != first
            ]
            # close on the pin's own side, then close on any side, then wherever
            for reach, allowed in ((4.0, sides[:1]), (4.0, sides[1:]), (99, sides)):
                for nx, ny in allowed:
                    if try_side(
                        cap,
                        ic,
                        pad,
                        nx,
                        ny,
                        rail,
                        bulk,
                        push=(nx, ny) == first and not bulk,
                        reach=reach,
                    ):
                        done = (ic, pad)
                        break
                if done:
                    break
            if done:
                break
        if not done:
            cap.SetOrientationDegrees(orig_rot)
            log.append(
                f"  could not fit {cap.GetReference()} ({cap.GetValue()}) near {cands[0][2].GetReference()}"
            )
            continue
        boxes[cap.GetReference()] = bbox(cap)
        pinned.add(cap.GetReference())
        ic, pad = done
        key = (ic.GetReference(), pad.GetNumber(), bulk)
        claimed[key] = claimed.get(key, 0) + 1
        placed += 1
        note = (
            "" if ic is cands[0][2] else f"   (no room at {cands[0][2].GetReference()})"
        )
        log.append(
            f"  {cap.GetReference():6} {cap.GetValue():8} -> {ic.GetReference()}.{pad.GetNumber()} ({rail}){note}"
        )
    pcbnew.SaveBoard(PCB, board)
    print("\n".join(log))
    print(f"decoupling caps placed: {placed} of {len(caps)} candidates")
    return 0


if __name__ == "__main__":
    sys.exit(main())
