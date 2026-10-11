"""Google Cloud Datastore repository implementation for Tournament persistence."""

from __future__ import annotations
import datetime
import json
import logging
from typing import List, Optional

from google.cloud import datastore

from src.domain.tournament import Tournament
from src.persistence.repository import TournamentRepository

logger = logging.getLogger(__name__)


class DatastoreTournamentRepository(TournamentRepository):
    """Persists multiple tournament entities in Google Cloud Datastore."""

    def __init__(
        self,
        project_id: Optional[str] = None,
        tournament_id: Optional[str] = None,
        namespace: Optional[str] = None,
    ):
        self.project_id = project_id
        self.namespace = namespace
        self.client = datastore.Client(project=project_id, namespace=namespace)

    def _get_key(self, tournament_id: str) -> datastore.Key:
        return self.client.key("Tournament", tournament_id)

    def list_all(self) -> List[Tournament]:
        query = self.client.query(kind="Tournament")
        entities = list(query.fetch())
        tournaments: List[Tournament] = []

        for entity in entities:
            if "data" in entity:
                try:
                    data = json.loads(entity["data"])
                    tournaments.append(Tournament.from_dict(data))
                except Exception as e:
                    logger.error("Fehler beim Deserialisieren von Turnier %s: %s", entity.key.name, e)

        tournaments.sort(
            key=lambda t: (t.date or "", t.created_at or ""),
            reverse=True,
        )
        return tournaments

    def get(self, tournament_id: Optional[str] = None) -> Optional[Tournament]:
        if tournament_id:
            key = self._get_key(tournament_id)
            entity = self.client.get(key)
            if entity is None or "data" not in entity:
                return None
            try:
                data = json.loads(entity["data"])
                return Tournament.from_dict(data)
            except Exception as e:
                logger.error("Fehler beim Deserialisieren des Turniers %s: %s", tournament_id, e)
                return None

        # Return latest tournament if none specified
        all_tournaments = self.list_all()
        return all_tournaments[0] if all_tournaments else None

    def save(self, tournament: Tournament) -> None:
        key = self._get_key(tournament.id)
        entity = datastore.Entity(key=key, exclude_from_indexes=["data"])
        entity["name"] = tournament.name
        entity["date"] = tournament.date
        entity["created_at"] = tournament.created_at
        entity["updated_at"] = datetime.datetime.now(datetime.timezone.utc)
        entity["data"] = json.dumps(tournament.to_dict(), ensure_ascii=False)
        self.client.put(entity)

    def delete(self, tournament_id: str) -> None:
        key = self._get_key(tournament_id)
        self.client.delete(key)

    def reset(self) -> None:
        query = self.client.query(kind="Tournament")
        keys = [entity.key for entity in query.fetch()]
        if keys:
            self.client.delete_multi(keys)
