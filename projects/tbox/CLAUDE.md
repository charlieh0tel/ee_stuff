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
  budgets) placed near each power conversion stage. In tbox
  `tools/gen_power_tree.py` draws it from two sources that never overlap:
  **topology and loads come from the schematic** (converters are parts
  with a `power_in` pin on one rail and a `power_out` pin on another, or
  a `Rail_out` field when the output reaches the rail through a passive
  or a plain output pin; loads are `Load_mA` fields), **capability comes
  from `power_tree.json`** (`max_ma`, its basis, thresholds). Never edit
  the generated block; rerun the generator after touching either source.
- **Load annotation.** Give every current-drawing symbol a `Load_mA`
  field (`"typ"` or `"typ/max"`, in mA) as part of normal schematic
  construction. *typ* is the normal receiving state (powered, nothing
  keyed, no button held); *max* is every load that can be on at once,
  each at its sustained maximum (amplifiers: full-scale sine at clip into
  the rated load). A converter's own quiescent/ground current is just its
  `Load_mA`. `tools/check_power.py` attributes each draw to the rail on
  the part's `power_in` pin and flattens the tree — every load is an
  occurrence on its own rail and on every rail upstream of it (1:1
  through linear stages). Set `Load_rail` only when attribution is
  ambiguous.
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
- `tools/check_sch.py` flags pin ends sitting on the interior of a wire
  or on another symbol's pin without a junction — KiCad silently
  connects those and ERC does not object. Run it (and ERC) after any
  schematic edit.
