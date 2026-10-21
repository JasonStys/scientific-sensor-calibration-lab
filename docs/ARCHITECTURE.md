# Architecture and decisions

Jason Stys · bounded offline educational instrument calibration.

```text
Preset Settings / explicit CLI JSON → strict input validation
                                          ↓ usable calibration only
                C# centered weighted fit ↔ Python Fraction normal equations
                                          ↓ every-field agreement
                  separate checks → global quality/age gate
                                          ↓
                    inverse correction + standard uncertainty
                         ↙                ↓               ↘
                    TypeScript UI     inert exports    opt-in SQLite
```

## ADR 1: Typed C# kernel with separate Python reference

C# provides a small strongly typed bounded numeric worker and checked integer input handling. It has no NuGet dependencies, plugins, file/device/network access or shell commands. JSON comes from stdin and finite fit/status JSON goes to stdout; native error messages are generic. Source uses pinned stable .NET10 SDK, not a preview installed on the PC. The native kernel calculates known-variance coefficients/covariance and reduced chi-square; analytical self-tests and Python differential tests execute the real worker.

Python standard library provides strict schemas, independent exact arithmetic, uncertainty propagation, evidence/reporting and SQL. It calls only the fixed reviewed executable/DLL with `shell=False`,10s deadline,≤64KiB request and≤4096byte accepted output; failures emit no verified report. Source requires a compiled DLL; frozen bundles include a self-contained worker/runtime. The reference uses raw exact normal equations instead of centered doubles. No production fit helpers are reused. Both still share model assumptions, so independent algorithms cannot establish physical truth.

Fitting is O(n) arithmetic operations and O(n) point storage; report processing is O(n+m+k) for calibration/check/sample records. Fraction arithmetic has nonconstant arbitrary-precision cost. No hot path contains unbounded pairwise search or implicit network I/O. Launching one native process per run adds latency but isolates a tiny contract; a persistent worker would need framing, lifecycle and resource review. Current bounds make the simple process boundary acceptable.

## ADR 2: Browser UI without accounts or cloud collection

TypeScript validates display dependencies and uses text nodes for supplied strings. HTML/CSS and real Canvas plots support responsive keyboard use. A request-generation guard rejects stale results; any form change or request/shape failure hides evidence/downloads. Exports regenerate from accepted settings, not partially edited controls. Custom file input stays CLI-only. No external fonts, scripts, analytics, upload, remote model or accounts are present.

## ADR 3: Read-only local service and explicit history

HTTP binds only127.0.0.1, checks exact Host/Origin/fetch-site metadata, confines built assets after symlink resolution, bounds routes/queries and rejects mutation. This standard-library threaded service is not an Internet-hardened multiuser server or DoS sandbox. The local user/other local processes may read synthetic results. SQLite writes happen only through explicit CLI: parameter binding, identity verification, immutable update/delete triggers,100-record cap and no automatic pruning. It is unencrypted and OS-file access is not prevented by SQL triggers.

## ADR 4: Desktop portability and release evidence

Three runners publish their native .NET worker/runtime, run native analytical contracts, freeze Python/service/UI/resources, smoke the real app and ZIP only after success. Actual .NET notices are required and retained. The worker entry is treated as a binary to preserve Unix executable mode; adjacent runtime files are data. Archives contain the complete onedir application, not a signed installer or universal/mobile binary.

Validation and CodeQL must pass on the exact main commit before a draft release is built. C#, Python and JavaScript/TypeScript scans are separate; open findings are reviewed independently of successful uploads. Download/checksum/CRC/content/Windows-and-browser acceptance precedes public publication. No Actions artifact/cache uploads or automatic storage cleanup occurs. Real hosting, multiuser accounts, hardware connections and physical validation would be separate projects requiring new authority and engineering review.
