# TBox project conventions

## General

- **DRY — one source of truth.** Don't maintain the same artifact in two
  places (e.g., power tree in both DESIGN.md and the schematic) unless one
  is generated from the other or from a common source. Docs point to the
  authoritative location instead of duplicating it.

## Design process

- Follow the EE design guidelines at
  https://github.com/charlieh0tel/ee-dev-process (read `pcba/` — schematic,
  PCB, library, release, and MCO checklists) for all schematic and layout
  work.

## Schematic and layout

- The power tree lives **in the schematic, generally on its own sheet**,
  drawn as boxes and arrows flowing **left to right** (wrapping to a new
  band when it outgrows the sheet), with load annotations (current
  budgets) placed near each power conversion stage. In tbox it is
  generated from `power_tree.json` by `tools/gen_power_tree.py` — edit
  the json, never the generated block.
- Prefer **SMT construction** — choose SMT packages unless a part is
  panel-mount or SMT is unavailable.

## Documentation

- Design docs: DESIGN.md (architecture/decisions), LEVELS.md (level plan,
  sourced data). Keep them current as the schematic evolves.

## Tooling

- Python scripts: lint and format with **ruff** (`ruff check` and
  `ruff format`) before committing.
