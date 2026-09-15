**A is still the right approach, but this implementation does not yet satisfy the specification.** The unflipped cardinal-rotation maths is sound. There are concrete dimensional errors, incorrect flip handling, and several cases where the checker accepts physically wrong geometry.

I read the prior review first, inspected the filed dimensioned drawings and embedded PCB footprints, and ran mutations in memory. No files were changed.

## 1. Recorded dimensions: three corrections

### Shoulder positions came from silkscreen, not F.Fab

The coordinates quoted in [mech.json](/home/ch/src/ee_stuff/projects/tbox/mech.json:80) are **silkscreen coordinates, expanded by 0.12 mm**. The actual embedded F.Fab geometry agrees with the vendor dimensions:

| Part | Recorded `panel_face` | Correct nominal value |
|---|---:|---:|
| SJ1-3533NG | 1.32 | **1.20 mm** |
| NRJ6HF-1 | 17.07 | **16.95 mm** |
| NRJ6HM-1-PRE | 17.57 | **17.45 mm** |

For example, SJ1’s actual F.Fab bushing spans **x=−2.10…3.90, y=−5.20…−1.20**, not the ranges quoted in the JSON.

Consequences on the current PCB:

- Front SJ1/Neutrik shoulders are **0.12 mm inside** the assumed panel mating plane.
- Rear SJ1/Neutrik shoulders are also **0.12 mm inside** their mating plane.
- All pass because placement and checking use the same wrong dimensions.

Using F.Fab to establish the relationship to a footprint origin is reasonable **after checking it against the vendor’s terminal-to-shoulder dimensions**. Silkscreen is unsuitable.

### HM’s drawing specifies Ø10, not Ø11.2

The filed **ST-NRJ6HM-1-PRE** drawing explicitly labels its panel cut-out **Ø10 [.394]**. HF specifies **Ø11.2 [.441]**. Both specify the **6.5 mm height**.

