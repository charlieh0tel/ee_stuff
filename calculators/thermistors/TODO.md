# TODO — ThermistorBuffering.ipynb

Ordered roughly by impact.

## Correctness

- [x] **Verify actual Vout range after rounding.** Compute
  `Vout = Vin·(1 + R4/(R2∥R3)) − R4·Vdd/R3` with *rounded* R2/R3/R4 and
  report `Vout_actual(Tmin)` and `Vout_actual(Tmax)`. Warn if either
  violates the margin. Today only `gain_actual` is shown; rounding R3
  shifts the offset and can push an extreme into a rail invisibly.
- [x] **Grid-search R2/R3/R4 over E-series neighbors** instead of
  rounding each independently from ideal values. Implemented as a
  3×3×3 search (R4 is also in the search since it scales R2/R3 ideal
  values linearly). Objective: feasibility first (both Vout extremes
  inside the requested margin), then maximise Vout span for best ADC
  utilisation; fall back to least-worst margin violation. Fixes the
  notebook's own default E12 case, which was violating both rails
  with the greedy pick.
- [x] **Input-filter cutoff varies with T.** `fcsmall_actual` uses
  `ntc.r0` (25 °C only). Source impedance is `Rpar(R_ntc(T), R1)` and
  swings several× across the operating range. Report fc at both
  temperature extremes (or worst case).
- [ ] **`KtoC` strips `.magnitude` without rescale.** Silently wrong if
  passed a non-K quantity. Rescale to K first, or assert units.
- [x] **Input validation.** Check `Tmin < Tmax`, `Vout_min < Vout_max`,
  `G_ideal > 1`, `Vin_max < Vdd`. Currently bad inputs silently produce
  NaN or wrong results.

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

- [ ] **Inconsistent `eseries_wrapper` use.** R1/R2/R3/Csmall/C1 go
  through the wrapper; R4 and R5 call `eseries.find_nearest` directly
  and tack on `* pq.Ohm`. Unify.
- [ ] **Inconsistent rounding direction.** R1 uses
  `find_greater_than_or_equal`; everything else uses `find_nearest`.
  Either unify or comment the intent.
- [x] **Drop redundant `* pq.CompoundUnit("V/V")` on `G_ideal`.** V/V is
  already dimensionless; the wrapper just makes `G_ideal - 1` brittle
  and error messages uglier. (Also dropped from `gain_actual`, which is
  now a plain `float`.)
- [ ] **Delete the unused `p()` helper.** Defined, uses `eval`, never
  called.
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
- [ ] **Drop hardcoded `ax1.set_ylim(-60, 5)`.** Clips real curves.
  Auto-range or make it a parameter.
- [ ] **Plot input filter over the T range,** not just at 25 °C (same
  root cause as the `fcsmall_actual` item above).
