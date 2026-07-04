# TBox — Transceiver Companion Box

A shack interface box between a pair of operator headsets and a ham
transceiver. Two mixable microphone channels, dual stereo headphone
outputs, an isolated stereo line out, PTT inputs with selectable override,
and a generic rig connector with rig-specific cables.

## Design decisions

| Decision | Choice |
|---|---|
| Mic connectors | 3.5mm TRS/TRRS, 8-pin Foster round, 1/4" TRS (no XLR) |
| Condenser support | Electret bias only (~5 V); +8 V accessory pin for Icom-style mics |
| Rig connection | Generic DE-9 on box + rig-specific cables |
| Channel layout | Two fixed, identical channel groups (A and B) — no cross-assignment |
| Headset usage | Both channels mixable; override selector: OFF / A→B / B→A |
| Muting | Full mute only (no ducking), JFET series+shunt, pop-free, LED indicated |
| Intercom | Global momentary button: mutes TX mix to rig, monitor stays live |
| RX path | Stereo throughout (main/sub for dual-receive rigs; mono rigs feed both) |
| Line out | Stereo, per-side source jumpers, levels via rear trims |
| VOX | Assumed OFF at the rig — TX mix is always present at mic out |
| Power | 12–14 V via Anderson Powerpole, runs down to ~10.5 V, all-linear, single rail |
| Construction | Mixer-style: control PCB under sheet-metal top panel, rear I/O PCB |
| Digital | None — all-analog, no MCU, no clocks |

## Block diagram

```
 CH A jacks ─┬─ bias sw ─ preamp A ─ mute A ─ level A ─┐
 (3.5mm, TRRS,│                        ▲ (LED)         │
  1/4", Foster)                 button or OVR B→A      │
                                                       ├─ TX MIX BUS
 CH B jacks ─┬─ bias sw ─ preamp B ─ mute B ─ level B ─┘     │
 (3.5mm, TRRS,│                        ▲ (LED)               ├──► monitor tap
  1/4", Foster)                 button or OVR A→B            │    (to phones)
                                                             │
                                              INTERCOM mute ─┤
                                     (momentary; locked out  │
                                      while PTT is down)     ├──► MIC OUT to rig
                                                             │    (padded, trim)
                                                             └──► LINE OUT
                                                                  TX-side jumper
 RX L ── pad ── trim ──┬─────────────────────────► LINE OUT L/R (isolated,
 RX R ── pad ── trim ──┤                            per-side source jumpers,
 from rig              │                            rear level trims)
 (mono cables tie L+R) │
                       ▼
     PHONES A (stereo) ◄── vol A × (RX L/R + mon A × TX MIX both ears)
     PHONES B (stereo) ◄── vol B × (RX L/R + mon B × TX MIX both ears)

 PTT A (3.5mm ∥ 1/4" ∥ Foster pin) ──┬── PTT logic ── PTT to rig
 PTT B (3.5mm ∥ 1/4" ∥ Foster pin) ──┘   │            (open-drain MOSFET,
                                         │             TX LED)
              OVERRIDE selector: OFF / A→B / B→A
              (A→B: PTT A keys rig AND mutes channel B; B→A mirror)

 RIG ◄── DE-9: MIC, MIC GND, PTT, RX L, RX R, RX GND, spare; shield
```

## Channel groups

Two identical, physically grouped channel sections (A and B). Each has:

- **Mic jacks:** 3.5mm TRS, mic side of the TRRS combo, 1/4" TRS, and an
  8-pin Foster. All paralleled into one preamp; plug a mic into exactly
  one (not enforced by switching contacts).
- **Electret bias switch** (rear panel): ~5 V through 2.2 kΩ from the
  bias rail; applies to all jacks in the group.
- **+8 V accessory pin (Foster):** current-limited (~10 mA), routable via
  the pin-map DIP for Icom-style mics (SM/HM series) that power their
  electrets from a separate pin.
