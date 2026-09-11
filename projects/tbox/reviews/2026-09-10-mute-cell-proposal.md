# Proposal under review: rework of the TBox mute cell

This is a **proposal only**. Nothing in the repository has been changed. The
schematic in `kicad/mute.kicad_sch` is still the "as drawn" circuit below.

## Context

`kicad/mute.kicad_sch` is one sheet instantiated three times: Preamp A
(refs 12xx), Preamp B (14xx) and the intercom (23xx). It mutes a
Vref-biased audio node. Reference designators below are the Preamp A
instance.

The mute node sits between the preamp output and the channel level pot.
Nominal level at the node is −17.2 dBV; speech peaks are roughly 15 dB
above that.

### As drawn

- `MUTE_A` is the command. It is a **diode-OR of source-only drivers**
  (manual mute switch, override, the PTT-gating jumper, and `MUTE_HOLD`
  from the supply supervisor). Its only sink is R1201, 100 kΩ to GND.
- Series/shunt fade: R1202 220 Ω from `IN` to node `FADE`. Q1201/Q1202
  are back-to-back 2N7002 (common source `FADE_S`, drains to `FADE` and
  `VREF`, gates tied to `FADE_G`), shunting `FADE` to `VREF`.
- Fade timing: D1201 (anode `MUTE_A`) → R1203 47 kΩ → `FADE_G`;
  C1202 100 nF and R1206 470 kΩ from `FADE_G` to GND.
- Switch timing: R1204 100 kΩ from `MUTE_A` to `SW_CTL`; C1203 1 µF from
  `SW_CTL` to GND.
- Q1203: 2N7002, gate `MUTE_A`, drain `MUTE_N`, source GND; R1205 100 kΩ
  from +9 V to `MUTE_N`.
- Q1204: 2N7002, gate `MUTE_N`, drain `SW_CTL`, source GND.
- U1201 TS12A12511 SPDT: COM = `OUT`, NC = `FADE` (signal), NO = `VREF`,
  logic input = `SW_CTL`. Logic high selects NO, i.e. muted.
- Supply is a single +9 V; `VREF` is a buffered mid-rail at 4.5 V.

### The two defects this is meant to fix

1. **Release sequencing.** C1203 discharges back through R1204 into
   `MUTE_A`, which has only R1201 to ground, so `MUTE_A` sits at
   `SW_CTL`/2. That holds Q1203 on, so Q1204 never fires promptly.
   Computed: on release the shunt is fully off at ~21 ms (R1206·C1202 =
   47 ms from 7.0 V down through 4.5 V), while the switch does not
   reconnect until 101–329 ms depending on where the 2N7002 threshold
   falls (SW_CTL decays with (R1204+R1201)·C1203 = 200 ms). The switch
   therefore recloses onto a live signal with no shunt.
2. **Gate drive.** Steady-state `FADE_G` = (MUTE − 0.6)·470/517 = 7.0 V
   at MUTE = 8.3 V, i.e. 2.5 V above Vref. The 2N7002 datasheet allows
   Vgs(th) up to 2.5 V and specifies R_DS(on) only at Vgs = 5 V and 10 V,
   so the claimed ~8 Ω pair (−29 dB with the 220 Ω) is not established.

### Intended behaviour, both directions

- **Mute:** shunt conducts first (~5 ms), then the switch opens (~90 ms).
- **Unmute:** the switch recloses **first** (promptly, while the shunt is
  still fully on), then the shunt releases over ~50 ms, fading the audio
  back in. The shunt is make-before-break around the switch transition so
  the switch never moves with signal present on it.

## The proposal

Buffer the command once, then hang both timing networks on the buffer
output rather than on the command line.

1. **Buffered command.** Keep Q1203 as the first inverter (gate `MUTE_A`,
   drain `MUTE_N`, R1205 100 kΩ pull-up to +9 V). Add a complementary
   pair driven from `MUTE_N`: a PMOS (source +9 V, gate `MUTE_N`, drain
   `MUTE_B`) and an NMOS (drain `MUTE_B`, gate `MUTE_N`, source GND).
   `MUTE_B` is then a stiff 0 / +9 V copy of `MUTE_A`, low impedance in
   both states.
