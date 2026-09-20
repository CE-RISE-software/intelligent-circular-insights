#!/usr/bin/env python3
"""Freeze the behaviour of the current system, before any of it is ported.

This is the no-regression oracle (ADR 0004). "Don't break what works" has to be a
command that exits 0 or 1, not a promise, and the only way to get one is to record
what the existing code does *first*.

Two modes, because the demo is awkward to boot:

  --service   (default)  Call the service objects directly. Works anywhere, needs
                         no server and no API key, and is the right level anyway:
                         we are porting services, not the HTTP shell.

  --http URL             Drive a running CE-RISE-Demo over HTTP. Catches routing
                         and serialisation regressions the service level cannot.
                         Run this on a machine where the demo actually boots.

Deliberately small. Two representative cases and two edge cases per area, around
30 records. Capturing every input would cost real API spend on the LLM paths and
catch almost nothing extra: a port that breaks behaviour breaks it on the first
case, not the fortieth. Small enough that a legitimate change is a readable diff.
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import os
import pathlib
import sys
import traceback
from typing import Any

# Fields that differ between two correct runs. Normalised away, and nothing else is.
VOLATILE = {
    "timestamp", "generated_at", "created_at", "issued_at_utc", "at",
    "latency_ms", "duration_ms", "elapsed", "elapsed_ms",
    "correlation_id", "request_id", "trace_id", "session_id", "run_id",
}
FLOAT_PLACES = 6


def normalise(value: Any) -> Any:
    """Strip what legitimately varies between runs; keep everything else exact."""
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return normalise(dataclasses.asdict(value))
    if isinstance(value, dict):
        return {k: normalise(v) for k, v in sorted(value.items()) if k not in VOLATILE}
    if isinstance(value, (list, tuple)):
        return [normalise(v) for v in value]
    if isinstance(value, float):
        # Guard against platform float noise without hiding a real numeric change.
        return round(value, FLOAT_PLACES)
    if hasattr(value, "as_dict"):
        return normalise(value.as_dict())
    if hasattr(value, "__dict__") and not isinstance(value, type):
        return normalise({k: v for k, v in vars(value).items() if not k.startswith("_")})
    return value


def write(out: pathlib.Path, area: str, case: str, payload: Any) -> None:
    target = out / area
    target.mkdir(parents=True, exist_ok=True)
    (target / f"{case}.json").write_text(
        json.dumps(normalise(payload), indent=2, sort_keys=True, default=str) + "\n"
    )


def record(out: pathlib.Path, area: str, case: str, fn: Any) -> tuple[str, str]:
    """Run one case. A raised exception is itself worth freezing — the current
    behaviour on a bad input is part of what must not silently change."""
    try:
        write(out, area, case, fn())
        return case, "ok"
    except Exception as exc:  # noqa: BLE001 - the failure mode is the record
        write(out, area, case, {"__raised__": type(exc).__name__, "message": str(exc)[:400]})
        return case, f"raised {type(exc).__name__}"


# ----------------------------------------------------------------- service mode
def capture_services(demo_root: pathlib.Path, llmmain_root: pathlib.Path,
                     out: pathlib.Path) -> list[tuple[str, str, str]]:
    results: list[tuple[str, str, str]] = []

    # -- carbon: the deterministic engine, self-contained in the demo ----------
    sys.path.insert(0, str(demo_root))
    from backend.core.carbon_calculation_service import get_carbon_service

    svc = get_carbon_service()
    for case, product in [
        ("representative_iphone15", "apple_iphone15_pro_128gb"),
        ("representative_bev_pack", "generic_bev_pack_60kwh"),
        ("edge_unknown_product", "no_such_product_at_all"),
    ]:
        results.append(("carbon", *record(out, "carbon", case,
                                          lambda p=product: svc.calculate(p))))
    results.append(("carbon", *record(out, "carbon", "edge_grid_scenario",
        lambda: svc.calculate("generic_bev_pack_60kwh", scenario={"grid": "CN"}))))
    for case, product in [("profile_lexmark", "lexmark_mx431adn"),
                          ("profile_fairphone", "fairphone_4")]:
        results.append(("carbon", *record(out, "carbon", case,
                                          lambda p=product: svc.load_product_profile(p))))

    # -- llmmain's originals, in a separate process -------------------------
    # CE-RISE-Demo and llmmain both ship a top-level package called ``backend``.
    # They cannot coexist in one interpreter, so the llmmain-side captures run
    # out-of-process. This collision is one of the concrete reasons for the port:
    # afterwards, every package has a name of its own.
    results.extend(_capture_llmmain(llmmain_root, out))
    return results


_LLMMAIN_PROBE = r"""
import json, sys, pathlib
sys.path.insert(0, sys.argv[1])
out = pathlib.Path(sys.argv[2])
from backend.services import symbolic_reasoning_service as sym

