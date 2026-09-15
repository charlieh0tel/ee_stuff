# Check my implementation of option A (panel geometry)

You reviewed the proposal for this on 2026-09-14 and filed
`reviews/2026-09-14-codex-gpt6-astra-panel-proposal-review.md`. **Read that
first** — it is the specification I worked to. I have now implemented it and
I want you to check the implementation, adversarially.

Your corrections that I accepted and applied:

- The Switchcraft axis is **3.00 mm**, not the 5.5 I had. The 0.098 [2,50]
  dimension is terminal projection below the body, not a standoff. You were
  right and my correction of your original number was wrong.
- The rear datum is **53 mm** (the rear drawing's own explicit annotation),
  not the 52 I derived from the side view. I moved the side view's rear board
  line to y=64 so the two agree.
- A is right but an axis-height scalar is not enough; it needs a full
  mechanical model, placement by transformed axis and shoulder, separate
  write and check, and the check must read the actual board.

New data since your review: I fetched both Neutrik dimensioned drawings you
located but could not read (`third_party/datasheets/Neutrik_NRJ6HF-1_drawing.pdf`
and `Neutrik_NRJ6HM-1-PRE_drawing.pdf`). Both give **6.5 mm** axis above the
PCB and an **Ø11.2 mm** panel cut-out. So the front drawing's implied 6 mm was
0.5 mm out and the rear's implied 12 mm was 5.5 mm out. I also read the C&K
AV2 toggle at **6.35 mm** (dimensioned, page F-11), which matches the figure
in your review.

## What I built (commit `74ba649`)

- **`mech.json`** — the shared model. Per board: `pcb_top_below_panel_top`
  (30.0 front, 53.0 rear, both declared to the component-side seating plane;
  control board null/unverified because it is sloped). Per footprint:
  `nose_dir`, `axis_offset`, `panel_face`, `nose_projection`, `axis_height`,
  `axis_height_tol`, `cutout`, plus `status` (`dimensioned` / `scaled` /
  `unverified`) and a `source` string naming the drawing, revision and view.
  An `unresolved` section lists panel parts with no record at all.
- **`tools/mech.py`** — `axis_on_board()` (footprint origin + rotation ->
  axis point, nose direction, panel-face point), `origin_for_axis()` (the
  inverse), `orient_for()`, `hole_y()`. Raises `Unresolved` for a missing
  record, an `unverified` status, or any null required field. No defaults.
- **`tools/gen_panels.py`** — `--write` updates the drawings; the default
  checks the drawings, and separately reads `kicad/tbox.kicad_pcb` and checks
  each part's axis against the panel x it serves and its panel face against
  the board edge (tolerance 0.05 mm on the board, 0.01 mm on the drawings).
  Reports `scaled` values as notes and fails on anything unresolved.
- **`tools/place_panel.py`** — `place_edge()` now sets the rotation from
  `orient_for()` and the position from `origin_for_axis()`, instead of
  centring a bounding box and putting the nearest pad 2 mm inside the edge.
  The old `orient_nose()` heuristic is deleted. The silent top-panel clamp
  `min(190 - py, y1 - 4.0)` is replaced by a reported failure — it now says
  D2118 is 2 mm past the control board's limit.
- **Apertures carry `data-ref="<REF>"`**; `front_positions()` and
  `rear_positions()` were rewritten to key on that instead of sorting circles
  and matching the nearest label.
- `tools/check_placement.py`: `band_of()` now tolerates a panel part whose
  origin lands exactly on the outer board edge, which placing by panel face
  makes normal (the two rear Switchcraft jacks sit at y=270.000).

## Current state

`tools/gen_panels.py` passes on every jack and rear toggle, on both the
drawings and the placed board. It fails on: the five Bourns 3386W trims and
the DE-9 (no record), plus the `unresolved` list. `place_panel.py` reports
those as UNPLACEABLE and leaves them where they were. `check_placement.py`,
`check_footprints.py`, `check_sch.py` pass; DRC is clean apart from the
unrouted ratsnest.

I deliberately left the 3386W unresolved: I could not find a clean dimension
for the side-adjust screw height above the board, and your review warned
against halving the body height because of the 0.38 mm minimum standoff.

## What I want from you

1. **Is the geometry right?** Check `tools/mech.py`'s maths — particularly
   the rotation convention, the `perp = (-nose[1], nose[0])` sign, and
   `origin_for_axis`'s slide. I had the perpendicular sign inverted at first;
   after fixing it, J1001's axis came out 0.80 mm from its hole and J1101's
   0.25 mm, which reproduce your figures exactly. Confirm or refute that
   agreement is meaningful rather than coincidental.
2. **Are the recorded values right?** Every number in `mech.json` against its
   cited drawing: axis heights, axis offsets, panel faces, nose projections,
   cut-outs, and both board datums. I derived the SJ1 and Neutrik axis
   offsets and panel faces from the stock KiCad footprints' F.Fab bushing
   blocks rather than from the vendor drawings — say if that is unsound.
3. **Does the checking actually check?** Try to construct a case each of
   `gen_panels.py` and the new `place_edge()` would wrongly accept. I care
   most about: a part whose record is right but whose footprint is wrong, a
   rotation that satisfies `orient_for` but is physically wrong, flipped
   footprints, and whether the 0.05 mm board tolerance is doing any work.
4. **What did I miss from your specification?** You listed cut-out geometry,
   hardware envelopes, panel thickness, the notch, the toggle throw axis,
   trims, pots, buttons, LEDs, DE-9. Some are recorded as unresolved rather
   than solved. Say which of those I should have solved and did not, versus
   which genuinely cannot be solved without an ordering identity.
5. **Anything now worse than before.** I changed placement for every panel
   part; if that has broken something that used to work, I would rather hear
   it now.

Be concrete and quantitative. Read the files. If the approach is sound but
the execution has bugs, list them with the failing case.
