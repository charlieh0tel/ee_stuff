#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = []
# ///
"""Board-partition checker for the TBox schematic.

The root sheet holds one sheet per PCB (Front Board, Control Board, Rear
Board).  A net that touches parts on more than one board is a ribbon net
and must pass through a ribbon connector on every board it spans; CHASSIS
is the enclosure and is exempt.  Ribbon connectors carry an
``Interconnect`` field naming their cable (e.g. "FC", "CR"); each cable
must have exactly two connectors on different boards, and since the
ribbons are straight-through, pin n must carry the same net at both ends.
Everything is read from the exported netlist.

Usage:
    tools/check_boards.py                 # exports the netlist via kicad-cli
    tools/check_boards.py --netlist x.net
    tools/check_boards.py --pinmap        # also print the ribbon pin maps
Exit status 1 if anything is reported.
"""

import argparse
import re
import sys

from power_model import export_netlist, parse_netlist

EXEMPT = {"CHASSIS"}


def board_of(comp):
    parts = comp["sheet"].strip("/").split("/")
    return parts[0] if parts and parts[0] else "Root"


def main():
    ap = argparse.ArgumentParser(description="Check the TBox board partition.")
    ap.add_argument("--netlist")
    ap.add_argument("--pinmap", action="store_true")
    args = ap.parse_args()
    with open(args.netlist or export_netlist()) as f:
        text = f.read()
    comps, touches = parse_netlist(text)

    # ribbons from the Interconnect field
    cables = {}
    for ref, c in comps.items():
        tag = c["fields"].get("Interconnect")
        if tag:
            cables.setdefault(tag, []).append(ref)
    ribbons = [tuple(sorted(v)) for _k, v in sorted(cables.items())]
    connectors = {r for pair in ribbons for r in pair}
    pin_count = {}

    # net -> {board: [refs]}, and connector pin -> net
    nets = {}
    pin_net = {}
    for ref, seen in touches.items():
        if ref.startswith("#"):
            continue
        b = board_of(comps[ref])
        for net, _pt in seen:
            nets.setdefault(net, {}).setdefault(b, set()).add(ref)
    for net, body in re.findall(
        r'\(net\s+\(code\s+"[^"]*"\)\s+\(name\s+"([^"]*)"\)(.*?)(?=\(net\s+\(code|\Z)',
        text,
        re.DOTALL,
    ):
        for ref, pin in re.findall(
            r'\(node\s+\(ref\s+"([^"]+)"\)\s+\(pin\s+"([^"]+)"\)', body
        ):
            if ref in connectors:
                pin_net[(ref, pin)] = None if net.startswith("unconnected-") else net
                pin_count[ref] = max(pin_count.get(ref, 0), int(pin))

    problems = []
    for tag, refs in sorted(cables.items()):
        if len(refs) != 2:
            problems.append(
                f"cable {tag!r} has {len(refs)} connector(s): {' '.join(sorted(refs))}"
            )
    ribbons = [pair for pair in ribbons if len(pair) == 2]
    for net, boards in sorted(nets.items()):
        if len(boards) < 2 or net in EXEMPT:
            continue
        for b, refs in boards.items():
            if not refs & connectors:
                problems.append(
                    f"{net}: spans {sorted(boards)} but has no ribbon connector on {b} "
                    f"({' '.join(sorted(refs))})"
                )
    for a, b in ribbons:
        for k in range(1, max(pin_count.get(a, 0), pin_count.get(b, 0)) + 1):
            na, nb = pin_net.get((a, str(k))), pin_net.get((b, str(k)))
            if na != nb:
                problems.append(f"{a}.{k} = {na!r} but {b}.{k} = {nb!r}")
        if board_of(comps[a]) == board_of(comps[b]):
            problems.append(f"{a} and {b} are on the same board")

    if args.pinmap:
        for a, b in ribbons:
            print(f"\n{a} ({board_of(comps[a])}) <-> {b} ({board_of(comps[b])})")
            for k in range(1, pin_count.get(a, 0) + 1, 2):
                left = pin_net.get((a, str(k)), "n/c")
                right = pin_net.get((a, str(k + 1)), "n/c")
                print(f"  {k:2}  {left:14}  {k + 1:2}  {right}")

    if problems:
        for p in problems:
            print(p)
        print(f"\n{len(problems)} problem(s).")
        return 1
    boards = sorted({board_of(c) for c in comps.values()})
    crossing = sum(1 for n, b in nets.items() if len(b) > 1 and n not in EXEMPT)
    print(
        f"OK: {len(boards)} boards {boards}; {crossing} ribbon nets all pass through connectors."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
