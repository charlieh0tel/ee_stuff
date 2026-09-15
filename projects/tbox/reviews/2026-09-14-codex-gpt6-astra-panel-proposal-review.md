**Choose A, with a broader mechanical datum model. Your sign convention is correct, but the analysis contains two important errors: the Switchcraft height is approximately 3.0 mm, and the rear-board datum conflicts between drawings.** The SVG socket openings also must not be treated as panel drilling diameters.

I reread [the earlier review](/home/ch/src/ee_stuff/projects/tbox/reviews/2026-09-10-codex-gpt6-astra-from-scratch.md), inspected the dimensioned vendor pages, and checked the current placement code and embedded PCB footprints. No files were changed.

## 1. Geometry: what is correct, and what needs correction

### Board datums and sign

Your equation is correct **when both dimensions reference the PCB’s component-side seating surface**:

\[
y_{\text{hole}}=y_{\text{PCB top}}-h_{\text{axis}}
\]

A taller jack therefore needs a hole **higher** on the panel, at a smaller SVG y coordinate.

The drawings disagree about the rear board:

| Source | Front PCB datum below panel top | Rear PCB datum below panel top |
|---|---:|---:|
| Side-view board lines, interpreted as PCB top | \(75-45=\mathbf{30.00}\) mm | \(63-11=\mathbf{52.00}\) mm |
| Rear-view explicit annotation and dashed line | — | **53.00 mm**, explicitly PCB **top**, 26 mm above floor |

The [side view](/home/ch/src/ee_stuff/projects/tbox/panel-side.svg:43) does **not** identify top versus underside. Its 0.7 mm dashed stroke is a drawing convention, not board thickness. The [rear view](/home/ch/src/ee_stuff/projects/tbox/panel-rear.svg:57) is explicit. Thus:

- **30 mm:** correct arithmetic, conditional on declaring the front line to represent PCB top.
- **52 mm:** correct side-view arithmetic, but not a consistent project datum.
- **53 mm:** the better-supported rear design intent; it agrees with `DESIGN.md`’s approximately 26 mm above the floor.

If the side-view lines represented the **undersides** of 1.6 mm boards, the component-side datums would instead be **28.40 mm front and 50.40 mm rear**. You subtract 1.6 mm, because the top surface is higher.

**My recommendation:** adopt **30.00 mm front and 53.00 mm rear**, explicitly measured to PCB top. Keep the front top at side-view y=75; move the rear top to **y=64**. Draw the undersides at **76.60 and 65.60**, respectively. These are proposed nominal assembly datums, still subject to the enclosure-clearance check.

### Jack heights

| Part | Supported axis height above seating surface | Assessment |
|---|---:|---|
| SJ-43514 | **2.25 ±0.20 mm** | Correct; dimension appears in the front elevation on PDF p. 2. |
| Switchcraft 35RAPC…H3 | **approximately 3.00 mm** | Your 5.5 mm interpretation is incorrect. |
| SJ1-3533NG | **7.00 ±0.15 mm** | Correct; explicit dimension on PDF p. 2. |
| Both Neutrik variants | **Unestablished from repository PDFs** | Keep separate, unresolved records. |

The Switchcraft **2.50 mm dimension runs from the body bottom to the terminal tips**. It is terminal projection, not a standoff above the PCB. Adding it to half the 6.00 mm body height measures to the pin tips, not the PCB surface.

Consequently, my earlier report’s **approximately 3.0 mm** remains the supported interpretation. However, the 6.00 mm dimension is marked **REF**, and axis-to-seating-plane height is not directly toleranced. Record **3.00 mm as provisional**, without inventing a ± tolerance. Confirm seating height on an actual mounted part or with Switchcraft. See the [repository drawing](/home/ch/src/ee_stuff/projects/tbox/third_party/datasheets/Switchcraft_35RAPC__H3_drawing.pdf).

### Corrected hole centres

Using the recommended **30.00 mm front datum**:

