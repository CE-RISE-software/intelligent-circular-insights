# Changelog

All notable changes to the CE-RISE Integrated Life Cycle Analysis Data Model will be documented in this file.

## [0.2.0] - 2026-08-27
### Added
- Explicit environmental, social, economic, integrated, and other assessment dimensions.
- Versioned references to product-system, CE-RISE model, external-model, and dataset inputs.
- Assessment toolchains with PROV-O mappings for inputs and tool executions.
- Structured functional-unit and assessment-boundary specifications.
- Optional assessment-indicator results partitioned by life cycle stage.

### Changed
- **BREAKING**: Renamed `impact_assessment_results` / `ImpactAssessmentResults` to `assessment_results` / `AssessmentResults` and `ImpactCategory` to `AssessmentIndicator`.
- **BREAKING**: Renamed `inventory_results` / `InventoryResults` to `assessment_inputs` / `AssessmentInputSet`.
- **BREAKING**: Renamed `AggregatedScores` to `AggregatedResults`.

## [0.1.0] - 2026-05-13
### Added
- Optional links from LCA metadata, database information, impact categories, indicator results, uncertainty ranges, aggregated scores, inventory references, interpretation records, limitations, and standard-compliance records to the CE-RISE uncertainty quantification, metrological traceability, and data quality framework utility models.
- Utility-model fields are optional, so existing LCA records without additional uncertainty, traceability, or data quality detail remain valid.

### Changed
- Renamed the local interpretation data-quality class from `DataQualityAssessment` to `LCADataQualityAssessment` to avoid a name collision with the imported CE-RISE data quality framework utility model.
- Prefixed local slot names `impact_method_value` and `numeric_value_value` with `lca_` to avoid import collisions with utility-model slots while preserving their existing `sql_identifier` annotations.

## [0.0.3] - 2026-02-03
### Breaking Changes
- **BREAKING**: Renamed `product_system_*` fields to `assessed_system_*` (reference, version, SQL identifiers)

### Added
- Explicit support for Digital Material Passports (DMP) alongside Digital Product Passports (DPP)
- Unified "assessed-system" model terminology supporting products, materials, components, and assemblies
- DMP-related keywords to citation metadata

### Changed
- All documentation and descriptions now use unified "assessed system" terminology
- Model references single unified `assessed-system` model instead of separate product/material models


## [0.0.2] - 2025-12-15
### Added
- Missing references from Beta release of data model.


## [0.0.1] - 2025-12-12
### Added
- Initial project structure and repository setup from template: https://ce-rise-models.codeberg.page/template-data-model/
- Complete data model structure for Integrated Life Cycle Analysis with 5 implementation steps:
  - **Step 1: LCAStudyMetadata** - Complete metadata for LCA analysis instances including study identification, practitioner/commissioner info, software/database details
  - **Step 2: ImpactAssessmentResults** - Flexible framework for environmental, social, and economic impact indicators with reference-based system
  - **Step 3: InventoryResults** - Reference-only approach linking to product-system model (no data duplication)
  - **Step 4: InterpretationResults** - Data quality assessment, uncertainty analysis, and limitations documentation
  - **Step 5: StandardCompliance** - Standards compliance tracking, validation status, and method references
- External ontology imports using owl.filler pattern:
  - Dublin Core Terms (dcterms) for metadata
  - PROV-O for provenance tracking
  - FOAF for organization definitions
  - Schema.org for contact and software information
  - ILCD for LCA-specific concepts
  - QUDT for units and measurements
- Unique SQL identifiers for all fields following `lca_[category]_[specific]` pattern
- Support for multiple LCA analyses on the same assessed system
- Triple bottom line support through flexible indicator references
- Documentation for representing Environmental, Social, and Economic components
- Artifacts built and deployed to pages
