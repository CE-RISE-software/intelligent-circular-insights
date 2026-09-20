# CE-RISE Product System

[![DOI](https://zenodo.org/badge/DOI/10.5281%2Fzenodo.22710386.svg)](https://doi.org/10.5281/zenodo.22710386) [![Schemas](https://img.shields.io/badge/Schema%20Files-LinkML%2C%20JSON%2C%20SHACL%2C%20OWL-32CD32)](https://ce-rise-models.codeberg.page/product-system/)

This repository defines the CE-RISE data model for defining LCA product systems through versioned references to reusable life cycle inventory datasets, activities, and flows. It represents calculation-specific assemblies, their reference-flow specifications, scope, provenance, and optional utility records without copying reusable inventory data or storing assessment results.

**Applicability**: This model supports both **Digital Product Passports (DPP)** and **Digital Material Passports (DMP)**. It can define product, material, component, assembly, or other Product Systems from foreground, background, and hybrid life cycle inventory data.

---

## Data Model Structure

The Product System data model defines calculation-specific LCA assemblies. It uses BONSAI semantic mappings for selected activities and reference units, OM 2 mappings for reference-flow measures and units, and PROV-O and Dublin Core Terms for versioned dataset references, source artifacts, assembly specifications, and provenance. It does not own activity, flow, or flow-object records; these remain in the Life Cycle Inventory Dataset model.

### Key Design Principles

- **Calculation-specific assembly**: A `ProductSystem` selects reusable activity records into one declared LCA product system.
- **LCI dataset reuse**: Versioned `LCIDatasetReference` records identify the reusable inventory data available to the assembly without copying it.
- **Explicit activity selection**: Each `ActivityReference` identifies a selected activity and its source LCI dataset reference.
- **Reference-flow scaling**: `ReferenceFlowSpecification` identifies the reference flow and direct OM 2 measure used to scale the Product System.
- **Assessment independence**: Functional units, assessment methods, impact indicators, LCIA results, interpretation, and reporting remain in `integrated-lca`.
- **Reproducible assembly**: Artifact versions, checksums, selection rules, mapping references, and retrieval timestamps can be recorded without prescribing a particular LCA tool.
- **Optional enrichment**: All fields are optional. Metrological traceability, data quality, and uncertainty records can be added where applicable without preventing basic Product System representation.
- **CE-RISE conventions**: Classes use direct LinkML attributes; semantic mappings use `class_uri` and `owl.filler` annotations; and stored values use unique `sql_identifier` annotations.

### Model Boundaries Within CE-RISE Architecture

**This model includes:**
- Calculation-specific Product System identity, version, description, and declared scope
- Versioned references to reusable LCI datasets and selected activities
- Reference-flow quantities, units, and optional uncertainty, traceability, and quality records
- Assembly specifications, source artifacts, checksums, and retrieval provenance

**This model excludes:**
- Reusable activity, flow, flow-object, location, temporal, lifecycle-stage, and classification records owned by `lci-dataset`
- Functional-unit definition, assessment methods, impact indicators, LCIA results, interpretation, and reporting owned by `integrated-lca`
- Product and material identity, composition, and other source content owned by profile models
- Lifecycle event histories and operational records owned by traceability and lifecycle models
- Execution of inventory or impact calculations, which remains the responsibility of consuming tools and services

### Core Hierarchy

```
ProductSystem (root)
|- ProductSystemIdentifier, Name, Description, Version, and Scope
|- LCIDatasetReferences (repeatable)
|  |- Source model, dataset identifiers, URIs, and versions
|  |- Source artifact URI and checksum
|  `- Data-selection, mapping, transformation, and retrieval references
|- ActivityReferences (repeatable)
|  |- LCIDatasetReferenceIdentifier
|  |- ActivityIdentifier, URI, and Version
|  `- ActivitySelectionReference
|- ReferenceFlowSpecification
|  |- ReferenceFlowLCIDatasetReferenceIdentifier and ReferenceFlowIdentifier
|  |- ReferenceFlowObjectReference, NumericalValue, and UnitReference
|  `- Optional uncertainty, traceability, and data-quality records
|- AssemblySpecificationReference
`- Optional product-system traceability and data-quality records
```

### Workflow Sequence

#### **Step 1: Declare reusable inventory datasets**
Use `LCIDatasetReference` to identify the versioned inventory datasets and concrete source artifacts available to the Product System.

#### **Step 2: Select the activity graph**
Use `ActivityReference` to select the source activities that compose the Product System. The referenced LCI datasets retain the flow records that link the selected activities.

#### **Step 3: Define scaling and assembly provenance**
Use `ReferenceFlowSpecification` to define the Product System scaling basis. Use `assembly_specification_reference` to retain the query, selection, mapping, or configuration used to create the assembly.

#### **Step 4: Preserve optional utility information**
Use the optional uncertainty, metrological traceability, and data-quality links to qualify reference-flow and Product System information where applicable.

### Data Properties

All model fields are optional. Scalar fields use typed ranges where relevant, including floats for reference-flow measures, URIs for resolvable references, and datetimes for input retrieval. The referenced LCI Dataset model remains responsible for activity, flow, and flow-object data.

#### SQL Identifiers

Every stored value and permissible value has a unique `sql_identifier` annotation. Identifiers follow this namespace pattern:

**Pattern**: `ps_[category]_[specific_name]`

**Features:**
- **Product System Prefix**: All identifiers start with `ps_`.
- **Hierarchical Namespacing**: Category prefixes provide context and prevent naming conflicts.
- **Database-Friendly**: Identifiers use underscores and avoid special characters.
- **Unique Across Model**: No duplicate identifiers occur within the model.

---

## Development Roadmap

| Step | Component | Criticalities Identified | Solutions Implemented | Status | Missing/TODO |
|------|-----------|-------------------------|----------------------|--------|--------------|
| **1** | **Product System Assembly** | One reusable inventory dataset can support multiple calculation-specific Product Systems | Versioned Product System container with declared scope and assembly provenance | **COMPLETED** | - |
| **2** | **LCI Dataset References** | Assemblies must identify the exact reusable inventory records and artifacts they consume | Versioned LCI dataset references with source-model, dataset, artifact, checksum, selection, and retrieval information | **COMPLETED** | - |
| **3** | **Activity Selection and Scaling** | A Product System needs explicit selected activities and a reproducible scaling basis without copying inventory data | Activity references linked to LCI dataset references and BONSAI- and OM 2-aligned reference-flow specification | **COMPLETED** | - |
| **4** | **Cross-Cutting Utility Integration** | Product System inputs need optional uncertainty, traceability, and quality information | Schema-level utility links where applicable, without changing the minimum Product System record | **COMPLETED** | - |

### Integration Opportunities

- **LCI Dataset**: `lci-dataset` supplies reusable activity, flow, and flow-object records through versioned dataset and activity references
- **BONSAI**: Selected activity and reference-unit semantics
- **OM 2**: Direct numerical values and units for reference-flow measures
- **PROV-O and Dublin Core Terms**: Versioned dataset, artifact, selection, mapping, and retrieval provenance
- **Integrated LCA**: `integrated-lca` can consume a versioned Product System artifact as an assessment input without a reverse dependency
- **CE-RISE utility models**: `uncertainty-quantification`, `metrological-traceability`, and `data-quality-framework` records can be included where the corresponding Product System fields are available

---

## Publishing

Release artifacts for each version (`schema.yaml`, `schema.json`, `shacl.ttl`, `model.ttl`)
are served directly from this URL:
```
https://ce-rise-models.codeberg.page/product-system/
```

---

## Accessing Previous Releases

If you want to view the files published for version `v0.0.1`, open:

```
https://codeberg.org/CE-RISE-models/product-system/src/tag/pages-v0.0.1/
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
