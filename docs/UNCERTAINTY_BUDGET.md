# Inspect modeled uncertainty contributions

Select a monitoring hour to see response-noise and fitted-parameter contributions to the inverse estimate's variance. With `x=(y-a)/b`, response variance is `u_y²/b²`; fitted-parameter variance is `(var(a)+2*x*cov(a,b)+x²*var(b))/b²`. Their sum equals the displayed combined standard uncertainty squared. Shares show which modeled source dominates for that sample; evaluation-reference values never enter this calculation.

The signed fit covariance cross term is shown for transparency. It can be negative and is **already included** in the fitted-parameter contribution: adding it again is incorrect. Fractions describe variance, not absolute error or probability. No residual rescaling, physical reference uncertainty, unmodeled correlation, certified coverage interval or causal fault diagnosis is added.

Missing/clipped, out-of-span, expired, failed-check or otherwise withheld estimates retain null budget fields. Unknown uncertainty is never zero uncertainty. JSON, sample CSV, HTML and CLI/history retain scalar budget fields under the evidence hash. The unchanged C# weighted-fit kernel still must match exact-rational Python reference coefficients/covariance. Source and Actions SDK pins now use installed stable10.0.403 consistently; numerical target/runtime and locked packages are unchanged.
