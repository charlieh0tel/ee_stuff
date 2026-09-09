**Second adversarial review — commit `7883f54`**

**The first review is not fully closed.** The new supervisor exceeds its RESET-pin voltage rating; the mute changes introduce delayed, abrupt unmuting; and the PTT inhibit shares that slow timing network. Several earlier fabrication and protection findings remain unresolved.

No project files were modified. Calculations below use the supplied vendor PDFs. Transient calculations are simplified circuit models, not measurements or vendor-model SPICE results.

**1. BLOCKER — PWR_OK exceeds the TPS3808 RESET-pin rating**

**Location:** [supply.kicad_sch:9952](/home/ch/src/ee_stuff/projects/tbox/kicad/supply.kicad_sch:9952), R2507/U2504; U2401/U2403 EN.

R2507 pulls RESET/PWR_OK toward **+9 V**. The TPS3808 allows **6.5 V operating, 7 V absolute maximum** on RESET. Its open-drain output does not permit arbitrary pull-up voltages.

The two OPA1622 EN inputs load this node, but insufficiently. Using TI’s approximate EN current, `(VEN − 0.7)/700k`, gives:

`(9 − V)/100k = 2(V − 0.7)/700k → V ≈ 7.156 V`

Thus even the loaded nominal voltage exceeds absolute maximum. Lower EN loading moves it farther toward 9 V. Supervisor malfunction can affect both headphone enable and rig-key inhibition. Evidence: [TPS3808, §§6.1–6.3 and 7.3.4](/home/ch/src/ee_stuff/projects/tbox/third_party/datasheets/TI_TPS3808.pdf); [OPA1622, §7.3.3](/home/ch/src/ee_stuff/projects/tbox/third_party/datasheets/TI_OPA1622.pdf).

**Fix:** Pull RESET up to a suitable regulated rail, such as 5 V, with a resistor selected for the combined EN load and Q2108 drive. A 10 kΩ pull-up is a reasonable starting point. Verify guaranteed logic levels and startup behavior; changing the pull-up alone does not fix finding 3.

**2. BLOCKER — The headset-jack board notches remain absent**

**Location:** J1103/J1303; [SJ-43514 footprint](/home/ch/src/ee_stuff/projects/tbox/kicad/tbox.pretty/Jack_3.5mm_CUI_SJ-43514_Horizontal.kicad_mod); [TODO.md:34](/home/ch/src/ee_stuff/projects/tbox/TODO.md:34).

The tip-terminal and pin-5 coordinates were corrected. The required **4.5 × 1.3 mm board-edge notch** remains only an F.Fab illustration. The PCB still has a straight outer edge through these locations.

The footprint also retains the explicitly estimated **10.8 mm terminal depth**, awaiting confirmation. Recording these requirements in TODO does not make the current board mechanically buildable.

**Evidence:** [Same Sky mechanical drawing, page 2](/home/ch/src/ee_stuff/projects/tbox/third_party/datasheets/SameSky_SJ-4351X.pdf), current footprint and PCB outline.

**Fix:** Incorporate both notches into the outline generator and qualify the undimensioned terminal depth against an authoritative footprint, model, or sample before fabrication.

**3. MAJOR — PTT inhibition is delayed by the audio-mute capacitors and is undefined during early startup**

**Location:** [keylogic.kicad_sch:10648](/home/ch/src/ee_stuff/projects/tbox/kicad/keylogic.kicad_sch:10648), Q2108/Q2109/R2122/D2120/D2121; U2504/U2501.

Q2109’s gate is MUTE_HOLD. Its only pull-up is **100 kΩ R2122**, and that node also charges both microphone mute cells through D2120/D2121. Therefore the hardware PTT inhibit inherits the audio timing load.

With both channels initially unmuted, an RC calculation using the actual resistor/capacitor values and 0.6 V diode drops gives:

| Supply held after reset assertion | Initial MUTE_HOLD | Time to 2.5 V | Time to 3 V |
|---|---:|---:|---:|
| 7.452 V | 1.52 V | 14.5 ms | 36.2 ms |
| 9 V | 1.73 V | 7.4 ms | 16.1 ms |

The 2N7002’s **2.5 V maximum threshold is specified at only 250 µA**; reaching that voltage does not establish a strong clamp against the PTT pull-up current. This is not a prompt brownout inhibit.

