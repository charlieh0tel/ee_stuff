# TODO

- Layout: 4-layer board (decided). The +9V thermal cap (385 mA, θJA ≈
  32.5 °C/W) assumes the TPS7A4701's VQFN pad is stitched to the internal
  ground plane with a via array (≥16 vias); confirm the via count and pour
  once the pad is drawn.

- Layout: `kicad/tbox.kicad_pcb` is the 300 × 270 panel (FRONT 50 /
  CONTROL 130 / REAR 90, two V-scores on the V-CUT layer), 4-layer
  signal/GND/GND/signal, net classes Default/Power/Phones
  (`tools/setup_pcb.py`). `tools/sync_pcb.py` is Update PCB from
  Schematic without the GUI (the F8 step is gone), then
  `tools/place_panel.py` (re)places: panel parts at
  the drawings' positions (front, rear and top panels), ribbon headers in
  gaps between them, everything else clustered by sub-sheet and then
  pulled toward its connections for a few passes (ratsnest star length
  ~17 m → ~11.8 m); `tools/place_decoupling.py` then parks every 100n
  against its IC's V+ pin (≤ 4 mm, shoving stray passives aside) and the
  bulk caps beside the hungriest ICs. Neither orients ICs nor reserves
  the regulator's thermal pour; hand layout from there. The 22 ribbon
  nets will show as unrouted between the connector pairs — record them
  as DRC exclusions once. Placement tool run: panel
  parts sit with their pads 2 mm inside the panel edge; each family's
  true panel-face offset (Switchcraft: panel surface at the footprint's
  y = 0; Neutrik/CUI/DSUB: per datasheet) sets where the board edge or
  its notch goes — settle per family in hand layout. The rear board's
  starting spread overflows its region by ~15 mm (transformers, supply
  electrolytics); the remaining DRC overlaps are that.

- Footprints are assigned (`tools/check_footprints.py` keeps it that way)
  and the chosen parts carry `MPN` fields. Before ordering boards:
  - **two of the five project footprints were rebuilt on 2026-09-11** after
    the third review: `Jack_3.5mm_Switchcraft_35RAPCxxH3_Horizontal` and
    `Jack_3.5mm_CUI_SJ-43514_Horizontal` were both **mirrored**, and the
    Switchcraft one additionally had 4.00/4.50 swapped between pins 4 and 5
    and all five 1.75 x 0.75 slots turned 90 degrees. Both vendor views are
    TOP views with the panel/PCB edge at the left, so they map into a
    footprint whose body runs along +y by a 90 degree CLOCKWISE page
    rotation: pins above the drawing axis go to POSITIVE x. **Audit the
    other three the same way** (C&K 7000-series AV2 and V-bracket, Triad
    TY-250P 2019-05-31) — two of two checked were wrong, so assume the
    rest are until shown otherwise. Still unconfirmed on the SJ-43514:
    the rear pins 3/5 are at y = 10.8 by scaling the drawing, not by a
    dimension (2.90 and 7.90 are dimensioned, 10.8 is not). The
    4.5 x 1.3 mm edge notch is now cut by `setup_pcb.py`. **1:1 print
    check passed 2026-09-12** on both rebuilt patterns; if that check
    seated a real jack it also settles the scaled 10.8 above;
  - C&K PVA ordering code: the `xxxxxx` in `PVA1OAH2xxxxxxV2` /
    `PVA1EEH2xxxxxxV2` is the actuator height/style, set by the
    top-panel-to-control-board gap (the enclosure decision); the
    light-pipe length for the 0805 LEDs comes from the same gap;
  - Bourns 3386 side-adjust style (W chosen; C/H/X share the function) —
    pick whichever puts the screw at the board edge cleanly;
  - NJM4556AM: confirm the DMP8 land pattern against the SOIC-8 assigned;
  - decoupling ownership: `place_decoupling.py` infers it (converter first,
    then schematic proximity); C2501 (ADP7142 input 4u7) still lands at the
    TPS7A4701 — move by hand or give caps a `Decouples` field if this
    keeps mattering;
  - confirm NRJ6HM-1-PRE's "-1" (threaded nose + nut) suffix on ordering;
  - OPA1622 (Texas_DRC0010J) land pattern and thermal-via count; SP724
    pinout against the Littelfuse drawing (1/3/4/6 inputs, 2 V-, 5 V+);
    TPS3808G01 divider values against the final +9 V threshold.

