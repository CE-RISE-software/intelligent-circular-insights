"""PEFDPP knowledge-graph service.

Loads the PEFDPP ontology (TBox) and the battery case study (ABox) from
``ontology/pefdpp`` into a single rdflib Graph and exposes typed accessors
over it.

The design point of WP3 is that the life cycle inventory is a *graph*, not a
spreadsheet: activities, exchanges, quantities, geographies, data-quality
scores and Circular Footprint Formula parameters are all addressable triples.
Everything downstream of this module — the LCA engine, the provenance
drill-down, the competency-question browser — reads from here, so no number in
the workbench exists without a triple behind it.

Note on the EF 3.1 elementary-flow scheme: ``ef31-elementaryflows.ttl`` is a
40 MB SKOS scheme listing the full EF 3.1 flow list. The case study references
it by UUID but does not import it, so it is *not* loaded by default. Call
``load_elementary_flow_scheme()`` if a query genuinely needs it.

Port note
---------
**Carried over, not rewritten**, on the same reasoning as the carbon engine: this
reader produces figures checked against published values, and restyling correct RDF
handling risks them for nothing. What changed is the boundary — the repo-relative
default data root is gone, so a caller (or a test pointing at a fixture) must say
where the graph lives.

``load_elementary_flow_scheme()`` reports honestly when the 41 MB EF 3.1 flow list is
absent; that file is deliberately not committed (``ontology/pefdpp/skos/README.md``).
Nothing in the default path needs it: the case study cites elementary flows by UUID,
and characterisation factors join on the same UUID from a small committed JSON.
"""

from __future__ import annotations

import glob
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from rdflib import RDF, RDFS, Graph, Literal, Namespace, URIRef
from rdflib.namespace import DCTERMS

# --- PEFDPP namespaces -------------------------------------------------------
PEFDPP = Namespace("https://w3id.org/mintjesba/pefdpp/")
ACT = Namespace("https://w3id.org/mintjesba/pefdpp/activity#")
FLOW = Namespace("https://w3id.org/mintjesba/pefdpp/flow#")
DS = Namespace("https://w3id.org/mintjesba/pefdpp/dataset#")
DQ = Namespace("https://w3id.org/mintjesba/pefdpp/dataquality#")
LCIA = Namespace("https://w3id.org/mintjesba/pefdpp/lcia#")
PRS = Namespace("https://w3id.org/mintjesba/pefdpp/product-system#")
PS = Namespace("https://w3id.org/mintjesba/pefdpp/pefstudy#")
EFU = Namespace("https://w3id.org/mintjesba/pefdpp/ef31-units#")
EFIC = Namespace("https://w3id.org/mintjesba/pefdpp/skos/ef31-impactcategories#")
GEO = Namespace("https://w3id.org/mintjesba/pefdpp/skos/pef-geographies#")

# --- external namespaces -----------------------------------------------------
OM = Namespace("http://www.ontology-of-units-of-measure.org/resource/om-2/")
FOAF = Namespace("http://xmlns.com/foaf/0.1/")

# Supplied by the composition root; no repo-relative guessing.
DEFAULT_DATA_ROOT: Path | None = None

#: The full EF 3.1 elementary-flow SKOS scheme — very large, loaded on demand.
LAZY_FILES = {"ef31-elementaryflows.ttl"}


def local_name(node: Any) -> str:
    """Return the readable tail of an IRI ('...#CellManufacturingAct')."""
    if node is None:
        return ""
    s = str(node)
    for sep in ("#", "/"):
        if sep in s:
            tail = s.rsplit(sep, 1)[-1]
            if tail:
                return tail
    return s


@dataclass
class Measure:
    """An om:Measure — a number with a unit."""

    value: float | None
    unit: str
    unit_iri: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {"value": self.value, "unit": self.unit, "unit_iri": self.unit_iri}


