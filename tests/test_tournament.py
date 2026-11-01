"""Unit tests for Tournament aggregate root."""

import pytest
from src.domain.tournament import Tournament


def test_tournament_creation_with_name_and_date():
    t = Tournament(name="Paderborner Herbstturnier 2026", date="2026-10-24")
    assert t.name == "Paderborner Herbstturnier 2026"
    assert t.date == "2026-10-24"
    assert t.formatted_date == "24.10.2026"
    assert t.id is not None
    assert len(t.id) > 0

    # Serialization with id and date
    d = t.to_dict()
    assert d["name"] == "Paderborner Herbstturnier 2026"
    assert d["date"] == "2026-10-24"
    assert d["formatted_date"] == "24.10.2026"
    assert d["id"] == t.id

    t2 = Tournament.from_dict(d)
    assert t2.id == t.id
    assert t2.name == t.name
    assert t2.date == "2026-10-24"
    assert t2.formatted_date == "24.10.2026"

    # Various date formats
    assert Tournament(date="2026-05-02").formatted_date == "02.05.2026"
    assert Tournament(date="15.11.2026").formatted_date == "15.11.2026"
    assert Tournament(date="").formatted_date == ""


def test_player_management():
    t = Tournament()
    p1 = t.add_player(1, "Alice")
    assert p1.number == 1
    assert p1.name == "Alice"

    # Duplicate number
    with pytest.raises(ValueError):
        t.add_player(1, "Bob")

    # Update player
    t.update_player(1, "Alice Cooper")
    assert t.get_player(1).name == "Alice Cooper"

    # Remove player
    t.remove_player(1)
    assert t.get_player(1) is None


def test_game_management():
    t = Tournament()
    # Initially games are not prefilled
    assert t.get_game(1).name == ""
    assert t.get_game(2).name == ""
    assert t.get_game(3).name == ""
    assert t.get_game(4).name == ""
    assert t.has_all_games() is False

    # Cannot set empty or pure whitespace name
    with pytest.raises(ValueError, match="nicht leer"):
        t.set_game(1, "")
    with pytest.raises(ValueError, match="nur aus Leerzeichen"):
        t.set_game(1, "   ")

    t.set_game(1, "Catan")
    assert t.get_game(1).name == "Catan"

    # Cannot set duplicate name (case-insensitive)
    with pytest.raises(ValueError, match="Jedes Spiel muss anders heißen"):
        t.set_game(2, "catan")

    t.set_game(2, "Carcassonne")
    t.set_game(3, "Azul")
    t.set_game(4, "Wingspan")

    assert t.get_game(1).name == "Catan"
    assert t.get_game(2).name == "Carcassonne"
    assert t.get_game(3).name == "Azul"
    assert t.get_game(4).name == "Wingspan"
    assert t.has_all_games() is True

    # Invalid round number
    with pytest.raises(ValueError):
        t.set_game(5, "Invalid")

    # set_all_games with duplicates or missing
    with pytest.raises(ValueError, match="Jedes Spiel muss anders heißen"):
        t.set_all_games({1: "Catan", 2: "Catan", 3: "Azul", 4: "Wingspan"})

    with pytest.raises(ValueError, match="nicht leer"):
        t.set_all_games({1: "Catan", 2: "   ", 3: "Azul", 4: "Wingspan"})

    # Valid set_all_games with multi-word names
    t.set_all_games({1: "Die Siedler", 2: "Stone Age", 3: "Azul", 4: "Wingspan"})
    assert t.get_game(1).name == "Die Siedler"
    assert t.get_game(2).name == "Stone Age"
    assert t.has_all_games() is True


