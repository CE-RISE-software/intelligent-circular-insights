import { expect, test, type Page } from "@playwright/test";

/**
 * Six windows, two backends.
 *
 * These are smoke tests in the strict sense: they assert that each window loads,
 * asks the backend, and renders a real outcome — never that a particular number
 * came back. The numbers are pinned in the Python suite, where a failure points at
 * the engine rather than at a selector.
 *
 * The one thing asserted *hard* here is the mode discipline, because it is a
 * frontend property and nothing else can check it: the badge must report the
 * backend named in the response header, on every page, including the pages where
 * a backend declines.
 */

type Mode = "normal" | "ce-rise";

/**
 * Seed the preference before the app's first render, as the Settings panel does.
 *
 * Seeded only when absent, and that `if` is load-bearing: `addInitScript` runs on
 * *every* navigation, including the reload the Settings panel performs after a
 * switch. Setting it unconditionally re-pinned the old mode on the way back and
 * made the switch look broken when it was not.
 */
async function useMode(page: Page, mode: Mode): Promise<void> {
  await page.addInitScript(m => {
    if (!window.localStorage.getItem("ici.backendMode")) {
      window.localStorage.setItem("ici.backendMode", m as string);
    }
  }, mode);
}

async function goto(page: Page, path: string): Promise<void> {
  await page.goto(path);
  await expect(page.getByTestId("mode-badge")).toBeVisible();
}

/** The badge starts blank and only fills once a response has been seen. */
async function expectServedBy(page: Page, mode: Mode): Promise<void> {
  const badge = page.getByTestId("mode-badge");
  await expect(badge).toHaveAttribute("data-mode", mode, { timeout: 15_000 });
  await expect(badge).toHaveAttribute("data-mismatch", "false");
}

for (const mode of ["normal", "ce-rise"] as const) {
  test.describe(`smoke · ${mode}`, () => {
    test.beforeEach(async ({ page }) => {
      await useMode(page, mode);
    });

    test("the shell loads and the badge names the backend that answered", async ({ page }) => {
      await goto(page, "/search");
      await expectServedBy(page, mode);
    });

    test("an unanswerable question abstains, and the envelope is shown", async ({ page }) => {
      // Chosen to match nothing, so the pack is empty and composition is never
      // entered: a full envelope, no model call, no spend. That makes this the one
      // search assertion that is deterministic on a clean checkout.
      await goto(page, "/search");
      await page.getByTestId("search-input").fill("zzzqqq unmatchable gibberish token");
      await page.getByTestId("search-submit").click();

      await expect(page.getByTestId("abstention")).toBeVisible({ timeout: 20_000 });
      await expect(page.getByTestId("audit-panel")).toBeVisible();
      // The panel reports the whole envelope, not just a score.
      await expect(page.getByTestId("tau-track")).toBeVisible();
      await expect(page.getByTestId("grounding-verdict")).toBeVisible();
      await expect(page.getByTestId("tau")).toHaveText("0.500");
      await expectServedBy(page, mode);
    });

    test("a question needing prose never leaves the window blank", async ({ page }) => {
      // With no cassette recorded this declines; with one it answers. Both are
      // outcomes the window must render — and the failure this guards against is
      // neither: a 500 that painted nothing and blanked the mode badge with it.
      await goto(page, "/search");
      await page.getByTestId("search-input").fill("What is the recycled cobalt content?");
      await page.getByTestId("search-submit").click();

      await expect(
        page.getByTestId("answer").or(page.getByTestId("declined")),
      ).toBeVisible({ timeout: 25_000 });
      await expectServedBy(page, mode);
    });

    test("carbon lists subjects and assesses one", async ({ page }) => {
      await goto(page, "/carbon");
      // The list is read from the profile directory, so this product exists in
      // both modes — ce-rise adds the graph without displacing the CSV engine.
      const subject = page.getByTestId("carbon-subject-fairphone_4");
      await expect(subject).toBeVisible({ timeout: 15_000 });
      await subject.click();
      await expect(page.getByTestId("carbon-result")).toBeVisible({ timeout: 20_000 });
      await expect(page.getByTestId("carbon-stages")).toBeVisible();
      await expectServedBy(page, mode);
    });

    test("validate reports typed, located violations", async ({ page }) => {
      await goto(page, "/validate");
      await page.getByTestId("validate-input").fill("{}");
      await page.getByTestId("validate-submit").click();
      await expect(page.getByTestId("validate-result")).toBeVisible({ timeout: 15_000 });
      await expectServedBy(page, mode);
    });

    test("the model catalogue is the same size in both backends", async ({ page }) => {
      await goto(page, "/models");
      await expect(page.getByTestId("model-catalog")).toBeVisible({ timeout: 15_000 });
      // The regression this guards: an earlier build mounted the graph *over* the
      // catalogue, and switching to the more rigorous backend emptied this table.
      await expect(page.locator('[data-testid^="model-"]')).toHaveCount(19); // 18 rows + the card
      await expectServedBy(page, mode);
    });

    test("compare asks both backends at once", async ({ page }) => {
      await goto(page, "/compare");
      await page.getByTestId("probe-carbon").click();
      await expect(page.getByTestId("compare-grid")).toBeVisible({ timeout: 25_000 });
      // Asking a specific backend must not move the session badge.
      await expectServedBy(page, mode);
    });
  });
}