- Bench (review 2026-09-08 follow-ups): measure an Icom hand mic
  (HM-36/HM-219) at 94 dB SPL with 8 V through 2k2, into 600 Ω and open,
  and fill the LEVELS.md row; mute fade — listen at full monitor level
  for the residual click, trim R1203/C1202 (fade) and R1204/C1203
  (switch delay) if needed. The fade's audible character still needs
  measuring: 47 ms is an electrical time constant, and the audible part
  is the few ms where the shunt resistance passes through something
  comparable to the 220R, which these very low-R_DS devices cross
  quickly. Check both the mute and the unmute transition, and confirm
  the switch reconnects before the shunt lets go. Also confirm the
  TS12A12511's actual logic trip point at 9 V, which the datasheet
  bounds only as 0.8 V low / 5 V high at 12 V; the switch delay is
  designed so that even the earliest trip finds the shunt conducting.
  Phones power-up with
  headphones plugged, volume at zero and maximum — the 1k Vref
  precharge (R2425–R2428) should leave no step at enable, and the
  disabled OPA1622 output must tolerate the 4.5 mA it can supply;
  supervisor threshold and hold (7.5 V, ~1.3 s)
  on a slow ramp, rapid cycling and a brown-out — rig PTT must stay
  released throughout; headphone amp temperature with both ears into
  16 Ω at full level.
- **Panel geometry: what `mech.json` still cannot answer.** The jacks and
  the rear toggles are resolved and `tools/gen_panels.py` passes on them.
  Still blocking a clean run, each for want of an ordering identity or a
  dimensioned drawing: the Bourns 3386W trims (side-adjust screw height
  above the board is not cleanly dimensioned -- the 0.38 mm minimum
  standoff means halving the body height is wrong), the DE-9 (no MPN, so
  no shell cut-out, centre height or jackscrew pattern; the drawing's
  40 mm fixing holes are unverified), the C&K PVA buttons (`xxxxxx` in
  the ordering code is the actuator height/style), the LED light pipes
  (none selected), the Alpha pots (shaft/bushing/nut stack unrecorded)
  and the panel-mount Powerpole and GND post. Also unresolved: panel
  thickness, which gates nut engagement everywhere; the control board's
  own board-to-panel transform, since it is sloped and a single scalar
  does not describe it; and every cut-out diameter except the Neutriks'
  dimensioned 11.2 mm. Two values are `scaled` rather than dimensioned
  and want confirming on real parts: the Switchcraft 3.00 mm axis height
  (both source dimensions are REF) and the C&K AV2 panel face.
- **D2118 has nowhere to go.** `panel-top.svg` puts the power LED at
  y=12, which is board y=178, past the control board's 176 mm limit. The
  placer used to clamp this silently; it now reports it and fails.
- **Deferred decision: input PTC and the rail budget.** RAW_13V8 sits at
  92% of its 400 mA cap (1812L050/60 hold at 50 C). Candidate swap is
  **1812L075/33**: 0.60 A at 50 C, Vmax 33 V (above the SMBJ18A's 29.2 V
  clamp, unlike the 24 V variant), Imax 20 A (vs 10 A, which also bears
  on the fault-current question below), and lower series resistance,
  0.110 vs 0.150 ohm. Costs a higher trip current, 1.5 A, against the
  1.4 A rating of the BLM21PG601 downstream. Separately, +9V is at 83%
  against the TPS7A4701's 385 mA thermal cap; that is driven by the two
  OPA1622 at 101 mA each, a continuous-sine-at-clip worst case rather
  than an operating state, and the 385 mA itself assumes the unverified
  pad/via implementation. Decide the PTC and whether to re-state the
  amplifier maximum. A smaller lever: the three mute buffer pull-ups at
  4k7 instead of 2k2 save ~6 mA.
- Supply source envelope is a bench/rig PSU or rig accessory jack
  (DESIGN.md). If the box ever goes mobile: fuse instead of the PTC,
  SMCJ-class TVS, pulse-rated bead, and the reverse Schottky's surge
  rating revisited.
- Bench: check TRRS mic↔phones crosstalk with a real headset before panel freeze;
  confirm the mute switching step is inaudible at full monitor level;
  measure the power-on hold (~1.3 s) and the logic highs (≥ 6 V at every
  TS12A12511 IN pin).

- Line-out transformers T3301/T3302 are Triad TY-250P (20 Hz–20 kHz,
  +13 dBm); bench: confirm 200 Hz at -10 dBV without visible distortion,
  driven from ~166 Ω into ≥10 kΩ, and that the ~2.8 dB insertion loss is
  absorbed by the line trims.

- CI: `tools/check_sch.py` is pure Python and can run in the shared
  workflow today; `tools/check_power.py` and `gen_power_tree.py` need
  `kicad-cli` (KiCad 9) in the runner — a KiCad container job. Until then
  both run locally before commit. Not annotated on purpose: the
  TS12A12511s (µA).
- `Load_rail` split syntax for a part drawing from two rails — nothing
  needs it yet.
