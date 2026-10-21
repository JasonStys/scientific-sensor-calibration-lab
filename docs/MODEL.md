# Calibration model, units and limitations

## Inputs and assumptions

The illustrative instrument converts a reference quantity `x` into response `y=a+b*x+error`. Browser examples use degC and mV only; values are fictional, not measured temperature telemetry. Strict JSON reference values are milli-units (`x_milli`/`reference_milli` divided by1000); response and response standard uncertainty are microvolts (`signal_uv`, `u_uv` divided by1000 to mV). Unit labels are metadata, **not automatic conversions**. CLI custom inputs must use one consistent reference unit and mV response after fixed scaling. Hour indices are synthetic ordered sample slots, not logged timestamps or inferred sampling rates.

The model assumes exact/error-free reference values, independent zero-mean response errors, and supplied **known** positive response standard uncertainties. No reference uncertainty, covariance between observations, hysteresis, non-Gaussian error model, environmental correction, repeatability estimation or standards traceability is inferred. The inverse propagation is first-order and conditional on the linear model and fitted slope, not an exact inverse-prediction confidence interval.

## Weighted fit

For usable calibration records only, `w_i=1/u_i²`. C# computes weighted means and centered sums; Python independently solves raw weighted normal equations with exact Fraction arithmetic. The calibration matrix is two columns (constant and x):

```text
b = sum[w (x−xbar)(y−ybar)] / sum[w (x−xbar)²]
a = ybar − b*xbar
var(b) = 1/Sxx
cov(a,b) = −xbar/Sxx
var(a) = 1/sum(w) + xbar²/Sxx
reduced chi-square = sum[((y−a−b*x)/u)²] / (n−2)
```

This is a known-response-variance covariance model; it is **not** multiplied by reduced chi-square. Inflating covariance automatically after misfit could conceal an invalid linear relationship. Users can explore declared-uncertainty multipliers, but must not reinterpret a relaxed review threshold as new evidence. GUI sigma multiplies supplied uncertainties only, not observed readings. Increasing sigma can change gates; it does not fix nonlinearity or establish a better physical model.

At least4 usable calibration points and at least1 reference-unit span are required. Repeated reference levels are permitted, not a substitute for span. Absolute fitted slope must be≥0.01mV/reference-unit. This is a documented numerical scope boundary, not an instrument sensitivity recommendation. Points at/beyond configured electronics rails are excluded as saturated; missing signals are excluded, not imputed.

Every native fit field, including unavailable status/count, must agree with the independent reference at **1e−7 absolute /1e−8 relative** tolerance before reporting. Native unknown fields/nonfinite/malformed output, timeout and failure prevent verified evidence. The independent implementation verifies the equations, not their suitability to a real sensor. Fit/correction calculations use full precision; only final report floats are normalized to ten significant digits for stable readable evidence. This is a serialization convention, not uncertainty-based significant-figure certification. The SHA-256 hashes canonical finite sorted JSON excluding `id`; it identifies contents, not trusted authorship or physical traceability.

## Separate checks and quality gates

Check records do not participate in fitting. A usable in-span check has standardized response residual:

```text
z_check = (y_check − a − b*x_ref) / sqrt(u_check² + var_fit(x_ref))
var_fit(x) = var(a) + 2*x*cov(a,b) + x²*var(b)
```

Missing, saturated or outside-span checks remain visible but are excluded from usable-check count. At least2 usable checks and all usable check magnitudes≤configured z-limit are required. Reusing the same observation in training/check sets would violate the independent-check assumption; the program cannot infer experimental independence from numbers. Synthetic examples construct distinct check records/noise. No blanket goodness-of-fit probability, p-value or family-wise false-positive rate is claimed for these configurable thresholds.

Gate precedence: unusable fit → excessive reduced chi-square → insufficient/failed checks → calibration age greater than maximum. A model passing these finite checks has gate`ok`, not “certified.” Default chi-square review threshold9 and max age90days are illustrative configurable rules, not standards or manufacturer intervals. Age equal to the limit is allowed. Age is explicit metadata, not read from the host clock or a forged instrument timestamp.

## Correction and uncertainty

For each usable response after global gates:

```text
x_est = (y_new−a)/b
u_combined(x_est) = sqrt(u_new² + var_fit(x_est)) / abs(b)
```

No extrapolation: x_est must lie within usable calibration reference span. Otherwise estimate/u are withheld. Available estimates display±1 combined **standard** uncertainty, not guaranteed bounds/95%coverage. Monitoring `reference_milli` is separate evaluation truth supplied by the fictional dataset, never part of the inverse correction. When present, `error=x_est−reference` and `z=error/u_combined`; excessive magnitude marks `reference-mismatch` but retains the diagnostic estimate/u. When absent, error/z remain null. A mismatch can have multiple causes; the algorithm does not establish causal drift or repair a calibration automatically.

Missing and saturated samples take precedence over model-gate reasons. All other invalid/global-gate samples retain original signal/reference but null estimate/u/error/z. RMSE and mean error cover only samples with both an available estimate and supplied reference. Evaluated-reference count, total sample count and withheld count are always reported, preventing a zero-case result from looking perfect. Rejected/unknown-reference observations are not silently counted as zero error. There is no raw-versus-corrected improvement claim without a defined baseline.

## Synthetic cases and numerical scope

All data is invented in `model.configuration`: nine nominal calibration levels0..100degC, five separate checks,24 monitoring slots; nominal response400+20*x mV with deterministic small errors. Unequal-noise case varies declared uncertainty and errors; drift case increases later response offset; clipping case hits two rails plus an in-electronics/out-of-calibration reading; missing case removes two calibration and two monitoring readings; nonlinear case adds a quadratic term and deliberately violates the linear assumption. One monitoring reference is absent in every preset. Electronics rails300..2600mV apply to all examples; the nonlinear case also clips high-response records. All162 finite controls are tested. A complete replayable example is `examples/instrument.json`.

The strict bounded schema accepts calibration/check sets≤64 and monitoring≤168. Weighted fitting is linear in point count in arithmetic operations, but Fraction bit-complexity grows with input denominators. This is not an O(n) constant-bit-cost promise for arbitrary precision/unbounded data. Bounds and native worker10s deadline are resource controls, not a real-time guarantee. Native total RSS is not inferred from Python tracemalloc measurements.

## Primary research

[NIST calibration of future measurements](https://www.itl.nist.gov/div898/handbook/mpc/section3/mpc366.htm) describes inverse use of a calibration relationship. [NIST Dataplot calibration](https://www.itl.nist.gov/div898/software/dataplot/refman1/auxillar/calibrat.htm) discusses calibration/inverse-prediction methods and the fixed-reference assumption. Those sources motivate separating response fitting from inverse estimation and uncertainty; this lab does not implement every NIST method or claim an exact classical inverse-prediction interval. [NIST errors-in-variables discussion](https://www.nist.gov/publications/errors-variables-calibration-dark-uncertainty) highlights reference/error complications omitted here. No endorsement or accreditation is implied. [Microsoft deployment documentation](https://learn.microsoft.com/en-us/dotnet/core/deploying/single-file/overview) distinguishes self-contained distribution and OS/architecture-specific binaries; this lab uses an untrimmed runtime directory inside its portable bundle.
