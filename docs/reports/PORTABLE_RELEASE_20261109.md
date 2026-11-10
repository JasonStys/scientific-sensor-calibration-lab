# Portable 1.1 release validation — 2026-11-09

Author: Jason Stys. This report describes observed local validation and the source contract
for the next portable release. It does not claim hosted results before those workflows run.

## Purpose and implementation

The published 1.0 portable artifacts predate the latest practical workflow. Version 1.1 makes
product identity consistent across Python, npm/lock metadata, the running service and UI.
`RELEASE.json` binds a bundle to its declared source, version, platform and clean/dirty state.
Older published releases and users' histories are preserved.

Packaging now checks the actual **freshly extracted** application from a new temporary working
directory. The earlier pre-archive-only smoke did not prove that extraction retained native
links or execute bits. Windows uses ZIP; Linux/macOS use tar.gz. Bounded archive tests reject
traversal, aliases, duplicate members, escaping links, wrong types and excessive content.

The stdlib release guard checks coherent versions, exact clean workflow source, current main,
complete successful required runs and a fresh draft/tag. Upload checks that unchanged draft's
source/version, embedded metadata, actual digest and absent same-name assets. It cannot replace
published assets. These guards remain active with Python optimization. Privileged release
jobs still have job-level contents-write permission; the GH token is supplied only to explicit
transport steps. No application startup calls GitHub or transmits user data.

## Actual new-feature acceptance

Actual bundled C# fit/runtime, independent reference agreement, variance-sum/fraction arithmetic, missing-value null budgets and expired-calibration withholding. Real UI controls and exported rows are exercised. Preserved checks retain runtime notices, all formats, SQL and exact input replay.

The compiled child must announce its owned ephemeral loopback URL and echo the random smoke
marker, runtime version and exact embedded metadata. Probes refuse redirects/proxies, enforce
bounded HTTP reads and fetch real built JavaScript/CSS. An owned Chromium context uses the
compiled service, blocks outside-origin resources, rejects browser errors and exercises the
new feature. Original domain-native checks remain in `tools/legacy_smoke.py` under guards
that are active with `python -O`; they were not discarded when the new browser journey was added.

## Observed local results

Windows/Python 3.14.6 and Node 24.18.1, using each repository's isolated locked environment:

| Gate                                                                     | Observed result                                       |
| ------------------------------------------------------------------------ | ----------------------------------------------------- |
| Complete Python/model/native/HTTP suite                                  | 374 passed; 96.91% combined statement/branch coverage |
| Focused release/archive/frozen-identity/draft lookup cases               | 89 passed and 28 subtests; included above             |
| Existing TypeScript unit suite                                           | 29 passed                                             |
| Strict TypeScript/Vite production build                                  | Passed                                                |
| Ruff lint/format and strict domain mypy                                  | Passed                                                |
| Fresh frozen Windows archive extraction + actual CLI/API/Chromium/export | Passed                                                |
| Original native notices/resource/persistence checks                      | Passed                                                |
| Independent ZIP CRC, sidecar, app executable and metadata inspection     | Passed                                                |

Observed local dirty-build archive (not a published or exact-clean CI artifact):

- File: `scientific-sensor-calibration-lab-v1.1.0-windows-amd64.zip`
- Bytes: 48395639; members: 280
- SHA-256: `2cf658109a77576afb0bfb0b244ba71832ee614ef3fc3c9798579c514762c29e`
- Embedded source: `86a8d89c2e4b48f0208dbd1270e0ac444a644a5c` with `source_dirty:true`.

The dirty flag is intentional for local pre-commit acceptance. A release requires a fresh
clean CI build at its accepted commit; this local checksum must not be presented as that
future release's checksum. No Linux/macOS native execution is claimed from this Windows run.
Their required hosted native jobs separately rebuild, extract and exercise each platform.

## Failures investigated and corrected

Restricted-shell HTTP tests failed with WinError10013 before reaching disposable listeners.
The unchanged suites passed in normal-user loopback scope; no warning or coverage gate was
weakened. Other projects in the same validation batch also required explicit pinned Rust-toolchain lookup. This sensor application uses its C# fit kernel; that Rust correction is not a sensor runtime feature.

New acceptance initially retained Flight-specific nominal/reset/240-tick checks from the
shared pilot, which are not APIs of this application. Those were replaced by this domain's
new-feature oracle and its preserved original smoke. The authored HTML title, not the release
display title, identifies compiled HTML. The Sensor button lookup used the existing
accessible names including their arrow decoration. Failures were not accepted as passes;
corrected checks ran against fresh extracted artifacts. Private failed evidence remains
outside the repository. No application numerical algorithm was changed to satisfy the harness.

Chromium dependency installation has a 15-minute setup budget inside a 25-minute native job,
based on observed hosted setup duration. Actual CLI 30-second, HTTP 8-second, browser 45-second
and complete extracted-smoke 120-second hard deadlines remain bounded, without test retries.

## Draft lookup correction and independent verification

In the shared release transport, the first Earth Observation 1.1 release attempt passed its macOS extracted native/browser
journey, then failed during upload because GitHub's release-by-tag REST endpoint returns
**published** releases. An untagged draft existed in the authenticated release list and
could be read by numeric ID, while that tag endpoint returned 404. This was a release-tooling
API error; the native application checks were not bypassed or changed to accept it.

Preparation and upload now use a complete authenticated listing capped at three pages of
100 releases, require a unique exact tag, and reread the immutable numeric ID. Full-page
exhaustion, malformed metadata, duplicate IDs/tags, identity changes, foreign API/upload
URLs and transport/authentication failures stop the operation. An existing public release
or draft blocks version creation even when no Git tag exists. Upload still requires the
same source, an unpublished non-prerelease draft, exact archive metadata/digest and absent
asset names. No overwrite, retry or permissive 404 fallback was introduced.

Nineteen independent real-shape API cases exercise untagged draft lookup, complete absence,
existing published versions, later pages, bounded-history exhaustion, identity swaps and
failures. Integrated prepare/upload fixtures use those real list/detail shapes and reject
the published-only tag endpoint. These tests are included in the observed suite above.
The changed lookup is release transport code, not bundled application behavior; existing
actual extracted-native evidence remains applicable. Clean-source three-platform CI is
still required before publication.

Sources: [GitHub REST release-by-tag](https://docs.github.com/en/rest/releases/releases#get-a-release-by-tag-name),
[authenticated release listing](https://docs.github.com/en/rest/releases/releases#list-releases),
[GitHub CLI draft lookup implementation](https://github.com/cli/cli/blob/trunk/pkg/cmd/release/shared/fetch.go).

## Scope and limitations

Modeled standard uncertainty excludes physical-reference uncertainty, unmodeled correlations and certification; the signed covariance cross term is already included.

These are unsigned/unnotarized desktop portable packages, not signed installers, public
hosting, native mobile installation or clean-machine installer certification. Local histories
are unencrypted files under the user's control. Hashes identify bytes, not authorship or truth.
No user store, real equipment, account or OS security setting was changed by validation.
