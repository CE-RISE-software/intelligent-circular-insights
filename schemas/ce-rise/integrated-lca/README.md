# CE-RISE Integrated Life Cycle Analysis

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.17910373.svg)](https://doi.org/10.5281/zenodo.17910373) [![Schemas](https://img.shields.io/badge/Schema%20Files-LinkML%2C%20JSON%2C%20SHACL%2C%20OWL-32CD32)](https://ce-rise-models.codeberg.page/integrated-lca/)

Repository for the data model used to represent integrated LCA results across environmental, social, economic, integrated, and other declared dimensions. It records study metadata, versioned assessment inputs, toolchains, methods, results, and interpretation. Inputs can include a versioned `product-system` record when available, as well as records from other CE-RISE or external models and datasets; their source content is not duplicated.

**Applicability**: This model supports both **Digital Product Passports (DPP)** and **Digital Material Passports (DMP)**, providing a flexible framework for LCA results regardless of whether the assessed entity is a finished product, raw material, component, or assembly.


---

## Data Model Structure

The Integrated Life Cycle Analysis data model provides a **flexible framework** for capturing results across environmental, social, economic, integrated, and other declared assessment dimensions. Rather than prescribing specific indicators, it allows results to reference external indicator standards and methodologies, enabling compatibility with established and evolving assessment methods.

**Core Philosophy**: This model provides a structure for:
- **"What was assessed?"** → Explicit assessment dimensions and references to indicators, subcategories, metrics, or accounting frameworks
- **"What are the results?"** → Numeric values with units, uncertainty ranges
- **"Which method was used?"** → Method name, version, and applicable calculation model or factor set
- **"Which source records and tools were used?"** → Versioned source references, artifacts, transformations, and tool executions
- **"How reliable are the results?"** → Data quality, completeness, uncertainty
- **"What standards apply?"** → ISO 14040/14044, UNEP social LCA guidance, ISO 15686-5, and applicable sector standards

### Key Design Principles

1. **Explicit Assessment Dimensions**: Environmental, social, economic, integrated, and other declared dimensions are represented directly
2. **Method Transparency**: Clear documentation of assessment methods and calculation models
3. **Uncertainty Quantification**: Confidence intervals, sensitivity analysis results
4. **Comparability**: Standardized units and normalization factors
5. **Interoperability**: Alignment with ISO 14040/14044, GHG Protocol, and social LCA guidelines

### Core Hierarchy

```
IntegratedLCAResults (root)
├── LCAAnalysisInstance (repeatable - multiple analyses possible)
│   ├── 1. LCAStudyMetadata
│   │   ├── StudyIdentifier
│   │   ├── StudyName
│   │   ├── StudyDate
│   │   ├── AssessmentDimensions
│   │   ├── CommissionerInfo
│   │   │   ├── OrganizationName
│   │   │   └── ContactInfo
│   │   ├── PractitionerInfo
│   │   │   ├── OrganizationName
│   │   │   ├── AuthorName
│   │   │   └── ContactInfo
│   │   ├── SoftwareInfo
│   │   │   ├── SoftwareName
│   │   │   ├── SoftwareVersion
│   │   │   └── CalculationTimestamp
│   │   ├── AssessmentToolchain
│   │   │   └── AssessmentToolExecution (repeatable)
│   │   │       ├── ToolRoles
│   │   │       ├── ToolReference
│   │   │       └── ConfigurationReference
│   │   ├── DatabaseInfo
│   │   │   ├── BackgroundDatabase
│   │   │   ├── DatabaseVersion
│   │   │   └── DataQualityInfo
│   │   ├── StudyScope
│   │   ├── FunctionalUnit
│   │   ├── FunctionalUnitSpecification
│   │   ├── SystemBoundaries
│   │   └── AssessmentBoundarySpecification
│   ├── 2. AssessmentResults
│   │   └── AssessmentIndicator (repeatable)
│   │       ├── AssessmentDimension
│   │       ├── IndicatorIdentifier
│   │       ├── IndicatorName
│   │       ├── AssessmentMethod
│   │       ├── MethodVersion
│   │       ├── IndicatorResult
│   │       │   ├── NumericValue
│   │       │   ├── Unit
│   │       │   └── UncertaintyRange
│   │       │       ├── LowerBound
│   │       │       ├── UpperBound
│   │       │       └── DistributionType
│   │       ├── LifeCycleStageResult (repeatable)
│   │       └── AggregatedResults
│   │           ├── SingleScore
│   │           ├── SingleScoreUnit
│   │           ├── NormalizedValue
│   │           ├── WeightedResult
│   │           └── WeightingSet
│   ├── 3. AssessmentInputSet
│   │   └── AssessmentInputReference (repeatable)
│   │       ├── InputRole
│   │       ├── SourceModel and SourceRecord references and versions
│   │       ├── SourceArtifact URI and checksum
│   │       └── DataSelectionReference
│   ├── 4. InterpretationResults
│   │   ├── LCADataQualityAssessment
│   │   │   ├── CompletenessCheck
│   │   │   ├── SensitivityAnalysis
│   │   │   └── ConsistencyCheck
│   │   ├── UncertaintyAnalysis
│   │   │   ├── ParameterUncertainty
│   │   │   ├── ModelUncertainty
│   │   │   └── ScenarioUncertainty
│   │   └── Limitations
│   │       ├── DataGaps
│   │       ├── MethodologicalChoices
│   │       └── Assumptions
│   └── 5. StandardCompliance
│       ├── ApplicableDimensions
│       ├── ApplicableStandards
│       ├── MethodReference
│       ├── IndicatorSetReference
│       ├── ValidationStatus
│       ├── ValidationDate
│       └── ValidatorInfo
```

### Workflow Sequence

#### **Step 1: LCAStudyMetadata**
Complete metadata for each LCA analysis instance:
- **StudyIdentifier**: Identifier for the LCA instance
- **PractitionerInfo**: Author/institution conducting the analysis
- **SoftwareInfo**: Primary software and version for simple single-tool cases
- **AssessmentToolchain**: Ordered tools and services for extraction, mapping, product-system generation, calculation, validation, aggregation, and reporting
- **DatabaseInfo**: Background database and version
- **FunctionalUnitSpecification**: Structured functional unit, reference flow, and scaling information
- **AssessmentBoundarySpecification**: Structured temporal, geographic, technological, lifecycle-stage, exclusion, and allocation scope
- **StudyScope**: Goal, intended application, target audience

*Note: Multiple LCAAnalysisInstance objects can represent distinct methods, assumptions, source selections, or temporal snapshots.*

#### **Step 2: AssessmentResults**
Flexible structure for indicators across declared sustainability dimensions:
- **AssessmentIndicator**: Repeatable result-bearing indicator with an explicit assessment dimension
- **IndicatorIdentifier**: URI or code pointing to an external indicator, subcategory, metric, or accounting framework
- **AssessmentMethod**: Method, model, or calculation approach used
- **MethodVersion**: Version of the method, model, or calculation approach
- **IndicatorResult**: Numeric value with unit and uncertainty range
- **LifeCycleStageResults**: Optional partitions by life cycle stage
- **AggregatedResults**: Optional normalized, weighted, valued, or otherwise aggregated results

#### **Step 3: AssessmentInputSet**
Versioned references to assessment inputs, without duplicating their source content:
- **AssessmentInputReference**: Repeatable source-model, source-record, artifact, version, and checksum reference
- **InputRole**: Declares whether the input is a product system, foreground or background inventory, product or material data, activity or event data, scenario, parameter set, evidence, or external dataset
- **DataSelectionReference**: Points to the query, mapping, transformation, or extraction specification used

#### **Step 4: InterpretationResults**
Quality and reliability assessment:
- **LCADataQualityAssessment**: Completeness, sensitivity, consistency checks
- **UncertaintyAnalysis**: Parameter, model, and scenario uncertainties
- **Limitations**: Documented data gaps and assumptions

#### **Step 5: StandardCompliance**
Links to external standards, methods, and validation:
- **ApplicableDimensions**: Dimensions to which the compliance statement applies
- **ApplicableStandards**: Standards, specifications, guidance, or normative references followed
- **MethodReference**: Link to full method or model documentation
- **IndicatorSetReference**: Indicator, subcategory, metric, or accounting framework used
- **ValidationStatus**: Third-party verification status
- **ValidationDate**: Date of validation or verification
- **ValidatorInfo**: Information about the validating organization or person

### Assessment Dimensions

Every `AssessmentIndicator` declares its `AssessmentDimension`; consumers must use this field rather than infer the dimension from an identifier, method name, or URI namespace. Environmental, social, and economic indicators can reference their applicable external standards and methods. `INTEGRATED` supports cross-dimensional or composite indicators, while `OTHER` retains extensibility for a declared dimension outside the enumerated set.

### Data Properties

Classes use direct LinkML attributes. Scalar attributes and permissible values intended for machine storage use the model's `sql_identifier` convention where applicable.

#### SQL Identifiers

`sql_identifier` annotations provide unique, machine-friendly database identifiers. They follow a structured namespace pattern to ensure uniqueness across the model:

**Pattern**: `lca_[category]_[specific_name]`

**Features:**
- **LCA Prefix**: All identifiers start with `lca_` to clearly identify them as belonging to the Integrated LCA data model
- **Hierarchical Namespacing**: Uses meaningful category prefixes to provide context and prevent naming conflicts
- **Database-Friendly**: Uses underscores and avoids special characters for SQL compatibility
- **Unique Across Model**: No duplicate identifiers, even when similar concepts appear in different parts of the hierarchy
- **Reasonable Length**: Abbreviated but meaningful names that balance clarity with practical database usage

**Examples:**
- `lca_study_functional_unit` - Functional unit in study metadata
- `lca_indicator_identifier` - Assessment indicator identifier
- `lca_indicator_dimension` - Assessment dimension
- `lca_assessment_input_source_record_uri` - Source record used as an assessment input
- `lca_method_reference` - Reference to method documentation

This identifier system enables seamless integration with databases and ensures clear data model composition when combining with other CE-RISE data models.

---

## Development Roadmap

| Step | Component | Criticalities Identified | Solutions Implemented | Status | Missing/TODO |
|------|-----------|-------------------------|----------------------|--------|--------------|
| **1** | **LCAStudyMetadata** | • Variable boundaries and functional units<br>• Multi-dimensional scope<br>• Provenance for multiple tools | • Structured functional-unit and boundary specifications<br>• Explicit assessment dimensions<br>• Ordered assessment toolchains | **COMPLETED** | • Study registry integration<br>• Automated metadata extraction |
| **2** | **AssessmentResults** | • Multiple assessment dimensions and indicator standards<br>• Evolving methods<br>• Method versioning | • Explicit dimension per indicator<br>• Reference-based method and indicator system<br>• Version tracking and stage partitions | **COMPLETED** | • Indicator registry APIs<br>• Automatic method updates<br>• Cross-method mapping |
| **3** | **AssessmentInputSet** | • Avoiding source-data duplication<br>• Inputs from different models and datasets<br>• Version and artifact traceability | • Reference-only input contract<br>• Source-model, record, artifact, version, and checksum references<br>• Declared input roles | **COMPLETED** | • Automatic reference validation<br>• Version compatibility checks<br>• Change detection alerts |
| **4** | **InterpretationResults** | • Quality assessment standards<br>• Uncertainty quantification<br>• Sensitivity analysis methods<br>• Documentation requirements | • Completeness, sensitivity, and consistency documentation<br>• Structured uncertainty and data-quality links<br>• Structured limitations | **COMPLETED** | • Automated quality scoring<br>• Uncertainty propagation tools |
| **5** | **StandardCompliance** | • Multiple assessment dimensions and standards<br>• Method documentation links<br>• Indicator-framework versions<br>• Validation tracking | • Applicable-dimension declarations<br>• External method links<br>• Indicator-framework references<br>• Validation status fields | **COMPLETED** | • Standard compliance checker<br>• Automated validation |

### Integration Opportunities

- **Assessment Toolchains**: PROV-O-aligned extraction, mapping, product-system generation, inventory calculation, assessment, aggregation, validation, and reporting tools
- **Impact Methods**: ReCiPe 2016, IMPACT World+, TRACI, CML-IA
- **Databases**: ecoinvent, GaBi databases, Agri-footprint, Social Hotspots Database
- **Standards**: ISO 14040/14044, UNEP social LCA guidelines, ISO 15686-5, and applicable sector standards
- **Reporting**: Environmental Product Declarations (EPD), Product Environmental Footprint (PEF)
- **CE-RISE and External Sources**: Versioned records and generated artifacts from product-system, other CE-RISE models, external models, datasets, and services can be recorded as assessment inputs
- **CE-RISE Utility Models**: LCA metadata, database information, assessment indicators, indicator results, uncertainty ranges, aggregated results, assessment inputs, interpretation records, limitations, and standard-compliance records can optionally reference `uncertainty-quantification`, `metrological-traceability`, and `data-quality-framework` records where relevant



---

## Publishing

Release artifacts for each version (`schema.json`, `shacl.ttl`, `model.ttl`)
are served directly from this URL:
```
https://ce-rise-models.codeberg.page/integrated-lca/
```


---

## Accessing Previous Releases

If you want to view the files published for version `v0.2.0`, open:

```
https://codeberg.org/CE-RISE-models/integrated-lca/src/tag/pages-v0.2.0/generated/
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

© 2025 CE-RISE consortium.  
Licensed under [Creative Commons Attribution–NonCommercial 4.0 International (CC BY-NC 4.0)](https://creativecommons.org/licenses/by-nc/4.0/).  
Attribution: CE-RISE project (Grant Agreement No. 101092281) and the individual authors/partners as indicated.

<a href="https://www.nilu.com" target="_blank" rel="noopener noreferrer">
  <img src="https://nilu.no/wp-content/uploads/2023/12/nilu-logo-seagreen-rgb-300px.png" alt="NILU logo" width="40"/>
</a>

Developed by NILU (Riccardo Boero — ribo@nilu.no) within the CE-RISE project.
