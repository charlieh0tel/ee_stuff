# TODO

- Verify the +9V thermal max (250 mA in `power_tree.json`) against the
  actual layout: it assumes the LM2940 TO-263 sits on a copper pour giving
  θJA ≈ 50 °C/W (Tj 125 °C, Ta 50 °C, 15 V in). Recompute once the pour is
  drawn.

- Power budget checking (`tools/check_power.py`). Split the data by where
  the truth is:
  - **Supply capability** is design analysis and lives in `power_tree.json`:
    each converter node gets `max_ma` + `max_basis` (rated current, or the
    thermal limit where that binds first — e.g. LM2940 at 15V in / 9V out is
    package-Pd-limited well below its 1A rating). Computed when the stage is
    designed; the generator prints it on the tree sheet next to the budget.
  - **Actual loads** live in the schematic: each load-drawing symbol gets a
    `Load_mA` custom field (typ/max) as part of normal schematic
    construction; the checker walks each rail net and sums per rail.
  - The checker reconciles the two: reports drift between extracted loads
    and the `loads` list in `power_tree.json` (missing/extra/changed), with
    `--update` to sync the json from the schematic and regenerate the tree
    sheet; and alerts when a rail's extracted total reaches 75% of `max_ma`
    (threshold configurable in the json). Run it in CI so a schematic edit
    that blows a budget fails the build.
