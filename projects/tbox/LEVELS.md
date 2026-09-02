# TBox Level Plan

Companion to [DESIGN.md](DESIGN.md). All levels in dBV (dB re 1 Vrms).
Speech nominal = long-term RMS; peaks assumed 12–15 dB above nominal
(crest factor). Noise bandwidth 20 kHz unless noted; the rig's ~3 kHz TX
filter buys ~8 dB beyond these figures.

## Rails and clip points

| Item | Value | Notes |
|---|---|---|
| Analog rail | 9.0 V | TPS7A4701 from ≥10.5 V input (~0.8 V margin after PTC + Schottky; dropout 0.22 V) |
| Vref | 4.5 V | buffered mid-rail |
| Op-amp swing | ≥7.4 Vpp | OPA1678: output guaranteed within 0.8 V of each rail at 2 kΩ; input CM range 0.5–7.0 V |
| Clip point | +8 dBV guaranteed | 2.6 Vrms; the plan below still budgets against +6 dBV for 2 dB of slack |
| Internal nominal | -15 dBV | 21 dB headroom to the +6 dBV planning figure; peaks reach ~0 dBV |

## TX path (mic jack → mic out)

| Node | Nominal | Peak | Notes |
|---|---|---|---|
| Mic jack, dynamic | -57 dBV | -42 | HI range; Heil HC-6/HC-7 spec |
| Mic jack, electret | -45 dBV | -30 | LO range; OHIS/CMC-9745/Heil iC class |
| Mic jack, powered desk mic | -28 dBV | -13 | LO range, level pot low; SM-30 class (reference only — Icom powered mics unsupported) |
| Preamp out | ~-17 dBV | ~-2 | HI +40 dB / LO +20 dB (two +20 dB stages; 8 dB peak margin to clip) |
| Mute node | -15 dBV | | ≤0.1 dB insertion (Ron ~5 Ω into 10k); mute depth >70 dB (see below) |
| Level pot (design center) | -21 dBV | | 10k audio taper, ~-4 dB nominal |
| Summing amp / TX MIX bus | -15 dBV | ~0 | +6 dB makeup |
| Mic out, MIC mode | -46 dBV (5 mV) | | +5 dB driver then -26 dB pad (~690 Ω source incl. the DE-9 series R); rear trim used range -20…0 dB ahead of the driver, nominal at -10 dB |
| Mic out, LINE mode | -10 dBV open, -12.5 dBV into 600 Ω | | +5 dB driver, trim at max; 200 Ω total build-out with the DE-9 series R |

**Mute depth:** the TS12A12511 SPDT opens the signal path and clamps
the node to Vref in one move (series + shunt): off isolation is -70 dB
at 1 MHz and better at audio. The residual is the switching step, which
is the driving op-amp's offset (≤4 mV, ~-48 dBV, 33 dB below nominal)
applied once — not a tone.

**Gain range coverage:** with the level pot's reach (±10 dB around design
center), LO covers roughly -50…-25 dBV sources, HI covers -65…-45 dBV.
Overlap at -50…-45, no gap. The unselected stage still runs; in LO mode
with a hot electret it clips off-path (harmless but worth knowing on the
bench).

## RX path (RX in → phones)

| Node | Nominal | Notes |
|---|---|---|
| RX in, K3S LINE OUT | -10 dBV | 600 Ω source; fixed level |
| RX in, phones-jack rigs | -30…+5 dBV | volume-dependent; the trim absorbs +5 dBV (5 Vpp) sources |
| Trim + buffer out | -15 dBV | 10 kΩ bridging load, rear trim, +15 dB buffer: total gain +15…-∞ dB, no fixed pad |
| RX bus (per side) | -15 dBV | |
| Monitor injection | up to -15 dBV | monitor pot (buffered): off → equal to RX |
| Mix node (per ear) | -24.5 dBV per source | passive mix into the volume gang (-9.5 dB) |
| Headphone amp out, max | -0.4 dBV open | +24 dB after the volume pot; 10 Ω build-out |

**Headphone power:** 0.955 Vrms open through the 10 Ω build-out gives
~17 mW into 32 Ω and ~22 mW into 16 Ω — meets the ≥20 mW/16 Ω spec for
one headset per position; three paralleled 16 Ω headsets current-limit
at ~4 mW each. Requires a 9 V-capable driver (NJM4556A); LM4880/TPA6112-
class parts are 5.5 V max and are out.

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
| Bias rail noise at mic node | ≤ 3 µVrms | ~71 dB below -35 dBV electret; LDO + RC (~15 Hz) + 100n at the mic node |
| Vref | buffered, stiff | DC bias only — every gain-setting leg of a ground-referenced stage returns to GND, so Vref noise is never amplified |

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

## Measurements

None required for design. The one unpublished figure — K3S LINE OUT
level (anecdotally 0.1–0.8 Vrms depending on CONFIG:LIN OUT) — falls
entirely within the RX input pad + trim range, and gets absorbed when
the trims are set at first hookup.
