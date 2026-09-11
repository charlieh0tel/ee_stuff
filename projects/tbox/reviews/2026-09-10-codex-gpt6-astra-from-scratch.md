**TBox independent design review — revision `5f28342092c32e6b086ae165e92a86fbd587ea97`**

**Do not release this revision for fabrication.** I found definite footprint errors, incompatible panel geometry, headphone protection that conducts on normal audio, and insufficiently driven power-fail inhibition. The mute and headphone start-up circuits also have calculable problems beyond the bench uncertainties already acknowledged.

I read the rendered schematic first, then traced connectivity in the supplied netlist and checked the source schematic, PCB, documentation, tools, and vendor PDFs. I did not read `reviews/`. Checker counterexamples were exercised in memory; no project files were changed. The expected unrouted connections are not findings.

Datasheet page references below refer to the PDFs in `third_party/datasheets/`.

---

**1. BLOCKER — Two custom jack footprints are mirrored; the Switchcraft footprint also swaps two dimensions**

**Location:** [Switchcraft footprint](/home/ch/src/ee_stuff/projects/tbox/kicad/tbox.pretty/Jack_3.5mm_Switchcraft_35RAPCxxH3_Horizontal.kicad_mod:29), J1101/J1301/J3201/J3203; [SJ-43514 footprint](/home/ch/src/ee_stuff/projects/tbox/kicad/tbox.pretty/Jack_3.5mm_CUI_SJ-43514_Horizontal.kicad_mod:29), J1103/J1303.

Both vendor drawings explicitly show the PCB layout from the component/top side. The project footprints transpose the drawing axes without the sign change required for a rotation, producing a reflection.

For the footprint convention used here—jack nose toward negative Y—the coordinates should be:

| Footprint/pad | Current `(x,y)`, mm | Required `(x,y)`, mm |
|---|---:|---:|
| Switchcraft R, vendor pin 2 | −5.2, 9.8 | +5.2, 9.8 |
| Switchcraft RN, pin 3 | −2.5, 8.4 | +2.5, 8.4 |
| Switchcraft T, pin 5 | +4.0, 5.4 | **−4.5, 5.4** |
| Switchcraft TN, pin 4 | +4.5, 13.0 | **−4.0, 13.0** |
| SJ-43514 S, pin 1 | −4.8, 2.9 | +4.8, 2.9 |
| SJ-43514 R2, pin 4 | +4.5, 2.9 | −4.5, 2.9 |
| SJ-43514 T, pin 2 | +3.6, 7.9 | −3.6, 7.9 |

**Evidence:** `Switchcraft_35RAPC__H3_drawing.pdf`, p. 1, “RECOMMENDED PC BOARD COMPONENT SIDE”; `SameSky_SJ-4351X.pdf`, p. 2, “PCB LAYOUT TOP VIEW.”

The Switchcraft drawing places pin 4 at a 4.00 mm lateral offset and pin 5 at 4.50 mm; the footprint reverses those dimensions in addition to mirroring them. The SJ-43514 tip hole is displaced laterally by 7.2 mm. These exceed drill tolerances by orders of magnitude.

The PCB footprints are on the front side; their placement rotations do not compensate for a reflection.

**Fix:** Rebuild both footprints from the explicitly identified top views, including body outlines, slot orientation, and auxiliary holes. Confirm SJ-43514 rear-pin depth from vendor CAD or a physical sample—the existing 10.8 mm depth is admittedly scaled from the drawing. Check a 1:1 print against actual parts.

After editing the libraries, explicitly update the footprints embedded in the PCB. `sync_pcb.py` only reloads an existing footprint when its library identifier changes; changing the library file under the same name will leave the old geometry on the board.

---

**2. BLOCKER — The panel drawings cannot accommodate the selected jacks on a common horizontal PCB**

**Location:** [panel-front.svg](/home/ch/src/ee_stuff/projects/tbox/panel-front.svg:29), [panel-rear.svg](/home/ch/src/ee_stuff/projects/tbox/panel-rear.svg), [place_panel.py](/home/ch/src/ee_stuff/projects/tbox/tools/place_panel.py:148), front/rear jack placement.

The front drawing places every jack axis at `cy="24"`. The selected jack families have different axis heights above the PCB:

| Family | Axis height above PCB |
|---|---:|
| SJ-43514 TRRS | 2.25 mm |
| Switchcraft 35RAPCxxH3 | approximately 3.0 mm |
| SJ1-3533NG phones | 7.0 mm |

**Evidence:** `SameSky_SJ-4351X.pdf`, p. 2; `Switchcraft_35RAPC__H3_drawing.pdf`, p. 1; `SameSky_SJ1-353xNG.pdf`, p. 2.