Separately, U2504 is powered by BIAS_5V, downstream of the ADP7142 and its 47 Ω/220 µF filter. The TPS3808 says RESET is **undefined below its power-on-reset supply voltage**. During that interval R2507 can raise PWR_OK and turn Q2108 on, defeating MUTE_HOLD while the discrete keying devices can already conduct. A held PTT during a slow ramp is therefore not guaranteed inhibited. Evidence: [TPS3808 §7.4](/home/ch/src/ee_stuff/projects/tbox/third_party/datasheets/TI_TPS3808.pdf), [ADP7142 undervoltage/startup specifications](/home/ch/src/ee_stuff/projects/tbox/third_party/datasheets/ADI_ADP7142.pdf), and [2N7002 electrical characteristics](/home/ch/src/ee_stuff/projects/tbox/third_party/datasheets/Diodes_2N7002.pdf).

**Fix:** Give the rig-key inhibit a separate, fast, default-inhibited path. Buffer the audio hold separately. Establish the inhibited state before the supervisor becomes operational, and test held PTT through slow ramps, rapid cycling and brownouts.

**4. MAJOR — Manual/override unmute takes hundreds of milliseconds to seconds, then reconnects unfaded audio**

**Location:** [mute.kicad_sch:2403](/home/ch/src/ee_stuff/projects/tbox/kicad/mute.kicad_sch:2403), R1201–R1204/C1202/C1203/D1201 and corresponding channel-B instances.

The release diode is correctly oriented: **anode SW_CTL, cathode MUTE**. The problem is its destination. Manual, override and startup-hold drivers source MUTE through diodes; they cannot pull it down. On release, the only steady discharge sink is **R1201 = 1 MΩ**.

D1201 consequently discharges C1203 into MUTE and the fade network. It does not produce the documented immediate switch release.

Starting from 8.3 V, the two-capacitor RC calculation gives:

| Event | Approximate time |
|---|---:|
| FADE_G falls below 5.5 V | 399 ms |
| SW_CTL falls below 5 V | 612 ms |
| SW_CTL falls below 3 V | 1.22 s |
| SW_CTL falls below 0.8 V | 2.80 s |

When SW_CTL reaches 5 V, FADE_G is already approximately **4.60 V**, close to VREF and insufficient to maintain the shunt. The eventual switch transition therefore reconnects substantial instantaneous audio. PTT-gated operation can lose the beginning of speech; manual and override release can pause and click.

The intercom instance has a transistor sink and does not share this particular slow-discharge problem. Its fade still needs qualification: the claimed pair resistance of approximately 6 Ω is not guaranteed at the available roughly **3.8 V gate-to-source drive**. The supplied 2N7002 resistance specification uses 5 V or 10 V drive.

**Fix:** Drive each timing input with a defined source and sink. Reconnect the analog switch while the shunt remains fully asserted, then release the shunt. Define switching thresholds and gate drive explicitly instead of relying on an unspecified analog-switch threshold and MOSFET resistance.

**5. MAJOR — OPA1622 EN does not establish a controlled charging sequence for the headphone output capacitors**

**Location:** [monphones.kicad_sch:7192](/home/ch/src/ee_stuff/projects/tbox/kicad/monphones.kicad_sch:7192), U2401/U2403, C2401/C2402/C2408/C2409.

The amplifier outputs operate near **4.5 V**, while the headphone side of each 470 µF capacitor returns to chassis. EN suppresses amplifier-generated transition glitches; it does not guarantee precharging these external capacitors.

TI explicitly warns that the disabled output is not a defined high-impedance node. Its small enable-transient figures do not establish quiet operation for this single-supply, large coupling-capacitor circuit. The explicit passive charging path through the feedback network is approximately **160 kΩ**, giving a **75 s** time constant with 470 µF.

An uncharged capacitor subjected to a 4.5 V output transition would initially apply:

`4.5 × 16/(16 + 3.3) ≈ 3.73 V`

to a 16 Ω load before amplifier current limiting. The corresponding output-network time constant is approximately **9 ms**. Actual amplitude depends on the disabled output behavior and current limit, but the circuit does not control it. Evidence: [OPA1622 §§7.4.1–7.4.2](/home/ch/src/ee_stuff/projects/tbox/third_party/datasheets/TI_OPA1622.pdf).

