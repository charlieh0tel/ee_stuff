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

- Footprint / MPN assignment pass: no instance has a footprint yet (the
  library defaults are overridden with ""). Includes: J3303 insulated-bushing
  line-out jack, C3312 non-polar 10 µF, HF-effective beads (≥50 Ω at 3 MHz),
  SW2103 on-off-on DPDT, latching mute buttons, dual-gang volume pots.

- Bench: check TRRS mic↔phones crosstalk with a real headset before panel freeze;
  confirm the mute switching step is inaudible at full monitor level;
  measure the power-on hold (~1 s) and the logic highs (≥ 6 V at every
  TS12A12511 IN pin).

- Supply-sheet reference designators are 1-digit (U3103, C3103 …) while the
  other sheets use per-sheet hundreds; renumber with the refdes tooling
  when convenient.

- Line-out transformers T3301/T3302: pick the part (candidate Bourns
  LM-NP-1001-B1L, SMT 600:600) and verify 150 Hz at -10 dBV without
  saturation, driven from ~100 Ω into ≥10 kΩ.

- CI: `tools/check_sch.py` is pure Python and can run in the shared
  workflow today; `tools/check_power.py` and `gen_power_tree.py` need
  `kicad-cli` (KiCad 9) in the runner — a KiCad container job. Until then
  both run locally before commit. Not annotated on purpose: the
  TS12A12511s (µA).
- `Load_rail` split syntax for a part drawing from two rails — nothing
  needs it yet.
