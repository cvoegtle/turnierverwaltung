"""Table and seating models."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Seat:
    position: int  # 1, 2, 3, (4)
    player_number: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "position": self.position,
            "player_number": self.player_number,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Seat:
        return cls(
            position=int(data["position"]),
            player_number=int(data["player_number"]),
        )


@dataclass
class PlayerPlacement:
    player_number: int
    rank: int  # 1..capacity; tied players have identical rank
    points_awarded: float = 0.0
    raw_score: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "player_number": self.player_number,
            "rank": self.rank,
            "points_awarded": round(self.points_awarded, 2),
            "raw_score": self.raw_score,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> PlayerPlacement:
        return cls(
            player_number=int(data["player_number"]),
            rank=int(data["rank"]),
            points_awarded=float(data.get("points_awarded", 0.0)),
            raw_score=float(data["raw_score"]) if data.get("raw_score") is not None else None,
        )


@dataclass
class Table:
    table_number: int
    round_number: int
    capacity: int  # 3 or 4
    seats: List[Seat] = field(default_factory=list)
    results: List[PlayerPlacement] = field(default_factory=list)

    @property
    def is_completed(self) -> bool:
        return len(self.results) == len(self.seats) and len(self.seats) > 0

    @property
    def player_numbers(self) -> List[int]:
        return [seat.player_number for seat in self.seats]

    def get_seat_for_player(self, player_number: int) -> Optional[Seat]:
        for seat in self.seats:
            if seat.player_number == player_number:
                return seat
        return None

    def get_result_for_player(self, player_number: int) -> Optional[PlayerPlacement]:
        for res in self.results:
            if res.player_number == player_number:
                return res
        return None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "table_number": self.table_number,
            "round_number": self.round_number,
            "capacity": self.capacity,
            "seats": [seat.to_dict() for seat in self.seats],
            "results": [res.to_dict() for res in self.results],
            "is_completed": self.is_completed,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Table:
        return cls(
            table_number=int(data["table_number"]),
            round_number=int(data["round_number"]),
            capacity=int(data["capacity"]),
            seats=[Seat.from_dict(s) for s in data.get("seats", [])],
            results=[PlayerPlacement.from_dict(r) for r in data.get("results", [])],
        )
