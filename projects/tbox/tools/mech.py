"""Shared mechanical model: where a panel part's axis is, on the board and on the panel.

Reads ``mech.json`` -- the one source of truth for every dimension that ties a
PCB part to a panel aperture -- and turns it into the two questions the tools
ask:

  * `axis_on_board(fp)`  -- where is this footprint's mechanical axis, and
    which way does its nose point, once the footprint is placed and rotated?
  * `hole_y(board, part)` -- what panel y should its aperture sit at?

The model deliberately has no defaults.  A part with no record, or one whose
status is ``unverified``, raises `Unresolved`; callers are expected to turn
that into a failure rather than a guess.  An axis height nobody has read off a
drawing must stop the build, not silently become zero.

See mech.json's ``_frame`` for the coordinate conventions.
"""

import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, "mech.json")


class Unresolved(Exception):
    """A part's mechanical geometry is missing or unverified."""


def load(path=SRC):
    with open(path) as f:
        return json.load(f)


#: what each question needs.  A trimmer reached *through* an aperture has no
#: panel face at all, but its axis height is still what sets the hole.
FOR_HOLE = ("axis_height",)
FOR_PLACING = ("nose_dir", "axis_offset", "panel_face")


def part(model, fpid, need=FOR_PLACING + FOR_HOLE):
    """Mechanical record for a footprint id, or raise Unresolved."""
    p = model["parts"].get(fpid)
    if p is None:
        raise Unresolved(f"{fpid}: no record in mech.json")
    if p.get("status") == "unverified":
        raise Unresolved(f"{fpid}: geometry unverified ({p.get('source', '')[:80]})")
    for k in need:
        if p.get(k) is None:
            raise Unresolved(f"{fpid}: {k} not established")
    return p


def datum(model, board):
    d = model["datums"].get(board)
    if d is None or d.get("pcb_top_below_panel_top") is None:
        raise Unresolved(f"{board}: no PCB-to-panel datum in mech.json")
    return d


def hole_y(model, board, fpid):
    """Panel y of the aperture centre: the PCB datum less the axis height."""
    return (
        datum(model, board)["pcb_top_below_panel_top"]
        - part(model, fpid, FOR_HOLE)["axis_height"]
    )


def _rot(v, deg):
    r = math.radians(deg)
    c, s = math.cos(r), math.sin(r)
    # KiCad rotates footprints counter-clockwise on screen, i.e. negative in
    # this y-down frame
    return (v[0] * c + v[1] * s, -v[0] * s + v[1] * c)


def axis_on_board(model, fpid, pos_mm, rot_deg, flipped=False):
    """-> (axis point in board mm, outward nose direction, panel-face point).

    `pos_mm` is the footprint origin on the board and `rot_deg` its
    orientation, both as pcbnew reports them.
    """
    p = part(model, fpid)
    if flipped:
        # KiCad's Flip() mirrors the footprint's local y at a fixed reported
        # orientation, and a bottom-side part also seats against the board from
        # the other face, so its axis height needs a different vertical
        # transform.  Neither is implemented; refuse rather than answer wrongly.
        raise Unresolved(
            f"{fpid}: on the back of the board -- flipped panel parts are not "
            f"modelled (planar and vertical transforms both differ)"
        )
    nose = tuple(p["nose_dir"])
    # the axis sits `axis_offset` from the origin, perpendicular to the nose:
    # footprint +x when the nose runs along y, footprint +y when along x
    perp = (-nose[1], nose[0])
    off = p["axis_offset"]
    ax_local = (perp[0] * off, perp[1] * off)
    face_local = (
        ax_local[0] + nose[0] * p["panel_face"],
        ax_local[1] + nose[1] * p["panel_face"],
    )
    nose_r = _rot(nose, rot_deg)
    ax = _rot(ax_local, rot_deg)
    face = _rot(face_local, rot_deg)
    return (
        (pos_mm[0] + ax[0], pos_mm[1] + ax[1]),
        nose_r,
        (pos_mm[0] + face[0], pos_mm[1] + face[1]),
    )


def origin_for_axis(model, fpid, axis_xy, face_at, rot_deg, flipped=False):
    """Inverse of `axis_on_board`: the footprint origin that puts the part's
    axis *line* through `axis_xy` and its panel face on the plane `face_at` (a
    board coordinate measured along the nose direction).

    Only the component of `axis_xy` across the nose is used -- sliding along
    the nose is what seats the face, so the returned axis reference point is
    generally not `axis_xy` itself.
    """
    p = part(model, fpid)
    if flipped:
        raise Unresolved(f"{fpid}: flipped panel parts are not modelled")
    nose = tuple(p["nose_dir"])
    perp = (-nose[1], nose[0])
    off = p["axis_offset"]
    ax_local = (perp[0] * off, perp[1] * off)
    ax = _rot(ax_local, rot_deg)
    nose_r = _rot(nose, rot_deg)
    # place the origin so the axis lands on axis_xy, then slide along the nose
    # until the panel face is at face_at
    ox, oy = axis_xy[0] - ax[0], axis_xy[1] - ax[1]
    face_now = (
        ox + ax[0] + nose_r[0] * p["panel_face"],
        oy + ax[1] + nose_r[1] * p["panel_face"],
    )
    # only the component along the nose matters
    if abs(nose_r[0]) > abs(nose_r[1]):
        slide = (face_at - face_now[0]) / nose_r[0]
    else:
        slide = (face_at - face_now[1]) / nose_r[1]
    return (ox + nose_r[0] * slide, oy + nose_r[1] * slide)


def orient_for(model, fpid, want_nose):
    """The footprint rotation that points this part's nose in `want_nose`."""
    p = part(model, fpid)
    for rot in (0, 90, 180, 270):
        n = _rot(tuple(p["nose_dir"]), rot)
        if abs(n[0] - want_nose[0]) < 1e-6 and abs(n[1] - want_nose[1]) < 1e-6:
            return rot
    raise Unresolved(f"{fpid}: nose {p['nose_dir']} cannot face {want_nose}")
