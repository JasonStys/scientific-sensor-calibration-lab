/** Unit-test boundary by Jason Stys; browser acceptance has its own Playwright runner. */
import { defineConfig } from "vitest/config";
export default defineConfig({ test: { include: ["web/**/*.test.ts"] } });
