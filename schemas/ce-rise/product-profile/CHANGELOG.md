# Changelog

All notable changes to the CE-RISE Product Profile Data Model will be documented in this file.

## [0.2.0] - 2026-08-31

### Added
- Optional structured physical dimensions with OM 2 unit references.
- Optional GS1 GPC and multi-valued UNSPSC product classifications.

### Changed
- **Breaking:** `unspsc_code_value` is now multi-valued.
- Clarified GHS, safety, and regulatory classification fields, and deprecated legacy generic classification fields in favour of established controlled vocabularies and the compliance-and-standards model.

## [0.1.0] - 2026-05-12

### Added
- Optional `ProductSpecification` links to the CE-RISE uncertainty quantification, metrological traceability, and data quality framework utility models.

## [0.0.3] - 2025-12-16

### Added
- References from the Beta version of the data model

## [0.0.2] - 26 Nov 2025

### Added
- Stage 3 fields other than EORI number, and their specific values
- Stage 4 fields

### Changed
- Updated formatting requirements for the EORI number in stage 3
- Field requirements set to a minimum
- sql_identifier are unique thanks to hierarchical naming

### Removed
- Removed unnecessary old stage 4 and 5


## [0.0.1] - 26 Nov 2025

### Added
- Initial project structure and repository setup from template: https://ce-rise-models.codeberg.page/template-data-model/
- Initial data model structure for profile (derived from previous unreleased version and project deliverables)
- Artifacts built and deployed to pages
