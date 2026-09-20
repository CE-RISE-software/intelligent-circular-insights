"""PEFDPP LCA engine — computes a PEF-style footprint straight from the RDF graph.

WHAT THIS DOES
--------------
1. Reads the PEFStudy: functional unit, reference flow, system boundary,
   product system and the life cycle stage of every activity.
2. Solves the foreground supply chain by demand-driven expansion. Each
   activity is scaled by (demand / its determining flow amount) and its inputs
   are pushed as new demands. This is a sequential Leontief solve over the
   graph — the linkages come from the RDF, not from a hand-built table.
3. Splits every scaled exchange into one of four kinds:
     - foreground  : produced by another activity in the graph → recurse
     - elementary  : an EF 3.1 flow → characterise with a real EF 3.1 factor
     - background  : ecoinvent-referenced → apply a labelled proxy factor,
                     with the electricity factor chosen from the activity's
                     own act:hasGeography
     - CFF waste   : a waste flow carrying an EndOfLifeScenario → apply the
                     PEF Circular Footprint Formula using the graph's own
                     R2/R3, virgin equivalent, recycling and disposal flows
4. Aggregates to the functional unit, by life cycle stage, by activity, by
   dataset and by flow role, and computes a contribution-weighted DQR.

WHAT THIS DOES NOT DO
---------------------
It does not produce an EF-compliant declaration. The case study graph carries
no background inventory (ecoinvent 3.12 is licensed and referenced by UUID
only), so background impacts come from a documented proxy factor pack. Every
such number is tagged ``tier`` and ``is_proxy`` and is rendered with a badge in
the UI. Point ``factors/background_factors.json`` at a licensed EF-node extract
and the same engine produces a compliant result.

Port note
---------
**Carried over, not rewritten.** Its results are the visible output of the WP3
integration and are pinned by golden tests — 5,387 triples, weighted DQR 1.218988,
five actor datasets with PEF "most relevant" flags. A port is the wrong moment to
move them.

``factors_root`` is separate from ``data_root`` because this repository keeps
ontologies under ``ontology/`` and data under ``data/``; the demo had both in one
directory, which worked but conflated a vocabulary with a dataset. It falls back to
``data_root``, so the original layout still works.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ici_substrates.pefdpp.graph import (
    ActivityRecord,
    FlowRecord,
    PefdppGraphService,
)

# --- unit handling -----------------------------------------------------------

UNIT_ALIASES = {
    "kilogram": "kg",
    "kg": "kg",
    "kilowatthour": "kWh",
    "kwh": "kWh",
    "megajoule": "MJ",
    "mj": "MJ",
    "tonnekilometre": "tkm",
    "tkm": "tkm",
    "cubicmetre": "m3",
    "m3": "m3",
    "item": "item",
    "unit": "item",
    "kilometre": "km",
    "year": "year",
}

#: Conversions applied when a flow is measured in a different unit from its
#: factor. Water is the only case in this study (m3 vs kg).
UNIT_CONVERSIONS = {("m3", "kg"): 1000.0, ("kg", "m3"): 0.001}

LIFE_CYCLE_STAGE_ORDER = [
    "RawMaterialAcquisition",
    "Manufacturing",
    "Distribution",
    "Use",
    "EndOfLife",
]

#: Classifies a background flow by what it does, so a reader can see how much
#: of the footprint is materials vs energy vs shaping vs logistics.
FLOW_ROLES = {
    "electricity": ("ElectricityMediumVoltage", "ElectricityLowVoltage"),
    "process_heat": (
        "HeatDistrictOrIndustrialNaturalGas",
        "SteamFromNaturalGas",
        "ThermalEnergyFromNaturalGas",
        "ThermalEnergyFromLightFuelOil",
    ),
    "transport": ("TransportFreightLorry3575MetricTonDieselEURO4",),
    "shaping": (
        "SheetRollingAluminium",
        "SheetRollingCopper",
        "SheetRollingSteel",
        "ImpactExtrusionOfAluminium1Stroke",
        "ExtrusionPlasticFilm",
        "InjectionMoulding",
    ),
    "waste_treatment": (
        "LandfillInertWaste",
        "LandifllOfInertSlag",
        "WastewaterTreatment",
        "CoolantWaterGlycolResidualTreatment",
        "TreatmentOfElectronicsScrapMetalsRecoveryInCopperSmelter",
    ),
}


def _norm_unit(unit: str) -> str:
    return UNIT_ALIASES.get((unit or "").strip().lower(), (unit or "").strip())


def _role_of(flow_type: str) -> str:
    for role, members in FLOW_ROLES.items():
        if flow_type in members:
            return role
    return "material"


# --- result records ----------------------------------------------------------


@dataclass
class ExchangeResult:
    """One scaled exchange, fully traced. This is the unit of provenance:
    every number in the UI is the sum of a set of these, and each one names the
    exact flow IRI and TTL file it came from."""

    flow_uri: str
    flow_id: str
    flow_type: str
    flow_type_label: str
    flow_class: str
    contextual_label: str
    direction: str
    activity: str
    activity_label: str
    activity_geography: str
    dataset: str
    life_cycle_stage: str
    role: str
    unit_amount: float | None  # amount per unit of the activity
    unit: str
    activity_scale: float  # how many activity units the FU needs
    scaled_amount: float | None  # unit_amount x activity_scale
    resolution: str  # foreground | elementary | background | cff | unresolved
    factor_value: float | None = None
    factor_unit: str = ""
    factor_tier: str = ""
    factor_source: str = ""
    factor_key: str = ""
    is_proxy: bool = False
    uncertainty_pct: float | None = None
    impacts: dict[str, float] = field(default_factory=dict)
    formula: str = ""
    notes: list[str] = field(default_factory=list)
    source_file: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {k: v for k, v in self.__dict__.items()}


class PefdppLcaService:
    """Turns the PEFDPP graph into numbers, with a trace behind every one."""

    MAX_DEPTH = 40

    def __init__(
        self,
        data_root: Path | None = None,
        graph_service: PefdppGraphService | None = None,
        factors_root: Path | None = None,
    ) -> None:
        """
        ``data_root`` is where the TTL lives; ``factors_root`` is where the JSON
        factor packs live. They are separate arguments because this repository keeps
        ontologies under ``ontology/`` and data under ``data/`` — the demo had both
        under one directory, which worked but conflated a vocabulary with a dataset.
        ``factors_root`` falls back to ``data_root`` so the original layout still works.
        """
        if data_root is None and graph_service is None:
            raise ValueError("PefdppLcaService needs a data_root or a graph_service")
        self.data_root = Path(data_root) if data_root else graph_service.data_root
        self.factors_root = Path(factors_root) if factors_root else self.data_root
        self.graph_service = graph_service or PefdppGraphService(self.data_root)
        self._bg: dict[str, Any] | None = None
        self._cf: dict[str, Any] | None = None
        self._scenario: dict[str, Any] = {}

    # -- factor packs ---------------------------------------------------------

    @property
    def background(self) -> dict[str, Any]:
        if self._bg is None:
            path = self.factors_root / "factors" / "background_factors.json"
            self._bg = json.loads(path.read_text())
        return self._bg

    @property
    def characterisation(self) -> dict[str, Any]:
        if self._cf is None:
            path = self.factors_root / "factors" / "ef31_characterisation_factors.json"
            self._cf = json.loads(path.read_text())
        return self._cf

    def impact_categories(self) -> list[dict[str, Any]]:
        return self.characterisation.get("impact_categories", [])

    # -- factor resolution ----------------------------------------------------

    def _grid_factor(self, geography: str, low_voltage: bool) -> dict[str, Any]:
        grids = self.background["electricity_grids"]
        key = (
            geography if geography in grids and not geography.startswith("_") else grids["_default"]
        )
        override = self._scenario.get("electricity_geography")
        overridden = False
        if override and override in grids and not override.startswith("_") and override != key:
            key, overridden = override, True
        entry = dict(grids[key])
        value = entry["value"]
        note = (
            f"grid mix for {key} — SCENARIO OVERRIDE, the graph says act:hasGeography = {geography}"
            if overridden
            else f"grid mix for {key}, selected from act:hasGeography in the graph"
        )
        if low_voltage:
            uplift = grids.get("low_voltage_uplift", 1.0)
            value *= uplift
            note += f"; x{uplift} for low-voltage distribution losses"
        entry.update({"value": value, "unit": "kWh", "resolved_geography": key, "note": note})
        return entry

    def _background_factor(self, flow_type: str, geography: str) -> dict[str, Any] | None:
        if flow_type == "ElectricityMediumVoltage":
            return self._grid_factor(geography, low_voltage=False)
        if flow_type == "ElectricityLowVoltage":
            return self._grid_factor(geography, low_voltage=True)
        entry = self.background["flow_factors"].get(flow_type)
        if not entry or not isinstance(entry, dict):
            return None
        return dict(entry)

    def _elementary_factors(self, flow_type: str) -> dict[str, Any] | None:
        return self.characterisation["elementary_flows"].get(flow_type)

    @staticmethod
    def _convert(amount: float, from_unit: str, to_unit: str) -> tuple[float | None, str]:
        f, t = _norm_unit(from_unit), _norm_unit(to_unit)
        if f == t:
            return amount, ""
        conv = UNIT_CONVERSIONS.get((f, t))
        if conv is None:
            return None, f"no conversion from {f} to {t}"
        return amount * conv, f"converted {f}->{t} (x{conv:g})"

    # -- supply-chain solve ---------------------------------------------------

    def _solve(
        self,
        demand_flow_type: str,
        demand_amount: float,
        demand_unit: str,
        stage_map: dict[str, str],
        origin: str,
        scales: dict[str, float],
        exchanges: list[ExchangeResult],
        diagnostics: list[dict[str, str]],
        depth: int = 0,
        path: tuple[str, ...] | None = None,
    ) -> None:
        """Expand one demand for a foreground-produced flow type."""
        gs = self.graph_service
        path = path or ()
        if depth > self.MAX_DEPTH:
            diagnostics.append(
                {
                    "severity": "error",
                    "code": "max_depth",
                    "message": f"Supply-chain expansion exceeded {self.MAX_DEPTH} levels at "
                    f"'{demand_flow_type}'. The graph may contain a cycle.",
                }
            )
            return

        act_id = gs.producers.get(demand_flow_type)
        if act_id is None:
            diagnostics.append(
                {
                    "severity": "error",
                    "code": "no_producer",
                    "message": f"No activity in the graph produces '{demand_flow_type}' as its "
                    f"determining flow, so the demand of {demand_amount:g} {demand_unit} "
                    f"could not be expanded.",
                }
            )
            return
        if act_id in path:
            diagnostics.append(
                {
                    "severity": "warning",
                    "code": "cycle",
                    "message": f"Cycle detected: '{act_id}' already appears in the current expansion "
                    f"path ({' -> '.join(path)}). Expansion stopped to keep the solve finite.",
                }
            )
            return

        act = gs.activities[act_id]
        det_amount = act.determining_amount or 0.0
        if det_amount == 0:
            diagnostics.append(
                {
                    "severity": "error",
                    "code": "zero_determining_flow",
                    "message": f"Activity '{act_id}' has a determining flow amount of 0; it cannot be scaled.",
                }
            )
            return

        amt, note = self._convert(demand_amount, demand_unit, act.determining_unit)
        if amt is None:
            diagnostics.append(
                {
                    "severity": "error",
                    "code": "unit_mismatch",
                    "message": f"Demand for '{demand_flow_type}' is in {demand_unit} but "
                    f"'{act_id}' is denominated in {act.determining_unit}: {note}.",
                }
            )
            return

        scale = amt / det_amount
        scales[act_id] = scales.get(act_id, 0.0) + scale
        stage = stage_map.get(act_id, "Unassigned")
        new_path = path + (act_id,)

        for flow in act.inputs + act.outputs:
            if flow.is_determining:
                continue
            self._handle_flow(
                flow,
                act,
                scale,
                stage,
                stage_map,
                origin,
                scales,
                exchanges,
                diagnostics,
                depth,
                new_path,
            )

    def _handle_flow(
        self,
        flow: FlowRecord,
        act: ActivityRecord,
        scale: float,
        stage: str,
        stage_map: dict[str, str],
        origin: str,
        scales: dict[str, float],
        exchanges: list[ExchangeResult],
        diagnostics: list[dict[str, str]],
        depth: int,
        path: tuple[str, ...],
    ) -> None:
        gs = self.graph_service
        amount = flow.amount
        scaled = (amount or 0.0) * scale

        base = dict(
            flow_uri=flow.uri,
            flow_id=flow.id,
            flow_type=flow.flow_type,
            flow_type_label=flow.flow_type_label,
            flow_class=flow.flow_class,
            contextual_label=flow.contextual_label,
            direction=flow.direction,
            activity=act.id,
            activity_label=act.label,
            activity_geography=act.geography,
            dataset=act.dataset,
            life_cycle_stage=stage,
            role=_role_of(flow.flow_type),
            unit_amount=amount,
            unit=flow.unit,
            activity_scale=scale,
            scaled_amount=scaled,
            source_file=flow.source_file,
        )

        # 1. produced by another foreground activity → recurse
        if flow.flow_type in gs.producers:
            producer = gs.producers[flow.flow_type]
            if flow.direction == "output":
                # an output that another activity treats (e.g. cells -> pyrometallurgy)
                exchanges.append(
                    ExchangeResult(
                        **base,
                        resolution="foreground",
                        formula=f"routed to '{producer}' for treatment",
                    )
                )
                self._solve(
                    flow.flow_type,
                    scaled,
                    flow.unit,
                    stage_map,
                    origin,
                    scales,
                    exchanges,
                    diagnostics,
                    depth + 1,
                    path,
                )
                return
            exchanges.append(
                ExchangeResult(**base, resolution="foreground", formula=f"supplied by '{producer}'")
            )
            self._solve(
                flow.flow_type,
                scaled,
                flow.unit,
                stage_map,
                origin,
                scales,
                exchanges,
                diagnostics,
                depth + 1,
                path,
            )
            return

        # 2. elementary flow → real EF 3.1 characterisation
        if flow.flow_class == "ElementaryFlow":
            self._characterise_elementary(base, flow, scaled, exchanges, diagnostics)
            return

        # 3. waste flow with a Circular Footprint Formula scenario
        if flow.eol_scenario and flow.direction == "output":
            self._apply_cff(base, flow, scaled, act, exchanges, diagnostics)
            return

        # 4. background flow → proxy factor
        self._characterise_background(base, flow, scaled, act, exchanges, diagnostics)

    def _characterise_elementary(
        self,
        base: dict[str, Any],
        flow: FlowRecord,
        scaled: float,
        exchanges: list[ExchangeResult],
        diagnostics: list[dict[str, str]],
    ) -> None:
        entry = self._elementary_factors(flow.flow_type)
        if entry is None:
            exchanges.append(
                ExchangeResult(
                    **base,
                    resolution="unresolved",
                    factor_key=flow.flow_type,
                    notes=[
                        f"Elementary flow '{flow.flow_type_label}' is not in the bundled EF 3.1 "
                        f"factor set. Reported as uncharacterised rather than estimated."
                    ],
                )
            )
            diagnostics.append(
                {
                    "severity": "info",
                    "code": "uncharacterised_elementary",
                    "message": f"Elementary flow '{flow.flow_type_label}' has no bundled "
                    f"characterisation factor.",
                }
            )
            return

        factors = entry.get("factors", {})
        if not factors and entry.get("confidence") == "not_bundled":
            diagnostics.append(
                {
                    "severity": "info",
                    "code": "cf_not_bundled",
                    "message": f"'{entry['label']}' is characterised in EF 3.1 but its factor is not "
                    f"bundled here; the flow is reported uncharacterised, not estimated.",
                }
            )
        # An output to the environment is an emission (+); an input is an extraction.
        sign = 1.0 if flow.direction == "output" else -1.0
        impacts = {cat: sign * scaled * cf for cat, cf in factors.items()}
        note = entry.get("note", "")
        exchanges.append(
            ExchangeResult(
                **base,
                resolution="elementary",
                factor_key=flow.flow_type,
                factor_value=factors.get("ClimateChange"),
                factor_unit="per kg",
                factor_tier="EF3.1",
                factor_source=self.characterisation["meta"]["source"],
                is_proxy=False,
                impacts=impacts,
                formula=(
                    f"{scaled:.6g} kg {entry['label']} x EF 3.1 CF"
                    if factors
                    else f"{scaled:.6g} kg {entry['label']} — no CF applies"
                ),
                notes=[note] if note else [],
            )
        )

    def _characterise_background(
        self,
        base: dict[str, Any],
        flow: FlowRecord,
        scaled: float,
        act: ActivityRecord,
        exchanges: list[ExchangeResult],
        diagnostics: list[dict[str, str]],
    ) -> None:
        entry = self._background_factor(flow.flow_type, act.geography)
        if entry is None:
            exchanges.append(
                ExchangeResult(
                    **base,
                    resolution="unresolved",
                    factor_key=flow.flow_type,
                    notes=[
                        f"No background factor for '{flow.flow_type_label}'. Excluded from the "
                        f"total rather than guessed."
                    ],
                )
            )
            diagnostics.append(
                {
                    "severity": "warning",
                    "code": "missing_background_factor",
                    "message": f"No background factor for '{flow.flow_type_label}' "
                    f"({flow.flow_type}); its contribution is missing from the total.",
                }
            )
            return

        amt, conv_note = self._convert(scaled, flow.unit, entry.get("unit", "kg"))
        if amt is None:
            exchanges.append(
                ExchangeResult(
                    **base,
                    resolution="unresolved",
                    factor_key=flow.flow_type,
                    notes=[
                        f"Unit mismatch: flow is in {flow.unit}, factor is per "
                        f"{entry.get('unit')} ({conv_note})."
                    ],
                )
            )
            diagnostics.append(
                {
                    "severity": "warning",
                    "code": "unit_mismatch",
                    "message": f"'{flow.flow_type_label}': {conv_note}.",
                }
            )
            return

        # An input carries its upstream burden; an output sent for treatment also
        # carries a burden (the treatment service is consumed, not produced).
        value = amt * entry["value"]
        notes = []
        if conv_note:
            notes.append(conv_note)
        if entry.get("note"):
            notes.append(entry["note"])
        notes = [n for n in notes if n]

        exchanges.append(
            ExchangeResult(
                **base,
                resolution="background",
                factor_key=flow.flow_type,
                factor_value=entry["value"],
                factor_unit=f"kg CO2e/{entry.get('unit', 'kg')}",
                factor_tier=entry.get("tier", "?"),
                factor_source=entry.get("source", ""),
                is_proxy=True,
                uncertainty_pct=entry.get("uncertainty_pct"),
                impacts={"ClimateChange": value},
                formula=f"{amt:.6g} {entry.get('unit', 'kg')} x {entry['value']:g} kg CO2e/"
                f"{entry.get('unit', 'kg')} = {value:.6g} kg CO2e",
                notes=notes,
            )
        )

    # -- Circular Footprint Formula ------------------------------------------

    def _apply_cff(
        self,
        base: dict[str, Any],
        flow: FlowRecord,
        scaled: float,
        act: ActivityRecord,
        exchanges: list[ExchangeResult],
        diagnostics: list[dict[str, str]],
    ) -> None:
        """PEF Circular Footprint Formula, end-of-life terms.

            (1-A) * R2 * (Erec_EoL - Ev* * Qs/Qp)      recycling burden and credit
          + (1-R2-R3) * ED                             disposal of the remainder

        R2, R3, the virgin equivalent, the recycling flow and the disposal flow all
        come from flow:hasEndOfLifeScenario in the graph. A and Qs/Qp are PEF
        defaults, taken from the factor pack because the case study does not
        declare them.
        """
        sc = flow.eol_scenario or {}
        defaults = self.background["cff_defaults"]
        r2 = sc.get("recycling_rate_R2")
        r3 = sc.get("energy_recovery_rate_R3") or 0.0
        if r2 is None:
            diagnostics.append(
                {
                    "severity": "warning",
                    "code": "cff_incomplete",
                    "message": f"'{flow.flow_type_label}' declares an EndOfLifeScenario but no "
                    f"recycling rate; CFF not applied.",
                }
            )
            exchanges.append(
                ExchangeResult(
                    **base,
                    resolution="unresolved",
                    notes=["EndOfLifeScenario without a recycling rate."],
                )
            )
            return

        a_default = defaults["A"]
        if flow.flow_type in defaults.get("A_polymer", {}).get("applies_to", []):
            a_default = defaults["A_polymer"]
        a = a_default["value"]
        qs_qp = defaults["Qs_Qp"]["value"]
        r2_override = self._scenario.get("recycling_rate")
        r2_note = ""
        if r2_override is not None:
            try:
                r2_new = max(0.0, min(1.0, float(r2_override)))
                r2_note = (
                    f"R2 overridden to {r2_new:g} by scenario; the graph declares "
                    f"{r2:g} in flow:recyclingRate."
                )
                r2 = r2_new
            except (TypeError, ValueError):
                pass

        def gwp_of(ft: str) -> tuple[float | None, dict[str, Any]]:
            e = self._background_factor(ft, act.geography) if ft else None
            return (e["value"] if e else None), (e or {})

        ev, ev_e = gwp_of(sc.get("virgin_equivalent", ""))
        erec, erec_e = gwp_of(sc.get("recycling_flow_type", ""))
        ed, _ed_explanation = gwp_of(sc.get("disposal_flow_type", ""))

        missing = [
            n
            for n, v in (("virgin equivalent", ev), ("recycling process", erec), ("disposal", ed))
            if v is None
        ]
        if missing:
            diagnostics.append(
                {
                    "severity": "warning",
                    "code": "cff_missing_factor",
                    "message": f"CFF for '{flow.flow_type_label}': no factor for "
                    f"{', '.join(missing)}; those terms are treated as zero.",
                }
            )
        ev = ev or 0.0
        erec = erec or 0.0
        ed = ed or 0.0

        recycling_term = (1 - a) * r2 * (erec - ev * qs_qp)
        disposal_term = max(0.0, 1 - r2 - r3) * ed
        per_kg = recycling_term + disposal_term
        total = scaled * per_kg

        exchanges.append(
            ExchangeResult(
                **base,
                resolution="cff",
                factor_key=flow.flow_type,
                factor_value=per_kg,
                factor_unit="kg CO2e/kg",
                factor_tier="CFF",
                is_proxy=True,
                factor_source=(
                    "PEF Circular Footprint Formula; R2/R3 and the virgin, recycling and "
                    "disposal flows read from the graph, A and Qs/Qp from PEF defaults"
                ),
                uncertainty_pct=max(
                    ev_e.get("uncertainty_pct", 0) or 0, erec_e.get("uncertainty_pct", 0) or 0
                )
                or None,
                impacts={"ClimateChange": total},
                formula=(
                    f"(1-A={1 - a:g}) x R2={r2:g} x (Erec={erec:g} - Ev={ev:g} x Qs/Qp={qs_qp:g}) "
                    f"+ (1-R2-R3={max(0.0, 1 - r2 - r3):g}) x Ed={ed:g} "
                    f"= {per_kg:.6g} kg CO2e/kg, x {scaled:.6g} kg = {total:.6g} kg CO2e"
                ),
                notes=[
                    f"A = {a:g} ({a_default['source']})",
                    f"Qs/Qp = {qs_qp:g} ({defaults['Qs_Qp']['source']})",
                    f"R1 (recycled content) = {defaults['R1']['value']:g}: {defaults['R1']['source']}",
                    "A negative value is a credit for material recovered and displacing virgin production.",
                ]
                + ([r2_note] if r2_note else []),
            )
        )

    # -- system closure -------------------------------------------------------

    def _closure_rules(self, study: dict[str, Any], ref_mass_kg: float) -> list[dict[str, Any]]:
        """Activity links that the ProductSystem declares but that no exchange in the
        graph drives. These are real gaps in the ABox; each is closed by an explicit,
        named, switchable assumption rather than silently."""
        return [
            {
                "id": "eol_closure",
                "flow_type": "EoLBatteryDisassembly",
                "amount": ref_mass_kg,
                "unit": "Kilogram",
                "default_on": True,
                "title": "End-of-life closure",
                "why": (
                    "The ProductSystem declares AL_BatteryDisassembly, AL_BatteryCellTreatment "
                    "and AL_MetalTreatment in the EndOfLife stage, but no exchange in the graph "
                    "sends the pack to disassembly — the boundary between the manufacturer's "
                    "DPP and the recycler's dataset is not wired up."
                ),
                "assumption": (
                    "Every kilogram of pack delivered to the customer eventually enters "
                    "disassembly, per the CFB-EV cradle-to-grave boundary (§4)."
                ),
            },
            {
                "id": "brazing_closure",
                "flow_type": "BrazingServiceForBatteryCase",
                "amount": ref_mass_kg / 165.0,
                "unit": "Item",
                "default_on": True,
                "title": "Brazing service closure",
                "why": (
                    "The ProductSystem declares AL_BrazingService, and the paper describes the "
                    "brazing of the cooling plate as an input to battery production, but no "
                    "activity in the graph consumes ft:BrazingServiceForBatteryCase."
                ),
                "assumption": (
                    "One brazed cooling plate per 165 kg battery pack (the pack mass in "
                    "Crenna et al. 2021), i.e. 1/165 of a brazing service per kg of pack. "
                    "The brazing dataset is denominated in batches of 70 items."
                ),
            },
        ]

    # -- main entry point -----------------------------------------------------

    def calculate(
        self,
        study_id: str | None = None,
        closures: dict[str, bool] | None = None,
        scenario: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        gs = self.graph_service
        study = gs.study(study_id)
        if not study:
            raise ValueError("No ps:PEFStudy found in the graph.")
        self._scenario = dict(scenario or {})

        fu = study.get("functional_unit", {})
        conv = fu.get("rf_to_fu_conversion")
        fu_amount = (fu.get("how_much_provided") or {}).get("value") or 1.0
        fu_unit = (fu.get("how_much_provided") or {}).get("unit") or ""
        ref_ft = fu.get("reference_flow_type")

        diagnostics: list[dict[str, str]] = []
        if conv is None:
            raise ValueError(
                "The functional unit declares no ps:RFtoFUConversion, so the "
                "reference flow cannot be scaled to the functional unit."
            )
        if not ref_ft:
            raise ValueError("The functional unit declares no reference flow.")

        # demand of the reference flow needed for one functional unit
        ref_mass = conv * fu_amount
        stage_map = (study.get("product_system") or {}).get("stage_map", {})

        scales: dict[str, float] = {}
        exchanges: list[ExchangeResult] = []

        self._solve(
            ref_ft,
            ref_mass,
            "Kilogram",
            stage_map,
            "reference_flow",
            scales,
            exchanges,
            diagnostics,
        )

        # closure rules for declared-but-unwired activity links
        closures = closures or {}
        applied_closures: list[dict[str, Any]] = []
        for rule in self._closure_rules(study, ref_mass):
            enabled = closures.get(rule["id"], rule["default_on"])
            rule = {**rule, "applied": bool(enabled)}
            applied_closures.append(rule)
            if not enabled:
                continue
            before = len(exchanges)
            self._solve(
                rule["flow_type"],
                rule["amount"],
                rule["unit"],
                stage_map,
                rule["id"],
                scales,
                exchanges,
                diagnostics,
            )
            rule["exchanges_added"] = len(exchanges) - before

        self._orphan_diagnostics(study, scales, diagnostics)

        return self._assemble(
            study,
            fu,
            fu_amount,
            fu_unit,
            ref_mass,
            ref_ft,
            scales,
            exchanges,
            diagnostics,
            applied_closures,
        )

    def _orphan_diagnostics(
        self, study: dict[str, Any], scales: dict[str, float], diagnostics: list[dict[str, str]]
    ) -> None:
        links = (study.get("product_system") or {}).get("activity_links", [])
        declared = {l["activity"] for l in links}
        reached = set(scales)
        for a in sorted(declared - reached):
            diagnostics.append(
                {
                    "severity": "warning",
                    "code": "unreached_activity",
                    "message": f"'{a}' is declared in the ProductSystem but was never reached by the "
                    f"supply-chain solve — no exchange in the graph demands its output.",
                }
            )
        for a in sorted(reached - declared):
            diagnostics.append(
                {
                    "severity": "warning",
                    "code": "unlinked_activity",
                    "message": f"'{a}' contributes to the result but has no prs:ActivityLink, so it "
                    f"carries no life cycle stage.",
                }
            )
        stages = {l["life_cycle_stage"] for l in links}
        for s in ("RawMaterialAcquisition",):
            if s not in stages:
                diagnostics.append(
                    {
                        "severity": "info",
                        "code": "stage_not_populated",
                        "message": f"The CFB-EV declares a '{s}' stage, but no activity is linked to it: "
                        f"raw material acquisition is carried entirely by background flows, "
                        f"which inherit the stage of the activity that consumes them.",
                    }
                )

    # -- aggregation ----------------------------------------------------------

    def _assemble(
        self,
        study: dict[str, Any],
        fu: dict[str, Any],
        fu_amount: float,
        fu_unit: str,
        ref_mass: float,
        ref_ft: str,
        scales: dict[str, float],
        exchanges: list[ExchangeResult],
        diagnostics: list[dict[str, str]],
        closures: list[dict[str, Any]],
    ) -> dict[str, Any]:
        gs = self.graph_service
        cats = {c["id"]: c for c in self.impact_categories()}

        totals: dict[str, float] = {}
        by_stage: dict[str, dict[str, float]] = {}
        by_activity: dict[str, dict[str, Any]] = {}
        by_dataset: dict[str, dict[str, Any]] = {}
        by_role: dict[str, float] = {}
        by_resolution: dict[str, dict[str, Any]] = {}
        variance = 0.0  # for the proxy uncertainty band on climate change

        for ex in exchanges:
            res = by_resolution.setdefault(ex.resolution, {"count": 0, "climate_change": 0.0})
            res["count"] += 1
            for cat, val in ex.impacts.items():
                if val is None or (isinstance(val, float) and math.isnan(val)):
                    continue
                totals[cat] = totals.get(cat, 0.0) + val
                by_stage.setdefault(ex.life_cycle_stage, {})
                by_stage[ex.life_cycle_stage][cat] = (
                    by_stage[ex.life_cycle_stage].get(cat, 0.0) + val
                )
                a = by_activity.setdefault(
                    ex.activity,
                    {
                        "activity": ex.activity,
                        "label": ex.activity_label,
                        "geography": ex.activity_geography,
                        "dataset": ex.dataset,
                        "life_cycle_stage": ex.life_cycle_stage,
                        "scale": scales.get(ex.activity, 0.0),
                        "impacts": {},
                    },
                )
                a["impacts"][cat] = a["impacts"].get(cat, 0.0) + val
                d = by_dataset.setdefault(
                    ex.dataset or "(unassigned)",
                    {"dataset": ex.dataset or "(unassigned)", "impacts": {}},
                )
                d["impacts"][cat] = d["impacts"].get(cat, 0.0) + val
                if cat == "ClimateChange":
                    res["climate_change"] += val
                    by_role[ex.role] = by_role.get(ex.role, 0.0) + val
                    if ex.uncertainty_pct:
                        variance += (abs(val) * ex.uncertainty_pct / 100.0) ** 2

        cc = totals.get("ClimateChange", 0.0)
        band = math.sqrt(variance)
        band_worst = sum(
            abs(v) * (ex.uncertainty_pct or 0) / 100.0
            for ex in exchanges
            for c, v in ex.impacts.items()
            if c == "ClimateChange" and ex.uncertainty_pct
        )

        # -- coverage per impact category
        coverage: list[dict[str, Any]] = []
        for cid, cat in cats.items():
            computed = cid in totals
            n = sum(1 for ex in exchanges if cid in ex.impacts)
            if cid == "ClimateChange":
                status, note = (
                    "computed",
                    (
                        "Foreground elementary flows use real EF 3.1 factors; background flows use the "
                        "labelled proxy pack."
                    ),
                )
            elif computed:
                status, note = (
                    "partial",
                    (
                        "Computed for the elementary flows that appear directly in the foreground graph "
                        "only. Background contributions need an EF-compliant background dataset."
                    ),
                )
            else:
                status, note = (
                    "not_computed",
                    (
                        "Declared in ps:includesImpactCategory, but no bundled factor reaches it. "
                        "Requires the full EF 3.1 reference package plus a licensed background dataset."
                    ),
                )
            coverage.append(
                {
                    "id": cid,
                    "label": cat["label"],
                    "unit": cat["unit"],
                    "value": totals.get(cid),
                    "status": status,
                    "contributing_exchanges": n,
                    "note": note,
                    "regulated": cat.get("regulated", False),
                    "regulation_note": cat.get("regulation_note", ""),
                    "declared_in_scope": cid
                    in (study.get("scope") or {}).get("impact_categories", []),
                }
            )
        coverage.sort(
            key=lambda c: (c["status"] != "computed", c["status"] != "partial", c["label"])
        )

        # -- contribution-weighted data quality
        dq = self._weighted_dqr(by_dataset, cc)

        # -- top contributors, by absolute climate change
        contributors = sorted(
            (ex for ex in exchanges if "ClimateChange" in ex.impacts),
            key=lambda e: abs(e.impacts["ClimateChange"]),
            reverse=True,
        )

        stage_rows = []
        for s in LIFE_CYCLE_STAGE_ORDER + sorted(set(by_stage) - set(LIFE_CYCLE_STAGE_ORDER)):
            if s not in by_stage:
                continue
            v = by_stage[s].get("ClimateChange", 0.0)
            stage_rows.append(
                {
                    "stage": s,
                    "climate_change": v,
                    "share_pct": (v / cc * 100.0) if cc else 0.0,
                    "impacts": by_stage[s],
                }
            )

        pack_mass = 165.0
        per_kg = cc / ref_mass if ref_mass else None

        return {
            "study": study,
            "functional_unit": {
                **fu,
                "declared": (
                    f"{fu_amount:g} {fu_unit} — {fu.get('what_provided', '')} "
                    f"{fu.get('how_well_provided', '')}"
                ).strip(),
                "reference_flow_amount": ref_mass,
                "reference_flow_unit": "kg",
                "reference_flow_type": ref_ft,
                "explanation": (
                    f"{fu_amount:g} {fu_unit} of delivered energy needs {ref_mass:.6g} kg of "
                    f"battery pack (ps:RFtoFUConversion = {fu.get('rf_to_fu_conversion')}). "
                    f"Every number below is per {fu_amount:g} {fu_unit} unless labelled otherwise."
                ),
            },
            "headline": {
                "climate_change_per_fu": cc,
                "climate_change_unit": "kg CO2 eq",
                "fu_label": f"{fu_amount:g} {fu_unit}",
                "uncertainty_band": band,
                "uncertainty_pct": (band / abs(cc) * 100.0) if cc else None,
                "uncertainty_band_worst_case": band_worst,
                "uncertainty_pct_worst_case": (band_worst / abs(cc) * 100.0) if cc else None,
                "uncertainty_note": (
                    "The narrow band combines the proxy-factor uncertainties in quadrature, which "
                    "assumes they are independent. The worst case adds them linearly, which is what "
                    "applies if the factor pack is systematically biased in one direction. The true "
                    "uncertainty sits between the two."
                ),
                "climate_change_per_kg_pack": per_kg,
                "climate_change_per_pack": (per_kg * pack_mass) if per_kg else None,
                "pack_mass_kg": pack_mass,
                "pack_mass_note": (
                    "Pack mass from Crenna et al. (2021) as cited in the case study; "
                    "used only to restate the result in familiar units."
                ),
                "regulated_indicator": True,
                "compliance_status": "indicative — not an EF-compliant declaration",
            },
            "by_stage": stage_rows,
            "by_activity": sorted(
                by_activity.values(),
                key=lambda a: abs(a["impacts"].get("ClimateChange", 0.0)),
                reverse=True,
            ),
            "by_dataset": sorted(
                by_dataset.values(),
                key=lambda d: abs(d["impacts"].get("ClimateChange", 0.0)),
                reverse=True,
            ),
            "by_role": sorted(
                (
                    {"role": k, "climate_change": v, "share_pct": (v / cc * 100.0) if cc else 0.0}
                    for k, v in by_role.items()
                ),
                key=lambda r: abs(r["climate_change"]),
                reverse=True,
            ),
            "by_resolution": by_resolution,
            "impact_coverage": coverage,
            "data_quality": dq,
            "activity_scales": [
                {
                    "activity": a,
                    "scale": s,
                    "label": gs.activities[a].label if a in gs.activities else a,
                    "geography": gs.activities[a].geography if a in gs.activities else "",
                    "dataset": gs.activities[a].dataset if a in gs.activities else "",
                    "life_cycle_stage": (study.get("product_system") or {})
                    .get("stage_map", {})
                    .get(a, "Unassigned"),
                    "determining_flow_type": gs.activities[a].determining_flow_type
                    if a in gs.activities
                    else "",
                    "determining_unit": gs.activities[a].determining_unit
                    if a in gs.activities
                    else "",
                }
                for a, s in sorted(scales.items(), key=lambda kv: -kv[1])
            ],
            "top_contributors": [ex.as_dict() for ex in contributors[:30]],
            "exchanges": [ex.as_dict() for ex in exchanges],
            "exchange_count": len(exchanges),
            "closures": closures,
            "scenario": {
                "applied": dict(self._scenario),
                "available": {
                    "electricity_geography": {
                        "label": "Manufacturing electricity grid",
                        "description": (
                            "Override the grid factor for every activity. By default "
                            "each activity uses its own act:hasGeography from the graph "
                            "— cell and pack in NO, active materials in CN, brazing in "
                            "ES, recycling in RER."
                        ),
                        "options": [
                            k for k in self.background["electricity_grids"] if not k.startswith("_")
                        ],
                    },
                    "recycling_rate": {
                        "label": "End-of-life recycling rate (R2)",
                        "description": (
                            "Override flow:recyclingRate on every waste flow carrying a "
                            "CFF scenario. The graph declares 0.95 for metals and 0.5 "
                            "for polymers."
                        ),
                        "range": [0.0, 1.0],
                    },
                },
            },
            "diagnostics": diagnostics,
            "method": {
                "engine": "PEFDPP graph solve (sequential Leontief over act:inputOf / act:outputOf)",
                "characterisation": self.characterisation["meta"],
                "background": self.background["meta"],
                "honesty_note": (
                    "The foreground inventory, its linkages, the geographies, the CFF parameters "
                    "and the data-quality scores are all read from the RDF graph. The background "
                    "impact intensities are proxies from a documented factor pack, because the "
                    "case study references ecoinvent 3.12 by UUID without shipping it. Swap the "
                    "factor pack for a licensed EF-node extract and this becomes a compliant "
                    "calculation with no change to the engine."
                ),
            },
        }

    def _weighted_dqr(self, by_dataset: dict[str, dict[str, Any]], cc: float) -> dict[str, Any]:
        """PEF asks for data quality weighted towards the processes that matter.
        Weight each dataset's declared DQR by its share of the climate-change result."""
        gs = self.graph_service
        rows: list[dict[str, Any]] = []
        num = den = 0.0
        for ds_id, agg in by_dataset.items():
            ds = gs.datasets.get(ds_id)
            share_val = agg["impacts"].get("ClimateChange", 0.0)
            share = abs(share_val) / abs(cc) if cc else 0.0
            dqr = ds.dqr_overall if ds else None
            rows.append(
                {
                    "dataset": ds_id,
                    "title": ds.title if ds else ds_id,
                    "dataset_type": ds.dataset_type if ds else "",
                    "compliance_level": ds.compliance_level if ds else "",
                    "declared_dqr": dqr,
                    "criteria": ds.dqr_criteria if ds else [],
                    "climate_change": share_val,
                    "contribution_share": share,
                    "is_most_relevant": share >= 0.05,
                }
            )
            if dqr is not None:
                num += dqr * share
                den += share
        rows.sort(key=lambda r: -r["contribution_share"])
        weighted = (num / den) if den else None

        def rating(v: float | None) -> str:
            if v is None:
                return "unknown"
            if v <= 1.6:
                return "excellent"
            if v <= 2.0:
                return "very good"
            if v <= 3.0:
                return "good"
            if v <= 4.0:
                return "fair"
            return "poor"

        return {
            "weighted_dqr": weighted,
            "weighted_rating": rating(weighted),
            "declared_study_dqr": None,
            "by_dataset": rows,
            "note": (
                "PEF requires the DQR to reflect the processes that actually drive the result. "
                "This weights each dataset's declared DQR by its share of the climate-change "
                "total, so a poor-quality dataset only matters in proportion to what it "
                "contributes. Datasets above 5% of the total are flagged 'most relevant'."
            ),
            "scale": "1 = excellent, 5 = poor (PEF DQR scale)",
        }

    # -- explain one number ---------------------------------------------------

    def explain(self, result: dict[str, Any], flow_uri: str) -> dict[str, Any]:
        """Full provenance for a single exchange: the triple, the file, the factor,
        the scaling chain and the arithmetic."""
        matches = [e for e in result["exchanges"] if e["flow_uri"] == flow_uri]
        if not matches:
            raise KeyError(f"No exchange with flow URI '{flow_uri}' in this result.")
        match = matches[0]
        gs = self.graph_service
        act = gs.activities.get(match["activity"])
        ds = gs.datasets.get(match["dataset"]) if match["dataset"] else None
        return {
            "exchange": match,
            "occurrences": matches if len(matches) > 1 else [],
            "occurrence_note": (
                f"This exchange is reached by {len(matches)} distinct supply-chain paths; the "
                f"result sums all of them."
                if len(matches) > 1
                else ""
            ),
            "triples": self._triples_for(flow_uri),
            "activity": act.as_dict(with_flows=False) if act else None,
            "dataset": ds.as_dict() if ds else None,
            "chain": [
                f"Functional unit: {result['functional_unit']['declared']}",
                f"Reference flow: {result['functional_unit']['reference_flow_amount']:.6g} kg "
                f"{result['functional_unit']['reference_flow_type']}",
                f"Activity '{match['activity']}' scaled by {match['activity_scale']:.6g}",
                f"Exchange declares {match['unit_amount']} {match['unit']} per activity unit",
                f"Scaled amount: {match['scaled_amount']:.6g} {match['unit']}",
                match["formula"] or "no factor applied",
            ],
        }

    def _triples_for(self, uri: str) -> list[dict[str, str]]:
        from rdflib import URIRef
        from rdflib.term import BNode

        g = self.graph_service.graph
        out: list[dict[str, str]] = []
        node = URIRef(uri)

        def emit(s: Any, depth: int = 0) -> None:
            if depth > 2:
                return
            for p, o in g.predicate_objects(s):
                out.append(
                    {
                        "subject": str(s),
                        "predicate": str(p),
                        "object": str(o),
                        "object_is_node": isinstance(o, BNode),
                    }
                )
                if isinstance(o, BNode):
                    emit(o, depth + 1)

        emit(node)
        return out
