# TBox adversarial design review

- **Reviewed revision:** `ab4ee9d` — Panel model: corrections from the implementation review
- **Review performed:** 2026-09-24
- **Documented:** 2026-09-27
- **Disposition:** Do not release this revision for fabrication.

This records the findings from the review of the current design, including
the exported netlist, embedded PCB footprints, mechanical model, tooling,
and vendor drawings. The recent mechanical corrections help, but electrical
defects and validation gaps remain. No project files were changed during
the review. This document records that review; it is not a new validation
run or a claim that any finding has subsequently been resolved.

Priority **P1** identifies defects to resolve before proceeding toward
fabrication. **P2** identifies other correctness and validation issues that
also need resolution before the relevant design or release claim is reliable.
Calculations and idealized circuit models below are not bench measurements.

## 1. [P1] Headphone protection conducts during normal audio

U1001, U1104 and U1304 clamp the AC-coupled headphone signals to GND/+9 V.
Those signals swing negative: the planned 0.79 Vrms into 16 Ω gives
approximately −1.12 V peaks. The SP724 starts conducting about one junction
drop below its negative rail. This creates asymmetric clipping and additional
amplifier current at intended operating levels.

All three arrays need protection compatible with bipolar audio. Changing
only U1001 leaves parallel clamps connected.

Evidence: [front schematic](kicad/front.kicad_sch),
[preamp schematic](kicad/preamp.kicad_sch), and
[filed SP724 datasheet](third_party/datasheets/Littelfuse_SP724.pdf).

## 2. [P1] Mute shunts inject the muted signal into VREF

The conducting MOSFET pair sends input audio through 220 Ω into the shared
reference. That reference has a 10 Ω isolation resistor and approximately
490 µF of distributed capacitance, giving about **2.12 Ω impedance at
150 Hz**. A 1 Vrms signal at the shunt input can therefore produce roughly
**9.6 mVrms on VREF**:

```text
Zref = 1 / (1/10 + j·2πf·490 µF)
Vref / Vin ≈ Zref / (220 Ω + Zref)
```

The muted switch output selects that disturbed VREF, and the rig-output
amplifier also follows VREF. Consequently, switch off-isolation does not
establish system mute depth.

A linear model assembled from the present connectivity predicted
approximately **48 dB intercom attenuation at 150 Hz**, and **64 dB at
1 kHz**, in a valid setting with channel/rig trims at maximum,
monitor/volume controls at zero, and LINE output. The calculation used ideal
op-amps, nominal passive values, a conducting shunt-pair resistance of
0.086 Ω, a 5 Ω analog-switch resistance, 16 Ω headphone loads, and a
10 kΩ approximation for each transformer primary load. The line-output
source selectors were set to RX left; the unused signal inputs were quiet.

These are idealized calculations, not transistor-level simulation or bench
measurements, but they identify a leakage path independent of switch
quality. The mute return needs separation from the reference used by
downstream ground-referenced outputs.

Evidence: [shared mute schematic](kicad/mute.kicad_sch), R2504 and
C2507 in the [supply schematic](kicad/supply.kicad_sch), and R3304 and
the output amplifiers in the [rig-output schematic](kicad/rigout.kicad_sch).

## 3. [P1] Headphone precharge does not establish “no step at enable”

Even assuming an ideal disabled amplifier, the 1 kΩ/470 µF network has
approximately a **478 ms** charging constant with 16 Ω headphones. After
the nominal 1.258 s supervisor delay, a 4.5 V reference step leaves
approximately **323 mV** uncharged:

```text
τ = [1000 Ω + (16 Ω || 4700 Ω)] × 470 µF ≈ 0.478 s
Residual = 4.5 V × exp(−1.258 s / τ) ≈ 0.323 V
```

Actual supply/reference ramps affect the residual; the nominal hold time
does not establish complete precharge.

