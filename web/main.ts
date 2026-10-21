/** DATUM calibration workbench by Jason Stys. State, functions, fields and DOM: docs/CODE_INDEX.md. */
import "./style.css";
import { label, number, parseRun, type Run } from "./contracts";

document.querySelector<HTMLDivElement>("#app")!.innerHTML = /* HTML */ ` <a
    class="skip"
    href="#workspace"
    >Skip to calibration experiment</a
  >
  <header>
    <a class="brand" href="#workspace"
      ><span class="brand-mark">⊹</span>DATUM <small>SCIENTIFIC SENSOR CALIBRATION LAB</small></a
    >
    <nav aria-label="Project">
      <a href="#method">Method & limits</a
      ><a href="https://github.com/JasonStys/scientific-sensor-calibration-lab">Source ↗</a
      ><a href="https://github.com/JasonStys">Jason Stys ↗</a>
    </nav>
  </header>
  <main id="workspace">
    <section class="intro">
      <div>
        <p class="eyebrow">INSTRUMENT NOTEBOOK / SYNTHETIC LABORATORY</p>
        <h1>A reading is a number.<br /><em>A measurement needs context.</em></h1>
        <p class="lede">
          Fit the response. Carry its uncertainty. Keep missing data, drift and the limits of your
          calibration in view.
        </p>
      </div>
      <aside>
        <span class="pill">OFFLINE · NO INSTRUMENT CONTROL</span>
        <p>
          C# weighted fit.<br />Independent rational reference.<br />Traceable assumptions, not a
          certificate.
        </p>
      </aside>
    </section>
    <form id="controls" aria-label="Calibration controls">
      <label
        >Scenario<select id="scenario">
          <option value="linear-clean">Stable linear instrument</option>
          <option value="unequal-noise">Unequal uncertainty</option>
          <option value="sensor-drift">Changing sensor offset</option>
          <option value="saturation">Clipping / range checks</option>
          <option value="missing-data">Missing readings</option>
          <option value="nonlinear-response">Unsupported nonlinearity</option>
        </select></label
      ><label
        >Declared uncertainty<select id="sigma">
          <option value="1">1× supplied standard u</option>
          <option value="2">2× supplied standard u</option>
          <option value="4">4× supplied standard u</option>
        </select></label
      ><label
        >Review threshold<select id="limit">
          <option value="3">3 standard u</option>
          <option value="2">2 standard u</option>
          <option value="4">4 standard u</option>
        </select></label
      ><label
        >Calibration age<select id="age">
          <option value="0">0 days</option>
          <option value="60">60 days</option>
          <option value="120">120 days / expired</option>
        </select></label
      ><button id="run" type="submit">Analyze calibration ↗</button>
    </form>
    <p id="status" role="status" aria-live="polite">
      Checking C# fit against the rational reference…
    </p>
    <div id="evidence" hidden>
      <div class="metrics">
        <div>
          <span>CALIBRATION GATE</span><strong id="gate"></strong
          ><small>model checks / not certification</small>
        </div>
        <div>
          <span>ESTIMATES AVAILABLE</span><strong id="available"></strong
          ><small>withheld samples remain visible</small>
        </div>
        <div>
          <span>REFERENCE MISMATCHES</span><strong id="mismatches"></strong
          ><small>review flags / not a causal diagnosis</small>
        </div>
        <div>
          <span>REFERENCE ERROR / RMSE</span><strong id="rmse"></strong
          ><small id="denominator"></small>
        </div>
      </div>
      <section class="panel">
        <div class="section-head">
          <div>
            <p class="eyebrow">01 / KNOW THE TRANSFER FUNCTION</p>
            <h2>Calibrate the response.<br />Validate on separate checks.</h2>
          </div>
          <p id="equation" class="inspection"></p>
        </div>
        <canvas
          id="fit-chart"
          width="1000"
          height="320"
          role="img"
          aria-label="Calibration response versus reference value: measured training points and fitted mean line; held-out checks are in the table and exact rows in JSON"
        ></canvas>
        <div class="legend">
          <span><i class="line"></i>C# fitted mean</span
          ><span><i class="alternate"></i>Calibration readings</span
          ><span>Reference / degC → response / mV · all data synthetic</span>
        </div>
        <p id="fit-detail" class="notice"></p>
        <div
          class="table-wrap"
          tabindex="0"
          role="region"
          aria-label="Scrollable held-out calibration checks"
        >
          <table>
            <caption>
              Separate check records, never used to fit coefficients. Standardized residuals use
              supplied response uncertainty plus mean-fit covariance.
            </caption>
            <thead>
              <tr>
                <th>Check</th>
                <th>Reference</th>
                <th>Standardized residual</th>
                <th>Review</th>
              </tr>
            </thead>
            <tbody id="checks"></tbody>
          </table>
        </div>
      </section>
      <section class="panel">
        <div class="section-head">
          <div>
            <p class="eyebrow">02 / KEEP UNCERTAINTY WITH THE VALUE</p>
            <h2>Correction is an estimate.<br />Absence is not zero.</h2>
          </div>
          <p class="muted">
            One supplied sample per synthetic hour.<br />Missing and withheld estimates break the
            line.
          </p>
        </div>
        <canvas
          id="sample-chart"
          width="1000"
          height="280"
          role="img"
          aria-label="Corrected sample estimates with plus or minus one combined standard uncertainty and separate supplied reference values; missing estimates are gaps"
        ></canvas>
        <div class="legend">
          <span><i class="line"></i>Estimate ±1 standard u</span
          ><span><i class="alternate"></i>Supplied evaluation reference</span
          ><span>No reference means no invented error score</span>
        </div>
        <label class="scrub"
          >Inspect sample hour <output id="hour-label">0</output
          ><input id="hour" type="range" min="0" max="23" value="0"
        /></label>
        <p id="sample-status" class="notice"></p>
        <div class="flow">
          <div class="node">
            <span>MEASURED RESPONSE</span><strong id="signal"></strong
            ><small>mV / missing is unavailable</small>
          </div>
          <div class="node bus">
            <span>CORRECTED ESTIMATE</span><strong id="estimate"></strong
            ><small id="estimate-unit"></small>
          </div>
          <div class="node">
            <span>COMBINED STANDARD u</span><strong id="uncertainty"></strong
            ><small>first-order / not a coverage guarantee</small>
          </div>
        </div>
        <p id="sample-detail" class="inspection"></p>
      </section>
      <section class="export">
        <div>
          <p class="eyebrow">03 / REPLAYABLE EVIDENCE</p>
          <h2>Take the assumptions<br />with the result.</h2>
          <p>
            Fit coefficients and covariance, excluded observations, separate checks, sample flags
            and full input. SQLite history is explicit through the CLI, never a hidden browser
            write.
          </p>
          <div id="downloads" class="downloads"></div>
        </div>
        <div>
          <span class="eyebrow">REPORT SHA-256</span><code id="identity"></code>
          <p id="verification" class="muted"></p>
          <p id="provenance" class="muted"></p>
        </div>
      </section>
    </div>
    <section id="method" class="method">
      <p class="eyebrow">METHOD / INTERNAL VERIFICATION IS NOT PHYSICAL TRACEABILITY</p>
      <h2>A fit is conditional.<br /><em>Make the conditions visible.</em></h2>
      <div class="method-grid">
        <article>
          <h3>01 · Know the assumptions</h3>
          <p>
            Linear response, independent known response standard uncertainties and error-free
            reference values. Fit covariance is not rescaled to hide large residuals. Reference
            uncertainty and correlated errors are not modeled.
          </p>
        </article>
        <article>
          <h3>02 · Withhold unsupported values</h3>
          <p>
            Missing or saturated signals, inadequate span, near-zero slopes, inconsistent fits,
            failed checks, expired calibration and extrapolation are explicit. A mismatch against a
            supplied reference is not proof of a specific failure cause.
          </p>
        </article>
        <article>
          <h3>03 · Verify, then interpret</h3>
          <p>
            C# centered weighted moments must agree with independently implemented exact-rational
            Python equations. Uncertainty is a first-order combined standard value—not a certified
            interval, laboratory accreditation or safety determination.
          </p>
        </article>
      </div>
      <p>
        <a
          href="https://github.com/JasonStys/scientific-sensor-calibration-lab/blob/main/docs/USER_GUIDE.md"
          >User guide ↗</a
        >
        ·
        <a href="https://github.com/JasonStys/scientific-sensor-calibration-lab/issues"
          >Help / report an issue ↗</a
        >
      </p>
    </section>
  </main>
  <footer>
    <span>Designed and engineered by <a href="https://github.com/JasonStys">Jason Stys</a></span
    ><span>SYNTHETIC SCIENTIFIC EDUCATION · NO ENDORSEMENT</span>
  </footer>`;