def test_tournament_lifecycle_and_standings():
    t = Tournament()
    for i in range(1, 9):
        t.add_player(i, f"Player {i}")

    t.generate_seating_plan(seed=42, iterations=1000)
    assert len(t.rounds) == 4

    # Table 1 in Round 1: suppose players are p1, p2, p3, p4
    table1 = t.rounds[1][0]
    p_nums = table1.player_numbers

    # Record result: tie for 1st place between first two players
    placements_data = [
        (p_nums[0], 1, 100.0),
        (p_nums[1], 1, 100.0),
        (p_nums[2], 3, 80.0),
        (p_nums[3], 4, 60.0),
    ]
    t.record_table_result(1, table1.table_number, placements_data)

    assert table1.is_completed
    assert t.has_results() is True
    assert t.get_player(p_nums[0]).scores[1] == 4.0
    assert t.get_player(p_nums[1]).scores[1] == 4.0
    assert t.get_player(p_nums[2]).scores[1] == 2.0
    assert t.get_player(p_nums[3]).scores[1] == 1.0

    # Once results are recorded, player management is locked
    with pytest.raises(ValueError, match="gesperrt"):
        t.add_player(99, "Latecomer")
    with pytest.raises(ValueError, match="gesperrt"):
        t.update_player(1, "Renamed")
    with pytest.raises(ValueError, match="gesperrt"):
        t.remove_player(8)

    # Test clearing table results
    t.clear_table_result(1, table1.table_number)
    assert not table1.is_completed
    assert t.has_results() is False
    assert 1 not in t.get_player(p_nums[0]).scores


def test_standings_no_tiebreaker():
    t = Tournament()
    p1 = t.add_player(1, "Anna")
    p2 = t.add_player(2, "Bernd")
    p3 = t.add_player(3, "Clara")
    p4 = t.add_player(4, "David")

    # Anna and Bernd have 15 points each (tied)
    p1.set_score(1, 5.0)
    p1.set_score(2, 5.0)
    p1.set_score(3, 5.0)  # 15.0

    p2.set_score(1, 5.0)
    p2.set_score(2, 5.0)
    p2.set_score(3, 5.0)  # 15.0

    # Clara has 10 points
    p3.set_score(1, 5.0)
    p3.set_score(2, 5.0)  # 10.0

    # David has 5 points
    p4.set_score(1, 5.0)  # 5.0

    standings = t.get_standings()
    assert len(standings) == 4

    # Ranks: Anna and Bernd both Rank 1, Clara Rank 3, David Rank 4
    assert standings[0].rank == 1
    assert standings[0].total_score == 15.0

    assert standings[1].rank == 1
    assert standings[1].total_score == 15.0

    assert standings[2].rank == 3
    assert standings[2].total_score == 10.0

    assert standings[3].rank == 4
    assert standings[3].total_score == 5.0


def test_serialization():
    t = Tournament(name="Sommerturnier 2026")
    t.add_player(1, "Anna")
    t.add_player(2, "Bernd")
    t.add_player(3, "Clara")
    t.add_player(4, "David")
    t.add_player(5, "Eva")
    t.add_player(6, "Felix")

    t.set_game(1, "Siedler")
    t.generate_seating_plan(seed=99, iterations=500)

    data = t.to_dict()
    assert data["name"] == "Sommerturnier 2026"
    assert len(data["players"]) == 6
    assert len(data["rounds"]) == 4

    reconstructed = Tournament.from_dict(data)
    assert reconstructed.name == "Sommerturnier 2026"
    assert len(reconstructed.players) == 6
    assert reconstructed.get_game(1).name == "Siedler"
    assert len(reconstructed.rounds) == 4
    assert reconstructed.rounds[1][0].capacity in (3, 4)


def test_alphabetical_table_labeling():
    from src.domain.table import Table, table_number_to_label, table_label_to_number

    assert table_number_to_label(1) == "A"
    assert table_number_to_label(2) == "B"
    assert table_number_to_label(3) == "C"
    assert table_number_to_label(26) == "Z"
    assert table_number_to_label(27) == "AA"

    assert table_label_to_number("A") == 1
    assert table_label_to_number("b") == 2
    assert table_label_to_number("Z") == 26
    assert table_label_to_number("AA") == 27

    t = Table(table_number=1, round_number=1, capacity=4)
    assert t.table_label == "A"
    assert t.name == "Tisch A"
    assert t.to_dict()["table_label"] == "A"

    t2 = Table(table_number=2, round_number=1, capacity=4)
    assert t2.table_label == "B"
    assert t2.name == "Tisch B"