Separately, OPA1622 input bias current through the **150 kΩ feedback
resistor** produces approximately **180 mV typical output offset from
VREF** at zero volume, potentially around 330 mV using the temperature-range
bias-current limit. Precharging to VREF cannot remove that mismatch.
TI also explicitly warns that the disabled output is not high impedance.

Revise the offset and output sequencing before treating startup behavior
as merely a listening test.

Evidence: R2407/R2408/R2419/R2420 and R2425–R2428 in the
[monitor/phones schematic](kicad/monphones.kicad_sch), and the
[OPA1622 datasheet](third_party/datasheets/TI_OPA1622.pdf), electrical
characteristics and shutdown-mode sections.

## 4. [P1] Permanent precharge resistors couple headphone audio into VREF

R2425–R2428 remain connected during playback. Each injects approximately
**0.95 mArms** at a 0.95 Vrms amplifier output. Two correlated channels
can disturb VREF by roughly **4 mVrms at 150 Hz**, before accounting for
the rest of the circuit. Several stages convert this reference disturbance
into output audio.

The power checker conceals the reference loading through its `no_loads`
exemption. Adding a hypothetical **1 Ω VREF-to-GND resistor in memory**
still left the model reporting zero VREF load and no warning.

The reference needs an explicit source/sink-current and impedance analysis.
“No load by design” is demonstrably false. Disconnecting the precharge
branches after startup or giving them a separate reference are possible
directions; their implementation must also address finding 3.

Evidence: [monitor/phones schematic](kicad/monphones.kicad_sch),
[power model](tools/power_model.py), and [power capability declarations](power_tree.json).

## 5. [P1] The source fuse does not establish the PTC fault-current rating

The selected 1812L050/60 has a **10 A maximum fault-current rating**.
A branch fuse marked a few amperes does not limit instantaneous fault
current to that value. A shack supply can exceed 10 A during the fuse’s
clearing interval while still satisfying the documented source description.

Specify an actual current-limited source envelope or coordinate protection
against prospective fault current and fuse clearing characteristics. This
issue applies to stationary supplies too.

Evidence: the source-envelope argument in [DESIGN.md](DESIGN.md), F2501
in the [supply schematic](kicad/supply.kicad_sch), and the
[PTC datasheet](third_party/datasheets/Littelfuse_1812L_PTC.pdf).

## 6. [P2] Panel generation does not validate actual cut-out sizes

`cutout.dia` is recorded but never applied to SVG geometry. For example,
the front Neutrik artwork contains Ø6.4 mm socket openings, while the model
specifies Ø10 mm or Ø11.2 mm panel cut-outs. These drawings remain
illustrations with corrected centers, not validated drilling geometry.

The attempted transform rejection also silently skips checking: adding a
transform creates an empty entry, which satisfies coverage and executes no
coordinate comparisons.

The following mutations were independently exercised in memory:

| Mutation | Additional diagnostic |
|---|---|
| Shrink J1102’s illustrated opening radius from 3.2 to 1 mm | None |
| Translate both J1102 circles by `(10,20)` mm | None |
| Move only J1102’s outer circle 10 mm sideways | None |
| Move front `Edge.Cuts` 5 mm | None |
| Shift J1101’s pads 1 mm without changing its origin | None |
| Rotate J1101 180° | Correctly rejected |

The baseline already fails for unrelated unresolved items. “None” means
the mutation adds no finding, not that the complete checker run succeeds.

Generate distinct fabrication cut-outs and validate their dimensions and
transforms. Compare against actual board edges and verified footprint
geometry, rather than only footprint identifiers and origins.

Evidence: `apertures()` and the cut-out-status check in
[gen_panels.py](tools/gen_panels.py), [panel-front.svg](panel-front.svg),
and [mech.json](mech.json).

## 7. [P2] Trimmer coverage is bypassed, and its axis offset is wrong

`mount: "through"` skips all placed-board checks, including lateral
alignment, facing and mounting side—not just recess depth. Moving RV3301
**20 mm sideways** added no diagnostic.

