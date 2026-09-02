#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = []
# ///
"""Power-budget checker for the TBox power tree.

Topology and loads come from the schematic, capability from
``power_tree.json`` -- see power_model.py for the rules and the typ/max
convention.  Each rail's flattened maximum (its own loads plus everything
downstream) is compared against ``max_ma``:

    OK        below the alert threshold
    ALERT     at/above alert_utilization * max_ma (still within max)
    OVER      above max_ma  -> exit status 1

Usage:
    tools/check_power.py                 # exports the netlist via kicad-cli
    tools/check_power.py --netlist x.net # use an existing netlist
    tools/check_power.py --strict        # ALERT also fails
    tools/check_power.py -v              # list every annotated part per rail
"""

import argparse
import json
import sys

from power_model import SRC, PowerTree, export_netlist, fmt_ma, parse_netlist


def main():
    ap = argparse.ArgumentParser(description="Check TBox power budgets.")
    ap.add_argument("--netlist", help="use this netlist instead of exporting")
    ap.add_argument("--json", default=SRC, help="power_tree.json path")
    ap.add_argument("--strict", action="store_true", help="ALERT also fails")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args()

    with open(args.json) as f:
        src = json.load(f)
    with open(args.netlist or export_netlist()) as f:
        tree = PowerTree(src, *parse_netlist(f.read()))

    print("topology (from the schematic):")
    for r in tree.order():
        if r == tree.root:
            print(f"  {r}  <- {src['input']['name']}")
        elif r in tree.parent:
            print(f"  {r}  <- {tree.parent[r]} via {tree.converter_label(r)}")
        else:
            print(f"  {r}  <- ???")

    print(f"\n{'rail':12} {'direct':>13} {'total':>13} {'cap':>6} {'util':>5}  status")
    print("-" * 62)
    failed = False
    for r in tree.order():
        n = tree.nodes[r]
        dt, dm = tree.direct_sum(r)
        tt, tm = tree.total(r)
        st, frac = tree.status(r)
        if st == "OVER" or (args.strict and st == "ALERT"):
            failed = True
        util = f"{frac * 100:4.0f}%" if frac is not None else ""
        cap = f"{n['max_ma']:g}" if n.get("max_ma") else "-"
        direct = f"{fmt_ma(dt)}/{fmt_ma(dm)}"
        total = f"{fmt_ma(tt)}/{fmt_ma(tm)}"
        tail = ""
        if n.get("no_loads") and not tree.direct[r]:
            tail = "  (no loads by design)"
        print(f"{r:12} {direct:>13} {total:>13} {cap:>6} {util:>5}  {st}{tail}")
        if args.verbose:
            for sheet, refs, t, m in tree.by_sheet(r):
                print(f"{'':12}   {sheet}: {' '.join(refs)} = {fmt_ma(t)}/{fmt_ma(m)}")

    if tree.warnings:
        print("\nwarnings:")
        for w in tree.warnings:
            print(f"  - {w}")

    if failed:
        print("\nFAIL: a rail exceeds its budget.")
        return 1
    print("\nOK: all rails within budget.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
