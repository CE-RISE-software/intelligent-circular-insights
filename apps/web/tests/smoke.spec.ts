import { expect, test, type Page } from "@playwright/test";
import type { SearchResult } from "../src/lib/types";

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
      await expect(page.getByTestId("audit-panel")).not.toContainText("Below the threshold");
      await page.getByTestId("toggle-trace").click();
      await expect(page.getByTestId("model-audit")).toContainText("not called");
      await expect(page.getByTestId("model-audit")).toContainText("live attempts 0");
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

    test("a failed compare request does not clear the session badge", async ({ page }) => {
      await goto(page, "/compare");
      await expectServedBy(page, mode);
      await page.route("**/api/carbon/calculate", route => route.abort());
      await page.getByTestId("probe-carbon").click();
      await expect(page.getByTestId("compare-grid")).toBeVisible();
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

test("smoke · an unscored grounded answer exposes model audit and survives a grounding decline", async ({ page }) => {
  await useMode(page, "ce-rise");
  const result: SearchResult = {
    decision: "answer", mode: "ce-rise", answer: "The declared capacity is 60 kWh [e1].",
    abstain_reason: null, weak_signal: null,
    confidence: { raw: 0.9, calibrated: 0.9, calibrator: "synthetic", signals: {} },
    operating_point: { tau: 0.5, coverage_target: null },
    grounding: { verdict: "fully_grounded", claims_total: 1, claims_resolved: 1, unresolved: [] },
    evidence: [{ id: "e1", kind: "substrate_row", ref: "synthetic:capacity", score: null, text: "60 kWh" }],
    provenance: [{ kind: "triple", ref: "synthetic:capacity", source_file: null, excerpt: "60 kWh" }],
    trace: {
      correlation_id: "synthetic-browser-test", model: "gpt-4o-mini", prompt_hashes: ["mode-prompt-hash"],
      cost: { prompt_tokens: 100, completion_tokens: 20, reasoning_tokens: 0, llm_calls: 0, usd: 0 },
      steps: [{ name: "grounding", detail: "1/1", duration_ms: 0 }],
    },
    data_trust: null,
  };
  await page.route("**/api/search", route => route.fulfill({
    status: 200, contentType: "application/json", headers: { "X-Backend-Mode-Used": "ce-rise" },
    body: JSON.stringify(result),
  }));
  await goto(page, "/search");
  await page.getByTestId("search-input").fill("capacity");
  await page.getByTestId("search-submit").click();
  await expect(page.getByTestId("evidence")).toContainText("unscored");
  await expect(page.getByTestId("grounding-verdict")).toContainText("Fully grounded");
  await page.getByTestId("toggle-trace").click();
  await expect(page.getByTestId("model-audit")).toContainText("gpt-4o-mini");
  await expect(page.getByTestId("trace")).toContainText("mode-prompt-hash");

  result.decision = "abstain";
  result.answer = null;
  result.abstain_reason = "The warranty claim could not be traced to evidence.";
  result.grounding = { verdict: "unresolved_claims", claims_total: 1, claims_resolved: 0,
    unresolved: [{ id: "claim:1", text: "Ten-year warranty", cited: [] }] };
  await page.getByTestId("search-submit").click();
  await expect(page.getByTestId("unresolved-claim")).toContainText("Ten-year warranty");
  await expect(page.getByTestId("audit-panel")).toContainText(result.abstain_reason);
  await expect(page.getByTestId("audit-panel")).not.toContainText("Below the threshold");
});


test.describe("smoke · record assistance", () => {
  // These two windows did not exist until the gap audit: the record composer was
  // built, tested and reachable only from Python tests. What is asserted here is
  // the half that could still go wrong — that a model's guess is never rendered
  // where a person would read it as evidence.

  test("validate offers repair only when the record does not conform", async ({ page }) => {
    await useMode(page, "normal");
    await goto(page, "/validate");

    await page.getByTestId("validate-input").fill("{}");
    await page.getByTestId("validate-submit").click();
    await expect(page.getByTestId("validate-result")).toBeVisible({ timeout: 15_000 });
    // An empty record cannot conform, so the offer is there.
    await expect(page.getByTestId("repair-offer")).toBeVisible();
    await expect(page.getByTestId("toggle-suggestions")).toBeChecked();
  });

  test("repair declines honestly when there is nothing to ground against", async ({ page }) => {
    await useMode(page, "normal");
    await goto(page, "/validate");

    // A product no source in the workspace mentions. The system refuses *before*
    // the model call rather than filling the gaps from its own priors.
    await page
      .getByTestId("validate-input")
      .fill(JSON.stringify({ dpp_id: "zzz-000", product: { brand: "Qqzzx", model: "Wubbleflorp 9000" } }));
    await page.getByTestId("validate-submit").click();
    await expect(page.getByTestId("repair-offer")).toBeVisible({ timeout: 15_000 });
    await page.getByTestId("repair-submit").click();

    const declined = page.getByTestId("declined");
    await expect(declined).toBeVisible({ timeout: 25_000 });
    await expect(declined).toContainText("no evidence was found");
  });

  test("the synthesize window loads and declines an ungroundable seed", async ({ page }) => {
    await useMode(page, "normal");
    await goto(page, "/synthesize");
    await expect(page.getByTestId("synthesize-form")).toBeVisible({ timeout: 15_000 });

    await page
      .getByTestId("synth-input")
      .fill(JSON.stringify({ dpp_id: "zzz-000", product: { brand: "Qqzzx", model: "Wubbleflorp 9000" } }));
    await page.getByTestId("synth-submit").click();

    const declined = page.getByTestId("declined");
    await expect(declined).toBeVisible({ timeout: 25_000 });
    await expect(declined).toContainText("no evidence was found");
    await expectServedBy(page, "normal");
  });

  test("synthesize is reachable from the sidebar in both modes", async ({ page }) => {
    for (const mode of ["normal", "ce-rise"] as const) {
      await page.context().clearCookies();
      await useMode(page, mode);
      await goto(page, "/search");
      await page.getByTestId("nav-synthesize").click();
      await expect(page.getByTestId("page-synthesize")).toBeVisible({ timeout: 15_000 });
    }
  });
});
