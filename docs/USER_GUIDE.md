# User guide and troubleshooting

Launch the extracted portable app or `python -m sensorlab serve` after source setup. It prints/opens an ephemeral local URL. Keep the console open; Ctrl+C stops the service. For a fixed port use `serve --port 8966 --no-browser` then open the exact printed `http://127.0.0.1:PORT/` address. No sign-in or Internet service is needed at runtime. No instrument is connected or controlled.

Start with Stable linear instrument. The fit panel shows response-versus-reference observations, the fitted line and separate checks. The second chart shows corrected estimates with±1 combined standard uncertainty and separate evaluation references; missing/withheld estimates break the line. The sample slider exposes signal, estimate, uncertainty, status and reference error without converting null to zero. Green verification means internal C#/reference agreement, not physical certification. A global gate label “Within checks” can coexist with individual reference mismatches that need human review.

Try these cases:

- **Changing offset:** select hour18 and inspect a reference mismatch. The invented case adds offset, but the algorithm only identifies disagreement; it does not prove a cause.
- **Missing readings:** hours4/5 have no response/estimate; two calibration records are excluded. Nothing is zero-filled.
- **Clipping/range:** hours8/10 hit the electronics rails; hour18 is inside electronics limits but outside calibrated span. These are different reasons to withhold a value.
- **Unsupported nonlinearity:** global fit-inconsistent gate prevents corrected estimates, even though a line can still be plotted diagnostically.
- **120-day age:** expired calibration withholds estimates and RMSE is unavailable, not zero.
- **Declared uncertainty multiplier:** changes supplied uncertainty, not the observations. Larger uncertainty can reduce standardized disagreement; that is an assumption change, not improved instrument performance. Thresholds/age rules are fictional configuration, not standards.

Change controls then click **Analyze calibration**. Prior evidence is hidden immediately to prevent stale results; downloads always use the accepted run's settings. Export JSON(full evidence), CSV(samples/statuses), HTML(inert full evidence) or INPUT(strict replayable config/data). CSV unavailable values are empty cells, not numeric zeros. Inspect denominator counts when comparing RMSE because rejected/unknown-reference rows are excluded from error metrics.

```text
python -m sensorlab export --format input --output editable.json
# Edit synthetic records with a text editor, retaining exact schema and fixed units.
python -m sensorlab export --input editable.json --output evidence.json --history history.sqlite3
python -m sensorlab export --input editable.json --format html --output evidence.html
```

Outputs are create-only. Histories are explicit local unencrypted SQLite, idempotent by verified content identity, immutable through this application, capped at100 unique reports and never automatically pruned. Choose a new file at capacity. Do not upload sensitive real instrument information to public issues or commit histories/data files.

Troubleshooting: missing native worker → build `calibration-core` in Release with pinned stable SDK; missing built UI →`npm ci` then`npm run build`; forbidden origin → use exact127.0.0.1 URL, no proxy/iframe; input rejected → fresh INPUT template and UTF-8≤64KiB with integer fixed units; cannot overwrite output → choose new path; portable app moved alone → extract/retain complete folder including `_internal` and native runtime. Unsigned OS warning → verify source/checksum and follow OS policy, never disable protection. A responsive website is not a native mobile installer; release binaries are desktop/architecture-specific.

[User help/issues](https://github.com/JasonStys/scientific-sensor-calibration-lab/issues) · [Jason Stys](https://github.com/JasonStys). Real instrument calibration requires appropriate physical standards, procedures, uncertainty budgets and qualified metrology review; this software does not provide those.
