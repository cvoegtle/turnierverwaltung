"""Player domain entity."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class Player:
    number: int
    name: str
    scores: Dict[int, float] = field(default_factory=dict)

    @property
    def total_score(self) -> float:
        """Sum of all round scores, rounded to 2 decimal places to avoid float artifacts."""
        return round(sum(self.scores.values()), 2)

    def set_score(self, round_num: int, score: float) -> None:
        self.scores[round_num] = round(score, 2)

    def get_score(self, round_num: int) -> float | None:
        return self.scores.get(round_num)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "number": self.number,
            "name": self.name,
            "scores": {str(k): v for k, v in self.scores.items()},
            "total_score": self.total_score,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Player:
        scores = {int(k): float(v) for k, v in data.get("scores", {}).items()}
        return cls(
            number=int(data["number"]),
            name=str(data["name"]),
            scores=scores,
        )
