# TODO

- Make `tools/gen_power_tree.py` idempotent: derive element UUIDs
  deterministically from content (e.g. `uuid.uuid5(namespace, element_text)`)
  instead of `uuid.uuid4()`, so regenerating an unchanged power tree produces
  a zero diff in `powertree.kicad_sch`, `supply.kicad_sch`, and
  `power_tree_gen.json`.
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
