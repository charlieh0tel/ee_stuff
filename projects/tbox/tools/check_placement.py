#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = []
# ///
"""Every footprint sits on the board its sheet says, and no net spans boards
except through a ribbon connector.

The panel holds three boards side by side; a part placed across a V-score
lands on the wrong board when the panel is snapped, and any net that then
crosses a score without a ribbon connector on each side is a broken wire.
`check_boards.py` proves this at the schematic level; this proves it on the
placed PCB.

Usage:
    tools/check_placement.py
Exit status 1 if anything is reported.
"""

import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.join(os.path.dirname(HERE), "kicad", "tbox.kicad_pcb")
BOARDS = {
    "Front Board": (0.0, 50.0),
    "Control Board": (50.0, 180.0),
    "Rear Board": (180.0, 270.0),
}
POWER = {"GND", "+9V", "VREF", "RAW_13V8", "BIAS_5V", "CHASSIS"}


def main():
    try:
        import pcbnew
    except ImportError:
        sys.exit(subprocess.call(["/usr/bin/python3", __file__] + sys.argv[1:]))
    import pcbnew

    board = pcbnew.LoadBoard(PCB)
    problems = []
    board_at = {}  # ref -> board the footprint physically sits on

    def band_of(y):
        return next((b for b, (lo, hi) in BOARDS.items() if lo <= y < hi), None)

    ribbons = {}  # ref -> cable name, for the ribbon connectors
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        want = fp.GetSheetname().strip("/").split("/")[0]
        if want not in BOARDS:
            continue
        if fp.HasField("Interconnect"):
            ribbons[ref] = fp.GetFieldText("Interconnect")
        c = fp.GetBoundingBox(False, False)
        top, bottom = c.GetTop() / 1e6, c.GetBottom() / 1e6
        lo, hi = BOARDS[want]
        board_at[ref] = band_of(fp.GetPosition().y / 1e6)
        # a jack nose may overhang the outer panel edge; only the V-scores count
        lo, hi = (lo if lo > 0 else -1e9), (hi if hi < 270 else 1e9)
        if top < lo or bottom > hi:
            problems.append(
                f"{ref}: on {want} in the schematic but its courtyard spans "
                f"y {top:.1f}..{bottom:.1f} mm (board is {lo:g}..{hi:g})"
            )
    nets = {}
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            n = pad.GetNetname()
            if n and not n.startswith("unconnected") and n.split("/")[-1] not in POWER:
                nets.setdefault(n, set()).add(fp.GetReference())
    for n, refs in sorted(nets.items()):
        boards = {board_at[r] for r in refs if r in board_at}
        if len(boards) < 2:
            continue
        # every board the net touches needs its own ribbon connector on the
        # net, and each cable must be present at both of its ends
        cables = {}
        for r in refs & ribbons.keys():
            cables.setdefault(ribbons[r], set()).add(board_at[r])
        reached = {b for bs in cables.values() if len(bs) == 2 for b in bs}
        if not boards <= reached:
            problems.append(
                f"net {n} spans {sorted(boards)} but ribbons reach only "
                f"{sorted(reached)}: {sorted(refs)}"
            )
    for p in problems:
        print(p)
    print(
        f"{len(problems)} problem(s)."
        if problems
        else "OK: every part on its board; no net crosses a score without a ribbon."
    )
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
