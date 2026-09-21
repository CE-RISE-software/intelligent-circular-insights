# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2026 CE-RISE consortium
"""``ImpactEngine`` over the deterministic CSV-factor engine.

Normal mode's impact path: flat product profiles and published emission factors.
Fast, broad, shallow — the counterpart to the graph-solved assessment CE-RISE mode
mounts. Both answer the same question, so the core sees one shape.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import asdict, dataclass
from pathlib import Path

from ici_core.domain.envelope import ProvenanceKind, ProvenanceLink
from ici_core.domain.errors import CapabilityError
from ici_core.domain.impact import (
    ImpactContribution,
    ImpactRequest,
    ImpactResult,
    Provenance,
    SubjectRef,
)
from ici_substrates.carbon.engine import CarbonCalculationService
from ici_substrates.paths import CARBON_ROOT


@dataclass
class CsvFactorImpactEngine:
    """Implements ``ImpactEngine`` for Normal mode."""

    service: CarbonCalculationService

    @classmethod
    def from_data_root(cls, data_root: Path | None = None) -> CsvFactorImpactEngine:
        return cls(CarbonCalculationService(data_root or CARBON_ROOT))

    # -- ImpactEngine -------------------------------------------------------
    def assess(self, subject: SubjectRef, req: ImpactRequest) -> ImpactResult:
        if req.indicator not in ("climate_change", "carbon", ""):
            raise CapabilityError(
                capability=f"impact indicator {req.indicator!r}",
                mode="normal",
                reason=(
                    "the CSV factor engine covers climate change only; mount the "
                    "CE-RISE profile for the full EF 3.1 indicator set"
                ),
            )

        payload = asdict(self.service.calculate(subject.id))
        total = float(payload.get("total_kg_co2e") or 0.0)

        # stage_results is keyed by stage name, not a list — preserved as the
        # engine returns it rather than reshaped, so the numbers stay traceable
        # to the oracle.
        contributions = tuple(
            ImpactContribution(
                label=str(stage.get("stage", name)),
                amount=float(stage.get("total_kg_co2e") or 0.0),
                unit="kg CO2e",
                share=(float(stage["total_kg_co2e"]) / total)
                if total and stage.get("total_kg_co2e")
                else None,
                # Estimated inputs are this engine's equivalent of a proxy factor,
                # and are badged the same way so a reader is never misled about
                # which numbers are measured and which are inferred.
                is_proxy=bool(stage.get("estimated_inputs")),
            )
            for name, stage in sorted(payload.get("stage_results", {}).items())
        )

        band = payload.get("uncertainty_range_kg_co2e") or {}
        uncertainty = (
            (float(band["low"]), float(band["high"])) if {"low", "high"} <= set(band) else None
        )

        diagnostics = [str(w) for w in payload.get("warnings", [])]
        diagnostics += [f"missing input: {m}" for m in payload.get("missing_inputs", [])]

        return ImpactResult(
            subject=subject,
            indicator="climate_change",
            total=total,
            unit="kg CO2e",
            functional_unit=req.functional_unit or "product lifecycle",
            contributions=contributions,
            uncertainty=uncertainty,
            data_quality=payload.get("uncertainty_pct"),
            diagnostics=tuple(diagnostics),
            uses_proxy_factors=bool(payload.get("used_bootstrap_estimates")),
        )

    def subjects(self) -> Sequence[SubjectRef]:
        """Read off the profile directory, never a hard-coded list."""
        root = self.service.products_dir
        if not root.is_dir():
            return ()
        return tuple(
            SubjectRef(id=path.stem, kind="product") for path in sorted(root.glob("*.json"))
        )

    def explain(self, result: ImpactResult, target: str) -> Provenance:
        payload = asdict(self.service.calculate(result.subject.id))

        links: list[ProvenanceLink] = []
        for item in payload.get("provenance", []):
            refs = item.get("source_refs") or []
            links.append(
                ProvenanceLink(
                    kind=ProvenanceKind.CALC_STEP,
                    ref=str(item.get("field_name") or "step"),
                    source_file=str(refs[0]) if refs else None,
                    excerpt=(
                        f"{item.get('label')} = {item.get('value')} "
                        f"{item.get('unit', '')} ({item.get('method')})"
                    ).strip()[:200],
                )
            )

        # Every factor actually applied, from the per-stage traces.
        for stage in payload.get("stage_results", {}).values():
            links.extend(
                ProvenanceLink(
                    kind=ProvenanceKind.CALC_STEP,
                    ref=str(trace.get("item_id") or trace.get("label") or "factor"),
                    excerpt=(
                        f"{trace.get('activity_value')} {trace.get('activity_unit', '')} "
                        f"x factor -> {trace.get('total_kg_co2e', '')}"
                    ).strip()[:200],
                )
                for trace in stage.get("traces", [])
            )

        return Provenance(
            target=target,
            links=tuple(links),
            arithmetic=(
                f"{len(result.contributions)} life cycle stages summed to "
                f"{result.total:.6f} {result.unit}"
            ),
            scaling_chain=tuple(c.label for c in result.contributions),
        )
