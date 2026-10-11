"""Abstract repository interface for Tournament persistence."""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List, Optional

from src.domain.tournament import Tournament


class TournamentRepository(ABC):
    """Abstract interface defining persistence operations for Tournaments."""

    @abstractmethod
    def list_all(self) -> List[Tournament]:
        """Returns all tournaments sorted by date/creation descending."""
        pass

    @abstractmethod
    def get(self, tournament_id: Optional[str] = None) -> Optional[Tournament]:
        """Retrieves a tournament by ID, or the most recent one if tournament_id is None."""
        pass

    @abstractmethod
    def save(self, tournament: Tournament) -> None:
        """Persists the tournament state."""
        pass

    @abstractmethod
    def delete(self, tournament_id: str) -> None:
        """Deletes a tournament by ID."""
        pass

    @abstractmethod
    def reset(self) -> None:
        """Resets or clears all tournaments."""
        pass


def create_repository(
    storage_type: str = "auto",
    project_id: Optional[str] = None,
    tournament_id: str = "default",
    file_path: Optional[str] = None,
) -> TournamentRepository:
    """Factory creating the appropriate repository based on storage_type."""
    import logging
    import os
    logger = logging.getLogger(__name__)

    st = storage_type.lower()
    if st == "memory":
        logger.info("Verwende InMemoryTournamentRepository (explizit konfiguriert).")
        from src.persistence.memory_repo import InMemoryTournamentRepository
        return InMemoryTournamentRepository()

    local_file = file_path or os.environ.get("LOCAL_DATA_FILE", "data/tournaments.json")
    if st == "file":
        logger.info("Verwende JsonFileTournamentRepository mit Datei: %s", local_file)
        from src.persistence.file_repo import JsonFileTournamentRepository
        return JsonFileTournamentRepository(file_path=local_file)

    if st == "datastore":
        from src.persistence.datastore_repo import DatastoreTournamentRepository
        return DatastoreTournamentRepository(project_id=project_id, tournament_id=tournament_id)

    # st == "auto"
    # Detect environment: Cloud Run, GCP, Datastore Emulator, or explicit project
    on_cloud_run = bool(os.environ.get("K_SERVICE") or os.environ.get("K_REVISION"))
    has_emulator = bool(os.environ.get("DATASTORE_EMULATOR_HOST"))
    has_explicit_project = bool(project_id or os.environ.get("DATASTORE_PROJECT_ID"))

    if on_cloud_run or has_emulator or has_explicit_project:
        try:
            from src.persistence.datastore_repo import DatastoreTournamentRepository
            repo = DatastoreTournamentRepository(project_id=project_id, tournament_id=tournament_id)
            _ = repo.get()
            logger.info("Google Cloud Datastore initialisiert (Cloud Run / Emulator / Projekt konfiguriert).")
            return repo
        except Exception as exc:
            logger.warning(
                "Google Cloud Datastore konnte nicht initialisiert werden (%s). "
                "Wechsle auf lokale Datei: %s",
                exc,
                local_file,
            )
            from src.persistence.file_repo import JsonFileTournamentRepository
            return JsonFileTournamentRepository(file_path=local_file)

    # Default for local development without emulator/cloud run: persist in local JSON file!
    logger.info("Lokale Entwicklungsumgebung erkannt. Speichere Turniere dauerhaft in '%s'.", local_file)
    from src.persistence.file_repo import JsonFileTournamentRepository
    return JsonFileTournamentRepository(file_path=local_file)