**Fix:** Provide a defined capacitor-precharge/output-disconnect sequence, or a validated controlled output-bias ramp. Connect the headphones only after the load-side voltage is safe. Measure startup, shutdown and brownout pulses with headphones connected and volume at zero and maximum.

**6. MAJOR — The intercom fade resistor reintroduces load-dependent TX level loss**

**Location:** R2302/U2301 in [mute.kicad_sch:2403](/home/ch/src/ee_stuff/projects/tbox/kicad/mute.kicad_sch:2403); RV3301–RV3303/J3301/J3302 in `rigout.kicad_sch`.

The added **2.2 kΩ R2302** remains in the signal path whenever intercom mute is released. TX_MIX drives the 10 kΩ mic-output trim and, depending on jumpers, either or both 10 kΩ line-output trims.

At audio midband:

| Trims selecting TX_MIX | Load | R2302 insertion loss |
|---|---:|---:|
| Mic only | 10 kΩ | −1.73 dB |
| Mic + one line output | 5 kΩ | −3.17 dB |
| Mic + both line outputs | 3.33 kΩ | −4.40 dB |

Thus changing a recording-output source changes the rig microphone level. From −15 dBV TX_MON, the +4.86 dB driver reaches only approximately **−11.87 to −14.54 dBV**, even with its trim fully open, before subsequent losses.

**Fix:** Buffer the post-mute TX_MIX node before distributing it, or move the fade into a stage whose gain and loading are controlled. Recalculate all output-selection combinations.

**7. MAJOR — The new LO gain clips advertised hot microphones before the level pot**

**Location:** [preamp.kicad_sch:5822](/home/ch/src/ee_stuff/projects/tbox/kicad/preamp.kicad_sch:5822), R1104/R1304/U1101/U1301; [LEVELS.md:40](/home/ch/src/ee_stuff/projects/tbox/LEVELS.md:40).

The new gains are **27.70 dB LO / 39.80 dB HI**. They fix the nominal electret-level shortage, but the claimed hot-source coverage is incorrect.

For the documented −28 dBV powered desk microphone, LO produces −0.30 dBV nominal and **+11.7 to +14.7 dBV peaks** with the stated crest factor. Those peaks exceed the approximately +8 dBV clip capability before the downstream level pot.

Similarly, a −25 dBV source produces **+2.7 dBV nominal**, not a +3 dBV peak. Its peaks reach approximately +14.7 to +17.7 dBV. Turning down RV2201/RV2202 cannot repair that clipping.

**Fix:** Add input attenuation or a lower preamp-gain setting, or narrow the supported source range. Put the adjustment ahead of whichever stage would otherwise clip.

**8. MAJOR — The chassis scheme has physical bonds, but not the claimed local, negligible-impedance returns**

**Location:** [front.kicad_sch:5877](/home/ch/src/ee_stuff/projects/tbox/kicad/front.kicad_sch:5877), NT1001/H1001; NT2401/H2401; NT3201/J3206; [DESIGN.md:408](/home/ch/src/ee_stuff/projects/tbox/DESIGN.md:408).

The studs have plated copper pads and J3206 has CHASSIS-connected shield pads. There is no simple missing-DC-bond error. The unresolved problem is the physical return geometry:

- H1001 is at **(160.475, 32.475) mm**, approximately **75–86 mm** from the two TRRS ring-2 pads. The documented short spur to the stud is not implemented.
- NT3201 is at **(102.75, 215.25) mm**, roughly **50 mm** from the DE-9 return/shield connections.
- Each net tie is a **0.5 mm-wide copper bridge**, not a chassis attachment.
- NT1001 and NT2401 create a parallel headphone-return route through the front/control ribbon grounds. The rear tie adds another parallel route.

Return current divides according to the complete path impedances—including contacts, PCB copper and ribbons—not the enclosure sheet resistance alone. The claim that these loops are benign because chassis impedance is “orders of magnitude” lower is unsupported. Shared return voltage is particularly consequential beside millivolt microphone signals.

The supplied [Pin 1 paper](/home/ch/src/ee_stuff/projects/tbox/third_party/papers/Pin_1_Revisited.pdf) specifically identifies long internal shield connections and shared impedance as failure mechanisms.

**Fix:** Place explicit chassis contacts beside the plastic-jack entries, define broad return copper and contact hardware, and separate headphone-current paths from microphone reference paths. Analyze and measure return-current division; do not assume it disappears through the chassis.

