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
- **Consider capacitive loading on the output of every device with a
  feedback loop** — op-amps, LDOs, switch-mode regulators, etc. Op-amps
  driving capacitance need compensation (e.g., series isolation R; see TI
  "Do-it-yourself: Three Ways to Stabilize Op Amp Capacitive Loads",
  https://www.ti.com/lit/ta/sszt999/sszt999.pdf). Alternatively, some
  op-amps are designed to drive high capacitive loads directly (e.g.
  LM8261, OPA994, ADA4870; see TI "Unlimited Capacitive Load Drive Op
  Amp Takes Guesswork Out Of Design",
  https://www.ti.com/lit/an/snoa808/snoa808.pdf). Regulators need output
  caps inside their datasheet capacitance/ESR stability window.

## Documentation

- Design docs: DESIGN.md (architecture/decisions), LEVELS.md (level plan,
  sourced data). Keep them current as the schematic evolves.

## Tooling

- Python scripts: lint and format with **ruff** (`ruff check` and
  `ruff format`) before committing.
