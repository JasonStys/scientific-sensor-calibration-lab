/** Real three-engine calibration workflows by Jason Stys. Functions/variables: docs/CODE_INDEX.md. */
import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { readFile } from "node:fs/promises";
test.beforeEach(async ({ page }) => {
  await page.goto("/");
  await expect(page.locator("#status")).toContainText("Verified");
});
test("native verified fit, chart, author and help", async ({ page }) => {
  await expect(page.locator("#gate")).toHaveText("Within checks");
  await expect(page.locator("#available")).toHaveText("24 / 24");
  await expect(page.locator("#checks tr")).toHaveCount(5);
  await expect(page.locator("#equation")).toContainText("20.024");
  await expect(page.locator("#identity")).toHaveText(/^[a-f0-9]{64}$/);
  const pixels = await page.locator("#fit-chart").evaluate((node) => {
    const ctx = (node as HTMLCanvasElement).getContext("2d")!,
      data = ctx.getImageData(0, 0, 1000, 320).data;
    let n = 0;
    for (let i = 3; i < data.length; i += 4) if (data[i]) n++;
    return n;
  });
  expect(pixels).toBeGreaterThan(3000);
  await expect(page.locator("footer")).toContainText("Jason Stys");
  await expect(page.getByRole("link", { name: "User guide" })).toHaveAttribute(
    "href",
    /docs\/USER_GUIDE.md/,
  );
});
test("controls invalidate old evidence and download accepted settings", async ({ page }) => {
  const original = await page.locator("#identity").textContent();
  await page.locator("#sigma").selectOption("2");
  await expect(page.locator("#evidence")).toBeHidden();
  await page.locator("#run").click();
  await expect(page.locator("#status")).toContainText("Verified");
  await expect(page.locator("#identity")).not.toHaveText(original!);
  expect(await page.locator("#downloads a").first().getAttribute("href")).toContain("sigma=2");
});
test("actual four-format downloads", async ({ page }) => {
  for (const kind of ["JSON", "CSV", "HTML", "INPUT"]) {
    const waiting = page.waitForEvent("download");
    await page
      .locator("#downloads")
      .getByRole("link", { name: kind + " ↓", exact: true })
      .click();
    const download = await waiting,
      path = await download.path();
    expect(path).not.toBeNull();
    const body = await readFile(path!, "utf8");
    if (kind === "JSON") {
      const r = JSON.parse(body);
      expect(r.verification.native_reference_verified).toBe(true);
      expect(r.rows).toHaveLength(24);
      expect(r.id).toBe(await page.locator("#identity").textContent());
    }
    if (kind === "CSV") expect(body.trim().split("\n")).toHaveLength(25);
    if (kind === "HTML") {
      expect(body).toContain("Scientific Sensor Calibration Lab");
      expect(body).not.toContain("<script");
    }
    if (kind === "INPUT") expect(JSON.parse(body).calibration).toHaveLength(9);
  }
});
test("missing readings are gaps not zero", async ({ page }) => {
  await page.locator("#scenario").selectOption("missing-data");
  await page.locator("#run").click();
  await expect(page.locator("#available")).toHaveText("22 / 24");
  await page.locator("#hour").fill("4");
  await expect(page.locator("#sample-status")).toContainText("missing");
  await expect(page.locator("#signal")).toHaveText("Unavailable");
  await expect(page.locator("#estimate")).toHaveText("Unavailable");
});
test("expired calibration withholds all estimates", async ({ page }) => {
  await page.locator("#age").selectOption("120");
  await page.locator("#run").click();
  await expect(page.locator("#gate")).toHaveText("calibration expired");
  await expect(page.locator("#available")).toHaveText("0 / 24");
  await expect(page.locator("#rmse")).toHaveText("Unavailable");
});
test("nonlinearity is not silently repaired", async ({ page }) => {
  await page.locator("#scenario").selectOption("nonlinear-response");
  await page.locator("#run").click();
  await expect(page.locator("#gate")).toHaveText("fit inconsistent");
  await expect(page.locator("#available")).toHaveText("0 / 24");
});
test("reference mismatch is visible in drift scenario", async ({ page }) => {
  await page.locator("#scenario").selectOption("sensor-drift");
  await page.locator("#run").click();
  await expect(page.locator("#status")).toContainText("Verified");
  await page.locator("#hour").fill("18");
  await expect(page.locator("#sample-status")).toContainText("reference mismatch");
  await expect(page.locator("#estimate")).not.toHaveText("Unavailable");
});
test("failures and malformed results hide prior evidence", async ({ page }) => {
  await page.route("**/api/run?**", (r) => r.fulfill({ status: 500, body: "failure" }));
  await page.locator("#run").click();
  await expect(page.locator("#status")).toContainText("No verified evidence");
  await expect(page.locator("#evidence")).toBeHidden();
  await page.route("**/api/run?**", (r) => r.fulfill({ json: { fit: {} } }));
  await page.locator("#run").click();
  await expect(page.locator("#status")).toContainText("No verified evidence");
});
test("stale response cannot revive old evidence", async ({ page }) => {
  let release!: () => void, entered!: () => void;
  const held = new Promise<void>((r) => {
      release = r;
    }),
    started = new Promise<void>((r) => {
      entered = r;
    });
  await page.route("**/api/run?**", async (route) => {
    const response = await route.fetch();
    entered();
    await held;
    await route.fulfill({ response });
  });
  await page.locator("#run").click();
  await started;
  await page.locator("#limit").selectOption("2");
  release();
  await expect(page.locator("#status")).toContainText("Controls changed");
  await expect(page.locator("#evidence")).toBeHidden();
});
test("hostile provenance stays text", async ({ page, request }) => {
  const response = await request.get("/api/run"),
    run = await response.json();
  run.input.provenance = '<img src=x onerror="window.injection=true">';
  await page.route("**/api/run?**", (r) => r.fulfill({ json: run }));
  await page.locator("#run").click();
  await expect(page.locator("#provenance")).toHaveText(run.input.provenance);
  await expect(page.locator("#provenance img")).toHaveCount(0);
});
test("mobile keyboard accessibility", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.locator("#scenario").focus();
  await page.keyboard.press("Tab");
  await expect(page.locator("#sigma")).toBeFocused();
  await page.getByRole("region", { name: "Scrollable held-out calibration checks" }).focus();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(
    true,
  );
  const result = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
    .analyze();
  expect(result.violations).toEqual([]);
});
test("read-only finite API and origin enforcement", async ({ request }) => {
  expect((await request.get("/api/run?limit=9")).status()).toBe(400);
  expect(
    (await request.get("/api/run", { headers: { Origin: "https://outside.invalid" } })).status(),
  ).toBe(403);
  expect((await request.post("/api/run")).status()).toBe(405);
  expect((await request.get("/.env")).status()).toBe(404);
});
