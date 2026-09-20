# CE-RISE Compliance and Standards

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.17938293.svg)](https://doi.org/10.5281/zenodo.17938293) [![Schemas](https://img.shields.io/badge/Schema%20Files-LinkML%2C%20JSON%2C%20SHACL%2C%20OWL-32CD32)](https://ce-rise-models.codeberg.page/compliance-and-standards/)

Repository for the data model covering regulatory compliance, standards, and conformity-related information for products and materials, including applicable regulations and standards, commitments, documentary evidence (e.g., DoC, certificates, CE marking), process evidence, and structured regulatory information sheets with safety warnings, legally required safe-use instructions, EMC statements, EU Responsible Person details, and market- or regulation-specific identifiers.

**Applicability**: This model supports both **Digital Product Passports (DPP)** and **Digital Material Passports (DMP)**, providing a flexible framework for compliance and regulatory requirements regardless of whether the assessed entity is a finished product, raw material, material batch, or commodity.


---

## Data Model Structure

The Compliance and Standards data model provides a comprehensive framework for capturing all regulatory, certification, and normative requirements for products and materials. It enables tracking of legal compliance across different markets, documentation of conformity assessments, management of certifications and declarations, and structured storage of legally required information including safety instructions, responsible person details, and market-specific regulatory identifiers.

### Key Design Principles

1. **Multi-Jurisdictional Support**: Captures compliance requirements across different regulatory regions (EU, US, Asia-Pacific, etc.)
2. **Evidence Traceability**: Complete documentation trail from commitments to certificates and declarations
3. **Regulatory Completeness**: Structured storage of all legally required information and disclosures
4. **Standards Alignment**: Direct references to applicable standards and regulations with version control
5. **Market-Specific Flexibility**: Supports region-specific requirements and identifiers

### Core Hierarchy

```
ComplianceAndStandards (root - for products and materials)
├── 1. EntityCommitments
│   └── Commitment (repeatable)
│       ├── CommitmentIdentifier
│       ├── CommitmentStatement
│       ├── CommitmentDescription
│       ├── CommitmentCategories (multivalued)
│       │   ├── Regulatory
│       │   ├── Voluntary
│       │   ├── Contractual
│       │   ├── IndustryStandard
│       │   ├── CustomerRequirement
│       │   ├── Environmental
│       │   ├── Social
│       │   └── Quality
│       ├── ComplianceStatus (multivalued by jurisdiction)
│       │   ├── Status (mandatory/voluntary/recommended/optional)
│       │   ├── Jurisdiction
│       │   ├── EffectiveDate
│       │   ├── ExpiryDate
│       │   ├── StatusNotes
│       │   └── IssuingAuthority
│       ├── ValidityPeriod
│       │   ├── StartDate
│       │   └── EndDate
│       ├── StakeholderScope
│       │   ├── ApplicableMarkets
│       │   ├── CustomerSegments
│       │   └── EntityVariants (product models, material grades, batches)
│       └── EvidenceReferences
│           ├── SupportingDocuments
│           ├── CertificationLinks
│           ├── AuditRecords
│           └── TestReports
├── 2. ApplicableRegulationStandards (Products and Materials)
│   └── RequirementEntry (repeatable)
│       ├── RequirementIdentifier
│       ├── RequirementType (Regulation/Standard/Specification)
│       ├── Title
│       ├── IssuingAuthority
│       ├── Version
│       ├── PublicationDate
│       ├── ApplicabilityStatus (multivalued by jurisdiction)
│       │   ├── Jurisdiction
│       │   ├── Status (mandatory/voluntary/recommended/superseded)
│       │   ├── EffectiveDate
│       │   ├── EndDate
│       │   ├── TransitionPeriod
│       │   ├── EnforcementLevel
│       │   └── Derogations
│       ├── SuccessorReference (if superseded)
│       ├── CommitmentLinks (references to related commitments)
│       ├── ComplianceEvidenceLinks (references to supporting evidence)
│       ├── RequirementScope
│       │   ├── EntityCategories (product categories, material types)
│       │   ├── IndustrySectors
│       │   ├── TechnicalDomains
│       │   ├── Exclusions
│       │   └── SpecialConditions
│       ├── HarmonizedStandards
│       └── AmendmentHistory
├── 3. EntityEvidence
│   └── EvidenceDocument (repeatable)
│       ├── EvidenceType (DoC/Certificate/TestReport/MaterialCertificate/SDS/GradeCertificate/ChemicalAnalysis/OriginCertificate/MaterialPropertiesTest/Marking/Other)
│       ├── DocumentIdentifier
│       ├── DocumentTitle
│       ├── IssueDate
│       ├── ValidityPeriod
│       │   ├── ValidFrom
│       │   └── ValidUntil
│       ├── IssuingAuthority
│       │   ├── AuthorityName
│       │   ├── AuthorityType
│       │   ├── AccreditationDetails
│       │   ├── AuthorityIdentifier
│       │   ├── AuthorityCountry
│       │   └── NotifiedBodyNumber
│       ├── ScopeOfEvidence
│       │   ├── EntitiesCovered (products, materials, batches, families)
│       │   ├── BatchLotIdentifiers (for materials tracked at batch level)
│       │   ├── StandardsVersions (with specific versions)
│       │   ├── RequirementReferences
│       │   ├── TechnicalSpecifications
│       │   ├── ModulesProcedures
│       │   └── Exclusions
│       ├── CommitmentSupport (which commitments this proves)
│       ├── ConformityAssessmentProcedure
│       ├── DocumentLanguages
│       ├── DigitalSignature
│       │   ├── SignatureType
│       │   ├── SignatureValue
│       │   ├── SignatureDate
│       │   ├── Signatory
│       │   └── CertificateReference
│       └── DocumentAccess
│           ├── DocumentURL
│           ├── AccessRestrictions
│           ├── RetentionPeriod
│           ├── DocumentFormat
│           ├── Checksum
│           └── StorageLocation
├── 4. ProcessEvidence
│   └── ManagementSystem (repeatable)
│       ├── SystemType (QMS/EMS/OHS/ISMS/ENERGY/CSR/FSMS/BCM)
│       ├── StandardReference
│       │   ├── StandardIdentifier
│       │   ├── StandardVersion
│       │   └── StandardYear
│       ├── CertificationDetails
│       │   ├── CertificationStatus
│       │   ├── CertificationBody
│       │   ├── CertificateNumber
│       │   ├── ValidityPeriod
│       │   └── AccreditationDetails
│       ├── AuditHistory
│       │   ├── AuditDate
│       │   ├── AuditType
│       │   ├── Findings
│       │   ├── CorrectiveActions
│       │   ├── AuditResult
│       │   └── Auditor
│       ├── PerformanceMetrics
│       │   ├── KPIs (name/value/unit/period)
│       │   └── ImprovementTargets (description/value/date)
│       ├── CommitmentAlignment (links to related commitments)
│       ├── EvidenceDocuments (references to certificates/reports)
│       └── ScopeDescription
└── 5. RegulatoryInformation
    ├── SafetyInformation
    │   └── SafetyItem (repeatable)
    │       ├── ItemType (Warning/Instruction/Prohibition/Caution/Danger/Notice)
    │       ├── Content (text)
    │       ├── SeverityLevel (if applicable)
    │       ├── ApplicableJurisdictions
    │       ├── Languages
    │       └── PictogramReference
    ├── UsageInstructions
    │   ├── IntendedUse
    │   ├── OperatingGuidelines
    │   ├── MaintenanceRequirements
    │   ├── DisposalInstructions
    │   ├── EmergencyProcedures
    │   └── StorageConditions
    ├── ComplianceStatements
    │   └── Statement (repeatable)
    │       ├── StatementType (EMC/Safety/Environmental/Radio/Chemical/Energy/Privacy/Accessibility)
    │       ├── StatementContent
    │       ├── ApplicableStandards
    │       ├── TestReferences
    │       └── ValidForJurisdictions
    ├── ResponsibleParties
    │   └── ResponsibleParty (repeatable)
    │       ├── Jurisdiction
    │       ├── PartyRole (Manufacturer/Importer/AuthorizedRep/Distributor)
    │       ├── LegalEntityName
    │       ├── RegisteredAddress
    │       ├── ContactDetails
    │       └── RegistrationNumbers (EORI/FDA/Other)
    └── RegulatoryIdentifiers
        └── Identifier (repeatable key-value pairs)
            ├── IdentifierType
            ├── IdentifierValue
            ├── IssuingAuthority
            └── ValidityScope
```

### Workflow Sequence

#### **Step 1: EntityCommitments**
Flexible framework for all types of commitments for products or materials:
- **Commitment Structure**: Generic, repeatable commitment container
- **Multi-Category Support**: Each commitment can be tagged as regulatory, voluntary, contractual, or multiple categories simultaneously
- **Jurisdictional Flexibility**: Same commitment can have different statuses in different markets
- **Temporal Evolution**: Tracks how commitment status changes over time (voluntary becoming regulatory)
- **Stakeholder Scope**: Defines which markets, customers, or entity variants (product models, material grades) the commitment applies to
- **Evidence Linking**: Direct references to supporting documentation and certifications

#### **Step 2: ApplicableRegulationStandards**
Flexible framework for all types of requirements with jurisdictional awareness:
- **RequirementEntry**: Generic, repeatable structure for any regulation, standard, or specification
- **Multi-Jurisdictional Status**: Same requirement can have different status across markets
- **Version Tracking**: Handles superseded standards with successor references
- **Commitment Integration**: Links requirements to related commitments and evidence
- **Evolution Support**: Tracks effective dates and end dates for changing requirements

#### **Step 3: EntityEvidence**
Unified evidence framework supporting multiple document types for products and materials:
- **EvidenceDocument**: Generic structure for any type of compliance evidence including material-specific types (material certificates, safety data sheets, grade certificates, chemical analysis, origin certificates, material property tests)
- **Version-Aware**: Links to specific versions of standards/regulations
- **Commitment Linkage**: Explicitly references which commitments the evidence supports
- **Digital Trust**: Includes digital signature and document retention information
- **Flexible Scope**: Can cover products, materials, batches/lots, processes, or organizational compliance
- **Batch/Lot Tracking**: Supports batch or lot-level compliance tracking for materials

#### **Step 4: ProcessEvidence**
Integrated management systems evidence with commitment alignment:
- **ManagementSystem**: Flexible structure for any management system type
- **Audit Trail**: Complete audit history with findings and corrective actions
- **Performance Tracking**: KPIs and improvement targets
- **Commitment Links**: Shows how management systems support commitments for products or materials
- **Evidence Integration**: References to supporting certificates and documents

#### **Step 5: RegulatoryInformation**
Market-agnostic regulatory information framework:
- **SafetyInformation**: Flexible, repeatable safety items for any jurisdiction
- **ComplianceStatements**: Generic statements adaptable to different regulatory requirements
- **ResponsibleParties**: Jurisdiction-specific responsible party information (not just EU)
- **RegulatoryIdentifiers**: Flexible key-value pairs for any market-specific identifier
- **Global Applicability**: Works for EU, US, Asia, and emerging markets without restructuring

### Data Properties

Each class has a corresponding value property (e.g., `regulation_name_value`, `certificate_number_value`) that holds the actual data. All value properties are string type except where specified otherwise (dates, booleans, numbers).

#### SQL Identifiers

Every data point in the model includes a `sql_identifier` annotation that serves as a unique, machine-friendly database identifier. These identifiers follow a structured namespace pattern to ensure uniqueness across the entire data model:

**Pattern**: `comp_[category]_[specific_name]`

**Features:**
- **Compliance Prefix**: All identifiers start with `comp_` to clearly identify them as belonging to the Compliance and Standards data model
- **Hierarchical Namespacing**: Uses category prefixes (`commit_`, `reg_`, `evid_`, `proc_`, `info_`) to provide context and prevent naming conflicts
- **Database-Friendly**: Uses underscores and avoids special characters for SQL compatibility
- **Unique Across Model**: No duplicate identifiers, even when similar concepts appear in different parts of the hierarchy
- **Reasonable Length**: Abbreviated but meaningful names that balance clarity with practical database usage

**Examples:**
- `comp_commit_regulatory_type` - Type of regulatory commitment
- `comp_reg_standard_identifier` - Standard identification number
- `comp_evid_doc_id` - Evidence document identifier
- `comp_mgmt_type` - Management system type
- `comp_party_name` - Responsible party name

This identifier system enables seamless integration with databases and ensures clear data model composition when combining with other CE-RISE data models.

---

## Development Roadmap

| Step | Component | Criticalities Identified | Solutions Implemented | Status | Missing/TODO |
|------|-----------|-------------------------|----------------------|--------|--------------|
| **1** | **EntityCommitments** | • Evolving regulatory landscape<br>• Multi-jurisdictional complexity<br>• Overlapping commitment categories<br>• Temporal status changes | • Flexible tagging system<br>• Multi-category support<br>• Jurisdiction-specific status<br>• Timeline tracking<br>• Generic commitment structure | **COMPLETED** | • Automated status updates<br>• Regulatory change monitoring<br>• Cross-jurisdiction mapping |
| **2** | **ApplicableRegulationStandards** | • Evolving requirements<br>• Multi-jurisdiction complexity<br>• Standards supersession<br>• Version tracking | • Flexible requirement structure<br>• Jurisdiction-specific status<br>• Successor references<br>• Commitment integration | **COMPLETED** | • Regulatory change monitoring<br>• Automated supersession tracking<br>• Standards database APIs |
| **3** | **EntityEvidence** | • Evidence-commitment linking<br>• Version specificity<br>• Digital authenticity<br>• Document lifecycle | • Generic evidence framework<br>• Commitment references<br>• Version-aware scope<br>• Digital signature support | **COMPLETED** | • Automated commitment matching<br>• Blockchain anchoring<br>• Retention management |
| **4** | **ProcessEvidence** | • System-commitment alignment<br>• Audit integration<br>• Performance tracking<br>• Multi-standard coverage | • Flexible system types<br>• Commitment linkage<br>• Audit trail capture<br>• KPI framework | **COMPLETED** | • Management system APIs<br>• Automated KPI collection<br>• Audit scheduling |
| **5** | **RegulatoryInformation** | • Global market support<br>• Flexible identifiers<br>• Multi-party roles<br>• Evolving requirements | • Market-agnostic structure<br>• Repeatable components<br>• Jurisdiction-aware parties<br>• Key-value identifiers | **COMPLETED** | • Market requirement APIs<br>• Translation management<br>• Regulatory updates |

### Integration Opportunities

- **Regulatory Databases**: Integration with EU NANDO, FDA databases, standards bodies repositories
- **Certification Bodies**: APIs with TÜV, SGS, Bureau Veritas, Intertek systems
- **Standards Organizations**: ISO, CEN, CENELEC, IEC online standards access
- **Legal Platforms**: Regulatory intelligence services, compliance monitoring tools
- **Document Management**: Digital signature platforms, blockchain notarization services
- **Translation Services**: Multi-language compliance documentation systems
- **Market Surveillance**: RAPEX, CPSC, product recall databases
- **CE-RISE Utility Models**: Compliance commitments, status decisions, requirement entries, evidence documents, certifications, audits, KPIs, and compliance statements can optionally reference `uncertainty-quantification`, `metrological-traceability`, and `data-quality-framework` records where relevant


---

## Publishing

Release artifacts for each version (`schema.json`, `shacl.ttl`, `model.owl`)  
are served directly from this URL:
```
https://ce-rise-models.codeberg.page/compliance-and-standards/
```


---

## Accessing Previous Releases

If you want to view the files published for version `v1.2.0`, open:

```
https://codeberg.org/CE-RISE-models/compliance-and-standards/src/tag/pages-v1.2.0/generated/
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