/** Resolve only owned fixed-template identifiers; report text is never interpreted as HTML. */
function element<T extends HTMLElement>(id: string): T {
  return document.getElementById(id) as T;
}
let current: Run | null = null,
  generation = 0;
const evidence = element("evidence"),
  status = element("status"),
  button = element<HTMLButtonElement>("run"),
  form = element<HTMLFormElement>("controls");
/** Build finite query values; accepted report settings, not mutable form state, later drive downloads. */
function query() {
  return new URLSearchParams(
    ["scenario", "sigma", "limit", "age"].map((k) => [k, element<HTMLSelectElement>(k).value]),
  );
}
/** Draw real calibration rows and fitted mean response on labeled data-derived axes. */
function drawFit() {
  if (!current) return;
  const r = current,
    ctx = element<HTMLCanvasElement>("fit-chart").getContext("2d")!,
    points = r.calibration_rows;
  const xmin = Math.min(...points.map((p) => p.x)),
    xmax = Math.max(xmin + 1, ...points.map((p) => p.x)),
    ys = points.flatMap((p) => [p.y_mv, p.predicted_mv]).filter((v): v is number => v !== null),
    ymin = Math.min(0, ...ys),
    ymax = Math.max(ymin + 1, ...ys) * 1.08;
  const x = (v: number) => 65 + ((v - xmin) / (xmax - xmin)) * 915,
    y = (v: number) => 275 - ((v - ymin) / (ymax - ymin)) * 245;
  ctx.clearRect(0, 0, 1000, 320);
  ctx.font = "13px monospace";
  ctx.lineWidth = 1;
  ctx.strokeStyle = "#c9c3ba";
  for (let i = 0; i <= 4; i++) {
    const val = ymin + ((ymax - ymin) * i) / 4;
    ctx.beginPath();
    ctx.moveTo(65, y(val));
    ctx.lineTo(980, y(val));
    ctx.stroke();
    ctx.fillStyle = "#514c49";
    ctx.fillText(number(val, 0), 2, y(val) - 3);
    const xv = xmin + ((xmax - xmin) * i) / 4;
    ctx.fillText(number(xv, 1), x(xv) - 10, 307);
  }
  if (r.fit.status === "ok") {
    ctx.strokeStyle = "#235a5b";
    ctx.lineWidth = 2.5;
    ctx.beginPath();
    ctx.moveTo(x(xmin), y(r.fit.a! + r.fit.b! * xmin));
    ctx.lineTo(x(xmax), y(r.fit.a! + r.fit.b! * xmax));
    ctx.stroke();
  }
  for (const p of points)
    if (p.y_mv !== null) {
      ctx.fillStyle = p.status === "usable" ? "#a6633a" : "#a83838";
      ctx.beginPath();
      ctx.arc(x(p.x), y(p.y_mv), 4.5, 0, Math.PI * 2);
      ctx.fill();
    }
}
/** Draw reference and accepted/diagnostic estimates; unavailable values never connect across gaps. */
function drawSamples() {
  if (!current) return;
  const rows = current.rows,
    ctx = element<HTMLCanvasElement>("sample-chart").getContext("2d")!,
    values = rows
      .flatMap((r) => [
        r.reference,
        r.estimate === null ? null : r.estimate + r.u!,
        r.estimate === null ? null : r.estimate - r.u!,
      ])
      .filter((x): x is number => x !== null),
    min = Math.min(0, ...values),
    max = Math.max(min + 1, ...values) * 1.05;
  const x = (h: number) => 65 + (h / Math.max(1, rows.length - 1)) * 915,
    y = (v: number) => 235 - ((v - min) / (max - min)) * 205;
  ctx.clearRect(0, 0, 1000, 280);
  ctx.font = "13px monospace";
  ctx.fillStyle = "#514c49";
  for (let i = 0; i <= 4; i++) {
    const h = ((rows.length - 1) * i) / 4;
    ctx.fillText(number(h, 0) + " h", Math.min(946, x(h) - 10), 267);
    ctx.fillText(number(min + ((max - min) * i) / 4, 0), 2, y(min + ((max - min) * i) / 4));
  }
  for (const key of ["reference", "estimate"] as const) {
    ctx.strokeStyle = key === "estimate" ? "#235a5b" : "#a6633a";
    ctx.lineWidth = 2;
    ctx.setLineDash(key === "reference" ? [5, 5] : []);
    ctx.beginPath();
    let connected = false;
    for (const r of rows) {
      const v = r[key];
      if (v === null) {
        connected = false;
        continue;
      }
      if (connected) ctx.lineTo(x(r.hour), y(v));
      else ctx.moveTo(x(r.hour), y(v));
      connected = true;
    }
    ctx.stroke();
  }
  ctx.setLineDash([]);
  for (const r of rows)
    if (r.estimate !== null) {
      ctx.strokeStyle = r.status === "reference-mismatch" ? "#a83838" : "#235a5b";
      ctx.beginPath();
      ctx.moveTo(x(r.hour), y(r.estimate - r.u!));
      ctx.lineTo(x(r.hour), y(r.estimate + r.u!));
      ctx.stroke();
      ctx.fillStyle = ctx.strokeStyle;
      ctx.beginPath();
      ctx.arc(x(r.hour), y(r.estimate), 3, 0, Math.PI * 2);
      ctx.fill();
    }
}
/** Inspect estimate, uncertainty and independently supplied reference without filling missing values. */
function inspect() {
  if (!current) return;
  const row = current.rows[Number(element<HTMLInputElement>("hour").value)]!;
  element("hour-label").textContent = String(row.hour);
  element("sample-status").textContent = label(row.status) + " · " + current.input.unit;
  element("signal").textContent = number(row.signal_mv);
  element("estimate").textContent = number(row.estimate);
  element("uncertainty").textContent = number(row.u);
  element("estimate-unit").textContent = current.input.unit;
  element("sample-detail").textContent =
    `Supplied reference: ${number(row.reference)} · estimate − reference: ${number(row.error)} · standardized error: ${number(row.z)}. A supplied reference is separate evaluation evidence, not an input to the inverse correction.`;
}
/** Render verified evidence via text nodes and fixed same-origin attachment links. */
function render(r: Run) {
  current = r;
  evidence.hidden = false;
  element("gate").textContent = r.gate === "ok" ? "Within checks" : label(r.gate);
  element("available").textContent = `${r.summary.estimated} / ${r.summary.samples}`;
  element("mismatches").textContent = String(r.summary.reference_mismatches);
  element("rmse").textContent = number(r.summary.rmse);
  element("denominator").textContent =
    `${r.input.unit} / ${r.summary.evaluated_references} evaluated references`;
  element("equation").textContent =
    r.fit.status === "ok"
      ? `response / mV = ${number(r.fit.a)} + ${number(r.fit.b)} × reference / ${r.input.unit}`
      : label(r.fit.status);
  element("fit-detail").textContent =
    `Calibration used ${r.summary.calibration_used}; excluded ${r.summary.calibration_excluded}. Reduced chi-square: ${number(r.fit.chi2_reduced)} (review threshold ${r.input.config.z_limit} standard u for separate checks). Age ${r.input.config.age_days} / ${r.input.config.max_age_days} allowed days. Gate: ${label(r.gate)}. These configurable review rules are not statistical certification.`;
  element("checks").replaceChildren(
    ...r.check_rows.map((p) => {
      const tr = document.createElement("tr");
      for (const text of [String(p.index), number(p.x), number(p.z), label(p.status)]) {
        const td = document.createElement("td");
        td.textContent = text;
        tr.append(td);
      }
      return tr;
    }),
  );
  element("identity").textContent = r.id;
  element("provenance").textContent = r.input.provenance;
  element("verification").textContent =
    "C# coefficients, covariance and fit status agreed with the independent Fraction reference at 1e−7 absolute / 1e−8 relative tolerance. This verifies calculations, not physical traceability.";
  element("downloads").replaceChildren(
    ...["json", "csv", "html", "input"].map((kind) => {
      const a = document.createElement("a"),
        q = new URLSearchParams(Object.entries(r.settings).map(([k, v]) => [k, String(v)]));
      q.set("format", kind);
      a.href = "/api/report?" + q;
      a.download = "";
      a.textContent = kind.toUpperCase() + " ↓";
      return a;
    }),
  );
  element<HTMLInputElement>("hour").max = String(r.rows.length - 1);
  element<HTMLInputElement>("hour").value = "0";
  drawFit();
  drawSamples();
  inspect();
}
/** Guard asynchronous responses by generation; control changes and failures hide stale evidence. */
async function run() {
  const version = ++generation;
  current = null;
  evidence.hidden = true;
  button.disabled = true;
  status.textContent = "Verifying the native fit and checking independent references…";
  try {
    const response = await fetch("/api/run?" + query(), { signal: AbortSignal.timeout(15000) });
    if (!response.ok) throw new Error("Request failed");
    const data = await response.json();
    if (version !== generation) return;
    render(parseRun(data));
    status.textContent =
      "Verified · C# fit matches the rational reference. Review data-quality and calibration gates below.";
  } catch {
    if (version !== generation) return;
    current = null;
    evidence.hidden = true;
    status.textContent =
      "No verified evidence available. Retry with supported local inputs. Previous results are hidden.";
  } finally {
    if (version === generation) button.disabled = false;
  }
}
form.addEventListener("submit", (event) => {
  event.preventDefault();
  void run();
});
form.addEventListener("change", () => {
  generation++;
  current = null;
  evidence.hidden = true;
  button.disabled = false;
  status.textContent = "Controls changed. Analyze calibration to create new evidence.";
});
element("hour").addEventListener("input", inspect);
void run();
