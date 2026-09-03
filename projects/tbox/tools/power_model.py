"""Power-tree model shared by check_power.py and gen_power_tree.py.

Two sources, strictly separated:

  schematic (via the exported netlist)
      - topology: a converter is any part with a ``power_in`` pin on one
        rail and a ``power_out`` pin on another.  A converter whose output
        reaches the rail through a passive (the ADP7142's RC) or from a
        plain ``output`` pin (the VREF buffer) declares the rail it feeds
        with a ``Rail_out`` field instead.
      - loads: every current-drawing symbol carries ``Load_mA`` ("typ" or
        "typ/max", mA), attributed to the rail on its ``power_in`` pin, or
        to the single rail net it touches, or to an explicit ``Load_rail``.
  power_tree.json
      - capability only: per rail ``max_ma`` / ``max_basis`` (and the
        ``_max_analysis`` behind it), ``alert_utilization``, optional
        ``efficiency`` + ``v`` for switching stages, ``no_loads`` for rails
        that carry no DC load by design, and the ``input`` description
        naming the root rail.

Convention for the two numbers:

  typ   the normal receiving state: powered, nothing keyed, no button
        held, phones at conversational level.
  max   every load that can be on at the same time, each at its sustained
        maximum (amplifiers: full-scale sine at clip into the rated load).

Rails are flattened: a load annotated once on a part is an occurrence on
its own rail and on every rail upstream of it -- 1:1 through a linear
stage, scaled by Vout/(Vin*efficiency) through a switching stage.  A
converter's own quiescent/ground current is just its ``Load_mA`` and lands
on its input rail like any other draw.
"""

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

