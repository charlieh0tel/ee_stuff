# A Diode Is Not a Square-Law Device

## Publication targets

- **Primary:** club newsletter — shorter, simpler, minimal math, conversational tone
- **Stretch:** QEX — can go longer and add more quantitative detail if the newsletter version is well-received

## Audience

Technically literate hams. Know what a mixer and a detector are, have built or used crystal radios, understand RF concepts. Not assumed to be EE graduates or comfortable with calculus.

## Core argument

A diode's I-V characteristic is exponential, not quadratic. "Square-law device" is an approximation that holds only in a limited amplitude range and only for the nonlinear part of the response — the linear term is always present and always dominant at small signals. The approximation is useful and important, but understanding its limits matters for both detection and mixing.

## Single-tone vs. two-tone distinction

Keep these separate throughout — same nonlinearity, different consequences:

- **Single tone (detection):** the v² term produces a DC output proportional to V², i.e., proportional to power. This is the "square-law detector" claim: DC out tracks RF power in. Crystal radios, envelope detectors, power meters.
- **Two tones (mixing):** the v² term cross-multiplies two signals at f₁ and f₂ to produce f₁ ± f₂. The linear term produces no sum/difference output at all. Superheterodyne receivers, product detectors, IMD analysis.

## Outline

1. **The claim** — where "square-law device" comes from; preview the single-tone/two-tone split
2. **What the diode actually does** — exponential I-V, stated not derived; graph of the curve
3. **Why square law seems right — detection** — v² → DC ∝ power; this is what detectors exploit
4. **Why square law seems right — mixing** — v² cross-multiplies two tones → f₁ ± f₂; linear term contributes nothing here
5. **Why it's wrong — the linear term always wins** — straight-line response is always larger than the parabolic term for small signals; consequences for both detection and mixing
6. **The sweet spot** — amplitude range where v² dominates the nonlinearity; below → linear (no detection/conversion); above → higher-order terms, distortion, compression
7. **Practical takeaways** — why Ge/Schottky beat Si for weak-signal detection; why bias helps; LO drive level in mixers; what "square-law range" means on a datasheet

## Length

- Newsletter version: 2–3 pages, one figure, no equations or at most one
- QEX version: 3–4 pages, two figures (I-V curve + regime diagram), light algebra acceptable

## Figures

- I-V curve annotated to show the three regimes (linear / square-law / exponential)
- Possibly adapt the regime amplitude diagram from diode_smallsignal.tex

## Relation to diode_smallsignal.tex

This is the companion "why it matters" piece. The full derivation document has the math; this one has the physical intuition and practical consequences. Can reference the full document for readers who want the derivation.
