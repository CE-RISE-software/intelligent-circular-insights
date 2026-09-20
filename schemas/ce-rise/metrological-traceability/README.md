# CE-RISE Metrological Traceability Data Model

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20084797.svg)](https://doi.org/10.5281/zenodo.20084797) [![Schemas](https://img.shields.io/badge/Schema%20Files-LinkML%2C%20JSON%2C%20SHACL%2C%20OWL-32CD32)](https://ce-rise-models.codeberg.page/metrological-traceability/)

This repository defines the CE-RISE cross-cutting data model for metrological traceability.
It provides reusable structures for documenting the reference basis of measured,
calculated, method-defined, or boundary-defined values, including measurands, units,
standards, calibration chains, reference materials, measurement procedures, method
references, and boundary-defined references.


---

## Data Model Structure

The Metrological Traceability data model is structured as a reusable utility model for
attaching traceability information to values defined in other CE-RISE data models. It can
describe SI-traceable measurements, method-defined properties, boundary-defined model
outputs, reference materials, calibration hierarchies, competence evidence, and
comparability assessments.

### Key Design Principles

- **Cross-model integration**: `TraceabilityStatement` is the main integration point for other
  CE-RISE data models. It can target a model, class, slot, record, value path, or value
  identifier without requiring each consumer model to duplicate traceability structures.
- **Layered traceability**: The model distinguishes SI traceability, method-defined traceability,
  boundary-defined traceability, reference material traceability, conventional references, and
  hybrid cases.
- **Documented chains**: Traceability can be represented as a linear chain or a branched
  network of links, including calibrations, comparisons, corrections, method steps, boundary
  definitions, datasets, software, and model execution records.
- **Uncertainty-aware by design**: Traceability records can point to the CE-RISE
  `uncertainty-quantification` model for uncertainty statements, budgets, or link-level
  uncertainty contributions.
- **Data-quality compatible**: Traceability records can point to the future CE-RISE
  `data-quality-framework` model for provenance, representativeness, completeness, and
  evidence quality assessments.
- **Standards-aligned but optional**: The model references established metrology and
  assessment standards while keeping every field optional to support partial or progressive
  documentation.

### Core Hierarchy

```
MetrologicalTraceability (root)
├── TraceabilityStatement
│   ├── TraceabilityBasis
│   ├── TraceabilityChain
│   │   └── TraceabilityLink
│   ├── MeasurementProcedure
│   ├── BoundaryDefinition
│   ├── CalibrationRecord
│   ├── ReferenceEntity
│   ├── ReferenceMaterial
│   ├── MeasurementStandard
│   └── CompetenceRecord
├── ComparabilityAssessment
└── EvidenceReference
```

### Workflow Sequence

#### **Step 1: Target the value**
Use `TraceabilityStatement` to identify the external model, class, slot, record, value path,
or value identifier to which traceability applies.

#### **Step 2: Define the traceability basis**
Use `TraceabilityBasis` to describe the common reference that gives meaning to the value:
SI unit realization, measurement standard, reference material, standardized method,
system boundary, characterization model, dataset, or conventional reference.

#### **Step 3: Document the chain or network**
Use `TraceabilityChain` and `TraceabilityLink` to represent the documented route from the
reported value to the reference. Links can include calibration, comparison, correction,
method definition, boundary definition, dataset mapping, or software/model execution.

#### **Step 4: Capture supporting records**
Use `CalibrationRecord`, `MeasurementProcedure`, `ReferenceMaterial`,
`MeasurementStandard`, `BoundaryDefinition`, `CompetenceRecord`, and `EvidenceReference`
to document the evidence needed to defend the traceability statement.

#### **Step 5: Assess comparability**
Use `ComparabilityAssessment` when two values need to be compared and the model must
record whether they share the same reference basis, measurand definition, method, or boundary.

### Data Properties

Most literal data fields follow the `*_value` naming pattern. Ranges are string by default,
with typed ranges used where appropriate for dates, datetimes, integers, booleans, URIs,
and enumerated values.

#### SQL Identifiers

Every data point in the model includes a `sql_identifier` annotation that serves as a unique, machine-friendly database identifier. These identifiers follow a structured namespace pattern to ensure uniqueness across the entire data model:

**Pattern**: `MODEL_[category]_[specific_name]`

**Features:**
- **Metrological Traceability Prefix**: All identifiers start with `mt_` to clearly identify them as belonging to this cross-cutting model
- **Hierarchical Namespacing**: Uses category prefixes such as `statement_`, `basis_`, `chain_`, `link_`, `calibration_`, `procedure_`, `boundary_`, and `evidence_`
- **Database-Friendly**: Uses underscores and avoids special characters for SQL compatibility
- **Unique Across Model**: No duplicate identifiers, even when similar concepts appear in different parts of the hierarchy
- **Reasonable Length**: Abbreviated but meaningful names that balance clarity with practical database usage

**Examples:**
- `mt_statement_identifier` - reusable identifier for a traceability statement
- `mt_basis_type` - type of traceability basis
- `mt_chain_identifier` - identifier for a traceability chain or network
- `mt_link_uncertainty_reference` - uncertainty reference attached to a traceability link
- `mt_boundary_definition_record` - boundary-definition record class identifier

This identifier system enables seamless integration with databases and ensures clear data model composition when combining with other CE-RISE data models.

---

## Development Roadmap

| Step | Component | Criticalities Identified | Solutions Implemented | Status | Missing/TODO |
|------|-----------|-------------------------|----------------------|--------|--------------|
| **1** | **Cross-Model TraceabilityStatement** | • Other models need a clean way to attach traceability without duplicating structures<br>• Traceability may apply to a field, value, record, dataset, model output, or comparison<br>• Direct embedding is not always practical | • Added reusable `TraceabilityStatement` class<br>• Added target references for model, class, slot, record, value path, and value identifier<br>• Added links to uncertainty, data quality, evidence, and standards | **COMPLETED** | • Add concrete examples for product, material, diagnostic, and LCA consumers |
| **2** | **Traceability Basis and References** | • Values are only comparable when their common reference is explicit<br>• References may be SI units, standards, reference materials, methods, datasets, or boundaries | • Added `TraceabilityBasis` and `ReferenceEntity`<br>• Added enums for SI, method, boundary, reference material, conventional, and hybrid traceability<br>• Added reference authority, version, URI, scope, and use date fields | **COMPLETED** | • Add controlled examples for SI, method-defined, and boundary-defined references |
| **3** | **Traceability Chain and Links** | • Traceability can be linear, branched, or networked<br>• Each link may add uncertainty or depend on evidence | • Added `TraceabilityChain` and `TraceabilityLink`<br>• Added chain completeness and validation status fields<br>• Added link roles for calibration, comparison, correction, method definition, boundary definition, dataset mapping, and software/model execution | **COMPLETED** | • Add sample chains for calibration hierarchy and LCA boundary traceability |
| **4** | **Calibration and Reference Artefacts** | • Calibration certificates, standards, and reference materials need explicit representation<br>• Validity periods and accreditation affect defensibility | • Added `CalibrationRecord`, `ReferenceMaterial`, and `MeasurementStandard`<br>• Added certificate, validity, assigned value, uncertainty, accreditation, and calibration interval fields | **COMPLETED** | • Add examples for instrument calibration and certified reference material use |
| **5** | **Method and Boundary Traceability** | • Method-defined properties require procedural fidelity<br>• Modelled outputs such as LCA indicators depend on boundary and scenario definitions | • Added `MeasurementProcedure` and `BoundaryDefinition`<br>• Added method parameters, sampling/specimen definition, environmental conditions, goal/scope, included/excluded processes, allocation, impact method, and characterization model fields | **COMPLETED** | • Align examples with integrated-lca and re-indicators consumer models |
| **6** | **Competence, Evidence, and Comparability** | • Traceability depends on competence and supporting evidence<br>• Two values may not be comparable if reference basis, measurand, method, or boundary differ | • Added `CompetenceRecord`, `EvidenceReference`, and `ComparabilityAssessment`<br>• Added accreditation, competence scope/status, evidence type, and comparability decision fields | **COMPLETED** | • Define comparison examples with uncertainty and data quality models |

### Integration Opportunities

- **CE-RISE uncertainty-quantification**: reference uncertainty statements, budgets, calibration uncertainty, link-level uncertainty contributions, and comparability uncertainty.
- **CE-RISE data-quality-framework**: reference data quality scores, provenance, representativeness, completeness, and evidence quality assessments.
- **QUDT**: semantic alignment for quantities, units, numeric values, and quantity kinds.
- **PROV-O**: provenance of evidence, procedures, software, agents, calibration records, and derivation.
- **SOSA/SSN**: observation procedures, features of interest, samples, sensors, and measurement systems.
- **JCGM VIM, GUM, ISO/IEC 17025, ILAC P10, ISO 17034, and ISO Guide 35**: conceptual basis for metrological traceability, traceability chains, calibration, competence, and reference materials.
- **ISO 14040/14044/14067 and Product Environmental Footprint methods**: conceptual basis for boundary-defined and model-defined traceability in LCA and carbon footprint claims.
- **CE-RISE consumer models**: product-profile, material-profile, diagnostic-results, integrated-lca, re-indicators-specification, and future utility or assessment models.

---

## Publishing

Release artifacts for each version (`schema.yaml`, `schema.json`, `shacl.ttl`, `model.ttl`)
are served directly from this URL:
```
https://ce-rise-models.codeberg.page/metrological-traceability/
```


---

## Accessing Previous Releases

If you want to view the files published for version `v0.0.1`, open:

```
https://codeberg.org/CE-RISE-models/metrological-traceability/src/tag/pages-v0.0.1/generated/
```

Files available in that directory typically include:

- schema.yaml
- schema.json
- shacl.ttl
- model.ttl
- index.html


---
<a href="https://europa.eu" target="_blank" rel="noopener noreferrer">
  <img src="https://ce-rise.eu/wp-content/uploads/2023/01/EN-Funded-by-the-EU-PANTONE-e1663585234561-1-1.png" alt="EU emblem" width="200"/>
</a>

Funded by the European Union under Grant Agreement No. 101092281 — CE-RISE.  
Views and opinions expressed are those of the author(s) only and do not necessarily reflect those of the European Union or the granting authority (HADEA).  
Neither the European Union nor the granting authority can be held responsible for them.

© 2026 CE-RISE consortium.  
Licensed under [Creative Commons Attribution–NonCommercial 4.0 International (CC BY-NC 4.0)](https://creativecommons.org/licenses/by-nc/4.0/).  
Attribution: CE-RISE project (Grant Agreement No. 101092281) and the individual authors/partners as indicated.

<a href="https://www.nilu.com" target="_blank" rel="noopener noreferrer">
  <img src="https://nilu.no/wp-content/uploads/2023/12/nilu-logo-seagreen-rgb-300px.png" alt="NILU logo" height="20"/>
</a>
<a href="https://www.empa.ch" target="_blank" rel="noopener noreferrer">
  <img src="https://www.empa.ch/image/company_logo?img_id=31464838&t=1762532293211" alt="EMPA logo" height="30"/>
</a>

Developed by NILU (Riccardo Boero — ribo@nilu.no) and EMPA (Matthias Rösslein — Matthias.Roesslein@empa.ch) within the CE-RISE project.