The TRRS and SJ1-3533NG axes differ by **4.75 mm**. A common change in PCB mounting height cannot make both align with holes on the same horizontal line. `DESIGN.md` correctly says the holes need per-part heights, but the front drawing does not implement that.

The rear drawing defines the PCB top at panel Y = 53 mm. It puts both Switchcraft PTT jacks and the SJ1-3533NG line-out jack at Y = 47 mm, implying a common 6 mm axis height. Their expected positions are approximately Y = 50 mm and Y = 46 mm respectively.

`front_positions()` explicitly extracts only the front jack X coordinates. Thus the placement generator cannot detect or resolve the vertical inconsistency.

**Fix:** Establish one PCB-to-enclosure datum per board and generate panel centers from each selected part’s axis height. Also establish the actual panel-face offset for each footprint; placing the nearest pad 2 mm inside the board edge is not a mechanical mating datum. Verify the complete assembly, including nuts, shoulders and board notches, before fixing the board outline and panel drilling.

---

**3. BLOCKER — SP724 protection clips the negative half-cycle of headphone audio**

**Location:** [front.kicad_sch](/home/ch/src/ee_stuff/projects/tbox/kicad/front.kicad_sch), U1001; [preamp.kicad_sch](/home/ch/src/ee_stuff/projects/tbox/kicad/preamp.kicad_sch), U1104/U1304.

The headphone signals are AC-coupled and centered on ground, but their SP724 arrays are referenced to GND and +9 V.

The authoritative nodes include:

- `PHJ_A_L`: J1001.T, J1002.T, J1103.T, U1001.1, U1104.1.
- `PHJ_A_R`: J1001.R, J1002.R, J1103.R1, U1001.3, U1104.3.
- Corresponding B signals connect to U1001.4/.6 and U1304.1/.3.
- Every array’s pin 2 is GND and pin 5 is +9 V.

**Evidence:** `Littelfuse_SP724.pdf`, p. 1, describes triggering about one base-emitter drop below V−. Page 3, Figure 2, shows substantial conduction in the approximately 0.8–1.1 V forward-drop region.

The level plan expects:

\[
V_{\text{phones,16Ω}}\approx0.79\ {\rm V_{RMS}}
\quad\Rightarrow\quad V_{\rm negative\ peak}\approx-1.12\ {\rm V}
\]

For 32 Ω headphones:

\[
0.86\sqrt2\approx1.22\ {\rm V_{peak}}
\]

These normal signal excursions enter the protector’s conducting region. The result is asymmetric clipping and extra amplifier current. The coupling capacitor can also acquire a rectified offset.

This is independent of the headphone amplifier’s otherwise adequate output capability.

**Fix:** Use protection whose nonconducting range accommodates the full bipolar headphone waveform, including permitted peaks. Establish its clamping voltage and energy/current compatibility with the protected circuitry. Replace every inappropriate parallel clamp on these nets, including the TRRS-associated arrays; replacing U1001 alone leaves the defect.

---

**4. BLOCKER — The power-fail hold cannot guarantee either audio mute or PTT inhibition**

**Location:** [keylogic.kicad_sch](/home/ch/src/ee_stuff/projects/tbox/kicad/keylogic.kicad_sch), R2122, Q2108/Q2109, D2120/D2121; [mute.kicad_sch](/home/ch/src/ee_stuff/projects/tbox/kicad/mute.kicad_sch), R1201/R1401 and associated fade networks; [DESIGN.md](/home/ch/src/ee_stuff/projects/tbox/DESIGN.md:192).

R2122 is a **100 kΩ** pull-up supplying both mute cells. Their pull-downs and fade-gate bleeders form a substantial DC divider. `MUTE_HOLD` is not approximately the supply voltage.

Consider the valid state with manual mutes released and the optional PTT-gating jumpers open. Let \(H\) be `MUTE_HOLD`, and approximate each conducting diode drop as 0.6 V. Each mute cell presents a 100 kΩ pull-down plus a diode/47 kΩ/470 kΩ branch:

\[
\frac{V_S-H}{100k}
=
2\left[
\frac{H-0.6}{100k}
+
\frac{H-1.2}{517k}
\right]
\]

This gives:

| Analog supply | `MUTE_HOLD`, Q2109 gate | `MUTE_A/B` | Fade gate, absolute |
|---|---:|---:|---:|
| 9.0 V | 3.15 V | 2.55 V | 1.77 V |
| 7.5 V | 2.71 V | 2.11 V | 1.37 V |
| 6.0 V | 2.26 V | 1.66 V | 0.97 V |

These are optimistic steady-state values: they omit additional loading while the switch-control capacitor is charging or its clamp remains conducting.

**Evidence:** `Diodes_2N7002.pdf`, p. 2, allows \(V_{GS(th)}=2.5\) V at only 250 µA. On-resistance is specified at 5 V and 10 V gate drive. At a 6 V brown-out plateau, the calculated 2.26 V gate drive does not guarantee that Q2109 can sink the PTT logic’s milliampere-scale pull-up current.

