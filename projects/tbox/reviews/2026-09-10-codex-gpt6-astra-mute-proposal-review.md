**I would change the existing circuit, but I would not draw this proposal unchanged.** Buffering fixes the command-line feedback mechanism. It does **not** establish the claimed switch timing, shunt attenuation at the switching instant, or reliable brown-out behavior.

The most consequential additional finding is upstream: **the supervisor’s 100 kΩ pull-up is too weak to guarantee the proposed buffer asserts at a 6 V rail.** Also, Vref does not immediately become 3 V when the rail falls to 6 V.

I checked the shared [mute schematic](/home/ch/src/ee_stuff/projects/tbox/kicad/mute.kicad_sch), its three instances in the supplied exported netlist, the upstream control and supply circuits, and the local vendor PDFs. Nothing was changed. Calculations below use idealized transistor switching or explicitly stated component models; they are not transistor-level simulation or bench results.

**Your description of the mute sheet is correct. The surrounding circuit adds several qualifications.**

- The mic commands have the stated 100 kΩ pull-downs. Their indicator branches feed MOSFET gates through 10 kΩ, so those branches provide no useful additional DC sink.
- The PTT-gating source comes through a **10 kΩ pull-up plus 1 kΩ series resistor**, before the OR diode. It is not a stiff 8.3 V source.
- `MUTE_HOLD` has **one 100 kΩ pull-up, R2122**, supplying both mic commands through D2120/D2121.
- The intercom command has **R2208 = 10 kΩ to +9 V and Q2201, an MMBT3904, pulling down actively**. Its release therefore does not suffer the same capacitor-feedback delay.
- `MUTE_HOLD` does **not** directly command the intercom cell. Muting the two preamps protects the intercom’s input signal, but is not equivalent to clamping its output during supply disturbances.
- `MUTE_B` already names the other microphone’s command. I would call the proposed local node `MUTE_DRV`.

The upstream connections are in [keylogic.kicad_sch](/home/ch/src/ee_stuff/projects/tbox/kicad/keylogic.kicad_sch:10755) and [txsum.kicad_sch](/home/ch/src/ee_stuff/projects/tbox/kicad/txsum.kicad_sch:3572).

**The existing release defect is real, although 101–329 ms is not the range obtained from the supplied datasheet.**

While Q1204 remains off:

\[
MUTE_A\simeq SW\_CTL/2,\qquad
SW\_CTL(t)=V_0e^{-t/200\,ms}.
\]

Approximating Q1203’s change of state by a gate threshold \(V_T\):

\[
t=200\,ms\ln\left(\frac{V_0}{2V_T}\right).
\]

The supplied [Diodes 2N7002 datasheet](/home/ch/src/ee_stuff/projects/tbox/third_party/datasheets/Diodes_2N7002.pdf), page 2, specifies **1.0–2.5 V**, measured at 250 µA. With \(V_0=8.3\) V, the calculation gives **101–285 ms**. The 329 ms figure corresponds to **0.8 V**, outside that particular threshold range.

These are estimates, not guaranteed timing limits: Q1203’s actual operating current and drain voltage differ from the threshold test conditions.

Using 0.6 V per diode and including the PTT source resistance gives:

| Existing circuit, steady state at 9 V | Command | Fade gate |
|---|---:|---:|
| Manual switch source | 8.40 V | 7.09 V |
| Own-PTT gating source | 7.44 V | 6.22 V |
| Supervisor alone, both mic cells loaded | 2.55 V | 1.77 V |

For the PTT case, the same release approximation gives **79–263 ms**. The weaker fade-gate drive makes that case worse, not better.

Your \(47\,ms\ln(7/4.5)=20.8\,ms\) calculation is correct as a **gate-voltage crossing**. Calling it the exact instant the shunt becomes fully off is too strong: the source node floats, and channel conduction depends on instantaneous signal voltage. Nevertheless, the separation between fade release and reconnection is plainly large enough to reject the documented sequencing claim.

**The proposed fade network has a fast initial charge and a slow final charge.**

For a stiff 9 V buffer, a constant 0.6 V diode drop, and initially discharged C_fade:

\[
\tau_{\rm initial}=(100k\parallel1M)47n=4.273\,ms
\]

but its initial exponential approaches

