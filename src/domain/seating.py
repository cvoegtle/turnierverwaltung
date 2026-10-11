"""Seating plan generator and optimizer across 4 tournament rounds."""

from __future__ import annotations
import math
import random
from collections import defaultdict
from typing import Any, Dict, List, Optional, Set, Tuple

from src.domain.table import Seat, Table


def calculate_table_capacities(player_count: int) -> List[int]:
    """Calculates table capacities (3 or 4) for a given player count.

    Number of tables is ceil(player_count / 4).
    Tables can only have 3 or 4 players.
    Returns list of capacities, e.g. [4, 4, 3] for 11 players.
    """
    if player_count < 3:
        raise ValueError("Mindestens 3 Spieler erforderlich.")
    if player_count == 5:
        raise ValueError(
            "5 Spieler können nicht in 3er- und 4er-Tische aufgeteilt werden. "
            "Mindestens 6 Spieler erforderlich (oder 3 bzw. 4)."
        )

    t = math.ceil(player_count / 4)
    k3 = (4 - (player_count % 4)) % 4
    k4 = t - k3

    if k4 < 0:
        raise ValueError(f"Keine gültige Tischaufteilung für {player_count} Spieler möglich.")

    # List with 4-player tables first, then 3-player tables
    capacities = [4] * k4 + [3] * k3
    if sum(capacities) != player_count:
        raise ValueError(
            f"Berechnete Plätze ({sum(capacities)}) weichen von Spieleranzahl ({player_count}) ab."
        )
    return capacities