Thus the HM record’s `cutout.dia: 11.2` and `cutout_status: dimensioned` are incorrect. Its source string substitutes the product-page “chassis shape” value for the actual cut-out drawing. The manufacturer-hosted drawings are [HM](https://www.neutrik.com/media/8570/download/st-nrj6hm-1-pre.PDF?v=2) and [HF](https://www.neutrik.com/media/8567/download/st-nrj6hf.PDF?v=2).

### The AV2 shoulder is dimensioned—and substantially farther forward

On printed **F-11**, the AV2 side view gives:

- Shoulder to bracket datum: **7.32 mm**
- Bracket datum to terminal 1: **12.70 mm**

With your footprint origin at terminal 1, that gives:

\[
\text{panel_face}=7.32+12.70=\mathbf{20.02\ mm}
\]

The [recorded 16.00 mm](/home/ch/src/ee_stuff/projects/tbox/mech.json:142) comes from the custom footprint’s inaccurate body outline.

For **SW3201**, currently at board **y=254.00, rotation 180°**, the physical shoulder is therefore approximately:

\[
254.00+20.02=\mathbf{274.02\ mm}
\]

That is **4.02 mm beyond** the assumed rear inner-panel plane at y=270. The corrected origin would be **y=249.98**.

This is a present assembly error, not merely missing qualification. Fix the custom footprint’s mechanical outline as well as the model.

## 2. Audit of the remaining numbers

All dimensions below are millimetres.

| Part | Axis height | Local axis offset | Nose projection | Cut-out assessment |
|---|---:|---:|---:|---|
| SJ-43514 | **2.25 ±0.20**, correct | **0**, correct for custom footprint | **3.00**, correct | Ø6.00 is nominal passing diameter; finished aperture remains unresolved |
| Switchcraft | **≈3.00**, correctly provisional | **0**, correct | **3.50 REF**, correct | M6×0.5 nominal thread; finished aperture remains unresolved |
| SJ1-3533NG | **7.00 ±0.15**, correct | **+0.90**, correct | **4.00**, correct | Ø6.00 nominal nose; finished aperture remains unresolved |
| NRJ6HF-1 | **6.50**, correct | **+7.23**, correct | **8.90**, correct | **Ø11.20**, correct |
| NRJ6HM-1-PRE | **6.50**, correct | **+7.23**, correct | **8.20**, correct | **Ø10.00**, correction above |
| C&K AV2 | **6.35**, correct | **0**, correct | Null is unfinished | Panel mounting patterns are available on F-8 |

The Neutrik transverse offset is independently supported by **11.43−4.20=7.23**, rather than relying solely on a drawn bushing midpoint.

Additional points:

- **Front 30.00 and rear 53.00 datums are consistent** with the declared seating planes and corrected side-view rear y=64.
- Those remain assembly design choices. The side drawing’s horizontal board ends sit **2 mm from the exterior wall lines**; without panel thickness, that does not establish that PCB edges coincide with inner panel faces.
- Null Neutrik height tolerances are honest about not recording a tolerance, but their drawings also specify a general tolerance standard in the title block. They are not necessarily untoleranced dimensions.
- SJ1’s description says “plastic bushing”; its material table specifies **brass, nickel-plated bushing**.
- The control-toggle source’s **11.68 mm shoulder** is supported. Its quoted **6.86 mm bushing** needs reconciliation with the ordering-specific **D9 entry on F-8, which specifies 7.11 mm**. My earlier review also overlooked that discrepancy.

### The trims can be resolved further than either of us thought

The [Bourns drawing, page 1](/home/ch/src/ee_stuff/projects/tbox/third_party/datasheets/Bourns_3386.pdf) has a **“Common Dimensions — Side Adjust Models H,S,W”** view.

It explicitly gives **5.64 mm from the adjustment axis to the lower seating datum**. The **0.38 mm minimum** identifies body relief above that datum; do not add it again. The sheet’s general tolerance is **±0.25 mm**, unless otherwise noted.

Therefore:

\[
y_{\text{trim}}=53-5.64=\mathbf{47.36\ mm}
\]

The current illustrated y=48 is **0.64 mm low**.

My warning against halving the body height was correct, but I missed this available dimension. Record it. Tool clearance and the desired panel-to-screw recess still need an assembly decision.

## 3. Geometry maths

### Unflipped rotation and perpendicular: correct

[The rotation matrix](/home/ch/src/ee_stuff/projects/tbox/tools/mech.py:65) matches KiCad’s positive counter-clockwise rotation in a y-down board frame:

\[
R_\theta(x,y)=(x\cos\theta+y\sin\theta,\,-x\sin\theta+y\cos\theta)
\]

`perp = (-nose[1], nose[0])` correctly gives:

- Nose `(0,−1)` → perpendicular `(+1,0)`, matching SJ1’s +0.90 local x.
- Nose `(+1,0)` → perpendicular `(0,+1)`, matching Neutrik’s +7.23 local y.

### The old 0.80/0.25 mm agreement is meaningful, but limited

I read the parent commit’s actual placements:

- **J1001:** origin x=204.90; plus 0.90 gives **205.80**, versus target 205.
- **J1101:** origin x=244.75; offset zero gives **244.75**, versus target 245.

These reproduce the earlier findings. However:

- J1001 tests the perpendicular sign **at rotation zero**.
- J1101’s offset is zero, so it **cannot test that sign**.
- Neither establishes flip correctness or validates shoulder dimensions.

The earlier **1.70 mm SJ1 shoulder error** also reproduces using the correct shoulder: **2.90−1.20=1.70**. Your current model instead computes 1.58—another indication of the 0.12 mm error.

### `origin_for_axis()` slide: correct for current cardinal use

Sliding along the nose preserves the transverse axis line while bringing the shoulder onto the requested coordinate plane. That is what these front/rear placements need.

The docstring overstates it: the returned axis **point** generally does not remain at `axis_xy`; the **axis line** does. For example, the supplied `(x,0)` becomes an axis reference point at `(x,1.32)` for the current SJ1 record.

For future arbitrary-angle panels, replace the dominant-coordinate branch with an explicit panel plane and normal.

### Flipped footprints: incorrect

[The flip code](/home/ch/src/ee_stuff/projects/tbox/tools/mech.py:81) mirrors local **x**. Testing actual KiCad `Flip()` behavior shows that, **at a fixed reported orientation**, its local transform mirrors **y**.

A concrete test using the exact `place_edge()` body:

1. Flip J1001.
2. Place it for target x=205, front edge y=0.
3. The placer chooses rotation 0°, origin **(205.90,1.32)**.
4. The model reports axis x=205 and shoulder y=0.
5. Actual B.Fab geometry has bushing axis **x=206.80**, shoulder **y=2.52**, and the nose points **toward +y**.

That is **1.80 mm sideways error**, incorrect shoulder placement, and reversed facing—accepted by the model.

Also, a bottom-mounted part needs a different **vertical seating-plane transform**; `hole_y()` currently ignores mounting side entirely.

**For this assembly, reject flipped panel parts until both planar and vertical transforms are implemented.**

## 4. The checking has demonstrable false negatives

Baseline `gen_panels.py` produced **18 problems**, all existing unresolved/coverage reports. Each “missed” mutation below added **no new error**; the overall run still failed for those unrelated baseline problems.

| Mutation tested in memory | Result |
|---|---|
| Rotate J1101 **180°** at its existing origin | Missed |
| Rotate J1101 **90°** at its existing origin | Missed |
| Shift all J1101 pads **1 mm**, preserving origin and footprint ID | Missed |
| Change J1102’s illustrated hole radius **3.2 → 1 mm** | Missed |
| Add `transform="translate(10,0)"` to both J1102 circles | Missed |
| Move only J1102’s outer circle **10 mm sideways** | Missed |
| Move J1101 origin **0.040 mm** sideways | Accepted within tolerance |
| Move J1101 origin **0.051 mm** sideways | Correctly rejected |
| Set front Neutrik `cy=99`, run `--pcb no` | No coordinate error reported |

### Required fixes

**Check facing.** [The board checker](/home/ch/src/ee_stuff/projects/tbox/tools/gen_panels.py:183) computes `_nose` and discards it. Switchcraft’s zero axis offset and zero shoulder distance make its coordinate checks invariant under rotation. Apply the specified **0.1° orientation tolerance**.

**Verify footprint identity and contents.** Both tools trust a library-ID string. Neither verifies the board’s MPN against `mpn`, nor verifies embedded pad/mechanical geometry against the supported footprint. `check_footprints.py` only establishes that a named library file exists.

Use a reviewed footprint geometry signature or compare normalized mechanical/pad geometry against a verified definition. Keep pad-edge clearance as a separate constraint.

**Generate and check actual cut-outs.** The SVGs still contain socket illustrations:

- Front Neutrik inner circles: **Ø6.4**
- Front 3.5 mm jack inner circles: **Ø3.6**

No generated drilling geometry uses `cutout.dia`. A changed radius cannot fail. Separate cut-outs from nuts, mouths and artwork, then validate their shapes and dimensions.

**Handle SVG geometry structurally.** `_panel_refs()` silently takes the last x for duplicate references; `apertures()` checks only raw y attributes. Neither evaluates transforms. Distinguish each aperture from its artwork and either support transforms or reject them.

**Repair `--pcb no`.** Without reading the board, `fpid_of` stays empty; `want` becomes `None`, and all dimensional checks are skipped. Obtain identities elsewhere or reject this mode.

**Read actual edges and notches.** The checker compares shoulders against hardcoded **0/270**, not actual `Edge.Cuts`. It never checks notch geometry.

**Enforce unresolved fields.** `part()` requires only four fields. Null cut-outs, null projection, unknown panel thickness, and unverified control geometry do not themselves fail coverage. A prose `unresolved` list is not a completeness check.

The **0.05 mm tolerance is doing work**, but it exceeds the requested **0.01 mm nominal consistency tolerance** and cannot compensate for these missing checks.

## 5. Missing specification coverage

| Item | What should be completed now | What genuinely needs more identity/design information |
|---|---|---|
| Rear toggles | Correct shoulder; record available mounting patterns, bushing data and throw direction | Chosen hardware stack and panel thickness |
| Trims | Record **5.64 mm axis height** and available footprint/slot dimensions | Recess and screwdriver envelope |
| Pots | Move shaft datums into shared model; record available RD901F/RD902F dimensions | Confirm complete ordering suffix/bracket configuration and hardware |
| SW2103 | Represent its known geometry; enforce left/right throw and verify contact-to-legend mapping | Control-board transform and hardware reach |
| Buttons | Preserve known base geometry and require missing fields | Complete actuator/cap ordering identity |
| LEDs | Include every intended indicator | Selected light pipes, including **D2118**, absent from the unresolved LED list |
| DE-9 | Require a supported connector and complete mounting geometry | Exact connector MPN |
| Powerpole/GND | Require panel-only mounting records | Selected retention assembly/post and hardware |
| Panel/enclosure | Model inner faces, PCB-edge gaps, board planes and supports | Chosen thicknesses and construction |
| Notches | Consolidate dimensions and inspect actual edges | Fabrication radius/process allowance |

Two specific implementation gaps remain:

- Only front and rear SVGs are checked. Side-view board planes/undersides and all top-panel geometry remain outside the check.
- **J3206 already has `data-ref`**, but `apertures()` ignores `<g>` elements. Its suggestion to run `--write` cannot fix that. Missing annotations also cause position-reader assertions **before** automatic annotation can run.

Unresolved status is appropriate where identity is genuinely missing. It should not substitute for extracting dimensions already available for selected parts.

## 6. Regressions and present limits

- **D2118 is still moved and saved after being reported unplaceable.** Its origin changed **y=176 →178**. That reduces the drawing mismatch from 4 to 2 mm, but still violates the placer’s own limit. The message incorrectly attributes TOP’s y=12 to the SVG, which says **y=10**. See [placement branch](/home/ch/src/ee_stuff/projects/tbox/tools/place_panel.py:312).
- Newly unplaceable edge parts are skipped before becoming anchors. Their occupied area is consequently absent from initial placement occupancy, allowing free-part placement to target it. Preserve occupancy for parts left in place.
- Mechanical placement reduced pad-edge distances: Switchcraft’s nearest copper is now **1.15 mm** inside the edge; SJ1’s is **0.42 mm**. These are not automatically violations, but the previous 2 mm heuristic no longer supplies a clearance constraint.
- The actual TRRS notches are currently correctly centered at **x=75 and225**, **4.50×1.30 mm**. This aspect has not regressed.
- I reran `check_placement.py`; it passes. I did not independently rerun DRC.

**Fix first:** the AV2 shoulder, the three 0.12 mm shoulder errors, HM cut-out data, flip rejection, facing validation, and real aperture checks. Until then, “passes on every jack and rear toggle” establishes agreement with the current model, not correct nominal panel geometry.