| Front family | Panel x coordinates | Required nominal y | Change from current y=24 |
|---|---|---:|---:|
| Switchcraft | 55, 245 | **≈27.00** | **3.00 mm down** |
| SJ-43514 TRRS | 75, 225 | **27.75** | **3.75 mm down** |
| SJ1-3533NG phones | 95, 205 | **23.00** | **1.00 mm up** |
| Neutrik | 30, 120, 180, 270 | **30.00 − verified height** | Pending |

For the rear:

| Rear family | Current y | Required with datum 52 | Required with recommended datum 53 |
|---|---:|---:|---:|
| Switchcraft PTT, x=35/265 | 47 | ≈49.00 | **≈50.00** |
| SJ1 line out, x=126 | 47 | 45.00 | **46.00** |
| Neutrik PTT, x=16/284 | 41 | \(52-h\) | **\(53-h\)** |

Thus the rear drawing explicitly implies **12 mm** for its Neutrik jacks and **6 mm** for its shared 3.5 mm graphic. Your **11/5 mm** values arise only from substituting the conflicting side-view datum.

Your same-Neutrik-family inconsistency is valid. So is the disagreement with [DESIGN.md](/home/ch/src/ee_stuff/projects/tbox/DESIGN.md:357).

### The “3.5 mm bushing” argument needs correction

The SJ-43514 drawing specifies:

- **Ø3.5 mm mating plug**
- **Ø3.6 mm socket opening**
- **Ø6.00 mm external nose**

The Switchcraft has an **M6×0.5 external thread**, and the SJ1 also has a **Ø6.00 mm external nose**. Sources: [SJ-43514 drawing](/home/ch/src/ee_stuff/projects/tbox/third_party/datasheets/SameSky_SJ-4351X.pdf), [SJ1 drawing](/home/ch/src/ee_stuff/projects/tbox/third_party/datasheets/SameSky_SJ1-353xNG.pdf).

The SVG’s black Ø3.6 circles therefore plausibly depict **socket mouths**, not enclosure cut-outs. If intended as cut-outs, they are undersized even with perfectly aligned centres.

The **3.75 mm displacement remains fatal to the intended alignment**. But “the hole and bushing do not overlap” uses the wrong bushing diameter; overlap is also weaker than the required condition that the passing part fit entirely inside the aperture.

## 2. A is the right option

**A is right, but adding only an axis-height scalar is incomplete.**

B could correct today’s centres, but leaves unnecessary manual maintenance once a shared model exists. C is not justified: the selected families can use different heights on one horizontal board. Reselect only if the complete assembly reveals an actual clearance, mounting, or reach conflict.

The right relationship is:

> Panel layout supplies desired operator positions; verified part geometry and board mounting datums determine the corresponding PCB placement and panel apertures.

## 3. What A should cover

### Shared data, keyed by part and footprint

I recommend a **separate shared mechanical data file**, consumed by the placer, panel generator/checker, and board-outline generator. Move the existing `DATUM` entries there.

Use the **full footprint identifier plus supported MPN/variant**. A footprint alone cannot distinguish parts with identical pins but different shafts, brackets, or bushing lengths.

Include:

- Local operator-axis position and direction.
- Height above the seating plane, with tolerance.
- Panel-facing shoulder position and nose projection.
- Required mounting rotation and toggle movement direction.
- Cut-out geometry, mounting holes, notch geometry.
- Hardware envelope and permitted panel-thickness stack.
- Source drawing/revision/page and verification status.

The schematic should retain **part identity and footprint selection**, not duplicate dimensional values. Unknown geometry must produce an explicit unresolved result; no default height of zero.

### PCB-to-panel datum

Use the **component-side PCB seating plane**, not pin tips, underside, courtyard, or footprint origin.

For front/rear panels, store **30.00/53.00 mm below their top edges**. Separately define:

- Panel inner and outer faces, and thickness.
- PCB edge position relative to the **inner face**.
- Floor inner surface and board supports.