@dataclass
class FlowRecord:
    """One exchange (act:inputOf / act:outputOf) as it stands in the graph."""

    uri: str
    id: str
    flow_type: str
    flow_type_uri: str
    flow_type_label: str
    flow_class: str  # ProductFlow | WasteFlow | ElementaryFlow | Flow
    contextual_label: str
    direction: str  # input | output
    activity: str
    amount: float | None
    unit: str
    is_determining: bool = False
    source_dataset: str = ""
    eol_scenario: dict[str, Any] | None = None
    transport: dict[str, Any] | None = None
    source_file: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "uri": self.uri,
            "id": self.id,
            "flow_type": self.flow_type,
            "flow_type_label": self.flow_type_label,
            "flow_class": self.flow_class,
            "contextual_label": self.contextual_label,
            "direction": self.direction,
            "activity": self.activity,
            "amount": self.amount,
            "unit": self.unit,
            "is_determining": self.is_determining,
            "source_dataset": self.source_dataset,
            "eol_scenario": self.eol_scenario,
            "transport": self.transport,
            "source_file": self.source_file,
        }


@dataclass
class ActivityRecord:
    """A unit process."""

    uri: str
    id: str
    label: str
    activity_type: str
    geography: str
    is_company_specific: bool | None
    dataset: str
    dataset_title: str
    determining_flow: str
    determining_flow_type: str
    determining_amount: float | None
    determining_unit: str
    inputs: list[FlowRecord] = field(default_factory=list)
    outputs: list[FlowRecord] = field(default_factory=list)
    source_file: str = ""

    def as_dict(self, with_flows: bool = True) -> dict[str, Any]:
        out = {
            "uri": self.uri,
            "id": self.id,
            "label": self.label,
            "activity_type": self.activity_type,
            "geography": self.geography,
            "is_company_specific": self.is_company_specific,
            "dataset": self.dataset,
            "dataset_title": self.dataset_title,
            "determining_flow": self.determining_flow,
            "determining_flow_type": self.determining_flow_type,
            "determining_amount": self.determining_amount,
            "determining_unit": self.determining_unit,
            "input_count": len(self.inputs),
            "output_count": len(self.outputs),
            "source_file": self.source_file,
        }
        if with_flows:
            out["inputs"] = [f.as_dict() for f in self.inputs]
            out["outputs"] = [f.as_dict() for f in self.outputs]
        return out


@dataclass
class DatasetRecord:
    uri: str
    id: str
    title: str
    dataset_type: str
    compliance_level: str
    dqr_overall: float | None
    dqr_criteria: list[dict[str, Any]]
    activities: list[str]
    publisher: str = ""
    licence: str = ""
    source_file: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "uri": self.uri,
            "id": self.id,
            "title": self.title,
            "dataset_type": self.dataset_type,
            "compliance_level": self.compliance_level,
            "dqr_overall": self.dqr_overall,
            "dqr_criteria": self.dqr_criteria,
            "activities": self.activities,
            "publisher": self.publisher,
            "licence": self.licence,
            "source_file": self.source_file,
        }


