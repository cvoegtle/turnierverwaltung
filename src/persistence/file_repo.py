"""JSON file implementation of TournamentRepository for local persistence."""

from __future__ import annotations
import copy
import json
import logging
import os
from typing import Dict, List, Optional

from src.domain.tournament import Tournament
from src.persistence.repository import TournamentRepository

logger = logging.getLogger(__name__)


class JsonFileTournamentRepository(TournamentRepository):
    """Persists tournaments into a local JSON file across server restarts."""

    def __init__(self, file_path: str = "data/tournaments.json"):
        self.file_path = file_path

    def _ensure_dir(self) -> None:
        dir_name = os.path.dirname(self.file_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)

    def _load_data(self) -> Dict[str, Tournament]:
        if not os.path.exists(self.file_path):
            return {}
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                raw_dict = json.load(f)
            tournaments: Dict[str, Tournament] = {}
            for t_id, t_data in raw_dict.items():
                tournaments[t_id] = Tournament.from_dict(t_data)
            return tournaments
        except Exception as e:
            logger.error("Fehler beim Laden von %s: %s", self.file_path, e)
            return {}

    def _save_data(self, tournaments: Dict[str, Tournament]) -> None:
        self._ensure_dir()
        raw_dict = {t_id: t.to_dict() for t_id, t in tournaments.items()}
        tmp_file = f"{self.file_path}.tmp"
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(raw_dict, f, indent=2, ensure_ascii=False)
        os.replace(tmp_file, self.file_path)

    def list_all(self) -> List[Tournament]:
        tournaments = list(self._load_data().values())
        tournaments.sort(
            key=lambda t: (t.date or "", t.created_at or ""),
            reverse=True,
        )
        return tournaments

    def get(self, tournament_id: Optional[str] = None) -> Optional[Tournament]:
        data = self._load_data()
        if tournament_id:
            return data.get(tournament_id)

        all_t = self.list_all()
        return all_t[0] if all_t else None

    def save(self, tournament: Tournament) -> None:
        data = self._load_data()
        data[tournament.id] = copy.deepcopy(tournament)
        self._save_data(data)

    def delete(self, tournament_id: str) -> None:
        data = self._load_data()
        if tournament_id in data:
            del data[tournament_id]
            self._save_data(data)

    def reset(self) -> None:
        self._save_data({})
