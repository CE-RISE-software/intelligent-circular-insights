# Changelog

All notable changes to the CE-RISE RE-Indicators Specification Data Model will be documented in this file.

## [0.0.5] - 2026-04-09

### Changed
- Published `schema.yaml` is now generated as a standalone resolved LinkML schema including imported indicator and product modules, instead of copying only the root `model/model.yaml`
- Forgejo Pages build now generates `schema.yaml` as part of the artefact pipeline before deployment

### Fixed
- `calculation.json` now includes human-readable parameter names, question texts, and answer texts in addition to identifiers, weights, and scores

## [0.0.4] - 2026-03-26

### Added
- Dedicated generated `calculation.json` artifact for runtime scoring, separated from validation artifacts

### Changed
- Published artifacts now distinguish validation/semantics outputs (`schema.json`, `shacl.ttl`, `model.ttl`) from the runtime computation output (`calculation.json`)

## [0.0.3] - 2026-02-11

### Added
- SPARQL-based SHACL completeness constraints ensuring all parameters and questions are answered when an Assessment references a specific indicator-product configuration
- Core Hierarchy documentation in README showing complete class structure
- Workflow Sequence documentation explaining specification development and product assessment workflows

### Changed
- Completeness constraints automatically merged into generated SHACL file for single-file validation

## [0.0.2] - 2026-02-06

### Added
- REfurbish indicator complete for Laptop with 99 questions across 4 parameter groups (P1-P4: product-design, support, refurbish-specific, cleaning/polishing)
- REmanufacture indicator complete for Laptop and Printer with fully shared core parameters (P1-P4: inspection/testing, disassembly/assembly, cleaning, reprocessing)
- REpair indicator complete for Laptop with 10 parameters
- REuse indicator complete for Laptop and Printer with fully shared core parameters (P1-P5: diagnosis, warranty, reset, data confidentiality, ownership)
- REcycle indicator complete for all 5 products (PV, Battery, Laptop, Printer, Heatpump) with core and product-specific parameters

### Changed
- Architecture improvements for parameter reusability across products

### Fixed
- Resolved namespace collision blocking SHACL/OWL generation
- All schema generation (JSON Schema, SHACL, OWL) now working for all 5 products

## [0.0.1] - 14 Nov 2025

### Added
- Initial project structure and repository setup from template: https://ce-rise-models.codeberg.page/template-data-model/
- Initial data model structure for indicators 
- Artifacts built and deployed to pages
