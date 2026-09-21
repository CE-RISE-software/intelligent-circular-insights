# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2026 CE-RISE consortium
"""The only module that wires the whole system together.

Everything above this line in the dependency graph knows about ports; everything
below it is an adapter. ``import-linter`` enforces that ``ici_core`` never imports
an adapter package, so this file is where the arrows finally meet.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Annotated

from fastapi import Depends, Header, Request

from apps.api.bundles import BundleRegistry
from apps.api.middleware.mode import ModeResolution, ModeResolver
from apps.api.settings import Settings, get_settings
from ici_core.domain.errors import CapabilityError
from ici_core.domain.modes import BackendMode
from ici_core.ledger import InMemoryLedger
from ici_core.usecases.deps import ProviderBundle
from ici_llm.provider import OpenAIProvider
from ici_llm.runtime import LLMRequest, LLMRuntime


def get_registry(request: Request) -> BundleRegistry:
    registry: BundleRegistry = request.app.state.registry
    return registry


def get_resolver(request: Request) -> ModeResolver:
    resolver: ModeResolver = request.app.state.mode_resolver
    return resolver


def resolve_mode(
    request: Request,
    resolver: Annotated[ModeResolver, Depends(get_resolver)],
    x_backend_mode: Annotated[str | None, Header()] = None,
) -> ModeResolution:
    """One resolution per request, shared with the response header.

    ``ModeMiddleware`` has already resolved and stashed it; this reads that value
    so the handler and the ``X-Backend-Mode-Used`` header can never disagree. The
    fallback path exists for tests that mount a router without the middleware.
    """
    stashed: ModeResolution | None = getattr(request.state, "mode_resolution", None)
    if stashed is not None:
        return stashed
    return resolver.resolve(header=x_backend_mode)


def get_bundle(
    registry: Annotated[BundleRegistry, Depends(get_registry)],
    resolution: Annotated[ModeResolution, Depends(resolve_mode)],
) -> ProviderBundle:
    """The adapter set for this request. Raises CapabilityError → 422 if absent."""
    return replace(registry.for_mode(resolution.mode), ledger=InMemoryLedger(mode=resolution.mode))


def get_llm_request(
    request: Request,
    bundle: Annotated[ProviderBundle, Depends(get_bundle)],
    x_model: Annotated[str | None, Header()] = None,
) -> LLMRequest:
    """Bind the resolved mode and model to fresh audit/budget state, never the bundle."""
    settings: Settings = request.app.state.settings
    if settings.llm_disabled:
        raise CapabilityError(
            capability="language model",
            mode=bundle.mode.value,
            reason="Language-model assistance is disabled in this deployment.",
        )
    if not isinstance(bundle.llm, OpenAIProvider):
        raise CapabilityError(
            capability="language model",
            mode=bundle.mode.value,
            reason="No request-scoped language-model adapter is configured.",
        )
    return LLMRuntime(bundle.llm).request(model=x_model, mode=bundle.mode)


__all__ = [
    "BackendMode",
    "Settings",
    "get_bundle",
    "get_llm_request",
    "get_registry",
    "get_resolver",
    "get_settings",
    "resolve_mode",
]
