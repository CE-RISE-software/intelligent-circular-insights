# Approach

Instead of being top-down, we use a bottom-up approach of separate independent modules, supported by cross-cutting models that can be reused in different places and with the possibility of having overlapped models where different models are used to represent the same information. This applies to both product and material passports, which share the same architecture while preserving their distinct information needs.

## Core Foundation: Identification Profile

This is achieved by prescribing only one core identification model component: either the **product-profile** (for product passports) or the **material-profile** (for material passports). This is the way by which the passport can be associated with the product or material and contains immutable identification data.

In the analogy with the human passport, this is like the name and date of birth - immutable information to identify the user, or even the fingerprints in the RFID chip of the passport (maybe also the picture, though people and pictures need to be updated some time).

## Three-Group Architecture Organization

To manage the complexity of modular composition, we organize the architecture into three main groups containing functional layers, each serving specific purposes while maintaining interoperability:

### A. Core Layers
The foundation of every Digital Product Passport:

* **Identification** - Static, foundational, always present - contains either the **product-profile** or **material-profile** as the required foundation
* **DPP & DMP Metadata** - Three models for comprehensive metadata management:
  * `dp-record-metadata` - Semantic and structural metadata for interpreting the DPP
  * `dp-access-and-governance` - Operational and access control metadata
  * `dp-record-custody` - Chain of custody and governance history

### B. Value-Added Information Layers
Domain-specific information that creates value throughout the product lifecycle:

* **Dynamic Lifecycle** - Events, operations, and time-dependent changes throughout the product lifecycle
* **Operation & Use** - How a product is used, maintained, and operated
* **Impact Assessment** - Environmental, social, and economic impact assessment using reusable `lci-dataset` records, calculation-specific `product-system` assemblies, and `integrated-lca` assessment inputs and results
* **Circularity & End-of-Life** - Circularity criteria, metrics, and end-of-life pathways
* **Legal, Compliance & Standards** - Regulatory, certification, and normative requirements

### C. Cross-Cutting Utility Layers
Reusable components that enhance data quality and reliability across all other layers:

* **Uncertainty** - Generic structures for representing uncertainty in measurements or assessments, and for documenting their metrological or methodological traceability basis
* **Data Quality** - Metadata for provenance, representativeness, completeness, and assessment pedigree

## Modular Composition

This three-group organization enables:

* **Clear separation of concerns** between core infrastructure, domain-specific value, and quality assurance
* **Independent modules** that can be developed and maintained separately within each layer
* **Cross-cutting models** that provide reusable components across different layers and contexts
* **Overlapped models** allowing different representations of the same information
* **Flexible composition** based on specific needs and requirements

## User-Driven Model Selection

Users have complete flexibility to select and combine models from the architecture based on their specific needs, without being constrained by predefined profiles. This approach allows them to:

* Start with the required core models and add others as needed
* Adapt their model selection over time as requirements evolve
* Maintain interoperability while customizing for their context

## Architecture Benefits

### Scalability
The three-group structure allows organizations to:
* Start with Core Layers for basic DPP & DMP functionality
* Progressively add Value-Added layers based on business needs
* Apply Cross-Cutting utilities where data quality, traceability, or uncertainty matter most

### Interoperability
By separating concerns into groups:
* Core layers ensure universal product identification
* Value-Added layers can vary by industry or use case
* Cross-Cutting layers provide consistent reliability and quality metadata

### Future-Proofing
The architecture accommodates evolution through:
* New models within existing layers
* New layers within the established groups
* Alternative models for the same purpose without breaking compatibility

## Flexibility Benefits

This flexibility in the approach allows sophisticated data representations to be easy and less expensive to deploy, but also to be adopted. We do not want to force users into filling in everything but to give the opportunity to use rich information. Hence the possibility to represent metrological traceability, uncertainty, data quality, compliance, etc. - all possible and integratable, at low cost for both system designers and system users.

This approach ensures that while maintaining a common foundation through an identification profile and comprehensive DPP & DMP metadata models, the architecture remains flexible and adaptable to diverse use cases and evolving requirements. The three-group structure provides clarity in understanding which components are essential (Core), which add specific value (Value-Added Information), and which ensure quality and trust (Cross-Cutting Utility).