2. **Fade gate.** Charge path: R_rise 100 kΩ in series with a diode
   (anode at `MUTE_B`) into `FADE_G`. Discharge path: R_fall 1 MΩ from
   `FADE_G` **back to `MUTE_B`**, not to ground. C_fade 47 nF from
   `FADE_G` to GND. R1206's return moves from GND to `MUTE_B`; D1201 and
   R1203 become the R_rise/diode pair.
   - `MUTE_B` high: both paths pull toward +9 V, so there is no divider
     and the diode drop stops mattering once `FADE_G` passes 8.4 V.
     Final 9.0 V, i.e. 4.5 V above Vref. Rise τ = (100 k ∥ 1 M)·47 n =
     4.3 ms.
   - `MUTE_B` low: the diode is reverse biased, so discharge is through
     R_fall alone, τ = 1 M·47 n = 47 ms, to 0 V.
3. **Switch delay.** R_sw 1 MΩ from `MUTE_B` to `SW_CTL`, C_sw 100 nF
   from `SW_CTL` to GND, τ = 100 ms on the rise. A diode **antiparallel**
   across R_sw (anode `SW_CTL`, cathode `MUTE_B`) dumps C_sw into the
   buffer's low side on release, in microseconds. R1204/C1203 are
   replaced by these. **Q1204 is deleted**; the buffer's NMOS does the
   sinking, and nothing can feed back into `MUTE_A`.
4. **Shunt devices.** Replace the 2N7002 pair with a MOSFET whose
   R_DS(on) is specified at the drive actually available (~4.5 V above
   Vref). At 3.5 Ω per channel the shunt gives −30.2 dB against the
   220 Ω; at 7.5 Ω it gives −23.9 dB.

Net change is about two parts per instance across three instances, and it
deletes the 470 kΩ-to-ground bleeder that caused the gate-drive loss.

## What I want from you

Review **this proposal**, adversarially and quantitatively. I have not
built it; I want to know if it is wrong before I draw it.

Specifically:

- Does it actually fix both defects, in all four transitions (mute
  assert, mute release, and the same two during the supervisor's
  power-on hold and a brown-out)?
- Does it introduce new problems? Consider at least: the floating
  `FADE_S` node and the body diodes of the back-to-back pair; charge
  injection and gate-source capacitance of the shunt devices into the
  audio node; the PMOS gate drive available from `MUTE_N` (a 100 kΩ
  pull-up against the PMOS Cgs and the NMOS that shares the node);
  shoot-through in the complementary pair; leakage across the 1 MΩ
  resistors against MOSFET gate leakage; what `MUTE_B` does while +9 V
  is coming up or collapsing, and whether the mute still asserts
  reliably when the rail is at 6 V; whether any node is left undriven in
  any state; the three instances' different drivers (the intercom
  instance has an active transistor pull-down on its command line, the
  two mic instances do not).
- Are the computed time constants and the resulting audible behaviour
  right? Recompute them. Is the ordering guaranteed across component
  tolerance and MOSFET threshold spread, or merely typical?
- Is there a materially better topology for the same job at similar
  parts cost? I am not attached to this one. Single +9 V supply, no MCU,
  no logic family in the design today, SMT, and the existing
  TS12A12511 and Vref buffer stay.
- Is "leave it exactly as drawn" defensible after all? I concluded it is
  not, because of the 101–329 ms unmute delay with the PTT-gating jumper
  fitted. Say so if you disagree.

You have read-only access to the repository, including the schematic, the
netlist, `DESIGN.md`, `LEVELS.md` and the vendor datasheets in
`third_party/datasheets/` (2N7002, TS12A12511, OPA1678 and the rest).
Check my numbers against the actual files rather than trusting this
summary; if the summary misdescribes the circuit, say so.

Be concrete. Give values, not directions. If you recommend a different
topology, draw it in text with component values and say what each
transition does and when.
