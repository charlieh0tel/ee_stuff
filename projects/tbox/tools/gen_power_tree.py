#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = []
# ///
"""Regenerate the Power Tree sheet and the Supply-sheet load notes.

Topology and loads are read from the schematic (netlist), capability from
power_tree.json -- see power_model.py.  Run after any change to a Load_mA
field, a converter, or the json.

Outputs:
  - kicad/powertree.kicad_sch : boxes-and-arrows tree, left-to-right,
    wrapping to a new band if it outgrows the sheet width
  - kicad/supply.kicad_sch    : per-stage load annotations (near stages)

Managed elements are tracked by UUID in kicad/power_tree_gen.json and
replaced wholesale on each run; hand-drawn content is left untouched.
The Power Tree sheet must already exist in the root hierarchy.
"""

import argparse
import json
import os
import uuid

from power_model import KI, SRC, PowerTree, export_netlist, fmt_ma, parse_netlist

STATE = os.path.join(KI, "power_tree_gen.json")
TREE_SCH = os.path.join(KI, "powertree.kicad_sch")
SUPPLY_SCH = os.path.join(KI, "supply.kicad_sch")

G = 1.27


def pt(n):
    return round(n * G, 4)


# Deterministic element UUIDs derived from (scope, sequence index): an
# unchanged power_tree.json regenerates byte-identical output (zero diff),
# and a small content edit only churns the lines that actually changed.
NS = uuid.UUID("b7e5d1a2-0c3f-4e6a-9b8c-1d2e3f4a5b6c")


# layout (grid units); A4 landscape drawable ~ x 12..220, y 12..150
X0, Y0 = 10, 16
BOX_MIN, BOX_MAX = 30, 80  # box width follows the longest line
CHAR_W = 0.9  # grid units per character at 1.27 mm
COL_GAP = 8
LINE = 2.2
PAD = 1.2
ROW_GAP = 4
X_MAX = 222  # wrap when a column would start past this
BAND_GAP = 6


def strip_managed(sch, old):
    out, i = [], 0
    while i < len(sch):
        j = sch.find('(uuid "', i)
        if j == -1:
            out.append(sch[i:])
            break
        k = max(sch.rfind("\n  (", i, j), sch.rfind("\n\t(", i, j))
        if k == -1:
            out.append(sch[i : j + 7])
            i = j + 7
            continue
        uid = sch[j + 7 : sch.find('"', j + 7)]
        depth = 0
        e = k + 1
        for e in range(k + 1, len(sch)):
            if sch[e] == "(":
                depth += 1
            elif sch[e] == ")":
                depth -= 1
                if depth == 0:
                    break
        kind = sch[k + 1 : e + 1].split("(", 2)[1].split()[0]
        if uid in old and kind in ("rectangle", "polyline", "text"):
            out.append(sch[i:k])
            i = e + 1
        else:
            out.append(sch[i : e + 1])
            i = e + 1
    return "".join(out)


class Emit:
    def __init__(self, scope):
        self.scope = scope
        self.items, self.uuids = [], []

    def _uid(self):
        return str(uuid.uuid5(NS, f"{self.scope}:{len(self.uuids)}"))

    def rect(self, x1, y1, x2, y2):
        u = self._uid()
        self.uuids.append(u)
        self.items.append(
            f"  (rectangle (start {pt(x1)} {pt(y1)}) (end {pt(x2)} {pt(y2)})"
            f' (stroke (width 0.1524) (type solid)) (fill (type none)) (uuid "{u}"))'
        )

    def line(self, pts_):
        u = self._uid()
        self.uuids.append(u)
        coords = " ".join(f"(xy {pt(x)} {pt(y)})" for x, y in pts_)
        self.items.append(
            f"  (polyline (pts {coords}) (stroke (width 0.1524) (type solid))"
            f' (uuid "{u}"))'
        )

    def text(self, t, x, y, size=1.27, bold=False):
        u = self._uid()
        self.uuids.append(u)
        b = " (bold yes)" if bold else ""
        t = t.replace('"', "'")
        self.items.append(
            f'  (text "{t}" (exclude_from_sim no) (at {pt(x)} {pt(y)} 0)'
            f" (effects (font (size {size} {size}){b}) (justify left bottom))"
            f' (uuid "{u}"))'
        )


def load_line(tree, name):
    tt, tm = tree.total(name)
    dt, dm = tree.direct_sum(name)
    s = f"load: {fmt_ma(tt)} typ / {fmt_ma(tm)} max mA"
    if tree.children.get(name):
        s += f" (direct {fmt_ma(dt)}/{fmt_ma(dm)} + downstream)"
    return s


def node_lines(name, tree):
    src = tree.src
    inp = src["input"]
    if name == inp["name"]:
        lines = [f"{inp['name']}  {inp['desc']}", inp["protection"]]
        if inp.get("note"):
            lines.append(inp["note"])
        return lines
    n = tree.nodes[name]
    hdr = n["name"]
    if tree.converter_label(name):
        hdr += "  <- " + tree.converter_label(name)
    lines = [hdr]
    if n.get("desc"):
        lines.append(n["desc"])
    lines.append(load_line(tree, name))
    if n.get("max_ma"):
        basis = f" ({n['max_basis']})" if n.get("max_basis") else ""
        lines.append(f"max: {n['max_ma']} mA{basis}")
    if n.get("note"):
        lines.append(n["note"])
    if n.get("no_loads"):
        lines.append(f"  {n['no_loads']}")
    for sheet, refs, t, m in tree.by_sheet(name):
        shown = " ".join(refs[:4]) + (f" +{len(refs) - 4}" if len(refs) > 4 else "")
        lines.append(f"  - {sheet}: {shown} = {fmt_ma(t)}/{fmt_ma(m)}")
    return lines


