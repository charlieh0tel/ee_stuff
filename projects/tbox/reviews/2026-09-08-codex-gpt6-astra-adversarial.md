**TBox is not ready for fabrication.** I found assembly-blocking footprint and placement errors, incorrect switch functions, an unintended chassis-ground path, and electrical faults affecting keying, protection, and headphone operation.

I reviewed the schematic connectivity, PCB placement, project documents, custom footprints, and Python tools. A fresh netlist matched the supplied export. ERC reported zero violations under the project configuration, and all four project checkers passed. Those results do not detect the defects below. No files were modified.

**1. BLOCKER — Components have been placed on the wrong snap-apart boards**

**Location:** [place_panel.py:409](/home/ch/src/ee_stuff/projects/tbox/tools/place_panel.py:409), `kicad/tbox.kicad_pcb`; multiple sheets.

The placer checks whether a footprint fits within the whole panel, without enforcing its assigned board’s boundaries. Its spiral search can cross a score line.

I found **38 footprint centers outside their schematic board’s region**. Examples:

| Refdes | Required board | Actual position, mm | Actual region |
|---|---|---:|---|
| U1101 | Front | 246, 58 | Control |
| U1102 | Front | 222, 93 | Control |
| U1201 | Front | 178, 70 | Control |
| R3201 | Rear | 221, 156 | Control |
| R3203 | Rear | 184, 163 | Control |
| FB2401 | Control | 191, 35 | Front |

This creates **14 additional nets crossing physical board boundaries without ribbon connections**, including `Net-(U1101A--)`, `/Front Board/Preamp A/MIC`, `Net-(Q3201-G)`, and `Net-(C2401-Pad2)`. Snapping the panel would separate parts of these circuits.

**Fix:** Enforce each footprint’s complete physical envelope within its assigned board during initial placement, refinement, and decoupling placement. Extend `check_boards.py` to check actual PCB coordinates and physical cross-boundary connectivity.

**2. BLOCKER — PCB controls do not align with the enclosure drawings**

**Location:** [place_panel.py:325](/home/ch/src/ee_stuff/projects/tbox/tools/place_panel.py:325), [setup_pcb.py:42](/home/ch/src/ee_stuff/projects/tbox/tools/setup_pcb.py:42), `panel-top.svg`, `panel-rear.svg`.

Top-panel coordinates represent control centers, but the script positions the **footprint origin** there.

For example, RV2201’s intended shaft position maps to PCB coordinate `(230,158)`. That is where its footprint origin sits; the footprint’s shaft center is actually `(237.5,160.5)`: **7.5 mm sideways and 2.5 mm longitudinally wrong**. RV2401 has the same offset.

Separately, `place_panel.py` defines the rear board’s outer edge as **y=250 mm**, while `setup_pcb.py` and the PCB use **y=270 mm**. Rear connectors are therefore placed against an edge 20 mm inside the actual board.

**Fix:** Use explicit shaft/bushing/button datums for each footprint, transformed by rotation. Share one board-boundary definition between tools. Verify the assembled PCB-to-panel geometry before routing.

**3. BLOCKER — Both C&K custom toggle footprints have undersized terminal holes; the DPDT footprint also swaps spacings**

**Location:** `SW2103`, `SW3201–SW3204`; [7201 footprint:29](/home/ch/src/ee_stuff/projects/tbox/kicad/tbox.pretty/SW_Toggle_CK_7201_V-Bracket_Vertical.kicad_mod:29), [7101 footprint](/home/ch/src/ee_stuff/projects/tbox/kicad/tbox.pretty/SW_Toggle_CK_7101_AV2_Horizontal.kicad_mod).

Both footprints use **1.3 mm terminal drills**. The specified terminals are approximately **0.76 × 1.27 mm**, with a 1.48 mm diagonal; C&K specifies **1.85 mm PCB holes**.

The 7201 V-bracket footprint additionally uses:

