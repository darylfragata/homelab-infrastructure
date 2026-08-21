"""Fallback analyzer for any Terraform resource type without a dedicated
service analyzer. Unsupported resources MUST NOT fail the application - this
analyzer can represent any resource type since it only relies on fields every
resource_changes entry has.
"""

from __future__ import annotations

from typing import FrozenSet

from analyzers.base import ResourceAnalyzer

# Intentionally empty: generic.py is the fallback of last resort, not matched
# against a specific type list by the registry.
SUPPORTED_TYPES: FrozenSet[str] = frozenset()


class GenericAnalyzer(ResourceAnalyzer):
    SERVICE_KEY = "generic"
    # IMPORTANT_ATTRIBUTES left empty on purpose: show the full, unfiltered diff.


ANALYZER = GenericAnalyzer()
