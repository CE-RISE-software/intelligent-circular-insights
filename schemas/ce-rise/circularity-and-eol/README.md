# CE-RISE Circularity and End-of-Life

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.17912234.svg)](https://doi.org/10.5281/zenodo.17912234) [![Schemas](https://img.shields.io/badge/Schema%20Files-LinkML%2C%20JSON%2C%20SHACL%2C%20OWL-32CD32)](https://ce-rise-models.codeberg.page/circularity-and-eol/)

Repository for the data model capturing circularity and end-of-life information for products, including material composition at beginning of life, design-for-circularity attributes, performance factors and scores, and end-of-life pathways such as disassembly, recycling, treatment options, and CRM recovery-related information.


---

## Data Model Structure

The Circularity and End-of-Life data model provides a comprehensive framework for capturing circular economy principles throughout a product's lifecycle. It enables tracking of material composition at beginning of life (linking to material DMPs), design decisions that support circularity, performance metrics that measure circular potential, and detailed end-of-life pathways including material recovery, recycling rates, and critical raw material (CRM) recovery strategies. This model creates the circular loop by linking materials used at product beginning of life to materials recovered at end of life.

### Key Design Principles

1. **Lifecycle Completeness**: Captures material information from beginning of life through end of life, creating circular loop
2. **Material Traceability**: Links to Digital Material Passports (DMPs) for materials used and recovered
3. **Design-Stage Integration**: Captures how products are designed with circularity in mind from inception
4. **Performance Measurement**: Quantifiable metrics for assessing circular economy performance
5. **End-of-Life Clarity**: Detailed pathways for product disposal, recovery, and material reintegration
6. **CRM Focus**: Special attention to Critical Raw Materials recovery and tracking
7. **Standards Alignment**: Integration with circular economy standards and recycling classification systems

### Core Hierarchy

```
CircularityAndEOL (root)
├── 0. BeginningOfLifeInformation
│   ├── MaterialCompositionEntries (vector)
│   │   └── MaterialCompositionEntry (per material)
│   │       ├── DMPReference (URI to material DMP)
│   │       ├── MaterialMass
│   │       ├── MaterialType (metal/polymer/ceramic/composite)
│   │       ├── SourceRegion
│   │       ├── VirginContentPercentage (for this material)
│   │       ├── RecycledContentPercentage (for this material)
│   │       ├── RenewableContentPercentage (for this material)
│   │       └── SupplierReference (optional)
│   └── ProductLevelSummary
│       ├── TotalProductMass
│       ├── OverallVirginPercentage (aggregated)
│       ├── OverallRecycledPercentage (aggregated)
│       ├── OverallRenewablePercentage (aggregated)
│       └── NumberOfMaterialsUsed
├── 1. DesignForCircularity
│   ├── ModularDesign
│   │   ├── ModularityLevel
│   │   ├── InterchangeableParts
│   │   └── StandardizedInterfaces
│   ├── MaterialSelection
│   │   ├── RecycledContent (%)
│   │   ├── RenewableContent (%)
│   │   ├── HazardousSubstances
│   │   └── MaterialPassport
│   ├── DisassemblyFeatures
│   │   ├── DisassemblyTime
│   │   ├── RequiredTools
│   │   ├── DisassemblyInstructions
│   │   └── FastenerTypes
│   └── DurabilityFeatures
│       ├── ExpectedLifetime
│       ├── RepairabilityIndex
│       ├── UpgradeCapability
│       └── MaintenanceSchedule
├── 2. ProductPerformanceFactors
│   ├── ResourceEfficiency
│   │   ├── MaterialIntensity
│   │   ├── EnergyEfficiency
│   │   ├── WaterFootprint
│   │   └── WasteGeneration
│   ├── LifespanFactors
│   │   ├── MeanTimeBetweenFailures
│   │   ├── WarrantyPeriod
│   │   ├── ServiceLife
│   │   └── ObsolescenceFactors
│   └── CircularCapability
│       ├── ReusePotential
│       ├── RefurbishmentPotential
│       ├── RemanufacturingPotential
│       └── RecyclingPotential
├── 3. CircularityAssessments
│   └── Assessment (repeatable)
│       ├── AssessmentType
│       ├── AssessmentMethodology
│       ├── AssessmentDate
│       ├── AssessmentVersion
│       ├── AssessmentScore
│       ├── ScoreUnit
│       ├── ScoreRange
│       ├── SubScores (repeatable)
│       │   ├── SubScoreName
│       │   ├── SubScoreValue
│       │   ├── SubScoreUnit (optional; for dimensional sub-scores)
│       │   └── SubScoreWeight
│       ├── DataSources
│       ├── AssessmentReference
│       └── CertificationStatus
└── 4. EndOfLifeInformation
    ├── CollectionAndSorting
    │   ├── CollectionSchemes
    │   ├── SortingInstructions
    │   ├── WasteClassification
    │   └── TakeBackPrograms
    ├── RecyclingPathways
    │   ├── RecyclableMaterials
    │   │   ├── MaterialType
    │   │   ├── RecyclingRate (%)
    │   │   └── RecyclingProcess
    │   ├── NonRecyclableMaterials
    │   │   ├── MaterialType
    │   │   ├── Percentage
    │   │   └── DisposalMethod
    │   ├── RecyclingInfrastructure
    │   │   ├── RequiredTechnology
    │   │   └── GeographicAvailability
    │   └── WEEERecyclingStream (per WEEE Directive 2012/19/EU)
    │       ├── WEEECategory (Annex III: temperature-exchange/screens/lamps/large/small/small-IT)
    │       ├── StreamFraction
    │       ├── RecoveryRate (%)
    │       ├── RecyclingRate (%)
    │       ├── PreparationForReuseRate (%)
    │       ├── InputAllocationPercentage
    │       └── TreatmentProcess
    ├── CRMRecovery
    │   ├── CriticalMaterialsList
    │   │   ├── MaterialName
    │   │   ├── Quantity
    │   │   └── Concentration
    │   ├── RecoveryMethods
    │   │   ├── ExtractionProcess
    │   │   ├── RecoveryRate (%)
    │   │   └── EconomicViability
    │   └── SecondaryRawMaterials
    │       ├── QualityGrade
    │       └── MarketDemand
    └── TreatmentOptions
        ├── EnergyRecovery
        │   ├── CaloricValue
        │   └── EmissionFactors
        ├── Landfilling
        │   ├── LandfillClassification
        │   └── LeachingPotential
        └── SpecialTreatment
            ├── HazardousWasteTreatment
            └── BiologicalTreatment
```

### Workflow Sequence

#### **Step 0: BeginningOfLifeInformation**
Establishes material composition baseline and links to material DMPs:
- **MaterialCompositionEntries**: Vectorized material-level information with DMP references
  - Each entry links to a specific material's Digital Material Passport (DMP) via URI
  - Captures material mass, type, source region for each material
  - Tracks virgin/recycled/renewable content at individual material level
  - Optional supplier reference for traceability
- **ProductLevelSummary**: Aggregated product-level composition metrics
  - Total product mass and number of materials used
  - Overall percentages aggregated across all materials
  - Provides high-level view of product material composition
- **Purpose**: Creates the starting point for circular loop by documenting what materials went INTO the product, enabling comparison with what comes OUT at end of life

#### **Step 1: DesignForCircularity**
Captures design decisions that enable circular economy principles:
- **ModularDesign**: Component modularity, standardization, and interchangeability
- **MaterialSelection**: Recycled/renewable content, hazardous substances tracking
- **DisassemblyFeatures**: Time, tools, instructions for product disassembly
- **DurabilityFeatures**: Lifetime expectations, repairability, upgrade paths

#### **Step 2: ProductPerformanceFactors**
Quantifiable factors that influence circular performance:
- **ResourceEfficiency**: Material intensity, energy/water use, waste generation
- **LifespanFactors**: MTBF, warranty, service life, obsolescence planning
- **CircularCapability**: Potential for reuse, refurbishment, remanufacturing, recycling

#### **Step 3: CircularityAssessments**
Generic container for any type of circularity-related assessment:
- **Assessment**: Repeatable structure that can store any assessment methodology
- **AssessmentType**: Identifier for the type of assessment performed
- **AssessmentMethodology**: Reference to the methodology used
- **SubScores**: Optional breakdown of the main score into components
- Supports multiple assessments of different types over time

#### **Step 4: EndOfLifeInformation**
Comprehensive end-of-life pathways and material recovery:
- **CollectionAndSorting**: Collection schemes, sorting instructions, waste classification
- **RecyclingPathways**: Recyclable/non-recyclable materials, rates, infrastructure
- **CRMRecovery**: Critical raw materials identification, recovery methods, secondary materials (with DMP references to recovered materials)
- **TreatmentOptions**: Energy recovery, landfilling, special treatment requirements
- **Purpose**: Completes the circular loop by documenting what materials come OUT of the product, with links to new DMPs for recovered materials

### Data Properties

Each class has a corresponding value property (e.g., `modularity_level_value`, `recycling_rate_value`) that holds the actual data. All value properties are string type except where specified otherwise (percentages as float, scores as integer).

#### SQL Identifiers

Every data point in the model includes a `sql_identifier` annotation that serves as a unique, machine-friendly database identifier. These identifiers follow a structured namespace pattern to ensure uniqueness across the entire data model:

**Pattern**: `circ_[category]_[specific_name]`

**Features:**
- **Circularity Prefix**: All identifiers start with `circ_` to clearly identify them as belonging to the Circularity and End-of-Life data model
- **Hierarchical Namespacing**: Uses category prefixes (`design_`, `perf_`, `score_`, `eol_`) to provide context and prevent naming conflicts
- **Database-Friendly**: Uses underscores and avoids special characters for SQL compatibility
- **Unique Across Model**: No duplicate identifiers, even when similar concepts appear in different parts of the hierarchy
- **Reasonable Length**: Abbreviated but meaningful names that balance clarity with practical database usage

**Examples:**
- `circ_bol_dmp_ref` - DMP reference in Beginning of Life
- `circ_bol_material_mass` - Material mass in Beginning of Life
- `circ_bol_overall_recycled_pct` - Overall recycled content percentage
- `circ_design_modularity_level` - Modularity level in Design for Circularity
- `circ_perf_recycling_potential` - Recycling potential in Performance Factors
- `circ_assessment_type` - Type of assessment performed
- `circ_assessment_score` - Assessment score value
- `circ_eol_crm_recovery_rate` - Critical material recovery rate
- `circ_eol_recycling_rate` - Material recycling rate

This identifier system enables seamless integration with databases and ensures clear data model composition when combining with other CE-RISE data models.

---

## Development Roadmap

> **Note:** This roadmap documents the model's initial development. The data model has since been further developed and refined — see [CHANGELOG.md](CHANGELOG.md) for the authoritative, up-to-date record of changes.

| Step | Component | Criticalities Identified | Solutions Implemented | Status | Missing/TODO |
|------|-----------|-------------------------|----------------------|--------|--------------|
| **0** | **BeginningOfLifeInformation** | • Material composition tracking<br>• DMP integration<br>• Product-level aggregation<br>• Material-level detail vectorization | • Material composition entry structure<br>• DMP reference via URI<br>• Product summary calculations<br>• Material-by-material breakdown | **COMPLETED** | • Automated DMP validation<br>• Mass balance verification<br>• Supplier data integration |
| **1** | **DesignForCircularity** | • Lack of standardized modularity metrics<br>• Material passport integration<br>• Disassembly time estimation methods<br>• Repairability index standards | • Modular design classification system<br>• Material selection criteria<br>• Disassembly instruction templates<br>• Durability metrics framework | **COMPLETED** | • Integration with material databases<br>• Automated disassembly time calculation<br>• Repairability score harmonization |
| **2** | **ProductPerformanceFactors** | • Resource efficiency measurement<br>• Lifespan prediction accuracy<br>• Circular capability assessment<br>• Data collection challenges | • Resource efficiency indicators<br>• Lifespan factor definitions<br>• Circular capability matrix<br>• Performance benchmarks | **COMPLETED** | • Real-time performance monitoring<br>• Predictive obsolescence models<br>• Industry-specific benchmarks |
| **3** | **CircularityAssessments** | • Multiple assessment methodologies<br>• Score comparability<br>• Version control<br>• Generic storage structure | • Generic assessment container<br>• Support for any methodology<br>• Repeatable assessments<br>• Sub-score breakdown capability | **COMPLETED** | • Assessment validation<br>• Historical tracking<br>• Interoperability standards |
| **4** | **EndOfLifeInformation** | • Collection scheme variety<br>• Recycling rate accuracy<br>• CRM identification and tracking<br>• Treatment option optimization | • Collection pathway mapping<br>• Material-specific recycling rates<br>• CRM recovery framework<br>• Treatment hierarchy | **COMPLETED** | • Real-time recycling infrastructure data<br>• CRM market price integration<br>• Automated waste classification |

### Integration Opportunities

- **Design Software**: CAD/CAM systems for modularity and disassembly analysis
- **Material Databases**: Integration with material property and composition databases
- **Recycling Infrastructure**: Connection to regional recycling facility databases
- **CRM Markets**: Links to critical raw material market data and recovery technologies
- **Standards Bodies**: Alignment with ISO 14040 series, EN 45555 series, and circular economy standards
- **CE-RISE Utility Models**: Selected material composition, circularity performance, assessment, recycling, CRM recovery, and treatment records can optionally reference `uncertainty-quantification`, `metrological-traceability`, and `data-quality-framework` records


---

## Publishing

Release artifacts for each version (`schema.json`, `shacl.ttl`, `model.owl`)  
are served directly from this URL:
```
https://ce-rise-models.codeberg.page/circularity-and-eol/
```


---

## Accessing Previous Releases

If you want to view the files published for version `v1.2.0`, open:

```
https://codeberg.org/CE-RISE-models/circularity-and-eol/src/tag/pages-v1.2.0/generated/
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