The audio side also lacks a guaranteed high. `DESIGN.md` incorrectly treats the TS12A12511’s 2.4 V logic-high specification at a 10 V **total bipolar supply** as a 10 V single-supply specification. In `TI_TS12A12511.pdf`, the ±5 V table on p. 5 gives 2.4 V; the 12 V single-supply table on p. 6 gives 5 V. Neither establishes correct operation from this approximately 2.55 V hold signal at a 9 V supply.

The supervisor’s threshold and delay are correctly calculated; the circuit driven by its output is the problem. The documented acceptance of a 15–35 ms delay does not address inadequate steady-state gate drive.

**Fix:** Give power-fail inhibition a sufficiently strong, explicitly budgeted driver. Keep PTT inhibition independent of charging the audio mute capacitors, and choose a switching device with guaranteed behavior at the minimum available gate voltage. Verify slow ramps and brown-out plateaus with PTT both held and released, measuring `PWR_OK`, `MUTE_HOLD`, switch control, and the rig PTT output.

---

**5. MAJOR — On microphone unmute, the switch-control capacitor backfeeds `MUTE` and reverses the intended sequence**

**Location:** [mute.kicad_sch](/home/ch/src/ee_stuff/projects/tbox/kicad/mute.kicad_sch), microphone instances R1204/C1203/Q1203/Q1204 and R1404/C1403/Q1403/Q1404; [DESIGN.md](/home/ch/src/ee_stuff/projects/tbox/DESIGN.md:91).

The documentation says nothing discharges through the source-only `MUTE` line, and that Q1204 reconnects the analog switch within microseconds before the fade shunt releases.

There is a direct discharge path:

`SW_CTL` → R1204, 100 kΩ → `MUTE_A` → R1201, 100 kΩ → GND.

When the diode-OR driver releases, charged C1203 therefore holds `MUTE_A` high. Q1203 remains on and prevents Q1204 from promptly discharging `SW_CTL`.

Ignoring gate leakage, immediately after release:

\[
V_{\rm MUTE}\approx\frac{V_{\rm SW\_CTL}}2
\]

The initial switch-control decay constant is:

\[
(100k+100k)\times1\mu F=200\ {\rm ms}
\]

For an initial 8.3 V switch-control voltage, a representative handoff at `MUTE` = 2 V occurs after:

\[
t=200{\rm ms}\ln\left(\frac{8.3}{4}\right)\approx146{\rm ms}
\]

The precise handoff depends on transistor characteristics; it is plainly not microseconds.

Meanwhile the fade gate initially discharges with approximately:

\[
470k\times100nF=47{\rm ms}
\]

Starting around 7 V, after 20 ms it is approximately 4.57 V, while `SW_CTL` is still approximately 7.51 V. The shunt no longer has useful positive gate drive above the 4.5 V audio reference, yet the analog switch remains disconnected. Reconnection consequently occurs without the intended protective shunt, allowing a waveform step and click.

The intercom instance has an active transistor pull-down on `IC_MUTE`, so this particular source-only release failure applies to the two microphone instances.

**Fix:** Isolate the timing capacitor from the command node with a buffer or an appropriately designed charge/discharge network. Make switch reconnection explicitly precede shunt release. Verify release from manual mute, override, and PTT gating separately; their source impedances matter.

---

**6. MAJOR — The fade MOSFETs receive substantially less gate drive than the level plan assumes**

**Location:** [mute.kicad_sch](/home/ch/src/ee_stuff/projects/tbox/kicad/mute.kicad_sch), all three instances; [LEVELS.md](/home/ch/src/ee_stuff/projects/tbox/LEVELS.md:32).

The claimed approximately 3.5 V gate drive above VREF neglects the diode drop and the 47 kΩ/470 kΩ divider.

For a steady mute command \(M\):

\[
V_G\approx(M-0.6)\frac{470}{470+47}
\]

At the quiescent audio bias, the useful gate drive is \(V_G-4.5\):

| Mute command | Fade gate | Gate drive above VREF |
|---|---:|---:|
| 8.3 V | 7.00 V | 2.50 V |
| 7.4 V | 6.18 V | 1.68 V |
| 6.8 V | 5.64 V | 1.14 V |

Even the favorable 8.3 V command provides only 2.5 V.

**Evidence:** `Diodes_2N7002.pdf`, p. 2, specifies threshold up to 2.5 V at 250 µA and maximum \(R_{DS(on)}=7.5\,Ω\) at 5 V. It does not establish two approximately 4 Ω channels at the available drive.

The stated attenuation:

\[
20\log_{10}\left(\frac{8}{220+8}\right)\approx-29.1{\rm dB}
\]