\[
V_{\infty,\rm initial}
=\frac{8.4/100k+9/1M}{1/100k+1/1M}
=8.455\,V.
\]

Thus:

\[
V_G(t)=8.455(1-e^{-t/4.273ms})
\]

until approximately **21.55 ms**, when it reaches 8.4 V. Thereafter, in this simplified diode model:

\[
V_G(t)=9-0.6e^{-(t-21.55ms)/47ms}.
\]

A real diode makes the transition gradual, but does not remove the slow tail.

| Time after buffer asserts | Fade gate | Approximate \(V_{GS}\), source at 4.5 V |
|---|---:|---:|
| 5 ms | 5.83 V | 1.33 V |
| 9.31 ms | 7.50 V | 3.00 V |
| 18.23 ms | 8.34 V | 3.84 V |
| 31.02 ms | 8.51 V | 4.01 V |
| 90 ms | 8.86 V | 4.36 V |

Consequently:

- “Shunt conducts first at about 5 ms” is plausible for a suitably selected device.
- **“Shunt has its 4.5 V specified on-resistance before the switch moves” does not follow.**
- Even at 90 ms, the gate has not reached 4.5 V above Vref.
- A device specified only at 4.5 V still has essentially no allowance for rail tolerance, gate leakage, source signal excursion, or brown-out.

Select the shunt using a **lower specified gate voltage**, preferably 2.5 V or lower, rather than treating nominal 4.5 V availability as sufficient.

Your attenuation arithmetic is correct:

\[
20\log_{10}\frac{7}{220+7}=-30.22\,dB,\qquad
20\log_{10}\frac{15}{220+15}=-23.90\,dB.
\]

Those results require the stated channel resistances **at that instant**, including temperature.

**The proposed switch delay is approximately 18 ms under your typical-threshold assumption, not 90 ms.**

For the proposed 100 ms switch RC:

\[
t_{\rm switch}=-100\,ms\ln(1-V_{\rm trip}/9).
\]

| Assumed trip voltage | Crossing time |
|---|---:|
| 0.8 V | 9.31 ms |
| 1.5 V | 18.23 ms |
| 2.4 V | 31.02 ms |
| 5.0 V | 81.09 ms |

