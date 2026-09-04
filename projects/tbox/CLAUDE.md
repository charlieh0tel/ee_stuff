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

- **The hierarchy mirrors the boards.** The root sheet holds one sheet
  per PCB (Front, Control, Rear) plus the Power Tree; functional
  sub-sheets live under their board. Wires on the root are the ribbon
  cables. A net that crosses boards is a hierarchical label threaded
  through sheet pins and a ribbon-connector pin on each board — never a
  global label (rails on power symbols and `CHASSIS` excepted).
  Ribbon connectors carry an `Interconnect` field naming their cable
  (`FC`, `CR`); `tools/check_boards.py` enforces all of this and checks
  both ends of each ribbon pin for pin; run it with `check_sch.py`
  after any edit. The Harness sheet is generated from the netlist by
  `tools/gen_harness.py` — rerun it after any change to a ribbon pin.
- **Reference designators encode the board**: sheets are numbered
  1x (front), 2x (control), 3x (rear) and annotation uses "first free
  after sheet number × 100", so `U1101` is board 1, sheet 11. Renumber
  with KiCad's annotator, never by hand.

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
- **Power symbols point the way current flows**: every GND symbol points
  down, every rail symbol (+9V, etc.) points up — never rotated to fit a
  wire. Where a connector has many GND or rail pins, collect them on a
  short rail and end it in a single, correctly oriented symbol.
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
- Layout lives in `kicad/tbox.kicad_pcb`, one panel with all three boards.
  `tools/setup_pcb.py` owns the outline, V-cuts, stack-up and labels (the
  "panel-frame" group — never hand-edit those, rerun the script);
  `tools/place_panel.py` places parts onto their board from the schematic
  sheet path and panel parts from `panel-*.svg`. Footprints enter the
  board only through KiCad's Update PCB from Schematic.
- `tools/check_footprints.py` fails on any board part without a footprint
  that exists (stock library or `kicad/tbox.pretty`); panel-only parts are
  `on_board no`. Every part with a specific vendor choice carries an
  `MPN` field — the BOM comes from the schematic, not a spreadsheet.
- `tools/check_sch.py` flags pin ends sitting on the interior of a wire
  or on another symbol's pin without a junction — KiCad silently
  connects those and ERC does not object. Run it (and ERC) after any
  schematic edit.
