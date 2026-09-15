#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = []
# ///
"""Panel apertures from the mechanical model -- generate them, or check them.

Every panel hole centre is `mech.json`'s PCB-to-panel datum for that board
less the part's axis height above its seating plane, so a taller jack sits
higher on the panel.  The drawings stop being hand-maintained geometry and
become an output that has to agree with the parts.

Three things are checked, and any of them fails the run:

  * **the drawings** -- each aperture's y against the computed value;
  * **the placed board** -- each part's mechanical axis against the panel x
    it is supposed to serve, and its panel face against the board edge.
    Regenerating the SVG from the same inputs would not catch a footprint
    that moved, so the board is read separately;
  * **coverage** -- any panel part whose geometry is missing or unverified.
    An unknown dimension stops the run; it never defaults.

Apertures are keyed by a `data-ref` attribute naming the reference
designator, not by sorting circles or guessing from a nearby label.  `--write`
adds those attributes the first time, using the old positional matching, and
thereafter nothing depends on drawing order.

Usage:
    tools/gen_panels.py            # check drawings and board, change nothing
    tools/gen_panels.py --write    # update the drawings from the model
    tools/gen_panels.py --pcb no   # skip the board check (drawings only)
"""

import argparse
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import mech
from place_panel import FRONT, REAR, W, front_positions, rear_positions

TOL = 0.01  # mm; nominal file/board agreement, not a fit tolerance
ANG_TOL = 0.1  # degrees
PANELS = {
    "Front Board": ("panel-front.svg", 0.0),  # board edge the jacks face
    "Rear Board": ("panel-rear.svg", 270.0),
}


def panel_x(board, ref, fx, rx):
    """Panel-drawing x for a reference (the front panel is mirrored)."""
    return W - fx[ref] if board == "Front Board" else rx[ref]


def board_x(board, px):
    return W - px if board == "Front Board" else px


def annotate(text, wanted):
    """Add data-ref="REF" to each aperture element, matched by its x."""
    out, added = text, 0

    def add(m):
        nonlocal added
        whole, x = m.group(0), float(m.group("x"))
        if "data-ref" in whole:
            return whole
        for ref, wx in wanted.items():
            if abs(wx - x) < 0.51:
                added += 1
                return whole[:-2].rstrip() + f' data-ref="{ref}"/>'
        return whole

    out = re.sub(
        r'<circle class="(?:qjack|mjack|hole)"\s+cx="(?P<x>[-\d.]+)"[^>]*/>', add, out
    )
    out = re.sub(r'<use href="#\w+" x="(?P<x>[-\d.]+)"[^>]*/>', add, out)
    return out, added


def apertures(text):
    """-> {ref: [(attr, value, span), ...]} for every annotated aperture."""
    found = {}
    for m in re.finditer(r'<(circle|use|g)\b[^>]*data-ref="([^"]+)"[^>]*>', text):
        tag, ref = m.group(1), m.group(2)
        if "transform" in m.group(0) and tag != "g":
            found.setdefault(ref, [])  # a transform would move it; refuse
            continue
        if tag == "g":
            am = re.search(r"translate\([-\d.]+,\s*([-\d.]+)\)", m.group(0))
            attr = "translate"
        else:
            attr = "cy" if tag == "circle" else "y"
            am = re.search(rf'\b{attr}="([-\d.]+)"', m.group(0))
        if am:
            start = m.start() + am.start(1)
            found.setdefault(ref, []).append(
                (attr, float(am.group(1)), (start, start + len(am.group(1))))
            )
    return found


