from __future__ import annotations

from importlib.metadata import entry_points
from typing import Callable, cast

from longcycle.domain.models import SourceDefinition
from longcycle.ports.source import SourcePlugin

PluginFactory = Callable[[SourceDefinition], SourcePlugin]


class SourceRegistry:
    """Registry supports built-ins, tests and third-party entry-point plugins."""

    def __init__(self) -> None:
        self._factories: dict[str, PluginFactory] = {}

    def register(self, name: str, factory: PluginFactory) -> None:
        if name in self._factories:
            raise ValueError(f"source plugin already registered: {name}")
        self._factories[name] = factory

    def load_entry_points(self) -> None:
        for entry_point in entry_points(group="longcycle.sources"):
            if entry_point.name not in self._factories:
                self._factories[entry_point.name] = cast(PluginFactory, entry_point.load())

    def create(self, definition: SourceDefinition) -> SourcePlugin:
        try:
            factory = self._factories[definition.plugin]
        except KeyError as exc:
            available = ", ".join(sorted(self._factories)) or "none"
            raise KeyError(f"unknown source plugin {definition.plugin!r}; available: {available}") from exc
        return factory(definition)

    @property
    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._factories))
