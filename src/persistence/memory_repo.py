"""In-memory implementation of TournamentRepository."""

from __future__ import annotations
import copy
from typing import Dict, List, Optional

from src.domain.tournament import Tournament
from src.persistence.repository import TournamentRepository


class InMemoryTournamentRepository(TournamentRepository):
    """In-memory repository managing multiple tournaments."""

    def __init__(self, initial_tournaments: Optional[List[Tournament]] = None):
        self._tournaments: Dict[str, Tournament] = {}
        if initial_tournaments:
            for t in initial_tournaments:
                self._tournaments[t.id] = copy.deepcopy(t)

    def list_all(self) -> List[Tournament]:
        tournaments = list(self._tournaments.values())
        # Sort by date descending, then created_at descending
        sorted_list = sorted(
            tournaments,
            key=lambda t: (t.date or "", t.created_at or ""),
            reverse=True,
        )
        return [copy.deepcopy(t) for t in sorted_list]

    def get(self, tournament_id: Optional[str] = None) -> Optional[Tournament]:
        if tournament_id:
            t = self._tournaments.get(tournament_id)
            return copy.deepcopy(t) if t else None

        # If no tournament_id provided, return the most recent tournament if any
        all_tournaments = self.list_all()
        return all_tournaments[0] if all_tournaments else None

    def save(self, tournament: Tournament) -> None:
        self._tournaments[tournament.id] = copy.deepcopy(tournament)

    def delete(self, tournament_id: str) -> None:
        self._tournaments.pop(tournament_id, None)

    def reset(self) -> None:
        self._tournaments.clear()