test.describe("smoke · where the backends differ", () => {
  test("normal declines PEF Studio with a reason and an escape hatch", async ({ page }) => {
    await useMode(page, "normal");
    await goto(page, "/pef/overview");

    const declined = page.getByTestId("declined");
    await expect(declined).toBeVisible({ timeout: 15_000 });
    await expect(declined).toContainText("no knowledge graph is mounted");
    // A decline is not an error: it offers the switch that would satisfy it.
    await expect(page.getByTestId("switch-mode")).toBeVisible();
    // And the badge still names who declined — the header is set by middleware,
    // so it survives a request whose handler never ran.
    await expectServedBy(page, "normal");
  });

  test("ce-rise serves PEF Studio", async ({ page }) => {
    await useMode(page, "ce-rise");
    await goto(page, "/pef/overview");
    await expect(page.getByTestId("pef-overview")).toBeVisible({ timeout: 25_000 });
    await expect(page.getByTestId("pef-coverage")).toBeVisible();
    // The caveat travels with the result rather than living in a footnote.
    await expect(page.getByTestId("compliance-note")).toContainText("not an EF-compliant declaration");
    await expectServedBy(page, "ce-rise");
  });

  test("ce-rise solves the product system off the graph", async ({ page }) => {
    await useMode(page, "ce-rise");
    await goto(page, "/pef/calculator");
    await expect(page.getByTestId("pef-result")).toBeVisible({ timeout: 25_000 });
    await expect(page.getByTestId("pef-stages")).toBeVisible();
  });

  test("a competency question shows its rows and the query behind them", async ({ page }) => {
    await useMode(page, "ce-rise");
    await goto(page, "/pef/questions");
    await expect(page.getByTestId("cq-list")).toBeVisible({ timeout: 25_000 });
    await page.getByTestId("run-cq-cq-fu").click();
    const result = page.getByTestId("cq-result");
    await expect(result).toBeVisible({ timeout: 15_000 });
    await expect(result).toContainText("SELECT");
  });

  test("sparql refuses a write before executing it", async ({ page }) => {
    await useMode(page, "ce-rise");
    await goto(page, "/pef/sparql");
    await page.getByTestId("sparql-input").fill("DELETE WHERE { ?s ?p ?o }");
    await page.getByTestId("sparql-submit").click();
    // Refused as a capability decline, not a 500.
    await expect(page.getByTestId("declined")).toBeVisible({ timeout: 15_000 });
  });
});

test.describe("smoke · the mode switch", () => {
  test("Settings offers only the backends this deployment built", async ({ page }) => {
    await useMode(page, "normal");
    await goto(page, "/search");
    await page.getByTestId("open-settings").click();
    await expect(page.getByTestId("mode-switch")).toBeVisible();
    await expect(page.getByTestId("mode-option-normal")).toBeVisible();
    await expect(page.getByTestId("mode-option-ce-rise")).toBeVisible();
  });

  test("switching in Settings changes which backend answers", async ({ page }) => {
    await useMode(page, "normal");
    await goto(page, "/search");
    await expectServedBy(page, "normal");

    await page.getByTestId("open-settings").click();
    await page.getByTestId("mode-option-ce-rise").click();
    await page.getByTestId("settings-save").click();

    await expect(page.getByTestId("mode-badge")).toHaveAttribute("data-mode", "ce-rise", {
      timeout: 20_000,
    });
  });

  test("a window that the previous backend declined works after the switch", async ({ page }) => {
    await useMode(page, "normal");
    await goto(page, "/pef/overview");
    await expect(page.getByTestId("declined")).toBeVisible({ timeout: 15_000 });
    await page.getByTestId("switch-mode").click();
    await expect(page.getByTestId("pef-overview")).toBeVisible({ timeout: 30_000 });
  });
});
