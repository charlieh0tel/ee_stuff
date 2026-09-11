#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = []
# ///
"""Update the PCB from the schematic without the GUI (KiCad's F8, headless).

Exports the netlist with kicad-cli and applies it to kicad/tbox.kicad_pcb
through the pcbnew API, the way "Update PCB from Schematic" does:

  - footprints are matched to symbols by their schematic path (sheet
    path + symbol uuid), never by reference;
  - a symbol with no footprint on the board gets one loaded from the
    library its Footprint field names, parked at (0, 0) so
    place_panel.py treats it as unplaced;
  - a footprint whose library part changed is replaced in place (same
    position, rotation and side);
  - reference, value, every symbol field, sheet name/file and the
    DNP / exclude-from-BOM attributes are copied onto the footprint;
  - every pad takes the net of its pin (all pads sharing a number),
    pins with no node are unconnected; nets are created as needed and
    unused ones dropped;
  - footprints whose symbol is gone are removed (with their pads' nets
    cleared first), unless --keep-orphans.

Everything else on the board (tracks, zones, the panel frame, hand
placement) is untouched.  Exit status 1 if anything could not be
resolved (a missing library part, a pad number the netlist names that
the footprint lacks).

Usage:
    tools/sync_pcb.py                 # export netlist, update the board
    tools/sync_pcb.py --netlist x.net # use an existing netlist
    tools/sync_pcb.py --dry-run       # report, change nothing
    tools/sync_pcb.py --keep-orphans  # do not delete footprints without a symbol
Needs KiCad's pcbnew Python module (re-execs under the system python3).
"""

import argparse
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
KI = os.path.join(ROOT, "kicad")
PCB = os.path.join(KI, "tbox.kicad_pcb")
SCH = os.path.join(KI, "tbox.kicad_sch")
STOCK = "/usr/share/kicad/footprints"


# ---- netlist ---------------------------------------------------------------------------


def _tokenize(text):
    """S-expression tokenizer: strings stay one token (quotes stripped)."""
    for m in re.finditer(r'"((?:[^"\\]|\\.)*)"|([()])|([^\s()"]+)', text):
        if m.group(1) is not None:
            yield ("s", m.group(1).replace('\\"', '"').replace("\\\\", "\\"))
        elif m.group(2):
            yield ("p", m.group(2))
        else:
            yield ("a", m.group(3))


def _parse(text):
    stack = [[]]
    for kind, tok in _tokenize(text):
        if kind == "p" and tok == "(":
            stack.append([])
        elif kind == "p":
            node = stack.pop()
            stack[-1].append(node)
        else:
            stack[-1].append(tok)
    return stack[0][0]


def _kids(node, key):
    return [k for k in node[1:] if isinstance(k, list) and k and k[0] == key]


def _kid(node, key, default=None):
    ks = _kids(node, key)
    return ks[0] if ks else default


def _atom(node, key, default=""):
    k = _kid(node, key)
    return k[1] if k and len(k) > 1 and not isinstance(k[1], list) else default


def read_netlist(path):
    """-> comps: path -> dict(ref, value, footprint, fields, sheetname, sheetfile,
    dnp, exclude_bom); nets: name -> [(ref, pin, pinfunction, pintype)]"""
    with open(path) as f:
        root = _parse(f.read())
    comps = {}
    for c in _kids(_kid(root, "components"), "comp"):
        ref = _atom(c, "ref")
        sp = _kid(c, "sheetpath")
        spath = _atom(sp, "tstamps") if sp else "/"
        snames = _atom(sp, "names") if sp else "/"
        # a multi-unit symbol lists every unit's uuid; any of them may be the
        # one an existing footprint was created with, a new one takes the first
        tk = _kid(c, "tstamps")
        tstamps = [t for t in tk[1:] if not isinstance(t, list)] if tk else []
        tstamp = tstamps[0] if tstamps else ""
        props = {}
        for p in _kids(c, "property"):
            props[_atom(p, "name")] = _atom(p, "value")
        if "exclude_from_board" in props:
            continue  # on_board no: a panel-only part
        fields = {}
        fl = _kid(c, "fields")
        if fl:
            for fld in _kids(fl, "field"):
                name = _atom(fld, "name")
                val = fld[2] if len(fld) > 2 and not isinstance(fld[2], list) else ""
                fields[name] = val
        comps[spath + tstamp] = {
            "paths": [spath + t for t in tstamps],
            "ref": ref,
            "value": _atom(c, "value"),
            "footprint": _atom(c, "footprint"),
            "fields": fields,
            "sheetname": snames,  # as F8 stores it: "/Front Board/Preamp A/"
            "sheetfile": props.get("Sheetfile", ""),
            "dnp": "dnp" in props,
            "exclude_bom": "exclude_from_bom" in props,
        }
    nets = {}
    for n in _kids(_kid(root, "nets"), "net"):
        name = _atom(n, "name")
        nodes = [
            (
                _atom(nd, "ref"),
                _atom(nd, "pin"),
                _atom(nd, "pinfunction"),
                _atom(nd, "pintype"),
            )
            for nd in _kids(n, "node")
        ]
        nets[name] = nodes
    return comps, nets


