# CE-RISE Usage and Maintenance

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.17816062.svg)](https://doi.org/10.5281/zenodo.17816062) [![Schemas](https://img.shields.io/badge/Schema%20Files-LinkML%2C%20JSON%2C%20SHACL%2C%20OWL-32CD32)](https://ce-rise-models.codeberg.page/usage-and-maintenance/)

Repository for the CE-RISE Usage and Maintenance data model that captures the operational lifecycle of products through a mixed temporal approach: static reference information (instructions, schedules), accumulating state-based metrics (usage hours, performance), and discrete event-based records (maintenance, repairs). It enables comprehensive tracking of how products are used, maintained, and serviced throughout their operational life.


---

## Data Model Structure
This data model captures how a product is operated and maintained throughout its lifecycle, using a **mixed approach** that combines:
- **Event-based data**: For discrete maintenance actions, repairs, and service activities that occur at specific points in time
- **State-based data**: For cumulative usage metrics, current performance levels, and static reference information

### Key Design Principles
1. **No overlap with other models**: Excludes static product information (Layer 1), lifecycle events and diagnostic results (Layer 2), and compliance data (Layer 6)
2. **Mixed temporal approach**: Combines timestamped events with accumulated state metrics
3. **Operational focus**: Centers on HOW the product is used and maintained, not WHAT it is or WHERE it's been
4. **Service integration**: Links maintenance activities to service providers and spare parts information
5. **Instruction repository**: Maintains operational and maintenance guidance separate from regulatory requirements


### Core Hierarchy

```
UsageAndMaintenance (root)
├── 1. UseInstructions (STATE-BASED)
│   ├── OperatingManualURL
│   ├── QuickStartGuide
│   ├── SafetyPrecautions
│   ├── OptimalOperatingParameters
│   ├── ProhibitedUses
│   ├── TrainingRequirements
│   └── TroubleshootingGuide
│
├── 2. MaintenanceInstructions (STATE-BASED)
│   ├── MaintenanceManualURL
│   ├── RoutineMaintenanceProcedures
│   ├── CleaningInstructions
│   ├── LubricationRequirements
│   ├── InspectionChecklists
│   ├── CalibrationProcedures
│   ├── StorageInstructions
│   ├── DecommissioningProcedures
│   ├── SpecialToolsRequired
│   └── MaintenanceSafetyRequirements
│
├── 3. UsageRelatedData (STATE-BASED)
│   ├── UsageMetrics
│   │   ├── TotalOperatingHours
│   │   ├── PowerOnCycles
│   │   ├── UsageIntensity
│   │   ├── EnergyConsumption
│   │   ├── DistanceTraveled
│   │   ├── LoadCycles
│   │   └── AverageDailyUsage
│   ├── OperationalConditions
│   │   ├── TypicalOperatingTemperature
│   │   ├── TypicalHumidityRange
│   │   ├── VibrationExposure
│   │   ├── EnvironmentalConditions
│   │   └── OperatingLocationType
│   ├── UsagePatterns
│   │   ├── PrimaryUseCase
│   │   ├── SecondaryUseCases
│   │   ├── PeakUsagePeriods
│   │   ├── IdleTimePercentage
│   │   └── SeasonalVariation
│   └── PerformanceTracking
│       ├── CurrentEfficiency
│       ├── PerformanceDegradationRate
│       ├── ReliabilityScore
│       ├── MeanTimeBetweenFailures
│       └── AvailabilityPercentage
│
└── 4. MaintenanceRepairRelatedData (MIXED)
    ├── MaintenanceSchedule (STATE)
    │   ├── PreventiveMaintenanceIntervals
    │   ├── PredictiveMaintenanceTriggers
    │   ├── MandatoryInspections
    │   ├── CalibrationSchedule
    │   └── ComponentReplacementSchedule
    ├── MaintenanceHistory (EVENT-BASED, MULTIVALUED)
    │   ├── MaintenanceDate
    │   ├── MaintenanceType
    │   ├── MaintenanceDescription
    │   ├── TechnicianId
    │   ├── ServiceOrganization
    │   ├── PartsReplaced (repeatable ReplacedComponent: name, old/new part & serial, manufacturer, quantity, reason, condition)
    │   ├── MaintenanceCost
    │   ├── NextMaintenanceDue
    │   ├── MaintenanceDuration
    │   └── MaintenanceEffectiveness
    ├── RepairHistory (EVENT-BASED, MULTIVALUED)
    │   ├── RepairDate
    │   ├── FailureDescription
    │   ├── RootCauseAnalysis
    │   ├── RepairActionsTaken
    │   ├── ComponentsReplaced (repeatable ReplacedComponent: name, old/new part & serial, manufacturer, quantity, reason, condition)
    │   ├── RepairDuration
    │   ├── RepairCost
    │   ├── WarrantyCoverage
    │   ├── RepairEffectiveness
    │   ├── DowntimeCaused
    │   └── FailureCategory
    ├── SoftwarePreparation (EVENT-BASED, MULTIVALUED - refurbishment OS/software setup)
    │   ├── PreparationDate
    │   ├── OSImage
    │   ├── LicenseStatus
    │   ├── DriverPack
    │   ├── UpdateState
    │   ├── BIOSConfiguration
    │   ├── DeviceResetState
    │   ├── FinalBootResult
    │   ├── PreparedBy
    │   └── PreparationNotes
    ├── SparePartsInformation (STATE)
    │   ├── CriticalSparePartsList
    │   ├── SparePartsAvailability
    │   ├── PartsInterchangeability
    │   ├── PartsSuppliers
    │   └── PartsOrderingInformation
    └── ServiceProviderInformation (STATE)
        ├── AuthorizedServiceCenters
        ├── ServiceHotline
        ├── RemoteSupportAvailability
        ├── ServiceContractOptions
        └── WarrantyServiceTerms
```

### Workflow Sequence

#### **Step 1: Reference Information Management (State-Based)**
Static instructional and scheduling content:
- **UseInstructions**: How to operate the product
- **MaintenanceInstructions**: How to maintain the product
- **MaintenanceSchedule**: When maintenance should occur
- **SparePartsInformation**: What parts are needed

#### **Step 2: Usage Data Collection (State-Based)** 
Continuous accumulation of operational metrics:
- **UsageMetrics**: Cumulative measurements (operating hours, energy consumption)
- **OperationalConditions**: Environmental parameters during use
- **UsagePatterns**: Behavioral patterns and use cases
- **PerformanceTracking**: Current performance vs. baseline

#### **Step 3: Maintenance Event Recording (Event-Based)**
Discrete maintenance activities with timestamps:
- **MaintenanceHistory**: Each maintenance action as a timestamped event
- **RepairHistory**: Each repair as a separate event with failure analysis
- **ServiceProvider**: Link to who performed the service
- **PartsReplaced**: Components changed during each event

### Data Properties

Each class has a corresponding value property (e.g., `name_value`, `company_id_value`) that holds the actual data. All value properties are string type except where specified otherwise.

#### SQL Identifiers

Every data point in the model includes a `sql_identifier` annotation that serves as a unique, machine-friendly database identifier. These identifiers follow a structured namespace pattern to ensure uniqueness across the entire data model:

**Pattern**: `uam_[category]_[specific_name]`

**Features:**
- **Usage and Maintenance Prefix**: All identifiers start with `uam_` to clearly identify them as belonging to the Usage and Maintenance data model
- **Hierarchical Namespacing**: Uses category prefixes (`usage_`, `maint_`, `repair_`, `inst_`) to provide context and prevent naming conflicts
- **Database-Friendly**: Uses underscores and avoids special characters for SQL compatibility
- **Unique Across Model**: No duplicate identifiers, even when similar concepts appear in different parts of the hierarchy
- **Reasonable Length**: Abbreviated but meaningful names that balance clarity with practical database usage

**Examples:**
- `uam_usage_total_hours` - Total operating hours in usage metrics
- `uam_maint_history_date` - Date of maintenance event in maintenance history  
- `uam_repair_failure_desc` - Failure description in repair history
- `uam_inst_operating_manual` - Operating manual URL in use instructions

This identifier system enables seamless integration with databases and ensures clear data model composition when combining with other CE-RISE data models.

---

## Development Roadmap

> **Note:** This roadmap documents the model's initial development. The data model has since been further developed and refined — see [CHANGELOG.md](CHANGELOG.md) for the authoritative, up-to-date record of changes.

| Step | Component | Sub-Components | Criticalities Identified | Solutions Planned | Status | Missing/TODO |
|------|-----------|---------------|-------------------------|-------------------|--------|--------------|
| **1** | **Reference Information<br>(Static)** | • UseInstructions<br>• MaintenanceInstructions<br>• MaintenanceSchedule<br>• SparePartsInfo<br>• ServiceProviderInfo | • Separation from regulatory requirements<br>• Multi-language support needs<br>• Version control for updates<br>• Preventive vs predictive scheduling<br>• Parts availability tracking<br>• Service provider network | • Separate use and maintenance instructions<br>• Plan URL-based document references<br>• Design flexible scheduling framework<br>• Include parts catalog structure<br>• Add service center listings<br>• **Import Schema.org HowTo** for instructions<br>• **Import GoodRelations** for spare parts<br>• **Align with ISO 14224** for maintenance schedules | **COMPLETED** | • Interactive instructions<br>• AR/VR guidance<br>• Real-time parts availability<br>• Automated scheduling<br>• 3D printing specs |
| **2** | **Usage Data Collection<br>(State-Based)** | • UsageMetrics<br>• OperationalConditions<br>• UsagePatterns<br>• PerformanceTracking | • Distinguish cumulative vs. instantaneous metrics<br>• Usage patterns vary by product type<br>• Performance degradation tracking<br>• Integration with IoT data sources<br>• Standardization of usage intensity levels | • Plan state-based cumulative structure<br>• Design flexible pattern categories<br>• Include performance baselines<br>• Define intensity classifications<br>• Add environment tracking<br>• **Import QUDT** for units (hours, kWh, km)<br>• **Import SSN/SOSA** for sensor data<br>• **Align with MIMOSA OSA-CBM** for metrics | **COMPLETED** | • IoT data ingestion<br>• Usage anomaly detection<br>• Multi-user tracking<br>• Energy efficiency calcs<br>• Predictive analytics |
| **3** | **Maintenance/Repair Events<br>(Event-Based)** | • MaintenanceHistory<br>• RepairHistory | • Event-based timestamp structure<br>• Link to service providers<br>• Parts traceability<br>• Cost tracking for TCO<br>• Root cause analysis<br>• Failure pattern recognition | • Design event-based structure<br>• Include technician IDs<br>• Add parts replacement tracking<br>• Plan failure categorization<br>• Include effectiveness metrics<br>• **Import Time Ontology** for timestamps<br>• **Import PROV-O** for event lineage<br>• **Align with IEC 62264** for maintenance ops | **COMPLETED** | • Diagnostic integration<br>• Warranty validation<br>• Failure prediction<br>• Component reliability<br>• Knowledge base |


### Integration Opportunities

- **QUDT** (Quantities, Units, Dimensions and Types) - For standardized units in usage metrics
- **Schema.org** - HowTo, MaintenanceSchedule, Service, ServiceChannel classes
- **SSN/SOSA** (Semantic Sensor Network) - For operational conditions and sensor-based metrics
- **GoodRelations** - For spare parts catalog and service provider information
- **ISO 14224** - Reliability and maintenance data standard for equipment
- **MIMOSA OSA-CBM** - Open System Architecture for Condition-Based Maintenance
- **IEC 62264 (ISA-95)** - Enterprise-control system integration including maintenance operations
- **Time Ontology in OWL** - For temporal aspects of maintenance schedules and events
- **PROV-O** - W3C provenance ontology for tracking maintenance event lineage
- **DCMI (Dublin Core)** - Metadata terms for documentation and records
- **FOAF** - For service provider and technician identification
- **RDF Data Cube** - For structuring multi-dimensional usage metrics
- **CE-RISE Utility Models** - Selected usage, operational condition, performance, maintenance, and repair records can optionally reference `uncertainty-quantification`, `metrological-traceability`, and `data-quality-framework` records

## Publishing

Release artifacts for each version (`schema.json`, `shacl.ttl`, `model.owl`)  
are served directly from this URL:
```
https://ce-rise-models.codeberg.page/usage-and-maintenance/
```


---

## Accessing Previous Releases

If you want to view the files published for version `v1.2.0`, open:

```
https://codeberg.org/CE-RISE-models/usage-and-maintenance/src/tag/pages-v1.2.0/generated/
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
