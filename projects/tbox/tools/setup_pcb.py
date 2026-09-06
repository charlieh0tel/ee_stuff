#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = []
# ///
"""Create (or refresh the frame of) kicad/tbox.kicad_pcb: the snap-apart panel.

One 300 x 270 mm outline holding the three boards edge to edge, split by
two V-score lines on the "V-CUT" user layer (fabs want them off
Edge.Cuts so the outline stays one closed shape) -- every board is a
rectangle, so no tabs or rails:

    y   0 .. 50    FRONT board   (jack edge = panel top edge)
    y  50 .. 180   CONTROL board (sloped under the top panel)
    y 180 .. 270   REAR board    (jack edge = panel bottom edge)

Also sets the 4-layer stack-up (signal / GND / GND / signal, 1.6 mm), the
default design rules, and labels each board.  Everything the script draws
lives in a group named "panel-frame" and is replaced on every run, so it
is safe to re-run after footprints and tracks exist.  Net classes are in
the project file and are written by --netclasses.

Usage:
    tools/setup_pcb.py                # create or refresh the frame
    tools/setup_pcb.py --netclasses   # also (re)write net classes into tbox.kicad_pro
Needs KiCad's pcbnew Python module (uses the system python3, hence the
`sys.executable` re-exec below when run through uv).
"""

import argparse
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
KI = os.path.join(os.path.dirname(HERE), "kicad")
PCB = os.path.join(KI, "tbox.kicad_pcb")
PRO = os.path.join(KI, "tbox.kicad_pro")

W = 300.0
BOARDS = [("FRONT", 0.0, 50.0), ("CONTROL", 50.0, 180.0), ("REAR", 180.0, 270.0)]
GROUP = "panel-frame"

# Every class needs wire_width/bus_width/line_style: a class without them
# gives schematic wires a width of 0, which collapses their bounding boxes and
# makes eeschema's load-time cleanup drop T-junctions and merge wires (found
# the hard way -- see CLAUDE.md).  Patterns live in net_settings.netclass_patterns.
NETCLASSES = [
    {
        "name": "Default",
        "clearance": 0.2,
        "track_width": 0.25,
        "via_diameter": 0.6,
        "via_drill": 0.3,
        "wire_width": 6,
        "bus_width": 12,
        "line_style": 0,
        "pcb_color": "rgba(0, 0, 0, 0.000)",
        "schematic_color": "rgba(0, 0, 0, 0.000)",
    },
    {
        "name": "Power",
        "clearance": 0.25,
        "track_width": 0.5,
        "via_diameter": 0.8,
        "via_drill": 0.4,
        "wire_width": 6,
        "bus_width": 12,
        "line_style": 0,
        "pcb_color": "rgba(255, 128, 0, 0.400)",
        "schematic_color": "rgba(0, 0, 0, 0.000)",
    },
    {
        "name": "Phones",
        "clearance": 0.2,
        "track_width": 0.4,
        "via_diameter": 0.8,
        "via_drill": 0.4,
        "wire_width": 6,
        "bus_width": 12,
        "line_style": 0,
        "pcb_color": "rgba(0, 160, 255, 0.400)",
        "schematic_color": "rgba(0, 0, 0, 0.000)",
    },
]
NETCLASS_PATTERNS = [
    {"netclass": "Power", "pattern": p}
    for p in ("+9V", "RAW_13V8", "GND", "BIAS_5V", "VREF")
] + [{"netclass": "Phones", "pattern": "/PH_*"}]


def mm(v):
    return round(v * 1_000_000)


