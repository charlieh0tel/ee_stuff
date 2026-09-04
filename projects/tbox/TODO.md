# TODO

- Layout: 4-layer board (decided). The +9V thermal cap (385 mA, θJA ≈
  32.5 °C/W) assumes the TPS7A4701's VQFN pad is stitched to the internal
  ground plane with a via array (≥16 vias); confirm the via count and pour
  once the pad is drawn.

- Layout: `kicad/tbox.kicad_pcb` is the 300 × 250 panel (FRONT 50 /
  CONTROL 130 / REAR 70, two V-scores on the V-CUT layer), 4-layer
  signal/GND/GND/signal, net classes Default/Power/Phones
  (`tools/setup_pcb.py`). Next: in KiCad, Update PCB from Schematic
  (F8) and save, then `tools/place_panel.py` puts every part on its own
  board and the panel parts at the drawings' positions; hand layout from
  there. The 22 ribbon nets will show as unrouted between the connector
  pairs — record them as DRC exclusions once. Board-edge notches per jack
  family (different nose-to-board-edge distances) are a layout detail.

- Footprints are assigned (`tools/check_footprints.py` keeps it that way)
  and the chosen parts carry `MPN` fields. Before ordering boards:
  - verify the four project footprints in `kicad/tbox.pretty` against the
    current vendor drawings (Switchcraft 35RAPC__H3 rev J, C&K 7000-series
    AV2 and V-bracket patterns, Triad TY-250P 2019-05-31);
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