def export_netlist(sch):
    fd, path = tempfile.mkstemp(suffix=".net", prefix="tbox-sync-")
    os.close(fd)
    subprocess.run(
        ["kicad-cli", "sch", "export", "netlist", "--output", path, sch],
        check=True,
        capture_output=True,
        text=True,
    )
    return path


# ---- footprint libraries ---------------------------------------------------------------


def lib_table(path):
    """fp-lib-table -> {nickname: directory} (KiCad-type libraries only)."""
    out = {}
    if not os.path.exists(path):
        return out
    with open(path) as f:
        t = f.read()
    for m in re.finditer(
        r'\(lib\s*\(name "([^"]+)"\)\s*\(type "([^"]+)"\)\s*\(uri "([^"]+)"\)', t
    ):
        name, kind, uri = m.groups()
        if kind != "KiCad":
            continue
        uri = uri.replace("${KIPRJMOD}", KI).replace("${KICAD10_FOOTPRINT_DIR}", STOCK)
        uri = re.sub(r"\$\{KICAD\d*_FOOTPRINT_DIR\}", STOCK, uri)
        out[name] = uri
    return out


def find_libs():
    libs = {}
    cfg = os.path.expanduser("~/.config/kicad")
    if os.path.isdir(cfg):
        for v in sorted(os.listdir(cfg)):
            libs.update(lib_table(os.path.join(cfg, v, "fp-lib-table")))
    libs.update(lib_table(os.path.join(KI, "fp-lib-table")))
    return libs


# ---- the update ------------------------------------------------------------------------


