# Changelog

All notable changes to the CE-RISE Circularity and End-of-Life Data Model will be documented in this file.

## [0.1.1] - 2026-06-24

### Changed
- Clarified the `RecyclableMaterials.recycling_rate` description to state explicitly that it is a recycling rate per WFD Art. 3 (recycling only), distinct from the broader recovery rate in traceability. Description only - no rename or structural change.

### Added
- `WEEERecyclingStream` class and a new `weee_recycling_streams` attribute on `RecyclingPathways`, providing WEEE-specific stream-level detail per Directive 2012/19/EU: WEEE category (new `WEEECategoryEnum`, Annex III), stream fraction, recovery / recycling / preparation-for-re-use rates, allocation of treatment outcome to product input, and treatment process reference. Complements the existing generic `RecyclableMaterials`.
- Optional `sub_score_unit` field on `SubScore`, for the unit of a sub-score value where it is dimensional (left empty for dimensionless scores).

## [0.1.0] - 2026-05-12
### Added
- Optional links from circularity and end-of-life records to the CE-RISE uncertainty quantification, metrological traceability, and data quality framework utility models.
- Utility-model links for material composition, product-level summaries, material selection, disassembly and durability features, resource efficiency, lifespan factors, circular capability, circularity assessments, recycling pathways, CRM recovery, and treatment options.

## [0.0.3] - 2026-02-03
### Added
- BeginningOfLifeInformation section with material composition tracking and DMP references
- MaterialCompositionEntry structure for vectorized material-level data (mass, type, source, content percentages per material)
- ProductLevelSummary for aggregated product-level composition metrics
- DMP reference support via URI linking to Digital Material Passports

### Changed
- Updated model description to include beginning of life material composition
- Enhanced Key Design Principles with lifecycle completeness and material traceability


## [0.0.2] - 2025-12-15
### Added
- Missign references to lit etc. that were in Beta release of the data model.

## [0.0.1] - 2025-12-12
### Added
- Initial project structure and repository setup from template: https://ce-rise-models.codeberg.page/template-data-model/
- Complete data model structure for Circularity and End-of-Life with 4 implementation stages:
  - **Stage 1: DesignForCircularity** - Design features enabling circular economy (modularity, materials, disassembly, durability)
  - **Stage 2: ProductPerformanceFactors** - Quantifiable performance metrics (resource efficiency, lifespan factors, circular capability)
  - **Stage 3: CircularityAssessments** - Generic assessment container supporting multiple methodologies with sub-scores
  - **Stage 4: EndOfLifeInformation** - Comprehensive EOL pathways (collection, recycling, CRM recovery, treatment options)
- External ontology imports using owl.filler pattern:
  - CHEBI for chemical entities and hazardous substances
  - ENVO for environmental concepts (waste, emissions, landfill)
  - Schema.org for instructions, lifetime, maintenance
  - QUDT for quantities and units
  - BFO for temporal/reliability concepts
  - ODP for design patterns
  - Dublin Core for metadata and provenance
- Unique SQL identifiers for all fields following `circ_[category]_[specific]` pattern
- Support for multiple assessments over time (repeatable/multivalued)
- Autonomous model design with interoperability potential
- No required fields maintaining flexibility
- Appropriate data types (float for percentages/metrics, string for descriptions, date for timestamps)
- Critical Raw Materials (CRM) recovery tracking
- Multi-valued material lists for comprehensive tracking
- Artifacts built and deployed to pages
