# CE-RISE Diagnostic Results

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.17814486.svg)](https://doi.org/10.5281/zenodo.17814486) [![Schemas](https://img.shields.io/badge/Schema%20Files-LinkML%2C%20JSON%2C%20SHACL%2C%20OWL-32CD32)](https://ce-rise-models.codeberg.page/diagnostic-results/)

The Diagnostic Results data model captures **structured outputs from diagnostic, repair, service, and condition-assessment operations** throughout a product's lifecycle. These are event-bound results that provide point-in-time assessments of product health, performance, and maintenance needs.


---

## Data Model Structure

This model is designed to capture **time-stamped diagnostic events and their results**, complementing the dynamic supply chain events in the Traceability model. Built using [LinkML](https://linkml.io/), it generates multiple schema formats (JSON Schema, SHACL, OWL) for maximum interoperability.

**Core Philosophy**: This model answers critical questions about product condition and maintenance:
- **"What is the current health status?"** → Device self-diagnostics and condition monitoring
- **"What issues were found?"** → Error codes, fault detection, anomaly identification
- **"What was done about it?"** → Service reports, repair actions, calibrations
- **"What might happen next?"** → Predictive maintenance, remaining useful life estimates
- **"Is it performing to spec?"** → Performance metrics, compliance tests, quality assessments

This model focuses exclusively on diagnostic outputs and assessment results. Static product specifications are in the Product Profile model, while the actual maintenance schedules and instructions are in the Usage and Maintenance model.

## Model Boundaries Within CE-RISE Architecture

### What This Model INCLUDES:
- **Service and repair reports** - Technician assessments, repair documentation, service completion records
- **Automated diagnostic outputs** - Self-test results, built-in diagnostics, IoT sensor assessments
- **Performance test results** - Benchmark tests, stress tests, compliance verifications
- **Predictive analytics outputs** - Remaining useful life, failure probability, maintenance predictions
- **Calibration and certification results** - Calibration certificates, accuracy verifications
- **Error and fault records** - Error codes, fault trees, failure mode identifications
- **Condition monitoring snapshots** - Battery health, component wear levels, degradation metrics
- **Quality control test results** - Production tests, acceptance tests, periodic inspections
- **Component inventory documentation** - Discovery of any product components, serial tracking, configuration
- **Data sanitization records** - Secure erasure certificates for any data-bearing components
- **Quality grading assessments** - Condition grades, functional assessments, market categorization

### What This Model EXCLUDES (handled by other CE-RISE models):
- **Static product specifications** → `product-profile` model (design specs, nominal values)
- **Supply chain events** → `traceability-and-life-cycle-events` model (logistics, ownership)
- **Maintenance schedules and instructions** → `usage-and-maintenance` model (how-to guides, intervals)
- **Environmental impact data** → `integrated-lca` model (carbon footprint, resource use)
- **Compliance certifications** → `compliance-and-standards` model (regulatory approvals)

### Key Design Principles

1. **Event-Bound Results**: Every diagnostic output is tied to a specific timestamp and diagnostic event
2. **Structured Data Capture**: Results follow standardized formats for machine readability
3. **Traceability Linkage**: Each diagnostic event references the product and can link to supply chain events
4. **Multi-Source Support**: Accommodates human technicians, automated systems, and IoT devices
5. **Standards Alignment**: Uses established vocabularies (ISO 13374, MIMOSA, IEC 61508, IEEE standards)
6. **Severity Classification**: Clear categorization of issue severity and urgency
7. **Action Tracking**: Links findings to corrective actions and follow-up requirements
8. **Evidence Management**: Supports attachments, images, sensor data, and measurement records


### Core Hierarchy

```
DiagnosticResults (root)
├── 1. DiagnosticEvent
│   ├── EventIdentifier (UUID)
│   ├── EventTimestamp (ISO 8601)
│   ├── DiagnosticType (service/self-test/predictive/calibration/inspection)
│   ├── PerformedBy (technician ID or system ID)
│   ├── ProductReference (link to product-profile)
│   ├── LocationReference (facility/field location)
│   ├── EventTrigger (scheduled/failure/request/periodic)
│   ├── UnitIdentifier (internal tracking ID)
│   ├── BatchIdentifier (batch/lot reference)
│   ├── AssetReference (asset management ID)
│   ├── DiagnosticSoftware
│   │   ├── ToolName
│   │   ├── ToolVersion
│   │   ├── ToolVendor
│   │   ├── ToolCertification
│   │   └── ToolConfiguration
│   ├── EnvironmentalConditions
│   │   ├── AmbientTemperature
│   │   ├── Humidity
│   │   ├── Pressure
│   │   ├── TestEnvironment (lab/field/factory/customer)
│   │   └── OtherConditions
│   ├── SessionMetadata
│   │   ├── SessionDuration
│   │   ├── TestSequence
│   │   ├── TestsCompleted
│   │   ├── TestsAborted
│   │   └── AbortReasons
├── 2. ComponentInventory
│   ├── ComponentIdentifier
│   ├── ComponentType (generic classification)
│   ├── ComponentCategory
│   ├── Manufacturer
│   ├── Model
│   ├── PartNumber
│   ├── SerialNumber
│   ├── Version/Revision
│   ├── ComponentSpecifications (key-value pairs)
│   ├── SubComponents (nested components)
│   │   ├── SubComponentID
│   │   ├── SubComponentType
│   │   ├── SubComponentModel
│   │   ├── SubComponentSerial
│   │   └── SubComponentSpecs
│   └── ComponentHierarchy (parent-child relationships)
├── 3. ComponentTestResults
│   ├── TestIdentifier
│   ├── TestTimestamp
│   ├── ComponentReference (links to ComponentInventory)
│   ├── TestType (functional/performance/safety/compliance)
│   ├── TestName
│   ├── TestResult (pass/fail/warning/not-tested/inconclusive)
│   ├── MeasuredValues (with units)
│   ├── ReferenceValues
│   ├── TestStandard (if applicable)
│   ├── TestProtocolReference
│   ├── ComplianceStandard (ISO/IEC/ASTM/proprietary)
│   ├── TestParameters
│   ├── Deviations
│   ├── ObservationCodes
│   ├── ObservationNotes
│   ├── TestComparison
│   │   ├── ReferenceBaseline
│   │   ├── PeerComparison
│   │   └── SpecificationCompliance
│   ├── RetestRequired
│   ├── InconclusiveReason
│   ├── CalibrationTraceability
│   │   ├── TestEquipmentID
│   │   ├── LastCalibrationDate
│   │   └── CalibrationCertificate
│   └── TestingCertificate (Certificate of Testing / CoT)
│       ├── CertificateIdentifier
│       ├── IssuingBody
│       ├── IssueDate
│       ├── TestStandard
│       ├── CertificateResult
│       └── DocumentReference
├── 4. ConditionMetrics
│   ├── MetricIdentifier
│   ├── ComponentReference
│   ├── MetricType (health/wear/performance/capacity)
│   ├── MetricName
│   ├── CurrentValue
│   ├── NominalValue
│   ├── Unit
│   ├── HealthScore (0-100%)
│   ├── DegradationIndicators
│   │   ├── WearLevel
│   │   ├── UsageCycles
│   │   ├── OperatingHours
│   │   └── PerformanceDegradation
│   └── EstimatedRemainingLife
├── 5. DataSanitization
│   ├── SanitizationIdentifier
│   ├── DataBearingComponents (list)
│   │   ├── ComponentReference
│   │   ├── ComponentType
│   │   ├── DataCapacity
│   │   ├── SanitizationMethod
│   │   ├── SanitizationStandard
│   │   ├── SanitizationResult (success/failed/partial)
│   │   ├── VerificationMethod
│   │   ├── SanitizationTimestamp
│   │   ├── PerformedBy
│   │   └── CertificateReference
│   └── ComplianceCertification
├── 6. QualityAssessment
│   ├── QualityGrade
│   ├── GradingScale
│   ├── CosmeticCondition
│   ├── FunctionalCondition
│   ├── PerformanceScore
│   ├── AssessmentCriteria
│   └── QualityCheckResults
├── 7. ServiceActions
│   ├── ActionIdentifier
│   ├── ActionType (repair/replace/adjust/clean/update)
│   ├── ActionDescription
│   ├── ComponentsAffected
│   ├── PartsReplaced
│   │   ├── OldPartNumber
│   │   ├── NewPartNumber
│   │   └── Quantity
│   ├── ActionOutcome
│   ├── TimeSpent
│   └── TechnicianNotes
├── 8. PredictiveAnalytics
│   ├── PredictionIdentifier
│   ├── PredictionModel
│   ├── ComponentReference
│   ├── FailureProbability
│   ├── TimeToFailure
│   ├── ConfidenceLevel
│   ├── RecommendedActions
│   ├── MaintenanceUrgency
│   └── CostBenefitAnalysis
└── 9. SoftwareVersionRecord (product's own firmware/OS/drivers)
    ├── SoftwareType (BIOS/firmware/OS/driver/application)
    ├── ComponentReference
    ├── SoftwareName
    ├── VersionBefore
    ├── VersionAfter
    ├── UpdateStatus
    ├── UpdateSource
    └── VerificationDate
```

### Workflow Sequence

#### **Step 1: DiagnosticEvent**
Foundation for all diagnostic activities with complete context:
- **event_identifier**: UUID for each diagnostic event (pattern validated)
- **event_timestamp**: ISO 8601 datetime with timezone
- **diagnostic_type**: Classification (SERVICE/SELF_TEST/PREDICTIVE/CALIBRATION/INSPECTION/REFURBISHMENT)
- **performed_by**: Who/what performed diagnostic (technician ID, system ID, software)
- **event_trigger**: What initiated it (SCHEDULED/FAILURE/REQUEST/QUALITY_CHECK/INTAKE/ALERT)
- **technician_observations**: Technician observations during diagnostic
- **failure_description**: Description of failure or issue found
- **recommended_actions**: Recommended next steps or actions

**DiagnosticSoftware** (nested class):
- **tool_name**: Name of diagnostic software or tool
- **tool_version**: Version (critical for reproducibility)
- **tool_vendor**: Vendor or manufacturer
- **tool_certification**: Certification status if validated
- **tool_configuration**: Configuration settings used

**EnvironmentalConditions** (nested class):
- **temperature**: Temperature during testing (float with unit)
- **humidity**: Humidity percentage
- **pressure**: Atmospheric pressure
- **test_environment**: Type (LAB/FIELD/FACTORY/CUSTOMER_SITE/SERVICE_CENTER/REMOTE)
- **other_conditions**: Additional environmental factors

**SessionMetadata** (nested class):
- **session_duration**: Total duration in seconds
- **test_sequence**: Order of tests performed
- **tests_completed**: Number of tests successfully completed
- **tests_aborted**: Number of tests aborted
- **abort_reasons**: Reasons for any aborted tests

#### **Step 2: ComponentInventory**
Generic component discovery and documentation (hardware or software):
- **component_identifier**: Unique identifier (alphanumeric with -._)
- **component_type**: Classification (PROCESSOR/MEMORY/STORAGE/SENSOR/ACTUATOR/MODULE/ASSEMBLY/POWER/COMMUNICATION/DISPLAY/CONNECTOR)
- **component_category**: Higher-level (HARDWARE/SOFTWARE/FIRMWARE/MECHANICAL/ELECTRICAL/OPTICAL/HYDRAULIC/PNEUMATIC)
- **manufacturer**: Component manufacturer name
- **model**: Specific model designation
- **part_number**: Manufacturer part number
- **serial_number**: Component serial number
- **version**: Firmware or hardware revision

**ComponentSpecification** (nested class, multivalued):
- **spec_name**: Name of specification parameter
- **spec_value**: Value of specification
- **spec_unit**: Unit of measurement

**ComponentHierarchy** (nested class):
- **parent_component**: Reference to parent component_identifier
- **hierarchy_level**: Level in hierarchy (0 for root)
- **assembly_position**: Physical/logical position in parent

**sub_components**: Nested ComponentInventory objects for full hierarchy tracking

#### **Step 3: ComponentTestResults**
Generic component testing outcomes for any component type:
- **test_identifier**: Unique test batch ID
- **component_reference**: Links to specific component being tested
- **test_type**: FUNCTIONAL/PERFORMANCE/STRESS/CALIBRATION/DIAGNOSTIC
- **test_name**: Specific test performed
- **test_result**: PASS/FAIL/WARNING/INCONCLUSIVE/SKIPPED
- **measured_values**: Actual measurements with units
- **expected_values**: Expected/nominal values
- **test_standard**: Reference standard (ISO/IEC/ASTM)
- **test_protocol**: Which test protocol was followed
- **compliance_requirements**: Applicable compliance requirements
- **calibration_status**: Test equipment calibration status
- **retest_required**: Whether test needs re-running
- **inconclusive_reason**: Why test couldn't determine result
- **observation_codes**: Standardized defect or issue codes
- **observation_notes**: Technician notes on observed issues

#### **Step 4: ConditionMetrics**
Generic condition and health assessment for any component:
- **metric_identifier**: Unique metric ID
- **component_reference**: Which component is being measured
- **metric_type**: HEALTH/WEAR/PERFORMANCE/CAPACITY/EFFICIENCY/RELIABILITY
- **metric_name**: Specific metric (e.g., "battery_capacity", "bearing_vibration")
- **current_value**: Current measured value
- **nominal_value**: Expected/design value
- **metric_unit**: Measurement unit
- **health_score**: Overall health percentage (0-100%)
- **degradation_rate**: Rate of degradation
- **usage_cycles**: Number of usage cycles
- **operating_hours**: Total operating hours
- **estimated_remaining_life**: Predicted useful life remaining

#### **Step 5: DataSanitization**
Secure data erasure for any data-bearing component:
- **sanitization_identifier**: Unique sanitization event ID
- **component_reference**: Reference to data-bearing component
- **sanitization_method**: OVERWRITE/SECURE_ERASE/DEGAUSS/PHYSICAL_DESTRUCTION/CRYPTO_ERASE
- **sanitization_standard**: NIST_800_88/DoD_5220/GDPR/ISO_27001
- **sanitization_result**: SUCCESS/FAILED/PARTIAL/VERIFIED
- **sanitization_timestamp**: When completed
- **sanitization_user**: Who performed the sanitization
- **verification_method**: How sanitization was verified
- **certificate_issued**: Whether certificate was issued
- **certificate_reference**: Audit trail certificate reference
- **data_classification**: PUBLIC/INTERNAL/CONFIDENTIAL/SECRET

#### **Step 6: QualityAssessment**
Quality assessment for any product:
- **assessment_identifier**: Unique quality assessment ID
- **overall_grade**: Overall grade (A/B/C/D/F or custom)
- **grading_scale**: LETTER/NUMERIC/PERCENTAGE/CUSTOM
- **cosmetic_score**: Physical appearance score (0-100)
- **functional_score**: Operational capability score (0-100)
- **performance_score**: Performance metrics score (0-100)
- **assessment_criteria**: Individual criteria with scores and weights
- **quality_issues**: Issues found with type and severity
- **certification_status**: CERTIFIED/REFURBISHED/WARRANTY/NONE

#### **Step 7: ServiceActions**
Service and repair actions performed:
- **action_identifier**: Unique action ID
- **action_type**: REPAIR/REPLACE/ADJUST/CALIBRATE/CLEAN/UPDATE/CONFIGURE
- **action_description**: Description of action performed
- **component_reference**: Reference to affected component
- **action_timestamp**: When performed
- **action_duration**: Time spent (minutes)
- **performed_by**: Technician or system
- **parts_replaced**: Old and new part numbers/serials
- **action_result**: SUCCESS/FAILED/PARTIAL/PENDING
- **follow_up_required**: Whether follow-up needed

#### **Step 8: PredictiveAnalytics**
Predictive maintenance and failure analysis:
- **prediction_identifier**: Unique prediction ID
- **component_reference**: Component being analyzed
- **prediction_type**: FAILURE_RISK/MAINTENANCE_DUE/PERFORMANCE_DEGRADATION/END_OF_LIFE
- **failure_probability**: Likelihood of failure (0-100%)
- **time_to_failure**: Estimated time until failure (ISO 8601)
- **confidence_level**: Statistical confidence in prediction (0-100%)
- **prediction_model**: Model/algorithm used
- **recommended_maintenance**: Preventive measures suggested
- **urgency_level**: IMMEDIATE/HIGH/MEDIUM/LOW/SCHEDULED
- **cost_estimate**: Economic impact assessment
- **risk_factors**: Contributing factors with impact levels

### Data Properties

Each class has a corresponding value property (e.g., `event_id_value`, `health_score_value`) that holds the actual data. All value properties are string type except where specified otherwise (integers for counts, floats for measurements, datetime for timestamps).

#### SQL Identifiers

Every data point in the model includes a `sql_identifier` annotation that serves as a unique, machine-friendly database identifier. These identifiers follow a structured namespace pattern to ensure uniqueness across the entire data model:

**Pattern**: `diag_[category]_[specific_name]`

**Features:**
- **Diagnostic Prefix**: All identifiers start with `diag_` to clearly identify them as belonging to the Diagnostic Results data model
- **Hierarchical Namespacing**: Uses category prefixes (`event_`, `service_`, `test_`, `error_`, `condition_`, `predict_`, `calib_`) to provide context and prevent naming conflicts
- **Database-Friendly**: Uses underscores and avoids special characters for SQL compatibility
- **Unique Across Model**: No duplicate identifiers, even when similar concepts appear in different parts of the hierarchy
- **Reasonable Length**: Abbreviated but meaningful names that balance clarity with practical database usage

**Examples:**
- `diag_event_id` - Event identifier in DiagnosticEvent
- `diag_service_technician` - Technician ID in ServiceReport
- `diag_test_result` - Test result in DiagnosticOutput
- `diag_error_code` - Error code in ErrorFaultRecord
- `diag_condition_health_score` - Health score in ConditionAssessment
- `diag_predict_failure_prob` - Failure probability in PredictiveMaintenance
- `diag_calib_certificate_id` - Certificate ID in CalibrationCertificate

This identifier system enables seamless integration with databases and ensures clear data model composition when combining with other CE-RISE data models.

---

## Development Roadmap

> **Note:** This roadmap documents the model's initial development. The data model has since been further developed and refined — see [CHANGELOG.md](CHANGELOG.md) for the authoritative, up-to-date record of changes.

| Step | Component | Criticalities Identified | Solutions Implemented | Status | Missing/TODO |
|------|-----------|-------------------------|----------------------|--------|--------------|
| **1** | **DiagnosticEvent** | • Need for event tracking and context<br>• Diagnostic software tracking<br>• Environmental conditions<br>• Session metadata<br>• Focus on diagnostic outputs only | • UUID-based event IDs with pattern validation<br>• DiagnosticSoftware with version/vendor/certification<br>• Environmental conditions (temp/humidity/pressure)<br>• Session metadata with duration/completion tracking<br>• Technician observations and failure descriptions<br>• Recommended actions field<br>• Removed redundant identifiers (relies on product-profile model) | **COMPLETE** | • Event correlation APIs<br>• Software validation APIs |
| **2** | **ComponentInventory** | • Generic component model<br>• Hierarchical relationships<br>• Product-agnostic design<br>• Flexible specifications<br>• Hardware discovery | • Generic component classification with enums (type/category/status)<br>• Nested sub-components support<br>• Flexible key-value specifications<br>• Component hierarchy tracking<br>• Version/firmware/hardware ID management<br>• Component status detection (present/absent/operational)<br>• Support for any product type (electronics/vehicles/industrial) | **COMPLETE** | • Component database<br>• Auto-discovery APIs |
| **3** | **ComponentTestResults** | • Test standards traceability<br>• Calibration tracking<br>• Result confidence<br>• Comparison baselines<br>• Observation tracking | • Test protocol and standard references<br>• Compliance requirements tracking<br>• Calibration status and traceability<br>• Measured vs expected values<br>• Test conditions capture<br>• Inconclusive reason handling<br>• Observation codes and notes<br>• Retest flags | **COMPLETE** | • Test automation<br>• Standards library |
| **4** | **ConditionMetrics** | • Generic metrics framework<br>• Health scoring<br>• Degradation tracking<br>• Life estimation | • Flexible metric types (health/wear/performance/capacity)<br>• Current vs nominal value tracking<br>• Health score 0-100 scale<br>• Degradation rate and usage cycles<br>• Operating hours tracking<br>• Estimated remaining life (ISO 8601)<br>• Condition indicators with severity | **COMPLETE** | • Predictive models<br>• Trend analysis |
| **5** | **DataSanitization** | • Any data-bearing component<br>• Method verification<br>• Standards compliance<br>• Audit trails | • Component reference linkage<br>• Multiple sanitization methods (overwrite/secure erase/degauss/physical/crypto)<br>• Standards compliance (NIST 800-88/DoD 5220/GDPR/ISO 27001)<br>• Verification method tracking<br>• Certificate issuance and reference<br>• Data classification levels<br>• User and timestamp tracking | **COMPLETE** | • Automated verification<br>• Blockchain certificates |
| **6** | **QualityAssessment** | • Flexible grading scales<br>• Assessment criteria<br>• Quality checks<br>• Performance scoring | • Multiple grading scales (letter/numeric/percentage/custom)<br>• Separate cosmetic/functional/performance scores<br>• Weighted assessment criteria<br>• Quality issues with type and severity<br>• Certification status tracking<br>• Overall grade assignment | **COMPLETE** | • ML-based assessment<br>• Criteria automation |
| **7** | **ServiceActions** | • Service tracking<br>• Parts replacement<br>• Action outcomes<br>• Time documentation | • Action type classification (repair/replace/adjust/calibrate/clean/update/configure)<br>• Component reference linkage<br>• Replaced parts tracking with old/new part numbers<br>• Action result recording (success/failed/partial/pending)<br>• Duration tracking in minutes<br>• Follow-up requirement flags<br>• Performer identification | **COMPLETE** | • Service automation<br>• Parts inventory |
| **8** | **PredictiveAnalytics** | • Failure prediction<br>• Confidence levels<br>• Cost-benefit analysis<br>• Urgency classification | • Prediction types (failure risk/maintenance due/degradation/end-of-life)<br>• Failure probability 0-100%<br>• Time-to-failure estimates (ISO 8601)<br>• Confidence level tracking<br>• Prediction model/algorithm reference<br>• Recommended maintenance actions<br>• Urgency levels (immediate/high/medium/low/scheduled)<br>• Cost estimates<br>• Risk factor analysis with impact levels | **COMPLETE** | • AI/ML integration<br>• Real-time updates |

### Integration Opportunities

**Within CE-RISE Architecture:**
- **Product Profile Integration**: References product identifiers, specifications, and nominal values
- **Traceability Events Linkage**: Diagnostic events can trigger supply chain events (recalls, returns)
- **Usage and Maintenance Sync**: Results inform maintenance schedules and update usage patterns
- **Compliance Updates**: Test results feed into compliance status and certification renewals
- **LCA Impact**: Component replacements and failures inform environmental impact calculations
- **Uncertainty, Metrological Traceability, and Data Quality**: Selected diagnostic records can optionally reference `uncertainty-quantification`, `metrological-traceability`, and `data-quality-framework` utility model records

**External System Integration:**
- **CMMS/EAM Systems**: Computerized Maintenance Management System integration
- **IoT Platforms**: Real-time diagnostic data ingestion from connected devices
- **MIMOSA Standards**: OSA-CBM (Condition-Based Maintenance) and OSA-EAI alignment
- **Industry Standards**: ISO 13374 (Condition Monitoring), IEC 61508 (Functional Safety)
- **OBD/Diagnostic Protocols**: Automotive (OBD-II), Industrial (OPC UA), Building (BACnet)
- **Predictive Analytics**: Integration with Azure ML, AWS SageMaker, Google AutoML
- **Service Management**: Field service platforms (ServiceNow, Salesforce Field Service)



---

## Publishing

Release artifacts for each version (`schema.json`, `shacl.ttl`, `model.owl`)  
are served directly from this URL:
```
https://ce-rise-models.codeberg.page/diagnostic-results/
```


---

## Accessing Previous Releases

If you want to view the files published for version `v1.2.0`, open:

```
https://codeberg.org/CE-RISE-models/diagnostic-results/src/tag/pages-v1.2.0/generated/
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
