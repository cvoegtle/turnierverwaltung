"""Unit tests for scoring rules and tie resolutions."""

import pytest
from src.domain.scoring import (
    calculate_points_for_ranks,
    compute_ranks_from_scores,
    build_table_placements,
    get_base_points,
)


def test_base_points():
    assert get_base_points(4) == [5.0, 3.0, 2.0, 1.0]
    assert get_base_points(3) == [5.0, 3.0, 1.0]
    with pytest.raises(ValueError):
        get_base_points(5)


def test_4_player_no_ties():
    ranks = {10: 1, 20: 2, 30: 3, 40: 4}
    pts = calculate_points_for_ranks(4, ranks)
    assert pts[10] == 5.0
    assert pts[20] == 3.0
    assert pts[30] == 2.0
    assert pts[40] == 1.0


def test_4_player_tie_for_first():
    # 2 players tie for 1st place -> split (5 + 3) / 2 = 4.0
    ranks = {10: 1, 20: 1, 30: 3, 40: 4}
    pts = calculate_points_for_ranks(4, ranks)
    assert pts[10] == 4.0
    assert pts[20] == 4.0
    assert pts[30] == 2.0
    assert pts[40] == 1.0


def test_4_player_tie_for_second():
    # 2 players tie for 2nd place -> split (3 + 2) / 2 = 2.5
    ranks = {10: 1, 20: 2, 30: 2, 40: 4}
    pts = calculate_points_for_ranks(4, ranks)
    assert pts[10] == 5.0
    assert pts[20] == 2.5
    assert pts[30] == 2.5
    assert pts[40] == 1.0


def test_4_player_3_way_tie_for_second():
    # 3 players tie for 2nd place -> split (3 + 2 + 1) / 3 = 2.0
    ranks = {10: 1, 20: 2, 30: 2, 40: 2}
    pts = calculate_points_for_ranks(4, ranks)
    assert pts[10] == 5.0
    assert pts[20] == 2.0
    assert pts[30] == 2.0
    assert pts[40] == 2.0


def test_4_player_4_way_tie():
    # 4 players tie for 1st place -> (5 + 3 + 2 + 1) / 4 = 2.75
    ranks = {10: 1, 20: 1, 30: 1, 40: 1}
    pts = calculate_points_for_ranks(4, ranks)
    assert pts[10] == 2.75
    assert pts[20] == 2.75
    assert pts[30] == 2.75
    assert pts[40] == 2.75


def test_3_player_no_ties():
    ranks = {10: 1, 20: 2, 30: 3}
    pts = calculate_points_for_ranks(3, ranks)
    assert pts[10] == 5.0
    assert pts[20] == 3.0
    assert pts[30] == 1.0


def test_3_player_tie_for_first():
    # 2 players tie for 1st -> (5 + 3) / 2 = 4.0
    ranks = {10: 1, 20: 1, 30: 3}
    pts = calculate_points_for_ranks(3, ranks)
    assert pts[10] == 4.0
    assert pts[20] == 4.0
    assert pts[30] == 1.0


def test_3_player_tie_for_second():
    # 2 players tie for 2nd -> (3 + 1) / 2 = 2.0
    ranks = {10: 1, 20: 2, 30: 2}
    pts = calculate_points_for_ranks(3, ranks)
    assert pts[10] == 5.0
    assert pts[20] == 2.0
    assert pts[30] == 2.0


def test_3_player_3_way_tie():
    # 3 players tie for 1st -> (5 + 3 + 1) / 3 = 3.0
    ranks = {10: 1, 20: 1, 30: 1}
    pts = calculate_points_for_ranks(3, ranks)
    assert pts[10] == 3.0
    assert pts[20] == 3.0
    assert pts[30] == 3.0


def test_compute_ranks_from_scores():
    scores = {1: 100, 2: 120, 3: 100, 4: 50}
    ranks = compute_ranks_from_scores(scores)
    assert ranks[2] == 1
    assert ranks[1] == 2
    assert ranks[3] == 2
    assert ranks[4] == 4


def test_build_table_placements():
    entries = [(1, 1, 100.0), (2, 1, 100.0), (3, 3, 50.0), (4, 4, 30.0)]
    placements = build_table_placements(4, entries)
    assert len(placements) == 4
    p1 = next(p for p in placements if p.player_number == 1)
    p2 = next(p for p in placements if p.player_number == 2)
    p3 = next(p for p in placements if p.player_number == 3)
    p4 = next(p for p in placements if p.player_number == 4)
    assert p1.points_awarded == 4.0
    assert p2.points_awarded == 4.0
    assert p3.points_awarded == 2.0
    assert p4.points_awarded == 1.0