is correct **if** the pair actually supplies 8 Ω. The circuit does not establish that condition. A permitted high-threshold pair can provide little pre-attenuation before the analog switch moves.

**Fix:** Recalculate the entire loaded command-to-gate path, then use devices with guaranteed resistance at the actual minimum drive or provide a stronger/higher gate drive. Measure attenuation versus gate voltage and audio amplitude across temperature. Merely adjusting the timing capacitors cannot repair insufficient shunt conductance.

---

**7. MAJOR — Headphone precharge neither finishes within the delay nor matches the enabled amplifier’s DC output**

**Location:** [monphones.kicad_sch](/home/ch/src/ee_stuff/projects/tbox/kicad/monphones.kicad_sch), U2401/U2403, R2425–R2428, C2401/C2402/C2408/C2409, 150 kΩ feedback resistors; [DESIGN.md](/home/ch/src/ee_stuff/projects/tbox/DESIGN.md:205).

There are two independent errors in the “no step at enable” argument.

**First, 1.26 seconds is insufficient charging time.** Even assuming the disabled amplifier is perfectly open-circuit:

\[
\tau=\left[1k+(16Ω\parallel4.7k)\right]470\mu F
=0.4775{\rm s}
\]

The supervisor delay is:

\[
t_D=\frac{220}{175}+0.0005=1.2576{\rm s}
\]

For a 4.5 V reference step at the start of that interval, the remaining error is:

\[
4.5e^{-1.2576/0.4775}=0.323{\rm V}
\]

When a low-impedance amplifier takes over, that represents roughly a 0.27 V initial pulse into 16 Ω after the 3.3 Ω build-out, decaying on approximately a 9 ms time scale.

Actual supply and reference ramps change the exact number; this is an illustrative calculation showing that the nominal timing does not imply complete precharge.

**Second, the enabled output does not equal VREF.** The OPA1622 has bipolar input bias current: `TI_OPA1622.pdf`, p. 5, gives 1.2 µA typical, 2 µA maximum at 25°C and 2.2 µA over temperature.

With volume at zero, the noninverting input is tied to VREF. The 150 kΩ feedback resistor creates an output displacement of approximately:

\[
|V_{\rm OUT}-V_{\rm REF}|\approx I_B\,150k
\]

That is approximately **180 mV typical**, potentially around **330 mV** over temperature, before adding offset voltage. Precharging to VREF cannot eliminate this mismatch, regardless of delay length. Its sign and interaction with residual capacitor error must be measured.

Finally, p. 18 explicitly warns that the disabled OPA1622 output is not high impedance and can be parasitically powered by an applied signal. The ideal charging calculation is therefore not a validated model of the actual disabled output.

**Fix:** Reduce and compensate the bias-current-induced offset, and sequence headphone connection against the amplifier’s actual settled output. A controlled output mute that remains active while the amplifier enables and settles is more defensible than assuming its disabled output can be precharged to the correct voltage. Test power-up, rapid cycling, power-down, and hot-plugging at minimum and maximum volume.

---

**8. MAJOR — Permanent precharge resistors inject headphone audio into the shared reference**

**Location:** [monphones.kicad_sch](/home/ch/src/ee_stuff/projects/tbox/kicad/monphones.kicad_sch), R2425–R2428; [supply.kicad_sch](/home/ch/src/ee_stuff/projects/tbox/kicad/supply.kicad_sch), R2504/C2507; [power_tree.json](/home/ch/src/ee_stuff/projects/tbox/power_tree.json:41).

The four 1 kΩ precharge resistors remain connected during normal operation. Each connects a headphone amplifier’s AC output, before the coupling capacitor, directly to VREF.

For approximately 0.95 Vrms output:

\[
I_{\rm injected}\approx0.95/1000=0.95{\rm mA_{RMS}}
\]

Two correlated outputs inject approximately 1.9 mA. At 150 Hz, treating the reference buffer as ideal before its 10 Ω isolation resistor and including approximately 490 µF of distributed reference capacitance:

\[
|Z_{\rm REF}|\approx
\left|\frac1{1/10+j2\pi(150)(490\mu F)}\right|
=2.12Ω
\]

Thus the first-order reference disturbance is approximately **4 mVrms**.

That disturbance does not cancel throughout the design. For example, at maximum volume and minimum monitor, the quiet headphone channel approximately has:

\[
V_{\rm OUT}=\frac{16}{3}V_{\rm RX}-\frac{13}{3}V_{\rm REF}
\]

Accounting for the quiet RX buffer’s own reference coupling still leaves roughly a −3.7 transfer from reference disturbance to headphone output. This predicts a quiet-channel disturbance on the order of 10–15 mVrms for the above example—crosstalk in the high −30 dB region, not an insignificant reference load.

The power model also reports VREF as zero load because `no_loads` exempts it. At start-up, the four precharge branches alone initially request approximately:

