# TBox Level Plan

Companion to [DESIGN.md](DESIGN.md). All levels in dBV (dB re 1 Vrms).
Speech nominal = long-term RMS; peaks assumed 12–15 dB above nominal
(crest factor). Noise bandwidth 20 kHz unless noted; the rig's ~3 kHz TX
filter buys ~8 dB beyond these figures.

## Rails and clip points

| Item | Value | Notes |
|---|---|---|
| Analog rail | 9.0 V | LDO from ≥10.5 V input, ≥1.5 V dropout margin |
| Vref | 4.5 V | buffered mid-rail |
| Op-amp swing | ~6 Vpp | NE5532-class, ~1.5 V from each rail |
| Clip point | +6 dBV | 2.1 Vrms, all internal nodes |
| Internal nominal | -15 dBV | 21 dB headroom to clip; peaks reach ~0 dBV |

## TX path (mic jack → mic out)

| Node | Nominal | Peak | Notes |
|---|---|---|---|
| Mic jack, dynamic | -57 dBV | -42 | HI range; Heil HC-6/HC-7 spec |
| Mic jack, electret | -45 dBV | -30 | LO range; OHIS/CMC-9745/Heil iC class |
| Mic jack, powered desk mic | -28 dBV | -13 | LO range, level pot low; Icom SM-30 |
| Preamp out | ~-15 dBV | ~0 | HI +45 dB / LO +25 dB |
| Mute node | -15 dBV | | ≤0.5 dB insertion; mute depth ≥60 dB (see below) |
| Level pot (design center) | -21 dBV | | 10k audio taper, ~-6 dB nominal |
| Summing amp / TX MIX bus | -15 dBV | ~0 | +6 dB makeup |
| Mic out, MIC mode | -46 dBV (5 mV) | | -31 dB pad, trim ±10 dB, 600 Ω build-out |
| Mic out, LINE mode | -10 dBV | | +5 dB stage, trim ±10 dB, drives 600 Ω |

**Mute depth:** a single JFET shunt only reaches ~-33 dB
(rON ~100 Ω against a ~4.7 kΩ series arm). Full mute requires a
**series + shunt JFET pair** per channel: series device opens, shunt
device clamps — ≥60 dB at 1 kHz. Both gates share the RC ramp.

**Gain range coverage:** with the level pot's reach (±10 dB around design
center), LO covers roughly -55…-30 dBV sources, HI covers -70…-50 dBV.
Overlap at -55…-50, no gap. Hot desk mics (SM-30, -28 dBV) land in LO
with the pot low.

## RX path (RX in → phones)

| Node | Nominal | Notes |
|---|---|---|
| RX in, K3S LINE OUT | -10 dBV | 600 Ω source; fixed level |
| RX in, phones-jack rigs | -30…+5 dBV | volume-dependent; pad tolerates +7 dBV (5 Vpp) |
| Input pad + trim out | -15 dBV | trim range -20…+5 dB after fixed -12 dB pad; 470 Ω load |
| RX bus (per side) | -15 dBV | |
| Monitor injection | up to -15 dBV | monitor pot: off → equal to RX |
| Headphone amp out, max | 0 dBV | +15 dB max gain after volume pot |

**Headphone power:** 1 Vrms = 31 mW into 32 Ω, ~40 mW into 16 Ω
(current-limited) — meets the ≥20 mW spec with margin. Requires a
9 V-capable driver (NJM4556A-class dual op-amp or op-amp + buffer);
LM4880/TPA6112-class parts are 5.5 V max and are out.

## Line out

| Node | Nominal | Notes |
|---|---|---|
| Source (RX bus or TX mix) | -15 dBV | per-side jumpers |
| Line amp | -10 dBV | +5 dB; rear trims -20…0 dB |
| After 600 Ω 1:1 transformer | -10 dBV | into ≥10 kΩ soundcard; ~-6 dB into 600 Ω |

## Noise budget

| Contributor | Target | Basis |
|---|---|---|
| Preamp EIN | ≤ -120 dBV | 4 nV/√Hz op-amp + 600 Ω source ≈ -123 dBV |
| TX SNR at bus, dynamic/HI | ≥ 60 dB | -123 + 45 = -78 dBV noise vs -15 dBV signal |
| TX SNR at bus, electret/LO | ≥ 78 dB | 20 dB less gain, hotter source |
| RX path SNR | ≥ 85 dB | line levels throughout |
| Bias rail noise at mic node | ≤ 3 µVrms | ~71 dB below -35 dBV electret; LDO + 2-pole RC (≤10 Hz) |
| Vref | buffered, ≤10 µV | common to all stages; rejected differentially where possible |

