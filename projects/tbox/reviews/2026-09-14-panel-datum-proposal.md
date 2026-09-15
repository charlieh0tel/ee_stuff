# Proposal under review: fixing the TBox panel hole heights

**Proposal only. Nothing in the repository has been changed.** I want you to
confirm or refute the analysis and the chosen option before I implement it.

You reviewed this project from scratch on 2026-09-10 and filed
`reviews/2026-09-10-codex-gpt6-astra-from-scratch.md`. Its finding 2 was a
BLOCKER: "The panel drawings cannot accommodate the selected jacks on a
common horizontal PCB." This is my working-out of that finding and my
proposed fix. **Read your own earlier report for this one** — unlike the
from-scratch pass, here I want continuity.

Since that review, blocker 1 (mirrored jack footprints) is fixed: both
custom footprints were rebuilt from the vendor top views and verified by
the user against real parts with a 1:1 print. Findings 4, 5 and 6 (the
mute cell and the supervisor pull-up) are also fixed. Everything else from
your report is still open.

## My analysis of the geometry

From `panel-side.svg`: the enclosure is a wedge, front-bottom (0,90),
rear-bottom (146,90), rear-top (146,11), front-top (0,45), so the front
apron runs from y=45 down to y=90 (45 mm) and the rear panel from y=11 to
y=90 (79 mm). The front board is drawn as a horizontal line at y=75, the
rear board at y=63.

`panel-front.svg` measures y downward from the apron top, so:

- front board surface sits at panel-front y = 75 - 45 = **30 mm**
- a jack's hole centre should therefore be at **y = 30 - (axis height
  above the board)**

`panel-rear.svg` measures y downward from the rear panel top, so:

- rear board surface sits at panel-rear y = 63 - 11 = **52 mm**
- hole centre = **y = 52 - (axis height)**

### What the drawings assert

Every one of the ten front jacks is drawn at `cy="24"`, i.e. the drawing
asserts a 6 mm axis height for all of them. The rear drawing does vary by
family: `<use href="#j14" x="16" y="41"/>` and `<use href="#j35" x="35"
y="47"/>`, asserting 11 mm for the 1/4" and 5 mm for the 3.5 mm.

### What the parts require

Read off the vendor drawings in `third_party/datasheets/`:

| Jack | Axis above PCB | Source |
|---|---|---|
| Same Sky SJ-43514 TRRS | 2.25 mm ±0.2 | `SameSky_SJ-4351X.pdf` side view |
| Switchcraft 35RAPC | about 5.5 mm | `Switchcraft_35RAPC__H3_drawing.pdf` front view: body 6.00 tall centred on the axis, body bottom 2.50 above the PCB |
| Same Sky SJ1-3533NG | 7.0 mm | `SameSky_SJ1-353xNG.pdf` |
| Neutrik NRJ6HF-1 / NRJ6HM-1-PRE | **not established** | the PDFs in the repo are the web spec sheets with no dimensioned drawing |

So on the front panel: TRRS holes are out by 3.75 mm, the Switchcraft by
0.5 mm, the SJ1-3533NG by 1.0 mm. The TRRS hole is 3.6 mm in diameter for
a 3.5 mm bushing, so a 3.75 mm error means hole and bushing do not overlap
at all.

Two further inconsistencies I found:

1. The front drawing asserts 6 mm for the Neutrik 1/4" while the rear
   drawing asserts 11 mm for the same jack. Both cannot be right.
2. `DESIGN.md` around line 362 already states the requirement correctly
   ("Each family puts its centre at a different height above the board, so
   panel holes sit at per-part heights along one row"). The front drawing
   does not implement what the document says.

`front_positions()` in `tools/place_panel.py` reads only the x coordinates
out of the drawing; the y coordinate is never read by any tool, so this
cannot fail a check today.

## The options I put to the user

- **A (the user chose this, and it is what I want you to confirm):**
  record each footprint's axis height in the datum table `place_panel.py`
  already keeps (it currently holds operator-datum offsets for pot shafts
  and button plungers), fix one PCB-to-panel datum per board, compute
  every hole centre from those two numbers, correct both drawings from the
  computed values, and add a checker that fails when a drawn hole
  disagrees with the computed one.
- **B:** hand-correct the `cy` values and add the cross-check without the
  generator.
- **C:** re-select jacks so the families share an axis height.

## What I want from you

1. **Is my geometry right?** Check the numbers above against the actual
   files and datasheets. In particular check the 30 mm and 52 mm board
   heights, the per-part axis heights, and whether I have the sign or the
   reference surface wrong anywhere. I could not settle whether the board
   lines in `panel-side.svg` are the top surface or the underside of the
   1.6 mm board; that matters at the same scale as the errors.
2. **Is A the right option?** Say so plainly if B or C is better, or if A
   is right but incomplete. I am not attached to it.
3. **If A, what exactly should it cover?** Be concrete about: where the
   axis height belongs (a per-footprint table in the tool, a field in the
   schematic symbol, a separate data file); what the PCB-to-panel datum
   should be measured to; whether the tool should rewrite the SVGs or only
   check them; what the checker's tolerance should be; and what else in
   the same class this should cover that I have not thought of (panel
   cut-outs for the pots, switches, LEDs and the DE-9, the toggle throw
   axis from your finding 14, panel thickness and nut/shoulder clearance,
   the board-edge inset the placer uses, the SJ-43514 edge notch).
4. **What would still be unverified after A is done?** I know the Neutrik
   axis height needs its real drawing. What else?

Be concrete and quantitative. Give values, not directions. If you think
the whole approach of deriving the panel from the parts is wrong for this
project, say that instead.

You have read-only access to the repository, including the panel SVGs, the
tools, `DESIGN.md`, and the vendor datasheets.
