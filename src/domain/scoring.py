"""Scoring rules for 4-player and 3-player tables with tie resolution."""

from __future__ import annotations
from collections import defaultdict
from typing import Dict, List, Optional, Tuple
from src.domain.table import PlayerPlacement

POINTS_4_PLAYER = [5.0, 3.0, 2.0, 1.0]
POINTS_3_PLAYER = [5.0, 3.0, 1.0]


def get_base_points(capacity: int) -> List[float]:
    """Returns the base points for a table with the given capacity."""
    if capacity == 4:
        return list(POINTS_4_PLAYER)
    elif capacity == 3:
        return list(POINTS_3_PLAYER)
    raise ValueError(f"Ungültige Tischgröße: {capacity}. Erlaubt sind 3 oder 4 Plätze.")


def compute_ranks_from_scores(scores: Dict[int, float], reverse: bool = True) -> Dict[int, int]:
    """Computes placement ranks from raw scores (e.g., game victory points).

    If reverse=True (default), higher score gets rank 1.
    Tied scores receive the same rank.
    Example: {1: 100, 2: 100, 3: 80, 4: 50} -> {1: 1, 2: 1, 3: 3, 4: 4}
    """
    if not scores:
        return {}

    sorted_players = sorted(scores.items(), key=lambda item: item[1], reverse=reverse)
    ranks: Dict[int, int] = {}
    current_rank = 1
    for idx, (p_num, score) in enumerate(sorted_players):
        if idx > 0 and score == sorted_players[idx - 1][1]:
            ranks[p_num] = ranks[sorted_players[idx - 1][0]]
        else:
            current_rank = idx + 1
            ranks[p_num] = current_rank
    return ranks


def calculate_points_for_ranks(capacity: int, player_ranks: Dict[int, int]) -> Dict[int, float]:
    """Calculates tournament points for players at a table based on their placement ranks.

    Points distribution:
    - 4-player table: 1st=5, 2nd=3, 3rd=2, 4th=1
    - 3-player table: 1st=5, 2nd=3, 3rd=1

    Ties:
    Points for the tied positions are summed and divided equally among tied players.
    """
    base_points = get_base_points(capacity)
    player_count = len(player_ranks)
    if player_count != capacity:
        raise ValueError(
            f"Anzahl Spieler ({player_count}) stimmt nicht mit Tischgröße ({capacity}) überein."
        )

    # Group players by rank
    rank_groups = defaultdict(list)
    for p_num, rank in player_ranks.items():
        rank_groups[rank].append(p_num)

    # Sort ranks ascending (rank 1 is best)
    sorted_ranks = sorted(rank_groups.keys())

    points_awarded: Dict[int, float] = {}
    current_pos = 0  # 0-indexed position in base_points

    for rank in sorted_ranks:
        tied_players = rank_groups[rank]
        k = len(tied_players)
        slice_points = base_points[current_pos : current_pos + k]
        avg_points = round(sum(slice_points) / k, 2)
        for p_num in tied_players:
            points_awarded[p_num] = avg_points
        current_pos += k

    return points_awarded


def build_table_placements(
    capacity: int,
    entries: List[Tuple[int, int, Optional[float]]],
) -> List[PlayerPlacement]:
    """Builds a list of PlayerPlacement objects from a list of (player_number, rank, raw_score)."""
    player_ranks = {p_num: rank for p_num, rank, _ in entries}
    points = calculate_points_for_ranks(capacity, player_ranks)

    placements = []
    for p_num, rank, raw_score in entries:
        placements.append(
            PlayerPlacement(
                player_number=p_num,
                rank=rank,
                points_awarded=points[p_num],
                raw_score=raw_score,
            )
        )
    return placements
