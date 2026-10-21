/** Calibration evidence guards by Jason Stys; types, fields and functions: docs/CODE_INDEX.md. */
export interface Row {
  hour: number;
  signal_mv: number | null;
  reference: number | null;
  estimate: number | null;
  u: number | null;
  error: number | null;
  z: number | null;
  status: string;
}
export interface Run {
  id: string;
  name: string;
  settings: { scenario: string; sigma: number; limit: number; age: number };
  input: {
    unit: string;
    provenance: string;
    config: { z_limit: number; age_days: number; max_age_days: number };
  };
  fit: {
    status: string;
    n: number;
    a: number | null;
    b: number | null;
    var_a: number | null;
    var_b: number | null;
    cov_ab: number | null;
    chi2_reduced: number | null;
    xmin: number | null;
    xmax: number | null;
  };
  gate: string;
  rows: Row[];
  calibration_rows: {
    index: number;
    x: number;
    y_mv: number | null;
    u_mv: number;
    status: string;
    predicted_mv: number | null;
    residual_mv: number | null;
  }[];
  check_rows: { index: number; x: number; status: string; z: number | null }[];
  summary: Record<string, number | null>;
  verification: { native_reference_verified: boolean };
}
export const statuses = [
  "estimated",
  "reference-mismatch",
  "missing",
  "saturated",
  "outside-calibration-span",
  "fit-inconsistent",
  "check-validation-failed",
  "calibration-expired",
  "insufficient-calibration",
  "insufficient-span",
  "noninvertible-fit",
];
/** Missing and nonfinite are not interchangeable; reject unsafe magnitudes before plotting. */
function finite(value: unknown): boolean {
  return typeof value === "number" && Number.isFinite(value) && Math.abs(value) <= 1e15;
}
/** Validate display dependencies; numerical certification still belongs to the independent backend checks. */
export function parseRun(value: unknown): Run {
  const r = value as Run | null;
  if (
    !r ||
    typeof r !== "object" ||
    !/^[a-f0-9]{64}$/.test(r.id ?? "") ||
    !/^[a-z0-9][a-z0-9-]{0,47}$/.test(r.name ?? "") ||
    r.verification?.native_reference_verified !== true ||
    !r.input ||
    !/^[A-Za-z][A-Za-z0-9_-]{0,15}$/.test(r.input.unit ?? "") ||
    typeof r.input.provenance !== "string" ||
    r.input.provenance.length > 240 ||
    !r.input.config ||
    !finite(r.input.config.z_limit)
  )
    throw new Error("Invalid verified identity");
  if (
    !r.settings ||
    ![1, 2, 4].includes(r.settings.sigma) ||
    ![2, 3, 4].includes(r.settings.limit) ||
    ![0, 60, 120].includes(r.settings.age) ||
    typeof r.settings.scenario !== "string" ||
    !r.fit ||
    !Number.isInteger(r.fit.n) ||
    r.fit.n < 0 ||
    r.fit.n > 64 ||
    (!statuses.includes(r.gate) && r.gate !== "ok")
  )
    throw new Error("Invalid input/fit envelope");
  for (const key of ["a", "b", "var_a", "var_b", "cov_ab", "chi2_reduced", "xmin", "xmax"] as const)
    if (r.fit[key] !== null && !finite(r.fit[key])) throw new Error("Invalid fit value");
  if (
    r.fit.status === "ok" &&
    (r.fit.a === null ||
      r.fit.b === null ||
      r.fit.var_a === null ||
      r.fit.var_b === null ||
      r.fit.cov_ab === null ||
      r.fit.chi2_reduced === null ||
      r.fit.xmin === null ||
      r.fit.xmax === null ||
      Math.abs(r.fit.b) < 0.00999999 ||
      r.fit.var_a < 0 ||
      r.fit.var_b < 0 ||
      r.fit.xmax <= r.fit.xmin)
  )
    throw new Error("Invalid available fit");
  if (
    !Array.isArray(r.rows) ||
    r.rows.length < 1 ||
    r.rows.length > 168 ||
    r.rows.some(
      (row, i) =>
        !row ||
        row.hour !== i ||
        !statuses.includes(row.status) ||
        [row.signal_mv, row.reference, row.estimate, row.u, row.error, row.z].some(
          (x) => x !== null && !finite(x),
        ) ||
        (row.u !== null && row.u <= 0) ||
        (row.estimate === null) !== (row.u === null) ||
        (row.error === null) !== (row.z === null),
    )
  )
    throw new Error("Invalid sample trace");
  if (
    !Array.isArray(r.calibration_rows) ||
    r.calibration_rows.length < 1 ||
    r.calibration_rows.length > 64 ||
    r.calibration_rows.some(
      (row) =>
        !row ||
        !finite(row.x) ||
        !finite(row.u_mv) ||
        row.u_mv <= 0 ||
        [row.y_mv, row.predicted_mv, row.residual_mv].some((x) => x !== null && !finite(x)),
    )
  )
    throw new Error("Invalid calibration trace");
  if (
    !Array.isArray(r.check_rows) ||
    r.check_rows.length < 1 ||
    r.check_rows.length > 64 ||
    r.check_rows.some((row) => !row || !finite(row.x) || (row.z !== null && !finite(row.z)))
  )
    throw new Error("Invalid check trace");
  const keys = [
    "samples",
    "estimated",
    "withheld",
    "reference_mismatches",
    "missing",
    "saturated",
    "calibration_used",
    "calibration_excluded",
    "checks_used",
    "evaluated_references",
    "rmse",
    "mean_error",
  ];
  if (
    !r.summary ||
    keys.some(
      (key) =>
        r.summary[key] === undefined ||
        (r.summary[key] === null && !["rmse", "mean_error"].includes(key)) ||
        (r.summary[key] !== null && !finite(r.summary[key])),
    ) ||
    r.summary.samples !== r.rows.length ||
    r.summary.estimated! + r.summary.withheld! !== r.rows.length
  )
    throw new Error("Invalid summary");
  return r;
}
/** Display unavailable values explicitly instead of coercing null to zero. */
export function number(value: number | null | undefined, digits = 3): string {
  return value === null || value === undefined
    ? "Unavailable"
    : value.toLocaleString("en-US", { maximumFractionDigits: digits });
}
/** Convert stable machine status to readable text without treating it as trusted markup. */
export function label(value: string): string {
  return value.replaceAll("-", " ");
}
