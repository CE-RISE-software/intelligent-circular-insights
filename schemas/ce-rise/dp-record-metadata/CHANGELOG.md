# Changelog

All notable changes to the CE-RISE DMP & DPP Record Metadata Data Model will be documented in this file.

## [0.0.2] - 2026-01-30

### Added
- Support for Digital Material Passports alongside Digital Product Passports
- Record scope field to distinguish product vs material records
- Expanded schema role examples to include material-specific roles
- Related passport linkage metadata with optional operation references

## [0.0.1] - 2025-12-10

### Added
- Initial implementation of DPP Record Metadata model for universal schema composition
- **Schema References**: Support for any schema type (CE-RISE, GS1, Schema.org, ISO, proprietary)
  - Dual reference system (URL or alternative identifier)
  - Schema type and language classification
  - Cryptographic hash verification with algorithm specification
  - Namespace management and documentation links
- **Schema Usage Context**: Metadata about how schemas are applied
  - Role classification (core-identity, sustainability-data, regulatory-compliance, etc.)
  - Profile and subset support
  - Dual completeness indicators (categorical and percentage)
  - Fallback schema references for graceful degradation
- **Composition Information**: How schemas fit in composite records
  - Sequence ordering for parsing
  - Composition methods (sequential, nested, mixed, overlay)
  - Data location pointers (JSONPath, XPath)
  - Dependency tracking
- **Metadata Versioning**: Version management for the metadata itself
  - Semantic versioning with compatibility levels
  - Lifecycle timestamps (created, modified)
  - Minimum parser version requirements
  - Language support (ISO 639-1)
- No required fields - fully flexible schema
- SQL identifiers with `dpm_` prefix for database integration
- Designed for open ecosystem - not limited to CE-RISE schemas
