# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2026 CE-RISE consortium
"""Obligation rules, as data.

Each rule says: given these structural facts about a product, this obligation
follows. They are the ``hasComponent(p,c) ∧ type(c,t) ∧ governedBy(t,s) ⇒
requiresCompliance(c,s)`` pattern from the paper, written as SPARQL CONSTRUCT so
that every variable in the head is bound in the body and evaluation terminates.

Held as a frozen catalogue rather than built inline in an if/elif chain, because
a rule set you can enumerate is one you can report coverage for, disable
individually for an ablation, and show to a domain expert for review.
"""

from __future__ import annotations

from dataclasses import dataclass

RDF_NS = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"


@dataclass(frozen=True)
class Rule:
    """One obligation rule: an id, a human reading, and the CONSTRUCT that fires it."""

    id: str
    description: str
    construct: str

    def sparql(self, namespace: str) -> str:
        return f"PREFIX ex: <{namespace}>\nPREFIX rdf: <{RDF_NS}>\n{self.construct}"


BATTERY_RULES: tuple[Rule, ...] = (
    Rule(
        "bat_requires_battery_safety",
        "A product containing a Battery must comply with the battery safety standard.",
        """CONSTRUCT { ?p ex:requiresCompliance ex:BatterySafetyStandard. }
           WHERE { ?p ex:hasComponent ?c . ?c rdf:type ex:Battery . }""",
    ),
    Rule(
        "bat_requires_battery_step",
        "A product containing a Battery needs a battery test step, unless it already has one.",
        """CONSTRUCT { ?p ex:requiresStep ex:BatteryTestStep. }
           WHERE { ?p ex:hasComponent ?c . ?c rdf:type ex:Battery .
                   FILTER NOT EXISTS { ?p ex:hasStep ex:BatteryTestStep } }""",
    ),
    Rule(
        "bat_requires_wireless_compliance",
        "A product containing a WirelessModule must meet wireless compliance.",
        """CONSTRUCT { ?p ex:requiresCompliance ex:WirelessComplianceStandard. }
           WHERE { ?p ex:hasComponent ?c . ?c rdf:type ex:WirelessModule . }""",
    ),
    Rule(
        "bat_requires_wireless_step",
        "A product containing a WirelessModule needs a wireless test step, unless present.",
        """CONSTRUCT { ?p ex:requiresStep ex:WirelessTestStep. }
           WHERE { ?p ex:hasComponent ?c . ?c rdf:type ex:WirelessModule .
                   FILTER NOT EXISTS { ?p ex:hasStep ex:WirelessTestStep } }""",
    ),
    Rule(
        "bat_lead_implies_rohs",
        "Any component using lead brings the product under RoHS.",
        """CONSTRUCT { ?p ex:requiresCompliance ex:RoHSStandard. }
           WHERE { ?p ex:hasComponent ?c . ?c ex:usesMaterial ex:LeadMaterial . }""",
    ),
)

TEXTILES_RULES: tuple[Rule, ...] = (
    Rule(
        "txt_care_label_for_any_fabric",
        "Any fabric component requires a care label.",
        """CONSTRUCT { ?p ex:requiresCompliance ex:CareLabelRequirement. }
           WHERE { ?p ex:hasComponent ?c . ?c rdf:type ex:Fabric . }""",
    ),
    Rule(
        "txt_wool_care_standard",
        "Wool brings the product under the wool care standard.",
        """CONSTRUCT { ?p ex:requiresCompliance ex:WoolCareStandard. }
           WHERE { ?p ex:hasComponent ?c . ?c ex:usesMaterial ex:WoolMaterial . }""",
    ),
)

VIESSMANN_RULES: tuple[Rule, ...] = (
    Rule(
        "vsm_emc_and_safety",
        "An electronic control unit brings EMC and safety obligations.",
        """CONSTRUCT { ?p ex:requiresCompliance ex:EMCStandard. }
           WHERE { ?p ex:hasComponent ?c . ?c rdf:type ex:ControlUnit . }""",
    ),
)

LEXMARK_RULES: tuple[Rule, ...] = (
    Rule(
        "prn_toner_label_weee",
        "A toner cartridge brings the product under WEEE labelling.",
        """CONSTRUCT { ?p ex:requiresCompliance ex:WEEEStandard. }
           WHERE { ?p ex:hasComponent ?c . ?c rdf:type ex:TonerCartridge . }""",
    ),
    Rule(
        "prn_lead_implies_rohs",
        "Any component using lead brings the product under RoHS.",
        """CONSTRUCT { ?p ex:requiresCompliance ex:RoHSStandard. }
           WHERE { ?p ex:hasComponent ?c . ?c ex:usesMaterial ex:LeadMaterial . }""",
    ),
)

RULES_BY_DOMAIN: dict[str, tuple[Rule, ...]] = {
    "battery": BATTERY_RULES,
    "textiles": TEXTILES_RULES,
    "viessmann": VIESSMANN_RULES,
    "lexmark": LEXMARK_RULES,
}


def rules_for(domain: str) -> tuple[Rule, ...]:
    return RULES_BY_DOMAIN.get(domain, ())
