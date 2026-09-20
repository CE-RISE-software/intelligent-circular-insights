# CE-RISE Product Profile

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.17723238.svg)](https://doi.org/10.5281/zenodo.17723238) [![Schemas](https://img.shields.io/badge/Schema%20Files-LinkML%2C%20JSON%2C%20SHACL%2C%20OWL-32CD32)](https://ce-rise-models.codeberg.page/product-profile/)


This repository provides the core data model defining the mandatory Product Profile for any Digital Product Passport, including product attributes, identity, origin, and compliance information that defines "what the product is when introduced" rather than "what happens to it over time."

**Static Information Focus**: This Product Profile model contains time-invariant information about product identification, manufacturing origin, import/export compliance, and basic physical characteristics. Dynamic lifecycle events (supply chain movements, ownership changes, real-time tracking) are handled by separate data models.

---

## Data Model Structure

The Product Profile data model is structured as a hierarchical taxonomy defining **static foundational information** for Digital Product Passports. The model captures product identity and origin data that remains constant throughout the product lifecycle. Built using [LinkML](https://linkml.io/), it generates multiple schema formats (JSON Schema, SHACL, OWL).

**Core Philosophy**: This model answers fundamental questions about product identity:
- **"What is this product?"** → Product identification and classification
- **"Who made it and where?"** → Manufacturing origin and facility details  
- **"How did it get here?"** → Import/export compliance and customs
- **"What is it made of?"** → Basic materials and physical properties

Dynamic supply chain events, lifecycle tracking, and real-time traceability are addressed by separate, complementary data models.

### Core Hierarchy

```
ProductProfile (root)
├── 1. GeneralProductInformation
│   ├── LotBatchNumber
│   ├── GTIN14
│   ├── SerialNumber
│   ├── ProductImages
│   ├── ProductType
│   └── UniqueProductIdentifier
├── 2. ManufacturersInformation
│   ├── OrganizationEntity (GS1 GLN, LEI, VAT, legal name)
│   ├── ManufacturingFacility (facility GLN, OSID, coordinates)
│   ├── Name
│   ├── ManufacturingDate
│   ├── PostalAddress
│   ├── RegisteredTradeNameOrTradeMark
│   ├── UniqueFacilityIdentifiers
│   ├── UniqueOperatorIdentifier
│   └── Website
├── 3. InformationRelatedToTheImporter
│   ├── EoriNumber (validated format: 2-letter country + up to 15 alphanumeric)
│   ├── CustomsDocumentation (MRN, declaration IDs, authorities, document URLs)
│   ├── ImportExportOperation (trade operations with Incoterms, values, dates)
│   ├── ImporterJurisdiction (EU 3-character country codes)
│   ├── TariffClassification (HS, CN, TARIC codes with duty rates)
│   ├── BorderCrossing (UN/LOCODE port codes, customs offices, crossing dates)
│   ├── AEOStatus (Authorized Economic Operator certification)
│   └── ImportAuthorization (licenses and permits for restricted goods)
└── 4. ProductSpecification
    ├── PhysicalAttributes (weight in grams, dimensions in mm, volume in mm³/ml)
    ├── MaterialIdentification (JSON array: material, percentage, country code)
    └── RegulatoryClassification (product category, safety classification)
```

### Workflow Sequence

#### **Step 1: GeneralProductInformation** 
Basic product identification with multiple identifier types:
- **LotBatchNumber**: Lot/batch tracking information
- **GTIN14**: Global Trade Item Number (14-digit format with GS1 integration)
- **SerialNumber**: Individual product serial numbers
- **ProductImages**: Product images for branding/visual identification (comma-separated URLs)
- **ProductType**: Product classification (3-digit GTIN prefix or alphanumeric code)
- **UniqueProductIdentifier**: Enables web link to product passport

#### **Step 2: ManufacturersInformation**
Manufacturer details with GS1-centric hierarchical structure:
- **OrganizationEntity**: Legal entity with GS1 GLN (preferred), LEI code, VAT number, company registration
- **ManufacturingFacility**: Physical facilities with facility GLN, Open Supply Hub ID, GPS coordinates

- **Name**: Manufacturer's legal name (Art 21 6. ESPR)
- **ManufacturingDate**: Month/year in manufacturing date codes
- **PostalAddress**: Physical address (Art 21 6. ESPR)
- **RegisteredTradeNameOrTradeMark**: Registered business names and trademarks
- **UniqueFacilityIdentifiers**: Value chain location identifiers
- **UniqueOperatorIdentifier**: Value chain actor identifiers
- **Website**: Manufacturer's website

#### **Step 3: InformationRelatedToTheImporter**
Comprehensive import/export tracking and compliance with EU customs regulations:
- **EoriNumber**: EU registration number with validated format (2-letter country code + up to 15 alphanumeric chars, e.g., GB123456789000)
- **CustomsDocumentation**: Customs documents (MRN, declaration IDs) with issuing authorities and digital document URLs (PDF/DOC/images)
- **ImportExportOperation**: Trade operations with type validation (IMPORT/EXPORT/TRANSIT/RE_EXPORT), dates, shipment IDs, quantities, Incoterms (FOB/CIF/EXW/DDP), and monetary values with currency codes
- **ImporterJurisdiction**: Legal establishment country using EU Publications Office 3-character country codes for EORI validation
- **TariffClassification**: International trade classification with 6-digit HS codes, 8-digit EU CN codes, 10-digit TARIC codes, descriptions, and duty rates
- **BorderCrossing**: Border crossing tracking with UN/LOCODE port codes (e.g., DEHAM, NLRTM), customs office codes, and precise crossing timestamps
- **AEOStatus**: Authorized Economic Operator certification (AEOC/AEOS/AEOF) for trusted trader benefits and trade facilitation
- **ImportAuthorization**: Import licenses and permits for restricted goods with validity periods and issuing authorities

#### **Step 4: ProductSpecification**
Universal basic characteristics that define any product at system entry (applicable to airplanes, t-shirts, sandwiches, etc.):
- **PhysicalAttributes**: Standardized physical measurements - weight in grams (150, 2.5e6), dimensions in millimeters LxWxH (300x200x100), volume for solids in mm³ (1e6) or liquids in ml (500). Scientific notation supported.
- **MaterialIdentification**: Structured material composition as JSON array - each material object contains name, percentage, and ISO 3166-1 alpha-2 country code. Example: `[{"material":"Cotton","percentage":80,"country":"TR"},{"material":"Polyester","percentage":20,"country":"CN"}]`
- **RegulatoryClassification**: Essential regulatory categories at entry - product category (Food, Electronics, Textiles, Machinery, Chemical), basic safety classification (Non-hazardous, Food-grade, Medical device, Hazardous) with optional GPC codes, GHS hazard classification, and CE marking categories

Product specifications may optionally embed CE-RISE utility model records for uncertainty statements, metrological traceability statements, and data quality assessments. These fields are optional and do not change the minimum information needed to describe a product profile.

### Data Properties

Each class has a corresponding value property (e.g., `name_value`, `company_id_value`) that holds the actual data. All value properties are string type except where specified otherwise.

#### SQL Identifiers

Every data point in the model includes a `sql_identifier` annotation that serves as a unique, machine-friendly database identifier. These identifiers follow a structured namespace pattern to ensure uniqueness across the entire data model:

**Pattern**: `pro_[category]_[specific_name]`

**Features:**
- **Product Profile Prefix**: All identifiers start with `pro_` to clearly identify them as belonging to the Product Profile data model
- **Hierarchical Namespacing**: Uses category prefixes (`gen_info_`, `mfr_info_`, `imp_info_`, `spec_info_`) to provide context and prevent naming conflicts
- **Database-Friendly**: Uses underscores and avoids special characters for SQL compatibility
- **Unique Across Model**: No duplicate identifiers, even when similar concepts appear in different parts of the hierarchy
- **Reasonable Length**: Abbreviated but meaningful names that balance clarity with practical database usage

**Examples:**
- `pro_gen_info_gtin14` - GTIN-14 identifier in General Product Information
- `pro_mfr_info_facility` - Manufacturing facility in Manufacturer Information  
- `pro_imp_info_eori` - EORI number in Import/Export Information
- `pro_spec_info_materials` - Material composition in Product Specifications

This identifier system enables seamless integration with databases and ensures clear data model composition when combining with other CE-RISE data models.


---

## Development Roadmap

| Step | Component | Criticalities Identified | Solutions Implemented | Status | Missing/TODO |
|------|-----------|-------------------------|----------------------|--------|--------------|
| **1** | **GeneralProductInformation** | • Unique product identifier lacks precision and standards<br>• No reference integration with discoverability/registries<br>• Missing serial number and lot number storage<br>• No connection to standard product nomenclature<br>• No product description and branding<br>• No classification for grouping products | • Added GS1 prefix and ontology integration<br>• Implemented GTIN-14 + serial number approach<br>• Added Schema.org prefix<br>• Created GTIN-14, Serial number, Lot/batch number subclasses<br>• Added ProductImages (comma-separated image URLs with format validation)<br>• Added ProductType (3-digit GTIN prefix or alphanumeric classification)<br>• Referenced UNTP framework for discoverability | **COMPLETED** | • UNTP Identity Resolver integration |
| **2** | **ManufacturersInformation** | • Incomplete description and separation of manufacturer facility and organization<br>• Lack of codification of facility and organization | • Implemented GS1-centric hierarchical model<br>• Added OrganizationEntity with GLN, LEI, VAT identification<br>• Added ManufacturingFacility with facility GLN and OSID<br>• Added GPS coordinates for precise facility location<br>• Renamed 'Company ID' to 'Organization identifier'<br>• Renamed 'Unique facility identifiers' to 'Facility identifier'<br>• Renamed 'Unique operator identifier' to 'Operator identifier' | **COMPLETED** | • GS1 GLN Registry integration<br>• Open Supply Hub API integration<br>• LEI code verification integration |
| **3** | **InformationRelatedToTheImporter** | • Limited to EORI number only<br>• Missing comprehensive import/export tracking<br>• No customs documentation integration<br>• No tariff classification system<br>• Missing border crossing information | • EORI number with validated EU format (2-letter country + alphanumeric)<br>• CustomsDocumentation with MRN, declaration IDs, and document URLs<br>• ImportExportOperation with trade activity tracking and Incoterms<br>• ImporterJurisdiction with EU 3-character country codes<br>• TariffClassification with HS/CN/TARIC codes and duty rates<br>• BorderCrossing with UN/LOCODE port codes and customs offices<br>• AEOStatus for trusted trader certification<br>• ImportAuthorization for restricted goods licensing | **COMPLETED** | • Real-time customs status API integration<br>• Tariff database integration (WTO, EU TARIC)<br>• Multi-modal transport tracking<br>• Trade compliance validation engines |
| **4** | **ProductSpecification** | • Limited to physical dimensions only<br>• Missing basic material information<br>• Lack of universal applicability across product types<br>• No regulatory classification framework | • PhysicalAttributes with standardized units (weight in grams, dimensions in mm, volume in mm³/ml)<br>• MaterialIdentification with structured JSON format (material, percentage, country code)<br>• Optional material classification standards: UNSPSC codes, CAS registry numbers, ISO standard references<br>• RegulatoryClassification with GPC codes, GHS hazard classification, and CE marking categories<br>• Universal design with scientific notation support for any product type | **COMPLETED** | • Extended regulatory taxonomy integrations |

### Integration Opportunities

- **Standards Integration**: GS1 GLN Registry, Open Supply Hub, LEI Registry, UNTP Framework
- **Regulatory Integration**: TARIC database, GPC registry, GHS database, CE marking systems
- **Customs Integration**: Real-time EORI validation, customs status APIs, trade compliance engines


---

## Publishing

Release artifacts for each version (`schema.json`, `shacl.ttl`, `model.owl`)  
are served directly from this URL:
```
https://ce-rise-models.codeberg.page/product-profile/
```

---

## Accessing Previous Releases

If you want to view the files published for version `v1.2.0`, open:

```
https://codeberg.org/CE-RISE-models/product-profile/src/tag/pages-v1.2.0/generated/
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

Developed by NILU (Riccardo Boero, Mahsa Motevallian) within the CE-RISE project.