- **Gain range switch** (rear panel, beside the bias switch): LO ~+25 dB
  (electrets, ~-45 dBV; Icom powered mics ride the level pot down) /
  HI ~+45 dB (dynamics, ~-57 dBV Heil class). Both ranges land nominal
  mic level at the same point at the channel level pot, which handles
  fine adjustment. Exact gains per [LEVELS.md](LEVELS.md).
  The switch throws a DC control line; gain switching happens at the
  preamp via signal relay or DG-class analog switch (mic-level signals
  don't cross boards).
- **Mute button:** front panel, latching/alternate-action (NKK/Schadow
  style; fallback: toggle, or momentary + flip-flop). Full mute: JFET
  series + shunt pair after the preamp (a single shunt only reaches
  ~-33 dB; the pair gives ≥60 dB), RC-ramped gates (~10 ms), muting node
  AC-coupled with no DC across the JFETs (DC across the mute element
  pops). Override mute uses the same circuit, triggered electrically.
- **Channel level pot** into the TX mix bus.
- **PTT jacks:** 3.5mm and 1/4", paralleled, contact-closure, plus the
  Foster PTT pin.
- **Foster pin mapping:** DIP switch or jumper block (Yaesu/Kenwood/Icom
  pinouts differ); sealed switches — mic audio routes through the
  contacts. UP/DWN buttons unsupported (no data path to the rig).

## Buses and outputs

- **TX mix bus:** channel A + B, post-mute, post-level-pot. Order on the
  bus: summing amp → monitor tap → intercom mute → mic out pad / line out
  TX tap.
- **Intercom:** global momentary button (front panel, reachable from both
  positions). While held, a JFET pair mutes the TX mix downstream of the
  monitor tap: operators hear each other, nothing reaches the rig or the
  line out. **PTT wins:** while the rig is keyed, the intercom is locked
  out (its DC control line is gated by the PTT output state) and its LED
  stays dark.
- **Mic out to rig:** TX mix padded to ~5 mV mic level, ~600 Ω source
  impedance, DC-blocking cap (rigs may put electret bias on their mic
  pin). Level trim rear-accessible — must not require opening the box.
  Trim range (or jumper) extends to line level (~300 mV) for rigs with a
  line-level TX input. Must drive a 600 Ω load. Level setting uses the
  rig's ALC/mic-gain meter — the box has no metering.
- **RX audio input (stereo):** RX L and RX R (main/sub on dual-receive
  rigs; mono rig cables feed L, bridged to both). Each: input pad
  tolerant of speaker level (~5 Vpp), ~470 Ω load resistor, wide-range
  trim (covers rigs whose only output is the volume-dependent phones
  jack).
- **Line out (stereo):** 3.5mm TRS, ~ -10 dBV, transformer isolated
  (two 600 Ω 1:1) to break the inevitable sound-card ground loop.
  Per-side source jumpers: RX L, RX R, RX blend, or TX mix. Levels via
  rear trims. TX tap is post-mute (recordings reflect what went out).
- **Monitor bus:** TX mix (tapped ahead of the intercom mute) feeds each
  headphone position (both ears equally) through its monitor-mix pot; pot
  at zero = off. Tap is post-fader: the channel level pot affects the
  monitor too.

## Headphone outputs (2 positions, stereo)

- Per position: 3.5mm phones, 1/4" phones, and the phones side of the
  TRRS combo, all paralleled off one stereo headphone amp.
- Headphone amp: NJM4556A-class dual op-amp or op-amp + buffer, powered
  from the 9 V rail. ≥20 mW per channel into 16 Ω; stable with multiple
  headphones in parallel.
- Two pots per position: volume (dual-gang) and monitor-mix level. Each
  ear: volume × (RX that side + monitor-pot × TX mix).
- TRRS wiring is CTIA.

## Keying

- Per channel: 3.5mm + 1/4" PTT jacks (paralleled) plus the Foster PTT
  pin and a front-panel momentary PTT button, all in parallel. Contact
  closure to ground; inputs pulled up, clamped, and filtered (keyers and
  computer interfaces may drive them).
- **Override selector, 3-position: OFF / A→B / B→A.** A→B: channel A's
  PTT keys the rig and fully mutes channel B while closed; B→A mirror.
  OFF: both PTTs just key the rig.
- Rig PTT output: open-drain MOSFET (tolerates 12 V+ pull-ups).
- Jumper option per channel: PTT gates the channel's own audio (mic live
  only while keyed) — also the mitigation if rig VOX must be on.

