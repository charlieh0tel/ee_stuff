#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = []
# ///
"""Geometric connectivity lint for KiCad schematics.

KiCad connects a symbol pin whose end lands anywhere on a wire, and two pin
ends that touch, without drawing a junction and without an ERC complaint.
Both are easy to do by accident when placing symbols and both produce a
short that only shows up in the netlist.  This script reports:

  - a pin end lying on the *interior* of a wire segment (not at an endpoint)
  - two pins of different symbols ending on the same point
  - a wire endpoint on the interior of another wire (T without a junction)
  - two symbols on one sheet sharing a reference designator and unit

Junction symbols and power symbols (#PWR/#FLG) are treated as intentional.

Usage:
    tools/check_sch.py                 # every kicad/*.kicad_sch
    tools/check_sch.py kicad/foo.kicad_sch ...
Exit status 1 if anything is reported.
"""

import glob
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
KI = os.path.join(os.path.dirname(HERE), "kicad")


def match_block(text, start):
    depth, i, in_str = 0, start, False
    while i < len(text):
        c = text[i]
        if in_str:
            if c == "\\":
                i += 1
            elif c == '"':
                in_str = False
        elif c == '"':
            in_str = True
        elif c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
        i += 1
    raise ValueError("unbalanced s-expression")


def top_level(text):
    for m in re.finditer(r"\n  \(", text):
        yield match_block(text, m.start() + 1)


def lib_pins(text):
    """lib_id -> {unit: [(x, y)]} pin positions in symbol coordinates."""
    m = re.search(r"\n  \(lib_symbols", text)
    if not m:
        return {}
    block = match_block(text, m.start() + 1)
    out = {}
    for sm in re.finditer(r'\n    \(symbol "([^"]+)"', block):
        lib_id = sm.group(1)
        sblock = match_block(block, sm.start() + 1)
        units = {}
        for um in re.finditer(r'\(symbol "([^"]+)_(\d+)_\d+"', sblock):
            ublock = match_block(sblock, um.start())
            pins = [
                (float(x), float(y))
                for x, y in re.findall(
                    r"\(pin\s+\w+\s+\w+\s*\(at\s+([-\d.]+)\s+([-\d.]+)", ublock
                )
            ]
            units.setdefault(int(um.group(2)), []).extend(pins)
        out[lib_id] = units
    return out


def xform(px, py, x, y, rot, mirror):
    if mirror == "y":
        px = -px
    elif mirror == "x":
        py = -py
    if rot == 0:
        return (x + px, y - py)
    if rot == 90:
        return (x - py, y - px)
    if rot == 180:
        return (x - px, y + py)
    return (x + py, y + px)


def r(p):
    return (round(p[0], 3), round(p[1], 3))


def check(path):
    with open(path) as f:
        text = f.read()
    libs = lib_pins(text)
    pins, wires, junctions = [], [], set()
    seen = {}
    for blk in top_level(text):
        head = blk.split(None, 1)[0]
        if head == "(symbol":
            lib_id = re.search(r'\(lib_id "([^"]+)"', blk).group(1)
            x, y, rot = re.search(r"\(at ([-\d.]+) ([-\d.]+) (\d+)\)", blk).groups()
            mir = re.search(r"\(mirror (\w)\)", blk)
            unit = int(re.search(r"\(unit (\d+)\)", blk).group(1))
            ref = re.search(r'"Reference" "([^"]+)"', blk).group(1)
            if not ref.startswith("#"):
                seen.setdefault((ref, unit), 0)
                seen[(ref, unit)] += 1
            units = libs.get(lib_id, {})
            for px, py in units.get(unit, []) + units.get(0, []):
                pins.append(
                    (
                        r(
                            xform(
                                px,
                                py,
                                float(x),
                                float(y),
                                int(rot),
                                mir.group(1) if mir else None,
                            )
                        ),
                        ref,
                    )
                )
        elif head == "(wire":
            pts = [
                r((float(a), float(b)))
                for a, b in re.findall(r"\(xy ([-\d.]+) ([-\d.]+)\)", blk)
            ]
            wires.append((pts[0], pts[1]))
        elif head == "(junction":
            a, b = re.search(r"\(at ([-\d.]+) ([-\d.]+)\)", blk).groups()
            junctions.add(r((float(a), float(b))))

    def interior(p, a, b):
        if a[0] == b[0] == p[0]:
            return min(a[1], b[1]) < p[1] < max(a[1], b[1])
        if a[1] == b[1] == p[1]:
            return min(a[0], b[0]) < p[0] < max(a[0], b[0])
        return False

    problems = [
        f"duplicate reference {r} unit {u} ({n} symbols)"
        for (r, u), n in seen.items()
        if n > 1
    ]
    by_pt = {}
    for pt, ref in pins:
        by_pt.setdefault(pt, []).append(ref)
    for pt, refs in by_pt.items():
        real = [x for x in refs if not x.startswith("#")]
        if len(real) > 1 and pt not in junctions:
            problems.append(f"{pt}: pins touch without a junction: {'+'.join(refs)}")
    for pt, ref in pins:
        if pt in junctions:
            continue
        for a, b in wires:
            if interior(pt, a, b):
                problems.append(f"{pt}: pin {ref} sits on the interior of wire {a}-{b}")
    ends = {p for w in wires for p in w}
    for p in ends:
        if p in junctions:
            continue
        for a, b in wires:
            if interior(p, a, b):
                problems.append(
                    f"{p}: wire end on the interior of wire {a}-{b} (no junction)"
                )
    return problems


def main(argv):
    files = argv or sorted(glob.glob(os.path.join(KI, "*.kicad_sch")))
    bad = 0
    for f in files:
        for p in check(f):
            print(f"{os.path.relpath(f)}: {p}")
            bad += 1
    if bad:
        print(f"\n{bad} problem(s).")
        return 1
    print(f"OK: {len(files)} sheet(s) clean.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
