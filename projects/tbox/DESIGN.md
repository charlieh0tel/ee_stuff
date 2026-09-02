# TBox — Transceiver Companion Box

A shack interface box between a pair of operator headsets and a ham
transceiver. Two mixable microphone channels, dual stereo headphone
outputs, an isolated stereo line out, PTT inputs with selectable override,
and a generic rig connector with rig-specific cables.

## Design decisions

| Decision | Choice |
|---|---|
| Mic connectors | 3.5mm TRS/TRRS, 1/4" TRS; round-plug ham mics via adapter pigtails |
| Condenser support | Electret bias only (~5 V); Icom powered mics unsupported |
| Rig connection | Generic DE-9 on box + rig-specific cables |
| Channel layout | Two fixed, identical channel groups (A and B) — no cross-assignment |
| Headset usage | Both channels mixable; override selector: OFF / A→B / B→A |
| Muting | Full mute only (no ducking), analog-switch SPDT to Vref, pop-free, LED indicated |
| Intercom | Global momentary button: mutes TX mix to rig, monitor stays live |
| RX path | Stereo throughout (main/sub for dual-receive rigs; mono rigs feed both) |
| Line out | Stereo, per-side source jumpers, levels via rear trims |
| VOX | Assumed OFF at the rig — TX mix is always present at mic out |
| Power | 12–14 V via Anderson Powerpole, runs down to ~10.5 V, all-linear, single rail |
| PCB | 4-layer (solid ground plane under the audio, thermal path for the VQFN regulator), SMT |
| Construction | Mixer-style: control PCB under sheet-metal top panel, rear I/O PCB |
| Digital | None — all-analog, no MCU, no clocks |

## Block diagram

```
 CH A jacks ─┬─ bias sw ─ preamp A ─ mute A ─ level A ─┐
 (3.5mm, TRRS,│                        ▲ (LED)         │
  1/4")                         button or OVR B→A      │
                                                       ├─ TX MIX BUS
 CH B jacks ─┬─ bias sw ─ preamp B ─ mute B ─ level B ─┘     │
 (3.5mm, TRRS,│                        ▲ (LED)               ├──► monitor tap
  1/4")                         button or OVR A→B            │    (to phones)
                                                             │
                                              INTERCOM mute ─┤
                                     (momentary; locked out  │
                                      while PTT is down)     ├──► MIC OUT to rig
                                                             │    (padded, trim)
                                                             └──► LINE OUT
                                                                  TX-side jumper
 RX L ── trim ── buf ──┬─────────────────────────► LINE OUT L/R (isolated,
 RX R ── trim ── buf ──┤                            per-side source jumpers,
 from rig              │                            rear level trims)
 (mono cables tie L+R) │
                       ▼
     PHONES A (stereo) ◄── vol A × (RX L/R + mon A × TX MIX both ears)
     PHONES B (stereo) ◄── vol B × (RX L/R + mon B × TX MIX both ears)

 PTT A (3.5mm ∥ 1/4" ∥ panel btn) ──┬── PTT logic ── PTT to rig
 PTT B (3.5mm ∥ 1/4" ∥ panel btn) ──┘   │            (open-drain MOSFET,
                                         │             TX LED)
              OVERRIDE selector: OFF / A→B / B→A
              (A→B: PTT A keys rig AND mutes channel B; B→A mirror)

 RIG ◄── DE-9: MIC, MIC GND, PTT, RX L, RX R, RX GND, spare; shield
```

## Channel groups

Two identical, physically grouped channel sections (A and B). Each has:

- **Mic jacks:** 3.5mm TRS, mic side of the TRRS combo, and 1/4" TRS.
  All paralleled into one preamp; plug a mic into exactly one (not
  enforced by switching contacts).
- **Electret bias switch** (rear panel): ~5 V through 2.2 kΩ from the
  bias rail; applies to all jacks in the group.