**9. MAJOR — New connector clamps still discharge into circuit GND**

**Location:** U1001/U1103/U1104/U1303/U1304/U3201; [preamp.kicad_sch:7181](/home/ch/src/ee_stuff/projects/tbox/kicad/preamp.kicad_sch:7181); `front.kicad_sch`, `reario.kicad_sch`.

All six SP724 arrays have **pin 2 on GND and pin 5 on +9 V**. The microphone RF capacitors C1101/C1109 and their B equivalents also return to GND. The new phones RF capacitors return to CHASSIS, but their clamp arrays do not.

Consequently, negative clamp current enters circuit ground, and positive clamp current enters the distributed +9 V rail. The schematic does not implement the claimed exclusion of external interference current from signal ground. The SP724 also calls for close supply bypassing; the preamp sheet has four ICs but only two 100 nF supply capacitors, without explicit clamp-bypass ownership. Evidence: [SP724 application and bypass requirements, page 2](/home/ch/src/ee_stuff/projects/tbox/third_party/datasheets/Littelfuse_SP724.pdf).

**Fix:** Design the connector discharge loop explicitly around local chassis bonds and appropriately bypassed protection rails. Coordinate the downstream current limiting with that loop. Verify positive and negative discharge paths through the actual layout.

**10. MAJOR — Battery-fault and load-dump protection remains uncoordinated**

**Location:** [supply.kicad_sch:8177](/home/ch/src/ee_stuff/projects/tbox/kicad/supply.kicad_sch:8177), F2501/FB2501/D2502; [DESIGN.md:241](/home/ch/src/ee_stuff/projects/tbox/DESIGN.md:241).

Correcting the PTC ordering suffix does not close the electrical finding. The selected 1812L050/60 has a **10 A maximum fault-current rating**, while the allowed source’s prospective fault current remains unspecified.

The SMBJ18A remains downstream of an unspecified 0805 ferrite bead, so its surge current traverses that bead. No bead pulse rating, upstream fuse coordination or surge-energy envelope establishes the retained load-dump claim. Evidence: [1812L ratings](/home/ch/src/ee_stuff/projects/tbox/third_party/datasheets/Littelfuse_1812L_PTC.pdf) and the current netlist.

**Fix:** Specify the source/fault envelope and upstream protection. Put the surge diversion path ahead of vulnerable filtering components and verify component pulse energy and fuse coordination.

**11. MAJOR — Mandatory supply-capacitor ownership is still not preserved**

**Location:** [place_decoupling.py:295](/home/ch/src/ee_stuff/projects/tbox/tools/place_decoupling.py:295); [supply.kicad_sch:6553](/home/ch/src/ee_stuff/projects/tbox/kicad/supply.kicad_sch:6553), C2513/U2503; C2515/U2504.

The current PCB contradicts the claimed capacitor-placement closure:

| Capacitor and intended device | Current center distance |
|---|---:|
| C2513, TPS7A4701 output capacitor → U2503 | 10.3 mm |
| C2501, ADP7142 input capacitor → U2501 | 10.9 mm |
| C2515 → U2504 | 41.3 mm |

More fundamentally, **C2515 is on +9 V, whereas U2504 VDD is BIAS_5V**. The supervisor has no local supply bypass; C2505 on BIAS_5V is approximately 47.6 mm away.

The heuristic prioritizes converter candidates but still lacks mandatory part/pin ownership and a failing distance requirement. TI requires close regulator capacitors and recommends a local 0.1 µF supervisor bypass. Evidence: [TPS7A47](/home/ch/src/ee_stuff/projects/tbox/third_party/datasheets/TI_TPS7A47.pdf), [TPS3808 pin functions](/home/ch/src/ee_stuff/projects/tbox/third_party/datasheets/TI_TPS3808.pdf).

**Fix:** Assign explicit capacitor owners and power pins. Put a bypass directly across U2504 VDD/GND, reserve the regulator capacitor loops before general placement, and fail placement verification when mandatory distances/loops are not met.

**12. MINOR — The supervisor hold is approximately 5.7 seconds, not 1.2 seconds**

**Location:** [supply.kicad_sch:9409](/home/ch/src/ee_stuff/projects/tbox/kicad/supply.kicad_sch:9409), C2516; TODO supervisor test instructions.

The TPS3808 equation is:

