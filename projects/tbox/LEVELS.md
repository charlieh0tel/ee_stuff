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
| Mic jack, dynamic | -55 dBV | -40 | HI range |
| Mic jack, electret/Icom | -35 dBV | -20 | LO range |
| Preamp out | -15 dBV | ~0 | HI +40 dB / LO +20 dB |
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
center), LO covers roughly -45…-25 dBV sources, HI covers -65…-45 dBV.
No gap. Quiet computer headsets (~-40 dBV) land in LO with the pot high.

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
| TX SNR at bus, dynamic/HI | ≥ 65 dB | -123 + 40 = -83 dBV noise vs -15 dBV signal |
| TX SNR at bus, electret/LO | ≥ 80 dB | 20 dB less gain, hotter source |
| RX path SNR | ≥ 85 dB | line levels throughout |
| Bias rail noise at mic node | ≤ 3 µVrms | ~71 dB below -35 dBV electret; LDO + 2-pole RC (≤10 Hz) |
| Vref | buffered, ≤10 µV | common to all stages; rejected differentially where possible |

## Response targets

- Box-wide: 150 Hz – 8 kHz ±1 dB (rig TX filter is the real limit).
- Line out through transformer: verify 150 Hz at full level without
  saturation (600 Ω 1:1 driven from low-Z, loaded ≥10 kΩ).

## Measurements needed

- Actual Icom mic output (HM-36, SM-30) — the -35 dBV assumption is
  recollection, not data.
- A sample of computer/gaming TRRS headsets: output level and bias
  current draw.
- K3S LINE OUT actual level at CONFIG:LIN OUT = 10.