If the drawing’s bottom edge is the enclosure’s exterior floor datum, the required standoff lengths are:

\[
L_{\text{front}}=13.40-t_{\text{floor}},\qquad
L_{\text{rear}}=24.40-t_{\text{floor}}
\]

All dimensions are millimetres. These become **13.40/24.40 mm** only when the reference floor is already its inside surface.

For the control board, measure separation **normal to the sloped panel**, with its own board-to-panel transform.

### Replace the pad-edge and courtyard heuristics

[Current placement](/home/ch/src/ee_stuff/projects/tbox/tools/place_panel.py:310) centres the footprint’s bounding box and positions its nearest **pad boundary** 2 mm inside the board edge. Neither locates the connector’s mechanical axis or shoulder.

Current PCB examples:

| Part | Actual issue |
|---|---|
| J1101 Switchcraft | Axis is at PCB x=244.75 rather than 245.00: **0.25 mm sideways error**. Its shoulder is **0.85 mm inside** the board edge. |
| J1001 SJ1 | Local axis offset is +0.90 mm; placed axis is x=205.80 rather than 205.00: **0.80 mm sideways error**. Its shoulder is **1.70 mm inside** the edge. |
| J1103 TRRS | Axis is x=224.9125 rather than 225.00; body-front datum is **0.05 mm inside** the edge. |

These cannot establish a common panel mating plane.

**Place by transformed axis and shoulder coordinates.** Keep pad-to-edge clearance as a separate constraint; changing pad dimensions must not move a panel connector.

### Generate explicitly; check without writing

Provide two operations:

- **`--write`**: update generated mechanical geometry in the SVGs.
- **`--check`**: compare existing SVGs and the actual PCB against expected geometry, without writing.

Use stable reference-based IDs, such as `J1103-cutout`, instead of matching sorted circles or nearby labels. Separate actual cut-outs from illustrated nuts, socket openings, knobs and legends.

Cover **all four SVGs**, including board planes and dimensions in the side view. Preserve hand-authored artwork outside generated groups.

The checker must inspect the **actual placed PCB**, not merely regenerate expected SVG values from the same inputs. Otherwise a moved footprint can still pass.

### Checker tolerance

Use **0.01 mm absolute tolerance** for nominal coordinate and dimension agreement. Use **0.1°** for orientation agreement.

These are file-consistency tolerances. Physical fit needs a separate tolerance stack:

\[
D_{\text{hole,min}}\ge D_{\text{passing part,max}}+2e_{\max}
\]

Here \(e_{\max}\) includes part-axis variation, assembly placement, panel drilling, and board mounting error.

For example, a **6.40 mm minimum hole** around a **6.10 mm maximum TRRS nose** leaves only **0.15 mm radial allowance**—less than the part’s **±0.20 mm axis-height tolerance alone**. Software agreement within 0.01 mm does not make that fit acceptable.

### Other components and constraints

| Item | Required coverage |
|---|---|
| **Rear toggles** | Axis, shoulder, mounting hole, hardware and throw direction. The selected AV2 drawing gives **6.35 mm axis height**, hence **y=46.65** with the 53 mm datum; current y=46 is 0.65 mm high. |
| **Rear trims** | Screwdriver access axis, tool envelope and recess depth. The 3386W drawing includes **0.38 mm minimum stand-off**, so establish actual seating rather than blindly halving body height. |
| **Top pots** | Retain verified local shaft offsets; add shoulder height, bushing/thread length, shaft projection, nut/washer stack and antirotation features. Knob diameter is not cut-out diameter. |
| **Buttons** | Exact actuator/cap variant, aperture, released/pressed/latching heights and full travel. Existing `xxxxxx` ordering placeholders cannot establish these. |
| **LEDs** | Selected light-pipe aperture, optical centre, length and retention—not just the SMD LED origin. |
| **DE-9** | Exact selected connector, shell cut-out, centre height, mating plane and jackscrew holes. J3206 has no MPN. The SVG draws fixing holes **40 mm apart**; that is not a verified mounting pattern. |
| **Powerpole/GND post** | Panel-only mounting geometry and hardware still need records, even though no PCB-height equation applies. |