def main():
    ap = argparse.ArgumentParser(
        description="Update the PCB from the schematic, headless."
    )
    ap.add_argument("--netlist", help="use this netlist instead of exporting one")
    ap.add_argument(
        "--pcb", default=PCB, help="board to update (default kicad/tbox.kicad_pcb)"
    )
    ap.add_argument(
        "--sch",
        default=SCH,
        help="root schematic to export (default kicad/tbox.kicad_sch)",
    )
    ap.add_argument("--dry-run", action="store_true", help="report only")
    ap.add_argument(
        "--reload",
        metavar="FPID[,FPID...]",
        help="reload these footprints' geometry from the library even though the "
        "library id has not changed (use 'all' for every footprint); needed after "
        "editing a .kicad_mod in place, which a plain run cannot detect",
    )
    ap.add_argument(
        "--keep-orphans", action="store_true", help="keep footprints without a symbol"
    )
    args = ap.parse_args()

    try:
        import pcbnew
    except ImportError:
        os.execv("/usr/bin/python3", ["/usr/bin/python3", *sys.argv])
    import pcbnew

    reload_set = set()
    if args.reload:
        reload_set = {f.strip() for f in args.reload.split(",") if f.strip()}

    comps, nets = read_netlist(args.netlist or export_netlist(args.sch))
    libs = find_libs()
    board = pcbnew.LoadBoard(args.pcb)
    problems = []

    by_path = {}
    for fp in board.GetFootprints():
        p = fp.GetPath().AsString()
        if p:
            by_path[p] = fp

    def fpid_of(fp):
        i = fp.GetFPID()
        return f"{i.GetLibNickname()}:{i.GetLibItemName()}"

    def load(fpid):
        nick, _, name = fpid.partition(":")
        if nick not in libs:
            problems.append(f"footprint library {nick!r} not in any fp-lib-table")
            return None
        fp = pcbnew.FootprintLoad(libs[nick], name)
        if fp is None:
            problems.append(f"{fpid}: not found in {libs[nick]}")
        else:
            fp.SetFPID(pcbnew.LIB_ID(nick, name))
        return fp

    # --- footprints: add, replace, update ---
    added, replaced, removed, reloaded = [], [], [], []
    for path, c in sorted(comps.items(), key=lambda kv: kv[1]["ref"]):
        if not c["footprint"]:
            problems.append(f"{c['ref']}: symbol has no footprint")
            continue
        fp = next((by_path[p] for p in c["paths"] if p in by_path), None)
        if fp is not None and fp.GetPath().AsString() != path:
            path = fp.GetPath().AsString()  # keep the uuid it was created with
        stale = bool(reload_set) and (
            "all" in reload_set or c["footprint"] in reload_set
        )
        if fp is not None and (fpid_of(fp) != c["footprint"] or stale):
            new = load(c["footprint"])
            if new is None:
                continue
            new.SetPosition(fp.GetPosition())
            new.SetOrientation(fp.GetOrientation())
            if fp.IsFlipped():
                new.Flip(new.GetPosition(), False)
            if fpid_of(fp) == c["footprint"]:
                reloaded.append(f"{c['ref']} ({c['footprint']})")
            else:
                replaced.append(f"{c['ref']}: {fpid_of(fp)} -> {c['footprint']}")
            if not args.dry_run:
                board.Remove(fp)
                board.Add(new)
            fp = new
            by_path[path] = fp
        elif fp is None:
            fp = load(c["footprint"])
            if fp is None:
                continue
            fp.SetPosition(pcbnew.VECTOR2I(0, 0))
            added.append(f"{c['ref']} ({c['footprint']})")
            if not args.dry_run:
                board.Add(fp)
            by_path[path] = fp
        if args.dry_run:
            continue
        fp.SetPath(pcbnew.KIID_PATH(path))
        fp.SetReference(c["ref"])
        fp.SetValue(c["value"])
        fp.SetSheetname(c["sheetname"])
        fp.SetSheetfile(c["sheetfile"])
        for name, val in c["fields"].items():
            if name in ("Reference", "Value", "Footprint"):
                continue
            if (
                name in ("Datasheet", "Description")
                and not val
                and not fp.HasField(name)
            ):
                continue
            fp.SetField(name, val)
        attrs = fp.GetAttributes()
        for flag, on in (
            (pcbnew.FP_DNP, c["dnp"]),
            (pcbnew.FP_EXCLUDE_FROM_BOM, c["exclude_bom"]),
        ):
            attrs = (attrs | flag) if on else (attrs & ~flag)
        fp.SetAttributes(attrs)

    # --- orphans ---
    known = {p for c in comps.values() for p in c["paths"]}
    for path, fp in list(by_path.items()):
        if path not in known:
            removed.append(f"{fp.GetReference()} ({fpid_of(fp)})")
            if not args.dry_run and not args.keep_orphans:
                board.Remove(fp)
                del by_path[path]
    unpathed = [
        fp.GetReference() for fp in board.GetFootprints() if not fp.GetPath().AsString()
    ]

    # --- nets ---
    ref_to_fp = {}
    for c in comps.values():
        for p in c["paths"]:
            if p in by_path:
                ref_to_fp[c["ref"]] = by_path[p]
                break
    net_changes = 0
    if not args.dry_run:
        for fp in ref_to_fp.values():
            for pad in fp.Pads():
                pad.SetNetCode(0)
        for name, nodes in nets.items():
            net = board.FindNet(name)
            if net is None:
                net = pcbnew.NETINFO_ITEM(board, name)
                board.Add(net)
            for ref, pin, func, ptype in nodes:
                fp = ref_to_fp.get(ref)
                if fp is None:
                    continue  # a component we could not place (already a problem)
                hit = False
                for pad in fp.Pads():
                    if pad.GetNumber() == pin:
                        if pad.GetNetname() != name:
                            net_changes += 1
                        pad.SetNet(net)
                        pad.SetPinFunction(func)
                        pad.SetPinType(ptype)
                        hit = True
                if not hit:
                    problems.append(
                        f"{ref}: pin {pin!r} ({func}) has no pad on {fpid_of(fp)}"
                    )
        board.RemoveUnusedNets(None)
        board.BuildConnectivity()

    # --- report ---
    for title, items in (
        ("added", added),
        ("replaced", replaced),
        ("reloaded from the library", reloaded),
        ("removed" if not args.keep_orphans else "orphans kept", removed),
    ):
        if items:
            print(f"{title} ({len(items)}):")
            for i in items:
                print(f"  {i}")
    if unpathed:
        print(f"footprints without a schematic path (left alone): {unpathed}")
    print(f"{len(comps)} symbols, {len(nets)} nets, {net_changes} pad net changes")
    for p in problems:
        print("PROBLEM:", p)
    if args.dry_run:
        print("dry run: board not written")
    elif problems:
        print("board not written")
        return 1
    else:
        pcbnew.SaveBoard(args.pcb, board)
        print(f"wrote {args.pcb}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