`tD = CT(nF)/175 + 0.0005 seconds`

For **1 µF**, that is **5.715 seconds nominal**, before capacitor/device tolerance. The divider arithmetic is correct: `0.405 × (1 + 174k/10k) = 7.452 V`; it is the delay arithmetic that is wrong.

**Fix:** Use approximately 210 nF for 1.2 seconds, or 220 nF for approximately 1.26 seconds, after establishing the required sequencing interval. Update the bench limits with tolerance bounds.

**13. MINOR — BLEND reverses polarity relative to the individual RX selections**

**Location:** [rigout.kicad_sch:10323](/home/ch/src/ee_stuff/projects/tbox/kicad/rigout.kicad_sch:10323), U3301B/R3301/R3302/R3318/J3301/J3302.

The summer implements **BLEND = −(L + R)** relative to VREF. Individual RX selections retain their polarity.

With one output selecting L and the other BLEND, an equal-gain downstream mono sum becomes:

`L − (L + R) = −R`

The main receiver disappears. This is a functional consequence of an otherwise permitted jumper combination.

**Fix:** Preserve polarity—for example, buffer the passive L/R average with noninverting gain 2—or explicitly restrict mixed BLEND/direct configurations where downstream summing is possible.

**14. MINOR — Load annotations still do not represent the specified operating maxima**

**Location:** U2401/U2403, R1101/R1301/R1109/R1309, R3201/R3202; [power_tree.json](/home/ch/src/ee_stuff/projects/tbox/power_tree.json).

The checker reports **260.1 mA maximum on +9 V**, but the inputs remain incomplete:

- New ring-bias resistors **R1109/R1309 have no Load_mA**. Existing tip-bias resistors remain `0/1 mA`; a grounded 2.2 kΩ branch draws roughly 2 mA, including bias-rail droop.
- R3201/R3202 still omit approximately **0.9 mA each** when PTT is grounded.
- OPA1678 `4/5 mA` per dual omits output current and is below the **5.6 mA full-temperature quiescent maximum**.
- OPA1622 quiescent maximum is **8.4 mA per dual** over temperature. At 145 mA peak per channel, an ideal stereo sine calculation gives approximately **100.7 mA/package**, above the annotated 95 mA. This is a sensitivity check, not a guaranteed output-current bound.
- The input capability remains 500 mA, although the PTC’s listed hold current is **400 mA at 50°C**.

The supervisor’s 0.02 mA and each SP724’s 0/0.01 mA annotations conservatively cover their specified supply currents. They do not cover external pull-up or signal-load currents.

**Fix:** Define temperature, load and signal scenarios; annotate all consuming branches; and derive amplifier maximum draw from those scenarios. The current numbers do not prove a budget overrun, but they are not defensible maxima.

**15. MINOR — The power checker still silently accepts missing passive loads**

**Location:** [power_model.py:200](/home/ch/src/ee_stuff/projects/tbox/tools/power_model.py:200), `_collect_loads()`; `parse_ma()`.

Missing annotations are mandatory only for devices with `power_in` pins. In an in-memory test, removing R1101’s annotation reduced the budget without any warning. The same omission already exists on the new ring-bias branches.

Parsing also accepts malformed forms such as `4//5`, `/4` and `4/` because empty fields are discarded.

**Fix:** Maintain an explicit inventory or marking of current-consuming passive branches, and require the exact one-number or two-number syntax. Preserve the new failures for missing IC annotations, invalid numbers and empty netlists.

**16. MINOR — The placement checker accepts a crossing net with no ribbon path to one of its boards**

**Location:** [check_placement.py:75](/home/ch/src/ee_stuff/projects/tbox/tools/check_placement.py:75).

The checker requires only **any** ribbon connector anywhere on a crossing net, rather than a valid connector path to every board it touches.

I changed R3205.1 to `/MUTE_A` in memory. That adds a rear-board branch to a net carried only by the front/control ribbon. The checker still returned **OK, exit 0**.

It also does not inspect tracks or apply the score’s 1 mm margin itself. The separate DRC keepouts currently provide that protection.

**Fix:** Require a complete connector path for each physical board touched by a net, validate against schematic assignments, and check the score clearance envelope. Retain DRC as an independent check.

**17. MINOR — Critical component specifications remain incomplete**

