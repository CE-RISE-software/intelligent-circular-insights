# CE-RISE Material Profile

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.18432618.svg)](https://doi.org/10.5281/zenodo.18432618) [![Schemas](https://img.shields.io/badge/Schema%20Files-LinkML%2C%20JSON%2C%20SHACL%2C%20OWL-32CD32)](https://ce-rise-models.codeberg.page/material-profile/)


This repository provides the core data model defining the mandatory Material Profile for any Digital Material Passport, including material attributes, identity, composition, origin, and compliance information that defines "what the material is when introduced" rather than "what happens to it over time."

**Static Information Focus**: This Material Profile model contains time-invariant information about material identification, composition, processing origin, import/export compliance, and technical characteristics. Dynamic lifecycle events (transformation, compounding, manufacturing into products) are handled by separate data models.

---

## Data Model Structure

The Material Profile data model is structured as a hierarchical taxonomy defining **static foundational information** for Digital Material Passports. The model captures material identity and origin data that remains constant for each batch. Built using [LinkML](https://linkml.io/), it generates multiple schema formats (JSON Schema, SHACL, OWL).

**Core Philosophy**: This model answers fundamental questions about material identity:
- **"What is this material?"** → Material identification via chemical identifiers, specifications, or commodity codes
- **"Who supplied it and where?"** → Supplier organization and processing facility details  
- **"How did it get here?"** → Import/export compliance and customs
- **"What are its properties?"** → Composition, purity, technical properties, and test conditions

Dynamic supply chain events, lifecycle tracking, and real-time traceability are addressed by separate, complementary data models.

### Material Identification

A material is uniquely identified by a **composite key**:

```
[IDENTIFIER_TYPE]:[IDENTIFIER_VALUE]:[BATCH_NUMBER]
```

**Identifier Types (one of):**
- `CAS:[number]` - CAS Registry Number (e.g., CAS:7732-18-5 for water)
- `InChI:[string]` - International Chemical Identifier (e.g., InChI:InChI=1S/H2O/h1H2)
- `InChIKey:[key]` - InChIKey for database matching (e.g., InChIKey:XLYOFNOQVPJJNP-UHFFFAOYSA-N)
- `SMILES:[string]` - Molecular structure string (e.g., SMILES:O)
- `SPEC:[code]` - ISO/EN/ASTM specification (e.g., SPEC:ISO-21305 for polymers)
- `UNSPSC:[code]` - UN Standard Products and Services Code - 8-digit (e.g., UNSPSC:50202306 for wheat)
- `HS:[code]` - Harmonized System code - 6-digit for trade commodities (e.g., HS:100190 for wheat)
- `SUPPLIER:[code]` - Supplier material code (e.g., SUPPLIER:SKU-12345)

**Plus:**
- Batch/lot number (required for composite key)

**Optional:**
- Processing date (extraction/processing/import date, ISO 8601)

**Examples:**
- `CAS:7732-18-5:BATCH-2024-001` (water by CAS)
- `SPEC:ISO-21305:BATCH-2024-001` (polymer by specification)
- `UNSPSC:50202306:BATCH-2024-001` (wheat commodity)
- `HS:100190:BATCH-2024-001` (wheat by HS code)

This composite key allows the same material to be referenced through different identifier systems (chemical, specification, commodity) while maintaining batch-level traceability.

### Core Hierarchy

```
MaterialProfile (root)
├── 1. MaterialIdentity
│   ├── ChemicalIdentifier (CAS, InChI, InChIKey, SMILES)
│   ├── SpecificationCode (ISO/EN/ASTM)
│   ├── CommodityCode (UNSPSC, HS)
│   ├── SupplierMaterialCode
│   ├── BatchNumber
│   ├── ProcessingDate
│   ├── ChemicalName
│   ├── MolecularFormula
│   └── MaterialGrade
├── 2. SupplierInformation
│   ├── OrganizationEntity (GS1 GLN, LEI, VAT, legal name)
│   ├── ProcessingFacility (facility GLN, coordinates, facility type)
│   └── MaterialOrigin (location, source type, extraction/harvest date)
├── 3. InformationRelatedToImportExport
│   ├── EoriNumber (validated format: 2-letter country + up to 15 alphanumeric)
│   ├── CustomsDocumentation (MRN, declaration IDs, authorities, document URLs)
│   ├── ImportExportOperation (trade operations with Incoterms, values, dates)
│   ├── ImporterJurisdiction (EU 3-character country codes)
│   ├── TariffClassification (HS, CN, TARIC codes with duty rates)
│   ├── BorderCrossing (UN/LOCODE port codes, customs offices, crossing dates)
│   ├── AEOStatus (Authorized Economic Operator certification)
│   └── ImportAuthorization (licenses and permits for restricted goods)
└── 4. MaterialSpecification
    ├── Composition (primary component, purity, additives, trace elements, recycled content)
    ├── PhysicalProperties (density, color, state, particle size)
    ├── MechanicalProperties (tensile strength, hardness, Young's modulus)
    ├── ThermalProperties (melting point, thermal conductivity, expansion coefficient)
    ├── ChemicalProperties (reactivity, corrosion resistance, solubility, flammability)
    ├── ElectricalProperties (electrical conductivity, resistivity)
    ├── OpticalProperties (refractive index)
    ├── Fingerprinting (isotope ratios, spectroscopy signatures, trace element profiles)
    └── TestConditions (reference temperature, humidity, pressure, testing standard, test date)
```

### Workflow Sequence

#### **Step 1: MaterialIdentity** 
Material identification with multiple identifier types and batch traceability:
- **ChemicalIdentifier**: CAS Registry Number, InChI, InChIKey, SMILES for pure chemicals and substances
- **SpecificationCode**: ISO/EN/ASTM specification codes for technical materials (alloys, polymers, ceramics)
- **CommodityCode**: UNSPSC (8-digit) or HS codes (6-digit) for commodity materials (agricultural, mineral, energy)
- **SupplierMaterialCode**: Supplier-specific SKU for non-standardized materials
- **BatchNumber**: Batch/lot number (required for composite key)
- **ProcessingDate**: Extraction, processing, or import date
- **ChemicalName**: IUPAC and common names
- **MolecularFormula**: Chemical formula
- **MaterialGrade**: Grade designation (pharmaceutical, food, technical, commercial)

#### **Step 2: SupplierInformation**
Supplier and processing facility details with GS1-centric hierarchical structure:
- **OrganizationEntity**: Legal entity with GS1 GLN (preferred), LEI code, VAT number, legal name, country of incorporation
- **ProcessingFacility**: Physical facilities with facility GLN, facility name, facility type (EXTRACTION, PROCESSING, RECYCLING, IMPORT), GPS coordinates, parent organization GLN
- **MaterialOrigin**: Material source location, source type (PRIMARY_EXTRACTION, RECYCLED, SYNTHESIZED, NATURAL_HARVEST), extraction/harvest date

#### **Step 3: InformationRelatedToImportExport**
Comprehensive import/export tracking and compliance with EU customs regulations:
- **EoriNumber**: EU registration number with validated format (2-letter country code + up to 15 alphanumeric chars)
- **CustomsDocumentation**: Customs documents (MRN, declaration IDs) with issuing authorities and digital document URLs
- **ImportExportOperation**: Trade operations with type validation (IMPORT/EXPORT/TRANSIT/RE_EXPORT), dates, shipment IDs, quantities, Incoterms, and monetary values with currency codes
- **ImporterJurisdiction**: Legal establishment country using EU Publications Office 3-character country codes
- **TariffClassification**: International trade classification with 6-digit HS codes, 8-digit EU CN codes, 10-digit TARIC codes, descriptions, and duty rates
- **BorderCrossing**: Border crossing tracking with UN/LOCODE port codes, customs office codes, and precise crossing timestamps
- **AEOStatus**: Authorized Economic Operator certification (AEOC/AEOS/AEOF) for trusted trader benefits
- **ImportAuthorization**: Import licenses and permits for restricted materials with validity periods and issuing authorities

#### **Step 4: MaterialSpecification**
Material composition and technical properties with test conditions:
- **Composition**: Primary component name and chemical identifier, primary component purity percentage, additives with function and concentration, trace elements with maximum allowable concentrations, composition test method and date, certification authority, recycled content percentage, recycled cycle number, recycled source (post-consumer, post-industrial)
- **PhysicalProperties**: Density, color, state (solid/liquid/gas/paste), particle size
- **MechanicalProperties**: Tensile strength, hardness, Young's modulus (for solid materials)
- **ThermalProperties**: Melting point, thermal conductivity, expansion coefficient
- **ChemicalProperties**: Reactivity, corrosion resistance, solubility, flammability
- **ElectricalProperties**: Electrical conductivity, resistivity
- **OpticalProperties**: Refractive index
- **Fingerprinting**: Isotope ratios, spectroscopy signatures (XRF, NMR, Raman), trace element profiles, analytical method used
- **TestConditions**: Reference temperature, humidity, pressure, testing standard applied, test date (critical for all property measurements)

Material specifications may optionally embed CE-RISE utility model records for uncertainty statements, metrological traceability statements, and data quality assessments. These fields are optional and do not change the minimum information needed to describe a material profile.

### Data Properties

Each class has a corresponding value property (e.g., `cas_registry_number_value`, `batch_number_value`) that holds the actual data. All value properties are string type except where specified otherwise (e.g., float for purity percentages).

#### SQL Identifiers

Every data point in the model includes a `sql_identifier` annotation that serves as a unique, machine-friendly database identifier. These identifiers follow a structured namespace pattern to ensure uniqueness across the entire data model:

**Pattern**: `mat_[category]_[specific_name]`

**Features:**
- **Material Profile Prefix**: All identifiers start with `mat_` to clearly identify them as belonging to the Material Profile data model
- **Hierarchical Namespacing**: Uses category prefixes (`identity_`, `supplier_`, `import_`, `specs_`) to provide context and prevent naming conflicts
- **Database-Friendly**: Uses underscores and avoids special characters for SQL compatibility
- **Unique Across Model**: No duplicate identifiers, even when similar concepts appear in different parts of the hierarchy
- **Reasonable Length**: Abbreviated but meaningful names that balance clarity with practical database usage

**Examples:**
- `mat_identity_cas_registry` - CAS Registry Number in Material Identity
- `mat_identity_batch_number` - Batch/lot number in Material Identity
- `mat_supplier_facility_gln` - Facility GLN in Supplier Information
- `mat_import_eori` - EORI number in Import/Export Information
- `mat_specs_composition_purity` - Purity percentage in Material Specification
- `mat_specs_tensile_strength` - Tensile strength in Material Specification

This identifier system enables seamless integration with databases and ensures clear data model composition when combining with other CE-RISE data models.


---

## Development Roadmap

| Step | Component | Criticalities Identified | Solutions Implemented | Status | Missing/TODO |
|------|-----------|-------------------------|----------------------|--------|--------------|
| **1** | **MaterialIdentity** | • Materials cannot be identified by GTIN (commercial product codes)<br>• Need support for chemical identifiers (CAS, InChI, SMILES)<br>• Need support for technical specifications (ISO/ASTM)<br>• Need support for commodity codes (UNSPSC, HS)<br>• Batch number must be primary identifier component<br>• Processing date should be optional, not part of unique key | • Multiple identifier type support: CAS, InChI, InChIKey, SMILES for chemicals<br>• ISO/EN/ASTM specification codes for technical materials<br>• UNSPSC (8-digit) and HS codes (6-digit) for commodities<br>• Supplier material codes for non-standardized materials<br>• Composite key format: [TYPE]:[VALUE]:[BATCH]<br>• Processing date as optional attribute, not key component<br>• Material grade field for quality designation | **COMPLETED** | • InChI/InChIKey registry integration<br>• UNSPSC database integration<br>• HS code validation |
| **2** | **SupplierInformation** | • Need supplier organization identification<br>• Processing facility types differ from manufacturing (extraction, recycling)<br>• Material origin tracking essential (mine, forest, recycling facility)<br>• Source type classification needed | • Reuse OrganizationEntity from product model (GLN, LEI, VAT)<br>• Reuse ManufacturingFacility structure renamed as ProcessingFacility<br>• Extended facility types: EXTRACTION, PROCESSING, RECYCLING, IMPORT<br>• MaterialOrigin class with source type (PRIMARY_EXTRACTION, RECYCLED, SYNTHESIZED, NATURAL_HARVEST)<br>• Extraction/harvest date tracking | **COMPLETED** | • GS1 GLN Registry integration<br>• Open Supply Hub API integration<br>• Material source verification |
| **3** | **InformationRelatedToImportExport** | • Materials subject to same import/export regulations as products<br>• Customs documentation and tariff classification apply<br>• Trade compliance requirements identical | • Direct reuse of entire InformationRelatedToTheImporter structure from product model<br>• EORI number with validated format<br>• CustomsDocumentation, ImportExportOperation, ImporterJurisdiction<br>• TariffClassification (HS/CN/TARIC)<br>• BorderCrossing, AEOStatus, ImportAuthorization<br>• All classes and attributes reused without modification | **COMPLETED** | • Real-time customs status API integration<br>• Material-specific tariff database queries |
| **4** | **MaterialSpecification** | • Need composition with purity and additives (not material percentages)<br>• Technical properties essential for material characterization<br>• Test conditions critical for all measurements<br>• Fingerprinting methods for authentication<br>• Recycled content belongs in composition, not separate classification | • Composition structure: primary component with purity, additives with function<br>• Trace elements with maximum concentrations<br>• Composition verification (test method, certification, test date)<br>• Physical, mechanical, thermal, chemical, electrical, optical properties<br>• Fingerprinting section (isotope ratios, XRF, NMR, Raman)<br>• TestConditions class linking all properties to reference conditions<br>• Recycled content integrated into composition | **COMPLETED** | • Material property database integrations<br>• Test condition validation |

### Integration Opportunities

- **Standards Integration**: CAS Registry, InChI/InChIKey databases, ISO/EN/ASTM standards, UNSPSC, GS1 GLN Registry, Open Supply Hub, LEI Registry
- **Regulatory Integration**: TARIC database, customs status APIs, trade compliance engines
- **Material Databases**: Material property databases, spectroscopy reference libraries, isotope ratio databases


---

## Publishing

Release artifacts for each version (`schema.json`, `shacl.ttl`, `model.owl`)  
are served directly from this URL:
```
https://ce-rise-models.codeberg.page/material-profile/
```

---

## Accessing Previous Releases

If you want to view the files published for version `v1.2.0`, open:

```
https://codeberg.org/CE-RISE-models/material-profile/src/tag/pages-v1.2.0/generated/
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

© 2026 CE-RISE consortium.  
Licensed under [Creative Commons Attribution–NonCommercial 4.0 International (CC BY-NC 4.0)](https://creativecommons.org/licenses/by-nc/4.0/).  
Attribution: CE-RISE project (Grant Agreement No. 101092281) and the individual authors/partners as indicated.

<a href="https://www.nilu.com" target="_blank" rel="noopener noreferrer">
  <img src="https://nilu.no/wp-content/uploads/2023/12/nilu-logo-seagreen-rgb-300px.png" alt="NILU logo" width="40"/>
</a>

Developed by NILU (Riccardo Boero — ribo@nilu.no) within the CE-RISE project.