## Indicators

- Power LED.
- TX lamp (PTT output asserted) — prominent, visible from across the desk.
- Per-channel PTT LED (that channel's PTT input closed).
- Per-channel mute LED (true JFET state — button or override).
- Intercom LED (lit while the intercom mute is engaged).
- All DC-driven.

## Rig interface

- DE-9 (female) on the box; rig cables carry: MIC, MIC GND, PTT, RX L,
  RX R, RX GND, +1 spare (reserved for a possible CW key line); shield to
  chassis. Mono rig cables tie RX L and RX R together at the DE-9.
- Protect every pin against ±12 V — DE-9 invites accidental RS-232
  hookups.
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
- **All-linear, single rail** (bipolar rails would require a charge pump
  or switcher):
  - Input π filter → LDO → **9 V analog rail** (Vref 4.5 V; internal
    nominal -15 dBV, clip +6 dBV — see [LEVELS.md](LEVELS.md)).
  - Buffered mid-rail virtual ground (Vref); all signal paths AC-coupled.
  - ~5 V **electret bias rail**, LDO + heavy RC (bias noise appears
    directly in the mic signal).
  - **+8 V accessory feed**, current-limited ~10 mA, small LDO or
    filtered dropper.
- JFET mutes single-supply: signal node at Vref; gate well below Vref =
  pinched off (unmuted), gate at Vref = shunting (muted). Pinch-off must
  sit inside the Vref window — J113-class, not J111.
- PTT logic is diode-OR and discretes; mute ramps are RC networks.

## RF immunity

- Every jack entry: ferrite bead + small shunt cap.
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
  line out, PTT jacks, rear trims (mic out, line out RX/TX, RX input),
  bias and gain range switches. Jack bushings nutted through the panel.
- **Front apron jacks** (per side: 1/4" + 3.5mm mic, TRRS, 3.5mm + 1/4"
  phones): control-board front edge or a narrow third board — decide
  during layout. Fosters are chassis-mount on the side walls, short
  flying leads to their channel's preamp.
- Board interconnect carries only line-level buses, DC, and PTT logic.
  Mic-level signals never cross a connector; each preamp lives on the
  board with its jacks.

## Enclosure (RF-tight)

Custom folded sheet aluminum (SendCutSend-class laser cut + CNC bend
service), wedge console profile:

- Geometry (provisional): 300 mm wide, ~13° slant, 45 mm front apron,
  150 mm slant surface → ~146 mm base depth, ~79 mm rear height.
- Foster mic connectors mount on the side walls, one per side, facing
  their operator — keeps plugs/cords out of the hand zone and the front
  interior clear.
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
  the point of entry.
- Everything is unbalanced (sleeve = shield = signal return), so the
  pin 1 problem can only be minimized: chassis-bonded sleeves + signal
  ground referenced to chassis at one point.
- **TRRS exception:** on CTIA the sleeve is the mic line and ground is
  Ring 2. Bond Ring 2 to chassis at entry; treat the sleeve as a signal
  line (ferrite + shunt cap).
- Metal-bushing chassis-mount jacks exist for 1/4" (Switchcraft
  11-series) and 3.5mm TRS (Switchcraft 35RAPC class); TRRS is scarce.
  For a PCB-mount plastic jack: mount hard against the grounded panel,
  stitch the PCB shield plane to chassis adjacent to the jack, keep the
  ground-to-chassis path under ~1 cm.

## Open items

- RF immunity target, quantitative (e.g. "no audible artifacts with
  100 W on any HF band + 6 m, feedline within 1 m") — decides gasket
  vs. no gasket and filter corner frequencies.
- Front jack placement: control-board front edge vs. third board. Decide
  with enclosure dimensions.
- Enclosure: confirm final dimensions and seam/flange details once panel
  layouts freeze; panel labeling method (engraving vs. etch vs. overlay).
- Latching mute button sourcing: confirm availability (with or without
  integral LED) before committing the panel design.
- Bench measurements (see LEVELS.md): K3S LINE OUT actual level; HM-36
  output if available.
- At layout: review every adjustment for accessibility once panel
  positions are known.
