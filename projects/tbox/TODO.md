# TODO

- Layout: 4-layer board (decided). The +9V thermal cap (385 mA, θJA ≈
  32.5 °C/W) assumes the TPS7A4701's VQFN pad is stitched to the internal
  ground plane with a via array (≥16 vias); confirm the via count and pour
  once the pad is drawn.

- Layout: three boards on one snap-apart 4-layer panel (mouse-bites or
  V-score, rails for the fab). Decide one `.kicad_pcb` with DRC
  exclusions for the 22 ribbon nets vs three PCB files from per-board
  netlists. Panel-mount Powerpole clip + 2 wires to J3101. IDC box-header
  footprints for the four ribbon connectors (`Interconnect` FC/CR; keyed, 2×13); the two ribbons are
  straight-through so a single cable part number.

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
