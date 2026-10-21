/** Real three-browser sensor-lab acceptance by Jason Stys. Fields: docs/CODE_INDEX.md. */
import { defineConfig, devices } from "@playwright/test";
const python =
  process.env.PYTHON ?? (process.platform === "win32" ? ".venv/Scripts/python.exe" : "python");
const external = process.env.CALIBRATION_BASE_URL;
export default defineConfig({
  testDir: "tests",
  testMatch: "ui.spec.ts",
  workers: 1,
  retries: 0,
  timeout: 30000,
  reporter: "list",
  use: {
    baseURL: external ?? "http://127.0.0.1:8965",
    trace: "off",
    screenshot: "off",
    video: "off",
    reducedMotion: "reduce",
  },
  ...(external
    ? {}
    : {
        webServer: {
          command: `"${python}" -m sensorlab serve --port 8965 --no-browser`,
          url: "http://127.0.0.1:8965/api/health",
          reuseExistingServer: false,
          timeout: 20000,
        },
      }),
  projects: [
    { name: "chromium", use: { ...devices["Desktop Chrome"] } },
    { name: "firefox", use: { ...devices["Desktop Firefox"] } },
    { name: "webkit", use: { ...devices["Desktop Safari"] } },
  ],
});
