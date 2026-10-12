from __future__ import annotations
import datetime
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from src.domain.game import Game
from src.domain.player import Player
from src.domain.scoring import build_table_placements
from src.domain.seating import SeatingOptimizer
from src.domain.table import Table


@dataclass
class StandingEntry:
    rank: int
    player: Player

    @property
    def total_score(self) -> float:
        return self.player.total_score

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rank": self.rank,
            "player": self.player.to_dict(),
            "total_score": self.total_score,
        }


@dataclass
class Tournament:
    name: str = "Spieleclub Paderborn Turnier"
    date: str = ""  # Termin, e.g. "2026-10-24"
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    created_at: str = field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat()
    )
    players: Dict[int, Player] = field(default_factory=dict)
    games: Dict[int, Game] = field(
        default_factory=lambda: {
            1: Game(round_number=1, name=""),
            2: Game(round_number=2, name=""),
            3: Game(round_number=3, name=""),
            4: Game(round_number=4, name=""),
        }
    )
    rounds: Dict[int, List[Table]] = field(default_factory=dict)

    @property
    def formatted_date(self) -> str:
        """Returns the tournament date formatted in German date format DD.MM.YYYY."""
        if not self.date:
            return ""
        try:
            parts = self.date.strip().split("-")
            if len(parts) == 3 and len(parts[0]) == 4:
                day_str = parts[2].split("T")[0].split(" ")[0]
                return f"{int(day_str):02d}.{int(parts[1]):02d}.{parts[0]}"
        except Exception:
            pass
        return self.date

    # Player management
    def add_player(self, number: int, name: str) -> Player:
        if number in self.players:
            raise ValueError(f"Spielernummer {number} existiert bereits.")
        clean_name = name.strip()
        if not clean_name:
            raise ValueError("Spielername darf nicht leer sein.")
        player = Player(number=number, name=clean_name)
        self.players[number] = player
        return player

    def update_player(self, number: int, new_name: str) -> None:
        if number not in self.players:
            raise ValueError(f"Spieler mit Nummer {number} nicht gefunden.")
        clean_name = new_name.strip()
        if not clean_name:
            raise ValueError("Spielername darf nicht leer sein.")
        self.players[number].name = clean_name

    def remove_player(self, number: int) -> None:
        if number not in self.players:
            raise ValueError(f"Spieler mit Nummer {number} nicht gefunden.")
        # Check if rounds already started with results
        for r_tables in self.rounds.values():
            for t in r_tables:
                if any(r.player_number == number for r in t.results):
                    raise ValueError(
                        f"Spieler {number} hat bereits Spielergebnisse und kann nicht gelöscht werden."
                    )
        del self.players[number]

    def get_player(self, number: int) -> Optional[Player]:
        return self.players.get(number)

    def set_game(self, round_num: int, name: str) -> None:
        if round_num not in (1, 2, 3, 4):
            raise ValueError(f"Ungültige Rundennummer: {round_num}. Erlaubt sind 1 bis 4.")
        clean_name = name.strip()
        if not clean_name:
            raise ValueError("Spielname darf nicht leer sein oder nur aus Leerzeichen bestehen.")
        for r, g in self.games.items():
            if r != round_num and g.name.strip() and g.name.strip().casefold() == clean_name.casefold():
                raise ValueError(
                    f"Jedes Spiel muss anders heißen. '{clean_name}' wird bereits für Runde {r} verwendet."
                )
        self.games[round_num] = Game(round_number=round_num, name=clean_name)

    def set_all_games(self, game_names: Dict[int, str]) -> None:
        """Sets and validates all 4 games at once, ensuring no empty/whitespace names and unique names."""
        if set(game_names.keys()) != {1, 2, 3, 4}:
            raise ValueError("Es müssen genau 4 Spiele für die Runden 1 bis 4 angegeben werden.")
        cleaned: Dict[int, str] = {}
        for r_num in (1, 2, 3, 4):
            val = (game_names.get(r_num) or "").strip()
            if not val:
                raise ValueError(f"Spiel für Runde {r_num} darf nicht leer sein oder nur aus Leerzeichen bestehen.")
            cleaned[r_num] = val

        seen: Dict[str, int] = {}
        for r_num, clean_name in cleaned.items():
            norm = clean_name.casefold()
            if norm in seen:
                raise ValueError(
                    f"Jedes Spiel muss anders heißen. '{clean_name}' (Runde {r_num}) ist doppelt zu Runde {seen[norm]}."
                )
            seen[norm] = r_num

        for r_num, clean_name in cleaned.items():
            self.games[r_num] = Game(round_number=r_num, name=clean_name)

    def has_all_games(self) -> bool:
        """Checks if all 4 games are entered, non-empty, and pairwise distinct."""
        names = []
        for r_num in (1, 2, 3, 4):
            g = self.games.get(r_num)
            if not g:
                return False
            clean = g.name.strip()
            if not clean:
                return False
            names.append(clean.casefold())
        return len(names) == 4 and len(set(names)) == 4

    def get_game(self, round_num: int) -> Game:
        return self.games.get(round_num, Game(round_number=round_num, name=""))

    # Seating allocation
    def generate_seating_plan(self, seed: Optional[int] = None, iterations: int = 25000) -> None:
        player_numbers = sorted(self.players.keys())
        if len(player_numbers) < 3:
            raise ValueError("Mindestens 3 Spieler erforderlich, um Tische einzuteilen.")
        if len(player_numbers) == 5:
            raise ValueError("5 Spieler können nicht auf 3er- und 4er-Tische aufgeteilt werden.")

        optimizer = SeatingOptimizer(iterations=iterations)
        self.rounds = optimizer.generate_seating_plan(player_numbers, rounds=4, seed=seed)

        # Clear existing player round scores when new seating plan is generated
        for p in self.players.values():
            p.scores.clear()

    # Results recording
    def record_table_result(
        self,
        round_num: int,
        table_num: int,
        placements_data: List[Tuple[int, int, Optional[float]]],
    ) -> None:
        """Records table results.

        placements_data is a list of (player_number, rank, optional_raw_score).
        Calculates awarded tournament points and updates player total scores.
        """
        if round_num not in self.rounds:
            raise ValueError(f"Runde {round_num} wurde noch nicht eingeteilt.")

        tables = self.rounds[round_num]
        table = next((t for t in tables if t.table_number == table_num), None)
        if not table:
            raise ValueError(f"Tisch {table_num} in Runde {round_num} nicht gefunden.")

        seated_pnums = set(table.player_numbers)
        input_pnums = set(p[0] for p in placements_data)
        if seated_pnums != input_pnums:
            raise ValueError(
                f"Eingegebene Spieler {input_pnums} stimmen nicht mit Tischbelegung {seated_pnums} überein."
            )

        placements = build_table_placements(table.capacity, placements_data)
        table.results = placements

        # Update player scores
        for place in placements:
            p = self.players.get(place.player_number)
            if p:
                p.set_score(round_num, place.points_awarded)

    def clear_table_result(self, round_num: int, table_num: int) -> None:
        if round_num not in self.rounds:
            return
        table = next((t for t in self.rounds[round_num] if t.table_number == table_num), None)
        if not table:
            return
        for place in table.results:
            p = self.players.get(place.player_number)
            if p and round_num in p.scores:
                del p.scores[round_num]
        table.results = []

    # Standings calculation
    def get_standings(self) -> List[StandingEntry]:
        """Calculates tournament standings sorted by total points descending.

        Per user requirement: NO TIEBREAKER.
        Tied players share the exact same rank.
        Example: Scores [15, 12, 12, 10] -> Ranks [1, 2, 2, 4].
        """
        players_list = list(self.players.values())
        # Sort primarily by total score descending, secondary by player number for stable display
        sorted_players = sorted(
            players_list,
            key=lambda p: (-p.total_score, p.number),
        )

        standings: List[StandingEntry] = []
        for idx, player in enumerate(sorted_players):
            if idx == 0:
                rank = 1
            else:
                prev_player = sorted_players[idx - 1]
                if player.total_score == prev_player.total_score:
                    rank = standings[-1].rank
                else:
                    rank = idx + 1
            standings.append(StandingEntry(rank=rank, player=player))

        return standings

    # Serialization
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "date": self.date,
            "formatted_date": self.formatted_date,
            "created_at": self.created_at,
            "players": [p.to_dict() for p in self.players.values()],
            "games": [g.to_dict() for g in self.games.values()],
            "rounds": {
                str(r_num): [t.to_dict() for t in tables]
                for r_num, tables in self.rounds.items()
            },
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Tournament:
        tournament = cls(
            id=str(data.get("id", uuid.uuid4().hex[:8])),
            name=str(data.get("name", "Spieleclub Paderborn Turnier")),
            date=str(data.get("date", "")),
            created_at=str(
                data.get("created_at", datetime.datetime.now(datetime.timezone.utc).isoformat())
            ),
        )

        # Load players
        for p_data in data.get("players", []):
            p = Player.from_dict(p_data)
            tournament.players[p.number] = p

        # Load games
        tournament.games.clear()
        for g_data in data.get("games", []):
            g = Game.from_dict(g_data)
            tournament.games[g.round_number] = g

        # Ensure all 4 games exist
        for r_num in (1, 2, 3, 4):
            if r_num not in tournament.games:
                tournament.games[r_num] = Game(round_number=r_num, name="")

        # Load rounds
        tournament.rounds.clear()
        rounds_dict = data.get("rounds", {})
        for r_str, tables_data in rounds_dict.items():
            r_num = int(r_str)
            tournament.rounds[r_num] = [Table.from_dict(t) for t in tables_data]

        return tournament