def main():
    ap = argparse.ArgumentParser(description="Regenerate the TBox power tree.")
    ap.add_argument("--netlist", help="use this netlist instead of exporting")
    args = ap.parse_args()
    with open(SRC) as f:
        src = json.load(f)
    with open(args.netlist or export_netlist()) as f:
        tree = PowerTree(src, *parse_netlist(f.read()))
    for w in tree.warnings:
        print(f"warning: {w}")
    children = {src["input"]["name"]: [tree.root]}
    children.update(tree.children)
    inp_name = src["input"]["name"]

    e = Emit("powertree")
    e.text(
        "POWER TREE  (generated: topology + loads from the schematic, capability from power_tree.json -- do not hand-edit)",
        X0,
        Y0 - 2,
        size=1.778,
        bold=True,
    )

    # left-to-right layout: recursive; each node placed at (x, y); children in
    # the next column, stacked; a subtree that would start past X_MAX wraps to
    # a new band below everything placed so far.
    band_bottom = [Y0]

    def place(name, x, y):
        """Place node and subtree; returns (bottom_y_of_subtree, box_geom)."""
        lines = node_lines(name, tree)
        w = max(BOX_MIN, min(BOX_MAX, 2 * PAD + CHAR_W * max(map(len, lines))))
        if x > X_MAX - w:
            # wrap: new band at left margin, below everything so far
            y = band_bottom[0] + BAND_GAP
            x = X0
        h = 2 * PAD + LINE * len(lines)
        e.rect(x, y, x + w, y + h)
        ty = y + PAD + LINE * 0.85
        for i, ln in enumerate(lines):
            e.text(ln, x + PAD, ty + LINE * i, bold=(i == 0))
        band_bottom[0] = max(band_bottom[0], y + h)
        geom = (x, y, x + w, y + h)
        cy = y
        sub_bottom = y + h
        for c in children.get(name, []):
            cb, cgeom = place(c, x + w + COL_GAP, cy)
            # arrow: parent right edge -> child left edge
            pcy = (geom[1] + geom[3]) / 2
            kcy = (cgeom[1] + cgeom[3]) / 2
            midx = (geom[2] + cgeom[0]) / 2
            if cgeom[0] > geom[2]:  # same band, child to the right
                e.line([(geom[2], pcy), (midx, pcy), (midx, kcy), (cgeom[0], kcy)])
                e.line(
                    [
                        (cgeom[0] - 1.6, kcy - 0.8),
                        (cgeom[0], kcy),
                        (cgeom[0] - 1.6, kcy + 0.8),
                    ]
                )
            else:  # wrapped band: drop from parent bottom
                e.line(
                    [
                        ((geom[0] + geom[2]) / 2, geom[3]),
                        ((geom[0] + geom[2]) / 2, cgeom[1] - 2),
                        (cgeom[0] - 2, cgeom[1] - 2),
                        (cgeom[0] - 2, kcy),
                        (cgeom[0], kcy),
                    ]
                )
                e.line(
                    [
                        (cgeom[0] - 1.6, kcy - 0.8),
                        (cgeom[0], kcy),
                        (cgeom[0] - 1.6, kcy + 0.8),
                    ]
                )
            cy = cb + ROW_GAP
            sub_bottom = max(sub_bottom, cb)
        return sub_bottom, geom

    place(inp_name, X0, Y0)

    # per-stage annotations on the supply sheet
    s_notes = Emit("supply")
    for n in src["nodes"]:
        if n.get("sch_note_at"):
            x, yy = n["sch_note_at"]
            if n.get("no_loads"):
                note = [n["sch_note"]] if n.get("sch_note") else []
            else:
                note = [load_line(tree, n["name"])] + (
                    n["sch_note"].split("\n") if n.get("sch_note") else []
                )
            for i, ln in enumerate(reversed(note)):
                s_notes.text(ln, x, yy - 2 * i)

    # ---- apply to files, replacing previously managed elements ----
    old = set()
    if os.path.exists(STATE):
        with open(STATE) as f:
            st = json.load(f)
        old = set(st.get("uuids", []) + st.get("supply", []) + st.get("powertree", []))

    for path, emit in ((TREE_SCH, e), (SUPPLY_SCH, s_notes)):
        with open(path) as f:
            sch = strip_managed(f.read(), old)
        tail = sch.rstrip()
        assert tail.endswith(")")
        sch = tail[:-1] + "\n".join(emit.items) + "\n)\n"
        with open(path, "w") as f:
            f.write(sch)

    with open(STATE, "w") as f:
        json.dump({"powertree": e.uuids, "supply": s_notes.uuids}, f, indent=0)
    print(
        f"power tree: {len(e.items)} elements -> powertree.kicad_sch; "
        f"{len(s_notes.items)} notes -> supply.kicad_sch"
    )


if __name__ == "__main__":
    main()
