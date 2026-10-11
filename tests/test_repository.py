"""Unit tests for repository implementations and factory."""

import os
from unittest.mock import MagicMock, patch
from src.domain.tournament import Tournament
from src.persistence.datastore_repo import DatastoreTournamentRepository
from src.persistence.file_repo import JsonFileTournamentRepository
from src.persistence.memory_repo import InMemoryTournamentRepository
from src.persistence.repository import create_repository


def test_in_memory_repository_multi_tournament():
    repo = InMemoryTournamentRepository()
    assert repo.list_all() == []
    assert repo.get() is None

    t1 = Tournament(name="Frühlingsturnier", date="2026-04-10")
    t2 = Tournament(name="Herbstturnier", date="2026-10-24")

    repo.save(t1)
    repo.save(t2)

    all_t = repo.list_all()
    assert len(all_t) == 2
    assert all_t[0].name == "Herbstturnier"
    assert all_t[1].name == "Frühlingsturnier"

    # Get by ID
    fetched_t1 = repo.get(t1.id)
    assert fetched_t1 is not None
    assert fetched_t1.name == "Frühlingsturnier"
    assert fetched_t1.date == "2026-04-10"

    # Default get returns newest
    latest = repo.get()
    assert latest.id == t2.id

    # Delete
    repo.delete(t1.id)
    assert len(repo.list_all()) == 1
    assert repo.get(t1.id) is None

    # Reset
    repo.reset()
    assert repo.list_all() == []


def test_json_file_repository(tmp_path):
    json_path = str(tmp_path / "tournaments.json")
    repo = JsonFileTournamentRepository(file_path=json_path)

    assert repo.list_all() == []
    assert repo.get() is None

    t1 = Tournament(name="Paderborner Turnier", date="2026-10-24")
    repo.save(t1)

    # Verify file was written to disk
    assert os.path.exists(json_path)

    # Re-instantiate repository pointing to same file (simulates app restart!)
    repo_restarted = JsonFileTournamentRepository(file_path=json_path)
    all_t = repo_restarted.list_all()
    assert len(all_t) == 1
    assert all_t[0].id == t1.id
    assert all_t[0].name == "Paderborner Turnier"
    assert all_t[0].date == "2026-10-24"

    # Delete
    repo_restarted.delete(t1.id)
    assert len(repo_restarted.list_all()) == 0


def test_create_repository_memory():
    repo = create_repository(storage_type="memory")
    assert isinstance(repo, InMemoryTournamentRepository)


def test_create_repository_file(tmp_path):
    json_path = str(tmp_path / "custom.json")
    repo = create_repository(storage_type="file", file_path=json_path)
    assert isinstance(repo, JsonFileTournamentRepository)
    assert repo.file_path == json_path


def test_create_repository_auto_uses_file_repo(tmp_path):
    json_path = str(tmp_path / "auto.json")
    repo = create_repository(storage_type="auto", file_path=json_path)
    assert isinstance(repo, JsonFileTournamentRepository)


def test_create_repository_auto_fallback_on_auth_error(tmp_path):
    with patch("src.persistence.datastore_repo.datastore.Client") as mock_client:
        mock_instance = MagicMock()
        mock_instance.query.side_effect = Exception("Auth failed")
        mock_instance.get.side_effect = Exception("Auth failed")
        mock_client.return_value = mock_instance

        json_path = str(tmp_path / "fallback.json")
        repo = create_repository(storage_type="auto", project_id="dummy-project", file_path=json_path)
        assert isinstance(repo, JsonFileTournamentRepository)


def test_datastore_repository_mocked():
    with patch("src.persistence.datastore_repo.datastore.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        repo = DatastoreTournamentRepository(project_id="test-proj")
        t = Tournament(name="Test Turnier", date="2026-11-01")

        # Save tournament
        repo.save(t)
        assert mock_client.put.called

        # Mock entity fetch
        mock_entity = {
            "data": '{"id": "t123", "name": "Test Turnier", "date": "2026-11-01", "players": [], "games": [], "rounds": {}}'
        }
        mock_client.get.return_value = mock_entity

        fetched = repo.get("t123")
        assert fetched is not None
        assert fetched.name == "Test Turnier"
        assert fetched.date == "2026-11-01"

        # Delete
        repo.delete("t123")
        assert mock_client.delete.called
