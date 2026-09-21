# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2026 CE-RISE consortium
"""Evidence acquisition: hybrid retrieval and persistent fact memory."""

from __future__ import annotations

from ici_core.text import tokenize
from ici_evidence.documents import DocumentEvidenceProvider, Passage, split_passages
from ici_evidence.inline import (
    DocumentTooLarge,
    InlineDocumentProvider,
    ParsedDocument,
    Section,
    parse_document,
)
from ici_evidence.memory import AppendOnlyFactMemory, UnvalidatedFactError

__all__ = [
    "AppendOnlyFactMemory",
    "DocumentEvidenceProvider",
    "DocumentTooLarge",
    "InlineDocumentProvider",
    "ParsedDocument",
    "Passage",
    "Section",
    "UnvalidatedFactError",
    "parse_document",
    "split_passages",
    "tokenize",
]
