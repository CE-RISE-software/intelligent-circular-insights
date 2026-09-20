# CE-RISE Data Quality Framework Data Model

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20117408.svg)](https://doi.org/10.5281/zenodo.20117408) [![Schemas](https://img.shields.io/badge/Schema%20Files-LinkML%2C%20JSON%2C%20SHACL%2C%20OWL-32CD32)](https://ce-rise-models.codeberg.page/data-quality-framework/)

This repository defines the CE-RISE cross-cutting data model for data quality assessment.
It provides a reusable framework for assessing fitness for purpose of data across DPP and
DMP models, covering provenance, representativeness, validity, accuracy, consistency,
timeliness, completeness, pedigree scoring, diagnostics, and remediation metadata.


---

## Data Model Structure

The Data Quality Framework data model is structured as a reusable utility model for
attaching quality assessments to values, datasets, records, indicators, model inputs, model
outputs, evidence, or data sources defined in other CE-RISE data models. It covers
pedigree scoring, diagnostic evidence, issue tracking, remediation, aggregation, and
translation of data quality scores into uncertainty metadata.

### Key Design Principles

- **Cross-model integration**: `DataQualityAssessment` is the main integration point for
  other CE-RISE data models. It can target a model, class, slot, record, value path, or
  value identifier without requiring each consumer model to duplicate data quality structures.
- **Fitness for purpose**: Quality is assessed against an intended use rather than as an
  abstract property. The same data may be adequate for exploratory use and inadequate for
  formal comparison or compliance.
- **Pedigree matrix support**: The model supports criterion-level scoring for validity,
  accuracy, consistency, timeliness, and completeness, while allowing additional criteria
  such as representativeness, transparency, provenance, reproducibility, and precision.
- **Diagnostics before remediation**: Quality scores can be supported by diagnostics that
  record expectations, deviations, metrics, likely causes, impacts, and reproducibility
  information.
- **Actionable quality management**: Issues and remediation actions can be represented
  explicitly, including severity, risk statements, owners, target dates, expected score
  improvements, and verification methods.
- **Uncertainty-aware by design**: Data quality scores can be translated into coefficients of
  variation, uncertainty factors, combined uncertainty factors, or references to the
  CE-RISE `uncertainty-quantification` model.
- **Traceability-compatible**: Quality records can point to the CE-RISE
  `metrological-traceability` model when quality depends on calibration, methods,
  boundary definitions, reference materials, or traceability evidence.
- **Standards-aligned but optional**: The model references established quality and
  provenance vocabularies while keeping every field optional to support partial or
  progressive documentation.

### Core Hierarchy

```
DataQualityFramework (root)
├── DataQualityAssessment
│   ├── DataCharacterization
│   ├── DataQualityProfile
│   │   └── QualityCriterionAssessment
│   │       └── QualityMetric
│   ├── QualityDiagnostic
│   ├── QualityIssue
│   │   └── RemediationAction
│   └── UncertaintyTranslation
├── QualityAggregation
└── EvidenceReference
```

### Workflow Sequence

#### **Step 1: Target the data**
Use `DataQualityAssessment` to identify the external model, class, slot, record, value path,
or value identifier to which the assessment applies.

#### **Step 2: Characterize the data**
Use `DataCharacterization` to document source, provider, collection method, protocol,
version, temporal/geographical/technological coverage, population or scope, preprocessing,
harmonization, and provenance.

#### **Step 3: Score quality criteria**
Use `DataQualityProfile` and `QualityCriterionAssessment` to score validity, accuracy,
consistency, timeliness, completeness, and any additional criteria needed for the use case.

#### **Step 4: Support scores with diagnostics**
Use `QualityDiagnostic` and `QualityMetric` to document expectation checks, missing-data
analysis, structural integrity, distributional drift, unit consistency, provenance checks,
impact analysis, and reproducibility information.

#### **Step 5: Track issues and remediation**
Use `QualityIssue` and `RemediationAction` to turn poor scores or diagnostic findings into
explicit risks, containment measures, technical fixes, governance actions, and verification
evidence.

#### **Step 6: Link quality to uncertainty**
Use `UncertaintyTranslation` when data quality scores need to become uncertainty metadata,
such as coefficient of variation ranges, uncertainty factors, or references to uncertainty
statements.

### Data Properties

Most literal data fields follow the `*_value` naming pattern. Ranges are string by default,
with typed ranges used where appropriate for dates, datetimes, integers, floats, booleans,
URIs, and enumerated values.

#### SQL Identifiers

Every data point in the model includes a `sql_identifier` annotation that serves as a unique, machine-friendly database identifier. These identifiers follow a structured namespace pattern to ensure uniqueness across the entire data model:

**Pattern**: `MODEL_[category]_[specific_name]`

**Features:**
- **Data Quality Framework Prefix**: All identifiers start with `dqf_` to clearly identify them as belonging to this cross-cutting model
- **Hierarchical Namespacing**: Uses category prefixes such as `assessment_`, `profile_`, `criterion_`, `metric_`, `diagnostic_`, `issue_`, `remediation_`, and `evidence_`
- **Database-Friendly**: Uses underscores and avoids special characters for SQL compatibility
- **Unique Across Model**: No duplicate identifiers, even when similar concepts appear in different parts of the hierarchy
- **Reasonable Length**: Abbreviated but meaningful names that balance clarity with practical database usage

**Examples:**
- `dqf_assessment_identifier` - reusable identifier for a data quality assessment
- `dqf_criterion_score` - pedigree score for a quality criterion
- `dqf_quality_flag` - operational green/orange/red decision flag
- `dqf_uncertainty_factor` - data-quality-derived uncertainty factor
- `dqf_remediation_action_identifier` - identifier for a remediation action

This identifier system enables seamless integration with databases and ensures clear data model composition when combining with other CE-RISE data models.

---

## Development Roadmap

| Step | Component | Criticalities Identified | Solutions Implemented | Status |
|------|-----------|-------------------------|----------------------|--------|
| **1** | **Cross-Model DataQualityAssessment** | • Other models need a clean way to attach data quality without duplicating quality structures<br>• Quality may apply to a value, field, record, dataset, indicator, evidence item, model input, or model output<br>• Fitness for purpose depends on intended use | • Added reusable `DataQualityAssessment` class<br>• Added target references for model, class, slot, record, value path, and value identifier<br>• Added intended use, fitness-for-purpose, uncertainty, traceability, evidence, and standards references | **COMPLETED** |
| **2** | **Data Characterization and Provenance** | • Quality assessment requires context: source, provider, method, scope, version, coverage, and preprocessing<br>• Missing provenance weakens auditability and interpretation | • Added `DataCharacterization` with data type, source type, provider, collection protocol, version, update frequency, temporal/geographic/technological coverage, sample size, variable definition, preprocessing, harmonization, and provenance fields | **COMPLETED** |
| **3** | **Pedigree Profile and Criterion Scores** | • D2.4 uses five core quality criteria and a 1-4 pedigree scale<br>• Consumers need both criterion-level and overall quality profiles | • Added `DataQualityProfile` and `QualityCriterionAssessment`<br>• Added enums for validity, accuracy, consistency, timeliness, completeness, and additional criteria<br>• Added quality score, confidence level, green/orange/red flag, limiting criteria, weights, thresholds, impacts, and rationales | **COMPLETED** |
| **4** | **Diagnostics and Metrics** | • Scores need evidence from reproducible diagnostics, not only labels<br>• Diagnostics need expectations, deviations, causes, impacts, metrics, and workflow references | • Added `QualityDiagnostic` and `QualityMetric`<br>• Added diagnostic types for profiling, missingness, structural/relational integrity, distributional drift, semantic/unit consistency, temporal/spatial alignment, provenance correlation, impact sensitivity, scoring checks, and reproducibility checks | **COMPLETED** |
| **5** | **Issues and Remediation** | • Poor scores must become actionable risks and improvement plans<br>• Remediation can be technical, analytical, or governance-related | • Added `QualityIssue` and `RemediationAction`<br>• Added issue severity/status, root cause, risk statement, scope, detected date, remediation type, priority, owner, due date, completion date, expected score improvement, and verification method fields | **COMPLETED** |
| **6** | **Quality-to-Uncertainty Translation and Aggregation** | • D2.4 translates data quality scores into CV% ranges or uncertainty factors when statistical uncertainty is unavailable<br>• Composite indicators need quality aggregation across inputs and profiles | • Added `UncertaintyTranslation` and `QualityAggregation`<br>• Added CV lower/upper, uncertainty factor, combined CV, combined UF, distribution assumption, translation method, aggregation level, method, inputs, weights, outputs, and rationale fields | **COMPLETED** |

### Integration Opportunities

- **CE-RISE uncertainty-quantification**: reference uncertainty statements, budgets, and data-quality-derived uncertainty factors or coefficients of variation.
- **CE-RISE metrological-traceability**: reference traceability chains, calibration evidence, method definitions, boundary definitions, and reference materials that affect quality scores.
- **W3C Data Quality Vocabulary (DQV)**: semantic alignment for quality dimensions, measurements, metrics, and annotations.
- **PROV-O**: provenance of source data, diagnostics, workflows, agents, evidence, and derivations.
- **DCAT**: dataset and distribution metadata for data sources and versions.
- **QUDT**: units and numeric values for quantitative quality metrics.
- **SKOS/RDFS/Dublin Core/PAV/Schema.org**: labels, definitions, notes, dates, versions, URLs, and metadata.
- **NUSAP, IPCC data quality guidance, ISO 14044, ISO 8000, and ISO 9001**: conceptual basis for pedigree scoring, data quality management, and assessment documentation.
- **CE-RISE consumer models**: product-profile, material-profile, diagnostic-results, integrated-lca, re-indicators-specification, and future utility or assessment models.

---

## Publishing

Release artifacts for each version (`schema.yaml`, `schema.json`, `shacl.ttl`, `model.ttl`)
are served directly from this URL:
```
https://ce-rise-models.codeberg.page/data-quality-framework/
```


---

## Accessing Previous Releases

If you want to view the files published for version `v0.0.1`, open:

```
https://codeberg.org/CE-RISE-models/data-quality-framework/src/tag/pages-v0.0.1/generated/
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