_NET_RE = re.compile(
    r'\(net\s+\(code\s+"[^"]*"\)\s+\(name\s+"([^"]*)"\)(.*?)(?=\(net\s+\(code|\Z)',
    re.DOTALL,
)
_NODE_RE = re.compile(
    r'\(node\s+\(ref\s+"([^"]+)"\)\s+\(pin\s+"([^"]+)"\)'
    r'(?:\s+\(pinfunction\s+"[^"]*"\))?\s+\(pintype\s+"([^"]*)"\)'
)
_COMP_RE = re.compile(
    r'\(comp\s+\(ref\s+"([^"]+)"\)(.*?)(?=\(comp\s+\(ref|\(libparts)', re.DOTALL
)
_FIELD_RE = re.compile(r'\(field\s+\(name\s+"([^"]+)"\)\s+"([^"]*)"\)')
_VALUE_RE = re.compile(r'\(value\s+"([^"]*)"\)')
_SHEET_RE = re.compile(r'\(sheetpath\s+\(names\s+"([^"]*)"')


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

    comps:   ref -> {"value", "fields": {name: value}, "sheet": "/TX Bus/"}
    touches: ref -> [(net_name, pintype)]
    """
    comps = {}
    for ref, body in _COMP_RE.findall(text):
        vm = _VALUE_RE.search(body)
        sm = _SHEET_RE.search(body)
        comps[ref] = {
            "value": vm.group(1) if vm else "",
            "fields": dict(_FIELD_RE.findall(body)),
            "sheet": sm.group(1) if sm else "/",
        }
    touches = {}
    for net_name, body in _NET_RE.findall(text):
        for ref, _pin, pintype in _NODE_RE.findall(body):
            touches.setdefault(ref, []).append((net_name, pintype))
    return comps, touches


def parse_ma(s):
    """'typ' or 'typ/max' -> (typ, max) floats, or None."""
    if s is None:
        return None
    try:
        nums = [float(p) for p in s.replace(" ", "").split("/") if p]
    except ValueError:
        return None
    return (nums[0], nums[-1]) if nums else None


def attribute(ref, touches, rails):
    """Rail a part draws from: its power_in rail, else the only rail it touches."""
    seen = touches.get(ref, [])
    pin_rails = {n for n, pt in seen if pt == "power_in" and n in rails}
    if len(pin_rails) == 1:
        return next(iter(pin_rails))
    if not pin_rails:
        any_rails = {n for n, _pt in seen if n in rails}
        if len(any_rails) == 1:
            return next(iter(any_rails))
    return None


class PowerTree:
    """Topology + loads from the netlist, capability from the json."""

    def __init__(self, src, comps, touches):
        self.src = src
        self.comps, self.touches = comps, touches
        self.nodes = {n["name"]: n for n in src["nodes"]}
        self.rails = set(self.nodes)
        self.root = src["input"]["rail"]
        self.warnings = []
        if self.root not in self.rails:
            raise SystemExit(f"error: input.rail {self.root!r} is not a rail node")
        self.parent, self.converter = self._derive_topology()
        self.children = {}
        for r, p in self.parent.items():
            self.children.setdefault(p, []).append(r)
        self.direct = self._collect_loads()  # rail -> [(ref, typ, max)]

    # -- topology ---------------------------------------------------------
    def _derive_topology(self):
        parent, converter = {}, {}
        for ref, seen in sorted(self.touches.items()):
            if ref.startswith("#"):
                continue
            ins = {n for n, pt in seen if pt == "power_in" and n in self.rails}
            outs = {n for n, pt in seen if pt == "power_out" and n in self.rails}
            declared = self.comps.get(ref, {}).get("fields", {}).get("Rail_out")
            if declared:
                if declared not in self.rails:
                    self.warnings.append(f"{ref}: Rail_out {declared!r} is not a rail")
                    continue
                outs.add(declared)
            for out in outs - ins:
                if len(ins) != 1:
                    self.warnings.append(
                        f"{ref}: feeds {out} but has {len(ins)} power_in rails"
                    )
                    continue
                src = next(iter(ins))
                if out in parent and parent[out] != src:
                    self.warnings.append(
                        f"{out}: fed from both {parent[out]} ({converter[out]}) "
                        f"and {src} ({ref})"
                    )
                    continue
                parent[out], converter[out] = src, ref
        for r in sorted(self.rails - {self.root}):
            if r not in parent:
                self.warnings.append(
                    f"{r}: no converter feeds it (power_out pin or Rail_out field)"
                )
        return parent, converter

    def converter_label(self, rail):
        ref = self.converter.get(rail)
        if not ref:
            return ""
        return f"{ref} {self.comps[ref]['value']}".strip()

    # -- loads ------------------------------------------------------------
    def _collect_loads(self):
        direct = {r: [] for r in self.rails}
        for ref, c in sorted(self.comps.items()):
            raw = c["fields"].get("Load_mA")
            if not raw:
                continue
            val = parse_ma(raw)
            if val is None:
                self.warnings.append(f"{ref}: unparseable Load_mA {raw!r}")
                continue
            rail = c["fields"].get("Load_rail") or attribute(
                ref, self.touches, self.rails
            )
            if rail is None:
                self.warnings.append(
                    f"{ref}: cannot attribute Load_mA to a rail (set Load_rail)"
                )
                continue
            if rail not in self.rails:
                self.warnings.append(f"{ref}: Load_rail {rail!r} is not a rail")
                continue
            if self.nodes[rail].get("no_loads"):
                self.warnings.append(
                    f"{ref}: Load_mA on {rail}, which is declared no_loads"
                )
            direct[rail].append((ref, val[0], val[1]))
        return direct

    def direct_sum(self, rail):
        items = self.direct[rail]
        return (sum(t for _r, t, _m in items), sum(m for _r, _t, m in items))

    def scale(self, rail):
        """Factor turning the child's output current into the parent's input current."""
        n = self.nodes[rail]
        eff = n.get("efficiency")
        if not eff:
            return 1.0
        p = self.nodes[self.parent[rail]]
        if "v" not in n or "v" not in p:
            raise SystemExit(
                f"error: {rail}: efficiency needs 'v' on it and its parent"
            )
        return n["v"] / (p["v"] * eff)

    def total(self, rail):
        """Flattened (typ, max): direct loads plus everything downstream."""
        typ, mx = self.direct_sum(rail)
        for c in self.children.get(rail, []):
            ct, cm = self.total(c)
            k = self.scale(c)
            typ += ct * k
            mx += cm * k
        return typ, mx

    def by_sheet(self, rail):
        """Direct loads grouped by board (top-level sheet): [(board, [refs], typ, max)]."""
        groups = {}
        for ref, t, m in self.direct[rail]:
            board = self.comps[ref]["sheet"].strip("/").split("/")[0] or "Root"
            g = groups.setdefault(board, [[], 0.0, 0.0])
            g[0].append(ref)
            g[1] += t
            g[2] += m
        return [(s, refs, t, m) for s, (refs, t, m) in sorted(groups.items())]

    def status(self, rail):
        """(status, utilization) from the flattened max against max_ma."""
        n = self.nodes[rail]
        cap = n.get("max_ma")
        if not cap:
            return "-", None
        _t, mx = self.total(rail)
        frac = mx / cap
        th = n.get("alert_utilization", self.src.get("alert_utilization", 0.75))
        if mx > cap:
            return "OVER", frac
        if frac >= th:
            return "ALERT", frac
        return "OK", frac

    def order(self):
        """Rails in tree order (parent before children)."""
        out = []

        def walk(r):
            out.append(r)
            for c in self.children.get(r, []):
                walk(c)

        walk(self.root)
        out += [r for r in sorted(self.rails) if r not in out]
        return out


def fmt_ma(x):
    return f"{x:g}" if abs(x - round(x)) < 0.05 else f"{x:.1f}"
