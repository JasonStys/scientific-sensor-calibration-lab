/**
 * Frozen C# fit and uncertainty-budget acceptance by Jason Stys.
 * Function: runNativeJourney callback; variables: independent variance arithmetic and withheld estimates.
 * Uses synthetic calibration only; no physical certification or instrument connection.
 * Symbol locations: docs/CODE_INDEX.md.
 */
import assert from "node:assert/strict";
import { expect } from "@playwright/test";
import { runNativeJourney } from "./native_browser.mjs";

await runNativeJourney(async ({ page, request }) => {
  await page.goto("/");
  await expect(page.locator("#status")).toContainText("Verified");
  await expect(page.locator("#uncertainty-budget")).toContainText("do not add it again");
  const response = await request.get("/api/run");
  assert.equal(response.status(), 200);
  const report = await response.json();
  assert.equal(report.verification.native_reference_verified, true);
  assert.equal(report.rows.length, 24);
  for (const row of report.rows) {
    if (row.estimate === null) {
      assert.equal(row.response_variance, null);
      assert.equal(row.fit_parameter_variance, null);
    } else {
      const sum = row.response_variance + row.fit_parameter_variance;
      assert.ok(row.response_variance >= 0 && row.fit_parameter_variance >= 0);
      assert.ok(Math.abs(sum - row.u ** 2) < 1e-8);
      assert.ok(Math.abs(row.response_variance_fraction + row.fit_variance_fraction - 1) < 1e-8);
      assert.equal(
        row.dominant_uncertainty,
        row.response_variance >= row.fit_parameter_variance ? "response" : "fit",
      );
    }
  }
  const exported = await request.get("/api/report?format=json");
  assert.equal(exported.status(), 200);
  assert.deepEqual((await exported.json()).rows, report.rows);
  await page.locator("#age").selectOption("120");
  await page.getByRole("button", { name: "Analyze calibration" }).click();
  await expect(page.locator("#status")).toContainText("Verified");
  await expect(page.locator("#uncertainty-budget")).toContainText("budget withheld");
  const withheld = await request.get("/api/run?age=120");
  assert.equal(withheld.status(), 200);
  for (const row of (await withheld.json()).rows) {
    assert.equal(row.estimate, null);
    assert.equal(row.response_variance, null);
    assert.equal(row.fit_parameter_variance, null);
  }
});