class SeatingOptimizer:
    """Heuristic optimizer generating table allocations across 4 rounds.

    Priority of objectives (descending):
    1. Equal 3-player vs 4-player table distribution for each player.
    2. Position balance: playing once at each position (1, 2, 3, 4).
    3. Opponent diversity: playing with as many distinct players as possible (minimizing repeat pairings).
    """

    def __init__(self, iterations: int = 25000):
        self.iterations = iterations

    def generate_seating_plan(
        self,
        player_numbers: List[int],
        rounds: int = 4,
        seed: Optional[int] = None,
    ) -> Dict[int, List[Table]]:
        if len(player_numbers) < 3:
            raise ValueError("Mindestens 3 Spieler erforderlich.")
        if len(set(player_numbers)) != len(player_numbers):
            raise ValueError("Spielernummern müssen eindeutig sein.")

        rng = random.Random(seed)
        n = len(player_numbers)
        capacities = calculate_table_capacities(n)
        num_tables = len(capacities)

        # Slot layout for a round: list of (table_idx, capacity, position)
        slots_layout: List[Tuple[int, int, int]] = []
        for t_idx, cap in enumerate(capacities):
            for pos in range(1, cap + 1):
                slots_layout.append((t_idx, cap, pos))

        players = list(player_numbers)

        # Build initial assignments for all rounds
        # assignments[r] = list of player_numbers corresponding to slots_layout
        assignments: List[List[int]] = []

        # Target 3-table appearances per player
        total_3_slots_per_round = sum(1 for _, cap, _ in slots_layout if cap == 3)
        total_3_slots = total_3_slots_per_round * rounds
        ideal_3_min = math.floor(total_3_slots / n)
        ideal_3_max = math.ceil(total_3_slots / n)

        # Initialize rounds with diversified permutations
        shuffled_players = list(players)
        for r in range(rounds):
            rng.shuffle(shuffled_players)
            assignments.append(list(shuffled_players))

        # Weight factors enforcing strict priority
        W_3TABLE = 100000.0
        W_POSITION = 1000.0
        W_PAIRINGS = 10.0

        def compute_cost() -> float:
            three_counts: Dict[int, int] = defaultdict(int)
            pos_counts: Dict[int, Dict[int, int]] = defaultdict(lambda: defaultdict(int))
            pair_counts: Dict[Tuple[int, int], int] = defaultdict(int)

            for r in range(rounds):
                table_members: Dict[int, List[int]] = defaultdict(list)
                for slot_idx, p in enumerate(assignments[r]):
                    t_idx, cap, pos = slots_layout[slot_idx]
                    table_members[t_idx].append(p)
                    pos_counts[p][pos] += 1
                    if cap == 3:
                        three_counts[p] += 1

                for members in table_members.values():
                    m_len = len(members)
                    for i in range(m_len):
                        for j in range(i + 1, m_len):
                            pair = (min(members[i], members[j]), max(members[i], members[j]))
                            pair_counts[pair] += 1

            cost_3table = 0.0
            for p in players:
                c = three_counts[p]
                if c < ideal_3_min:
                    cost_3table += (ideal_3_min - c) ** 2
                elif c > ideal_3_max:
                    cost_3table += (c - ideal_3_max) ** 2

            cost_pos = 0.0
            for p in players:
                for pos in (1, 2, 3, 4):
                    cnt = pos_counts[p][pos]
                    if cnt > 1:
                        cost_pos += (cnt - 1) ** 2

            cost_pair = 0.0
            for pair, count in pair_counts.items():
                if count > 1:
                    cost_pair += (count - 1) ** 2

            return W_3TABLE * cost_3table + W_POSITION * cost_pos + W_PAIRINGS * cost_pair

        current_cost = compute_cost()
        best_cost = current_cost
        best_assignments = [[p for p in r_assign] for r_assign in assignments]

        # Simulated Annealing / Local Search
        t_start = 50.0
        t_end = 0.1

        for step in range(self.iterations):
            if current_cost == 0:
                break

            r = rng.randint(0, rounds - 1)
            i = rng.randint(0, n - 1)
            j = rng.randint(0, n - 1)
            if i == j:
                continue

            # Swap players i and j in round r
            assignments[r][i], assignments[r][j] = assignments[r][j], assignments[r][i]
            new_cost = compute_cost()
            delta = new_cost - current_cost

            # Annealing temperature schedule
            temperature = t_start * ((t_end / t_start) ** (step / self.iterations))
            if delta < 0 or (temperature > 0 and rng.random() < math.exp(-delta / max(temperature, 1e-4))):
                current_cost = new_cost
                if current_cost < best_cost:
                    best_cost = current_cost
                    best_assignments = [[p for p in r_assign] for r_assign in assignments]
            else:
                # Revert swap
                assignments[r][i], assignments[r][j] = assignments[r][j], assignments[r][i]

        # Construct Table domain objects from best_assignments
        result_plan: Dict[int, List[Table]] = {}
        for r_idx in range(rounds):
            round_num = r_idx + 1
            tables: List[Table] = []
            for t_idx, cap in enumerate(capacities):
                table_num = t_idx + 1
                tables.append(Table(table_number=table_num, round_number=round_num, capacity=cap))

            round_assignment = best_assignments[r_idx]
            for slot_idx, p in enumerate(round_assignment):
                t_idx, cap, pos = slots_layout[slot_idx]
                tables[t_idx].seats.append(Seat(position=pos, player_number=p))

            # Ensure seats are sorted by position
            for t in tables:
                t.seats.sort(key=lambda s: s.position)

            result_plan[round_num] = tables

        return result_plan


def evaluate_seating_quality(
    plan: Dict[int, List[Table]],
    player_numbers: List[int],
) -> Dict[str, Any]:
    """Analyzes a generated seating plan against the 3 tournament goals."""
    three_counts: Dict[int, int] = defaultdict(int)
    pos_counts: Dict[int, Dict[int, int]] = defaultdict(lambda: defaultdict(int))
    pair_counts: Dict[Tuple[int, int], int] = defaultdict(int)
    opponents: Dict[int, Set[int]] = defaultdict(set)

    for round_num, tables in plan.items():
        for table in tables:
            t_players = [s.player_number for s in table.seats]
            for s in table.seats:
                pos_counts[s.player_number][s.position] += 1
                if table.capacity == 3:
                    three_counts[s.player_number] += 1
                for other in t_players:
                    if other != s.player_number:
                        opponents[s.player_number].add(other)

            for i in range(len(t_players)):
                for j in range(i + 1, len(t_players)):
                    pair = (min(t_players[i], t_players[j]), max(t_players[i], t_players[j]))
                    pair_counts[pair] += 1

    repeat_pairs = {pair: count for pair, count in pair_counts.items() if count > 1}

    return {
        "three_table_counts": dict(three_counts),
        "position_counts": {p: dict(pos_counts[p]) for p in player_numbers},
        "repeat_pair_counts": repeat_pairs,
        "opponent_counts": {p: len(opponents[p]) for p in player_numbers},
    }
