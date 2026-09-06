#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = []
# ///
"""Every board part must have a footprint that exists.

Reads the exported netlist: each component that is on the board (KiCad's
``on_board`` attribute -- panel-only parts are marked ``on_board no`` in
the schematic and skipped) must carry a non-empty Footprint whose library
is either a stock KiCad library or the project's ``kicad/tbox.pretty`` and
whose file exists.  Power symbols and net ties are checked like anything
else (net ties do have footprints).

Usage:
    tools/check_footprints.py [--netlist x.net]
Exit status 1 if anything is reported.
"""

import argparse
import glob
import os
import re
import sys

from power_model import KI, export_netlist

STOCK = "/usr/share/kicad/footprints"


def main():
    ap = argparse.ArgumentParser(description="Check TBox footprints.")
    ap.add_argument("--netlist")
    args = ap.parse_args()
    with open(args.netlist or export_netlist()) as f:
        text = f.read()
    # on_board is not in the netlist; read it from the sheets
    off_board = set()
    for p in glob.glob(os.path.join(KI, "*.kicad_sch")):
        with open(p) as f:
            t = f.read()
        for m in re.finditer(r'\(property "Reference"\s*"([^"]+)"', t):
            blk_start = t.rfind("(symbol", 0, m.start())
            if re.search(r"\(on_board no\)", t[blk_start : m.start()]):
                off_board.add(m.group(1))
    problems, n = [], 0
    for ref, body in re.findall(
        r'\(comp\s+\(ref\s+"([^"]+)"\)(.*?)(?=\(comp\s+\(ref|\(libparts)',
        text,
        re.DOTALL,
    ):
        if ref in off_board:
            continue
        n += 1
        m = re.search(r'\(footprint\s+"([^"]*)"\)', body)
        fp = m.group(1) if m else ""
        if not fp:
            problems.append(f"{ref}: no footprint")
            continue
        lib, name = fp.split(":", 1) if ":" in fp else ("", fp)
        path = (
            os.path.join(KI, "tbox.pretty", f"{name}.kicad_mod")
            if lib == "tbox"
            else os.path.join(STOCK, f"{lib}.pretty", f"{name}.kicad_mod")
        )
        if not os.path.exists(path):
            problems.append(f"{ref}: footprint {fp!r} not found")
    if problems:
        for p in problems:
            print(p)
        print(f"\n{len(problems)} problem(s).")
        return 1
    print(
        f"OK: {n} board parts have footprints ({len(off_board)} panel-only part(s) skipped: {' '.join(sorted(off_board))})."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
