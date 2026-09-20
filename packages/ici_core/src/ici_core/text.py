# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2026 CE-RISE consortium
"""Shared text handling.

``tokenize`` lives in the core because two adapters need it — retrieval, to score
passages, and the signal layer, to measure whether evidence agrees with itself —
and an adapter that imports another adapter is exactly the coupling this
architecture exists to prevent. It is pure: no I/O, no configuration, no state.
"""

from __future__ import annotations

import re

TOKEN = re.compile(r"[a-z0-9][a-z0-9\-_.]*")


def tokenize(text: str) -> list[str]:
    """Lowercase tokens, with sentence punctuation stripped from the edges.

    Identifiers are the point: ``EN_62133-2``, ``B-0001``, ``gpt-4o-mini`` must
    survive as single tokens, because they are exactly what these questions turn
    on. But a token ending a sentence arrives as ``en_62133-2.`` and would then
    never match a query for ``en_62133-2`` — so trailing separators come off while
    internal ones stay.
    """
    return [stripped for raw in TOKEN.findall(text.lower()) if (stripped := raw.strip("._-"))]
