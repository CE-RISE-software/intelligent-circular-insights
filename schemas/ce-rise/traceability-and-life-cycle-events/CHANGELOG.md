# Changelog

All notable changes to the CE-RISE Traceability and Life Cycle Events Data Model will be documented in this file.

## [0.1.1] - 2026-06-24

### Changed
- **Breaking:** `RefurbishmentEvent.components_replaced` changed from free-text `string` (multivalued) to a structured, repeatable `ReplacedComponent` object.
- Clarified the `RecyclingEvent.recovery_percentage` description to state explicitly that it is a recovery rate per WFD Annex II (recovery is broader than recycling), distinct from the recycling-specific rate in circularity-and-eol. Description only - no rename or structural change.

### Fixed
- **WFD Art. 3 compliance:** removed `ENERGY_RECOVERY` from `DisposalMethodEnum` - energy recovery is a recovery operation (WFD Annex II, R1), not disposal. Clarified `INCINERATION` as "without energy recovery" (WFD Annex I, D10). Added a `recovery_operation` field (new `RecoveryOperationEnum`: PREPARATION_FOR_REUSE, RECYCLING, ENERGY_RECOVERY, BACKFILLING, OTHER_RECOVERY) to `RecyclingEvent`, formally separating recycling from recovery and giving energy recovery its correct home.

### Added
- `DataErasureEvidence` class linked from `RefurbishmentEvent` via the new `data_erasure_evidence` attribute. Provides structured, auditable proof of secure data erasure (method, standard, tool, certificate ID, media serial, operator, timestamp, result, document reference), replacing reliance on free text. Typed with W3C PROV-O / SOSA / Dublin Core / schema.org and harmonised with the diagnostic-results `DataSanitization` class.
- `IntakeEvent` and `IntakeConditionItem` classes linked from `ReverseLogistics` via the new `intake_event` attribute, capturing device condition and triage at intake: structured condition findings (`condition_items` with `IntakeConditionCategoryEnum`), data-bearing `media_status`, `triage_decision` (`TriageDecisionEnum`), evidence references, plus the refurbisher-specific identifiers `intake_identifier`, `internal_asset_id`, `customer_asset_tag`, and `previous_owner_reference`.
- `ReplacedComponent` class (component name, old/new part number, old/new serial number, manufacturer, quantity, reason, condition), typed with schema.org / Dublin Core. Harmonised with the usage-and-maintenance `ReplacedComponent` and diagnostic-results `ReplacedPart` classes.
- New `IntakeConditionCategoryEnum` and `TriageDecisionEnum`.
- `PhysicalCustodyEvent` class and a new top-level `physical_custody` track on the root container, capturing in-workshop physical custody handoffs (holder, location, timestamp, transfer reason, sealed/open status) at workshop granularity (intake, storage, bench, data wipe, QA, resale), kept distinct from legal `OwnershipEvent`.
- New `CustodyStageEnum` and `SealStatusEnum`.
- Added `prov`, `dcterms`, and `sosa` prefixes to support standard ontology typing.

## [0.1.0] - 2026-05-12

### Added
- Optional links from selected lifecycle event classes to the CE-RISE uncertainty quantification, metrological traceability, and data quality framework utility models.

## [0.0.3] - 2026-02-03

### Breaking Changes
- **BREAKING**: Renamed classes and fields from "product" to "entity" terminology (`ProductHistory` → `EntityHistory`, `linked_product_identifier` → `linked_entity_identifier`, `input_products` → `input_entities`, etc.)
- **BREAKING**: Updated SQL identifiers to reflect entity terminology

### Added
- Explicit support for Digital Material Passports (DMP) alongside Digital Product Passports (DPP)
- Unified "entity" terminology supporting products, materials, batches, and commodities
- DMP-related keywords to citation metadata

### Changed
- All documentation now uses "entity" terminology with explicit coverage of products, materials, batches, and commodities

## [0.0.2] - 2025-12-16

### Added
- References from Beta release of the data model

## [0.0.1] - 2025-12-03

### Added
- Initial project structure and repository setup from template: https://ce-rise-models.codeberg.page/template-data-model/
- Complete data model structure for traceability and lifecycle events aligned with GS1 EPCIS 2.0
- Six core event categories: ProductHistory, OwnershipEvent, ValueAddingActivityLocation, ActorTracking, LogisticsEvents, ReverseLogistics
- Two additional event categories for comprehensive supply chain coverage: AggregationEvents and SupplyChainIncidents
- EPCIS 2.0 compatibility with proper vocabulary alignment using owl.filler annotations
- Support for GS1 standards (GLN, GTIN, EPC URIs) and UN/LOCODE for locations
- Comprehensive enumerations for ownership status, return reasons, recycling streams, disposal methods, packaging levels, incident types, severity levels, and resolution status
- SQL-friendly identifier system with trc_ prefix and hierarchical namespacing
- Integration with CE-RISE architecture through cross-model references
- Pattern validation for standard formats (GLN, UN/LOCODE, ISO durations, currency codes)
- Error declaration support for event corrections
- Sensor metadata support for IoT integration
- Complete reverse logistics pathway management including refurbishment, recycling, and disposal events
- Supply chain incident tracking with severity classification and corrective action management
- Packaging hierarchy tracking through aggregation/disaggregation events
- Artifacts built and deployed to pages