The mechanical record also says `axis_offset: 0`, but the adjustment axis
is centered over the middle terminal, **2.54 mm from the footprint
origin**. The existing placement reflects that offset: RV3301’s origin is
x=163.54 for its x=161 panel access position at 180°.

Preserve that relationship when implementing placement, and keep the
available axis/facing checks independent of the unresolved recess depth.

Evidence: the `mount == "through"` branch in
[gen_panels.py](tools/gen_panels.py), the 3386W record in
[mech.json](mech.json), the embedded footprint in
[the PCB](kicad/tbox.kicad_pcb), and the
[Bourns drawing](third_party/datasheets/Bourns_3386.pdf).

## 8. [P2] The transformer footprint reserves the wrong body envelope

The TY-250P footprint uses **17.8 × 22.8 mm** fabrication geometry and an
**18.8 mm-wide courtyard**. Triad specifies overall width **22.86 mm**,
length **19.558 mm**, and height **17.78 mm**. The footprint appears to
use the vertical height as a planar dimension.

Its courtyard therefore understates the maximum width by approximately
**4.06 mm**. Clearance checks can pass placements that do not accommodate
the specified transformer envelope. The corrected maximum envelope already
intersects neighboring footprint bounding boxes; that warrants checking
actual component bodies before routing. Bounding-box intersections are
not, by themselves, proof of a physical collision.