The TS12A12511 specifies \(V_{IL}=0.8\) V and \(V_{IH}=5\) V in its **12 V single-supply** table. Its 2.4 V high specification applies to the **5 V single-supply and ±5 V dual-supply** tables. The latter is not a 10 V single-supply specification. There is no dedicated 9 V timing threshold specification, and VIH is not a specified trip point. See the local [TS12A12511 datasheet](/home/ch/src/ee_stuff/projects/tbox/third_party/datasheets/TI_TS12A12511.pdf), pages 5–7; [TI’s current datasheet](https://www.ti.com/lit/ds/symlink/ts12a12511.pdf) has the same tables.

Even provisionally using 0.8 V as the earliest switching boundary, the tolerance margin is inadequate for a generic “4.5 V rated” replacement:

- Switch R −1%, C −20%: 0.8 V reached at **7.37 ms**.
- Fade resistors +1%, C +20%: initial fade τ becomes **5.18 ms**.
- Fade drive at that instant: approximately **1.92 V above Vref**, or **1.78 V** with a 0.8 V charging-diode drop.

That is a concrete counterexample to guaranteed attenuation from a 4.5 V on-resistance specification.

Also, the TS12A12511 does not specify Schmitt hysteresis. A slow ramp spends substantial time in its undefined logic region; noise sensitivity and switching behavior there need consideration.

**Release is substantially improved, but “microseconds” needs a qualified discharge path.**

At a stable rail, the new buffer removes the feedback into `MUTE_A`. That fixes the original mechanism for both mic instances.

However, placing a diode directly across R_sw makes the initial discharge current depend on MOSFET resistance, diode resistance, capacitor ESR and wiring. C_sw stores:

\[
Q=100n\cdot9=0.9\,\mu C.
\]

An illustrative 5 Ω discharge loop would initially demand roughly **1.7 A**. There is no benefit in demanding that current.

Use **1 kΩ in series with the discharge diode** for the proposed 100 nF capacitor. Initial current becomes about **8 mA**. A constant-0.7-V diode approximation gives approximately **0.44 ms to 0.8 V**, before allowing for buffer delay and its low-state voltage.

That is comfortably fast relative to the fade. But the diode also means that “dumped to zero in microseconds” is inaccurate: forward voltage falls with current, and the remaining tail includes R_sw.

On fade release, neglecting leakage:

\[
V_G=9e^{-t/47ms}.
\]

Assuming the source remains near 4.5 V:

| Remaining gate drive | Time after release |
|---|---:|
| 2.5 V | 11.81 ms |
| 1.5 V | 19.06 ms |
| 1.0 V | 23.15 ms |
| 0 V | 32.58 ms |

**47 ms is an electrical time constant, not a 47–50 ms audio fade.** The audible transition occurs over the portion of the MOSFET characteristic where its resistance changes through values comparable to 220 Ω. That may occupy only a few milliseconds, with substantial transient distortion. A lower-resistance, higher-transconductance replacement can make that transition sharper.

**The supervisor and collapsing rail prevent an all-transitions approval.**

After your buffering removes the timing-network loads, the supervisor still supplies two 100 kΩ pull-downs through its 100 kΩ pull-up:

\[
MUTE_{\rm mic}\simeq\frac{V_{rail}-V_D}{3}.
\]

For \(V_D=0.6\) V:

- At 9 V: **2.8 V**.
- At 7.5 V: **2.3 V**.
- At 6 V: **1.8 V**.

The unchanged Q1203 cannot be guaranteed to recognize the last two as asserted. With the complementary output stage, a partially conducting Q1203 can also leave **both output devices conducting continuously**.

There is another independent problem. The [Vref circuit](/home/ch/src/ee_stuff/projects/tbox/kicad/supply.kicad_sch:6056) includes:

- 10 kΩ ∥ 10 kΩ feeding 10 µF: **50 ms**.
- Buffer output isolation of 10 Ω into 470 µF: approximately **4.7 ms**.

For an illustrative abrupt 9→6 V step, assuming the buffer continues following its input:

| Time after rail step | Vref |
|---|---:|
| 5 ms | 4.44 V |
| 14.3 ms | 4.24 V |
| 28.8 ms | 3.93 V |
| 50 ms | 3.61 V |

Even granting an ideal, immediately asserted 6 V `MUTE_DRV`, your proposed fade gate is approximately **5.26 V at 14.3 ms**. Available drive is therefore only **1.03 V**, not 3 V.

The transition assessment is consequently:

| Transition | Assessment |
|---|---|
| Normal mute assertion | Plausible with appropriate low-voltage shunt devices; proposed timing/attenuation not guaranteed. |
| Normal mute release | Feedback defect fixed; add controlled discharge impedance and specify devices. |
| Power-on hold assertion | Eventually likely at normal rail, but no guaranteed initial mute interval; SW_CTL starts low and supervisor command drive is marginal. |
| Power-on hold release | Once fully powered and held long enough, behaves like normal release. |
| Brown-out assertion | **Not reliable as proposed:** weak command drive, lagging Vref, and insufficient guaranteed shunt drive. |
| Brown-out recovery release | Normal release after a successful hold and rail recovery; does not repair a failed assertion. |

No delayed mute circuit can preserve the requested sequence through an arbitrarily fast loss of its operating supply. A guaranteed brown-out requirement needs a specified rail-decay envelope or enough hold-up to complete the sequence.

On deeper collapse, the large Vref capacitor also matters to **existing** circuitry: retained Vref can exceed the falling switch supply. The analog switch’s signal-pin limits must then be checked; the proposal does not provide power-off isolation.

**The other risks are manageable, but several require actual part choices.**

- **Floating common source and body diodes.** Both body-diode anodes connect to `FADE_S`; their cathodes connect to FADE and Vref. They therefore do not form an ordinary forward-diode path between the audio node and Vref. Floating `FADE_S` is normal for this arrangement. Its voltage is nevertheless history-dependent through capacitance, leakage and transient channel conduction. When conducting strongly, it is approximately Vref plus half the small residual signal. When off, it is not necessarily Vref. Do not add a low-value source-to-Vref resistor: that creates a diode/resistor loading path on one signal polarity.

- **Gate feedthrough.** The initial proposed gate slew is approximately **2 V/ms**. An illustrative effective 50 pF coupling capacitance produces \(C\,dV/dt\approx100\) nA, or approximately **22 µV across 220 Ω** while that impedance approximation applies. A 1 nF device raises that estimate to **0.44 mV**. These are scale estimates, not bounds; capacitances near zero drain voltage and movement of the floating source matter.

- **Switch charge injection remains.** The shunt reduces voltage across the switching signal terminals; it cannot remove the TS12A12511’s own charge injection into COM. Its single-supply tables give **65 pC typical at 5 V and 491 pC typical at 12 V**, under their stated test conditions. There is no justified 9 V maximum obtained by interpolation. “The switch never moves with signal present” should therefore become an attenuation target, not a literal zero-signal or click-free guarantee.

- **Residual audio is still significant.** −17.2 dBV is 138 mVrms. With a true 15 dB crest factor, the peak is 776 mV. The 7 Ω and 15 Ω shunts leave approximately **24 mV and 49 mV peak**. If the level-plan “peak dBV” figures mean RMS-equivalent sine levels, those become **34 mV and 70 mV**. Either interpretation leaves an audible-switching question.

- **100 kΩ PMOS gate pull-up.** Its time constant uses the combined PMOS/NMOS capacitance and Q1203 drain capacitance, with Miller charge added. For an illustrative total 100 pF–1 nF, τ is **10–100 µs**. A gate transition from 1 to 8 V takes **21–208 µs**. That is usually short enough for release sequencing, but it is not negligible for shoot-through.

- **Complementary-pair shoot-through.** Both devices conduct over much of that transition. The current is not limited by the timing resistors. Its value cannot be calculated without the PMOS/NMOS selections. A slow or intermediate command can make this sustained rather than transient. Reducing R1205 helps switching speed but does not remove the topology’s overlap conduction.

- **Leakage.** Through 1 MΩ, 10 nA means 10 mV; 100 nA means 100 mV; 1 µA means 1 V. Count **both shunt gates**, diode leakage, capacitor leakage and PCB leakage. Some ESD-protected small MOSFETs have µA gate-leakage specifications. The discharge diode’s reverse leakage also bypasses the switch charging resistor and can advance assertion. The supplied 1N4148W has a useful room-temperature leakage specification, but its high-temperature figures cannot support simply assuming negligible leakage everywhere.

At valid steady supply, your buffer gives every control/timing node a DC path. `FADE_S` remains intentionally floating when off. During supply ramps, “has a resistor path” does not establish a valid logic state.

**For a discrete implementation, I would use a resistor-loaded buffer instead of the complementary pair.**

Here is a concrete candidate. It removes shoot-through, lowers fade-network impedances, limits capacitor discharge current, and gives considerably more sequencing margin. It deliberately makes the *typical* switch delay approximately 90 ms.

```text
Command receiver:

MUTE command ───────── gate Q3
       │               Q3 = BSS138BK
      100k             source = GND
       │               drain = MUTE_N
      GND
                       +9 V
                        │
                       100k
                        │
                     MUTE_N ───── gate Q4
                                  Q4 = existing 2N7002
                                  source = GND
                                  drain = MUTE_DRV

                       +9 V
                        │
                       2.2k
                        │
                     MUTE_DRV


Fade gate:

MUTE_DRV ── 4.7k ──|>|──── FADE_G
                    D1        │
MUTE_DRV ── 100k ──────────────┤
                             470n
                              │
                             GND

D1 = 1N4148W, anode toward MUTE_DRV.


Switch control:

MUTE_DRV ───── 470k ─────── SW_CTL ── TS12A12511 IN
                              │
                              1µ
                              │
                             GND

SW_CTL ── 220Ω ──|>|── MUTE_DRV
                 D2

D2 = 1N4148W, anode toward SW_CTL.


Audio:

IN ── 220Ω ── FADE ───────── TS12A12511 NC
               │
               D
          Q1 PMV30UN2
               S
               ├── FADE_S
               S
          Q2 PMV30UN2
               D
               │
              VREF

Q1/Q2 gates = FADE_G.
COM = OUT; NO = VREF, unchanged.
```

Also change the shared **R2122 from 100 kΩ to 10 kΩ**. With the two command pull-downs, the supervisor commands become approximately:

\[
MUTE_{\rm mic}=\frac{V_{rail}-0.6}{1.2},
\]

or **7.0 V at 9 V** and **4.5 V at 6 V**.

BSS138BK gives Q3 an explicit low-voltage conduction specification. For the audio pair, PMV30UN2 is a concrete option with **±12 V gate rating, ±100 nA gate-leakage limits at 25°C, and 100 mΩ maximum on-resistance at 1.5 V gate drive and 25°C**. Its capacitance is substantially higher than a 2N7002’s, so it requires an audio transient check. [BSS138BK datasheet](https://assets.nexperia.com/documents/data-sheet/BSS138BK.pdf), [PMV30UN2 datasheet](https://assets.nexperia.com/documents/data-sheet/PMV30UN2.pdf).

For this candidate, I numerically integrated the coupled resistor/capacitor networks, including the 2.2 kΩ buffer pull-up and a constant 0.6 V diode drop:

| Event at a stable 9 V rail | Calculated result |
|---|---:|
| Fade gate at 5 ms | approximately 6.7 V |
| SW_CTL reaches 0.8 V | 45 ms |
| SW_CTL reaches 1.5 V | 87 ms |
| SW_CTL reaches 2.4 V | 147 ms |
| SW_CTL reaches 5 V | 384 ms |
| Fade gate at earliest listed switch crossing | 8.62 V |

The 470 ms switch RC is intentional. It provides approximately 90 ms at a 1.5 V trip point; **it still does not provide a guaranteed 90 ms delay**.

On release, Q4 sinks the switch capacitor through D2/220 Ω. Initial discharge current is approximately **35–40 mA**, with reconnection on the order of **1 ms**. The fade gate falls only about **0.19 V in the first millisecond**, leaving substantial shunt drive.

At 6 V, the switch reaches 0.8 V at approximately **69 ms**. For the illustrative 9→6 V step above, gate drive at that time is approximately **2.35 V**, allowing for lagging Vref.

One adverse calculated corner—fade R +1%, fade C +20%, switch R −1%, switch C −20%, 0.8 V charging-diode drop and 200 nA total gate leakage—gave:

- Stable 9 V: earliest 0.8 V switch crossing at **36 ms**, with **3.84 V** shunt drive.
- Abrupt 9→6 V: crossing at **55 ms**, with approximately **1.98 V** shunt drive.

Those are useful margins against the selected device’s 1.5 V rating, rather than an assumption that nominal 4.5 V is always available. They are **not** a complete temperature qualification or a guarantee for arbitrary rail collapse.

This alternative costs roughly **three added passives per cell**, retains the existing second inverter transistor, and consumes approximately **4.1 mA per unmuted cell** in the 2.2 kΩ pull-up. The resistor dissipates about 37 mW.

Its transition behavior is:

- **Mute:** shunt becomes strong within several milliseconds; switch changes later.
- **Unmute:** switch reconnects in roughly 1 ms; shunt gate subsequently decays with 47 ms electrical τ.
- **Power-on:** after the command receiver becomes valid, the cell charges into mute; the existing long supervisor hold allows settling. It still does not establish a guaranteed mute from the first instant of rail rise.
- **Brown-out:** the stronger supervisor pull-up fixes command recognition at 6 V, and the lower-voltage shunt specification plus longer delay accommodates the illustrated Vref lag. Faster/deeper collapses still require a defined operating envelope.
- **Recovery:** after the supervisor hold, release follows the normal sequence.

The principal remaining development task is the **audio fade characteristic**. These very low-resistance MOSFETs improve guaranteed suppression but may produce a sharper fade knee. I would not label this “50 ms audio fade” without measuring it.

If **90 ms must itself be bounded**, use a comparator or a specified Schmitt-trigger timing stage instead of the analog switch input as the timing threshold. A CD40106B is supply-compatible and explicitly tolerates slow inputs, but its threshold spread still needs budgeting; merely inserting one does not create a precision delay. [TI CD40106B datasheet](https://www.ti.com/lit/ds/symlink/cd40106b.pdf).

**Leaving the circuit exactly as drawn is not defensible against the stated sequencing requirement.** Your release diagnosis survives the numerical corrections, and the supervisor loading exposes an additional weakness. The proposal’s buffering idea is sound; the missing pieces are a stronger supervisor command, shunt specifications below nominal gate drive, controlled discharge current, and timing margins that include Vref’s behavior during brown-out.