- **Gain range switch** (rear panel, beside the bias switch): LO ~+20 dB
  (electrets, ~-45 dBV) / HI ~+40 dB (dynamics, ~-57 dBV Heil class).
  Both ranges land nominal mic level at the same point at the channel
  level pot, which handles fine adjustment. Exact gains per
  [LEVELS.md](LEVELS.md). The switch throws a DC control line; gain
  switching happens at the preamp with a 9 V-rated SPDT analog switch
  (TS12A12511, U202/U302) selecting the stage-1 or stage-2 output
  (mic-level signals don't cross boards).
- **Mute button:** top panel, latching/alternate-action (NKK/Schadow
  style; fallback: toggle, or momentary + flip-flop). Full mute: a
  TS12A12511 SPDT analog switch after the preamp — COM is the output,
  NC the signal, NO = Vref — so muting both opens the path and clamps
  the node (series + shunt in one part, >70 dB, no pinch-off
  dependence). No DC across the switch: the stage ahead has unity DC gain
  at Vref and the load returns to Vref, so the switching step is only the
  op-amp offset (a few mV) and there is no pop. A JFET series+shunt pair
  was the first design; at 9 V single-supply a worst-case J113
  (|Vgs(off)| = 3 V) is neither fully off at 0 dBV peaks when muted nor
  fully off when unmuted, so it was dropped. Override mute uses the same
  circuit, triggered electrically. The mute is one shared sub-sheet
  (`kicad/mute.kicad_sch`, pins IN / OUT / MUTE) instantiated in each
  preamp and once more for the intercom; a power-on hold keeps both
  channels muted for ~1 s while the audio coupling caps settle.
- **Channel level pot** into the TX mix bus.
- **PTT jacks:** 3.5mm and 1/4", paralleled, contact-closure.
- **Round-plug ham mics** (Yaesu/Kenwood/Icom/Elecraft 8-pin Foster)
  connect via per-brand adapter pigtails: Foster-female → 3.5mm mic plug
  + 3.5mm PTT plug (rear PTT jack). Covers dynamics and mic-line-bias
  electrets (Elecraft MH2 with BIAS ON). Known exception: Icom powered
  mics (SM/HM series, separate +8 V pin) are unsupported. Each preamp
  keeps a polarized spare header so a Foster side-board option can be
  retrofitted.

## Buses and outputs

- **TX mix bus:** channel A + B, post-mute, post-level-pot. Order on the
  bus: summing amp → monitor tap → intercom mute → mic out pad / line out
  TX tap.
- **Intercom:** global momentary button (front panel, reachable from both
  positions). While held, the same switch mutes the TX mix downstream of the
  monitor tap: operators hear each other, nothing reaches the rig or the
  line out. **PTT wins:** while the rig is keyed, the intercom is locked
  out (its DC control line is gated by the PTT output state) and its LED
  stays dark (a resistor-NOR on the TX Bus sheet).
- **Mic out to rig:** TX mix padded to ~5 mV mic level, ~600 Ω source
  impedance, DC-blocking cap (rigs may put electret bias on their mic
  pin). Level trim rear-accessible — must not require opening the box
  (used range -20…0 dB, ahead of the driver). A rear jumper (JP401)
  selects MIC (padded to mic level) or LINE (~-10 dBV) for rigs with a
  line-level TX input. Must drive a 600 Ω load; source impedance ~690 Ω
  in MIC mode including the DE-9 series resistor. Level setting uses
  the rig's ALC/mic-gain meter — the box has no metering.
- **RX audio input (stereo):** RX L and RX R (main/sub on dual-receive
  rigs; mono rig cables feed L, bridged to both). Each: 10 kΩ bridging
  load, rear trim straight into a +15 dB buffer — the trim is the pad,
  so speaker-level sources (~5 Vpp) are simply turned down and weak
  phones-jack sources get up to +15 dB. Buffers drive the
  `RX_L_BUS`/`RX_R_BUS` at -15 dBV.
- **Line out (stereo):** 3.5mm TRS, ~ -10 dBV, transformer isolated
  (two 600 Ω 1:1) to break the inevitable sound-card ground loop.
  Per-side source jumpers: RX L, RX R, RX blend, or TX mix. Levels via
  rear trims. TX tap is post-mute (recordings reflect what went out).
  The isolated secondaries return to the jack sleeve (`LOUT_RET`), never
  to signal ground, and carry a DC block against sound-card plug-in
  power.
- **Monitor bus:** TX mix (tapped ahead of the intercom mute) feeds each
  headphone position (both ears equally) through its monitor-mix pot; pot
  at zero = off. Tap is post-fader: the channel level pot affects the
  monitor too.

## Headphone outputs (2 positions, stereo)

- Per position: 3.5mm phones, 1/4" phones, and the phones side of the
  TRRS combo, all paralleled off one stereo headphone amp.
- Headphone amp: NJM4556A dual op-amp, powered from the 9 V rail.
  ≥20 mW per channel into 16 Ω for one headset per position.
- Two pots per position: volume (dual-gang) and monitor-mix level. Each
  ear: volume × (RX that side + monitor-pot × TX mix). The monitor pot is
  buffered so the passive mix into the volume gang doesn't interact; the
  headphone amp makes up the mix loss. Rated for one headset per
  position (three paralleled 16 Ω headsets current-limit).
- TRRS wiring is CTIA.

## Keying

- Per channel: 3.5mm + 1/4" PTT jacks (paralleled) and a front-panel
  momentary PTT button, all in parallel. Contact closure to ground;
  inputs pulled up, clamped, and filtered (keyers and computer
  interfaces may drive them).
- **Override selector, 3-position: OFF / A→B / B→A** (top panel, center,
  below the TX lamp; thrown toward the channel that wins). A→B: channel
  A's PTT keys the rig and fully mutes channel B while closed; B→A
  mirror. OFF (center): both PTTs just key the rig. Realized as a DPDT
  on-off-on toggle (SW703); lever directions as marked on the top panel.
- Rig PTT output: open-drain MOSFET (tolerates 12 V+ pull-ups).
- Control lines (`MUTE_A/B`, `PTT_ACTIVE`, `IC_MUTE`) are DC logic,
  0 V / +9 V, active high. `PTT_ACTIVE` is high while the rig PTT output
  is asserted and gates the intercom.
- Jumper option per channel: PTT gates the channel's own audio (mic live
  only while keyed) — also the mitigation if rig VOX must be on.

