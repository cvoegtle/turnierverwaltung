"""Unit tests for table capacity calculation and seating optimizer."""

import pytest
from src.domain.seating import (
    calculate_table_capacities,
    evaluate_seating_quality,
    SeatingOptimizer,
)


def test_calculate_table_capacities():
    assert calculate_table_capacities(3) == [3]
    assert calculate_table_capacities(4) == [4]
    with pytest.raises(ValueError):
        calculate_table_capacities(5)
    assert calculate_table_capacities(6) == [3, 3]
    assert calculate_table_capacities(7) == [4, 3]
    assert calculate_table_capacities(8) == [4, 4]
    assert calculate_table_capacities(9) == [3, 3, 3]
    assert calculate_table_capacities(10) == [4, 3, 3]
    assert calculate_table_capacities(11) == [4, 4, 3]
    assert calculate_table_capacities(12) == [4, 4, 4]
    assert calculate_table_capacities(13) == [4, 3, 3, 3]
    assert calculate_table_capacities(14) == [4, 4, 3, 3]
    assert calculate_table_capacities(15) == [4, 4, 4, 3]
    assert calculate_table_capacities(16) == [4, 4, 4, 4]


def test_seating_optimizer_12_players():
    players = list(range(1, 13))
    optimizer = SeatingOptimizer(iterations=6000)
    plan = optimizer.generate_seating_plan(players, rounds=4, seed=42)

    assert set(plan.keys()) == {1, 2, 3, 4}

    # Each round must seat all 12 players across 3 tables of 4
    for r in range(1, 5):
        tables = plan[r]
        assert len(tables) == 3
        seated = []
        for t in tables:
            assert t.capacity == 4
            assert len(t.seats) == 4
            seated.extend([s.player_number for s in t.seats])
            # Check seat positions
            assert [s.position for s in t.seats] == [1, 2, 3, 4]
        assert sorted(seated) == players

    # Check quality
    quality = evaluate_seating_quality(plan, players)
    # Objective 1: No 3-player tables when 12 players
    assert all(count == 0 for count in quality["three_table_counts"].values())

    # Objective 2: Positions should be evenly distributed (ideally 1 per position)
    for p in players:
        pos_dist = quality["position_counts"][p]
        # At most 4 rounds, each position 1..4 should ideally appear once
        for pos in (1, 2, 3, 4):
            assert pos_dist.get(pos, 0) in (0, 1, 2)


def test_seating_optimizer_13_players_balance():
    players = list(range(1, 14))
    optimizer = SeatingOptimizer(iterations=8000)
    plan = optimizer.generate_seating_plan(players, rounds=4, seed=123)

    assert set(plan.keys()) == {1, 2, 3, 4}

    # 13 players: 1 table of 4, 3 tables of 3 (total 13)
    for r in range(1, 5):
        tables = plan[r]
        assert len(tables) == 4
        capacities = sorted([t.capacity for t in tables])
        assert capacities == [3, 3, 3, 4]
        seated = [s.player_number for t in tables for s in t.seats]
        assert sorted(seated) == players

    quality = evaluate_seating_quality(plan, players)
    # Objective 1: 3-table appearances
    # Total 3-player seats across 4 rounds = 4 * 9 = 36.
    # 36 / 13 ~ 2.77 -> every player should have either 2 or 3 appearances at 3-player tables!
    for p in players:
        count = quality["three_table_counts"].get(p, 0)
        assert count in (2, 3), f"Player {p} has {count} 3-table appearances (expected 2 or 3)"
