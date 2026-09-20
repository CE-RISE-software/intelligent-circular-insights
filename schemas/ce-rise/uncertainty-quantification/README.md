# CE-RISE Uncertainty Quantification Data Model

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20084514.svg)](https://doi.org/10.5281/zenodo.20084514) [![Schemas](https://img.shields.io/badge/Schema%20Files-LinkML%2C%20JSON%2C%20SHACL%2C%20OWL-32CD32)](https://ce-rise-models.codeberg.page/uncertainty-quantification/)

This repository defines the CE-RISE cross-cutting data model for uncertainty quantification.
It provides generic structures for representing uncertainty in measurements, assessments,
model outputs, indicators, and derived values, including uncertainty statements,
distributions, coverage intervals, budgets, components, propagation analyses, and
comparison metadata.

The model is part of the cross-cutting utility layer in the CE-RISE Digital Material and
Product Passport architecture. It is designed to be called from other CE-RISE data models
without forcing those models to duplicate uncertainty logic.

---

## Data Model Structure

The Uncertainty Quantification data model is structured as a reusable utility model for
Digital Product Passport and Digital Material Passport records. It is not tied to a single
domain model: instead, it provides uncertainty records that can be embedded in, or referenced
from, other CE-RISE models such as product profile, material profile, diagnostic results,
integrated LCA, RE indicators, and future assessment models.

Built using [LinkML](https://linkml.io/), the model generates multiple schema formats
(JSON Schema, SHACL, OWL/Turtle) from one canonical YAML definition.

**Core Philosophy**: this model answers uncertainty-specific questions that other models
should not need to solve repeatedly:

- **"Which value is uncertain?"** -> cross-model targeting of a model, class, slot, record, or value path
- **"What is the measurand?"** -> operational definition of the quantity, method, conditions, and boundary
- **"How is uncertainty represented?"** -> distribution, interval, standard uncertainty, expanded uncertainty, or factor
- **"Where does the uncertainty come from?"** -> uncertainty budget, components, Type A/Type B evidence, correlations
- **"How was uncertainty propagated?"** -> analytical/GUM, Monte Carlo, Bayesian, sensitivity, scenario, or hybrid methods
- **"Can values be compared?"** -> traceability and boundary compatibility assessment

Metrological traceability and data quality are handled by separate cross-cutting models. This
model references them through lightweight fields rather than duplicating their content.

### Key Design Principles

1. **Cross-cutting by design**: uncertainty can be attached to values from any CE-RISE data model.
2. **No compulsory domain fields**: fields remain optional so the model can support partial records and progressive enrichment.
3. **Standards-aligned, not standards-duplicating**: concepts follow JCGM GUM, VIM, ISO/IEC 17025, ISO 5725, and related guidance without importing a single external uncertainty ontology wholesale.
4. **Reference-friendly integration**: other models can use an `uncertainty_statement_identifier_value` or embed an `UncertaintyStatement`.
5. **Separation of concerns**: traceability details belong in `metrological-traceability`; data quality scoring belongs in `data-quality-framework`.
6. **Multiple uncertainty representations**: supports probability distributions, coverage intervals, uncertainty budgets, expanded uncertainty, coefficient of variation, and uncertainty factors.
7. **Publication pipeline compatibility**: the model follows the standard CE-RISE LinkML structure and publication pipeline.

### Core Hierarchy

```
UncertaintyQuantification (root)
├── 1. UncertaintyStatement (multivalued)
│   ├── target references (model, class, slot, record, value path)
│   ├── QuantityValue
│   ├── MeasurandSpecification
│   ├── UncertaintyDistribution
│   ├── UncertaintyInterval
│   ├── UncertaintyBudget
│   └── PropagationAnalysis
├── 2. UncertaintyBudget (multivalued)
│   ├── InputQuantity
│   ├── UncertaintyComponent
│   ├── Correlation
│   ├── combined standard uncertainty
│   ├── expanded uncertainty
│   └── coverage factor and probability
├── 3. PropagationAnalysis (multivalued)
│   ├── output distribution
│   ├── output interval
│   ├── SensitivityResult
│   └── ScenarioUncertainty
├── 4. ComparisonAssessment (multivalued)
│   ├── left and right uncertainty statement references
│   ├── traceability match
│   ├── boundary match
│   └── comparison decision
├── 5. MethodReference (multivalued)
└── 6. EvidenceReference (multivalued)
```

### Workflow Sequence

#### **Step 1: UncertaintyStatement**
Reusable statement describing uncertainty for a reported value, model output, field, dataset, or comparison:

- **Uncertainty statement identifier**: stable identifier that other CE-RISE models can reference
- **Target references**: model, class, slot, record, value path, or value identifier
- **Reported value**: optional numeric, textual, categorical, interval, calculated, measured, simulated, or estimated value
- **Traceability reference**: pointer to metrological traceability records
- **Data quality reference**: pointer to data quality assessments used to justify uncertainty
- **Evidence and standards**: references to certificates, reports, standards, software, or literature

#### **Step 2: MeasurandSpecification**
Operational definition of what the uncertainty statement is about:

- **Measurand identifier and name**: stable reference to the quantity or value of interest
- **Quantity kind and unit**: quantity classification and unit information, aligned with QUDT-style concepts
- **Object or matrix**: product, material, sample, population, dataset, or system being evaluated
- **Method and standard**: measurement, test, calculation, or modelling method and version
- **Measurement model**: equation, statistical model, or calculation model relating inputs to the result
- **Conditions and boundary**: environmental conditions, reference conditions, system boundary, corrections, rounding, and decision rules

#### **Step 3: Uncertainty Representation**
Probability and interval structures for communicating uncertainty:

- **UncertaintyDistribution**: normal, lognormal, triangular, uniform, rectangular, empirical, discrete, multimodal, or custom distributions
- **DistributionParameter**: flexible name-value-unit parameters such as mean, standard deviation, minimum, maximum, shape, or scale
- **UncertaintyInterval**: coverage intervals, expanded uncertainty intervals, percentile intervals, credible intervals, tolerance intervals, and decision intervals
- **Core uncertainty quantities**: standard uncertainty, relative standard uncertainty, combined standard uncertainty, expanded uncertainty, coverage factor, coverage probability, coefficient of variation, and uncertainty factor

#### **Step 4: UncertaintyBudget**
Structured account of uncertainty sources and their combination:

- **InputQuantity**: model input estimates with units, uncertainty, distributions, and references
- **UncertaintyComponent**: individual contribution from repeatability, reproducibility, calibration, sampling, method bias, model discrepancy, data quality, boundary conditions, software, or other sources
- **Evaluation type**: Type A, Type B, mixed, data-quality-derived, expert judgement, or scenario-based evaluation
- **Correlation**: covariance and correlation coefficients between input quantities or components
- **Combined result**: combined standard uncertainty, expanded uncertainty, effective degrees of freedom, and coverage interval

#### **Step 5: PropagationAnalysis**
Description of how uncertainty is propagated from inputs to outputs:

- **Propagation method**: analytical/GUM, Monte Carlo, Bayesian updating, bootstrap, sensitivity analysis, scenario analysis, hybrid, or not evaluated
- **Model equation**: equation or reference to the computational model
- **Simulation metadata**: number of runs, random seed, software reference, and analysis timestamp
- **Output representation**: output distribution and output interval
- **SensitivityResult**: sensitivity drivers and quality hotspot flags
- **ScenarioUncertainty**: scenario-specific uncertainty for boundary, allocation, structural, or modelling alternatives

#### **Step 6: ComparisonAssessment**
Assessment of whether two uncertainty-backed values can be compared meaningfully:

- **Left and right statement references**: the uncertainty statements being compared
- **Traceability match**: whether the traceability bases are matching, compatible, partial, divergent, or not assessed
- **Boundary match**: whether method, scope, or system boundaries are compatible
- **Comparison decision**: direct comparison valid, valid with expanded uncertainty, conditional, not recommended, or infeasible
- **Additional uncertainty component**: optional component added when mismatch must be reflected quantitatively

### Data Properties

Each data-bearing field follows the CE-RISE `*_value` convention where applicable. Fields are
typed as `string`, `float`, `integer`, `boolean`, `date`, `datetime`, or `uri` depending on the
expected value. Object relationship fields connect the core classes, for example
`uncertainty_statements`, `reported_value`, `measurand`, `probability_distribution`,
`coverage_interval`, `uncertainty_budget`, and `propagation_analysis`.

The model intentionally avoids making uncertainty data compulsory. A consuming model may provide
only a simple uncertainty statement reference, while richer records can include full distributions,
budgets, components, propagation analyses, and evidence references.

#### SQL Identifiers

Every data point in the model includes a `sql_identifier` annotation that serves as a unique,
machine-friendly database identifier. These identifiers follow a structured namespace pattern to
ensure uniqueness across the entire data model:

**Pattern**: `uq_[category]_[specific_name]`

**Features:**
- **Uncertainty Quantification Prefix**: All identifiers start with `uq_` to clearly identify them as belonging to this cross-cutting model
- **Hierarchical Namespacing**: Uses category prefixes (`statement_`, `measurand_`, `distribution_`, `budget_`, `component_`, `propagation_`, `scenario_`, `comparison_`, `evidence_`) to provide context and prevent naming conflicts
- **Database-Friendly**: Uses underscores and avoids special characters for SQL compatibility
- **Unique Across Model**: No duplicate identifiers within the uncertainty model
- **Composition-Friendly**: Designed to coexist with identifiers from product, material, LCA, diagnostic, traceability, and data quality models

**Examples:**
- `uq_statement_identifier` - identifier for an uncertainty statement
- `uq_applies_to_value_path` - pointer to the external value being qualified
- `uq_measurand_description` - operational definition of the measurand
- `uq_distribution_type` - probability distribution type
- `uq_combined_standard_uncertainty` - combined standard uncertainty
- `uq_coverage_factor` - coverage factor used for expanded uncertainty
- `uq_component_identifier` - identifier for an uncertainty component
- `uq_propagation_method` - uncertainty propagation method
- `uq_traceability_reference` - reference to a metrological traceability record
- `uq_data_quality_reference` - reference to a data quality assessment

This identifier system enables seamless integration with databases and ensures clear data model
composition when combining with other CE-RISE data models.

---

## Development Roadmap

| Step | Component | Criticalities Identified | Solutions Implemented | Status | Missing/TODO |
|------|-----------|-------------------------|----------------------|--------|--------------|
| **1** | **Cross-Model UncertaintyStatement** | • Other models need a clean way to attach uncertainty without duplicating uncertainty structures<br>• Uncertainty may apply to a field, value, record, dataset, model output, or comparison<br>• Direct embedding is not always practical | • Added reusable `UncertaintyStatement` class<br>• Added target references for model, class, slot, record, value path, and value identifier<br>• Added traceability and data quality reference fields<br>• Added evidence and standards reference fields | **COMPLETED** | • Add concrete examples for product, material, diagnostic, and LCA consumers |
| **2** | **Measurand and Value Context** | • Values are not comparable unless the measurand, method, conditions, and boundary are explicit<br>• Some values are measured; others are calculated, simulated, estimated, categorical, or interval-based | • Added `MeasurandSpecification` for quantity, unit, object/matrix, sample, method, model, boundary, conditions, corrections, and decision rules<br>• Added `QuantityValue` for numeric, text, unit, type, timestamp, and source | **COMPLETED** | • Align examples with metrological traceability model once available |
| **3** | **Distribution and Interval Representation** | • Uncertainty may be a full probability distribution, a summary statistic, an interval, or a multiplicative factor<br>• DQA-derived uncertainty may use CV% or uncertainty factors | • Added `UncertaintyDistribution`, `DistributionParameter`, and `UncertaintyInterval`<br>• Added distribution and interval enums<br>• Added standard uncertainty, expanded uncertainty, coverage factor, coverage probability, CV, and uncertainty factor fields | **COMPLETED** | • Add sample instances for normal, lognormal, triangular, and empirical distributions |
| **4** | **Uncertainty Budget and Components** | • Uncertainty sources need to be visible and traceable<br>• Type A/Type B evaluation, correlations, and data-quality-derived components must be representable | • Added `UncertaintyBudget`, `InputQuantity`, `UncertaintyComponent`, and `Correlation`<br>• Added uncertainty source and evaluation type enums<br>• Added component-level traceability, data quality, and evidence references | **COMPLETED** | • Add examples for measurement, model discrepancy, and data-quality-derived components |
| **5** | **Propagation, Sensitivity, and Scenario Analysis** | • Uncertainty can be propagated analytically, numerically, or through scenario analysis<br>• LCA and model outputs need sensitivity and scenario support | • Added `PropagationAnalysis`, `SensitivityResult`, and `ScenarioUncertainty`<br>• Added analytical/GUM, Monte Carlo, Bayesian, bootstrap, sensitivity, scenario, hybrid, and not-evaluated methods<br>• Added simulation metadata and quality hotspot flags | **COMPLETED** | • Add examples for Monte Carlo and scenario comparisons |
| **6** | **Comparison Assessment** | • Two values may not be comparable if traceability, method, or boundary differ<br>• Mismatch may require expanded uncertainty or a conditional comparison decision | • Added `ComparisonAssessment` with traceability match, boundary match, comparison decision, and optional additional uncertainty component | **COMPLETED** | • Define comparison examples with metrological traceability and data quality models |

### Integration Opportunities

- **CE-RISE metrological-traceability**: reference traceability chains, calibration hierarchies, method-defined traceability, and boundary-defined traceability.
- **CE-RISE data-quality-framework**: reference data quality scores, pedigree assessments, data limitations, and DQA-to-uncertainty translations.
- **QUDT**: semantic alignment for quantities, units, numeric values, and quantity kinds.
- **PROV-O**: provenance of evidence, generated uncertainty statements, software, agents, and derivation.
- **SOSA/SSN**: observation procedures, features of interest, observed properties, sensors, and sampling context.
- **W3C DQV**: data quality concepts where this model needs to point to quality metrics or quality annotations.
- **JCGM GUM/VIM and ISO standards**: conceptual basis for measurand, standard uncertainty, Type A/Type B evaluation, uncertainty budget, expanded uncertainty, coverage interval, and coverage factor.
- **CE-RISE consumer models**: product-profile, material-profile, diagnostic-results, integrated-lca, re-indicators-specification, and future utility or assessment models.

---

## Publishing

Release artifacts for each version (`schema.yaml`, `schema.json`, `shacl.ttl`, `model.ttl`)
are served directly from this URL:
```
https://ce-rise-models.codeberg.page/uncertainty-quantification/
```

---

## Accessing Previous Releases

If you want to view the files published for version `v0.0.1`, open:

```
https://codeberg.org/CE-RISE-models/uncertainty-quantification/src/tag/pages-v0.0.1/generated/
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
