# CE-RISE Traceability and Life Cycle Event

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.17803667.svg)](https://doi.org/10.5281/zenodo.17803667) [![Schemas](https://img.shields.io/badge/Schema%20Files-LinkML%2C%20JSON%2C%20SHACL%2C%20OWL-32CD32)](https://ce-rise-models.codeberg.page/traceability-and-life-cycle-events/)

The Traceability and Life Cycle Events data model captures **dynamic event-based information** throughout the supply chain journey and entire lifecycle of products, materials, batches, and commodities. This model is part of the CE-RISE Digital Product Passport (DPP) and Digital Material Passport (DMP) architecture, focusing specifically on time-stamped events that occur during supply chain operations.

**Applicability**: This model supports tracking of any entity type - individual products, material batches, components, commodities, or assemblies - using the same event-based framework.

---

## Data Model Structure

This model is designed to be **compatible with GS1 EPCIS 2.0** (Electronic Product Code Information Services), the global standard for supply chain visibility, while extending it with additional fields required for Digital Product Passports. Built using [LinkML](https://linkml.io/), it generates multiple schema formats (JSON Schema, SHACL, OWL).

**Core Philosophy**: This model answers critical questions about entity journey and lifecycle (whether product, material, batch, or commodity):
- **"Where has this entity been?"** → Supply chain events and logistics tracking
- **"Who has handled it?"** → Ownership transfers and actor involvement
- **"What happened to it?"** → Value-adding activities and transformations
- **"How did it move?"** → Transportation events during supply chain journey
- **"Can it be returned?"** → Reverse logistics and end-of-life pathways

## Model Boundaries Within CE-RISE Architecture

### What This Model INCLUDES:
- **Supply chain custody and movement events** - All time-stamped events showing entity location and status changes for products, materials, batches, or commodities
- **Business transaction and ownership transfers** - Legal custody changes and commercial transactions for any tracked entity
- **Entity transformations during supply chain** - Value-adding activities, processing, packaging operations on products or materials
- **Actor interactions and responsibilities** - Who handled the entity when and in what capacity
- **Transportation and logistics operations** - Movement between locations with carrier and route details
- **Return and reverse logistics pathways** - Returns, refurbishment routing, and end-of-life collection for products and materials
- **Supply chain inventory operations** - Stock movements, transfers, and custody changes at facilities (integrated in LogisticsEvents)
- **Packaging hierarchy events** - Aggregation and disaggregation operations for items, batches, cases, pallets, containers (Step 7)
- **Supply chain incidents and exceptions** - Damage, theft, delays, contamination, and other disruptions during operations (Step 8)

### What This Model EXCLUDES (handled by other CE-RISE models):
- **Static identity and specifications** → `product-profile` or `material-profile` models (identity, manufacturing origin, composition, initial import/export data)
- **Diagnostic and test results** → `diagnostic-results` model (service reports, condition assessments, quality test outputs)
- **Usage patterns and maintenance activities** → `usage-and-maintenance` model (how entity is used, maintenance schedules, repair records)
- **Environmental impact calculations** → `integrated-lca` model (carbon footprint, resource consumption, impact assessments)
- **Regulatory compliance status and certifications** → `compliance-and-standards` model (regulatory approvals, compliance evidence, certificates)
- **Data quality, uncertainty, and metrological traceability metadata** → `data-quality-framework`, `uncertainty-quantification`, and `metrological-traceability` utility models
- **Circularity design and end-of-life specifications** → `circularity-and-eol` model (design for circularity, recyclability, material recovery specifications)

**Key Principle**: This model focuses exclusively on time-stamped events and state changes that occur during supply chain operations, from initial market entry through end-of-life collection.

### EPCIS Alignment Strategy

This model adopts and extends the **GS1 EPCIS 2.0 standard** event structure:
- **ObjectEvent** → Maps to our LogisticsEvents (observation of objects at locations)
- **TransactionEvent** → Maps to our OwnershipEvent (business transactions)
- **TransformationEvent** → Maps to our ValueAddingActivityLocation (inputs to outputs)
- **AggregationEvent** → Maps to our AggregationEvents (packaging/unpacking operations)
- **AssociationEvent** → Maps to our ActorTracking (entity associations)

Each event type inherits EPCIS's four dimensions (What, When, Where, Why) and extends them with DPP-specific requirements. This ensures:
- Direct import/export of EPCIS event data
- Compatibility with existing GS1 infrastructure
- Extensibility for circular economy requirements

### Why This Model Beyond Direct EPCIS Usage

**This model provides a DPP-optimized structure for EPCIS events, adding explicit support for reverse logistics (returns, refurbishment, recycling) which EPCIS handles weakly.** Rather than requiring implementers to interpret how EPCIS maps to DPP needs, this model provides that mapping explicitly with clear event categories for ownership transfers, value-adding activities, and end-of-life pathways that are critical for circular economy but not well-defined in standard EPCIS implementations.

### Core Hierarchy

```
TraceabilityLifecycleEvents (root - for products, materials, batches, commodities)
├── 1. EntityHistory
│   ├── EventIdentifier
│   ├── EventTimestamp
│   ├── EventType
│   ├── EventLocation
│   ├── EventDescription
│   └── LinkedEntityIdentifier (EPC URI, GTIN+serial, batch number, lot ID)
├── 2. OwnershipEvent
│   ├── TransferDate
│   ├── PreviousOwner (GLN, LEI, organization details)
│   ├── NewOwner (GLN, LEI, organization details)
│   ├── TransferType (sale, consignment, lease, donation)
│   ├── TransferLocation
│   ├── ChainOfCustodyReference
│   └── OwnershipDocumentation
├── 3. PhysicalCustodyEvent (in-workshop custody handoffs, distinct from legal ownership)
│   ├── CustodyEventIdentifier
│   ├── LinkedEntityIdentifier
│   ├── CustodyStage (intake/storage/bench/data-wipe/QA/packaging/resale/shipping)
│   ├── Holder
│   ├── CustodyLocation
│   ├── CustodyTimestamp
│   ├── TransferReason
│   ├── SealStatus (sealed/open/tamper-evident)
│   └── CustodyEvidence
├── 4. ValueAddingActivityLocation
│   ├── ActivityIdentifier
│   ├── ActivityType (assembly, processing, packaging, quality control)
│   ├── ActivityDate
│   ├── FacilityIdentifier (GLN, OSID)
│   ├── ProcessDescription
│   ├── InputEntities (components/materials/batches consumed)
│   └── OutputEntities (resulting products/materials/batches)
├── 5. ActorTracking
│   ├── ActorIdentifier (GLN, LEI, VAT)
│   ├── ActorRole (manufacturer, distributor, retailer, service provider)
│   ├── ActivityTimestamp
│   ├── ActionPerformed
│   ├── ResponsibilityScope
│   └── CertificationStatus
├── 6. LogisticsEvents
│   ├── ShipmentIdentifier
│   ├── TransportMode (road, rail, sea, air, multimodal)
│   ├── DepartureLocation (UN/LOCODE)
│   ├── DepartureTimestamp
│   ├── ArrivalLocation (UN/LOCODE)
│   ├── ArrivalTimestamp
│   ├── CarrierIdentifier
│   ├── RouteInformation
│   ├── IntermediateStops
│   │   ├── StopLocation (UN/LOCODE)
│   │   ├── StopTimestamp
│   │   └── StopDuration
│   ├── TransportConditions (temperature, humidity tracking)
│   ├── ShipmentComposition (multiple products in shipment)
│   └── InventoryEvents (stock intake, transfers, adjustments)
├── 7. ReverseLogistics
│   ├── ReturnEventIdentifier
│   ├── ReturnInitiationDate
│   ├── ReturnReason (defect, warranty, end-of-life, recall)
│   ├── IntakeEvent (condition assessment and triage at intake)
│   │   ├── IntakeIdentifier
│   │   ├── IntakeDate
│   │   ├── InternalAssetId / CustomerAssetTag / PreviousOwnerReference
│   │   ├── IntakeLocation
│   │   ├── ReceivedBy
│   │   ├── ConditionItems (repeatable: category/status/description/evidence)
│   │   ├── MediaStatus (data-bearing media: present/removed/wiped/unknown)
│   │   ├── TriageDecision (refurbish/repair/parts-harvest/recycle/dispose/...)
│   │   └── IntakeEvidence
│   ├── CustomerReturnChannels
│   │   ├── ReturnLocation
│   │   ├── ReturnMethod
│   │   └── ReturnDocumentation
│   ├── RefurbishmentEvent
│   │   ├── RefurbishmentDate
│   │   ├── RefurbishmentActivities
│   │   ├── ComponentsReplaced (repeatable ReplacedComponent: name, old/new part & serial, manufacturer, quantity, reason, condition)
│   │   ├── RefurbishmentCertification
│   │   └── DataErasureEvidence (method, standard, tool, certificate ID, media serial, operator, timestamp, result, document)
│   ├── RecyclingEvent
│   │   ├── RecyclingDate
│   │   ├── RecoveryOperation (WFD Annex II: preparation-for-reuse/recycling/energy-recovery/backfilling/other)
│   │   ├── RecyclingStream
│   │   ├── MaterialsRecovered
│   │   └── RecoveryPercentage
│   └── DisposalEvent
│       ├── DisposalDate
│       ├── DisposalMethod (WFD Annex I disposal; energy recovery is NOT disposal)
│       ├── DisposalFacility
│       └── DisposalCertification
├── 8. AggregationEvents
│   ├── AggregationEventID
│   ├── AggregationType (PACK/UNPACK)
│   ├── ParentIdentifier (container, pallet, case)
│   ├── ChildIdentifiers (items being packed/unpacked)
│   ├── AggregationLocation
│   ├── AggregationTimestamp
│   └── PackagingHierarchyLevel
└── 9. SupplyChainIncidents
    ├── IncidentIdentifier
    ├── IncidentType (damage, theft, delay, contamination, cold-chain-break)
    ├── IncidentTimestamp
    ├── IncidentLocation
    ├── AffectedProducts
    ├── IncidentSeverity
    ├── RootCause
    ├── CorrectiveActions
    └── IncidentDocumentation
```

### Workflow Sequence



#### **Step 1: EntityHistory**
Foundation for all lifecycle events with complete audit trail for products, materials, batches, or commodities (EPCIS-compatible base structure):
- **EventIdentifier**: Unique identifier for each event (UUID format, maps to EPCIS eventID)
- **EventTimestamp**: ISO 8601 timestamp with timezone (EPCIS eventTime)
- **EventType**: EPCIS event types (ObjectEvent, TransactionEvent, TransformationEvent, etc.)
- **EventLocation**: GLN or URI for location (EPCIS readPoint/bizLocation)
- **EventDescription**: Human-readable event description (extends EPCIS)
- **LinkedEntityIdentifier**: EPC URI, GTIN + serial, batch number, or lot identifier for tracked entity (EPCIS epcList)
- **Disposition**: Business state (uses EPCIS disposition vocabulary directly)
- **BizStep**: Business process step (uses cbv:BizStep directly)
- **Action**: How event relates to lifecycle (uses epcis:Action directly)

#### **Step 2: OwnershipEvent** 
Legal ownership and custody transfers throughout supply chain (extends EPCIS TransactionEvent):
- **TransferDate**: Precise timestamp of ownership change (EPCIS eventTime)
- **PreviousOwner**: Source party GLN (EPCIS source)
- **NewOwner**: Destination party GLN (EPCIS destination)
- **TransferType**: Business transaction type (uses cbv:BTT directly - po/desadv/inv/rma etc)
- **TransferLocation**: Physical location GLN (EPCIS bizLocation)
- **ChainOfCustodyReference**: Previous event links (EPCIS extensions)
- **OwnershipDocumentation**: Digital references (EPCIS bizTransactionList)


#### **Step 3: ValueAddingActivityLocation**
Transformation and processing events that modify or enhance entities - products, materials, batches, or commodities (EPCIS TransformationEvent):
- **ActivityIdentifier**: Unique activity reference (EPCIS eventID)
- **ActivityType**: Activity type (uses cbv:BizStep directly - commissioning/transformation/decommissioning)
- **ActivityDate**: When occurred (EPCIS eventTime)
- **FacilityIdentifier**: Facility GLN (EPCIS bizLocation)
- **ProcessDescription**: Transformation details (EPCIS extensions)
- **InputEntities**: Input EPCs, batch numbers, or lot identifiers and quantities (EPCIS inputEPCList/inputQuantityList)
- **OutputEntities**: Output EPCs, batch numbers, or lot identifiers and quantities (EPCIS outputEPCList/outputQuantityList)
- **TransformationID**: Links related transformations (EPCIS transformationID)

#### **Step 4: ActorTracking**
All supply chain participants and their interactions with entities (products, materials, batches, commodities):
- **ActorIdentifier**: Organization identifier (GLN/LEI/VAT)
- **ActorRole**: MANUFACTURER/DISTRIBUTOR/WHOLESALER/RETAILER/SERVICE_PROVIDER/TRANSPORTER
- **ActivityTimestamp**: When actor interacted with entity
- **ActionPerformed**: Specific action taken
- **ResponsibilityScope**: Actor's responsibility boundaries
- **CertificationStatus**: Relevant certifications (ISO, organic, fair trade)

#### **Step 5: LogisticsEvents**
Supply chain transportation and movement tracking (post-import):
- **ShipmentIdentifier**: Unique shipment reference (carrier tracking number)
- **TransportMode**: ROAD/RAIL/SEA/AIR/MULTIMODAL/PIPELINE
- **DepartureLocation**: Origin UN/LOCODE (e.g., DEHAM for Hamburg)
- **DepartureTimestamp**: Departure time with timezone
- **ArrivalLocation**: Destination UN/LOCODE
- **ArrivalTimestamp**: Actual or estimated arrival
- **CarrierIdentifier**: Transport company GLN or identifier
- **RouteInformation**: Planned route details
- **IntermediateStops**: Distribution centers, warehouses, and transshipment points
- **TransportConditions**: Temperature, humidity, shock monitoring data
  
*Note: Initial import/export and customs data are captured in the Product Profile or Material Profile models. This tracks subsequent domestic and international movements within the supply chain.*

#### **Step 6: ReverseLogistics**
End-of-life and return pathway management for products and materials:
- **ReturnEventIdentifier**: Unique return tracking ID
- **ReturnInitiationDate**: When return process started
- **ReturnReason**: DEFECT/WARRANTY_CLAIM/END_OF_LIFE/PRODUCT_RECALL/CUSTOMER_DISSATISFACTION
- **CustomerReturnChannels**: Available return methods and locations
- **RefurbishmentEvent**: Repair and refurbishment activities for products or materials
- **RecyclingEvent**: Material and product recovery and recycling processes
- **DisposalEvent**: Final disposal method and certification

#### **Step 7: AggregationEvents**
Packaging hierarchy operations for products, materials, and batches (extends EPCIS AggregationEvent):
- **AggregationEventID**: Unique identifier for aggregation operation (EPCIS eventID)
- **AggregationType**: PACK (aggregation) or UNPACK (disaggregation) operation
- **ParentIdentifier**: Container, pallet, batch, or case EPC being packed/unpacked (EPCIS parentID)
- **ChildIdentifiers**: Items, sub-batches, or materials being aggregated/disaggregated (EPCIS childEPCs)
- **AggregationLocation**: GLN where operation occurred (EPCIS bizLocation)
- **AggregationTimestamp**: When packing/unpacking happened (EPCIS eventTime)
- **PackagingHierarchyLevel**: Level in packaging hierarchy (item/batch/case/pallet/container)

#### **Step 8: SupplyChainIncidents**
Exception and disruption management during supply chain operations:
- **IncidentIdentifier**: Unique incident tracking ID
- **IncidentType**: DAMAGE/THEFT/DELAY/CONTAMINATION/COLD_CHAIN_BREAK/SECURITY_BREACH
- **IncidentTimestamp**: When incident occurred
- **IncidentLocation**: GLN or UN/LOCODE where incident happened
- **AffectedEntities**: EPCs, GTINs, batch numbers, or lot identifiers of affected entities (products, materials, batches, commodities)
- **IncidentSeverity**: CRITICAL/HIGH/MEDIUM/LOW severity level
- **RootCause**: Identified cause of the incident
- **CorrectiveActions**: Actions taken to resolve or mitigate
- **IncidentDocumentation**: References to incident reports, insurance claims, photos

### Key Design Principles

1. **EPCIS Compliance**: Core event structure follows GS1 EPCIS 2.0 standard for maximum interoperability
2. **Event-Centric Architecture**: Every entry is a time-stamped event with clear before/after states
3. **Immutable Event Log**: Events are append-only, creating permanent audit trails
4. **Actor Attribution**: Every event links to responsible actors with verifiable identities
5. **Location Precision**: Events include precise location data using GS1 GLN and international standards
6. **Document Linkage**: Events reference supporting documentation without duplicating static data
7. **Standards-Based**: Native support for GS1 (EPCIS, GLN, GTIN), UN/LOCODE, and ISO standards
8. **Extensible**: EPCIS extension mechanism for DPP-specific requirements
9. **Supply Chain Focused**: Captures only supply chain events, not product usage, diagnostics, or compliance activities (handled by other CE-RISE models)
10. **Interoperable by Design**: Events can be directly imported/exported to EPCIS repositories and integrated with existing supply chain infrastructure



### Data Properties

Each class has a corresponding value property (e.g., `name_value`, `company_id_value`) that holds the actual data. All value properties are string type except where specified otherwise.

#### SQL Identifiers

Every data point in the model includes a `sql_identifier` annotation that serves as a unique, machine-friendly database identifier. These identifiers follow a structured namespace pattern to ensure uniqueness across the entire data model:

**Pattern**: `trc_[category]_[specific_name]`

**Features:**
- **Traceability Prefix**: All identifiers start with `trc_` to clearly identify them as belonging to the Traceability and Life Cycle Events data model
- **Hierarchical Namespacing**: Uses category prefixes (`hist_`, `owner_`, `value_`, `actor_`, `logis_`, `reverse_`, `agg_`, `incident_`) to provide context and prevent naming conflicts
- **Database-Friendly**: Uses underscores and avoids special characters for SQL compatibility
- **Unique Across Model**: No duplicate identifiers, even when similar concepts appear in different parts of the hierarchy
- **Reasonable Length**: Abbreviated but meaningful names that balance clarity with practical database usage

**Examples:**
- `trc_hist_event_id` - Event identifier in Entity History
- `trc_hist_linked_entity_id` - Linked entity identifier (product, material, batch, commodity)
- `trc_owner_transfer_date` - Transfer date in Ownership Events
- `trc_value_input_entities` - Input entities in Value-Adding Activities
- `trc_value_output_entities` - Output entities in Value-Adding Activities
- `trc_actor_gln` - Actor GLN in Actor Tracking
- `trc_logis_shipment_id` - Shipment identifier in Logistics Events
- `trc_reverse_return_reason` - Return reason in Reverse Logistics
- `trc_agg_parent_id` - Parent identifier in Aggregation Events
- `trc_incident_affected_entities` - Affected entities in Supply Chain Incidents

This identifier system enables seamless integration with databases and ensures clear data model composition when combining with other CE-RISE data models.


---

## Development Roadmap

> **Note:** This roadmap documents the model's initial development. The data model has since been further developed and refined — see [CHANGELOG.md](CHANGELOG.md) for the authoritative, up-to-date record of changes.

### Current Implementation Status

| Step | Component | Supply Chain Focus | Solutions Implemented | Status | Missing/TODO |
|------|-----------|-------------------|----------------------|--------|--------------|
| **1** | **EntityHistory** | • Foundation event structure<br>• EPCIS compatibility<br>• Event audit trails<br>• Entity identity linking (products, materials, batches, commodities) | • UUID-based event identifiers<br>• ISO 8601 timestamps<br>• EPCIS EventType alignment<br>• CBV BizStep integration<br>• Links to product-profile or material-profile identifiers | **COMPLETE** | - |
| **2** | **OwnershipEvent** | • Business transaction tracking<br>• Custody chain management<br>• Legal ownership transfers<br>• Supply chain transparency | • GLN-based party identification<br>• CBV BTT vocabulary<br>• Chain of custody references<br>• Digital document linking<br>• Transaction event structure | **COMPLETE** | - |
| **3** | **ValueAddingActivityLocation** | • Supply chain transformations<br>• Processing and packaging<br>• Input/output tracking<br>• Facility-based activities | • CBV BizStep vocabulary<br>• Input/output entity arrays<br>• Facility GLN identification<br>• Transformation event structure<br>• Process documentation | **COMPLETE** | - |
| **4** | **ActorTracking** | • Supply chain participant roles<br>• Actor responsibility tracking<br>• Certification management<br>• Performance accountability | • Multiple identifier support<br>• Role-based tracking<br>• Activity timestamps<br>• Responsibility definitions<br>• Certification status tracking | **COMPLETE** | - |
| **5** | **LogisticsEvents** | • Transportation tracking<br>• Multi-modal logistics<br>• Route optimization<br>• Condition monitoring | • UN/LOCODE standards<br>• Multi-modal support<br>• Intermediate stops<br>• Carrier identification<br>• Transport conditions | **COMPLETE** | - |
| **6** | **ReverseLogistics** | • Return pathway management<br>• End-of-life collection<br>• Reverse supply chains<br>• Recovery operations | • Return reason classification<br>• Multi-channel returns<br>• Refurbishment tracking<br>• Recovery documentation<br>• Disposal certification | **COMPLETE** | - |
| **7** | **AggregationEvents** | • Packaging hierarchy tracking<br>• Parent-child relationships<br>• Pack/unpack operations<br>• Container management | • EPCIS AggregationEvent structure<br>• Parent/child EPC tracking<br>• Hierarchy level classification<br>• Aggregation type handling<br>• Location/timestamp tracking | **COMPLETE** | - |
| **8** | **SupplyChainIncidents** | • Exception event handling<br>• Incident tracking<br>• Risk management<br>• Disruption documentation | • Incident classification system<br>• Severity level tracking<br>• Root cause analysis fields<br>• Corrective action tracking<br>• Documentation references | **COMPLETE** | - |



### Integration Opportunities

**Within CE-RISE Architecture:**
- **Cross-Model References**: Events reference identifiers from `product-profile`, link to results in `diagnostic-results`, trigger updates in `usage-and-maintenance`
- **Data Flow Integration**: Supply chain events feed into `integrated-lca` for impact calculations and `compliance-and-standards` for regulatory tracking
- **Shared Metadata**: Selected event records can optionally reference `uncertainty-quantification`, `metrological-traceability`, and `data-quality-framework` utility model records

**External System Integration:**
- **GS1 EPCIS Infrastructure**: Direct compatibility with EPCIS 2.0 repositories and query interfaces
- **Event Streaming**: Apache Kafka, AWS Kinesis for real-time EPCIS event processing
- **Blockchain**: Immutable event logging via Hyperledger Fabric or Ethereum with EPCIS payloads
- **IoT Platforms**: Integration with transport condition sensors generating EPCIS sensor events
- **Standards Bodies**: Full GS1 EPCIS 2.0 compliance, CBV (Core Business Vocabulary), UN/CEFACT alignment
- **Analytics**: Time-series databases for event analysis, graph databases for EPCIS event chains
- **External APIs**: EPCIS capture/query interfaces, GS1 Digital Link resolvers, carrier tracking APIs
- **Existing Systems**: Import from legacy WMS/ERP systems via EPCIS adapters



---

## Accessing Previous Releases

If you want to view the files published for version `v1.2.0`, open:

```
https://codeberg.org/CE-RISE-models/traceability-and-life-cycle-events/src/tag/pages-v1.2.0/generated/
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