def main():
    ap = argparse.ArgumentParser(description="Panel apertures from mech.json.")
    ap.add_argument("--write", action="store_true", help="update the drawings")
    args = ap.parse_args()

    model = mech.load()
    fx, rx = front_positions(), rear_positions()
    problems, notes = [], []

    # the board is always read: the footprint ids come from it, and checking
    # the drawings against the same inputs that generated them proves nothing
    try:
        import pcbnew
    except ImportError:
        os.execv("/usr/bin/python3", ["/usr/bin/python3", *sys.argv])
    board = pcbnew.LoadBoard(os.path.join(ROOT, "kicad", "tbox.kicad_pcb"))
    placed = {fp.GetReference(): fp for fp in board.GetFootprints()}
    fpid_of = {}
    for ref, fp in placed.items():
        i = fp.GetFPID()
        fpid_of[ref] = f"{i.GetLibNickname()}:{i.GetLibItemName()}"

    for brd, (svg, edge) in PANELS.items():
        path = os.path.join(ROOT, svg)
        with open(path) as f:
            text = f.read()
        refs = set(FRONT.values()) if brd == "Front Board" else set(REAR.values())
        wanted = {r: panel_x(brd, r, fx, rx) for r in refs}

        added = 0
        if args.write:
            text, added = annotate(text, wanted)
            if added:
                notes.append(f"{svg}: tagged {added} aperture element(s) with data-ref")

        found = apertures(text)
        missing = sorted(refs - set(found))
        if missing:
            problems.append(
                f"{svg}: no data-ref aperture for {missing} "
                f"(run --write once to tag them)"
            )

        edits = []
        for ref in sorted(found):
            if ref not in refs:
                continue
            fpid = fpid_of.get(ref)
            if fpid is None:
                problems.append(f"{ref}: on the panel but not on the board")
                continue
            try:
                want = mech.hole_y(model, brd, fpid)
            except mech.Unresolved as e:
                problems.append(f"{ref}: {e}")
                continue
            for _attr, have, span in found[ref]:
                if abs(have - want) > TOL:
                    if args.write:
                        edits.append((span, f"{want:g}"))
                    else:
                        problems.append(
                            f"{svg}: {ref} aperture at y={have:g}, model says "
                            f"{want:g} ({have - want:+.2f} mm)"
                        )

        if args.write and (edits or added):
            for (s, e), new in sorted(edits, reverse=True):
                text = text[:s] + new + text[e:]
            with open(path, "w") as f:
                f.write(text)
            if edits:
                notes.append(f"{svg}: moved {len(edits)} aperture coordinate(s)")

        # --- the placed board ---
        for ref in sorted(refs):
            fp = placed.get(ref)
            if fp is None:
                continue
            if model["parts"].get(fpid_of[ref], {}).get("mount") == "through":
                notes.append(
                    f"{ref}: reached through the panel, not seated against it; "
                    f"its depth behind the panel is an open assembly decision"
                )
                continue
            try:
                axis, _nose, face = mech.axis_on_board(
                    model,
                    fpid_of[ref],
                    (fp.GetPosition().x / 1e6, fp.GetPosition().y / 1e6),
                    fp.GetOrientationDegrees(),
                    fp.IsFlipped(),
                )
            except mech.Unresolved as e:
                problems.append(f"{ref}: {e}")
                continue
            want_x = board_x(brd, wanted[ref])
            if abs(axis[0] - want_x) > TOL:
                problems.append(
                    f"{ref}: axis on the board at x={axis[0]:.2f}, panel wants "
                    f"{want_x:.2f} ({axis[0] - want_x:+.2f} mm)"
                )
            if abs(face[1] - edge) > TOL:
                problems.append(
                    f"{ref}: panel face at y={face[1]:.2f}, board edge is "
                    f"{edge:.2f} ({face[1] - edge:+.2f} mm)"
                )
            # facing: a part with no axis offset and no shoulder distance has
            # coordinates that are invariant under rotation, so check the nose
            want_nose = (0.0, -1.0) if brd == "Front Board" else (0.0, 1.0)
            if abs(_nose[0] - want_nose[0]) > math.radians(ANG_TOL) or abs(
                _nose[1] - want_nose[1]
            ) > math.radians(ANG_TOL):
                problems.append(
                    f"{ref}: nose points ({_nose[0]:+.2f},{_nose[1]:+.2f}), "
                    f"the panel is at ({want_nose[0]:+.0f},{want_nose[1]:+.0f})"
                )
            rec = model["parts"][fpid_of[ref]]
            if rec.get("cutout_status") != "dimensioned":
                problems.append(
                    f"{ref}: panel cut-out for {fpid_of[ref]} is "
                    f"{rec.get('cutout_status', 'missing')}, so the aperture "
                    f"size is not established"
                )

    for fpid, rec in sorted(model["parts"].items()):
        if rec.get("status") == "scaled":
            notes.append(f"scaled (not dimensioned): {fpid} -- {rec['source'][:110]}")

    for k, why in model.get("unresolved", {}).items():
        if k.startswith("_"):
            continue
        problems.append(f"unresolved panel part: {k} -- {why}")

    for n in notes:
        print(n)
    for p in problems:
        print(p)
    print(
        f"{len(problems)} problem(s)."
        if problems
        else "OK: panels agree with mech.json."
    )
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
