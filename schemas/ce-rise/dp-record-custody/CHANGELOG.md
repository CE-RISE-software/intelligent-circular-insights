# Changelog

All notable changes to the CE-RISE DP Record Custody Data Model will be documented in this file.

## [0.0.3] - 2026-01-30

### Added
- Expand scope to include Digital Material Passports (DMPs) alongside Digital Product Passports (DPPs).
- Add data-level passport record transformation details to custody events (inputs, outputs, operation type/method, operation reference).

## [0.0.2] - 2025-12-15

### Added
- Missing references in annotatiosn from Beta release of data model.

## [0.0.1] - 2025-12-11

### Added
- Initial project structure from CE-RISE template
- Complete five-stage DPP Record Custody data model implementation in LinkML
- **Stage 1: Custody Events** - Comprehensive event tracking with OIDC/OAuth2 authentication, cryptographic hash chains, digital signatures
- **Stage 2: Custodian History** - Full custodian identification using DIDs/LEI, custody periods, responsibilities with ODRL policies
- **Stage 3: Transfer Records** - Authorized transfers with legal basis tracking, verification methods, smart contract support
- **Stage 4: Integrity Evidence** - Data fingerprinting, blockchain anchoring (Ethereum, Polygon, Hyperledger), external attestation
- **Stage 5: Governance Actions** - Validation records, audit trail, disposal tracking with legal hold checks
- Industry-standard authentication integration (OpenID Connect, OAuth 2.0, SAML, X.509, DIDs, WebAuthn)
- Comprehensive ontology integration using PROV-O, Security Vocabulary, ODRL, DPV, Verifiable Credentials
- Unique SQL identifiers for all attributes following `dprc_` prefix pattern
- OWL filler annotations for proper RDF/OWL generation
- 29 classes across 5 stages providing complete custody chain tracking
- 29 enumerations covering event types, authentication methods, hash algorithms, blockchain networks
- Successfully generates JSON Schema (1275 lines), SHACL (863 lines), and OWL/TTL (2574 lines)
- Complete README documentation with forensic-level audit trail capabilities
- Artifacts built and deployed to pages
