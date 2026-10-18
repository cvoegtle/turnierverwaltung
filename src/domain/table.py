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


def table_number_to_label(num: int) -> str:
    """Converts 1-based table number to alphabetical label (1 -> A, 2 -> B, ..., 26 -> Z, 27 -> AA)."""
    if num <= 0:
        return str(num)
    result = []
    n = num
    while n > 0:
        n -= 1
        result.append(chr(ord('A') + (n % 26)))
        n //= 26
    return "".join(reversed(result))


def table_label_to_number(label: str) -> int:
    """Converts alphabetical label to 1-based table number ('A' -> 1, 'B' -> 2, ..., 'AA' -> 27)."""
    clean_label = str(label).strip().upper()
    if clean_label.isdigit():
        return int(clean_label)
    num = 0
    for char in clean_label:
        if 'A' <= char <= 'Z':
            num = num * 26 + (ord(char) - ord('A') + 1)
        else:
            raise ValueError(f"Ungültige Tischbezeichnung: {label}")
    return num


@dataclass
class Table:
    table_number: int
    round_number: int
    capacity: int  # 3 or 4
    seats: List[Seat] = field(default_factory=list)
    results: List[PlayerPlacement] = field(default_factory=list)

    @property
    def table_label(self) -> str:
        """Returns alphabetical table label (e.g. 'A', 'B', 'C')."""
        return table_number_to_label(self.table_number)

    @property
    def name(self) -> str:
        """Returns human-readable name (e.g. 'Tisch A')."""
        return f"Tisch {self.table_label}"

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
            "table_label": self.table_label,
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