\[
4\times4.5/1k=18{\rm mA}
\]

versus the model’s 10 mA reference capability.

**Fix:** Disconnect the precharge resistors after their function is complete, or use a separate precharge reference that cannot carry audio into the shared bias network. Model reference source/sink current and impedance explicitly. Confirm with a one-channel-driven, other-channel-quiet test, especially near the bottom of the audio band.

---

**9. MAJOR — The entry protection and chassis-bond placement do not implement the claimed short discharge paths**

**Location:** [tbox.kicad_pcb](/home/ch/src/ee_stuff/projects/tbox/kicad/tbox.kicad_pcb), U3201, U1001, H1001, NT3201, J3203/J3206; [DESIGN.md](/home/ch/src/ee_stuff/projects/tbox/DESIGN.md:350).

Several actual distances contradict the claimed protection “at the jacks” and discharge loops of a few millimetres:

| Relationship | Footprint-origin distance |
|---|---:|
| U3201 to protected PTT-B jack J3203 | **228 mm** |
| U1001 to protected phones-B jack J1003 | **108 mm** |
| H1001 chassis stud to TRRS J1103 | **74 mm** |
| H1001 chassis stud to TRRS J1303 | **93 mm** |
| Rear net tie NT3201 to DE-9 J3206 | approximately **49 mm** |

These are placement distances, not routed trace lengths; routing cannot make the endpoint separation disappear.

For PTT B, the netlist path is J3203 → FB3202 → `PTT_B_IN` → U3201.3. One clamp near the other operator’s PTT jack cannot also provide a local clamp at this entrance.

For the DE-9, C3203–C3207 return to **GND**, and D3201–D3205 also clamp to GND. Their currents therefore enter the circuit ground network before reaching chassis through its bonds. Naming the connector grounds `CHASSIS` does not make those separate shunt returns local chassis paths.

**Evidence:** `Pin_1_Revisited.pdf`, pp. 1–2, explains the RF impedance of even short bonding wires; `Pin_1_Revisited_Part_2.pdf`, p. 1, Figure 2, depends on physical current paths and avoiding shared impedance. The present tens-to-hundreds-of-millimetres paths do not implement that condition.

Likewise, multiple chassis–GND ties plus ribbon ground conductors create parallel return paths. The statement that headphone current “never enters” ribbon ground is not electrically exact; current divides according to impedance.

**Fix:** Put suitable protection at each physical entrance and provide short, wide chassis connections at each relevant connector group. Separate connector RF diversion from downstream rail clamping deliberately. Verify the complete discharge loop, including the return connection, rather than only clamp-to-jack distance.

This establishes a placement/topology defect; the resulting RF susceptibility and ESD withstand level still require testing on the routed assembly.

---

**10. MAJOR — A source fuse does not establish compliance with the PTC’s 10 A maximum fault-current rating**

**Location:** [supply.kicad_sch](/home/ch/src/ee_stuff/projects/tbox/kicad/supply.kicad_sch), F2501; [DESIGN.md](/home/ch/src/ee_stuff/projects/tbox/DESIGN.md:413).

The source-envelope argument says that a supply fused at a few amperes bounds prospective fault current below the PTC’s 10 A maximum. A fuse does not clamp instantaneous current to its marked rating.

**Evidence:** `Littelfuse_1812L_PTC.pdf`, p. 2, specifies for 1812L050/60:

- 0.5 A hold;
- **10 A maximum fault current**;
- up to 0.15 s to trip at 8 A.

A 13.8 V bench/rig supply capable of delivering 20 A into a short remains consistent with the stated source category even if its branch is protected by a 3 A fuse. Current above 10 A can flow during the fuse’s clearing interval. No particular upstream fuse, clearing curve, or current-limited source is specified.

**Fix:** Specify a source with a demonstrated maximum fault current within the PTC rating, or choose input protection rated for the actual prospective current and coordinate it with the upstream fuse. Document the source/fuse combination that establishes the rating. This requirement also applies to stationary shack supplies.

---

**11. MAJOR — Critical capacitor ratings and several ordering identities are not established**

**Location:** [supply.kicad_sch](/home/ch/src/ee_stuff/projects/tbox/kicad/supply.kicad_sch), [monphones.kicad_sch](/home/ch/src/ee_stuff/projects/tbox/kicad/monphones.kicad_sch), rig-output circuitry, supplied `tbox-bom.csv`.

Numerous capacitors have a value and footprint but no MPN or sufficient rating fields. Consequently the schematic does not establish that the parts fitted will satisfy voltage, effective capacitance, ESR, ripple-current, or mechanical requirements.

Specific consequential examples:

