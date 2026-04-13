# TODO — ThermistorBuffering.ipynb

Ordered roughly by impact.

## Missing analyses

- [ ] **°C-per-ADC-LSB figure.** The real FOM for a temperature chain.
  Given ADC bit count, show min/mid/max °C/LSB and worst-case deviation
  from an ideal linear fit over the operating range.
- [ ] **Op-amp constraints.** Surface required GBW (≈ G · f_signal),
  `Ib · Rpar(R_ntc, R1)` input-bias error, input common-mode range
  (+ input swings 0…Vdd — not all RRIO parts actually reach the rails),
  and Vos/Vos-drift budget. Source impedance at both T extremes is
  now printed (partial credit); the rest is still TODO.
- [ ] **Component-tolerance analysis.** E12 is ±10 %, E96 is ±1 %.
  Add a worst-case or Monte-Carlo sweep so the user sees what their
  series choice costs in °C of output error.

## Parametrization / UX

- [ ] **Asymmetric filter spec.** `Csmall` is specified by value, `C1`
  by cutoff. Pick one convention or allow either for both caps.
- [ ] **Independent Vout margins.** Replace the single
  `Vout_margin_percent` with independent `Vout_min` / `Vout_max` so
  asymmetric op-amp swing and ADC-DNL considerations can be expressed.

## Code quality

- [ ] **Split the mega-cell.** Cell 3 holds the sensor model,
  dataclasses, solver, plotting, HTML rendering, and helpers. Split
  into ~4 cells (model / solver / plotting / reporting).
- [ ] **Guard `%pip install`** behind a try/import so local runs aren't
  noisy. Keep it working on Colab.

## Plot (`plot_frequency_response`)

- [ ] **Rename "Filter Frequency Response"** or extend it — currently
  only the two passive RC stages are modeled; the op-amp gain is
  elided. True under the ideal-op-amp assumption, but not obvious to
  the user.
- [ ] **Plot input filter over the T range,** not just at 25 °C
  (source impedance varies with Rntc).
