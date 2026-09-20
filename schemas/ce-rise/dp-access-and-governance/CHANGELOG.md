# Changelog

All notable changes to the CE-RISE DPP Access and Governance Data Model will be documented in this file.

## [0.0.3] - 2026-01-30

### Added
- Support for Digital Material Passport alongside Digital Product Passport.

## [0.0.2] - 2025-12-15

### Added
- Missing references from Beta release of CE-RISE the data model.

## [0.0.1] - 2025-12-11

### Added
- Initial project structure from CE-RISE template
- Complete five-stage DPP Access and Governance data model implementation in LinkML
- **Stage 1: Access Control** - Three-tier access model with public/authenticated/restricted levels, security settings, GDPR-compliant consent management
- **Stage 2: Data Carrier** - Support for multiple carrier types (QR, RFID, NFC, blockchain, IPFS), redundancy configuration, update mechanisms
- **Stage 3: Data Longevity** - Retention policies, SLA commitments, archival strategies, disposal policies with legal hold support
- **Stage 4: Interoperability** - API specifications, format negotiation, protocol support (REST, GraphQL, MQTT, WebSocket), standards compliance
- **Stage 5: System Integration** - Source system connectors, consumer management, operational metrics (performance, capacity, service)
- Comprehensive ontology integration using 12+ standards (DCAT, PROV-O, DPV, ODRL, ACL, Schema.org, DC Terms, etc.)
- Unique SQL identifiers for all attributes following `dpag_` prefix pattern
- OWL filler annotations for proper RDF/OWL generation
- 31 classes across 5 stages with full attribute coverage
- 20 enumerations covering authentication methods, protocols, formats, and system types
- Successfully generates JSON Schema (1732 lines), SHACL (1081 lines), and OWL/TTL (3185 lines)
- Complete README documentation with aligned hierarchy and development roadmap
- Artifacts built and deployed to pages