captured = {}
reasoner = sym.build_reasoner(run_owl_rl=True, domain="battery")
captured["reasoner_type"] = type(reasoner).__name__
captured["products"] = [str(p).rsplit("#", 1)[-1].rsplit("/", 1)[-1]
                        for p in reasoner.list_products()]
captured["derived_by_rules"] = reasoner.apply_rules()
captured["obligations"] = {
    str(p).rsplit("#", 1)[-1].rsplit("/", 1)[-1]: {
        "compliance": sorted(str(x).rsplit("#", 1)[-1].rsplit("/", 1)[-1]
                             for x in reasoner.requires_compliance(
                                 str(p).rsplit("#", 1)[-1].rsplit("/", 1)[-1])),
        "steps": sorted(str(x).rsplit("#", 1)[-1].rsplit("/", 1)[-1]
                        for x in reasoner.requires_steps(
                            str(p).rsplit("#", 1)[-1].rsplit("/", 1)[-1])),
    }
    for p in reasoner.list_products()
}

graph = getattr(reasoner, "graph", None) or getattr(reasoner, "g", None)
if graph is not None:
    captured["triple_count"] = len(graph)
    captured["predicates"] = sorted(
        {str(p).rsplit("/", 1)[-1].rsplit("#", 1)[-1] for _, p, _ in graph}
    )[:40]

# Product ids read out of the shipped ontology via list_products(), not guessed.
# ProductA is the rich case (5 standards, 2 steps); ProductB and ProductC each
# carry one standard, which makes them useful for checking the rule fires
# narrowly rather than returning everything it knows.
cases = [
    ("compliance_rich", "which compliance standards apply?", "ProductA"),
    ("compliance_single", "which compliance standards apply?", "ProductB"),
    ("compliance_wireless", "which compliance standards apply?", "ProductC"),
    ("edge_empty_query", "", "ProductA"),
    ("edge_unknown_product", "which standards apply?", "no_such_product"),
    ("edge_no_product", "which compliance standards are required?", None),
]
for name, q, product in cases:
    entry = {}
    try:
        ans = sym.answer_symbolic(q, product=product, session="ref", domain="battery")
        if ans is None:
            entry = {"answer": None}
        else:
            entry = {
                "text": ans.text,
                "fired": ans.fired,
                "evidence": [list(e) for e in ans.evidence],
                "trace": {
                    "product": ans.trace.product,
                    "asserted": [list(t) for t in ans.trace.asserted],
                    "inferred": [list(t) for t in ans.trace.inferred],
                    "rules_fired": list(ans.trace.rules_fired),
                },
            }
    except Exception as exc:
        entry = {"__raised__": type(exc).__name__, "message": str(exc)[:200]}
    try:
        entry["fire_flag"] = sym.sym_fire_flags(q, product=product, domain="battery")
    except Exception as exc:
        entry["fire_flag"] = f"raised {type(exc).__name__}"
    captured[name] = entry

