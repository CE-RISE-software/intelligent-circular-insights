# Changelog

All notable changes to the CE-RISE Diagnostic Results Data Model will be documented in this file.

## [0.2.0] - 2026-08-31

### Added
- Optional `usage_based_prediction` structure for non-time-based failure forecasts using a condition-metrics counter reference and QUDT-aligned quantities.

### Changed
- Require `assessment_standard` whenever `overall_grade` is reported.

## [0.1.1] - 2026-06-24

### Added
- `TestingCertificate` class (Certificate of Testing / CoT) linked from `ComponentTestResults` via the new `testing_certificate` attribute. Captures certificate ID, issuing body, issue date, test standard, certified result, and document reference - required evidence for ICT diagnostic processes.
- `SoftwareVersionRecord` class and `DiagnosticSoftwareTypeEnum`, linked from the root `DiagnosticResults` via the new `software_versions` attribute. Captures the diagnosed product's own BIOS, firmware, OS, and driver versions with before/after values, update status, source, and verification date. DiagnosticSoftware remains scoped to the diagnostic tool, not the product.

## [0.1.0] - 2026-05-12

### Added
- Optional links from diagnostic test, measurement, reference, calibration, condition, sanitization, quality assessment, service, and predictive analytics records to the CE-RISE uncertainty quantification, metrological traceability, and data quality framework utility models.

### Changed
- Renamed local controlled vocabularies to diagnostic-specific names where needed to avoid symbol conflicts with imported utility models.

## [0.0.4] - 2026-05-12

### Added
- Replaced placeholder diagnostic branches with concrete LinkML classes for component inventory, component test results, condition metrics, data sanitization, quality assessment, service actions, and predictive analytics.
- Added supporting nested classes for measured values, reference values, test parameters, deviations, comparisons, calibration metadata, degradation indicators, data-bearing components, assessment criteria, quality issues, replaced parts, and risk factors.
- Added controlled vocabularies for component, test, calibration, condition, sanitization, quality, service, prediction, urgency, and severity concepts.

## [0.0.3] - 2025-12-16

### Added
- Missing references from Beta release of data model

## [0.0.2] - 2025-12-04

### SAME as [0.0.1] which failed deployment because of Codeberg malfunction

## [0.0.1] - 2025-12-04

### Added
- Initial project structure and repository setup from template: https://ce-rise-models.codeberg.page/template-data-model/
- Complete implementation of 8-step diagnostic workflow:
  - **Step 1: DiagnosticEvent** - Foundation event with context, environmental conditions, session metadata
  - **Step 2: ComponentInventory** - Generic component discovery with hierarchical structure support
  - **Step 3: ComponentTestResults** - Test results with measured/expected values, standards compliance
  - **Step 4: ConditionMetrics** - Health scoring, degradation tracking, remaining life estimation
  - **Step 5: DataSanitization** - Secure erasure tracking with methods, standards, certification
  - **Step 6: QualityAssessment** - Multi-scale grading with cosmetic/functional/performance scoring
  - **Step 7: ServiceActions** - Service and repair tracking with parts replacement
  - **Step 8: PredictiveAnalytics** - Failure prediction with risk factors and maintenance recommendations
- Comprehensive enum definitions for controlled vocabularies
- Ontology integration using owl.filler annotations (dcterms, prov, schema, qudt, sosa)
- Product-agnostic design supporting electronics, vehicles, industrial equipment, and more
- Pattern validation for identifiers, timestamps, and durations
- SQL-friendly identifier annotations for database integration