Evidence: [project footprint](kicad/tbox.pretty/Transformer_Triad_TY-250P.kicad_mod),
[filed drawing](third_party/datasheets/Triad_TY-250P.pdf), and
[manufacturer dimensions](https://www.triadmagnetics.com/item/audio-transformers/pc-mount-plugin-printed-circuit-audio-transformers/ty-250p).

## 9. [P2] Top-panel geometry is inconsistent and outside the checker

The placer takes top positions from a hardcoded table and forces orientation
zero. SW2103 consequently throws front/back rather than toward the
left/right operator legends.

D2118 currently remains at PCB y=178. The table requests panel y=12,
whereas the SVG shows **y=10**, corresponding to PCB y=180 under the
placer’s transform. Reporting the placement failure now prevents another
move, but does not repair the stored mismatch.

The control-board transform, panel thickness, hardware engagement and
mounting details still need resolution before an assembly fit can be
established.

Evidence: `TOP` and the top-panel placement branch in
[place_panel.py](tools/place_panel.py), [panel-top.svg](panel-top.svg),
[mech.json](mech.json), and the V-bracket drawing on printed page F-13
of the [C&K catalog](third_party/datasheets/CK_7000-series_toggles.pdf).

## 10. [P2] Protection placement leaves distant entrances unchecked

U3201 is approximately **228 mm from PTT-B jack J3203**, which it
protects. The checker passes because the same array is near PTT A. U1001
similarly serves a phones jack approximately **108 mm away**.

Evaluate every protected entrance and its return path. An
array-to-nearest-jack measurement cannot establish a short discharge loop
for every input. These are footprint-origin distances, not routed lengths;
routing cannot eliminate their endpoint separation.

C2501 also remains approximately **15.9 mm from the ADP7142 input it
should decouple**, confirming the acknowledged ownership problem.

Evidence: the nearest-jack test in
[check_placement.py](tools/check_placement.py), `ATTACH` in
[place_panel.py](tools/place_panel.py), capacitor ownership in
[place_decoupling.py](tools/place_decoupling.py), and
[the placed board](kicad/tbox.kicad_pcb).

## 11. [P2] Placement and synchronization have false-success cases

Existing free components and unresolved panel parts are omitted from initial
occupancy unless anchored. Adding new parts can therefore target occupied
space. See the occupancy initialization in
[place_panel.py](tools/place_panel.py).

Two reproduced examples show why passing checks need narrower interpretation:

| Mutation | Result |
|---|---|
| Move R1104 to x=−10 mm, y=30 mm | `check_placement.py` still passes |
| Substitute a 0603 resistor footprint for J1103 in the input model | `sync_pcb.py --dry-run` returns success |

The placement checker lacks the corresponding outer-X containment check.
Synchronization dry-run skips the pad/net validation that would reject the
substitution. Validate the complete proposed update in memory, suppressing
only the final save.

Evidence: [check_placement.py](tools/check_placement.py) and the net-update
branch guarded by `if not args.dry_run` in [sync_pcb.py](tools/sync_pcb.py).

## 12. [P2] Procurement and performance claims remain insufficiently specified

Critical capacitors still lack complete ratings or ordering identities,
including regulator input capacitance, ADP7142 effective output capacitance,
and headphone coupling-capacitor ripple/ESR requirements. Values and
footprints alone do not establish these properties. Examples include C2512,
C2501/C2504, and C2401/C2402/C2408/C2409 in the
[supply](kicad/supply.kicad_sch) and
[monitor/phones](kicad/monphones.kicad_sch) schematics.

Two specific documentation corrections matter:

- **PVA H2 already specifies 23 mm total height.** The trailing placeholders
  concern other ordering options; treating them as the unresolved height
  obscures information already available. See the ordering table in the
  [PVA datasheet](third_party/datasheets/CK_PVA.pdf).
- **“+8 dBV guaranteed” is not a universal signal-path limit.** An OPA1678
  follower centered at 4.5 V reaches its 7 V upper common-mode boundary at
  approximately **+4.95 dBV**. With the stated +6 dBV planning limit and
  15 dB crest factor, unclipped nominal microphone limits calculate to
  approximately **−36.7 dBV LO** and **−48.8 dBV HI**, below the advertised
  upper coverage. See [LEVELS.md](LEVELS.md) and the
  [OPA1678 datasheet](third_party/datasheets/TI_OPA1678.pdf).

## Correction to the earlier SJ1 bushing conclusion

**A brass SJ1-3533NG bushing does not establish a sleeve-to-panel electrical
bond.** Same Sky explicitly markets this part as **isolated ground**, and
the filed drawing does not establish the nut connection asserted in
`mech.json`. J3303’s transformer isolation should not be reported as
defeated on that evidence.

Evidence: [manufacturer description](https://www.sameskydevices.com/product/interconnect/connectors/audio-connectors/jacks/sj1-3533ng),
[filed drawing](third_party/datasheets/SameSky_SJ1-353xNG.pdf), and the
SJ1 record in [mech.json](mech.json).

## Recent fixes that checked out

- Cardinal rotation and inverse-placement calculations.
- Reversed-jack detection.
- Corrected shoulder placements.
- Synchronization of all six rebuilt custom jack instances with their
  library pad geometry.
- Buffered mute commands and the stronger supervisor pull-up address the
  earlier command-backfeed and divider defects. This does not establish
  complete transient performance or resolve the reference leakage above.

## Validation results and limits

| Check | Result at the reviewed revision |
|---|---|
| ERC | 0 violations |
| Schematic geometry, board partition, footprint existence, placement checks | Pass |
| PCB/schematic parity | 0 issues |
| DRC | 446 silkscreen warnings; 499 unconnected items |
| Panel checker | 21 problems |
| Declared power budget | Raw rail 367.95/400 mA; +9 V 319.95/385 mA; both alert |
| Ruff | 2 import-order errors in `gen_panels.py`; formatting passes |

The DRC warnings comprise 199 silkscreen overlaps, 199 silkscreen-over-copper
warnings and 48 silkscreen-edge-clearance warnings. No copper-clearance or
schematic-parity errors were reported. The PCB has no routed tracks, so
these results do not establish routed-board correctness. The declared
power-budget totals likewise do not establish reference loading or the
assumed thermal implementation.

Checker counterexamples were exercised in memory. Review exports and
temporary analysis artifacts were directed to `/tmp`; no project files
were changed during the review. Thermal performance, RF immunity, assembly
fit and transient behavior remain unverified. The electrical calculations
above are analysis, not hardware measurements.
