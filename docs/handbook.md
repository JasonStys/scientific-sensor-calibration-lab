# Scientific Sensor Calibration Lab · DATUM handbook

By Jason Stys.

Review per-estimate variance budgets, missing samples and expired-calibration withholding in the 1.1 portable calibration workflow.

Review per-estimate variance budgets, missing samples and expired-calibration withholding in the 1.1 portable calibration workflow.

Bundles the native fit/runtime with a practical uncertainty review and export path, tested against actual compiled execution and independent arithmetic after extraction.

## Read the documentation

| Edition                                                      | Audience and contents                                                                                              |
| ------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------ |
| [project-guide.docx](reports/project-guide.docx)             | User and developer guide: purpose, current usage, design, boundaries and source references.                        |
| [validation-review.docx](reports/validation-review.docx)     | Reviewer edition: exact tested baseline, observed workflows, dated local results and remaining limits.             |
| [validation-evidence.xlsx](reports/validation-evidence.xlsx) | Two filterable Excel Tables for observed workflows and test-source inventory, with recalculating outcome formulas. |

The editable Markdown remains the maintenance source. The Word files are readable editions. The workbook is an evidence index rather than a test runner. See [publication identities and review](reports/publications.json) and the [documentation refresh record](reports/documentation-refresh-2026-11-09.md).

## Current usage and help

[README quick start](../README.md) is the entry point. Use the project-specific guides below before changing inputs, operating modes or deployment assumptions.

### Usage and operations

- [RELEASE](RELEASE.md)
- [USER GUIDE](USER_GUIDE.md)

### Design and contracts

- [API](API.md)
- [ARCHITECTURE](ARCHITECTURE.md)
- [MODEL](MODEL.md)

### Security and validation

- [VALIDATION](VALIDATION.md)

## Historical results and reproduction

The reviewed source is [`1bdb2244451af67d90600e60c566435b66ea2bd0`](https://github.com/JasonStys/scientific-sensor-calibration-lab/tree/1bdb2244451af67d90600e60c566435b66ea2bd0). The observed functional workflow baseline is `1bdb2244451af67d90600e60c566435b66ea2bd0`; those observations are recorded at `2026-11-10T05:25:40.628667+00:00`. They do not certify an unrun later revision.

- [Detailed recorded validation](reports/PORTABLE_RELEASE_20261109.md)
- [Current Actions](https://github.com/JasonStys/scientific-sensor-calibration-lab/actions) records later integration checks separately.
- Preserve dated measurements and follow the existing testing guide to reproduce them; a test-source inventory alone does not establish execution.

## Practical boundaries

- Modeled standard uncertainty excludes physical reference uncertainty, unmodeled correlations and certification.
- The signed covariance cross term is already inside fit variance; withheld estimates have no invented uncertainty budget.
- Synthetic local instrument examples and unsigned desktop portable packages; no system installer, real instrument connection or certified measurement service.

## Maintaining these editions

Update the editable usage/design/test documents first. Rebuild and visually review every Word page and workbook tab before replacing an edition; verify the exact binary digests and evidence source in publications.json. Keep account data, logs with secrets, installed-app state and private test stores out of documentation. Source and release assets retain their existing security and licensing boundaries.
