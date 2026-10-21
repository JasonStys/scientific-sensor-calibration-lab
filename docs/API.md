# Local API and strict input

Read-only IPv4 loopback GET routes: `/api/health`, `/api/catalog`, `/api/run`, `/api/report`. Exact Host`127.0.0.1:PORT`, absent/same Origin and non-cross-site fetch metadata are required. No CORS. POST/PUT/PATCH/DELETE/OPTIONS/HEAD return405. Static routes are `/`, `/index.html`, exact built `/assets/NAME` with allowed suffixes, confined after symlink resolution; no source/dotfile/arbitrary-file routes.

Run defaults: `scenario=linear-clean&sigma=1&limit=3&age=0`. Six scenario IDs are in catalog, sigma1/2/4, limit2/3/4, age0/60/120. Duplicate/unknown fields or unsupported numbers reject400; maximum8 query fields and1024 request-target characters. Report adds `format=json|csv|html|input`, returning a fixed attachment name. `format` is invalid on run. Forbidden origin403, target too long414, unknown route404 and verification/resource failure500 return generic messages without tracebacks or partial evidence. All responses set CSP, nosniff, no-framing, no-referrer and no-store headers. No mutation or data-upload route exists.

## CLI exact JSON

Root exact keys: schema(integer1), name(lowercase alphanumeric/hyphen1..48, starts alphanumeric), provenance(text1..240), unit(label1..16 beginning letter, remaining alphanumeric/underscore/hyphen), config, calibration, checks, samples. No extra keys, duplicates, type coercion or scripts. UTF-8 only,≤65536bytes, malformed JSON/depth/encoding rejected. Input unit labels do not perform conversion.

Config exact integer fields/bounds:

| Field                     | Bounds / meaning                                                        |
| ------------------------- | ----------------------------------------------------------------------- |
| rail_low_uv, rail_high_uv | −10000000..10000000; low strictly below high; equality counts saturated |
| age_days                  | 0..3650 explicit age                                                    |
| max_age_days              | 1..3650 inclusive allowed age                                           |
| z_limit                   | 2..5 standardized review threshold                                      |
| chi_limit                 | 1..25 reduced chi-square review threshold                               |

Calibration and checks are each1..64 exact records `{x_milli,signal_uv,u_uv}`. Reference x: integer−1000000..1000000; signal: integer−10000000..10000000 or null; standard response uncertainty: integer1..100000. Samples are1..168 exact records `{signal_uv,u_uv,reference_milli}` with the same bounds, but reference may also be null. Booleans are never accepted as integers. Empty/insufficient usable fit data yields an explicit model-unavailable result, not an invented estimate.

See `examples/instrument.json` for a complete editable file. Fit/check records should be separate observations: no mathematical validation can certify independence of user-supplied experiments.

## Evidence contract

Report contains schema, author, name, GUI settings(or null for CLI custom data), complete input, fit, global gate, calibration/check/sample rows, summary, method/limitations, verification tolerances and content SHA-256. All output responses use mV; estimates/u/errors use the supplied reference unit. `u` is combined standard uncertainty, not an interval endpoint or probability. Unavailable numerical values are JSON null and empty CSV cells. Sample CSV includes every monitoring row/status; full calibration/check evidence is in JSON/HTML, not silently omitted from their respective full reports. Input download is strict replay JSON, not a report masquerading as input. HTML is escaped script-free content.

C# internal worker accepts only `{points:[{x_milli,signal_uv,u_uv},...]}` with0..64 non-null bounded points. Python filters missing/rail-saturated calibration records first. Worker enforces exact duplicate-free keys, primitive integer bounds, strict UTF-8, depth8 and64KiB. It returns only fit/status/count/covariance fields; Python checks the shape/status and all numerical values against the independent reference. It cannot read user paths or execute supplied commands. Custom file uploads do not reach it through HTTP.
