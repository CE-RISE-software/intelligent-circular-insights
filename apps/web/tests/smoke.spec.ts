import { expect, test, type Page } from "@playwright/test";
import { Buffer } from "node:buffer";
import type { RepairResult, SearchResult } from "../src/lib/types";

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

  test("repair without evidence or training suggestions reports gaps without a model call", async ({ page }) => {
    await useMode(page, "normal");
    await goto(page, "/validate");

    // Without sources or permission for training suggestions, no model is called.
    await page
      .getByTestId("validate-input")
      .fill(JSON.stringify({ dpp_id: "zzz-000", product: { brand: "Qqzzx", model: "Wubbleflorp 9000" } }));
    await page.getByTestId("validate-submit").click();
    await expect(page.getByTestId("repair-offer")).toBeVisible({ timeout: 15_000 });
    await page.getByTestId("toggle-suggestions").uncheck();
    await page.getByTestId("repair-submit").click();

    await expect(page.getByTestId("no-fills")).toBeVisible();
    await expect(page.getByTestId("cannot-ground")).toBeVisible();
    await expect(page.getByTestId("repair-trace")).toContainText("not called");
    await expect(page.getByTestId("unverified-suggestions")).not.toBeVisible();
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
    await expect(declined).toContainText("no same-product structured evidence");
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

  for (const mode of ["normal", "ce-rise"] as const) {
    test(`recorded repair shows grounded fills and a synthetic preview · ${mode}`, async ({ page }) => {
      await useMode(page, mode);
      await goto(page, "/validate");
      await page.getByTestId("validate-submit").click();
      await page.getByTestId("repair-submit").click();
      await expect(page.getByTestId("grounded-fills")).toContainText("repository:synthetic-demo-dpp-001");
      await expect(page.getByTestId("repair-preview")).toContainText("Synthetic test record");
      await expect(page.getByTestId("repair-trace")).toContainText("live attempts 0");
      await expect(page.getByTestId("repair-trace")).toContainText("prompt hash");
      await expectServedBy(page, mode);
      await page.getByTestId("validate-input").fill("{}");
      await expect(page.getByTestId("repair-preview")).not.toBeVisible();
      await expect(page.getByTestId("validate-result")).not.toBeVisible();
    });

    test(`recorded synthesis shows field provenance · ${mode}`, async ({ page }) => {
      await useMode(page, mode);
      await goto(page, "/synthesize");
      await page.getByTestId("synth-submit").click();
      await expect(page.getByTestId("synth-result")).toContainText("Synthetic test record");
      await expect(page.getByTestId("synth-support")).toContainText("repository:synthetic-demo-dpp-001");
      await expect(page.getByTestId("synth-trace")).toContainText("live attempts 0");
      await expectServedBy(page, mode);
      await page.getByTestId("synth-input").fill("{}");
      await expect(page.getByTestId("synth-result")).not.toBeVisible();
    });
  }

  test("editing a seed invalidates an in-flight synthesis result", async ({ page }) => {
    await useMode(page, "normal");
    let release!: () => void;
    const held = new Promise<void>(resolve => { release = resolve; });
    await page.route("**/api/synthesize", async route => {
      await held;
      await route.fulfill({ status: 422, contentType: "application/json",
        body: JSON.stringify({ error: "record_not_grounded", mode: "normal", reason: "STALE RESULT" }) });
    });
    await goto(page, "/synthesize");
    const request = page.waitForRequest("**/api/synthesize");
    await page.getByTestId("synth-submit").click();
    await request;
    await page.getByTestId("synth-input").fill("{}");
    const response = page.waitForResponse("**/api/synthesize");
    release();
    await response;
    await expect(page.getByText("STALE RESULT")).not.toBeVisible();
    await expect(page.getByTestId("synth-submit")).toBeEnabled();
  });

  test("training suggestions stay in review and out of the repaired preview", async ({ page }) => {
    await useMode(page, "normal");
    const result: RepairResult = {
      mode: "normal", record: {}, conforms: false,
      after: { profile: "eu-dpp", conforms: false, checked_paths: 0, violations: [
        { kind: "required", location: "/compliance", message: "missing", expected: null, actual: null },
      ] },
      grounded_fills: [], rejected: [],
      cannot_be_grounded: [{ path: "/compliance", reason: "No supporting source" }],
      unverified_suggestions: [{ path: "/compliance", value: "UNVERIFIED-CANDIDATE",
        rationale: "Check applicability with the manufacturer", model_score: 0.3,
        source: "model_training", status: "unverified", requires_review: true }],
      trace: { correlation_id: "synthetic-browser-test", model: "gpt-4o-mini", prompt_hashes: [],
        cost: { llm_calls: 0, usd: 0, prompt_tokens: 0, completion_tokens: 0, reasoning_tokens: 0 },
        steps: [] },
    };
    await page.route("**/api/validate/repair", route => route.fulfill({
      status: 200, contentType: "application/json", headers: { "X-Backend-Mode-Used": "normal" },
      body: JSON.stringify(result),
    }));
    await goto(page, "/validate");
    await page.getByTestId("validate-input").fill("{}");
    await page.getByTestId("validate-submit").click();
    await page.getByTestId("repair-submit").click();
    const review = page.getByTestId("unverified-suggestions");
    await expect(review).toContainText("UNVERIFIED-CANDIDATE");
    await expect(review).toContainText("0.30");
    await expect(review).toContainText("not evidence");
    await expect(review.getByRole("button")).toHaveCount(0);
    await expect(page.getByTestId("repair-preview")).not.toContainText("UNVERIFIED-CANDIDATE");
    await expect(page.getByTestId("grounded-fills")).not.toBeVisible();
    await page.getByTestId("toggle-suggestions").uncheck();
    await expect(review).not.toBeVisible();
  });
});


