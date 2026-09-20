# Components

The CE-RISE DPP architecture is organized into three main groups of components, each containing functional layers with specific data models that maintain interoperability across the system.

## Architecture Components by Group

---

### A. Core Layers

Foundation components that are essential for every Digital Product Passport.

#### <u>Product Identification Layer</u>
I. **[Product Profile](product-profile.md)** - Defines the immutable identity, origin, and basic specification of the product

#### <u>Material Identification Layer</u>
I. **[Material Profile](material-profile.md)** - Defines the immutable identity, origin, and basic specification of the material

#### <u>DPP & DMP Metadata Layer</u>
Models providing metadata for DPP & DMP record management and governance:

I. **[DP Record Metadata](dp-record-metadata.md)** - Semantic and structural metadata of the DPP record
  * Ontology bindings and schema references
  * Data model versions and profiles
  * Supported representation formats
  * Validation schemas
  
II. **[DP Access and Governance](dp-access-and-governance.md)** - Operational and access-related metadata
  * Access levels and permissions
  * Security settings
  * Data carrier specifications
  * Longevity policies
  * Interoperability configurations
  
III. **[DP Record Custody](dp-record-custody.md)** - Chain of custody and governance history
  * Custody event tracking
  * Custodian identification
  * Transfer authorizations
  * Integrity evidence (signatures, hashes)

---

### B. Value-Added Information Layers

Domain-specific components that provide rich information throughout the product lifecycle.

#### <u>Dynamic Lifecycle Layer</u>
Models capturing time-dependent changes and events:

I. **[Traceability and Lifecycle Events](traceability-and-life-cycle-events.md)** - Dynamic traceability and supply-chain events

II. **[Diagnostic Results](diagnostic-results.md)** - Structured outputs from diagnostic, repair, service, or condition-assessment operations

#### <u>Operation & Use Layer</u>
I. **[Usage and Maintenance](usage-and-maintenance.md)** - Product usage, service/repair actions, and instructions for operation and upkeep

#### <u>Impact Assessment Layer</u>
Models for comprehensive impact calculations:

I. **[Integrated LCA](integrated-lca.md)** - Environmental, social, and economic assessment inputs, methods, results, and interpretation

II. **[Product System](product-system.md)** - Calculation-specific assembly of versioned LCI datasets and selected activities, with reference-flow and provenance information

III. **[Life Cycle Inventory Dataset](lci-dataset.md)** - Reusable inventory activities, flows, flow objects, exchange quantities, and source provenance

#### <u>Circularity & End-of-Life Layer</u>
Circularity metrics and end-of-life pathways:

I. **[Circularity and EoL](circularity-and-eol.md)** - Design for circularity, performance scores, and end-of-life information

II. **[RE Indicators Specification](re-indicators-specification.md)** - Specific end-of-life indicators and recovery options

#### <u>Legal, Compliance & Standards Layer</u>
Regulatory and standards conformity:

I. **[Compliance and Standards](compliance-and-standards.md)**  - Regulatory compliance, certifications, and evidence documentation

II. **Conformity Requirements Specification** *(planned)* - Standard-specific data requirements and procedures

---

### C. Cross-Cutting Utility Layers

Reusable components that support data quality and reliability across all other layers.

#### <u>Uncertainty Layer</u>
I. **[Uncertainty Quantification](uncertainty-quantification.md)** - Generic structures for representing uncertainty in measurements, assessments, and indicators

II. **[Metrological Traceability](metrological-traceability.md)** - Reusable structures for documenting the metrological and methodological reference basis of measured, calculated, method-defined, or boundary-defined values

#### <u>Data Quality Layer</u>
I. **[Data Quality Framework](data-quality-framework.md)** - Metadata for data quality, provenance, representativeness, completeness, and assessment pedigree

---


## Using the Components

### Modularity
Each component can be used independently or combined with others based on your specific use case requirements.

### Interoperability
All components follow standardized interfaces to ensure seamless integration across different systems and platforms.

### Extensibility
The architecture allows for custom extensions and additional models as new requirements emerge.

For detailed specifications and schemas for each model, visit the individual component pages or their respective repositories.
