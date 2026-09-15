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

import math
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


JACK_REACH = (
    25.0  # mm, ESD array to the jack it clamps (a 1/4" jack body alone is ~20 mm deep)
)


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
        b = next((b for b, (lo, hi) in BOARDS.items() if lo <= y < hi), None)
        if b is None:
            # a panel part is placed by its mechanical axis, so its origin can
            # land exactly on the outer board edge
            b = next(
                (b for b, (lo, hi) in BOARDS.items() if lo - 0.01 <= y <= hi + 0.01),
                None,
            )
        return b

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
        boards = {board_at[r] for r in refs if board_at.get(r)}
        stray = sorted(r for r in refs if r in board_at and board_at[r] is None)
        if stray:
            problems.append(f"net {n}: {stray} sit outside every board band")
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
    # an ESD array must sit at the jack it protects: within JACK_REACH of a
    # jack footprint sharing one of its input nets
    fps = {fp.GetReference(): fp for fp in board.GetFootprints()}
    for ref, fp in fps.items():
        if fp.GetValue() != "SP724":
            continue
        # the jack may be one series passive (bead, resistor) upstream
        reach = set()
        for pad in fp.Pads():
            reach.add(pad.GetNetname())
            for r in nets.get(pad.GetNetname(), ()):
                if len(fps[r].Pads()) == 2:
                    reach.update(p.GetNetname() for p in fps[r].Pads())
        jacks = {
            r
            for n in reach
            for r in nets.get(n, ())
            if "Jack" in str(fps[r].GetFPID().GetLibItemName())
        }
        if not jacks:
            problems.append(f"{ref}: SP724 with no jack on any of its input nets")
            continue
        d = min(
            math.hypot(
                (fp.GetPosition().x - fps[j].GetPosition().x) / 1e6,
                (fp.GetPosition().y - fps[j].GetPosition().y) / 1e6,
            )
            for j in jacks
        )
        if d > JACK_REACH:
            problems.append(
                f"{ref}: SP724 is {d:.1f} mm from its nearest jack "
                f"({sorted(jacks)}), limit {JACK_REACH:g}"
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