test.describe("smoke · the decline stays readable", () => {
  /**
   * A contrast regression, caught by measuring a screenshot rather than by looking
   * at one. The declined panel's heading came out at 1.53:1 against its background
   * — WCAG AA wants 3.0 for large text, and every other heading in this app reads
   * at about 14:1.
   *
   * The cause was a tinted fill at 14% opacity with nothing opaque beneath it, so
   * the page's magenta gradient showed through and the "background" behind the
   * heading was the gradient, not the panel.
   *
   * It is worth a test because of *which* panel it was. The product's whole claim
   * is that declining honestly beats guessing; the text explaining why it declined
   * cannot be the least legible thing on the page.
   *
   * The assertion is on opacity rather than on a computed ratio, because opacity is
   * the property that actually failed and the one a future edit would regress.
   */
  const ALPHA = /rgba?\([^)]*?(?:,\s*([\d.]+))?\)$/;

  function opacity(colour: string): number {
    const m = colour.match(ALPHA);
    return m && m[1] !== undefined ? Number.parseFloat(m[1]) : 1;
  }

  test("a declined panel is opaque enough to hide the page gradient", async ({ page }) => {
    await useMode(page, "normal");
    await goto(page, "/pef/overview");
    const panel = page.getByTestId("declined");
    await expect(panel).toBeVisible({ timeout: 15_000 });

    const background = await panel.evaluate(el => getComputedStyle(el).backgroundColor);
    expect(opacity(background),
      `declined panel background ${background} lets the page show through`).toBeGreaterThan(0.85);

    // And the text on it is dark ink, not the mid-tone that measured 1.53:1.
    const head = await panel.locator(".head").evaluate(el => getComputedStyle(el).color);
    const parts = (head.match(/\d+/g) ?? []).slice(0, 3).map(Number);
    expect(parts, `could not read a colour from ${head}`).toHaveLength(3);
    const [r = 0, g = 0, b = 0] = parts;
    const relative = (v: number) => {
      const c = v / 255;
      return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
    };
    const luminance = 0.2126 * relative(r) + 0.7152 * relative(g) + 0.0722 * relative(b);
    // Against the near-white panel base, this keeps the heading above AA.
    expect(luminance, `heading colour ${head} is too light for this panel`).toBeLessThan(0.22);
  });

  test("the unverified-suggestion surface is opaque too", async ({ page }) => {
    // Same failure mode, and the same reason it matters: a quarantine nobody can
    // read is not a review surface.
    await useMode(page, "normal");
    await goto(page, "/validate");
    const opacityOf = await page.evaluate(() => {
      const probe = document.createElement("section");
      probe.className = "suggestion-review";
      document.body.append(probe);
      const bg = getComputedStyle(probe).backgroundColor;
      probe.remove();
      return bg;
    });
    expect(opacity(opacityOf)).toBeGreaterThan(0.85);
  });
});