(out / "symbolic").mkdir(parents=True, exist_ok=True)
(out / "symbolic" / "reasoner_surface.json").write_text(
    json.dumps(captured, indent=2, sort_keys=True, default=str) + "\n"
)
print("ok")
"""


def _capture_llmmain(llmmain_root: pathlib.Path,
                     out: pathlib.Path) -> list[tuple[str, str, str]]:
    import subprocess

    proc = subprocess.run(
        [sys.executable, "-c", _LLMMAIN_PROBE, str(llmmain_root), str(out)],
        capture_output=True, text=True, timeout=300,
    )
    if proc.returncode == 0:
        return [("symbolic", "reasoner_surface", "ok")]
    tail = (proc.stderr or proc.stdout).strip().splitlines()
    return [("symbolic", "reasoner_surface", f"failed: {tail[-1][:90] if tail else '?'}")]


# -------------------------------------------------------------------- app mode
# Paths and request shapes read from the demo's own OpenAPI schema, not guessed.
# Cases marked llm=True call OpenAI. They are skipped unless --include-llm, because
# the oracle is a one-off and the running cost of this repo is meant to be zero.
APP_CASES: list[tuple[str, str, str, str, dict[str, Any] | None, bool]] = [
    # -- search: the reliability path, and the reason this oracle matters most
    ("search", "representative_carbon", "POST", "/api/search",
     {"q": "What is the carbon footprint of the Lexmark MX431adn?", "session": "ref"}, True),
    ("search", "representative_compliance", "POST", "/api/search",
     {"q": "Which compliance standards does ProductA require?", "product": "ProductA",
      "session": "ref"}, True),
    ("search", "edge_empty_query", "POST", "/api/search", {"q": "", "session": "ref"}, True),
    ("search", "edge_unanswerable", "POST", "/api/search",
     {"q": "What is the airspeed velocity of an unladen swallow?", "session": "ref"}, True),
    ("search", "suggestions", "GET", "/api/search/suggestions", None, False),

    # -- carbon: deterministic, no model in the loop
    ("carbon", "products", "GET", "/api/carbon/products", None, False),
    ("carbon", "representative_iphone15", "POST", "/api/carbon/calculate",
     {"product_id": "apple_iphone15_pro_128gb", "include_trace": True}, False),
    ("carbon", "representative_bev_pack", "POST", "/api/carbon/calculate",
     {"product_id": "generic_bev_pack_60kwh", "include_trace": True}, False),
    ("carbon", "edge_unknown_product", "POST", "/api/carbon/calculate",
     {"product_id": "no_such_product_at_all", "include_trace": True}, False),
    ("carbon", "edge_bootstrap_estimates", "POST", "/api/carbon/calculate",
     {"product_id": "fairphone_4", "use_bootstrap_estimates": True, "include_trace": True},
     False),

    # -- validate: suggest=False keeps the model out of it
    ("validate", "representative_valid", "POST", "/api/validate",
     {"dpp": {"schema_version": "1.0", "dpp_id": "ref-001",
              "product": {"name": "Reference product", "category": "battery"}},
      "suggest": False}, False),
    ("validate", "edge_empty_dpp", "POST", "/api/validate", {"dpp": {}, "suggest": False},
     False),
    ("validate", "edge_wrong_types", "POST", "/api/validate",
     {"dpp": {"schema_version": 1.0, "dpp_id": ["not", "a", "string"], "product": "a string"},
      "suggest": False}, False),

    # -- models: the 17-module catalogue and its routing
    ("models", "catalogue", "GET", "/api/ce-rise-models/catalog", None, False),
    ("models", "route_carbon_question", "POST", "/api/ce-rise-models/route",
     {"question": "What is the recycled content of this battery?"}, False),
    ("models", "edge_empty_question", "POST", "/api/ce-rise-models/route",
     {"question": ""}, False),

    # -- pef: the WP3 integration, all deterministic
    ("pef", "overview", "GET", "/api/pefdpp/overview", None, False),
    ("pef", "calculate", "POST", "/api/pefdpp/calculate", {}, False),
    ("pef", "value_chain", "GET", "/api/pefdpp/value-chain", None, False),
    ("pef", "competency_questions", "GET", "/api/pefdpp/competency-questions", None, False),
    ("pef", "edge_sparql_injection", "POST", "/api/pefdpp/sparql",
     {"query": "DELETE WHERE { ?s ?p ?o }", "limit": 5}, False),
    ("pef", "edge_unknown_activity", "GET", "/api/pefdpp/activity/no_such_activity", None,
     False),

    # -- synthesize: model in the loop
    ("synthesize", "representative_battery", "POST", "/api/synthesize",
     {"category": "battery", "brand": "ReferenceCo", "model_name": "REF-1"}, True),

    ("service", "settings", "GET", "/api/settings", None, False),
]


def capture_app(demo_root: pathlib.Path, out: pathlib.Path,
                include_llm: bool) -> list[tuple[str, str, str]]:
    """Drive the demo in-process with TestClient.

    In-process rather than over a socket because it needs no server lifecycle, no
    port, and no waiting — and it exercises the same routing and serialisation a
    real request would. Pass --http to go over the wire instead.
    """
    sys.path.insert(0, str(demo_root))
    os.chdir(demo_root)
    from fastapi.testclient import TestClient

    from backend.main import app  # type: ignore

    results: list[tuple[str, str, str]] = []
    with TestClient(app) as client:
        for area, case, method, path, body, needs_llm in APP_CASES:
            if needs_llm and not include_llm:
                results.append((area, case, "skipped (needs OpenAI; pass --include-llm)"))
                continue
            results.append((area, *record(out, area, case,
                                          _caller(client, method, path, body))))
    return results


def capture_http(base: str, out: pathlib.Path,
                 include_llm: bool) -> list[tuple[str, str, str]]:
    import httpx

    results: list[tuple[str, str, str]] = []
    with httpx.Client(base_url=base.rstrip("/"), timeout=180.0) as client:
        for area, case, method, path, body, needs_llm in APP_CASES:
            if needs_llm and not include_llm:
                results.append((area, case, "skipped (needs OpenAI; pass --include-llm)"))
                continue
            results.append((area, *record(out, area, case,
                                          _caller(client, method, path, body))))
    return results


def _caller(client: Any, method: str, path: str, body: Any) -> Any:
    def call() -> dict[str, Any]:
        resp = (client.request(method, path, json=body) if body is not None
                else client.request(method, path))
        try:
            payload = resp.json()
        except Exception:  # noqa: BLE001
            payload = {"__text__": resp.text[:4000]}
        # Status is part of the contract: a 422 that becomes a 500 is a regression
        # even if the body looks similar.
        return {"status": resp.status_code, "body": payload}

    return call


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--http", metavar="URL",
                    help="drive a running demo over the wire instead of in-process")
    ap.add_argument("--services-only", action="store_true",
                    help="capture service objects only, skipping the HTTP layer")
    ap.add_argument("--include-llm", action="store_true",
                    help="also capture the endpoints that call OpenAI (about 6 calls "
                         "on gpt-4o-mini). Off by default: this repo is meant to cost "
                         "nothing to run.")
    ap.add_argument("--demo-root", type=pathlib.Path,
                    default=pathlib.Path(__file__).resolve().parents[2] / "CE-RISE-Demo")
    ap.add_argument("--llmmain-root", type=pathlib.Path,
                    default=pathlib.Path(__file__).resolve().parents[2])
    ap.add_argument("--out", type=pathlib.Path,
                    default=pathlib.Path(__file__).resolve().parents[1] / "tests" / "reference")
    args = ap.parse_args()

    args.out = args.out.resolve()
    args.demo_root = args.demo_root.resolve()
    args.llmmain_root = args.llmmain_root.resolve()
    args.out.mkdir(parents=True, exist_ok=True)
    try:
        if args.services_only:
            results = capture_services(args.demo_root, args.llmmain_root, args.out)
        elif args.http:
            results = capture_http(args.http, args.out, args.include_llm)
        else:
            results = capture_services(args.demo_root, args.llmmain_root, args.out)
            results += capture_app(args.demo_root, args.out, args.include_llm)
    except Exception:  # noqa: BLE001
        traceback.print_exc()
        return 1

    width = max((len(f"{a}/{c}") for a, c, _ in results), default=20)
    for area, case, status in results:
        print(f"  {area + '/' + case:<{width}}  {status}")
    print(f"\n{len(results)} records → {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
