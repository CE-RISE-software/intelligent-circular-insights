# CE-RISE DP Record Custody

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.17900533.svg)](https://doi.org/10.5281/zenodo.17900533) [![Schemas](https://img.shields.io/badge/Schema%20Files-LinkML%2C%20JSON%2C%20SHACL%2C%20OWL-32CD32)](https://ce-rise-models.codeberg.page/dp-record-custody/)

Repository for the CE-RISE DP Record Custody data model, part of the DP Metadata Layer for Digital Product Passports (DPP) and Digital Material Passports (DMP). This model represents the complete chain of custody and governance history of the DPP/DMP record itself, tracking who did what when. It captures custody events (creation, update, transfer, archival), identifies custodians, records authorized transfers, includes cryptographic integrity evidence, and maintains comprehensive governance records. The model ensures forensic-level auditability, accountability, and secure lifecycle governance of the DPP/DMP as information objects, complementing the structural metadata (dp-record-metadata) and operational governance (dp-access-and-governance). All five stages are now fully implemented with industry-standard authentication (OIDC, OAuth2, SAML, DIDs) and comprehensive ontology support.


---

## Data Model Structure
This data model provides a comprehensive audit trail of who did what to DPP/DMP records and when, capturing the complete chain of custody from creation through archival or disposal. It ensures forensic-level traceability of all changes, transfers, and governance actions applied to DPP/DMP data throughout its lifecycle.

### Key Design Principles
1. **Event-based tracking**: Every significant action is captured as a timestamped event
2. **Custodian identification**: Clear identification of all parties who handle the data
3. **Integrity preservation**: Cryptographic evidence for all custody changes
4. **Transfer authorization**: Explicit recording of authority for custody transfers
5. **Immutable history**: Append-only event log that cannot be altered
6. **Compliance-ready**: Supports regulatory requirements for data governance auditing


### Core Hierarchy

```
DPRecordCustody (root)
├── 1. CustodyEvents (multivalued, chronological)
│   ├── EventMetadata
│   │   ├── EventID (unique identifier)
│   │   ├── EventType (creation, update, transfer, validation, archival, disposal)
│   │   ├── EventTimestamp (ISO 8601)
│   │   ├── EventDescription
│   │   └── EventJustification (reason for the event)
│   ├── EventActor
│   │   ├── ActorID (OpenID sub claim, OIDC identifier)
│   │   ├── ActorName (from OIDC name/preferred_username claim)
│   │   ├── ActorEmail (from OIDC email claim)
│   │   ├── ActorRole (creator, editor, validator, custodian, auditor)
│   │   ├── ActorOrganization (from OIDC org claim or SAML assertion)
│   │   ├── ActorAuthentication (OAuth2, OIDC, SAML, X.509)
│   │   └── ActorSessionID (JWT jti or session identifier)
│   └── EventIntegrity
│       ├── PreviousHash (hash of previous event for chain integrity)
│       ├── CurrentHash (hash of current event data)
│       ├── HashAlgorithm (SHA-256, SHA-3, etc.)
│       ├── DigitalSignature (optional)
│       └── SignatureAlgorithm (if signed)
│   └── RecordTransformationDetails (optional)
│       ├── Inputs (source passport record IDs)
│       ├── Outputs (result passport record IDs)
│       ├── OperationType (derived_from, aggregated_from, merged_from, split_from, reconciled_with, enriched_with, versioned_from, distilled_from)
│       ├── OperationMethod (rule_based, manual_curation, automated_pipeline, external_source)
│       └── OperationRef (optional workflow/process reference)
│
├── 2. CustodianHistory (multivalued)
│   ├── CustodianIdentity
│   │   ├── CustodianID (DID, OIDC sub, or LEI for organizations)
│   │   ├── CustodianName
│   │   ├── CustodianType (individual, organization, system)
│   │   ├── CustodianContact (vCard or Schema.org ContactPoint)
│   │   ├── CustodianJurisdiction (ISO 3166 country code)
│   │   └── CustodianCertifications (ISO 27001, SOC2, etc.)
│   ├── CustodyPeriod
│   │   ├── CustodyStartTime
│   │   ├── CustodyEndTime
│   │   └── CustodyDuration (calculated)
│   └── CustodyResponsibilities
│       ├── DataStewardship (what they were responsible for)
│       ├── AccessGranted (permissions during custody)
│       └── ComplianceObligations (regulatory requirements)
│
├── 3. TransferRecords (multivalued)
│   ├── TransferAuthorization
│   │   ├── AuthorizationID (UUID or system identifier)
│   │   ├── AuthorizingParty (DID or OIDC identifier)
│   │   ├── AuthorizationToken (OAuth2 token or signed JWT)
│   │   ├── AuthorizationDocument (URI reference)
│   │   ├── LegalBasis (GDPR Article 6/9, contract, consent)
│   │   └── TransferConditions (smart contract or policy rules)
│   ├── TransferDetails
│   │   ├── TransferID
│   │   ├── TransferTimestamp
│   │   ├── FromCustodian
│   │   ├── ToCustodian
│   │   └── TransferMethod (API, manual, migration, etc.)
│   └── TransferVerification
│       ├── VerificationMethod
│       ├── VerificationTimestamp
│       ├── VerificationResult
│       └── VerificationEvidence
│
├── 4. IntegrityEvidence
│   ├── DataFingerprint
│   │   ├── FingerprintValue
│   │   ├── FingerprintAlgorithm
│   │   ├── FingerprintScope (full record, specific fields)
│   │   └── FingerprintTimestamp
│   ├── BlockchainAnchoring (optional)
│   │   ├── BlockchainNetwork (Ethereum, Polygon, Hyperledger)
│   │   ├── TransactionHash
│   │   ├── BlockNumber
│   │   ├── SmartContractAddress
│   │   └── DIDDocument (W3C DID for blockchain identity)
│   └── ExternalAttestation
│       ├── AttestationProvider (TSA, notary service, CA)
│       ├── AttestationID
│       ├── AttestationTimestamp (RFC 3161 timestamp)
│       ├── AttestationProof (X.509 cert, VC, or signed statement)
│       └── AttestationStandard (eIDAS, ETSI, RFC 3161)
│
└── 5. GovernanceActions
    ├── ValidationRecords
    │   ├── ValidationID
    │   ├── ValidationType (schema, business rules, regulatory)
    │   ├── ValidationTimestamp
    │   ├── Validator (person/system)
    │   └── ValidationOutcome
    ├── AuditTrail
    │   ├── AuditID
    │   ├── AuditType (internal, external, regulatory)
    │   ├── AuditTimestamp
    │   ├── Auditor
    │   └── AuditFindings
    └── DisposalRecord (when applicable)
        ├── DisposalAuthorization
        ├── DisposalTimestamp
        ├── DisposalMethod
        ├── DisposalVerification
        └── RetentionException (if any data retained)

```

### Workflow Sequence

#### **Step 1: Custody Event Capture**
Record every significant action on the DPP/DMP record:
- **EventMetadata**: Unique ID, type, timestamp, description, justification
- **EventActor**: Who performed the action with OIDC/OAuth2 authentication, JWT session tracking
- **EventIntegrity**: Cryptographic chain linking with hashes and optional signatures
- **RecordTransformationDetails**: Optional data-level lineage details linking related passport records

#### **Step 2: Custodian Management**
Track all parties who have had custody of the data:
- **CustodianIdentity**: Full identification using DIDs, OIDC, or LEI (Legal Entity Identifier)
- **CustodyPeriod**: When they had custody with precise timestamps
- **CustodyResponsibilities**: What they were authorized to do and compliance requirements

#### **Step 3: Transfer Documentation**
Record all authorized transfers between custodians:
- **TransferAuthorization**: Legal basis and conditions for transfer
- **TransferDetails**: Who, when, and how the transfer occurred
- **TransferVerification**: Proof that transfer was completed successfully

#### **Step 4: Integrity Preservation**
Maintain cryptographic evidence of data integrity:
- **DataFingerprint**: Hashes of the data at specific points in time
- **BlockchainAnchoring**: Optional immutable ledger recording
- **ExternalAttestation**: Third-party verification services

#### **Step 5: Governance Recording**
Document all governance actions taken on the data:
- **ValidationRecords**: Schema and business rule validations
- **AuditTrail**: Internal and external audit activities
- **DisposalRecord**: When and how data was disposed of (if applicable)

### Data Properties

Each custody element serves a specific audit and governance purpose. Most fields are required to ensure complete forensic traceability, with optional fields for enhanced governance scenarios.

#### SQL Identifiers

Every data point includes a `sql_identifier` annotation following the pattern:

**Pattern**: `dprc_[category]_[specific_name]`

**Features:**
- **DP Record Custody Prefix**: All identifiers start with `dprc_`
- **Hierarchical Namespacing**: Category prefixes (`event_`, `custodian_`, `transfer_`, `integrity_`, `governance_`)
- **Database-Friendly**: Uses underscores, avoids special characters
- **Unique Across Model**: No duplicate identifiers
- **Forensic Focus**: Names reflect audit and custody concepts

**Examples:**
- `dprc_event_id` - Unique event identifier
- `dprc_event_timestamp` - When the event occurred
- `dprc_custodian_id` - Custodian identifier
- `dprc_transfer_authorization` - Transfer authorization reference
- `dprc_integrity_hash` - Integrity hash value
- `dprc_governance_audit_id` - Audit record identifier

---

## Development Roadmap

| Step | Component | Sub-Components | Criticalities Identified | Solutions Planned | Status | Missing/TODO |
|------|-----------|---------------|-------------------------|-------------------|--------|--------------|
| **1** | **Custody Events** | • EventMetadata<br>• EventActor<br>• EventIntegrity | • Event ordering and sequencing<br>• Actor authentication verification<br>• Hash chain integrity<br>• Event type standardization<br>• Timestamp precision | • Chronological event list<br>• Authentication methods<br>• SHA-256/SHA-3 hashing<br>• Event type enumeration<br>• ISO 8601 timestamps | **COMPLETED** | • Event replay protection<br>• Multi-signature support<br>• Event correlation<br>• Batch event processing |
| **2** | **Custodian History** | • CustodianIdentity<br>• CustodyPeriod<br>• CustodyResponsibilities | • Custodian verification<br>• Overlapping custody periods<br>• Responsibility mapping<br>• Jurisdiction handling<br>• Contact management | • Identity verification<br>• Period validation<br>• RBAC integration<br>• Legal jurisdiction<br>• Contact schemas | **COMPLETED** | • Custodian registry<br>• Delegation chains<br>• Backup custodians<br>• Emergency access |
| **3** | **Transfer Records** | • TransferAuthorization<br>• TransferDetails<br>• TransferVerification | • Authorization validation<br>• Transfer atomicity<br>• Cross-system transfers<br>• Legal compliance<br>• Verification methods | • Auth document refs<br>• Atomic transfers<br>• Transfer protocols<br>• Legal basis tracking<br>• Verification proofs | **COMPLETED** | • Smart contracts<br>• Escrow mechanisms<br>• Rollback capability<br>• Transfer templates |
| **4** | **Integrity Evidence** | • DataFingerprint<br>• BlockchainAnchoring<br>• ExternalAttestation | • Hash algorithm selection<br>• Blockchain integration<br>• Attestation providers<br>• Evidence preservation<br>• Scope definition | • Multiple hash algos<br>• Blockchain adapters<br>• Attestation APIs<br>• Evidence storage<br>• Granular scoping | **COMPLETED** | • Quantum-safe hashing<br>• Multi-chain support<br>• Notarization<br>• Evidence archival |
| **5** | **Governance Actions** | • ValidationRecords<br>• AuditTrail<br>• DisposalRecord | • Validation rules<br>• Audit completeness<br>• Disposal verification<br>• Retention policies<br>• Regulatory compliance | • Validation framework<br>• Audit standards<br>• Disposal workflows<br>• Retention rules<br>• Compliance tracking | **COMPLETED** | • Auto-validation<br>• Audit analytics<br>• Disposal automation<br>• Hold management |

### Integration Opportunities

#### Authentication & Identity Standards
- **OpenID Connect (OIDC)** - Industry standard for user authentication
- **OAuth 2.0** - Authorization framework for API access
- **W3C DIDs** - Decentralized Identifiers for self-sovereign identity
- **SAML 2.0** - Enterprise single sign-on
- **WebAuthn/FIDO2** - Passwordless authentication
- **LEI (ISO 17442)** - Legal Entity Identifiers for organizations
- **X.509 Certificates** - PKI-based authentication

#### Provenance & Audit Ontologies
- **W3C PROV-O** - Provenance Ontology for tracking entity derivation
- **PREMIS** - Preservation metadata for digital objects
- **Dublin Core** - Metadata terms for resource description
- **FOAF** - Friend of a Friend for agent identification
- **vCard** - Contact information standard
- **Schema.org** - Structured data vocabulary

#### Compliance & Standards
- **ISO 27037** - Digital evidence chain of custody
- **ISO 15489** - Records management standards
- **RFC 3161** - Time-stamp protocol
- **eIDAS** - EU electronic identification and trust services
- **GDPR Articles** - Legal basis references
- **Verifiable Credentials** - W3C standard for tamper-proof claims

#### Blockchain & Integrity
- **EthOn** - Ethereum Ontology
- **BLONDiE** - Blockchain Ontology with Dynamic Extensibility
- **EPCIS** - Events for supply chain visibility
- **Time Ontology** - Temporal concepts and relations



---

## Publishing

Release artifacts for each version (`schema.json`, `shacl.ttl`, `model.owl`)  
are served directly from this URL:
```
https://ce-rise-models.codeberg.page/dp-record-custody/
```


---

## Accessing Previous Releases

If you want to view the files published for version `v1.2.0`, open:

```
https://codeberg.org/CE-RISE-models/dp-record-custody/src/tag/pages-v1.2.0/generated/
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
