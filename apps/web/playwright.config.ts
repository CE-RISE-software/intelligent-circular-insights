import { defineConfig, devices } from "@playwright/test";

/**
 * The smoke gate: every window loads and answers, in both modes.
 *
 * Both servers are started by Playwright rather than assumed, so the gate is one
 * command on a clean checkout. The API runs with cassette replay, which makes no
 * network call and fails loudly on a miss — so a smoke run can never quietly spend
 * money on the OpenAI account.
 */
// Dedicated ports keep the no-spend gate isolated from a developer's presentation
// servers. Reusing a live backend on port 8000 makes a nominal replay test perform
// paid model calls and then misreport them as a cassette regression.
const API = "http://127.0.0.1:18000";
const WEB = "http://127.0.0.1:15173";

export default defineConfig({
  testDir: "./tests",
  timeout: 30_000,
  expect: { timeout: 7_000 },
  fullyParallel: false,
  workers: 1,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [["github"], ["list"]] : [["list"]],
  use: {
    baseURL: WEB,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  // ICI_CHROMIUM lets a sandboxed or air-gapped environment point at a browser
  // that is already on disk. `playwright install` needs cdn.playwright.dev, which
  // a managed network may refuse; without this the gate would simply be
  // unrunnable there rather than runnable with the browser it already has.
  projects: [
    {
      name: "chromium",
      use: {
        ...devices["Desktop Chrome"],
        ...(process.env.ICI_CHROMIUM
          ? { launchOptions: { executablePath: process.env.ICI_CHROMIUM } }
          : {}),
      },
    },
  ],
  webServer: [
    {
      // Run from the repository root: the API is a uv workspace, not a package
      // in this directory.
      command:
        "uv run uvicorn apps.api.main:app --host 127.0.0.1 --port 18000 --log-level warning",
      cwd: "../..",
      url: `${API}/api/health`,
      reuseExistingServer: false,
      timeout: 180_000,
      env: { LLM_CASSETTE_MODE: "replay", LLM_CASSETTE_DIR: "tests/cassettes/recorded" },
    },
    {
      command: "npm run dev -- --host 127.0.0.1 --port 15173 --strictPort",
      url: WEB,
      reuseExistingServer: false,
      timeout: 90_000,
      env: { ICI_API_TARGET: API },
    },
  ],
});
