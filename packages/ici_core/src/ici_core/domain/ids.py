# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2026 CE-RISE consortium
"""Identifier newtypes.

These are ``NewType`` rather than bare ``str`` so that mypy catches the class of bug
where a product id is passed where an evidence id belongs. They cost nothing at
runtime and they have already paid for themselves in systems this size.
"""

from __future__ import annotations

from typing import NewType

DppId = NewType("DppId", str)
ProductId = NewType("ProductId", str)
EvidenceId = NewType("EvidenceId", str)
FactId = NewType("FactId", str)
ClaimId = NewType("ClaimId", str)
SubstrateId = NewType("SubstrateId", str)
ProfileId = NewType("ProfileId", str)
CorrelationId = NewType("CorrelationId", str)
SignalName = NewType("SignalName", str)
CalibratorId = NewType("CalibratorId", str)
