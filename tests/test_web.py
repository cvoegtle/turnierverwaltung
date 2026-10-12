"""Integration tests for Flask web UI, tournament creation, and workflows."""

import pytest
from src.config import Config
from src.domain.tournament import Tournament
from src.persistence.memory_repo import InMemoryTournamentRepository
from src.web.app import create_app


@pytest.fixture
def client():
    config = Config()
    config.STORAGE_TYPE = "memory"
    repo = InMemoryTournamentRepository()
    app = create_app(config=config, repository=repo)
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_tournaments_index_and_creation(client):
    # Initial page with no tournaments
    resp = client.get("/")
    assert resp.status_code == 200
    assert "Noch keine Turniere vorhanden" in resp.get_data(as_text=True)
    import datetime
    today_iso = datetime.date.today().isoformat()
    assert f'value="{today_iso}"' in resp.get_data(as_text=True)

    # Create tournament with name and date (Termin)
    resp = client.post(
        "/tournaments/new",
        data={"name": "Herbstturnier 2026", "date": "2026-10-24"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    content = resp.get_data(as_text=True)
    assert "Herbstturnier 2026" in content
    assert "24.10.2026" in content

    # Check that tournament appears on the overview page without displaying tournament ID
    resp = client.get("/tournaments")
    assert resp.status_code == 200
    assert "Herbstturnier 2026" in resp.get_data(as_text=True)
    assert "24.10.2026" in resp.get_data(as_text=True)
    assert "Spiele unvollständig" in resp.get_data(as_text=True)
    repo = client.application.extensions["repository"]
    t = repo.list_all()[0]
    assert f"ID: {t.id}" not in resp.get_data(as_text=True)

    # Dashboard cannot be accessed before games are entered (redirects to games)
    dash_resp = client.get(f"/tournaments/{t.id}")
    assert dash_resp.status_code == 302
    assert dash_resp.headers["Location"].endswith(f"/tournaments/{t.id}/games?wizard=1")

    # Enter games
    client.post(
        f"/tournaments/{t.id}/games",
        data={
            "game_1": "Game 1",
            "game_2": "Game 2",
            "game_3": "Game 3",
            "game_4": "Game 4",
        },
    )

    # Now dashboard can be accessed and does not display tournament ID
    dash_resp = client.get(f"/tournaments/{t.id}")
    assert dash_resp.status_code == 200
    assert "Turnier-ID" not in dash_resp.get_data(as_text=True)
    assert f"<code>{t.id}</code>" not in dash_resp.get_data(as_text=True)



def test_edit_and_delete_tournament(client):
    # Create tournament
    client.post("/tournaments/new", data={"name": "Altes Turnier", "date": "2026-05-01"})
    repo = client.application.extensions["repository"]
    t = repo.list_all()[0]
    t.set_all_games({1: "Spiel A", 2: "Spiel B", 3: "Spiel C", 4: "Spiel D"})
    repo.save(t)

    # Edit tournament
    resp = client.post(
        f"/tournaments/{t.id}/edit",
        data={"name": "Aktualisiertes Turnier", "date": "2026-05-02"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert "Aktualisiertes Turnier" in resp.get_data(as_text=True)
    assert "02.05.2026" in resp.get_data(as_text=True)

    # Delete tournament
    resp = client.post(f"/tournaments/{t.id}/delete", follow_redirects=True)
    assert resp.status_code == 200
    assert len(repo.list_all()) == 0


def test_players_crud_within_tournament(client):
    client.post("/tournaments/new", data={"name": "Turnier 1", "date": "2026-10-24"})
    repo = client.application.extensions["repository"]
    t = repo.list_all()[0]

    # Trying to add player before games are entered redirects to games
    blocked_resp = client.post(
        f"/tournaments/{t.id}/players/add",
        data={"number": "1", "name": "Alice"},
    )
    assert blocked_resp.status_code == 302
    assert blocked_resp.headers["Location"].endswith(f"/tournaments/{t.id}/games?wizard=1")

    # Enter games
    t.set_all_games({1: "Spiel 1", 2: "Spiel 2", 3: "Spiel 3", 4: "Spiel 4"})
    repo.save(t)

    # Add single player
    resp = client.post(
        f"/tournaments/{t.id}/players/add",
        data={"number": "1", "name": "Alice"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    html_content = resp.get_data(as_text=True)
    assert "Alice" in html_content
    assert "btn-icon-cloud" in html_content
    assert "💾" not in html_content

    # Bulk add players
    resp = client.post(
        f"/tournaments/{t.id}/players/bulk",
        data={"names": "Bob\nCharlie\nDavid\nEva\nFelix"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    content = resp.get_data(as_text=True)
    assert "Bob" in content
    assert "Felix" in content

    # Edit player
    resp = client.post(
        f"/tournaments/{t.id}/players/1/edit",
        data={"name": "Alice Wonderland"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert "Alice Wonderland" in resp.get_data(as_text=True)

    # Delete player
    resp = client.post(f"/tournaments/{t.id}/players/6/delete", follow_redirects=True)
    assert resp.status_code == 200
    assert "Felix" not in resp.get_data(as_text=True)


def test_games_configuration(client):
    client.post("/tournaments/new", data={"name": "Turnier 1", "date": "2026-10-24"})
    repo = client.application.extensions["repository"]
    t = repo.list_all()[0]

    # Post games without wizard and check redirect to tournament dashboard (overview)
    resp = client.post(
        f"/tournaments/{t.id}/games",
        data={
            "game_1": "Catan",
            "game_2": "Carcassonne",
            "game_3": "Azul",
            "game_4": "Wingspan",
        },
    )
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith(f"/tournaments/{t.id}")

    # Follow redirect and verify dashboard contains success message
    follow_resp = client.get(resp.headers["Location"])
    assert follow_resp.status_code == 200
    assert "Spiele erfolgreich gespeichert" in follow_resp.get_data(as_text=True)

    resp = client.get(f"/tournaments/{t.id}/games")
    assert "Catan" in resp.get_data(as_text=True)
    assert "Wingspan" in resp.get_data(as_text=True)


def test_complete_tournament_flow(client):
    # 1. Create tournament
    client.post("/tournaments/new", data={"name": "Meisterschaft 2026", "date": "2026-10-24"})
    repo = client.application.extensions["repository"]
    t = repo.list_all()[0]

    # 2. Configure games (must be done before players / rounds!)
    client.post(
        f"/tournaments/{t.id}/games",
        data={
            "game_1": "Game A",
            "game_2": "Game B",
            "game_3": "Game C",
            "game_4": "Game D",
        },
    )

    # 3. Register 8 players
    for i in range(1, 9):
        client.post(
            f"/tournaments/{t.id}/players/add",
            data={"number": str(i), "name": f"Player {i}"},
        )

    # 4. Generate seating
    resp = client.post(f"/tournaments/{t.id}/rounds/generate", follow_redirects=True)
    assert resp.status_code == 200
    assert "Tischverteilung für alle 4 Runden erfolgreich berechnet" in resp.get_data(as_text=True)

    # Check dashboard: recalculate is now in danger zone, not top header action buttons
    dash_resp = client.get(f"/tournaments/{t.id}")
    dash_html = dash_resp.get_data(as_text=True)
    assert "Tischverteilung neu berechnen" in dash_html
    assert "danger-zone" in dash_html
    assert "Turnier-ID" not in dash_html

    # 5. View round 1
    resp = client.get(f"/tournaments/{t.id}/rounds/1")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert "Tisch 1" in html
    assert "Tisch 2" in html

    # 6. Submit result for Table 1
    updated_t = repo.get(t.id)
    t1 = updated_t.rounds[1][0]
    p_nums = t1.player_numbers

    result_data = {
        f"rank_{p_nums[0]}": "1",
        f"score_{p_nums[0]}": "100",
        f"rank_{p_nums[1]}": "1",
        f"score_{p_nums[1]}": "100",
        f"rank_{p_nums[2]}": "3",
        f"score_{p_nums[2]}": "70",
        f"rank_{p_nums[3]}": "4",
        f"score_{p_nums[3]}": "50",
    }
    resp = client.post(
        f"/tournaments/{t.id}/rounds/1/tables/1/result",
        data=result_data,
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert "Ergebnisse für Tisch 1 (Runde 1) gespeichert" in resp.get_data(as_text=True)

    # 7. Check standings
    resp = client.get(f"/tournaments/{t.id}/standings")
    assert resp.status_code == 200
    standings_html = resp.get_data(as_text=True)
    assert "Turnierwertung: Meisterschaft 2026" in standings_html
    assert "4.00" in standings_html

    # 8. Check exports
    csv_resp = client.get(f"/tournaments/{t.id}/export/csv")
    assert csv_resp.status_code == 200
    assert csv_resp.mimetype == "text/csv"
    assert "Gesamtpunkte" in csv_resp.get_data(as_text=True)

    json_resp = client.get(f"/tournaments/{t.id}/export/json")
    assert json_resp.status_code == 200
    assert json_resp.mimetype == "application/json"


def test_guided_tournament_creation_wizard(client):
    # Step 1: Create tournament via POST /tournaments/new
    resp = client.post(
        "/tournaments/new",
        data={"name": "Wizard Cup", "date": "2026-11-15"},
    )
    assert resp.status_code == 302
    repo = client.application.extensions["repository"]
    t = repo.list_all()[0]
    assert resp.headers["Location"].endswith(f"/tournaments/{t.id}/games?wizard=1")

    # Step 2: User is guided to the Games step
    games_resp = client.get(resp.headers["Location"])
    assert games_resp.status_code == 200
    games_html = games_resp.get_data(as_text=True)
    assert "Schritt 2 von 3: Turnierspiele festlegen" in games_html
    assert "Wizard Cup" in games_html
    assert "15.11.2026" in games_html
    assert "Spiele speichern &amp; weiter zu den Spielern →" in games_html or "Spiele speichern & weiter zu den Spielern →" in games_html

    # Requirement checks: games are not prefilled, no skipping or cancel buttons
    assert 'value=""' in games_html
    assert "Spiele überspringen" not in games_html
    assert "Assistent beenden" not in games_html
    assert "Abbrechen" not in games_html

    # Cannot leave games step before games are entered
    skip_attempt = client.get(f"/tournaments/{t.id}/players")
    assert skip_attempt.status_code == 302
    assert skip_attempt.headers["Location"].endswith(f"/tournaments/{t.id}/games?wizard=1")

    # Cannot submit duplicate names
    dup_resp = client.post(
        f"/tournaments/{t.id}/games",
        data={
            "wizard": "1",
            "game_1": "Catan",
            "game_2": "catan",
            "game_3": "Azul",
            "game_4": "Wingspan",
        },
    )
    assert dup_resp.status_code == 200
    assert "Jedes Spiel muss anders heißen" in dup_resp.get_data(as_text=True)

    # Cannot submit whitespace-only names
    ws_resp = client.post(
        f"/tournaments/{t.id}/games",
        data={
            "wizard": "1",
            "game_1": "   ",
            "game_2": "Carcassonne",
            "game_3": "Azul",
            "game_4": "Wingspan",
        },
    )
    assert ws_resp.status_code == 200
    assert "darf nicht leer sein" in ws_resp.get_data(as_text=True)

    # Submit valid games in wizard mode
    resp_games_post = client.post(
        f"/tournaments/{t.id}/games",
        data={
            "wizard": "1",
            "game_1": "Die Siedler von Catan",
            "game_2": "Carcassonne",
            "game_3": "Azul",
            "game_4": "Wingspan",
        },
    )
    assert resp_games_post.status_code == 302
    assert resp_games_post.headers["Location"].endswith(f"/tournaments/{t.id}/players?wizard=1")

    # Step 3: User is guided to the Players step
    players_resp = client.get(resp_games_post.headers["Location"])
    assert players_resp.status_code == 200
    players_html = players_resp.get_data(as_text=True)
    assert "Schritt 3 von 3: Turnierteilnehmer erfassen" in players_html
    assert "Es werden noch mindestens" in players_html

    # Register players in wizard mode
    bulk_resp = client.post(
        f"/tournaments/{t.id}/players/bulk",
        data={
            "wizard": "1",
            "names": "Alice\nBob\nCharlie\nDiana",
        },
    )
    assert bulk_resp.status_code == 302
    assert bulk_resp.headers["Location"].endswith(f"/tournaments/{t.id}/players?wizard=1")

    # Inspect players page with registered players
    players_resp2 = client.get(bulk_resp.headers["Location"])
    players_html2 = players_resp2.get_data(as_text=True)
    assert "4 Spieler" in players_html2
    assert "Bereit zum Starten" in players_html2
    assert "Tische auslosen" in players_html2
    assert "Setup beenden & zum Dashboard" not in players_html2
    assert "btn-icon-delete" in players_html2

    # Finish wizard by calculating seating
    generate_resp = client.post(
        f"/tournaments/{t.id}/rounds/generate",
        data={"wizard": "1"},
        follow_redirects=True,
    )
    assert generate_resp.status_code == 200
    final_html = generate_resp.get_data(as_text=True)
    assert "Turnier-Setup erfolgreich abgeschlossen" in final_html
    assert "Runde 1" in final_html
    assert "Die Siedler von Catan" in final_html


def test_game_recording_mandatory_and_validation(client):
    # 1. Create a tournament
    client.post("/tournaments/new", data={"name": "Sperr-Turnier", "date": "2026-10-30"})
    repo = client.application.extensions["repository"]
    t = repo.list_all()[0]

    # Verify that trying to access any subroute redirects to games
    for route in [
        f"/tournaments/{t.id}",
        f"/tournaments/{t.id}/players",
        f"/tournaments/{t.id}/rounds/1",
        f"/tournaments/{t.id}/standings",
        f"/tournaments/{t.id}/export/csv",
        f"/tournaments/{t.id}/export/json",
    ]:
        resp = client.get(route)
        assert resp.status_code == 302, f"Expected 302 for {route}"
        assert resp.headers["Location"].endswith(f"/tournaments/{t.id}/games?wizard=1")

    # Verify navbar on games page only shows games (Pflicht), no overview/players/rounds/standings
    games_resp = client.get(f"/tournaments/{t.id}/games")
    games_html = games_resp.get_data(as_text=True)
    assert "Spiele erfassen (Pflicht)" in games_html
    assert f"/tournaments/{t.id}/players" not in games_html
    assert f"/tournaments/{t.id}/standings" not in games_html
    assert "Spiele überspringen" not in games_html
    assert "Abbrechen" not in games_html

    # Cannot save if any game is empty or pure whitespace
    resp_empty = client.post(
        f"/tournaments/{t.id}/games",
        data={
            "game_1": "Catan",
            "game_2": "   ",
            "game_3": "Azul",
            "game_4": "Wingspan",
        },
    )
    assert resp_empty.status_code == 200
    assert "darf nicht leer sein" in resp_empty.get_data(as_text=True)
    assert 'value="Catan"' in resp_empty.get_data(as_text=True)

    # Cannot save if games have duplicate names (case-insensitive and trimmed)
    resp_dup = client.post(
        f"/tournaments/{t.id}/games",
        data={
            "game_1": "  Catan  ",
            "game_2": "catan",
            "game_3": "Azul",
            "game_4": "Wingspan",
        },
    )
    assert resp_dup.status_code == 200
    assert "Jedes Spiel muss anders heißen" in resp_dup.get_data(as_text=True)

    # Games with spaces between words are allowed, leading/trailing whitespace trimmed
    resp_ok = client.post(
        f"/tournaments/{t.id}/games",
        data={
            "wizard": "1",
            "game_1": "  Stone Age  ",
            "game_2": "Castle Combo",
            "game_3": "Rajas of the Ganges",
            "game_4": "Kingdomino",
        },
    )
    assert resp_ok.status_code == 302
    assert resp_ok.headers["Location"].endswith(f"/tournaments/{t.id}/players?wizard=1")

    # Verify games were trimmed and stored in repo
    updated_t = repo.get(t.id)
    assert updated_t.get_game(1).name == "Stone Age"
    assert updated_t.get_game(2).name == "Castle Combo"
    assert updated_t.get_game(3).name == "Rajas of the Ganges"
    assert updated_t.get_game(4).name == "Kingdomino"
    assert updated_t.has_all_games() is True

    # Now subroutes can be accessed
    assert client.get(f"/tournaments/{t.id}").status_code == 200
    assert client.get(f"/tournaments/{t.id}/players").status_code == 200

