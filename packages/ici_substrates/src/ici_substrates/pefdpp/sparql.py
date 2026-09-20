"""A read-only SPARQL guard.

Exposing a query endpoint over a knowledge graph is useful and is also an injection
surface. The guard is deliberately a denylist of *operations* rather than a filter on
text: SPARQL Update has a closed set of keywords, and rejecting the parsed form of a
query is more honest than pattern-matching a string.

Three things are refused, each for its own reason:

- **Update operations** — this endpoint must not be able to change the graph.
- **Federation** (``SERVICE``) — would let a caller make this server fetch from
  somewhere else, turning a read endpoint into an outbound request.
- **Unbounded results** — a query with no limit can exhaust memory on a graph that
  a future substrate may make much larger.
"""

from __future__ import annotations

import re

UPDATE_KEYWORDS = (
    "INSERT",
    "DELETE",
    "DROP",
    "CLEAR",
    "CREATE",
    "LOAD",
    "COPY",
    "MOVE",
    "ADD",
)
FEDERATION_KEYWORDS = ("SERVICE",)
MAX_LIMIT = 1000
DEFAULT_LIMIT = 200

# Strip literals and comments before scanning, so a query that merely *mentions*
# "delete" inside a string is not refused for it.
_LITERAL = re.compile(r'"""[\s\S]*?"""|"[^"\n]*"|\'[^\'\n]*\'')
_COMMENT = re.compile(r"#[^\n]*")


class UnsafeQueryError(ValueError):
    """The query asks for something a read-only endpoint must not do."""


def _scannable(query: str) -> str:
    return _COMMENT.sub(" ", _LITERAL.sub(" ", query)).upper()


def check(query: str) -> None:
    """Raise ``UnsafeQueryError`` if the query must not run. Otherwise return."""
    if not query or not query.strip():
        raise UnsafeQueryError("empty query")

    body = _scannable(query)
    for keyword in UPDATE_KEYWORDS:
        if re.search(rf"\b{keyword}\b", body):
            raise UnsafeQueryError(
                f"only read-only queries are allowed; SPARQL Update keyword {keyword!r} found"
            )
    for keyword in FEDERATION_KEYWORDS:
        if re.search(rf"\b{keyword}\b", body):
            raise UnsafeQueryError(
                f"federation is not allowed; {keyword!r} would make this server "
                f"fetch from elsewhere"
            )
    if not re.search(r"\b(SELECT|ASK|CONSTRUCT|DESCRIBE)\b", body):
        raise UnsafeQueryError("query has no SELECT, ASK, CONSTRUCT or DESCRIBE form")


def clamp_limit(limit: int | None) -> int:
    """Bound the result size. A read endpoint should not be able to exhaust memory."""
    if limit is None:
        return DEFAULT_LIMIT
    return max(1, min(int(limit), MAX_LIMIT))