| Parts | Requirement that remains unestablished |
|---|---|
| C2512, 10 µF on regulator input | Working/transient voltage and capacitance retained at input bias |
| C2510/C2511 on raw supply | Voltage rating |
| C2501/C2504, ADP7142 input/output | Effective capacitance and ESR across bias and temperature |
| C2401/C2402/C2408/C2409, 470 µF headphone coupling | Voltage, ESR and audio ripple-current ratings |
| C2507, 470 µF reference | Voltage, ESR and transient-current behavior |
| C3312/C3315/C3316, “10u NP” in 1206 | Actual nonpolar technology, voltage rating and retained capacitance |

**Evidence:** `ADI_ADP7142.pdf`, p. 4, requires at least 1.5 µF effective capacitance and specifies the allowed ESR range. “4u7” and an 0805 footprint do not establish either condition.

The raw-rail issue includes transients: `Bourns_SMBJ.pdf`, p. 2, gives a 29.2 V clamp value for SMBJ18A at its specified 10/1000 µs test current. A capacitor selected merely for 15 V nominal operation would not follow the stated protection envelope.

At the nominal headphone level, each coupling capacitor carries approximately:

\[
0.79/16\approx49{\rm mA_{RMS}}
\]

Its ripple rating therefore matters.

Several mechanical ordering identities also remain incomplete. The PVA `xxxxxx` strings are not orderable part numbers, and `TODO.md` misidentifies that placeholder as actuator height: the H2 portion already selects a height in the C&K ordering table. The exact DE-9 part and missing Alpha pot drawings also prevent complete mechanical verification.

The grouped BOM itself combines incompatible items. For example, “PTT A” groups D2102 and SW2101 together; “10u” groups different capacitor technologies and footprints. Such rows cannot represent one ordering item.

**Fix:** Assign orderable parts or complete procurement specifications before fabrication, because the eventual choices may change footprints. Group the purchasing BOM by MPN and package/rating identity, not value alone. These are unestablished ratings, not assertions that every generic capacitor will fail.

---

**12. MAJOR — The checkers accept counterexamples to the guarantees the workflow relies on**

**Location:** [check_sch.py](/home/ch/src/ee_stuff/projects/tbox/tools/check_sch.py:166), [check_boards.py](/home/ch/src/ee_stuff/projects/tbox/tools/check_boards.py:85), [check_footprints.py](/home/ch/src/ee_stuff/projects/tbox/tools/check_footprints.py:55), [check_placement.py](/home/ch/src/ee_stuff/projects/tbox/tools/check_placement.py:62), [power_model.py](/home/ch/src/ee_stuff/projects/tbox/tools/power_model.py:151), [sync_pcb.py](/home/ch/src/ee_stuff/projects/tbox/tools/sync_pcb.py:258).

I exercised the following counterexamples without modifying the project:

| Checker | Counterexample accepted | Cause and concrete correction |
|---|---|---|
| `check_sch.py` | Wire `(0,0)→(10,10)` with another wire ending at `(5,5)`, without the required explicit junction, produced no finding. | `interior()` handles only horizontal and vertical segments. Use general collinearity/segment tests, and include hierarchical sheet pins in geometry checks. |
| `check_footprints.py` | Replacing J1103’s footprint with an existing 0603 resistor footprint still passed. | It checks existence only, as its docstring says. Add pin/pad compatibility checks and a separate vendor-geometry approval record; existence cannot certify a footprint. |
| `check_boards.py` | One logical signal on four boards, with cable A joining boards 1–2 and cable B joining boards 3–4, passed despite no connection between the pairs. | It checks that every board has a connector, not that the signal’s cable graph is connected. Require connectedness per cross-board net. The current TBox cable maps themselves match. |
| `check_placement.py` | Moving R1104 to X = −10 mm, Y = 30 mm still passed. | It checks score-related Y bounds but no outer X bounds, and exempts outer Y edges wholesale. Check actual board boundaries with explicit allowed connector overhangs. |
| `check_placement.py` | A copper track crossing the front/control score passed. | It inspects footprint-pad net membership, not copper geometry. Require score checks on tracks/vias/zones, or explicitly rely on the corresponding DRC rule. The existing DRC keepout should catch this track; this is a limitation of the checker, not proof that the whole toolchain misses it. |
| `check_power.py` / model | Breaking R2503’s connection to `BIAS_5V` left the model reporting the rail as fed, without warnings. | `Rail_out` supplies an asserted relationship without proving the passive path. Traverse and verify the converter-to-rail connection. |
| `check_power.py` / model | Adding a 1 Ω resistor from VREF to GND without `Load_mA` produced no warning and left the calculated VREF load zero. | `no_loads` suppresses the very check that could disprove the assertion. Validate the assertion instead of exempting the rail. |
| `sync_pcb.py --dry-run` | Substituting the resistor footprint for J1103 reported a replacement and succeeded without reporting the missing jack pads. | Dry-run skips pad/net validation. Perform the complete update and validation in memory; suppress only the final save. |