def frame(board, pcbnew):
    # drop the previous frame
    for g in list(board.Groups()):
        if g.GetName() == GROUP:
            for item in list(g.GetItems()):
                board.Remove(item)
            board.Remove(g)
    g = pcbnew.PCB_GROUP(board)
    g.SetName(GROUP)
    board.Add(g)

    def add(item):
        board.Add(item)
        g.AddItem(item)

    def line(x1, y1, x2, y2, layer, width=0.1):
        s = pcbnew.PCB_SHAPE(board)
        s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(pcbnew.VECTOR2I(mm(x1), mm(y1)))
        s.SetEnd(pcbnew.VECTOR2I(mm(x2), mm(y2)))
        s.SetLayer(layer)
        s.SetWidth(mm(width))
        add(s)

    def text(s, x, y, layer, size=3.0, thick=0.4):
        t = pcbnew.PCB_TEXT(board)
        t.SetText(s)
        t.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
        t.SetLayer(layer)
        t.SetTextSize(pcbnew.VECTOR2I(mm(size), mm(size)))
        t.SetTextThickness(mm(thick))
        add(t)

    H = BOARDS[-1][2]
    E = pcbnew.Edge_Cuts
    V = (
        pcbnew.User_1
    )  # named "V-CUT" below; the outline itself must stay one closed shape
    line(0, 0, W, 0, E)
    line(W, 0, W, H, E)
    line(W, H, 0, H, E)
    line(0, H, 0, 0, E)
    for name, y0, y1 in BOARDS:
        if y0 > 0:  # V-score between boards, full width, on the V-CUT layer
            line(-5, y0, W + 5, y0, V, 0.2)
            text(f"V-CUT y={y0:g}", W / 2, y0 - 2.5, V, 2.0, 0.3)
        text(
            f"TBOX {name} BOARD  rev 0.2  ({W:g} x {y1 - y0:g})",
            W / 2,
            (y0 + y1) / 2,
            pcbnew.Cmts_User,
            4.0,
            0.6,
        )
        text(
            "panel edge / jacks" if name != "CONTROL" else "top panel above",
            W / 2,
            y0 + 6 if name == "FRONT" else y1 - 6,
            pcbnew.Cmts_User,
            2.0,
            0.3,
        )
    text(
        "TBox panel: 300 x 270, 4-layer 1.6 mm, two V-scores; snap apart into FRONT / CONTROL / REAR",
        6,
        -4,
        pcbnew.Cmts_User,
        2.5,
        0.35,
    )


def stackup(board, pcbnew):
    ds = board.GetDesignSettings()
    ds.SetCopperLayerCount(4)
    board.SetLayerName(pcbnew.In1_Cu, "GND1")
    board.SetLayerName(pcbnew.In2_Cu, "GND2")
    board.SetLayerName(pcbnew.User_1, "V-CUT")
    ds.m_MinClearance = mm(0.15)
    ds.m_TrackMinWidth = mm(0.15)
    ds.m_ViasMinSize = mm(0.5)
    ds.m_MinThroughDrill = mm(0.2)  # the TPS7A4701 thermal-via footprint uses 0.2 mm
    ds.m_CopperEdgeClearance = mm(0.3)
    ds.m_SolderMaskExpansion = mm(0.05)


def netclasses():
    with open(PRO) as f:
        pro = json.load(f)
    ns = pro.setdefault("net_settings", {})
    ns["classes"] = NETCLASSES
    ns["netclass_patterns"] = NETCLASS_PATTERNS
    ns.setdefault("meta", {"version": 5})
    with open(PRO, "w") as f:
        json.dump(pro, f, indent=2)
        f.write("\n")
    print("net classes written:", [c["name"] for c in NETCLASSES])


def main():
    ap = argparse.ArgumentParser(description="Set up the TBox panel PCB.")
    ap.add_argument("--netclasses", action="store_true")
    args = ap.parse_args()
    try:
        import pcbnew
    except ImportError:
        # uv's interpreter has no pcbnew; run under the system python
        sys.exit(subprocess.call(["/usr/bin/python3", __file__] + sys.argv[1:]))
    import pcbnew

    if os.path.exists(PCB):
        board = pcbnew.LoadBoard(PCB)
        created = False
    else:
        board = pcbnew.BOARD()
        created = True
    stackup(board, pcbnew)
    frame(board, pcbnew)
    tb = board.GetTitleBlock()
    tb.SetTitle("TBox — panel: FRONT / CONTROL / REAR")
    tb.SetRevision("0.2")
    tb.SetCompany("TBox")
    board.SetTitleBlock(tb)
    pcbnew.SaveBoard(PCB, board)
    # the page-settings API is not exposed to Python in this build; the file is
    with open(PCB) as f:
        txt = f.read()
    with open(PCB, "w") as f:
        f.write(txt.replace('(paper "A4")', '(paper "A3")', 1))
    print(("created" if created else "refreshed"), PCB)
    if args.netclasses:
        netclasses()
    return 0


if __name__ == "__main__":
    sys.exit(main())