class PefdppGraphService:
    """Loads and indexes the PEFDPP graph. Thread-safe, lazily initialised."""

    def __init__(self, data_root: Path | None = None) -> None:
        if data_root is None:
            raise ValueError(
                "PefdppGraphService needs an explicit data_root; there is no "
                "repo-relative default, so a test can point it at a fixture"
            )
        self.data_root = Path(data_root)
        self._graph: Graph | None = None
        self._lock = threading.Lock()
        self._loaded_files: list[str] = []
        self._parse_errors: list[dict[str, str]] = []
        self._elementary_scheme_loaded = False
        # indices
        self._activities: dict[str, ActivityRecord] = {}
        self._datasets: dict[str, DatasetRecord] = {}
        self._producers: dict[str, str] = {}  # flow_type id -> activity id
        self._flow_source: dict[str, str] = {}  # flow uri -> source file

    # -- loading --------------------------------------------------------------

    @property
    def graph(self) -> Graph:
        if self._graph is None:
            with self._lock:
                if self._graph is None:
                    self._load()
        return self._graph  # type: ignore[return-value]

    def _ttl_files(self) -> list[Path]:
        pattern = str(self.data_root / "**" / "*.ttl")
        files = [Path(p) for p in sorted(glob.glob(pattern, recursive=True))]
        return [f for f in files if f.name not in LAZY_FILES]

    def _load(self) -> None:
        g = Graph()
        g.bind("pefdpp", PEFDPP)
        g.bind("act", ACT)
        g.bind("flow", FLOW)
        g.bind("dataset", DS)
        g.bind("dq", DQ)
        g.bind("lcia", LCIA)
        g.bind("prs", PRS)
        g.bind("ps", PS)
        g.bind("om", OM)
        g.bind("efic", EFIC)
        g.bind("geo", GEO)
        g.bind("efu", EFU)

        for f in self._ttl_files():
            try:
                g.parse(str(f), format="turtle")
                self._loaded_files.append(str(f.relative_to(self.data_root)))
                # remember which file each flow/activity subject came from
                sub = Graph()
                sub.parse(str(f), format="turtle")
                rel = str(f.relative_to(self.data_root))
                for s in set(sub.subjects()):
                    if isinstance(s, URIRef):
                        self._flow_source.setdefault(str(s), rel)
            except Exception as exc:  # a broken TTL must not kill the workbench
                self._parse_errors.append({"file": str(f), "error": f"{type(exc).__name__}: {exc}"})

        self._graph = g
        self._build_indices()

    def load_elementary_flow_scheme(self) -> bool:
        """Load the 40 MB EF 3.1 elementary-flow SKOS scheme on demand."""
        if self._elementary_scheme_loaded:
            return True
        target = self.data_root / "ontology" / "skos" / "ef31-elementaryflows.ttl"
        if not target.exists():
            return False
        with self._lock:
            if self._elementary_scheme_loaded:
                return True
            self.graph.parse(str(target), format="turtle")
            self._elementary_scheme_loaded = True
        return True

    # -- indexing -------------------------------------------------------------

    def _measure(self, node: Any) -> Measure:
        if node is None:
            return Measure(None, "")
        m = self.graph.value(node, FLOW.hasMeasure) or node
        val = self.graph.value(m, OM.hasNumericalValue)
        unit = self.graph.value(m, OM.hasUnit)
        try:
            fval = float(val) if val is not None else None
        except (TypeError, ValueError):
            fval = None
        return Measure(fval, local_name(unit), str(unit) if unit else "")

    def _flow_class(self, flow_type: Any) -> str:
        types = set(self.graph.objects(flow_type, RDF.type))
        for cls, name in (
            (FLOW.ElementaryFlow, "ElementaryFlow"),
            (FLOW.WasteFlow, "WasteFlow"),
            (FLOW.ProductFlow, "ProductFlow"),
        ):
            if cls in types:
                return name
        return "Flow"

    def _eol_scenario(self, flow: Any) -> dict[str, Any] | None:
        node = self.graph.value(flow, FLOW.hasEndOfLifeScenario)
        if node is None:
            return None

        def cff(prop: URIRef) -> float | None:
            v = self.graph.value(node, prop)
            if v is None:
                return None
            raw = self.graph.value(v, FLOW.hasValue)
            try:
                return float(raw) if raw is not None else None
            except (TypeError, ValueError):
                return None

        return {
            "recycling_rate_R2": cff(FLOW.recyclingRate),
            "energy_recovery_rate_R3": cff(FLOW.energyRecoveryRate),
            "recycled_content_R1": cff(FLOW.recycledContentRate),
            "virgin_equivalent": local_name(self.graph.value(node, FLOW.virginEquivalent)),
            "recycling_flow_type": local_name(self.graph.value(node, FLOW.recyclingFlowType)),
            "disposal_flow_type": local_name(self.graph.value(node, FLOW.disposalFlowType)),
            "energy_recovery_flow_type": local_name(
                self.graph.value(node, FLOW.energyRecoveryFlowType)
            ),
        }

    def _transport(self, flow: Any) -> dict[str, Any] | None:
        dist = self.graph.value(flow, FLOW.transportDistance)
        if dist is None:
            return None
        val = self.graph.value(dist, OM.hasNumericalValue)
        unit = self.graph.value(dist, OM.hasUnit)

        def num(prop: URIRef) -> float | None:
            v = self.graph.value(flow, prop)
            try:
                return float(v) if v is not None else None
            except (TypeError, ValueError):
                return None

        try:
            dval = float(val) if val is not None else None
        except (TypeError, ValueError):
            dval = None
        return {
            "distance": dval,
            "distance_unit": local_name(unit),
            "empty_returns": num(FLOW.transportEmptyReturns),
            "loading_rate": num(FLOW.transportLoadingRate),
        }

    def _flow_record(
        self, flow: Any, direction: str, activity: Any, determining: Any
    ) -> FlowRecord:
        ft = self.graph.value(flow, FLOW.hasFlowType)
        m = self._measure(flow)
        label = self.graph.value(ft, RDFS.label) if ft is not None else None
        src = self.graph.value(ft, FLOW.sourcedFrom) if ft is not None else None
        ctx = self.graph.value(flow, FLOW.contextualLabel)
        return FlowRecord(
            uri=str(flow),
            id=local_name(flow),
            flow_type=local_name(ft),
            flow_type_uri=str(ft) if ft else "",
            flow_type_label=str(label) if label else local_name(ft),
            flow_class=self._flow_class(ft) if ft is not None else "Flow",
            contextual_label=str(ctx) if ctx else "",
            direction=direction,
            activity=local_name(activity),
            amount=m.value,
            unit=m.unit,
            is_determining=(determining is not None and flow == determining),
            source_dataset=local_name(src),
            eol_scenario=self._eol_scenario(flow),
            transport=self._transport(flow),
            source_file=self._flow_source.get(str(flow), ""),
        )

    def _dqr(self, node: Any) -> tuple[float | None, list[dict[str, Any]]]:
        dq_node = self.graph.value(node, DQ.hasDataQuality)
        if dq_node is None:
            return None, []
        raw = self.graph.value(dq_node, DQ.hasOverallDQR)
        try:
            overall = float(raw) if raw is not None else None
        except (TypeError, ValueError):
            overall = None
        crit: list[dict[str, Any]] = []
        for c in self.graph.objects(dq_node, DQ.hasDQRCriterion):
            dim = self.graph.value(c, DQ.forDimension)
            val = self.graph.value(c, DQ.hasValue)
            just = self.graph.value(c, DQ.hasJustification)
            try:
                ival = int(val) if val is not None else None
            except (TypeError, ValueError):
                ival = None
            crit.append(
                {
                    "dimension": local_name(dim),
                    "value": ival,
                    "justification": str(just) if just else "",
                }
            )
        crit.sort(key=lambda c: c["dimension"])
        return overall, crit

    def _build_indices(self) -> None:
        g = self.graph

        # datasets
        for d in g.subjects(RDF.type, DS.LCIDataset):
            overall, crit = self._dqr(d)
            pub = g.value(d, DCTERMS.publisher)
            pub_name = g.value(pub, FOAF.name) if pub is not None else None
            self._datasets[local_name(d)] = DatasetRecord(
                uri=str(d),
                id=local_name(d),
                title=str(g.value(d, DCTERMS.title) or local_name(d)),
                dataset_type=local_name(g.value(d, DS.hasDatasetType)),
                compliance_level=local_name(g.value(d, DS.hasComplianceLevel)),
                dqr_overall=overall,
                dqr_criteria=crit,
                activities=sorted(local_name(a) for a in g.objects(d, DS.containsActivity)),
                publisher=str(pub_name) if pub_name else "",
                licence=str(g.value(d, DCTERMS.license) or ""),
                source_file=self._flow_source.get(str(d), ""),
            )

        act_to_dataset = {}
        for ds_id, ds in self._datasets.items():
            for a in ds.activities:
                act_to_dataset[a] = ds_id

        # activities
        for a in g.subjects(RDF.type, ACT.Activity):
            aid = local_name(a)
            det = g.value(a, ACT.hasDeterminingFlow)
            det_m = self._measure(det) if det is not None else Measure(None, "")
            det_ft = g.value(det, FLOW.hasFlowType) if det is not None else None
            atype = g.value(a, ACT.hasActivityType)
            atype_label = g.value(atype, RDFS.label) if atype is not None else None
            cs = g.value(a, ACT.isCompanySpecific)
            rec = ActivityRecord(
                uri=str(a),
                id=aid,
                label=str(atype_label) if atype_label else local_name(atype) or aid,
                activity_type=local_name(atype),
                geography=local_name(g.value(a, ACT.hasGeography)),
                is_company_specific=bool(cs) if isinstance(cs, Literal) else None,
                dataset=act_to_dataset.get(aid, ""),
                dataset_title=self._datasets[act_to_dataset[aid]].title
                if aid in act_to_dataset
                else "",
                determining_flow=local_name(det),
                determining_flow_type=local_name(det_ft),
                determining_amount=det_m.value,
                determining_unit=det_m.unit,
                source_file=self._flow_source.get(str(a), ""),
            )
            for f in g.subjects(ACT.inputOf, a):
                rec.inputs.append(self._flow_record(f, "input", a, det))
            for f in g.subjects(ACT.outputOf, a):
                rec.outputs.append(self._flow_record(f, "output", a, det))
            rec.inputs.sort(key=lambda f: f.id)
            rec.outputs.sort(key=lambda f: f.id)

            # ignore TBox property IRIs that share the act: namespace
            if not rec.inputs and not rec.outputs and det is None:
                continue
            self._activities[aid] = rec
            if det_ft is not None:
                self._producers.setdefault(local_name(det_ft), aid)

    def _ensure_loaded(self) -> None:
        """Force the lazy parse before an index is read.

        The accessors below used to do this with a bare ``self.graph`` statement,
        which is correct but reads exactly like a line someone forgot to finish.
        Naming it costs nothing and stops a future reader from "tidying" it away.
        """
        _ = self.graph

    # -- public accessors -----------------------------------------------------

    @property
    def activities(self) -> dict[str, ActivityRecord]:
        self._ensure_loaded()
        return self._activities

    @property
    def datasets(self) -> dict[str, DatasetRecord]:
        self._ensure_loaded()
        return self._datasets

    @property
    def producers(self) -> dict[str, str]:
        """flow-type id -> id of the activity whose determining flow it is."""
        self._ensure_loaded()
        return self._producers

    def source_file_of(self, uri: str) -> str:
        self._ensure_loaded()
        return self._flow_source.get(uri, "")

    def flow_type_label(self, ft_id: str) -> str:
        for act in self.activities.values():
            for f in act.inputs + act.outputs:
                if f.flow_type == ft_id:
                    return f.flow_type_label
        return ft_id

    def flow_type_source_dataset(self, ft_id: str) -> str:
        for act in self.activities.values():
            for f in act.inputs + act.outputs:
                if f.flow_type == ft_id and f.source_dataset:
                    return f.source_dataset
        return ""

    def load_report(self) -> dict[str, Any]:
        self._ensure_loaded()
        return {
            "data_root": str(self.data_root),
            "triples": len(self.graph),
            "files_loaded": self._loaded_files,
            "parse_errors": self._parse_errors,
            "activity_count": len(self._activities),
            "dataset_count": len(self._datasets),
            "elementary_flow_scheme_loaded": self._elementary_scheme_loaded,
            "lazy_files": sorted(LAZY_FILES),
        }

    # -- PEF study ------------------------------------------------------------

    def studies(self) -> list[str]:
        return sorted(local_name(s) for s in self.graph.subjects(RDF.type, PS.PEFStudy))

    def study(self, study_id: str | None = None) -> dict[str, Any]:
        """Return the goal, scope, functional unit and product system of a PEFStudy."""
        g = self.graph
        subjects = list(g.subjects(RDF.type, PS.PEFStudy))
        if not subjects:
            return {}
        node = subjects[0]
        if study_id:
            for s in subjects:
                if local_name(s) == study_id:
                    node = s
                    break

        goal = g.value(node, PS.hasGoal)
        scope = g.value(node, PS.hasScope)
        fu = g.value(scope, PS.hasFunctionalUnit) if scope is not None else None
        sb = g.value(scope, PS.hasSystemBoundary) if scope is not None else None
        prod_sys = g.value(node, PS.hasProductSystem)
        overall, crit = self._dqr(node)

        def agent(n: Any) -> dict[str, str]:
            if n is None:
                return {}
            return {"iri": str(n), "name": str(g.value(n, FOAF.name) or local_name(n))}

        def txt(subj: Any, prop: URIRef) -> str:
            v = g.value(subj, prop) if subj is not None else None
            return str(v) if v is not None else ""

        fu_data: dict[str, Any] = {}
        if fu is not None:
            how_much = self._measure(g.value(fu, PS.howMuchProvided))
            how_long = self._measure(g.value(fu, PS.howLongProvided))
            conv = g.value(fu, PS.RFtoFUConversion)
            try:
                conv_f = float(conv) if conv is not None else None
            except (TypeError, ValueError):
                conv_f = None
            ref_flow = g.value(fu, PS.hasReferenceFlow)
            ref_ft = g.value(ref_flow, FLOW.hasFlowType) if ref_flow is not None else None
            fu_data = {
                "uri": str(fu),
                "what_provided": txt(fu, PS.whatProvided),
                "how_well_provided": txt(fu, PS.howWellProvided),
                "how_much_provided": how_much.as_dict(),
                "how_long_provided": how_long.as_dict(),
                "rf_to_fu_conversion": conv_f,
                "reference_flow": local_name(ref_flow),
                "reference_flow_uri": str(ref_flow) if ref_flow else "",
                "reference_flow_type": local_name(ref_ft),
                "conforms_to": local_name(g.value(fu, DCTERMS.conformsTo)),
            }

        stage_map: dict[str, str] = {}
        links: list[dict[str, str]] = []
        if prod_sys is not None:
            for al in g.objects(prod_sys, PRS.hasActivityLink):
                a = g.value(al, PRS.forActivity)
                stage = g.value(al, PRS.hasLifeCycleStage)
                links.append(
                    {
                        "link": local_name(al),
                        "activity": local_name(a),
                        "life_cycle_stage": local_name(stage),
                    }
                )
                if a is not None:
                    stage_map[local_name(a)] = local_name(stage)
            links.sort(key=lambda l: (l["life_cycle_stage"], l["activity"]))

        std = g.value(node, DCTERMS.conformsTo)
        std_data = {}
        if std is not None:
            creator = g.value(std, DCTERMS.creator)
            std_data = {
                "id": local_name(std),
                "title": str(g.value(std, DCTERMS.title) or local_name(std)),
                "issued": str(g.value(std, DCTERMS.issued) or ""),
                "creator": str(g.value(creator, FOAF.name) or "") if creator is not None else "",
                "source": str(g.value(std, DCTERMS.source) or ""),
                "description": str(g.value(std, DCTERMS.description) or ""),
            }

        return {
            "id": local_name(node),
            "uri": str(node),
            "title": str(g.value(node, DCTERMS.title) or local_name(node)),
            "conforms_to": std_data,
            "goal": {
                "intended_application": txt(goal, PS.intendedApplication),
                "decision_context": txt(goal, PS.decisionContext),
                "commissioner": agent(g.value(goal, PS.commissioner)) if goal is not None else {},
                "verifier": agent(g.value(goal, PS.verifier)) if goal is not None else {},
            },
            "scope": {
                "assumption": txt(scope, PS.hasAssumption),
                "limitation": txt(scope, PS.hasLimitation),
                "biodiversity_relevance": txt(scope, PS.biodiversityRelevance),
                "impact_categories": sorted(
                    local_name(c) for c in g.objects(scope, PS.includesImpactCategory)
                )
                if scope is not None
                else [],
            },
            "system_boundary": {
                "boundary_type": local_name(g.value(sb, PS.hasBoundaryType))
                if sb is not None
                else "",
                "cut_off_criteria": txt(sb, PS.cutOffCriteria),
                "justification": txt(sb, PS.hasJustification),
                "excludes_activity": txt(sb, PS.excludesActivity),
                "exclusion_justification": txt(sb, PS.exclusionJustification),
            },
            "functional_unit": fu_data,
            "product_system": {
                "id": local_name(prod_sys),
                "activity_links": links,
                "stage_map": stage_map,
            },
            "declared_lcia_results": sorted(
                local_name(r) for r in g.objects(node, PS.hasLCIAResult)
            ),
            "data_quality": {"overall_dqr": overall, "criteria": crit},
            "source_file": self._flow_source.get(str(node), ""),
        }

    # -- generic SPARQL -------------------------------------------------------

    #: SPARQL Update keywords. Matched as whole words so that a variable named
    #: ?loadingRate or a property called flow:transportLoadingRate is not mistaken
    #: for a LOAD statement.
    _UPDATE_KEYWORDS = (
        "insert",
        "delete",
        "drop",
        "clear",
        "load",
        "create",
        "add",
        "move",
        "copy",
    )

    def query(self, sparql: str, limit: int = 200) -> dict[str, Any]:
        """Run a read-only SPARQL SELECT/ASK over the graph."""
        import re as _re

        # Blank out IRIs and string literals FIRST — an IRI fragment such as
        # <...pefdpp/activity#> contains a '#', and stripping comments before
        # IRIs would swallow the rest of a single-line query.
        scan = _re.sub(r'<[^>\s]*>|"[^"\n]*"|\'[^\'\n]*\'', " ", sparql)
        scan = _re.sub(r"#[^\n]*", " ", scan)
        for banned in self._UPDATE_KEYWORDS:
            if _re.search(rf"\b{banned}\b", scan, flags=_re.IGNORECASE):
                raise ValueError(
                    f"Only read-only queries are allowed (SPARQL Update keyword "
                    f"'{banned.upper()}' found)."
                )
        if not _re.search(r"\b(select|ask|construct|describe)\b", scan, flags=_re.IGNORECASE):
            raise ValueError("Query must be a SELECT, ASK, CONSTRUCT or DESCRIBE.")
        res = self.graph.query(sparql)
        cols = [str(v) for v in (res.vars or [])]
        rows: list[dict[str, Any]] = []
        for i, row in enumerate(res):
            if i >= limit:
                break
            if isinstance(row, bool):
                return {"columns": ["result"], "rows": [{"result": row}], "truncated": False}
            item: dict[str, Any] = {}
            for c in cols:
                val = row[c] if c in cols else None
                try:
                    val = row[cols.index(c)]
                except Exception:
                    val = None
                item[c] = (
                    local_name(val)
                    if isinstance(val, URIRef)
                    else (str(val) if val is not None else None)
                )
            rows.append(item)
        return {"columns": cols, "rows": rows, "truncated": len(rows) >= limit}