There is also a real current counterexample in the ESD placement check: it uses the distance to the **nearest** protected jack. U3201 passes because it is near one PTT jack while protecting another 228 mm away.

Related generator limitations matter:

- `sync_pcb.py` does not refresh changed library geometry under an unchanged identifier—particularly consequential for finding 1.
- [gen_harness.py](/home/ch/src/ee_stuff/projects/tbox/tools/gen_harness.py:124) renders the first connector’s pin map without verifying the second. Invoke shared cable validation before generating the sheet.
- `gen_power_tree.py` prints model warnings but continues generating output. Invalid input should fail generation.
- [place_decoupling.py](/home/ch/src/ee_stuff/projects/tbox/tools/place_decoupling.py:29) recognizes only three named rails. The ADP7142 output before R2503 is an unnamed net, so its output capacitor is not reliably recognized by this mechanism. C2501 is currently approximately 15.9 mm from U2501, consistent with the acknowledged ownership problem. Use explicit capacitor ownership and verify placement after generation.
- `place_panel.py` uses hard-coded top-panel coordinates and discards the front panel’s vertical coordinates. It cannot prove mechanical agreement among the drawings and PCB.

**Fix:** Turn these counterexamples into regression fixtures, distinguish narrowly scoped checks from release guarantees, and add an independent final validation pass. A zero exit status presently does not establish the advertised physical or electrical properties.

---

**13. MAJOR — The stated microphone coverage and universal clipping guarantee exceed the circuit’s established limits**

**Location:** [LEVELS.md](/home/ch/src/ee_stuff/projects/tbox/LEVELS.md:8), preamp gain-range coverage and unity-gain OPA1678 buffers.

The actual preamp gains are:

\[
G_{\rm LO}=1+\frac{10k}{430}=24.256=27.696{\rm dB}
\]

\[
G_{\rm second}=1+\frac{10k}{3.3k}=4.030=12.107{\rm dB}
\]

\[
G_{\rm HI}=97.76=39.803{\rm dB}
\]

Using the document’s +6 dBV planning limit and 15 dB speech crest factor, maximum nominal inputs are:

\[
L_{\rm LO,max}=6-27.696-15=-36.70{\rm dBV}
\]

\[
L_{\rm HI,max}=6-39.803-15=-48.80{\rm dBV}
\]

The stated coverage to −32 dBV in LO and −45 dBV in HI therefore includes sources that clip before the level pot. For example:

\[
-32+27.696+15=+10.70{\rm dBV}
\]

The text notices this peak but still describes it as covered. Attenuation after the preamp cannot repair it.

Separately, the claimed universal “+8 dBV guaranteed” ignores input common-mode limits. `TI_OPA1678.pdf`, p. 8, gives an upper input common-mode boundary of \(V_+-2\) V. At 9 V supply, a unity-gain buffer centered at 4.5 V reaches that boundary at a positive amplitude of 2.5 V:

\[
20\log_{10}(2.5/\sqrt2)=+4.95{\rm dBV}
\]

Its input common-mode range is exceeded before the proposed universal output clipping limit. Moreover, the cited output-swing specification’s table conditions use ±15 V supplies; it is not itself a complete 9 V, all-load guarantee.

**Fix:** Specify headroom per stage, including input common-mode and actual output loading. Correct the guaranteed source ranges or add attenuation before the first gain stage. The nominal dynamic/electret examples remain plausible; the defect concerns the claimed limits.

---

**14. MINOR — The override toggle’s movement axis does not match the panel legend**

**Location:** SW2103 in [tbox.kicad_pcb](/home/ch/src/ee_stuff/projects/tbox/kicad/tbox.kicad_pcb); [panel-top.svg](/home/ch/src/ee_stuff/projects/tbox/panel-top.svg:79).

The panel specifies a left/right throw toward the winning operator. The placed switch is at 0°, with the three-contact row running along PCB Y.

**Evidence:** `CK_7000-series_toggles.pdf`, printed page F-13, shows the V6 bracket switch’s actuator movement along the three-contact direction. In the current placement that gives front/back movement, not left/right.

**Fix:** Rotate the switch 90° and verify which physical throw connects each contact pair before assigning A→B and B→A legends.

---

**15. MINOR — Several remaining numerical and part descriptions are stale**

**Location:** [DESIGN.md](/home/ch/src/ee_stuff/projects/tbox/DESIGN.md), [LEVELS.md](/home/ch/src/ee_stuff/projects/tbox/LEVELS.md), schematic annotations and [TODO.md](/home/ch/src/ee_stuff/projects/tbox/TODO.md).

These discrepancies can mislead assembly and bench work:

