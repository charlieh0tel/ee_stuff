# TBox project conventions

- Follow the EE design guidelines at
  https://github.com/charlieh0tel/ee-dev-process (read `pcba/` — schematic,
  PCB, library, release, and MCO checklists) for all schematic and layout
  work.
- The power tree lives **in the schematic**, with load annotations
  (current budgets) placed near each power conversion stage.
- **DRY — one source of truth.** Don't maintain the same artifact in two
  places (e.g., power tree in both DESIGN.md and the schematic) unless one
  is generated from the other or from a common source. Docs point to the
  authoritative location instead of duplicating it.
- Prefer **SMT construction** — choose SMT packages unless a part is
  panel-mount or SMT is unavailable.
- Design docs: DESIGN.md (architecture/decisions), LEVELS.md (level plan,
  sourced data). Keep them current as the schematic evolves.
