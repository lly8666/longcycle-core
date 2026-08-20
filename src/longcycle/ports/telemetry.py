from __future__ import annotations

from contextlib import AbstractContextManager
from typing import Any, Protocol


class Span(AbstractContextManager["Span"], Protocol):
    def set_attribute(self, key: str, value: str | int | float | bool) -> None: ...


class Telemetry(Protocol):
    def span(self, name: str, **attributes: Any) -> Span: ...

    def increment(self, name: str, value: float = 1, **labels: str) -> None: ...

    def observe(self, name: str, value: float, **labels: str) -> None: ...


class _NullSpan:
    def __enter__(self) -> "_NullSpan":
        return self

    def __exit__(self, *_: object) -> None:
        return None

    def set_attribute(self, key: str, value: str | int | float | bool) -> None:
        del key, value


class NullTelemetry:
    def span(self, name: str, **attributes: Any) -> _NullSpan:
        del name, attributes
        return _NullSpan()

    def increment(self, name: str, value: float = 1, **labels: str) -> None:
        del name, value, labels

    def observe(self, name: str, value: float, **labels: str) -> None:
        del name, value, labels
