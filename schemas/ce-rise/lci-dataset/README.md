# CE-RISE Life Cycle Inventory Dataset

[![DOI](https://zenodo.org/badge/DOI/10.5281%2Fzenodo.22710170.svg)](https://doi.org/10.5281/zenodo.22710170) [![Schemas](https://img.shields.io/badge/Schema%20Files-LinkML%2C%20JSON%2C%20SHACL%2C%20OWL-32CD32)](https://ce-rise-models.codeberg.page/lci-dataset/)

This repository defines the CE-RISE data model for reusable life cycle inventory datasets. It represents dataset metadata, activities, flows, flow objects, activity types, locations, temporal scopes, lifecycle stages, classifications, quantitative exchange data, and versioned source records. It provides reusable inventory data without defining a calculation-specific Product System or life cycle assessment result.

**Applicability**: This model supports both **Digital Product Passports (DPP)** and **Digital Material Passports (DMP)**. It can represent product, material, component, assembly, or other inventory data, and foreground, background, and hybrid inventory scope.

---

## Data Model Structure

The Life Cycle Inventory Dataset data model defines reusable life cycle inventory data. It uses BONSAI semantic mappings for activities, flows, flow objects, and activity types; OM 2 mappings for measures and units; SKOS for classifications and lifecycle stages; Schema.org for locations; and PROV-O for source-record provenance. ORIONT concepts for flow direction, flow location, reference year, and validity year are represented locally because no stable machine-readable ORIONT import is available.

### Key Design Principles

- **Reusable inventory data**: An `LCIDataset` owns activities and flows that can support multiple Product System assemblies.
- **Graph-based representation**: Activities and flows represent transformations, external background connections, product exchanges, waste exchanges, and elementary interventions.
- **Direct quantity representation**: BONSAI `Flow` records use OM 2 numerical-value and unit fields.
- **Reference-only provenance**: CE-RISE records, external datasets, artifacts, versions, and mappings are referenced rather than duplicated in the inventory dataset.
- **Assessment independence**: Product System assembly, functional units, assessment methods, impact indicators, LCIA results, and result partitions remain outside this model.
- **Controlled extensibility**: Flow types, lifecycle stages, classifications, locations, and units can reference external schemes instead of hardcoding a single vocabulary.
- **Optional enrichment**: All fields are optional. Metrological traceability, data quality, and uncertainty records can be added where applicable without preventing basic inventory representation.
- **CE-RISE conventions**: Classes use direct LinkML attributes; semantic mappings use `class_uri` and `owl.filler` annotations; and stored values use unique `sql_identifier` annotations.

### Model Boundaries Within CE-RISE Architecture

Within CE-RISE, `lci-dataset` owns reusable inventory data; `product-system` defines a calculation-specific assembly of selected LCI datasets and activities; and `integrated-lca` represents assessment inputs, methods, results, interpretation, and reporting.

**This model includes:**
- Reusable foreground, background, and hybrid life cycle inventory datasets
- Activities, flows, flow objects, activity types, quantities, units, locations, temporal scope, lifecycle stages, and classifications
- Versioned references to CE-RISE records, external datasets, artifacts, selection rules, and transformations
- Optional uncertainty, metrological traceability, and data quality records where represented by the schema

**This model excludes:**
- Product System assembly, selected-activity composition, and reference-flow demand
- Functional-unit definition, assessment methods, impact indicators, LCIA results, interpretation, and reporting owned by `integrated-lca`
- Product and material identity, composition, and other source content owned by profile models
- Lifecycle event histories and operational records owned by traceability and lifecycle models
- Execution of inventory or impact calculations, which remains the responsibility of consuming tools and services

### Core Hierarchy

```
LCIDataset (root)
|- LCIDatasetIdentifier, Name, Description, Version, and Scope
|- Activities (repeatable)
|  |- ActivityTypeReference, LocationReference, and TemporalScope
|  |- DeterminingFlowReference, LifecycleStageReference, and Origin
|  `- SourceRecordReferences and optional traceability and data-quality records
|- Flows (repeatable)
|  |- FlowKind, FlowDirection, and FlowObjectReference
|  |- InputToActivityReference, OutputOfActivityReference, and CounterpartActivityReference
|  |- FlowLocationReference and LifecycleStageReference
|  |- FlowNumericalValue, FlowUnitReference, and FlowQuantityKindReference
|  `- Classifications, source records, and optional uncertainty, traceability, and data-quality records
|- FlowObjects (repeatable)
|  `- Identifier, name, kind, classifications, and source records
|- ActivityTypes (repeatable)
|  `- Identifier, name, URI, and classifications
|- Locations (repeatable)
|  `- Identifier, name, URI, code, and scheme reference
|- LifecycleStages (repeatable)
|  `- Identifier, code, name, scheme, sequence, and definition reference
`- SourceRecordReferences (repeatable)
   |- Source model and referenced-record identifiers, URIs, and versions
   |- Source artifact URI and checksum
   `- Data-selection, mapping, transformation, and retrieval references
```

### Workflow Sequence

#### **Step 1: Define the inventory dataset**
Use `LCIDataset` to identify the represented inventory data, its version, and its foreground, background, hybrid, or other scope.

#### **Step 2: Build the inventory graph**
Use `Activity`, `Flow`, `FlowObject`, and `ActivityType` to represent transformations and exchanges. A flow may be linked as input to or output from an activity and may point to a counterpart activity, including an external background activity.

#### **Step 3: Contextualize exchanges**
Use `LCIDatasetLocation`, `TemporalScope`, `LifecycleStage`, and `ClassificationReference` for geographic, temporal, stage, compartment, and other controlled-vocabulary context. `FlowDirection`, flow-specific location, reference year, and validity year retain applicable ORIONT concepts.

#### **Step 4: Preserve provenance and optional utility information**
Use `SourceRecordReference` to record source-model and record versions, artifacts, checksums, and selection or transformation rules. `LCIDataset` and `Activity` support optional metrological traceability and data-quality records; `Flow` additionally supports optional uncertainty records.

### Data Properties

All model fields are optional. Scalar fields use typed ranges where relevant, including floats for measures, URIs for resolvable identifiers, dates and datetimes for temporal values, and `xsd:gYear` for reference and validity years. Flow kinds cover product, elementary, waste, and other flows; flow direction distinguishes input and output exchanges.

#### SQL Identifiers

Every stored value and permissible value has a unique `sql_identifier` annotation. Identifiers follow this namespace pattern:

**Pattern**: `lci_[category]_[specific_name]`

**Features:**
- **LCI Dataset Prefix**: All identifiers start with `lci_`.
- **Hierarchical Namespacing**: Category prefixes provide context and prevent naming conflicts.
- **Database-Friendly**: Identifiers use underscores and avoid special characters.
- **Unique Across Model**: No duplicate identifiers occur within the model.

---

## Development Roadmap

| Step | Component | Criticalities Identified | Solutions Implemented | Status | Missing/TODO |
|------|-----------|-------------------------|----------------------|--------|--------------|
| **1** | **LCIDataset and Scope** | Reusable inventory data requires its own versioned ownership boundary, separate from Product System assembly | Versioned `LCIDataset` root with declared inventory scope | **COMPLETED** | - |
| **2** | **Inventory Graph** | Activities, exchanges, foreground data, circular flows, and background references need consistent representation | BONSAI-aligned activities, flows, flow objects, activity types, input/output relations, counterpart activities, and direct flow measures | **COMPLETED** | - |
| **3** | **Context, Classifications, and Sources** | Inventory exchanges need temporal, geographic, lifecycle-stage, classification, and reproducible source context | Location, temporal scope, ORIONT-compatible direction and years, SKOS concepts, and PROV-O-aligned source records | **COMPLETED** | - |
| **4** | **Cross-Cutting Utility Integration** | Inventory data needs optional uncertainty, traceability, and quality information | Schema-level utility links where applicable, without changing the minimum inventory record | **COMPLETED** | - |

### Integration Opportunities

- **BONSAI**: Activity, flow, flow-object, activity-type, determining-flow, input, output, location, and temporal semantics
- **OM 2**: Direct numerical values and units for flows
- **ORIONT**: Flow direction, flow location, lifecycle-stage context, reference year, and validity year concepts
- **SKOS**: Lifecycle-stage, elementary-flow-compartment, and external classification concepts
- **Schema.org and PROV-O**: Location and versioned source-record, artifact, and transformation provenance
- **External LCI datasets and tools**: Background activities and datasets can be referenced with source-record versions and artifacts
- **CE-RISE source models**: Product, material, traceability, usage, circularity, and other records can be referenced through `SourceRecordReference`
- **Product System**: `product-system` can assemble versioned LCI dataset records into calculation-specific Product Systems
- **CE-RISE utility models**: `uncertainty-quantification`, `metrological-traceability`, and `data-quality-framework` records can be included where the corresponding LCI dataset fields are available

---

## Publishing

Release artifacts for each version (`schema.yaml`, `schema.json`, `shacl.ttl`, `model.ttl`)
are served directly from this URL:
```
https://ce-rise-models.codeberg.page/lci-dataset/
```

---

## Accessing Previous Releases

If you want to view the files published for version `v0.0.1`, open:

```
https://codeberg.org/CE-RISE-models/lci-dataset/src/tag/pages-v0.0.1/
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

Funded by the European Union under Grant Agreement No. 101092281 - CE-RISE.
Views and opinions expressed are those of the author(s) only and do not necessarily reflect those of the European Union or the granting authority (HADEA).
Neither the European Union nor the granting authority can be held responsible for them.

Copyright 2026 CE-RISE consortium.
Licensed under [Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0)](https://creativecommons.org/licenses/by-nc/4.0/).
Attribution: CE-RISE project (Grant Agreement No. 101092281) and the individual authors/partners as indicated.

<a href="https://www.nilu.com" target="_blank" rel="noopener noreferrer">
  <img src="https://nilu.no/wp-content/uploads/2023/12/nilu-logo-seagreen-rgb-300px.png" alt="NILU logo" height="20"/>
</a>
<a href="https://www.universiteitleiden.nl" target="_blank" rel="noopener noreferrer">
  <img src="https://upload.wikimedia.org/wikipedia/commons/b/b0/UniversiteitLeidenLogo.svg" alt="Leiden University logo" height="30"/>
</a>
<a href="https://www.empa.ch" target="_blank" rel="noopener noreferrer">
  <img src="https://www.empa.ch/image/company_logo?img_id=31464838&t=1762532293211" alt="Empa logo" height="30"/>
</a>

Developed by NILU (Riccardo Boero - ribo@nilu.no), Leiden University (Mintjes, B.A. (Berend) - b.a.mintjes@cml.leidenuniv.nl), and Empa (Francesco Barilli - francesco.barilli@empa.ch; Roland Hischier - roland.hischier@empa.ch) within the CE-RISE project.
