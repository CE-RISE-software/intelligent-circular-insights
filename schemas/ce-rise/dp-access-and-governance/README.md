# CE-RISE DP Access and Governance

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.17899269.svg)](https://doi.org/10.5281/zenodo.17899269) [![Schemas](https://img.shields.io/badge/Schema%20Files-LinkML%2C%20JSON%2C%20SHACL%2C%20OWL-32CD32)](https://ce-rise-models.codeberg.page/dp-access-and-governance/)

Repository for the CE-RISE DP (Digital Passport) Access and Governance data model, part of the DP Metadata Layer in the digital product passport and/or digital material passport architecture. This model defines the operational and access-related metadata that governs how DPP and DMP records are stored, exposed, shared, and maintained across systems. It specifies access levels, security settings, data carrier characteristics, longevity policies, interoperability configurations, and system integration parameters. This metadata acts as the "operational envelope" that controls how DPP and DMP data is accessed and managed throughout its lifecycle, complementing the structural metadata (dpp-record-metadata) and custody tracking (dpp-record-custody).


---

## Data Model Structure
This data model provides the operational framework for DPP and DMP record management, defining how data is accessed, who can access it, where it's stored, and how long it remains available. It ensures proper governance of DPP and DMP data across different systems, access contexts, and lifecycle stages while maintaining security and compliance requirements.

### Key Design Principles
1. **Access control granularity**: Support for multi-level access rights (public, authenticated, role-based)
2. **Carrier agnostic**: Works with any data storage mechanism (QR codes, RFID, cloud, blockchain)
3. **Longevity awareness**: Explicit policies for data retention and availability
4. **Security by design**: Built-in security classification and encryption support
5. **Interoperability focus**: Standard protocols and API specifications for cross-system integration
6. **Compliance ready**: Supports regulatory requirements for data access and retention

### Core Hierarchy

```
DPAccessAndGovernance (root)
├── 1. AccessControl
│   ├── AccessLevels
│   │   ├── PublicAccess
│   │   │   ├── PublicFields (list of openly accessible fields)
│   │   │   ├── PublicAccessURL
│   │   │   └── PublicDataLicense (license governing public data usage)
│   │   ├── AuthenticatedAccess
│   │   │   ├── AuthenticationMethod (OAuth2, API key, certificate, etc.)
│   │   │   ├── AuthenticatedFields
│   │   │   ├── AuthenticationEndpoint
│   │   │   └── TokenLifetime (authentication token validity duration)
│   │   └── RestrictedAccess
│   │       ├── RoleBasedPermissions (expanded with RolePermission class)
│   │       ├── RestrictedFields
│   │       ├── AccessRequestProcess
│   │       └── AccessJustificationRequired (whether justification needed)
│   ├── SecuritySettings
│   │   ├── EncryptionMethod (for data in transit)
│   │   ├── DataClassification (public, internal, confidential, secret, personal)
│   │   ├── TransportSecurity (TLS, API signatures)
│   │   ├── AccessAttemptLogging (expanded AccessLogging class with retention)
│   │   └── IntegrityVerification (method for verifying data integrity)
│   └── ConsentManagement
│       ├── ConsentRequired (boolean)
│       ├── ConsentScope (purpose of consent)
│       ├── ConsentRevocationMethod
│       ├── ConsentDuration (validity period in days)
│       └── ConsentGranularity (field-level, record-level, etc.)
│
├── 2. DataCarrier
│   ├── CarrierType (QR code, RFID, NFC, URL, API, blockchain, IPFS, etc.)
│   ├── CarrierCapacity (data size limits in bytes)
│   ├── CarrierLocation (expanded class with location type, addresses, instructions)
│   ├── CarrierRedundancy (expanded class with redundancy levels, failover)
│   └── CarrierUpdateMechanism (expanded class with update methods, offline capability)
│
├── 3. DataLongevity
│   ├── RetentionPolicy
│   │   ├── MinimumRetentionPeriod (in days)
│   │   ├── MaximumRetentionPeriod (in days, 0 for indefinite)
│   │   ├── RetentionJustification (legal or business justification)
│   │   ├── RegulatoryRequirement (specific regulations)
│   │   └── DataCategories (categories covered by policy)
│   ├── AvailabilityCommitment
│   │   ├── GuaranteedAvailabilityPeriod (in days)
│   │   ├── ServiceLevelAgreement (uptime percentage)
│   │   ├── MaintenanceWindows (expanded class with schedule, duration, notice)
│   │   ├── AvailabilityZones (geographic or logical zones)
│   │   └── DisasterRecoveryTime (recovery time objective in hours)
│   ├── ArchivalStrategy
│   │   ├── ArchiveFormat (ZIP, TAR.GZ, Parquet, JSON-LD, RDF, WARC, BagIt)
│   │   ├── ArchiveLocation
│   │   ├── ArchiveAccessProcess
│   │   ├── ArchiveEncryption (encryption method for archives)
│   │   ├── ArchiveIntegrityCheck (verification method)
│   │   └── ArchiveRetrievalTime (expected retrieval time in hours)
│   └── DisposalPolicy
│       ├── DisposalCriteria (conditions triggering disposal)
│       ├── DisposalMethod (deletion, anonymization, pseudonymization, etc.)
│       ├── DisposalNotification (who to notify)
│       ├── DisposalVerification (method for verifying disposal)
│       └── LegalHoldCheck (check for legal holds before disposal)
│
├── 4. InteroperabilityConfiguration
│   ├── APISpecification
│   │   ├── APIEndpoints (list of available endpoints)
│   │   ├── APIVersion
│   │   ├── APIDocumentationURL
│   │   ├── RateLimits (expanded RateLimit class with types and scopes)
│   │   └── APIAuthentication (required authentication method)
│   ├── FormatDelivery
│   │   ├── FormatNegotiation (HTTP Accept, URL parameter, file extension)
│   │   ├── SupportedFormats (list of output formats)
│   │   ├── FormatConversionService (conversion endpoint)
│   │   ├── CompressionOptions (GZIP, Brotli, Deflate, ZIP)
│   │   └── DefaultFormat (when none specified)
│   ├── ProtocolSupport
│   │   ├── TransferProtocols (HTTPS, HTTP/2, HTTP/3, MQTT, CoAP, etc.)
│   │   ├── QueryProtocols (REST, GraphQL, SPARQL, SQL, OData, gRPC)
│   │   ├── SubscriptionProtocols (WebSocket, SSE, Webhooks, MQTT, AMQP)
│   │   └── ProtocolVersion (specific versions supported)
│   └── StandardsCompliance
│       ├── ComplianceStandards (ISO, W3C, GS1, etc.)
│       ├── ConformanceCertificates (URLs or identifiers)
│       ├── ValidationEndpoint (compliance validation service)
│       └── ComplianceLevel (level achieved)
│
└── 5. SystemIntegration
    ├── DataSourceSystems (expanded class per source system)
    │   ├── SourceSystemIdentifier (unique ID)
    │   ├── SourceSystemName (human-readable name)
    │   ├── SourceSystemType (ERP, MES, PLM, IoT, etc.)
    │   ├── SyncFrequency (in seconds)
    │   ├── DataMappings (expanded DataMapping class with transformations)
    │   ├── ConnectionEndpoint
    │   └── LastSyncTimestamp
    ├── ConsumerSystems (expanded class per consumer)
    │   ├── ConsumerIdentifier (unique ID)
    │   ├── ConsumerName (human-readable name)
    │   ├── ConsumerType (analytics, reporting, marketplace, etc.)
    │   ├── UsageRestrictions (list of restrictions)
    │   ├── UsageTracking (expanded class with access/modification tracking)
    │   └── AuthorizedScopes (data scopes allowed)
    └── OperationalMetrics (all expanded as detailed classes)
        ├── PerformanceMetrics (response time, throughput, latency P99, connections)
        ├── CapacityMetrics (storage usage/capacity, bandwidth, CPU utilization)
        └── ServiceMetrics (uptime %, error rate, SLA compliance, availability status)
```

### Workflow Sequence

#### **Step 1: Access Control Setup**
Define who can access what data and under what conditions:
- **AccessLevels**: Three-tier access model (public, authenticated, restricted)
- **SecuritySettings**: Encryption for transit, classification, transport security
- **ConsentManagement**: GDPR-compliant consent handling
- **AccessAttemptLogging**: Track failed access attempts and permission checks only

#### **Step 2: Data Carrier Configuration**
Specify how and where the DPP and DMP data is stored and accessed:
- **CarrierType**: Physical or digital storage mechanism
- **CarrierCapacity**: Size constraints and optimization
- **CarrierRedundancy**: Backup and failover strategies
- **UpdateMechanism**: How carrier data is refreshed

#### **Step 3: Longevity and Retention**
Establish lifecycle policies for data availability:
- **RetentionPolicy**: How long data must/can be kept
- **AvailabilityCommitment**: SLAs and uptime guarantees
- **ArchivalStrategy**: Long-term preservation approach
- **DisposalPolicy**: Policies for when and how to dispose (actual disposal events in custody model)

#### **Step 4: Interoperability Setup**
Enable cross-system data exchange:
- **APISpecification**: RESTful or other API definitions
- **FormatDelivery**: How to negotiate and deliver formats (not what formats exist)
- **ProtocolSupport**: Communication protocols
- **StandardsCompliance**: Adherence to industry standards

#### **Step 5: System Integration**
Connect with upstream and downstream systems:
- **DataSourceSystems**: Where data originates
- **ConsumerSystems**: Who uses the data
- **OperationalMetrics**: Monitor performance and availability (not audit trails)

### Data Properties

Each governance parameter serves a specific operational purpose. All fields are optional to allow flexibility across different deployment scenarios and regulatory contexts.

#### SQL Identifiers

Every data point includes a `sql_identifier` annotation following the pattern:

**Pattern**: `dpag_[category]_[specific_name]`

**Features:**
- **DP Access Governance Prefix**: All identifiers start with `dpag_`
- **Hierarchical Namespacing**: Category prefixes (`access_`, `carrier_`, `longevity_`, `interop_`, `system_`)
- **Database-Friendly**: Uses underscores, avoids special characters
- **Unique Across Model**: No duplicate identifiers
- **Operational Focus**: Names reflect governance and access concepts

**Examples:**
- `dpag_access_public_fields` - List of public data fields
- `dpag_carrier_type` - Data carrier mechanism
- `dpag_longevity_retention_period` - Data retention duration
- `dpag_interop_api_endpoints` - API access points
- `dpag_system_consumer_id` - Authorized consumer identifier

---

## Development Roadmap

| Step | Component | Sub-Components | Criticalities Identified | Solutions Planned | Status | Missing/TODO |
|------|-----------|---------------|-------------------------|-------------------|--------|--------------|
| **1** | **Access Control** | • AccessLevels<br>• SecuritySettings<br>• ConsentManagement<br>• AuditLogging | • Multi-level access complexity<br>• GDPR compliance<br>• Authentication standards<br>• Audit requirements<br>• Role management | • Three-tier access model<br>• Standard auth methods<br>• Consent tracking<br>• Audit trail design<br>• RBAC implementation | **COMPLETED** | • OAuth2 integration<br>• Zero-trust model<br>• Consent UI<br>• Audit analytics |
| **2** | **Data Carrier** | • CarrierType<br>• Capacity<br>• Location<br>• Redundancy<br>• Updates | • Diverse carrier types<br>• Size limitations<br>• Update synchronization<br>• Offline capability<br>• Carrier migration | • Flexible carrier model<br>• Capacity metadata<br>• Location tracking<br>• Redundancy strategy<br>• Update protocols | **COMPLETED** | • Carrier optimization<br>• Migration tools<br>• Offline sync<br>• Carrier monitoring |
| **3** | **Data Longevity** | • RetentionPolicy<br>• Availability<br>• Archival<br>• DisposalPolicy | • Regulatory requirements<br>• Storage costs<br>• Archive accessibility<br>• Disposal policies<br>• Legal holds | • Policy framework<br>• SLA definitions<br>• Archive standards<br>• Disposal policies<br>• Compliance tracking | **COMPLETED** | • Automated archival<br>• Cost optimization<br>• Legal hold system<br>• Policy automation |
| **4** | **Interoperability** | • APIs<br>• FormatDelivery<br>• Protocols<br>• Standards | • API versioning<br>• Format delivery<br>• Protocol diversity<br>• Standards evolution<br>• Rate limiting | • OpenAPI specs<br>• Content negotiation<br>• Protocol adapters<br>• Standards mapping<br>• Rate limit config | **COMPLETED** | • API gateway<br>• Auto-conversion<br>• Protocol bridge<br>• Compliance testing |
| **5** | **System Integration** | • Sources<br>• Consumers<br>• OperationalMetrics | • System discovery<br>• Data synchronization<br>• Usage tracking<br>• Performance monitoring<br>• Service monitoring | • System registry<br>• Sync protocols<br>• Operational metrics<br>• Monitoring setup<br>• Performance tracking | **COMPLETED** | • Auto-discovery<br>• Real-time sync<br>• Ops dashboard<br>• Alert system |

### Integration Opportunities

- **W3C ODRL** - Open Digital Rights Language for access policies
- **XACML** - eXtensible Access Control Markup Language
- **OAuth 2.0 / OpenID Connect** - Authentication and authorization
- **W3C VC** - Verifiable Credentials for access tokens
- **PREMIS** - Preservation metadata for longevity
- **OpenAPI** - API specification standard
- **CloudEvents** - Event data specification
- **LDP** - Linked Data Platform for data access
- **DCAT-AP** - Data Catalog Application Profile for metadata
- **ISO 27001** - Information security management

---

## Publishing

Release artifacts for each version (`schema.json`, `shacl.ttl`, `model.owl`)  
are served directly from this URL:
```
https://ce-rise-models.codeberg.page/dp-access-and-governance/
```


---

## Accessing Previous Releases

If you want to view the files published for version `v1.2.0`, open:

```
https://codeberg.org/CE-RISE-models/dp-access-and-governance/src/tag/pages-v1.2.0/generated/
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
