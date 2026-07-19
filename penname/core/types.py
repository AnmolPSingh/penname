"""Immutable data types shared across the engine."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Span:
    """A detected sensitive value at an absolute character offset in a text."""

    start: int
    end: int
    entity_type: str
    score: float
    text: str


@dataclass(frozen=True, slots=True)
class MappingEntry:
    original: str
    pen_name: str
    entity_type: str
    score: float = 1.0  # detection confidence, shown on the review screen


@dataclass(frozen=True, slots=True)
class Mapping:
    """The reversible link between pen names and real values. Never leaves the machine."""

    entries: tuple[MappingEntry, ...]

    def to_dict(self) -> dict:
        return {
            "version": 1,
            "entries": [
                {
                    "original": e.original,
                    "pen_name": e.pen_name,
                    "entity_type": e.entity_type,
                    "score": e.score,
                }
                for e in self.entries
            ],
        }

    @classmethod
    def from_dict(cls, data: dict) -> Mapping:
        if data.get("version") != 1:
            raise ValueError(f"unsupported mapping version: {data.get('version')!r}")
        return cls(
            entries=tuple(
                MappingEntry(
                    e["original"], e["pen_name"], e["entity_type"], e.get("score", 1.0)
                )
                for e in data["entries"]
            )
        )


@dataclass(frozen=True, slots=True)
class PseudonymizeResult:
    text: str
    mapping: Mapping