**Location:** C2513; new nonpolar RX/line-output capacitors; ferrites; PVA switch MPN fields; [TODO.md:29](/home/ch/src/ee_stuff/projects/tbox/TODO.md:29).

Examples still preventing qualification:

- C2513 remains “47u X7R” without a voltage rating or MPN establishing **at least 10 µF effective capacitance at 9 V**.
- C3401/C3402 are nonpolar, but have no specified voltage rating. A −12 V input against +4.5 V internal bias produces **16.5 V capacitor stress**.
- Ferrites lack impedance curves, DC resistance/current and applicable pulse specifications.
- PVA MPNs still contain `xxxxxx` and explanatory prose rather than complete ordering codes.

**Fix:** Supply exact MPNs or controlled substitution specifications covering electrical ratings and mechanical options. These are release requirements, not substitutions to settle after fabrication.

**18. MINOR — Remaining documentation can still direct an incorrect layout or level adjustment**

**Location:** [DESIGN.md:259](/home/ch/src/ee_stuff/projects/tbox/DESIGN.md:259), [DESIGN.md:449](/home/ch/src/ee_stuff/projects/tbox/DESIGN.md:449), [LEVELS.md:26](/home/ch/src/ee_stuff/projects/tbox/LEVELS.md:26), `power_tree.json`.

Material contradictions remain:

- VREF is labelled “DC bias only” and “no load,” although headphone/output gain resistors, pots, the BLEND summer and fade shunts return signal current to it.
- The layout instructions still specify **NT3201 as the only chassis tie**, contradicting the implemented three-tie scheme.
- The mute-node table increases approximately −17 dBV to −16.7 dBV while describing an attenuation. Its fixed 10 kΩ loading assumption also omits the downstream summing-resistor load.
- MIC-mode nominal voltage still lacks an explicit load condition; approximately 690 Ω source impedance substantially reduces the voltage into 600 Ω.
- Transformer insertion loss remains outside the nominal level table while TODO says the trims absorb it; a fully open attenuator cannot recover missing gain.
- The TS12A12511 2.4 V threshold justification still mixes dual-supply and single-supply conditions.

**Fix:** Recalculate the level tables from the loaded circuit and reconcile the grounding instructions before routing or commissioning.

**Disposition of the 26 first-review findings**

“Closed” below means the identified defect is removed; it does not imply completed hardware qualification.

| First review | Status | Current evidence |
|---|---|---|
| 1. Parts on wrong boards | closed | All 407 footprints remain within their assigned score bands; current crossing nets have ribbon paths. |
| 2. Panel datums/rear edge | closed | Pot/button datums and rear y=270 boundary corrected; final enclosure fit remains unverified. |
| 3. C&K terminal patterns | closed | 1.85 mm drills and corrected DPDT terminal/bracket spacings are present. |
| 4. SJ-43514 footprint/notch | partly | Terminal coordinates corrected; notch and terminal-depth qualification remain outstanding. |
| 5. NJM4556AM footprint mismatch | closed | Replaced by OPA1622 with the corresponding DRC0010J footprint. |
| 6. Incorrect switch functions | partly | OA/EE functions and 7203 center-off corrected; complete PVA ordering codes remain missing. |
| 7. Unintended phones chassis bonds | partly | Sleeves now intentionally use CHASSIS; return geometry and parallel paths remain unresolved. |
| 8. Headphone package dissipation | closed | OPA1622 removes the DMP8 300 mW limitation; final copper thermal performance remains to qualify. |
| 9. RX ±12 V protection | partly | Nonpolar topology and 2.2 kΩ limiting fix the identified mechanisms; capacitor ratings and fault qualification remain incomplete. |
| 10. Keying fail-safe | partly | Rear gate pull-down added; supervisor voltage, startup and inhibit timing remain defective. |
| 11. TX LED resistor dissipation | closed | 2.2 kΩ/0805 materially reduces dissipation; its stale load annotation is separate. |
| 12. Regulator capacitor placement | regressed | Claimed OUT-pin placement is not preserved; C2513 is now 10.3 mm from U2503. |
| 13. Input fault coordination | open | PTC fault-current limit and bead/TVS coordination remain unresolved. |
| 14. Headphone startup transients | partly | EN added, but coupling-capacitor charging remains uncontrolled. |
| 15. Pop-free mute | regressed | Fade added, but manual/override release now has long delay and reconnects after the shunt releases. |
| 16. Insufficient LO gain | closed | LO is now 27.70 dB; hot-source clipping is a separate consequence. |
| 17. BLEND loading | closed | U3301B buffers the distribution load; polarity consequences remain. |
| 18. Connector RF/ESD protection | partly | Front filters, arrays and secondary TVSs added; discharge-return implementation remains incomplete. |
| 19. Copper across scores | closed | Both scores have ±1 mm keepouts covering all four copper layers, tracks, vias, pads and fills. |
| 20. Truncated transformer footprint | closed | Footprint graphics are retained; both PCB transformer instances have body/courtyard graphics. |
| 21. Power-checker undercounting | partly | Missing IC loads, bad numbers and empty models fail; missing passive loads still pass. |
| 22. Generator quoted-parenthesis corruption | closed | In-memory quoted-parenthesis, quote and backslash probes preserved the unmanaged tail. |
| 23. TS mic plug shorted by ring | closed | Tip and ring are separate; a grounded ring no longer shorts the tip signal. |
| 24. Unsupported load maxima | open | Missing loads, quiescent-only amplifier budgets and PTC temperature derating remain. |
| 25. Incomplete BOM | partly | PTC suffix and several MPNs corrected; critical capacitor, bead and switch specifications remain incomplete. |
| 26. Contradictory documentation | open | VREF, grounding, loaded levels and threshold justifications remain inconsistent. |

