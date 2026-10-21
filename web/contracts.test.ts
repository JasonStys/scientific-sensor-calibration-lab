/** Unit tests for bounded calibration display contracts by Jason Stys. Index: docs/CODE_INDEX.md. */
import { expect, test } from "vitest";
import { label, number, parseRun } from "./contracts";
/** Build a minimal protocol fixture; this is not a replacement fitting oracle. */
function fixture() {
  return {
    id: "a".repeat(64),
    name: "test",
    settings: { scenario: "linear-clean", sigma: 1, limit: 3, age: 0 },
    input: {
      unit: "degC",
      provenance: "Synthetic",
      config: { z_limit: 3, age_days: 0, max_age_days: 90 },
    },
    fit: {
      status: "ok",
      n: 4,
      a: 10,
      b: 2,
      var_a: 1,
      var_b: 1,
      cov_ab: 0,
      chi2_reduced: 1,
      xmin: 0,
      xmax: 100,
    },
    gate: "ok",
    rows: [
      {
        hour: 0,
        signal_mv: 14,
        reference: 2,
        estimate: 2,
        u: 1,
        error: 0,
        z: 0,
        status: "estimated",
      },
    ],
    calibration_rows: [
      { index: 0, x: 0, y_mv: 10, u_mv: 1, status: "usable", predicted_mv: 10, residual_mv: 0 },
    ],
    check_rows: [{ index: 0, x: 1, status: "within-check", z: 0 }],
    summary: {
      samples: 1,
      estimated: 1,
      withheld: 0,
      reference_mismatches: 0,
      missing: 0,
      saturated: 0,
      calibration_used: 4,
      calibration_excluded: 0,
      checks_used: 2,
      evaluated_references: 1,
      rmse: 0,
      mean_error: 0,
    },
    verification: { native_reference_verified: true },
  };
}
test("valid evidence", () => expect(parseRun(fixture()).fit.b).toBe(2));
test.each([null, {}, [], "unsafe"])("invalid envelope %s", (v) =>
  expect(() => parseRun(v)).toThrow(),
);
test.each(["a", "b", "var_a", "var_b", "cov_ab", "chi2_reduced", "xmin", "xmax"] as const)(
  "nonfinite fit %s",
  (key) => {
    const r = fixture();
    r.fit[key] = NaN;
    expect(() => parseRun(r)).toThrow();
  },
);
test.each(["signal_mv", "reference", "estimate", "u", "error", "z"] as const)(
  "nonfinite sample %s",
  (key) => {
    const r = fixture();
    r.rows[0]![key] = Infinity;
    expect(() => parseRun(r)).toThrow();
  },
);
test.each([
  "verification",
  "settings",
  "status",
  "summary",
  "counter",
  "slope",
  "uncertainty",
  "calibration",
  "checks",
])("fails closed %s", (kind) => {
  const r = fixture();
  if (kind === "verification") r.verification.native_reference_verified = false;
  if (kind === "settings") r.settings.sigma = 99;
  if (kind === "status") r.rows[0]!.status = "unknown";
  if (kind === "summary") r.summary.samples = 2;
  if (kind === "counter") r.summary.withheld = 3;
  if (kind === "slope") r.fit.b = 0;
  if (kind === "uncertainty") r.rows[0]!.u = -1;
  if (kind === "calibration") r.calibration_rows = [];
  if (kind === "checks") r.check_rows = [];
  expect(() => parseRun(r)).toThrow();
});
test("absent values are not zero", () => {
  expect(number(null)).toBe("Unavailable");
  expect(number(undefined)).toBe("Unavailable");
  expect(number(0)).toBe("0");
  expect(number(1.23456)).toBe("1.235");
  expect(label("reference-mismatch")).toBe("reference mismatch");
});
