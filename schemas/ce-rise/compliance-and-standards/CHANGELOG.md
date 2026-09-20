# Changelog

All notable changes to the CE-RISE Compliance and Standards Data Model will be documented in this file.

## [0.1.0] - 2026-05-12

### Added
- Optional links from compliance commitments, status decisions, requirement entries, evidence documents, certification details, audit records, KPIs, and compliance statements to the CE-RISE uncertainty quantification, metrological traceability, and data quality framework utility models.
- Utility-model fields are optional, so existing records that do not include uncertainty, traceability, or data quality details remain valid.

### Changed
- Disambiguated pre-existing duplicate `sql_identifier` annotations for root evidence/process slots and stakeholder-scope exclusions.

## [0.0.3] - 2026-02-03

### Breaking Changes
- **BREAKING**: Renamed classes and fields from "product" to "entity" terminology (`ProductCommitments` → `EntityCommitments`, `ProductEvidence` → `EntityEvidence`, `product_variants` → `entity_variants`, etc.)
- **BREAKING**: Updated SQL identifiers to reflect entity terminology

### Added
- Explicit support for Digital Material Passports (DMP) alongside Digital Product Passports (DPP)
- Unified "entity" terminology supporting products, materials, batches, and commodities
- DMP-related keywords to citation metadata
- Material-specific evidence types: MATERIAL_CERTIFICATE, MATERIAL_DATASHEET, SAFETY_DATA_SHEET, GRADE_CERTIFICATE, CHEMICAL_ANALYSIS, ORIGIN_CERTIFICATE, MATERIAL_PROPERTIES_TEST
- Batch/lot identifier tracking in ScopeOfEvidence for materials tracked at batch level
- Enhanced ontology references: BFO, CHEBI, DCAT for material-specific evidence types
- Standard references: EN 10204, ISO 10474, ISO/IEC 17025, ASTM E-series, UN GHS, REACH Annex II, ISO 22000, OECD Due Diligence Guidance

### Changed
- All documentation now uses "entity" or "products and materials" terminology

## [0.0.2] - 2025-12-15

### Added
- Missing relevant references from Beta data model release

## [0.0.1] - 2025-12-15

### Added
- Complete implementation of all 5 stages of the Compliance and Standards data model
- **Stage 1: ProductCommitments** - Flexible commitment framework with multi-category support and jurisdiction-aware status tracking
- **Stage 2: ApplicableRegulationStandards** - Requirements tracking with multi-jurisdictional applicability and version management
- **Stage 3: ProductEvidence** - Unified evidence framework with digital signatures and version-aware scope
- **Stage 4: ProcessEvidence** - Management systems with audit trails and performance metrics
- **Stage 5: RegulatoryInformation** - Market-agnostic regulatory information including safety, instructions, and identifiers
- External ontology integration via owl.filler pattern (dcterms, prov, schema, qudt, envo, foaf, org, vcard, time, dcat)
- SQL identifiers following pattern `comp_[category]_[specific_name]` for database integration
- Comprehensive enumerations for all type fields
- README hierarchy aligned with implemented model structure
