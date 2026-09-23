# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2026 CE-RISE consortium
"""Choosing which profile a record is actually checked against.

CE-RISE mode should validate, repair and synthesise using the consortium's data
models rather than only the hand-written EU DPP schema. The obvious way to do that
-- check the record against all of them at once -- is wrong, and wrong for a reason
worth writing down, because it is the same reason the impact engines are routed
rather than substituted (see ``layered.py``).

The EU DPP schema and the CE-RISE models describe **different documents**. Their
top-level vocabularies do not intersect at a single term: a passport declares
``dpp_id``, ``product``, ``materials``, ``compliance``; ``ProductSystem`` declares
``product_system_identifier``, ``activity_references``, ``reference_flow_specification``.
Every CE-RISE root model closes its object, so a conjunction of the two profiles is
not merely strict, it is unsatisfiable: no document conforms to both, and a mode
that checked both would reject every record ever written.

So the profile is *routed*, by the only question that has an answer: which model
recognises this record's vocabulary? A record whose top-level terms belong to exactly
one CE-RISE model is checked against that model. Anything else -- a passport, an empty
object, a record straddling two models -- goes to the regulatory profile, which is the
one whose job is to say what is missing. That fallback is deliberate: the CE-RISE
models declare no required fields, so routing an unrecognised record to one of them
would answer "conforms" about a document it had not understood.

Recognition is vocabulary, not validity. Routing on *conformance* would mean that the
more broken a CE-RISE document is, the less likely it is to be recognised as one --
so a ProductSystem with a single wrong type would be told it was missing ``dpp_id``,
which is no help to anybody. A model recognises a record when it knows all of its
top-level terms; what the values are then is what the check is for.

The report names the profile that actually ran, never the sentinel, so a caller is
never told a record "conforms" without being told to what.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from ici_core.domain.ids import ProfileId
from ici_core.domain.record import (
    ConformanceReport,
    DPPRecord,
    SchemaProfile,
    ViolationKind,
)
from ici_core.ports import SchemaRegistry

AUTO = ProfileId("ce-rise:auto")


@dataclass
class LayeredSchemaRegistry:
    """Implements ``SchemaRegistry`` by picking the profile that fits the record.

    ``inner`` supplies every individual profile and does all the validating; this
    only decides which one an unspecified request is answered by.
    """

    inner: SchemaRegistry
    base_profile: ProfileId
    candidates: tuple[ProfileId, ...] = ()
    auto_id: ProfileId = field(default=AUTO)

    def default_profile(self) -> ProfileId:
        """Route, when there is anything to route between.

        This is what makes the mode switch change what Validate, Repair and
        Synthesize *do* rather than only what they offer: a request that names no
        profile is answered by the consortium's model when the record is one of
        theirs, and by the regulatory schema when it is not.
        """
        return self.auto_id if self.candidates else self.inner.default_profile()

    def profiles(self) -> Sequence[SchemaProfile]:
        """The individual profiles, plus routing offered as a choice of its own."""
        individual = list(self.inner.profiles())
        if not self.candidates:
            return individual
        return [
            SchemaProfile(
                id=self.auto_id,
                title="CE-RISE — match the record to its data model",
                layer="ce-rise-routed",
                version=None,
                source=", ".join(str(p) for p in (self.base_profile, *self.candidates)),
            ),
            *individual,
        ]

    def conform(self, record: DPPRecord, profile: ProfileId) -> ConformanceReport:
        if profile != self.auto_id:
            # A named profile is honoured exactly. Quietly checking something else
            # would make a caller's "conforms" mean something they did not ask for.
            return self.inner.conform(record, profile)
        return self.inner.conform(record, self._route(record))

    # -- routing --------------------------------------------------------------
    def _route(self, record: DPPRecord) -> ProfileId:
        """The CE-RISE model this record is written in, or the regulatory profile.

        Decided by asking each candidate rather than by reading their schemas here:
        the registry is what knows its profiles' contents, and duplicating that
        knowledge would let the two copies drift.

        An empty record raises no unknown term anywhere, so it is recognised by every
        candidate and therefore by none of them in particular -- which is why the
        ambiguous case falls back rather than picking the first.
        """
        if not record.payload:
            return self.base_profile
        fits = [p for p in self.candidates if self._recognises(record, p)]
        return fits[0] if len(fits) == 1 else self.base_profile

    def _recognises(self, record: DPPRecord, profile: ProfileId) -> bool:
        """Whether every top-level term in the record belongs to this profile.

        Top level only: what kind of document this is, is decided by the terms it
        declares, not by a stray unknown key somewhere inside one of them.
        """
        report = self.inner.conform(record, profile)
        return not any(
            v.kind is ViolationKind.UNKNOWN_PROPERTY and v.location in ("", "/")
            for v in report.violations
        )


__all__ = ["AUTO", "LayeredSchemaRegistry"]
