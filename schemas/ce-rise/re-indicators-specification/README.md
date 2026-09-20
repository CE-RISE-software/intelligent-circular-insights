# CE-RISE RE-Indicators Specification Data Model

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.17610026.svg)](https://doi.org/10.5281/zenodo.17610026) [![Schemas](https://img.shields.io/badge/Schema%20Files-LinkML%2C%20JSON%2C%20SHACL%2C%20OWL-32CD32)](https://ce-rise-models.codeberg.page/re-indicators-specification/)


This repository provides the data model specifying the RE-indicators in the CE-RISE project.

Generated artifacts are intentionally split by purpose:
- `schema.json`, `shacl.ttl`, and `model.ttl` are validation and semantics artifacts
- `calculation.json` is a dedicated runtime scoring artifact with indicator configurations, parameter weights, question weights, and answer scores

## Artefact Usage Guidance

All published artefacts are derived from the same underlying LinkML data model, but they serve different roles and should not be used interchangeably.

### 1. Full specification and canonical reference

Use the published specification artefacts as the canonical source of truth for the model structure and identifiers:
- `schema.yaml` is the standalone resolved LinkML schema including imported indicator and product modules
- `schema.json` is the JSON Schema form of the model for JSON-oriented tooling
- `shacl.ttl` is the RDF validation artefact, including completeness constraints
- `model.ttl` is the OWL/RDF semantics artefact

These artefacts define the model, identifiers, and validation/semantic structure. They are the authoritative reference for what parameters, questions, answers, and relationships exist in a given version.

### 2. Runtime computation and frontend lookup

Use `calculation.json` for runtime scoring and for frontend lookup of human-readable questionnaire content.

This artefact is derived from the same specification, but is shaped for application use. It contains:
- indicator-product configurations
- parameter references and weights
- question identifiers and weights
- answer identifiers and scores
- human-readable parameter names
- human-readable question texts
- human-readable answer texts

Typical use cases:
- computing scores from selected answers
- resolving `parameter_id`, `question_id`, and `selected_answer_id` from assessment records into displayable labels and texts
- driving frontend questionnaires from a versioned specification artefact

### 3. Assessment data records

Assessment records should remain normalized and reference the published specification rather than duplicating the full questionnaire text.

In practice, an `Assessment` record should store:
- `model_version`
- `indicator_specification_id`
- parameter identifiers
- question identifiers
- selected answer identifiers
- computed scores and evidence fields

Assessment records are not expected to embed the full parameter name, question text, or answer text. Client applications should resolve those values against the corresponding published specification artefact for the same version, typically `calculation.json`.

### 4. Recommended integration pattern

For developers and downstream users, the recommended pattern is:
1. Publish a versioned model release
2. Derive `schema.yaml`, `schema.json`, `shacl.ttl`, `model.ttl`, and `calculation.json` from that same version
3. Create assessment records that reference that released specification by version and identifier
4. Use `calculation.json` to render human-readable questionnaires and to interpret normalized assessment records
5. Use `schema.json` or `shacl.ttl` for validation, depending on the data format and validation depth required

This keeps records compact and stable while ensuring that all human-readable content and scoring logic remain versioned and reproducible.

---

## Data Model Structure

### Core Hierarchy

The RE-Indicators data model is organized into two main class groups: **Specification Classes** (defining the indicator structure) and **Assessment Classes** (capturing actual product evaluations).

```
SPECIFICATION CLASSES (define indicator structure)
│
├── IndicatorProductConfiguration (root - links indicator to product)
│   ├── id (REQUIRED - e.g., "REcycle_PV")
│   ├── indicator_type (REQUIRED - REcycle, REuse, REpair, etc.)
│   ├── product_category (REQUIRED - PV, Laptop, Printer, etc.)
│   ├── name
│   ├── description
│   └── ParameterApplication (multivalued)
│       ├── parameter_ref (REQUIRED - reference to ParameterSpecification)
│       ├── weight (REQUIRED - 0.0 to 1.0)
│       └── applicable_questions (list of question IDs)
│
├── ParameterSpecification (abstract - defined in *_core.yaml)
│   ├── id (REQUIRED - unique identifier)
│   ├── name (REQUIRED - e.g., "Documentation availability")
│   ├── description
│   ├── weight (REQUIRED - 0.0 to 1.0)
│   ├── is_bonus (boolean - default false)
│   └── QuestionSpecification (multivalued, inlined)
│       ├── id (REQUIRED - e.g., "Q1.1")
│       ├── text (REQUIRED - question text)
│       ├── weight (REQUIRED - 0.0 to 1.0)
│       └── AnswerOption (multivalued, inlined, REQUIRED)
│           ├── id
│           ├── text (REQUIRED - answer text)
│           └── score (REQUIRED - 0.0 to 5.0)
│
ASSESSMENT CLASSES (capture actual evaluations)
│
└── Assessment (root - actual product evaluation)
    ├── id (REQUIRED - unique identifier)
    ├── timestamp (REQUIRED - datetime of assessment)
    ├── model_version (REQUIRED - version used)
    ├── indicator_specification_id (REQUIRED - e.g., "REcycle_PV")
    ├── total_score (computed overall score)
    ├── ProductInfo (REQUIRED, inlined)
    │   ├── manufacturer
    │   ├── model
    │   ├── serial_number
    │   └── product_category (REQUIRED)
    └── ParameterAssessment (multivalued, inlined)
        ├── parameter_id (REQUIRED - reference to ParameterSpecification)
        ├── computed_score (REQUIRED - calculated parameter score)
        └── QuestionAnswer (multivalued, inlined)
            ├── question_id (REQUIRED - reference to QuestionSpecification)
            ├── selected_answer_id (ID of chosen AnswerOption)
            ├── answer_score (REQUIRED - score obtained)
            └── notes (optional evidence/justification)

ENUMS
├── IndicatorType: REuse, REpair, REmanufacture, REfurbish, REcycle
└── ProductCategoryType: PV, Battery, Laptop, Printer, HVAC, Heatpump
```

### Workflow Sequence

The RE-Indicators model supports two distinct workflows: **Specification Development** (creating and maintaining indicator definitions) and **Product Assessment** (evaluating actual products using those definitions).

#### **Workflow A: Specification Development** (for model developers/maintainers)

**Step 1: Define Core Parameters** (`model/indicators/*_core.yaml`)
Define reusable parameters with their questions and answer options in core library files:
- Create `ParameterSpecification` objects with unique IDs (e.g., `P1_documentation`)
- Define `QuestionSpecification` entries with weights within each parameter
- Specify `AnswerOption` choices with scores (0.0-5.0 scale)
- Set parameter weights and bonus flags
- **Result**: Centralized, reusable parameter definitions shared across products

**Step 2: Configure Product-Specific Weights** (`model/indicators/*_ProductName.yaml`)
Create product configurations that reference core parameters with custom weights:
- Create `IndicatorProductConfiguration` with indicator type and product category
- Add `ParameterApplication` entries referencing core parameters by ID
- Assign product-specific weights to each parameter (must sum to ≤1.0)
- Optionally filter applicable questions for this product
- **Result**: Product-specific scoring configurations (e.g., REcycle_PV, REcycle_Laptop)

**Step 3: Version and Publish**
Lock specifications with Git tags for reproducible assessments:
- Tag releases (e.g., `v1.0.0`) to version both core parameters and product configs
- Generate schema artifacts (JSON Schema, SHACL, OWL)
- Publish to documentation website
- **Result**: Stable, citable specifications for assessments

#### **Workflow B: Product Assessment** (for assessors/users)

**Step 1: Create Assessment Instance**
Initialize an `Assessment` object with metadata:
- Generate unique assessment ID
- Record timestamp and model version used
- Capture `ProductInfo` (manufacturer, model, serial number, category)
- Reference the applicable `indicator_specification_id` (e.g., "REcycle_PV")
- **Result**: Documented assessment context

**Step 2: Answer Questions for Each Parameter**
For each parameter in the product configuration, answer all applicable questions:
- Create `ParameterAssessment` entry linking to parameter ID
- For each question, create `QuestionAnswer` with:
  - Selected answer option ID
  - Score from that answer (0.0-5.0)
  - Optional notes/evidence
- **Result**: Complete question responses with justification

**Step 3: Calculate Parameter Scores**
Compute weighted scores for each parameter:
- **Formula**: `parameter_score = Σ(question_score × question_weight)`
- Store in `ParameterAssessment.computed_score`
- Verify weights sum to 1.0 within each parameter
- **Result**: Normalized parameter scores (0.0-5.0 scale)

**Step 4: Calculate Total Indicator Score**
Compute overall indicator score across all parameters:
- **Formula**: `total_score = Σ(parameter_score × parameter_weight) / 5.0`
- Handle bonus parameters separately (can exceed 1.0)
- Store in `Assessment.total_score`
- **Result**: Final indicator score (0.0-1.0 scale, where 1.0 = best)

**Step 5: Document and Export**
Finalize the assessment with full traceability:
- Ensure all required fields are populated
- Include evidence and notes for transparency
- Export to JSON, RDF, or other formats
- Reference the specific model version used
- **Result**: Complete, auditable assessment record

### Completeness Validation

**Requirement**: If an Assessment references a specific indicator-product configuration version (e.g., `REcycle_PV v1.0.0`), then **ALL** parameters and **ALL** questions from that version **MUST** be answered.

#### Implementation

The model enforces completeness through **SPARQL-based SHACL constraints** automatically merged into `generated/shacl.ttl`:

1. **Parameter Coverage**: Validates that Assessment contains a `ParameterAssessment` for every parameter defined in the referenced `IndicatorProductConfiguration`
2. **Question Coverage**: Validates that each `ParameterAssessment` contains a `QuestionAnswer` for every question defined in the referenced `ParameterSpecification`
3. **Answer Selection**: Validates that each `QuestionAnswer` has a `selected_answer_id` (answer must be chosen)

#### Format Support

| Format | Completeness Validation | Notes |
|--------|------------------------|-------|
| **JSON Schema** | ❌ Not supported | Cannot validate cross-document references |
| **Calculation Artifact** | ❌ Not applicable | Runtime scoring data only; not a validation artifact |
| **SHACL** | ✅ **Full support** | SPARQL-based constraints included in generated SHACL |
| **OWL** | ❌ Not supported | Class-level constraints only |

#### Usage

When validating Assessment data:

```bash
# The generated SHACL includes completeness constraints automatically
shacl validate \
  --shapes generated/shacl.ttl \
  --data assessment-data.ttl
```

**Validation will fail if:**
- Assessment is missing any parameter from the specification
- ParameterAssessment is missing any question from the parameter
- QuestionAnswer does not have a selected answer

### Architecture Overview

The CE-RISE RE-Indicators data model implements a three-layer architecture for maximum reusability and clear versioning:

### 1. Core Model Layer (`model/model.yaml`)
Defines abstract classes that form the foundation:
- **Indicators**: The 5 RE indicators (REcycle, REuse, REpair, REmanufacture, REfurbish)
- **Parameters**: Scoreable components within indicators (e.g., Documentation availability)
- **Questions**: Individual assessment questions with weights
- **Assessments**: Structure for recording actual product evaluations

### 2. Core Parameter Libraries (`model/indicators/*_core.yaml`)
Centralized definitions of reusable parameters, questions, and answer options:

```yaml
# Example: REcycle_core.yaml
Documentation_Parameter:
  id: P1_documentation
  name: Documentation availability
  questions:
    - Q1.1: Unique Product identifier (weight: 0.05)
    - Q1.2: Bill of materials (weight: 0.45)
    - Q1.3: Safety manual (weight: 0.25)
    - Q1.4: Disassembly manual (weight: 0.25)
  answer_options:
    - Publicly available (score: 5.0)
    - Available to independent recyclers (score: 4.0)
    - Available to authorized recyclers (score: 3.0)
    - Available to manufacturers only (score: 1.0)
    - Not available (score: 0.0)

# All 6 REcycle parameters defined once and reused across products
```

### 3. Product Configuration Layer (`model/indicators/*_ProductName.yaml`)
Product-specific configurations that reference shared parameters with custom weights:

```yaml
# Example: REcycle_PV.yaml
REcycle_PV_Config:
  product_category: PV
  parameter_applications:
    - parameter_ref: P1_documentation
      weight: 0.1
    - parameter_ref: P2_material_composition
      weight: 0.3
    - parameter_ref: P3_depollution
      weight: 0.1
    - parameter_ref: P4_dismantling
      weight: 0.1
    - parameter_ref: P5_recyclability_rate
      weight: 0.4
    - parameter_ref: P6_takeback_scheme
      weight: 0.1

# REcycle_Printer.yaml uses the same parameters with different weights
```

### Key Design Principles

1. **Core Parameter Libraries**: Common parameters, questions, and answer options are defined once and reused across products
2. **Product-Specific Weights**: Each product references shared parameters but can customize their relative importance (weights)
3. **Namespace Isolation**: Centralized parameter definitions eliminate naming conflicts between products
4. **DRY Architecture**: Questions and scoring are maintained in a single location, reducing duplication and maintenance
5. **Version Lock**: Git tags (e.g., v1.0.0) lock both shared parameter definitions and product configurations
6. **Normalized Scoring**: All indicator final scores range from 0 to 1, where 1 represents the highest/best score (most recyclable, reusable, etc.) and 0 represents the lowest/worst score

### Data Properties

Each class has a corresponding value property (e.g., `name_value`, `company_id_value`) that holds the actual data. All value properties are string type except where specified otherwise.

#### SQL Identifiers

Every data point in the model includes a `sql_identifier` annotation that serves as a unique, machine-friendly database identifier. These identifiers follow a structured namespace pattern to ensure uniqueness across the entire data model:

**Pattern**: `reind_[indicator]_[category]_[specific_name]`

This identifier system enables seamless integration with databases and ensures clear data model composition when combining with other CE-RISE data models.


---

## Development Roadmap

### RE Indicators Status

The CE-RISE project defines 5 core Resource Efficiency indicators with specific product applicability:

| Indicator | Status | Relevant Product Groups | Progress |
|-----------|--------|------------------------|----------|
| **REcycle** | Complete | PV, Battery, Heatpump, Laptop, Printer | All 5 products complete with product-specific parameters |
| **REuse** | Complete | Laptop, Printer | All 2 products complete with shared core parameters |
| **REpair** | Complete | Laptop | 1/1 product complete |
| **REmanufacture** | Complete | Laptop, Printer | All 2 products complete with shared core parameters |
| **REfurbish** | Complete | Laptop | 1/1 product complete |

**Total Scope**: 11 indicator-product combinations (all complete)

### Current Implementation Status

#### Completed - REcycle Indicator (5/5 products)

#### Completed - REuse Indicator (2/2 products)

#### Completed - REpair Indicator (1/1 products)

#### Completed - REmanufacture Indicator (2/2 products)

#### Completed - REfurbish Indicator (1/1 products)


---

## Publishing

Release artifacts for each version (`schema.json`, `calculation.json`, `shacl.ttl`, `model.ttl`)  
are served directly from this URL:
```
https://ce-rise-models.codeberg.page/re-indicators-specification/
```

---

## Accessing Previous Releases

If you want to view the files published for version `v1.2.0`, open:

https://codeberg.org/CE-RISE-models/re-indicators-specification/src/tag/pages-v1.2.0/generated/

Files available in that directory typically include:

- schema.yaml
- schema.json
- calculation.json
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

© 2025 CE-RISE consortium.  
Licensed under [Creative Commons Attribution–NonCommercial 4.0 International (CC BY-NC 4.0)](https://creativecommons.org/licenses/by-nc/4.0/).  
Attribution: CE-RISE project (Grant Agreement No. 101092281) and the individual authors/partners as indicated.

<a href="https://www.empa.cch" target="_blank" rel="noopener noreferrer">
  <img src="https://www.empa.ch/image/company_logo?img_id=31464838&t=1762532293211" alt="EMPA logo" height="30"/>
</a>
<a href="https://www.nilu.com" target="_blank" rel="noopener noreferrer">
  <img src="https://nilu.no/wp-content/uploads/2023/12/nilu-logo-seagreen-rgb-300px.png" alt="NILU logo" height="20"/>
</a>

Developed by EMPA and NILU (Riccardo Boero — ribo@nilu.no) within the CE-RISE project.