There is already a useful top-panel checker counterexample: **PWR is drawn at y=10**, `TOP` says **12**, and the placement clamp produces effective panel **y=14**. That is a **4 mm mismatch**. Remove the silent clamp and report an impossible placement.

For finding 14, require SW2103’s throw axis to project **left/right**: **90° or 270°**, rather than current 0°. Also verify which contact pair closes for each direction; axis alignment alone cannot validate the legends.

### Thickness, reach and hardware

Store actual hardware stacks. Known nominal projections are:

- TRRS nose: **3.00 mm**
- Switchcraft threaded nose: **3.50 mm**
- SJ1 nose: **4.00 mm**

Subtract shoulder-to-inner-panel gap and panel thickness to obtain external projection; then check plug seating, washers and nut engagement.

There is a similar control-board issue: interpreting its side-view line as PCB top gives approximately **17.4–17.7 mm normal distance to the top panel**. The V6 toggle drawing gives **11.68 mm shoulder height plus 6.86 mm bushing**, or **18.54 mm total**. Only approximately **0.9–1.1 mm** would extend beyond that drawn panel surface. Nut engagement is therefore unestablished. [C&K drawing, printed F-13](/home/ch/src/ee_stuff/projects/tbox/third_party/datasheets/CK_7000-series_toggles.pdf).

Neutrik specifies panel thickness **<3 mm** for both selected variants; mounting hardware is ordered separately. That limit does not verify the chosen washer/nut assembly. [HF product data](https://www.neutrik.com/en/product/nrj6hf-1), [HM product data](https://www.neutrik.com/en/product/nrj6hm-1-pre).

### SJ-43514 notch

This is **already implemented**: [setup_pcb.py](/home/ch/src/ee_stuff/projects/tbox/tools/setup_pcb.py:142) creates **4.50 mm wide × 1.30 mm deep** notches, and they exist in the current PCB.

A should verify:

- Their position relative to the transformed jack datum.
- Width, depth and fabrication corner radii.
- Actual `Edge.Cuts`, copper clearance and board-edge relationship.
- Continued alignment after moving a jack.

Consolidate the notch dimensions into the shared model. A footprint’s `F.Fab` notch annotation alone is insufficient.

## 4. What remains unverified after A

Even the expanded A establishes **document and nominal assembly consistency**, not a completed mechanical qualification.

Remaining work includes:

1. **Authoritative dimensions and tolerances.** Neutrik heights; Switchcraft’s toleranced seating height; exact DE-9, buttons, light pipes and mounting hardware. I located the manufacturer’s separate [HF drawing](https://www.neutrik.com/media/8567/download/st-nrj6hf.PDF?v=2) and [HM drawing](https://www.neutrik.com/media/8570/download/st-nrj6hm-1-pre.PDF?v=2), but could not inspect their dimension graphics through the available web rendering. I have not assigned heights from them.
2. **Full enclosure clearance.** Flanges, supports, solder tails, component heights, ribbon connectors and cables, and interference between the sloped control board and horizontal boards.
3. **Manufacturing and assembly tolerances.** Hole location/size, board thickness and bow, component seating, notch tooling, and cumulative alignment across the 300 mm width.
4. **Mechanical function.** Full plug insertion, nut/tool access, button travel, toggle polarity, mounting loads and assembly sequence.
5. **Chassis bonding.** Mechanical contact and bare-metal hardware interfaces still need validation; matching coordinates does not close the RF/ESD findings.
6. **The other open review findings.** A does not close unrelated electrical or checker defects. Finding 14 closes only if movement direction **and contact-to-legend mapping** are verified.

**Implement A with corrected heights, explicit PCB-top datums, and real mating-plane placement. A change that only rewrites `cy` values should not close finding 2.**