## Response targets

- Box-wide: 150 Hz – 8 kHz ±1 dB (rig TX filter is the real limit).
- Line out through transformer: verify 150 Hz at full level without
  saturation (600 Ω 1:1 driven from low-Z, loaded ≥10 kΩ).

## Published source data

| Item | Value | Source |
|---|---|---|
| Heil Pro Set / Pro 7 (HC-6/HC-7 dynamic) | -57 dB @ 1 kHz, 600 Ω | [1], [2] |
| Heil iC electret element | -48 dB @ 1 kHz, 1.5 kΩ | [1], [2] |
| OHIS electret mic level | -45 dBV ±3 into 600–1k Ω | [3] |
| CUI CMC-9745 capsule | -44 dBV/Pa; 3 V std, 0.5 mA, 2.2 kΩ | [4] |
| Icom SM-30 desk mic | -28 dB ±4 (re 1 V/Pa), 600 Ω, 8 V powered | [5] |
| Icom SM-50 desk mic | -30 dB ±4 (re 1 V/Pa), 55 Ω | [6] |
| Icom HM-36 | unpublished (electret, 8 V) | [7] |
| Icom mic input | 600 Ω; pin 2 = +8 V, 10 mA max | [8] §12-2 |
| Icom ACC MOD input | 100 mV rms nominal, 10 kΩ | [8] §12-1 |
| Android TRRS bias | 1.8–2.9 V via 2.2 kΩ; mic ≥1 kΩ DC | [9], [10] |
| OHIS bias | 5 V via ~6.8 kΩ (~0.5 mA, ~2 V at element) | [3] |
| K3S LINE OUT | no published level; ~1 Vp-p @ 600 Ω anecdotal | [11], [12] (unverified) |

Bias note: TBox's 5 V through 2.2 kΩ leaves ~4 V at a 0.5 mA capsule —
within capsule ratings (10 V max), same practice as Icom's 8 V feed.

### References

1. Heil Pro Set: <https://heilhamradio.com/product/pro-set/>
2. Heil Pro 7: <https://heilhamradio.com/product/pro-7/>
3. Open Headset Interconnect Standard v0.3:
   <https://open-headset-interconnect-standard.github.io/ohis/Open-Headset-Interconnect-Standard.pdf>
   (via <https://ohis.org>; see also the Icom OHIS adapter writeup at
   <https://electronics.halibut.com/2023/12/30/simple-ohis-user-adapter-for-icom-radios/>)
4. CUI/Same Sky CMC-9745-44P datasheet:
   <https://www.sameskydevices.com/product/resource/cmc-9745-44p.pdf>
5. Icom SM-30: <https://www.icomjapan.com/lineup/options/SM-30/>
6. Icom SM-50: <https://www.icomjapan.com/lineup/options/SM-50/>
7. RigPix HM-36 (sensitivity listed "?"):
   <https://www.rigpix.com/microphones/icom_hm36.htm>
8. Icom IC-7300 Basic Manual:
   <https://www.hamradio.co.uk/userfiles/file/IC-7300_ENG_Basic_0.pdf>
9. Android wired headset jack (device) spec:
   <https://source.android.com/docs/core/interaction/accessories/headset/jack-headset-spec>
10. Android wired headset (accessory) spec:
    <https://source.android.com/docs/core/interaction/accessories/headset/plug-headset-spec>
11. Elecraft reflector, K3 LINE OUT recording thread:
    <https://elecraft.mailman.qth.narkive.com/2rhZ9MtJ/k3-recording-from-lin-out>
12. Elecraft archive, LINE OUT level discussion:
    <https://groups.google.com/g/elecraft-archive/c/C5ZKMZ0uXeM>

Also consulted: K3S Owner's Manual rev A1 (LINE OUT/LINE IN/MIC jack
descriptions, no mV figures published):
<https://ftp.elecraft.com/K3S/Manuals%20Downloads/K3S%20Owner's%20man%20A1.pdf>;
Heil "All Things iCOM" tech note (8 V on pin 1, DC-block adapters):
<https://static.dxengineering.com/global/images/technicalarticles/ico-ic-7300_bk.pdf>

## Measurements still needed

- K3S LINE OUT actual level at CONFIG:LIN OUT = 10 (bench, one-time).
- HM-36 output if one is on hand (expected between Heil iC and SM-30).
