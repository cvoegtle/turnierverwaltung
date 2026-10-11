"""Game domain entity."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class Game:
    round_number: int
    name: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "round_number": self.round_number,
            "name": self.name,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Game:
        return cls(
            round_number=int(data["round_number"]),
            name=str(data.get("name", "")),
        )