test.describe("smoke · single passport", () => {
  // The last window from the demo's port table, and the one that most needed
  // folding back into the shared path: in the demo it had its own pipeline, its
  // own confidence number and no grounding check at all.

  test("a pasted passport is split on its own structure", async ({ page }) => {
    await useMode(page, "normal");
    await goto(page, "/single-dpp");
    await page.getByTestId("single-read").click();

    const sections = page.getByTestId("single-sections");
    await expect(sections).toBeVisible({ timeout: 15_000 });
    // Keys, not character offsets.
    await expect(sections).toContainText("Compliance");
    await expect(sections).toContainText("/compliance");
    await expectServedBy(page, "normal");
  });

  test("reading needs no model, and a broken document still reads", async ({ page }) => {
    await useMode(page, "normal");
    await goto(page, "/single-dpp");
    await page.getByTestId("single-input").fill('{"broken": ');
    await page.getByTestId("single-read").click();

    // A malformed passport is exactly what someone wants help with, so it is read
    // as text and the problem is named rather than the request failing.
    const warnings = page.getByTestId("single-warnings");
    await expect(warnings).toBeVisible({ timeout: 15_000 });
    await expect(warnings).toContainText("does not parse");
  });

  test("asking renders an outcome and the same envelope as search", async ({ page }) => {
    await useMode(page, "normal");
    await goto(page, "/single-dpp");
    await page.getByTestId("single-read").click();
    await expect(page.getByTestId("single-ask")).toBeVisible({ timeout: 15_000 });

    await page.getByTestId("single-question").fill("Which compliance standards does this carry?");
    await page.getByTestId("single-submit").click();

    // Answer, abstention or an honest decline — never a blank window. When it
    // answers, the audit panel beside it is literally the search window's.
    await expect(
      page.getByTestId("single-answer").or(page.getByTestId("declined")),
    ).toBeVisible({ timeout: 25_000 });
    await expectServedBy(page, "normal");
  });

  test("changing the document clears the previous reading", async ({ page }) => {
    // Sections from one passport beside an answer about another is how somebody
    // reads a result about the wrong product.
    await useMode(page, "normal");
    await goto(page, "/single-dpp");
    await page.getByTestId("single-read").click();
    await expect(page.getByTestId("single-sections")).toBeVisible({ timeout: 15_000 });

    await page.getByTestId("single-input").fill('{"dpp_id": "other-999"}');
    await expect(page.getByTestId("single-sections")).toBeHidden();
  });

  test("a file upload replaces the example and can be read", async ({ page }) => {
    await useMode(page, "normal");
    await goto(page, "/single-dpp");
    await page.getByTestId("single-file").setInputFiles({
      name: "uploaded-passport.txt", mimeType: "text/plain",
      buffer: Buffer.from("Synthetic uploaded passport.\n\nDeclared capacity: 5 kWh."),
    });
    await expect(page.getByTestId("single-input")).toHaveValue(/Declared capacity: 5 kWh/);
    await page.getByTestId("single-read").click();
    await expect(page.getByTestId("single-sections")).toContainText("Declared capacity");
    await expectServedBy(page, "normal");
  });

  test("editing during a delayed parse cannot restore old sections", async ({ page }) => {
    await useMode(page, "normal");
    let release!: () => void;
    const held = new Promise<void>(resolve => { release = resolve; });
    await page.route("**/api/single-dpp/parse", async route => {
      await held;
      await route.continue();
    });
    await goto(page, "/single-dpp");
    const request = page.waitForRequest("**/api/single-dpp/parse");
    await page.getByTestId("single-read").click();
    await request;
    await page.getByTestId("single-input").fill("a different document");
    const response = page.waitForResponse("**/api/single-dpp/parse");
    release();
    await response;
    await expect(page.getByTestId("single-read")).toBeEnabled();
    await expect(page.getByTestId("single-sections")).not.toBeVisible();
  });

  test("editing during a delayed answer cannot show the prior passport's result", async ({ page }) => {
    await useMode(page, "normal");
    let release!: () => void;
    const held = new Promise<void>(resolve => { release = resolve; });
    await page.route("**/api/single-dpp/ask", async route => {
      await held;
      await route.fulfill({ status: 422, contentType: "application/json",
        headers: { "X-Backend-Mode-Used": "normal" },
        body: JSON.stringify({ error: "model_unavailable", mode: "normal", reason: "STALE PASSPORT" }) });
    });
    await goto(page, "/single-dpp");
    await page.getByTestId("single-read").click();
    await expect(page.getByTestId("single-ask")).toBeVisible();
    const request = page.waitForRequest("**/api/single-dpp/ask");
    await page.getByTestId("single-question").fill("Which standard?");
    await page.getByTestId("single-submit").click();
    await request;
    await page.getByTestId("single-input").fill("A different passport.");
    const response = page.waitForResponse("**/api/single-dpp/ask");
    release();
    await response;
    await expect(page.getByText("STALE PASSPORT")).not.toBeVisible();
    await expect(page.getByTestId("single-sections")).not.toBeVisible();
  });

  test("it is reachable in both modes", async ({ page }) => {
    for (const mode of ["normal", "ce-rise"] as const) {
      await page.context().clearCookies();
      await useMode(page, mode);
      await goto(page, "/search");
      await page.getByTestId("nav-single-dpp").click();
      await expect(page.getByTestId("page-single-dpp")).toBeVisible({ timeout: 15_000 });
    }
  });
});