- **Headphone part:** DESIGN still names NJM4556A; the netlist uses OPA1622. TODO still requests checking the old DMP8/SOIC footprint.
- **Preamp stage labels:** +20/+20 dB annotations disagree with the actual +27.7/+12.1 dB network.
- **TX indicator current:** R2102 = 2.2 kΩ gives roughly \((13.4-2)/2200=5.2\) mA for a representative 2 V LED, not the stated 17 mA.
- **Reference topology:** The assertion that every ground-referenced stage’s gain-setting leg returns to GND is false. The headphone gain-setting resistors return to VREF, as do several other networks. The reference-noise analysis must follow the actual topology.
- **Noise estimate:** Using the OPA1678’s 4.5 nV/√Hz, a 600 Ω source, the 100 Ω input resistor, and \(430Ω\parallel10kΩ\), a simple room-temperature white-noise estimate is approximately 6.2 nV/√Hz input-referred. Over 20 kHz this is approximately 0.88 µVrms, or **−121 dBV**, rather than −123 dBV. This still approximately meets the −120 dBV target. The electret/LO SNR reasoning also uses an obsolete 20 dB gain difference; the actual difference is 12.1 dB.
- **Transformer identity:** TY-250P is specified as 1000 Ω CT : 1000 Ω CT/250 Ω, not inherently a 600 Ω transformer. Its suitability for the chosen termination should be stated separately.
- **Thermal premise:** The 385 mA regulator capability is conditional on the assumed thermal implementation. The currently embedded regulator footprint has nine small plated thermal holes, while TODO’s calculation assumes at least sixteen vias plus a suitable plane connection. Via count alone is not a thermal proof.

**Fix:** Regenerate numerical annotations from one maintained source where possible, and remove obsolete part-specific instructions. Reconcile the thermal budget with the final copper and measured temperature rise.

---

**16. MINOR — CTIA compatibility does not establish compatibility with the 5 V microphone bias**

**Location:** [preamp.kicad_sch](/home/ch/src/ee_stuff/projects/tbox/kicad/preamp.kicad_sch), TRRS microphone bias feed; headset compatibility claims.

CTIA specifies contact assignment; it does not establish that every compatible headset microphone tolerates the chosen bias.

For a capsule drawing 0.5 mA through 2.2 kΩ:

\[
V_{\rm mic}=5-(0.5{\rm mA})(2.2k)=3.9{\rm V}
\]

That exceeds the 1.8–2.9 V microphone-bias range specified for Android-compatible headset interfaces. This does **not** prove damage to a particular headset, but it means broad compatibility is not established by CTIA wiring alone. [Android headset-jack specification](https://source.android.com/docs/core/interaction/accessories/headset/jack-headset-spec)

**Fix:** Specify supported headset microphone ratings, or provide an appropriate lower-voltage bias option for the TRRS connector. Verify loaded bias voltage, microphone current and output level with representative supported headsets.

---

**What checked out**

The basic architecture is workable once the above defects are addressed. In particular:

| Checked item | Independent result |
|---|---|
| Preamp gain networks | +27.70 dB LO and +39.80 dB HI agree with the revised level table. |
| TX summer | 20 kΩ feedback / 10 kΩ inputs gives −2 per channel, as intended. |
| RX amplifier | \(1+47k/10k=5.7\), or +15.12 dB; its input network adds a small attenuation. |
| Rig drivers | \(1+7.5k/10k=1.75\), or +4.86 dB. |
| MIC pad | \(620/(100+12000+620)=0.04874\), or −26.24 dB. Including the DE-9 resistor, source impedance is approximately 690 Ω. |
| LINE-mode loading | 200 Ω total build-out into 600 Ω gives −2.50 dB, matching the level plan. |
| Headphone gain/power | Passive mixing followed by gain 16 produces approximately the stated 39 mW into 16 Ω, before accounting for the erroneous protection. |
| Transformer wiring | Primary 2–4, secondary 5–8 with 6–7 joined, implements the intended full-winding 1:1 connection. The secondary return remains isolated. |
| 9 V regulator programming | ANYOUT selections give \(1.4+6.4+0.8+0.4=9.0\) V. |
| Supervisor | \(0.405(1+174k/10k)=7.452\) V; 220 nF gives approximately 1.258 s delay. |
| Supply budget arithmetic | The present declared-load model gives approximately 306.8 mA maximum on +9 V and 354.8 mA at the raw input. Those sums fit the declared capabilities, subject to the omitted reference/transient loads and thermal premise. |
| Ribbon connectivity | The present two straight-through ribbon pin maps agree, and the checked PCB pad assignments agree with the netlist. |
| Supply protection ordering | The input TVS is ahead of the ferrite bead, so its main surge current need not cross the bead. |

The remaining bench work should validate a corrected circuit: it should not be used to decide whether mirrored holes, inappropriate clamp polarity, inadequate logic drive, or the identified timing backfeed are acceptable.