- Terminal-column spacing: **6.35 mm**, vendor drawing **4.83 mm**.
- Bracket-leg spacing: **4.83 mm**, vendor drawing **6.35 mm**.

These parts cannot fit the patterns as drawn. Evidence: [C&K 7000-series mounting drawings](https://www.ckswitches.com/media/1394/7000toggle.pdf).

**Fix:** Correct both hole sizes and the DPDT spacings; adjust annular rings and clearances. Check actual samples against a dimensioned print before release.

**4. BLOCKER — The SJ-43514 headset footprint has a misplaced tip terminal and lacks the required board notch**

**Location:** J1103/J1303; [SJ-43514 footprint:43](/home/ch/src/ee_stuff/projects/tbox/kicad/tbox.pretty/Jack_3.5mm_CUI_SJ-43514_Horizontal.kicad_mod:43).

The tip pad is at `(4.5,7.9)` mm. The vendor drawing places it **3.6 mm from the centerline**, requiring `(3.6,7.9)` with the footprint’s coordinate convention. The **0.9 mm error** is incompatible with a 1.1 mm hole.

The claimed compatibility with the switched variant is also wrong: the provided pin-3/pin-5 holes are 2.5 mm apart, versus **3.2 mm** in the drawing.

The required **4.5 × 1.3 mm board-edge notch** appears only on F.Fab; the PCB outline does not implement it. The footprint itself admits that the rear terminal depth was scaled from an illustration.

Evidence: [Same Sky SJ-4351X drawing](https://www.sameskydevices.com/product/resource/sj-4351x.pdf).

**Fix:** Correct the dimensioned coordinates, obtain confirmation of the unspecified depth, and add the actual Edge.Cuts notch. Qualify the exact SJ-43514 part mechanically.

**5. BLOCKER — NJM4556AM is assigned an incompatible SOIC footprint**

**Location:** U2401/U2403, `monphones.kicad_sch`.

The BOM specifies **NJM4556AM**, a **DMP8** package, but assigns `SOIC-8_3.9x4.9mm_P1.27mm`.

DMP8 has a roughly **5 × 5 mm body**, **6.8 mm overall lead span**, and a recommended pad-row spacing of **6.10 mm**. The selected footprint has approximately **4.95 mm pad-row spacing**. Equal lead pitch does not make these packages interchangeable.

Evidence: [Nisshinbo DMP8 package and land pattern](https://www.nisshinbo-microdevices.co.jp/en/pdf/package/dmp8.pdf).

**Fix:** Assign a qualified DMP8 footprint to both amplifiers and update the PCB instances.

**6. BLOCKER — The selected switch functions reverse PTT/mute behavior and eliminate override OFF**

**Location:** SW2101/SW2102/SW2104/SW2105, `keylogic.kicad_sch`; SW2201, `txsum.kicad_sch`; SW2103.

| Function | Specified part code | Actual function | Required function |
|---|---|---|---|
| PTT A/B, intercom | PVA1**EE**… | Push-push, maintained | Momentary |
| Mute A/B | PVA1**OA**… | Momentary | Maintained |
| Override OFF/A→B/B→A | **7201**MD9V6BE | ON–NONE–ON | ON–OFF–ON |

Ordering these parts makes PTT remain asserted after release, makes mute release with the button, and provides no neutral override position. Evidence: [C&K PVA function codes](https://www.ckswitches.com/media/1343/pva.pdf), [7000-series functions](https://www.ckswitches.com/media/1394/7000toggle.pdf).

**Fix:** Use OA for momentary functions, EE for maintained mute, and the appropriate **7203** center-off configuration. Replace the `xxxxxx` PVA placeholders with complete orderable numbers.

**7. MAJOR — Phones jacks create additional GND–CHASSIS bonds**

**Location:** J1002/J1004, `front.kicad_sch`; NT3201; `DESIGN.md:300,379`.

The NRJ6HF-1 phones-jack sleeves are connected to **GND**. Neutrik explicitly specifies this model with a **“sleeve contact/frontpanel connection.”** Thus a conductive panel creates two extra physical GND–CHASSIS bonds, despite the schematic showing only NT3201. A plastic shell does not establish isolation for this model. Evidence: [Neutrik NRJ6HF-1 datasheet](https://www.neutrik.com/en/product/nrj6hf-1.pdf).

Headphone return current can consequently divide between ribbon grounds and the enclosure/NT3201 path, undermining the grounding rationale and coupling phones current into other signal returns.

**Fix:** Select explicitly isolated phones jacks, or redesign the grounding around deliberate multiple bonds. Verify sleeve-to-panel continuity using the actual jack and mounting hardware.

**8. MAJOR — The stated 16 Ω headphone rating exceeds the package’s thermal budget**

**Location:** U2401/U2403 and the 10 Ω output resistors, `monphones.kicad_sch`; `LEVELS.md:56`.

For one nominal −15 dBV source, the documented mix attenuation and gain produce approximately **0.948 Vrms** before the 10 Ω resistor. Into 16 Ω this requires **51.6 mA peak per amplifier** and supplies approximately **21.3 mW per ear**.

With both channels of one package driven, an ideal class-B estimate gives:

`PD ≈ 9 × (0.012 + 2 × 0.0516/π) − 2 × 0.948²/26 ≈ 0.334 W`

The NJM4556AM’s specified DMP8 dissipation is **300 mW at 25°C**. Even typical 8 mA quiescent current gives approximately **0.298 W**, leaving essentially no margin. The guaranteed 9 V output-swing tests also use **40 mA**, below the required current. Evidence: [NJM4556A datasheet, page 2](https://www.nisshinbo-microdevices.co.jp/en/pdf/datasheet/NJM4556A_E.pdf).

**Fix:** Use an output stage/package with a defensible continuous stereo thermal rating at the enclosure’s maximum ambient temperature. Validate both ears into 16 Ω with continuous tones and overloads; speech duty cycle cannot establish a continuous power rating.

**9. MAJOR — The claimed DE-9 ±12 V tolerance does not protect the RX inputs**

**Location:** C3401/C3402, R3403/R3404, U3401, `rxin.kicad_sch`; RX series resistors and D3202/D3203, `reario.kicad_sch`.

C3401/C3402 are polarized 10 µF capacitors, positive toward the approximately 4.5 V amplifier input. With the trim at maximum and **+12 V DC at the jack**, each capacitor sees approximately **7.5 V reverse bias**.

The **SMAJ15CA** devices do not clamp ±12 V. A stiff +12 V hot-plug step also couples through the capacitor toward the amplifier input. With roughly 200 Ω total series resistance, the initial internal-clamp current can approach **35 mA**, exceeding the OPA1678’s **±10 mA input-current limit**. External source impedance may reduce this, but the protection claim does not specify it. Evidence: [OPA1678 absolute maximum ratings](https://www.ti.com/lit/ds/symlink/opa1678.pdf).

**Fix:** Use bipolar or suitable nonpolar coupling capacitors, adequate voltage ratings, and coordinated external clamps/current limiting. Check powered and unpowered faults, including whether clamp current back-powers the 9 V rail.

**10. MAJOR — Rig keying has no defined fail-safe state during sequencing or a disconnected ribbon**

**Location:** Q3201/R3203, `reario.kicad_sch`; Q2104/Q2105, C2101/C2102, R2117 and PTT logic, `keylogic.kicad_sch`.

Q3201 has **no local gate-to-source pull-down**. Its pull-down is on the control board, reached through the ribbon. Disconnecting that ribbon leaves the rig-keying MOSFET gate floating and susceptible to retained charge, drain coupling, or RF.

During startup/brown-out, the active-low inputs, 100 nF filters, MOSFET inverters, and pull-ups settle at different rates. There is no supply supervisor inhibiting Q3201. C2103’s startup circuit operates the audio mutes, not the rig-key output.

**Fix:** Add a rear-board gate-to-source resistor and a hardware supply-valid inhibit that guarantees “unkeyed” until the control rail and input logic are valid. Test slow ramps, rapid cycling, brown-outs, held PTT, and disconnected ribbons.

**11. MAJOR — The TX indicator resistor has an unsupported dissipation**

**Location:** R2102, 680 Ω, `keylogic.kicad_sch`.

R2102 is assigned a generic **0603** footprint without a power-rated MPN. Its own annotation allows approximately **17 mA**, which dissipates:

`I²R = 0.017² × 680 ≈ 0.197 W`

At the upper input voltage it can be higher. This exceeds ordinary 0.1 W 0603 parts and leaves no justified thermal margin.

**Fix:** Reduce indicator current or specify a larger, appropriately derated resistor—for example a qualified 0.5 W part. Specify the LED and recalculate using maximum supply and minimum LED forward voltage.

**12. MAJOR — The decoupling placer moves the TPS7A4701 output capacitor away from the regulator**

**Location:** U2503/C2513, PCB; [place_decoupling.py:245](/home/ch/src/ee_stuff/projects/tbox/tools/place_decoupling.py:245).

The tool allocates bulk capacitors to the IC with the largest `Load_mA` on the same rail and sheet. That does not preserve regulator input/output capacitor ownership.

C2513, the TPS7A4701’s **47 µF output capacitor**, is approximately **28 mm from U2503**, near U2501 instead. TI calls for the output capacitor close to the regulator; its guaranteed stability requires at least 10 µF effective capacitance. Evidence: [TPS7A4701 capacitor requirements](https://www.ti.com/lit/ds/symlink/tps7a47.pdf).

**Fix:** Give mandatory regulator and reference capacitors explicit component/pin associations. Exclude them from generic bulk allocation. Place C2513 at U2503 OUT/GND with a short return loop and verify its effective capacitance at 9 V.

**13. MAJOR — Input fault protection is not coordinated for the stated battery/load-dump use**

**Location:** F2501, FB2501, D2501/D2502, `supply.kicad_sch`; `DESIGN.md:215`.

The intended 1812L050/60 PTC has a **10 A maximum fault-current rating**. A battery or high-current radio supply can exceed that unless upstream protection limits the prospective fault.

The SMBJ18A is downstream of an unspecified **0805 ferrite bead**. TVS surge current therefore passes through that bead. Neither its pulse-current capability nor coordination with the PTC’s trip time is established. A TVS clamp voltage below the regulator’s absolute maximum does not establish load-dump survival.

Evidence: [Littelfuse 1812L ratings and trip data](https://www.littelfuse.com/~/media/electronics/datasheets/resettable_ptcs/littelfuse_ptc_1812l_datasheet.pdf.pdf).

**Fix:** Specify source fault current and surge waveform/energy. Provide properly rated upstream fusing or a protected input stage; place the main surge path ahead of vulnerable filter components. Verify TVS energy, fuse clearing, diode stress, and sustained overvoltage behavior.

**14. MAJOR — Startup muting does not suppress headphone or downstream startup transients**

**Location:** C2103/R2121, U1201/U1401/U2301; U3401 and U2401/U2403.

The startup hold mutes the two microphone paths. It does not disconnect the headphones or mute the RX chain.

RX input bias settles through **100 kΩ × 10 µF ≈ 1 s**, while VREF and the gain-leg capacitors have different time constants. The headphone **470 µF output capacitors** must also charge toward the amplifier’s roughly 4.5 V output bias through connected loads. Turning the volume down does not remove that output-bias charging transient.

**Fix:** Add a defined headphone startup/shutdown sequence, using output disconnection or an amplifier with suitable mute and controlled startup. Release it after the slowest relevant bias node settles, and assert it promptly on power loss. Measure the resulting pulse at the headset load.

**15. MAJOR — The mute circuit cannot provide the claimed pop-free switching**

**Location:** U1201/U1401/U2301, `mute.kicad_sch`; `DESIGN.md:79`; `LEVELS.md:32`.

The documentation assumes the switching step is only amplifier offset. That is true only when the instantaneous audio signal is zero.

Switching from an audio waveform to VREF creates a step equal to the waveform’s instantaneous amplitude, even with perfectly matched DC levels. At 0 dBV sine-wave level this can approach **1.4 V**. The TS12A12511 also has finite charge injection. Evidence: schematic SPDT topology and [TS12A12511 switching characteristics](https://www.ti.com/lit/ds/symlink/ts12a12511.pdf).

**Fix:** Use controlled gain ramps or appropriate zero-crossing switching, with sequencing for override/intercom. Correct the pop-free claim until measured. Simply slowing the logic-control edge is not an audio fade.

**16. MAJOR — LO gain cannot reach the documented nominal level**

**Location:** U1101/U1301 and gain selection, `preamp.kicad_sch`; RV2201/RV2202, `txsum.kicad_sch`; `LEVELS.md:24,38`.

Each preamp stage has gain approximately **10.09**, or **20.08 dB**:

| Source and mode | Actual preamp output |
|---|---:|
| −57 dBV dynamic, HI | −16.84 dBV |
| −45 dBV electret, LO | −24.92 dBV |

LO is approximately **8 dB below** the common −17 dBV target. The level pot attenuates; it cannot supply the claimed positive adjustment. Even fully open, one nominal electret channel followed by the +6 dB summer reaches only approximately **−18.9 dBV**, below the −15 dBV bus target.

**Fix:** Revise the gain allocation—for example, approximately +28 dB LO and +40 dB HI—or provide additional adjustable gain. Recalculate source coverage using the pot’s actual attenuation range.

**17. MAJOR — BLEND loading prevents the nominal line-output level**

**Location:** R3301/R3302, J3301/J3302, RV3302/RV3303, `rigout.kicad_sch`.

The two 22 kΩ blend resistors present an **11 kΩ source impedance**. One selected 10 kΩ output trim loads that by **−6.44 dB**; selecting BLEND for both outputs presents 5 kΩ and produces **−10.10 dB** loading.

Even for equal, in-phase −15 dBV sources—the favorable case—the +4.86 dB drivers yield approximately:

- One BLEND destination: **−16.6 dBV** before transformer loss.
- Two BLEND destinations: **−20.2 dBV** before transformer loss.

The trims are already at maximum and cannot restore −10 dBV. Changing one output’s source selection also changes the other BLEND output’s level.

**Fix:** Buffer BLEND before distributing it, and set its gain explicitly. Recalculate loaded levels for every jumper combination.

**18. MAJOR — Connector protection allows RF/ESD onto the ribbon and signal ground**

**Location:** Front mic/phones jacks; FB2401–FB2404 and C2403/C2404/C2411/C2412; rear PTT inputs; J3303.

The protection arrangement is incomplete in ways that matter in a transmitter environment:

| Interface | Finding |
|---|---|
| Front phones, including TRRS | Filters belong to the control-board amplifier sheet, so external interference reaches the front board and ribbon before filtering. No dedicated connector ESD clamps are provided. |
| Front mic | Beads/capacitors and small series resistors do not establish a safe ESD discharge path; shunt currents enter circuit ground. |
| Rear PTT | Input clamps are on the control board after the ribbon. |
| Isolated line out | The RF shunts are upstream of the secondary DC-block capacitors; there is no dedicated jack-side surge clamp. |
| DE-9 audio | The 15 V TVS threshold does not protect the 9 V amplifier inputs, as demonstrated in finding 9. |

**Fix:** Put coordinated RF and ESD protection at each connector entry. Route external common-mode discharge currents to the intended chassis structure; preserve line-output isolation by protecting its secondary domain appropriately. Specify bead impedance curves and pulse ratings rather than only “600 Ω.”

**19. MAJOR — Score lines do not constrain copper or routing**

**Location:** [setup_pcb.py:139](/home/ch/src/ee_stuff/projects/tbox/tools/setup_pcb.py:139), `tbox.kicad_pcb`.

The internal separation lines at y=50 and y=180 are drawing-layer graphics. They are not board edges or all-layer copper keepouts. Normal routing and zone filling can cross them, and ordinary outer-edge clearance rules will not protect those cuts.

After depanelization, such tracks break; copper planes extending into scores also create exposed copper and possible burr/short risks.

**Fix:** Add fabricator-qualified score clearances on every copper layer, prohibit routing across them, and define separate board-plane regions. Add a checker for copper and component clearance to every separation line.

**20. MAJOR — The TY-250P footprint silently loses its body and courtyard**

**Location:** T3301/T3302; [TY-250P footprint:85](/home/ch/src/ee_stuff/projects/tbox/kicad/tbox.pretty/Transformer_Triad_TY-250P.kicad_mod:85).

An extra closing parenthesis ends the footprint before its F.Fab, courtyard, and silkscreen graphics. KiCad loads the pads but ignores the trailing graphics.

I verified that the PCB transformer instances have **zero graphical items**. Placement therefore underestimates the approximately 18 × 23 mm transformer body and cannot reliably avoid collisions.

`check_footprints.py` passes this file because it checks only existence.

**Fix:** Correct the expression structure, update both PCB instances, and recheck spacing. Validate exactly one complete footprint expression, successful parsing, and required courtyard/body geometry.

**21. MAJOR — The power checker silently undercounts missing or malformed loads**

**Location:** [power_model.py:189](/home/ch/src/ee_stuff/projects/tbox/tools/power_model.py:189), [check_power.py:75](/home/ch/src/ee_stuff/projects/tbox/tools/check_power.py:75).

Missing `Load_mA` fields are skipped. Unparseable values produce warnings but do not cause a failing exit status.

In-memory adversarial checks demonstrated:

- Removing U2401’s annotation lowers the 9 V maximum from approximately **250 to 160 mA**, without a warning.
- Making it malformed produces the same undercount, with a warning but a passing result.
- An empty parsed netlist can produce zero loads and a passing budget.

Numeric parsing also lacks adequate checks for negative/nonfinite values and `typ > max`.

**Fix:** Require valid, finite annotations for an explicit inventory of current-consuming parts, with deliberate exemptions. Reject malformed/empty netlists, invalid converter topology, unattributable loads, and invalid numbers. Treat model-integrity warnings as failures.

**22. MAJOR — The power-tree generator can delete valid schematic content**

**Location:** [gen_power_tree.py:58](/home/ch/src/ee_stuff/projects/tbox/tools/gen_power_tree.py:58), `strip_managed()`.

The function counts parentheses without respecting quoted strings. Parentheses inside a valid text property therefore alter its perceived expression depth.

An in-memory reproduction with a managed text string containing an unmatched literal `(` caused the function to consume the remaining schematic tail. The normal generator subsequently writes that result.

**Fix:** Use the existing string-aware expression parser or a proper s-expression parser. Validate the resulting complete schematic before writing, and use atomic replacement. Include quoted parentheses, escaped quotes, and backslashes in parser tests.

**23. MINOR — The 3.5 mm mic jacks short a mono TS microphone plug**

**Location:** J1101/J1301, `preamp.kicad_sch`; adapter description in `DESIGN.md:95`.

Tip and ring are hard-connected. Inserting a TS plug makes the jack’s ring contact touch the plug sleeve, grounding the microphone signal through that connection.

The document specifies TRS jacks but describes adapter pigtails only as having a “3.5mm mic plug.” A normal mono pigtail built from that instruction will fail.

**Fix:** Define the adapter’s exact contact wiring and required plug type. Prefer a TS-compatible mic input arrangement if mono plugs are intended to work; do not hard-short tip and ring indiscriminately.

**24. MINOR — Load annotations and rail capabilities are not defensible maxima**

**Location:** U1101/U1301 and other OPA1678s; U2503; R1101/R1301; [power_tree.json](/home/ch/src/ee_stuff/projects/tbox/power_tree.json).

Examples:

- OPA1678 annotations of **4/5 mA per dual** principally describe quiescent current and omit output-load current; the full-temperature quiescent limit can also exceed 5 mA per dual.
- U2503’s **1 mA** corresponds to the no-load ground-current limit, not a guaranteed value across output load.
- Each 2.2 kΩ microphone-bias resistor is annotated **0/1 mA**. A grounded mic line draws approximately **2.2 mA**.
- Rear 10 kΩ PTT pull-ups consume approximately **0.9 mA each** when asserted.
- F2501’s **500 mA hold rating applies at 20°C**; the manufacturer’s reference derating is **400 mA at 50°C**.

Evidence: [OPA1678](https://www.ti.com/lit/ds/symlink/opa1678.pdf), [TPS7A4701](https://www.ti.com/lit/ds/symlink/tps7a47.pdf), [1812L temperature derating](https://www.littelfuse.com/~/media/electronics/datasheets/resettable_ptcs/littelfuse_ptc_1812l_datasheet.pdf.pdf).

**Fix:** Define operating scenarios, temperature, output loading, and included faults; annotate consistently. Recalculate the budget rather than presenting the current total as a guaranteed maximum.

**25. MINOR — Critical BOM fields remain insufficient for procurement and electrical verification**

**Location:** F2501, C2513, input capacitors, ferrites, indicator LEDs, PVA switches.

F2501 specifies **1812L050/60DR**, whereas the manufacturer’s ordering table specifies **1812L050/60MR** for this variant. Evidence: [Littelfuse ordering table, page 7](https://www.littelfuse.com/~/media/electronics/datasheets/resettable_ptcs/littelfuse_ptc_1812l_datasheet.pdf.pdf).

C2513 is merely “47u X7R” in 1210, without voltage rating or MPN. Its effective capacitance at 9 V cannot be checked. Similar omissions prevent verification of capacitor voltage stress, ferrite current capability, LED current limits, and final control heights.

**Fix:** Complete exact MPNs or controlled substitution specifications for electrically and mechanically critical parts. Gate voltage rating, effective capacitance, resistor dissipation, ferrite current, and complete switch ordering codes.

**26. MINOR — Remaining documentation claims contradict the circuit or omit loading conditions**

**Location:** `DESIGN.md:234,379,387`; `LEVELS.md:28,68,80`.

The discrepancies could cause incorrect layout or commissioning:

- **VREF is not “DC bias only.”** Phones and rig-output gain-setting resistors return to VREF, and several pots/mix networks load it with audio current. Its noise and impedance must be analyzed with the actual topology.
- The grounding section says TRRS ring 2 should bond to chassis, while the board-partition section and schematic use **GND**. Following the former instruction would introduce another bond.
- The nominal MIC-mode calculation is approximately **4.8 mV open circuit**, but only **2.2 mV into 600 Ω** with the approximately 690 Ω source resistance. The trim can compensate, but the nominal setting is wrong for that load.
- The line-output table does not budget transformer insertion loss and winding/source resistance consistently. An attenuator cannot compensate loss once it is fully open.
- The TS12A12511 **2.4 V VIH** figure cited for “10 V” belongs to the dual-supply condition, not a general 10 V single-supply guarantee. The actual control voltages have useful margin, but the stated justification is incorrect. Evidence: [TS12A12511 electrical tables](https://www.ti.com/lit/ds/symlink/ts12a12511.pdf).

**Fix:** Rewrite these statements from the netlist, with explicit load impedances, jumper settings, temperature, and supply conditions.

**Ribbon connectivity audit**

At the schematic level, both ribbons are straight-through and their endpoint pin assignments match. All **22 unique crossing nets** are accounted for:

| Net | Front↔Control: J1005/J2001 | Control↔Rear: J2002/J3001 |
|---|---:|---:|
| GND | 1,3,6,8,10,17,18,21,22,25,26 | 1,3,5,8,10,12,14,18,23,25 |
| +9V | 2,4 | 4,6 |
| VREF | 5 | 7 |
| BIAS_5V | — | 2 |
| PRE_A_OUT | 7 | — |
| PRE_B_OUT | 9 | — |
| MUTE_A | 11 | — |
| MUTE_B | 12 | — |
| GAIN_A_HI | 13 | 19 |
| GAIN_B_HI | 14 | 20 |
| BIAS_A | 15 | 21 |
| BIAS_B | 16 | 22 |
| PH_A_L | 19 | — |
| PH_A_R | 20 | — |
| PH_B_L | 23 | — |
| PH_B_R | 24 | — |
| TX_MIX | — | 9 |
| RX_L_BUS | — | 11 |
| RX_R_BUS | — | 13 |
| PTT_A_IN | — | 15 |
| PTT_B_IN | — | 16 |
| PTT_ACTIVE | — | 17 |

Control↔Rear pins 24 and 26 are unused.

The intended partition keeps preamps and microphone switching on Front, supply/summing/phones amplifiers on Control, and rig protection/transformers on Rear. Raw input power reaches Control by pigtail; the full supply current does not traverse either ribbon.

The Front↔Control ribbon nevertheless carries headphone output current: approximately **52 mA peak per signal conductor** at the stated single-source level into 16 Ω, with up to approximately **207 mA instantaneous summed return current** for four in-phase channels. Ground interleaving exists, but cable resistance, shared-return crosstalk, and capacitive loading cannot be qualified without cable specifications. Finding 1 invalidates this intended partition in the present PCB placement.

**Checked and found sound**

- TPS7A4701 ANY-OUT connections select **1.4 + 0.4 + 0.8 + 6.4 = 9 V**; SENSE/FB connects to OUT. Low-ESR ceramic output capacitance is appropriate—there is no LM2940-style minimum-ESR requirement.
- The stated **385 mA thermal calculation** is arithmetically consistent with 15 V input, 50°C ambient, 125°C junction, and 32.5°C/W. Achieving that thermal resistance remains unverified.
- ADP7142 fixed-output sense wiring and the bias-rail RC arrangement are coherent. The VREF buffer senses before its 10 Ω isolation resistor, leaving the 470 µF reservoir outside the feedback loop.
- Preamp and RX feedback polarities are correct; the TX summer implements approximately −2 gain. Normal-operating coupling-cap polarities and headphone output-cap polarity are consistent with the DC biases.
- TS12A12511 COM/NC/NO and supply pin assignments are correct. Calculated steady-state control highs exceed approximately 6 V in the loaded cases examined.
- TY-250P primary/secondary pin connections and the 6–7 series link are correct; coupling prevents intentional winding DC. **600:600 Ω operation is explicitly allowed by Triad’s footnote**, despite the main 1 kΩ rating. Nominal voltage is below its stated 4.2 Vrms limit. [Triad TY-250P datasheet](https://www.triadmagnetics.com/products/ty-250p/)
- Switchcraft 35RAPC contact-to-pad mapping agrees with its drawing. CTIA microphone-on-sleeve/ring-2-return mapping is electrically correct.

**Could not verify**

- Routed stability, RF immunity, ESD survival, crosstalk, noise, mute depth, startup pulse amplitude, transformer low-frequency distortion, or thermal performance. The PCB has no tracks or copper zones.
- The assumed TPS7A4701 thermal resistance. Its footprint currently supplies nine thermal holes, while TODO calls for at least sixteen; copper geometry and enclosure temperature are unresolved.
- Final capacitor effective values/ratings, ferrite characteristics, complete control heights, ribbon length/AWG/capacitance, and Powerpole/upstream-fuse details.
- Physical mounting isolation, contact resistance through finished panels, and full enclosure fit with actual parts.
- The SJ-43514’s undocumented terminal-depth dimension and complete vendor qualification of the Alpha pot variants.
- Final fabrication DRC and score-process compatibility. ERC was clean, but the project disables checks including footprint-filter mismatch.
- The external EE-process checklist referenced by CLAUDE.md; its linked content could not be retrieved.