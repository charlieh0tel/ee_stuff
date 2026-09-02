# TODO

- Verify the +9V thermal max (385 mA in `power_tree.json`) against the
  actual layout: it assumes the TPS7A4701's VQFN pad sits on a ground pour
  with vias giving θJA ≈ 32.5 °C/W (Tj 125 °C, Ta 50 °C, 15 V in).
  Recompute once the pour is drawn.

- Footprint / MPN assignment pass: no instance has a footprint yet (the
  library defaults are overridden with ""). Includes: J401 insulated-bushing
  line-out jack, C408 non-polar 10 µF, HF-effective beads (≥50 Ω at 3 MHz),
  SW703 on-off-on DPDT, latching mute buttons, dual-gang volume pots.

- Bench: measure NE5532 clip on the 9 V rail (LEVELS assumes +6 dBV);
  check TRRS mic↔phones crosstalk with a real headset before panel freeze;
  confirm the mute switching step is inaudible at full monitor level;
  measure the power-on hold (~1 s) and the logic highs (≥ 6 V at every
  TS12A12511 IN pin).

- Supply-sheet reference designators are 1-digit (U1, C1 …) while the
  other sheets use per-sheet hundreds; renumber with the refdes tooling
  when convenient.

- Line-out transformers T401/T402: pick the part (candidate Bourns
  LM-NP-1001-B1L, SMT 600:600) and verify 150 Hz at -10 dBV without
  saturation, driven from ~100 Ω into ≥10 kΩ.

- Power budget checking — `tools/check_power.py` exists (extracts `Load_mA`
  per rail via the netlist, alerts at `alert_utilization`, exits nonzero on
  OVER). Remaining:
  - `Load_mA` is annotated on every op-amp and LED dropper (supply, TX
    bus, RX+Phones, Keying). Still unannotated: the preamp op-amps and the TS12A12511s
    (U201/U202, U301/U302 — the preamp sheet predates the convention),
    electret bias and VREF draws.
  - `--update`: sync `power_tree.json` from the extracted loads and
    regenerate the tree sheet (needs a per-load ref linkage first; the json
    `loads` list is still freeform functional groupings, so the current
    reconciliation is advisory-only).
  - Wire `check_power.py` into CI so a schematic edit that blows a budget
    fails the build.
