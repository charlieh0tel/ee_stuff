# TODO

- Layout: 4-layer board (decided). The +9V thermal cap (385 mA, θJA ≈
  32.5 °C/W) assumes the TPS7A4701's VQFN pad is stitched to the internal
  ground plane with a via array (≥16 vias); confirm the via count and pour
  once the pad is drawn.

- Layout: `kicad/tbox.kicad_pcb` is the 300 × 270 panel (FRONT 50 /
  CONTROL 130 / REAR 90, two V-scores on the V-CUT layer), 4-layer
  signal/GND/GND/signal, net classes Default/Power/Phones
  (`tools/setup_pcb.py`). Next: in KiCad, Update PCB from Schematic
  (F8) and save, then `tools/place_panel.py` (re)places: panel parts at
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
  - verify the five project footprints in `kicad/tbox.pretty` against the
    current vendor drawings (Switchcraft 35RAPC__H3 rev J, C&K 7000-series
    AV2 and V-bracket patterns, Triad TY-250P 2019-05-31, Same Sky
    SJ-4351X rev 1.06 — the rear pins 3/5 are at y = 10.8 by scaling the
    drawing, not by a dimension; confirm, and cut the 4.5 × 1.3 mm edge
    notch the drawing calls for);
  - C&K PVA button height code (H1–H4) and the light-pipe length for the
    0805 LEDs, both set by the panel-to-board gap found in layout;
  - Bourns 3386 side-adjust style (W chosen; C/H/X share the function) —
    pick whichever puts the screw at the board edge cleanly;
  - NJM4556AM: confirm the DMP8 land pattern against the SOIC-8 assigned;
  - bead MPN: any 0805 bead with ≥50 Ω at 3 MHz (the footprint is fixed);
  - confirm NRJ6HM-1-PRE's "-1" (threaded nose + nut) suffix on ordering.

- Bench: check TRRS mic↔phones crosstalk with a real headset before panel freeze;
  confirm the mute switching step is inaudible at full monitor level;
  measure the power-on hold (~1 s) and the logic highs (≥ 6 V at every
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