**Checked and found sound**

- A fresh netlist matched the supplied export: **1,116 pin-to-net assignments, zero differences**, and matching component properties. PCB DRC reported **zero schematic-parity differences**.
- ERC reported **zero violations under the project’s configured exclusions**. All five project checkers passed. DRC reported 499 unconnected items and 371 silkscreen-related violations; no other violation categories were reported.
- Independent PCB inspection found no pad copper within either score’s ±1 mm keepout. The PCB remains unrouted.
- TPS3808 SOT-23 pin mapping, MR/VDD connections and nominal **7.452 V** divider calculation are correct. Its 5 V supply is within rating once established.
- OPA1622 signal/supply pin mapping is correct. **Pad 11, V− and GND are connected to GND** in both schematic and PCB. Its guaranteed EN thresholds are compatible with a properly designed 5 V control signal.
- The headphone **3.3 Ω resistors precede the coupling capacitors and lie outside feedback**. The 470 µF capacitors are series coupling elements, not 470 µF shunt loads directly across the amplifier outputs.
- The fade FETs have common sources and opposing body diodes. There is no single forward body-diode path permanently shorting audio to VREF.
- SP724 mapping matches the vendor drawing: **1/3/4/6 inputs, 2 V−, 5 V+**. Normal 5 V mic bias is below its +9 V upper clamp rail.
- RX upper and lower 1N4148W clamps have correct polarity using **pin 1 = cathode**. For an isolated ±12 V step from normal bias, the 2.2 kΩ resistors constrain input current to roughly 5–6 mA even if internal clamps conduct first.
- The RX diodes’ specified capacitance is at most **2 pF each**; it is small beside the existing 100 pF RF capacitor. Their room-temperature leakage specification is compatible with this audio path; hot leakage remains a qualification item.
- BLEND implements the documented inverting unity gain per input, with +6.02 dB for equal in-phase inputs. Its two output selections no longer load a passive summing node.
- Both line-output TVSs connect jack-side signals to **LOUT_RET**, preserving transformer-domain isolation. Transformer winding connections and the 6–7 links remain correct.
- No unintended new connection was identified in the reviewed supervisor, fade, clamp, BLEND or headphone pin maps. `check_sch.py` reports all 15 sheet files clean.

**Could not verify**

- Actual mute audibility, headphone startup/shutdown pulse amplitude, or transistor/switch behavior across production and temperature variation.
- OPA1622 loop stability with the complete ribbon, ferrites, 10 nF filters, headphone cables and loads. Correct isolation topology alone does not establish phase margin.
- Routed RF immunity, ESD survival, crosstalk, noise, chassis contact impedance or current division.
- Final regulator/headphone thermal performance, thermal-via implementation, capacitor effective values, ribbon specifications and enclosure fit.
- Coordinated input surge survival and powered/unpowered connector-fault behavior without complete component ratings and test conditions.
- The external EE-process checklist linked from CLAUDE.md; retrieval failed.