#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = []
# ///
"""Power-budget checker for the TBox power tree.

Reconciles the two sources of truth:

  - Supply capability lives in ``power_tree.json``: each rail node carries
    ``max_ma`` (deliverable maximum) and the global ``alert_utilization``.
  - Actual loads live in the schematic: each current-drawing symbol carries a
    ``Load_mA`` field ("typ" or "typ/max", in mA). Optionally ``Load_rail``
    names the rail explicitly when attribution is ambiguous.

For each rail the checker sums the ``Load_mA`` of the parts drawing from it
(attributed via the part's power-input pin) and compares the total against
``max_ma``:

    OK        below the alert threshold
    ALERT     at/above alert_utilization * max_ma (still within max)
    OVER      above max_ma  -> exit status 1 (fails CI)

It also prints an advisory comparison against the human ``loads`` list in the
json (best-effort numeric parse) to flag drift.

Usage:
    tools/check_power.py                 # auto-exports the netlist via kicad-cli
    tools/check_power.py --netlist x.net # use an existing netlist
    tools/check_power.py --strict        # ALERT also fails (exit 1)

Loads are attributed to the rail on a part's power_in pin. If a part has no
power_in pin it is attributed to the single rail net it touches; if that is
ambiguous, set a ``Load_rail`` field on the symbol.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
KI = os.path.join(ROOT, "kicad")
SRC = os.path.join(ROOT, "power_tree.json")
ROOT_SCH = os.path.join(KI, "tbox.kicad_sch")

# tolerant s-expression atom scanners over the flat kicad netlist text
_NET_RE = re.compile(
    r'\(net\s+\(code\s+"[^"]*"\)\s+\(name\s+"([^"]*)"\)(.*?)(?=\(net\s+\(code|\Z)', re.S
)
_NODE_RE = re.compile(
    r'\(node\s+\(ref\s+"([^"]+)"\)\s+\(pin\s+"([^"]+)"\)'
    r'(?:\s+\(pinfunction\s+"[^"]*"\))?\s+\(pintype\s+"([^"]*)"\)'
)
_COMP_RE = re.compile(
    r'\(comp\s+\(ref\s+"([^"]+)"\)(.*?)(?=\(comp\s+\(ref|\(libparts)', re.S
)
_FIELD_RE = re.compile(r'\(field\s+\(name\s+"([^"]+)"\)\s+"([^"]*)"\)')
_VALUE_RE = re.compile(r'\(value\s+"([^"]*)"\)')


def export_netlist():
    """Export the project netlist via kicad-cli to a temp file; return path."""
    fd, path = tempfile.mkstemp(suffix=".net", prefix="tbox-power-")
    os.close(fd)
    try:
        subprocess.run(
            ["kicad-cli", "sch", "export", "netlist", "--output", path, ROOT_SCH],
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        sys.exit("error: kicad-cli not found; pass --netlist with an exported netlist")
    except subprocess.CalledProcessError as exc:
        sys.exit(f"error: kicad-cli netlist export failed:\n{exc.stderr}")
    return path


def parse_netlist(text):
    """Return (comps, touches).

    comps:   ref -> {"value": str, "fields": {name: value}}
    touches: ref -> list of (rail_net_name, pintype)
    """
    comps = {}
    for ref, body in _COMP_RE.findall(text):
        fields = {n: v for n, v in _FIELD_RE.findall(body)}
        vm = _VALUE_RE.search(body)
        comps[ref] = {"value": vm.group(1) if vm else "", "fields": fields}

    touches = {}
    for net_name, body in _NET_RE.findall(text):
        for ref, _pin, pintype in _NODE_RE.findall(body):
            touches.setdefault(ref, []).append((net_name, pintype))
    return comps, touches


def parse_ma(s):
    """Parse a 'typ' or 'typ/max' mA string -> (typ, max) floats, or None."""
    if s is None:
        return None
    parts = s.replace(" ", "").split("/")
    try:
        nums = [float(p) for p in parts if p != ""]
    except ValueError:
        return None
    if not nums:
        return None
    return (nums[0], nums[-1])


def loose_ma(s):
    """Best-effort single number from a freeform json load string (max-ish)."""
    nums = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", str(s))]
    return max(nums) if nums else None


def attribute(ref, touches, rails):
    """Which rail does this part draw from? Returns rail name or None."""
    seen = touches.get(ref, [])
    pin_rails = {n for n, pt in seen if pt == "power_in" and n in rails}
    if len(pin_rails) == 1:
        return next(iter(pin_rails))
    if not pin_rails:
        any_rails = {n for n, _pt in seen if n in rails}
        if len(any_rails) == 1:
            return next(iter(any_rails))
    return None  # ambiguous or none


def main():
    ap = argparse.ArgumentParser(description="Check TBox power budgets.")
    ap.add_argument("--netlist", help="use this netlist instead of exporting")
    ap.add_argument("--json", default=SRC, help="power_tree.json path")
    ap.add_argument(
        "--strict", action="store_true", help="ALERT (>=threshold) also fails"
    )
    args = ap.parse_args()

    src = json.load(open(args.json))
    default_util = src.get("alert_utilization", 0.75)
    nodes = {n["name"]: n for n in src["nodes"]}
    rails = set(nodes)

    text = open(args.netlist).read() if args.netlist else open(export_netlist()).read()
    comps, touches = parse_netlist(text)

    # attribute each Load_mA-bearing part to a rail
    per_rail = {r: [] for r in rails}  # rail -> [(ref, typ, max)]
    warnings = []
    for ref, c in sorted(comps.items()):
        raw = c["fields"].get("Load_mA")
        if not raw:
            continue
        val = parse_ma(raw)
        if val is None:
            warnings.append(f"{ref}: unparseable Load_mA {raw!r}")
            continue
        rail = c["fields"].get("Load_rail") or attribute(ref, touches, rails)
        if rail is None:
            warnings.append(
                f"{ref}: cannot attribute Load_mA to a rail (set Load_rail)"
            )
            continue
        if rail not in rails:
            warnings.append(f"{ref}: Load_rail {rail!r} is not a power_tree node")
            continue
        per_rail[rail].append((ref, val[0], val[1]))

    over = False
    print(f"{'rail':12} {'typ':>8} {'max':>8} {'cap':>7} {'util':>6}  status")
    print("-" * 56)
    for name, node in nodes.items():
        cap = node.get("max_ma")
        items = per_rail.get(name, [])
        typ = sum(t for _r, t, _m in items)
        mx = sum(m for _r, _t, m in items)
        util_th = node.get("alert_utilization", default_util)
        if cap:
            frac = mx / cap
            if mx > cap:
                status, over = "OVER", True
            elif frac >= util_th:
                status = "ALERT"
            else:
                status = "OK"
            utils = f"{frac * 100:4.0f}%"
            caps = f"{cap:g}"
        else:
            status, utils, caps = "-", "", "-"
        print(f"{name:12} {typ:8.2f} {mx:8.2f} {caps:>7} {utils:>6}  {status}")

    # advisory: extracted vs the human loads list in the json
    print("\nvs power_tree.json loads (advisory):")
    for name, node in nodes.items():
        listed = [loose_ma(ld.get("ma")) for ld in node.get("loads", [])]
        listed = [x for x in listed if x is not None]
        listed_sum = sum(listed)
        extracted = sum(m for _r, _t, m in per_rail.get(name, []))
        n_ann = len(per_rail.get(name, []))
        note = ""
        if node.get("loads") and n_ann == 0:
            note = "  (not yet annotated)"
        elif extracted > listed_sum + 0.5:
            # extracted draw beats the human estimate -> revisit the budget note
            note = f"  OVER json estimate (~{listed_sum:g})"
        elif n_ann:
            note = f"  ({n_ann} part(s) annotated)"
        print(
            f"  {name:12} json~{listed_sum:6g} mA   extracted {extracted:6g} mA{note}"
        )

    if warnings:
        print("\nwarnings:")
        for w in warnings:
            print(f"  - {w}")

    if over or (
        args.strict
        and any(
            p
            and sum(m for _r, _t, m in p)
            >= nodes[r].get("alert_utilization", default_util)
            * (nodes[r].get("max_ma") or 1e18)
            for r, p in per_rail.items()
        )
    ):
        print("\nFAIL: a rail exceeds its budget.")
        return 1
    print("\nOK: all rails within budget.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