## Indicators

- Power LED.
- TX lamp (PTT output asserted) — prominent, visible from across the desk.
- Per-channel PTT LED (that channel's PTT input closed).
- Per-channel mute LED (mute control-line state — button, override or
  power-on hold).
- Intercom LED (lit while the intercom mute is engaged).
- All DC-driven, powered from the raw filtered rail (not the 9 V analog
  rail) so LED step loads never touch audio (TX lamp ~17 mA, others
  ~5 mA; see the Keying sheet).

## Rig interface

- DE-9 (female) on the box; rig cables carry: MIC, MIC GND, PTT, RX L,
  RX R, RX GND, +1 spare (reserved for a possible CW key line); shield to
  chassis. Mono rig cables tie RX L and RX R together at the DE-9.
  Pinout and protection: see the Keying sheet (J705). The spare lands on
  header J706 inside the box.
- Protect every pin against ±12 V — DE-9 invites accidental RS-232
  hookups (bead, shunt cap, TVS and series R per line; see the sheet).
- One cable per rig family (Icom 8-pin, Yaesu RJ45, Kenwood 8-pin, etc.).

### Reference rig: Elecraft K3S

Per K3S Owner's Manual rev A1, pp. 17–22. All connections on the K3S rear
panel; front mic and phones jacks stay free.

- **Cable:** DE-9 →
  - MIC → rear **MIC** jack (3.5mm mono; electret or dynamic, hi/lo-Z).
    K3S settings: MAIN:MIC SEL = RP, gain range Low/High as needed,
    bias OFF.
  - PTT → **PTT IN** jack (RCA; also on ACC pin 4 in parallel). Contact
    closure to ground.
  - RX L/R → **LINE OUT** (3.5mm stereo, transformer-isolated, 600 Ω;
    left = main, right = sub; post-AGC, pre-AF-gain, so independent of
    the rig volume knob). Level via CONFIG:LIN OUT; keep ≤ 10 to avoid
    transformer saturation.
  - Sleeves to DE-9 grounds, shield to backshell.
- **Line-level TX alternative:** K3S **LINE IN** (3.5mm mono,
  transformer-isolated, 600 Ω) with MAIN:MIC SEL = LINE IN; rig's MIC
  knob sets the level. Watch input-transformer saturation.

## Power supply

- Input: 11–15 V DC (13.8 V nominal; operates down to ~10.5 V on a
  sagging battery). Anderson Powerpole, rear panel; reverse-polarity
  protected, PTC resettable fuse on the board.
- **Input TVS** after the π filter: the regulator is a TPS7A4701
  (36 V max, ceramic-stable, 4 µVrms) rather than the automotive LM2940
  originally planned — the LM2940's 0.1–1 Ω output-ESR window is a BOM
  trap with today's low-ESR parts. The TVS covers the load-dump case the
  LM2940 would have survived on its own.
- **All-linear, single rail** (bipolar rails would require a charge pump
  or switcher):
  - Input π filter → LDO → **9 V analog rail** (Vref 4.5 V; internal
    nominal -15 dBV, clip +6 dBV planning figure — see
    [LEVELS.md](LEVELS.md)). Op-amps are OPA1678 (4.5–36 V, 4.5 nV/√Hz,
    2 mA/ch): at 9 V the output is guaranteed within 0.8 V of each rail
    and the input common-mode range is 0.5–7 V. The NE5532 it replaces
    is only specified from 10 V total and its input range at 9 V would
    have been 3–6 V — 0.1 V of margin at 0 dBV peaks. The NJM4556A
    headphone amps are specified at 9 V.
  - Buffered mid-rail virtual ground (Vref) used as **DC bias only**: every
  ground-referenced input or output (mic, RX in, mic out, line out,
  phones) keeps its gain-setting leg on GND, not Vref, so Vref noise is
  never amplified. Vref itself is stiff and its rail divider is
  filtered well below the audio band. All signal paths AC-coupled.
  - ~5 V **electret bias rail**, low-noise LDO (ADP7142, ~11 µVrms) + a
    light RC, decoupled again where it enters each mic node (bias noise
    appears directly in the mic signal).
- Analog switches single-supply (TS12A12511, gain select and mute): V-
  to GND, signals stay inside 0…9 V, logic input needs a solid high —
  the datasheet guarantees VIH 2.4 V at 10 V and 5 V at 12 V (typ ~1.5
  V), so every control line is designed to sit ≥ 6 V loaded.

### Power tree

Drawn on the Power Tree sheet by `tools/gen_power_tree.py` from two
sources: topology and loads from the schematic (converter pins and
`Load_mA` fields), capability from `power_tree.json` (`max_ma` and the
analysis behind it). `tools/check_power.py` flattens the tree so each
rail's total includes everything downstream and checks it against
`max_ma`. Current figures: +9V 62 mA typ / 250 mA max (the max is two
16 Ω headsets at sine clip plus every LED and pull-up on), which is 64 %
of the regulator's 385 mA thermal limit at 15 V in (θJA ≈ 32.5 °C/W,
which needs the VQFN pad stitched to a ground plane — one reason the
board is 4-layer). LED indicators run from the raw filtered
rail (`RAW_13V8`) via droppers — never from the 9 V analog rail.
- PTT logic is diode-OR and discretes. All logic transistors are
  2N7002 so no base current loads the pull-ups; logic highs stay above
  ~7 V.
  Per channel: PTT inputs (pulled up, clamped, filtered) → `PTT_x_N`
  (low = keyed) → inverter → `PTT_x`. `PTT_ACTIVE` = `PTT_A` OR `PTT_B`
  drives the rig MOSFET, the TX lamp and the intercom lockout. `MUTE_x`
  = latching button OR override (the other channel's `PTT`) OR
  jumper-gated `PTT_x_N` OR the power-on hold.

## RF immunity

- Every jack entry: ferrite bead + shunt cap sized for HF, not just VHF
  (corner ~270 kHz on audio lines; larger on DC lines); every op-amp
  input pin gets its own RC stop.
- Feedthrough caps or C-L-C (cap–ferrite–cap) filters at every panel
  entry, including power and PTT lines.
- The box operates next to a transmitter; RF immunity dominates the
  design.

## Mechanical construction

Mixer-style, two boards:

- **Control board** horizontal under the sheet-metal top panel. PCB-mount
  pots, mute buttons, override selector, and LEDs through panel cutouts;
  pot bushings nutted to the panel (mounting + bonding). Preamps, buses,
  mutes, headphone amps, and the supply live here.
- **Rear I/O board** vertical behind the rear panel: DE-9, Powerpole,
  line out, PTT jacks, rear trims (mic out, line out L/R, RX input),
  bias and gain range switches, and the amplifiers those trims feed
  (mic-out driver U403, line amps U402) so no pot wiper crosses the
  interconnect. Jack bushings nutted through the panel.
- **Front apron jacks** (per side: 1/4" + 3.5mm mic, TRRS, 3.5mm + 1/4"
  phones): control-board front edge or a narrow third board — decide
  during layout.
- Board interconnect carries only line-level buses, DC, and PTT logic.
  Mic-level signals never cross a connector; each preamp lives on the
  board with its jacks.

## Enclosure (RF-tight)

Custom folded sheet aluminum (SendCutSend-class laser cut + CNC bend
service), wedge console profile:

- Geometry (provisional): 300 mm wide, ~13° slant, 45 mm front apron,
  150 mm slant surface → ~146 mm base depth, ~79 mm rear height.
- Two-piece shell: U-pan (base + wedge-profile sides) + wrap top (apron,
  slant surface, rear skirt in one bent piece). Overlapping flanged seams
  everywhere, screws into PEM nuts/tapped flanges every 25–40 mm.
- Chem-film (chromate/alodine) finish from the vendor — conductive on
  all mating surfaces. Anodize is an insulator — not on any mating
  surface.
- Top panel bonds to chassis along its perimeter — flange contact or
  finger stock/gasket, not just corner screws.
- Metal-body jacks wherever sourceable, bushings nutted to the panel so
  shields bond at the point of entry. Plastic PCB-mount jacks (TRRS): see
  pin 1 section.
- Pots and switches metal-body, bushings bonded to the panel.

### Grounding and the pin 1 problem

- No shield current flows through PCB ground. Shields bond to chassis at
  the point of entry: every jack sleeve, TRRS ring 2 and DE-9 return is
  on the `CHASSIS` net, which ties to signal `GND` at exactly one place
  (NT701, at the DE-9 on the Keying sheet).
- Everything is unbalanced (sleeve = shield = signal return), so the
  pin 1 problem can only be minimized: chassis-bonded sleeves + signal
  ground referenced to chassis at one point.
- Exception: the line-out jack J401 is **insulated-bushing** — its
  sleeve is the transformer secondaries' return (`LOUT_RET`), and a
  chassis bond there would defeat the isolation.
- **TRRS exception:** on CTIA the sleeve is the mic line and ground is
  Ring 2. Bond Ring 2 to chassis at entry; treat the sleeve as a signal
  line (ferrite + shunt cap).
- Metal-bushing chassis-mount jacks exist for 1/4" (Switchcraft
  11-series) and 3.5mm TRS (Switchcraft 35RAPC class); TRRS is scarce.
  For a PCB-mount plastic jack: mount hard against the grounded panel,
  stitch the PCB shield plane to chassis adjacent to the jack, keep the
  ground-to-chassis path under ~1 cm.

## Open items

- Line-out jack J401 must be an insulated-bushing part (isolation), and
  the rear GND post (J707) needs a chassis-stud part — both are footprint
  decisions.
- Layout: TPS7A4701 thermal pad pour/vias (the 385 mA thermal max in
  `power_tree.json` assumes it); single CHASSIS–GND tie at NT701 only.
- Footprint / MPN pass for every part (see TODO.md).

- RF immunity target, quantitative (e.g. "no audible artifacts with
  100 W on any HF band + 6 m, feedline within 1 m") — decides gasket
  vs. no gasket and filter corner frequencies.
- Front jack placement: control-board front edge vs. third board. Decide
  with enclosure dimensions (the mic-out/line-out amps now live on the
  rear board so no pot wiper crosses the interconnect).
- Enclosure: confirm final dimensions and seam/flange details once panel
  layouts freeze; panel labeling method (engraving vs. etch vs. overlay).
- Latching mute button sourcing: confirm availability (with or without
  integral LED) before committing the panel design.
- At layout: review every adjustment for accessibility once panel
  positions are known.
