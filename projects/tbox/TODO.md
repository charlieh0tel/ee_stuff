# TODO

- Layout: 4-layer board (decided). The +9V thermal cap (385 mA, θJA ≈
  32.5 °C/W) assumes the TPS7A4701's VQFN pad is stitched to the internal
  ground plane with a via array (≥16 vias); confirm the via count and pour
  once the pad is drawn.

- Footprint / MPN assignment pass: no instance has a footprint yet (the
  library defaults are overridden with ""). Includes: J401 insulated-bushing
  line-out jack, C408 non-polar 10 µF, HF-effective beads (≥50 Ω at 3 MHz),
  SW703 on-off-on DPDT, latching mute buttons, dual-gang volume pots.

- Bench: check TRRS mic↔phones crosstalk with a real headset before panel freeze;
  confirm the mute switching step is inaudible at full monitor level;
  measure the power-on hold (~1 s) and the logic highs (≥ 6 V at every
  TS12A12511 IN pin).

- Supply-sheet reference designators are 1-digit (U1, C1 …) while the
  other sheets use per-sheet hundreds; renumber with the refdes tooling
  when convenient.

- Line-out transformers T401/T402: pick the part (candidate Bourns
  LM-NP-1001-B1L, SMT 600:600) and verify 150 Hz at -10 dBV without
  saturation, driven from ~100 Ω into ≥10 kΩ.

- CI: `tools/check_sch.py` is pure Python and can run in the shared
  workflow today; `tools/check_power.py` and `gen_power_tree.py` need
  `kicad-cli` (KiCad 9) in the runner — a KiCad container job. Until then
  both run locally before commit. Not annotated on purpose: the
  TS12A12511s (µA).
- `Load_rail` split syntax for a part drawing from two rails — nothing
  needs it yet.
