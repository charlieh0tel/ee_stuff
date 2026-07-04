# TODO

- Make `tools/gen_power_tree.py` idempotent: derive element UUIDs
  deterministically from content (e.g. `uuid.uuid5(namespace, element_text)`)
  instead of `uuid.uuid4()`, so regenerating an unchanged power tree produces
  a zero diff in `powertree.kicad_sch`, `supply.kicad_sch`, and
  `power_tree_gen.json`.
