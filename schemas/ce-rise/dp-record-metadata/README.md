# CE-RISE DMP & DPP Record Metadata

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.17880431.svg)](https://doi.org/10.5281/zenodo.17880431) [![Schemas](https://img.shields.io/badge/Schema%20Files-LinkML%2C%20JSON%2C%20SHACL%2C%20OWL-32CD32)](https://ce-rise-models.codeberg.page/dp-record-metadata/)

Repository for the CE-RISE DMP & DPP Record Metadata data model, part of the DMP & DPP Metadata Layer in the Digital Material and Product Passport architecture. This model provides a universal metadata envelope that declares which data models and schemas compose a DMP/DPP record, regardless of their origin. It supports any combination of CE-RISE models, industry standards, proprietary schemas, or established ontologies, enabling true interoperability. The metadata acts as a "table of contents" that tells consumers which models to use for interpreting each part of the composite DMP/DPP record, promoting an open and extensible ecosystem rather than a closed system.


---

## Data Model Structure
This data model provides a universal metadata framework for declaring the composition of any DMP/DPP record. It supports heterogeneous data sources by allowing references to any schema or ontology - whether CE-RISE models, GS1 standards, Schema.org types, industry-specific schemas, or proprietary formats. The metadata declares which models are used and in what sequence, enabling parsers to correctly interpret composite records built from diverse sources.

### Key Design Principles
1. **Schema-agnostic**: Supports any data model, ontology, or schema - not limited to CE-RISE
2. **Models-first approach**: The list of applied schemas is the primary and often only required metadata
3. **Composite record support**: Enables combination of heterogeneous data sources in a defined sequence
4. **Version awareness**: Tracks schema versions for proper interpretation
5. **Minimal overhead**: Thin metadata layer that doesn't duplicate what's already in the referenced schemas
6. **Open ecosystem**: Promotes interoperability by accepting any standard or proprietary format

### Core Hierarchy

```
DPRecordMetadata (root)
├── RecordScope (product or material)
├── RelatedPassports (multivalued)
│   ├── RelatedPassportId (URI/identifier)
│   ├── RelationType (derived_from, contributes_to, split_from, merged_into, recycled_into, manufactured_from)
│   └── OperationRef (link to traceability or life-cycle event)
├── AppliedSchemas (multivalued)
│   ├── SchemaReference
│   │   ├── SchemaURL
│   │   ├── SchemaIdentifier (alternative if URL not available)
│   │   ├── SchemaType (CE-RISE, GS1, Schema.org, ISO, custom, etc.)
│   │   ├── SchemaLanguage (LinkML, JSON-Schema, XSD, SHACL, RDF-Schema, OWL, etc.)
│   │   ├── SchemaVersion
│   │   ├── SchemaHash
│   │   ├── HashAlgorithm (SHA-256, SHA-512, MD5, etc.)
│   │   ├── SchemaNamespace
│   │   └── DocumentationURL
│   ├── SchemaUsage
│   │   ├── SchemaRole (core-identity, sustainability-data, regulatory-compliance, usage-tracking, material-identity, material-composition, processing-history, batch-traceability, safety-sheet, recycled-content, etc.)
│   │   ├── SchemaProfile (subset or profile used)
│   │   ├── DataCompleteness (full, partial, minimal)
│   │   ├── CompletenessPercentage (0-100)
│   │   ├── FallbackSchemaURL
│   │   └── SchemaNotes
│   └── CompositionInfo
│       ├── SequenceOrder (position in composite record)
│       ├── CompositionMethod (sequential, nested, mixed, overlay)
│       ├── DataLocation (JSONPath, XPath, or other pointer)
│       ├── ParentSchema (if nested)
│       └── DependencySchemas
│
└── MetadataVersioning
    ├── MetadataSchemaVersion
    ├── CompatibilityLevel
    ├── MetadataCreated (timestamp)
    ├── MetadataModified (timestamp)
    ├── MetadataSchemaURL
    ├── MinimumParserVersion
    └── MetadataLanguage (ISO 639-1 code)
```

### Workflow Sequence

#### **Step 1: Schema Reference Declaration**
Core identification and reference information for each schema:
- **SchemaURL**: Direct URL to the schema definition
- **SchemaIdentifier**: Alternative identifier (URN, DOI, registry ID) if URL not available
- **SchemaType**: Classification of origin (CE-RISE, GS1, Schema.org, ISO, custom)
- **SchemaLanguage**: Technical format (LinkML, JSON-Schema, XSD, SHACL, RDF-Schema, OWL)
- **SchemaVersion**: Specific version for proper interpretation
- **SchemaHash & HashAlgorithm**: Cryptographic verification of schema integrity
- **SchemaNamespace**: Namespace/prefix used in the record
- **DocumentationURL**: Human-readable documentation link

#### **Step 2: Schema Usage Context**
Metadata about how each schema is applied in the record:
- **SchemaRole**: Purpose in the DMP/DPP (core-identity, sustainability-data, regulatory-compliance, usage-tracking, material-identity, material-composition, processing-history, batch-traceability, safety-sheet, recycled-content)
- **SchemaProfile**: Specific profile or subset being used
- **DataCompleteness**: Categorical completeness (full, partial, minimal)
- **CompletenessPercentage**: Numeric percentage of populated fields (0-100)
- **FallbackSchemaURL**: Alternative schema for graceful degradation
- **SchemaNotes**: Additional usage notes or exceptions
- **CompositionInfo**: How the schema fits in the composite:
  - SequenceOrder: Position in the record
  - CompositionMethod: Integration approach (sequential, nested, mixed, overlay)
  - DataLocation: Pointer to where data resides
  - ParentSchema: Reference if nested
  - DependencySchemas: Other required schemas

#### **Step 3: Metadata Versioning**
Version and lifecycle information for the metadata structure itself:
- **MetadataSchemaVersion**: Version of this DMP & DPP Record Metadata schema
- **CompatibilityLevel**: Backward/forward compatibility (e.g., "compatible-with: 1.x")
- **MetadataCreated**: Timestamp when metadata was created
- **MetadataModified**: Last modification timestamp
- **MetadataSchemaURL**: Reference to this metadata schema definition
- **MinimumParserVersion**: Required parser version to process
- **MetadataLanguage**: Language of descriptive text (ISO 639-1)

#### **Step 4: Passport Linkages**
Optional links to other passport records (product ↔ material relationships):
- **RelatedPassportId**: Identifier or URL of the related passport
- **RelationType**: Relationship type (derived_from, contributes_to, split_from, merged_into, recycled_into, manufactured_from)
- **OperationRef**: Optional reference to a traceability or life-cycle event that defines the linkage

Examples of supported schemas:
- CE-RISE models (product-profile v1.0, usage-and-maintenance v1.0)
- GS1 EPCIS events
- Schema.org Product types
- Industry standards (IEC 61360, ISO 14040 series)
- Proprietary company schemas
- National/regional standards

### Data Properties

The metadata is intentionally minimal - it declares what schemas are used without duplicating their content. Each referenced schema brings its own validation rules, ontology bindings, and semantic definitions.

#### SQL Identifiers

Every data point in the model includes a `sql_identifier` annotation that serves as a unique, machine-friendly database identifier. These identifiers follow a structured namespace pattern to ensure uniqueness across the entire data model:

**Pattern**: `dpm_[category]_[specific_name]`

**Features:**
- **DMP & DPP Metadata Prefix**: All identifiers start with `dpm_` to clearly identify them as DMP & DPP Record Metadata
- **Hierarchical Namespacing**: Uses category prefixes (`schema_`, `version_`)
- **Database-Friendly**: Uses underscores and avoids special characters for SQL compatibility
- **Unique Across Model**: No duplicate identifiers within the metadata model
- **Metadata-specific**: Designed to coexist with product data identifiers from other models

**Examples:**
- `dpm_schema_reference_url` - URL or identifier of an applied schema
- `dpm_schema_type` - Type classification (CE-RISE, GS1, custom, etc.)
- `dpm_schema_language` - Technical format (LinkML, JSON-Schema, etc.)
- `dpm_schema_version` - Version of an applied schema
- `dpm_schema_hash` - Integrity checksum of schema
- `dpm_schema_order` - Sequence position in composite record
- `dpm_schema_role` - Purpose of schema in DMP/DPP
- `dpm_schema_completeness` - Data coverage level
- `dpm_record_scope` - Record scope (product or material)
- `dpm_related_passport_id` - Identifier for a related passport
- `dpm_relation_type` - Type of relationship to the related passport
- `dpm_operation_ref` - Reference to a traceability or life-cycle event
- `dpm_metadata_version` - Version of this metadata schema

This identifier system enables the metadata to be stored alongside product data without naming conflicts.

---

## Development Roadmap

| Step | Component | Sub-Components | Criticalities Identified | Solutions Implemented | Status | Missing/TODO |
|------|-----------|---------------|-------------------------|----------------------|--------|--------------|
| **1** | **Schema References<br>(Core Metadata)** | • SchemaURL & Identifier<br>• SchemaType & Language<br>• Version & Hash<br>• Namespace<br>• Documentation | • Support any schema type<br>• Handle diverse versioning<br>• Schema integrity verification<br>• Parser selection<br>• Namespace conflicts | • Dual reference (URL/ID)<br>• Type taxonomy<br>• Hash with algorithm<br>• Namespace isolation<br>• Documentation links | **COMPLETED** | • Schema registry integration<br>• Auto-discovery<br>• Hash verification tools |
| **2** | **Schema Usage &<br>Composition** | • SchemaRole & Profile<br>• Completeness metrics<br>• Fallback schemas<br>• Composition info<br>• Dependencies | • Purpose classification<br>• Partial schema usage<br>• Graceful degradation<br>• Complex compositions<br>• Dependency management | • Role taxonomy<br>• Dual completeness metrics<br>• Fallback URLs<br>• Composition methods<br>• Dependency tracking | **COMPLETED** | • Role standardization<br>• Profile validation<br>• Coverage analysis |
| **3** | **Metadata Versioning** | • Schema version<br>• Compatibility<br>• Timestamps<br>• Parser requirements<br>• Language | • Metadata evolution<br>• Backward compatibility<br>• Lifecycle tracking<br>• Parser compatibility | • Semantic versioning<br>• Compatibility levels<br>• Created/modified dates<br>• Min parser version<br>• ISO language codes | **COMPLETED** | • Auto-migration<br>• Version negotiation |

### Integration Opportunities

- **W3C DCAT** - Data Catalog Vocabulary for dataset metadata
- **Schema.org Dataset** - For dataset-level metadata structures
- **DCMI Terms** - Dublin Core for basic metadata elements
- **VOID** - Vocabulary of Interlinked Datasets
- **JSON-LD** - For @context declarations when using multiple schemas
- **OpenAPI/AsyncAPI** - For API schema references
- **GS1 Web Vocabulary** - For GS1 schema references
- **ISO 15836** - Dublin Core Metadata Element Set
- **LinkML** - For schema definitions

---

## Publishing

Release artifacts for each version (`schema.json`, `shacl.ttl`, `model.owl`)  
are served directly from this URL:
```
https://ce-rise-models.codeberg.page/dp-record-metadata/
```


---

## Accessing Previous Releases

If you want to view the files published for version `v1.2.0`, open:

```
https://codeberg.org/CE-RISE-models/dp-record-metadata/src/tag/pages-v1.2.0/generated/
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
