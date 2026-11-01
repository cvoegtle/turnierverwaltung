"""HTTP routes for tournament management UI."""

from __future__ import annotations
import datetime
import json
from typing import List, Optional, Tuple
from flask import (
    Blueprint,
    Response,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from src.domain.tournament import Tournament
from src.persistence.repository import TournamentRepository

bp = Blueprint("main", __name__)


def get_repo() -> TournamentRepository:
    return current_app.extensions["repository"]


def get_tournament_or_404(t_id: str) -> Tournament:
    repo = get_repo()
    tournament = repo.get(t_id)
    if not tournament:
        abort(404, description=f"Turnier mit ID '{t_id}' nicht gefunden.")
    return tournament


@bp.before_request
def enforce_games_configured():
    if not request.endpoint or not request.endpoint.startswith("main."):
        return None

    excluded_endpoints = {
        "main.index",
        "main.create_tournament",
        "main.delete_tournament",
        "main.games",
    }
    if request.endpoint in excluded_endpoints:
        return None

    t_id = request.view_args.get("t_id") if request.view_args else None
    if not t_id:
        return None

    repo = get_repo()
    tournament = repo.get(t_id)
    if not tournament:
        return None

    if not tournament.has_all_games():
        flash(
            "Die Spieleerfassung kann nicht verlassen werden, bevor alle 4 Spiele eingegeben sind. Jedes Spiel muss einen eindeutigen Namen haben.",
            "warning",
        )
        return redirect(url_for("main.games", t_id=t_id, wizard=1))


# --- Tournament Overview & Management ---

@bp.route("/")
@bp.route("/tournaments")
def index():
    repo = get_repo()
    tournaments = repo.list_all()
    today_date = datetime.date.today().isoformat()
    return render_template(
        "tournaments.html",
        tournaments=tournaments,
        today_date=today_date,
    )


@bp.route("/tournaments/new", methods=["GET", "POST"])
def create_tournament():
    repo = get_repo()
    if request.method == "GET":
        tournaments = repo.list_all()
        today_date = datetime.date.today().isoformat()
        return render_template(
            "tournaments.html",
            tournaments=tournaments,
            today_date=today_date,
        )

    name = request.form.get("name", "").strip()
    date_val = request.form.get("date", "").strip()

    if not name:
        flash("Bitte einen Turniernamen eingeben.", "warning")
        return redirect(url_for("main.index"))

    tournament = Tournament(name=name, date=date_val)
    repo.save(tournament)
    flash(
        f"Turnier '{tournament.name}' angelegt! Schritt 1 abgeschlossen. Bitte lege nun die 4 Spiele fest.",
        "success",
    )
    return redirect(url_for("main.games", t_id=tournament.id, wizard=1))



@bp.route("/tournaments/<t_id>/edit", methods=["POST"])
def edit_tournament(t_id: str):
    repo = get_repo()
    tournament = get_tournament_or_404(t_id)
    name = request.form.get("name", "").strip()
    date_val = request.form.get("date", "").strip()

    if not name:
        flash("Turniername darf nicht leer sein.", "warning")
    else:
        tournament.name = name
        tournament.date = date_val
        repo.save(tournament)
        flash("Turnierdaten erfolgreich aktualisiert.", "success")

    return redirect(url_for("main.tournament_dashboard", t_id=t_id))


@bp.route("/tournaments/<t_id>/delete", methods=["POST"])
def delete_tournament(t_id: str):
    repo = get_repo()
    tournament = get_tournament_or_404(t_id)
    repo.delete(t_id)
    flash(f"Turnier '{tournament.name}' wurde gelöscht.", "info")
    return redirect(url_for("main.index"))


# --- Tournament Details & Flow ---

@bp.route("/tournaments/<t_id>")
def tournament_dashboard(t_id: str):
    tournament = get_tournament_or_404(t_id)
    rounds_summary = []
    for r_num in (1, 2, 3, 4):
        tables = tournament.rounds.get(r_num, [])
        total_tables = len(tables)
        completed_tables = sum(1 for t in tables if t.is_completed)
        rounds_summary.append({
            "round_number": r_num,
            "game_name": tournament.get_game(r_num).name,
            "total_tables": total_tables,
            "completed_tables": completed_tables,
            "is_generated": total_tables > 0,
            "is_completed": total_tables > 0 and completed_tables == total_tables,
        })

    all_tournaments = get_repo().list_all()

    return render_template(
        "index.html",
        tournament=tournament,
        rounds_summary=rounds_summary,
        player_count=len(tournament.players),
        all_tournaments=all_tournaments,
    )


@bp.route("/tournaments/<t_id>/players", methods=["GET"])
def players(t_id: str):
    tournament = get_tournament_or_404(t_id)
    is_wizard = request.args.get("wizard") == "1"
    sorted_players = sorted(tournament.players.values(), key=lambda p: p.number)
    next_number = max([p.number for p in sorted_players], default=0) + 1
    return render_template(
        "players.html",
        tournament=tournament,
        players=sorted_players,
        next_number=next_number,
        wizard=is_wizard,
    )


@bp.route("/tournaments/<t_id>/players/add", methods=["POST"])
def add_player(t_id: str):
    repo = get_repo()
    tournament = get_tournament_or_404(t_id)
    is_wizard = request.form.get("wizard") == "1" or request.args.get("wizard") == "1"
    if tournament.has_results():
        flash("Die Spielerverwaltung ist gesperrt, da bereits Ergebnisse erfasst wurden.", "warning")
        return redirect(url_for("main.players", t_id=t_id))
    try:
        number = int(request.form.get("number", 0))
        name = request.form.get("name", "").strip()
        tournament.add_player(number, name)
        repo.save(tournament)
        flash(f"Spieler #{number} ({name}) erfolgreich hinzugefügt.", "success")
    except ValueError as e:
        flash(f"Fehler beim Hinzufügen: {e}", "danger")
    return redirect(url_for("main.players", t_id=t_id, wizard=1 if is_wizard else None))


@bp.route("/tournaments/<t_id>/players/bulk", methods=["POST"])
def bulk_add_players(t_id: str):
    repo = get_repo()
    tournament = get_tournament_or_404(t_id)
    is_wizard = request.form.get("wizard") == "1" or request.args.get("wizard") == "1"
    if tournament.has_results():
        flash("Die Spielerverwaltung ist gesperrt, da bereits Ergebnisse erfasst wurden.", "warning")
        return redirect(url_for("main.players", t_id=t_id))
    raw_text = request.form.get("names", "")
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]

    if not lines:
        flash("Keine Namen eingegeben.", "warning")
        return redirect(url_for("main.players", t_id=t_id, wizard=1 if is_wizard else None))

    added_count = 0
    next_num = max([p.number for p in tournament.players.values()], default=0) + 1
    for name in lines:
        if "," in name:
            parts = name.split(",", 1)
            try:
                p_num = int(parts[0].strip())
                p_name = parts[1].strip()
            except ValueError:
                p_num = next_num
                p_name = name
        else:
            p_num = next_num
            p_name = name

        while p_num in tournament.players:
            p_num += 1

        try:
            tournament.add_player(p_num, p_name)
            added_count += 1
            next_num = p_num + 1
        except Exception as e:
            flash(f"Fehler bei Spieler '{name}': {e}", "danger")
            break

    repo.save(tournament)
    if added_count > 0:
        flash(f"{added_count} Spieler erfolgreich hinzugefügt.", "success")
    return redirect(url_for("main.players", t_id=t_id, wizard=1 if is_wizard else None))


@bp.route("/tournaments/<t_id>/players/<int:number>/edit", methods=["POST"])
def edit_player(t_id: str, number: int):
    repo = get_repo()
    tournament = get_tournament_or_404(t_id)
    is_wizard = request.form.get("wizard") == "1" or request.args.get("wizard") == "1"
    if tournament.has_results():
        flash("Die Spielerverwaltung ist gesperrt, da bereits Ergebnisse erfasst wurden.", "warning")
        return redirect(url_for("main.players", t_id=t_id))
    new_name = request.form.get("name", "").strip()
    try:
        tournament.update_player(number, new_name)
        repo.save(tournament)
        flash(f"Spieler #{number} aktualisiert.", "success")
    except ValueError as e:
        flash(f"Fehler beim Aktualisieren: {e}", "danger")
    return redirect(url_for("main.players", t_id=t_id, wizard=1 if is_wizard else None))


@bp.route("/tournaments/<t_id>/players/<int:number>/delete", methods=["POST"])
def delete_player(t_id: str, number: int):
    repo = get_repo()
    tournament = get_tournament_or_404(t_id)
    is_wizard = request.form.get("wizard") == "1" or request.args.get("wizard") == "1"
    if tournament.has_results():
        flash("Die Spielerverwaltung ist gesperrt, da bereits Ergebnisse erfasst wurden.", "warning")
        return redirect(url_for("main.players", t_id=t_id))
    try:
        tournament.remove_player(number)
        repo.save(tournament)
        flash(f"Spieler #{number} gelöscht.", "success")
    except ValueError as e:
        flash(f"Fehler beim Löschen: {e}", "danger")
    return redirect(url_for("main.players", t_id=t_id, wizard=1 if is_wizard else None))


@bp.route("/tournaments/<t_id>/games", methods=["GET", "POST"])
def games(t_id: str):
    repo = get_repo()
    tournament = get_tournament_or_404(t_id)
    is_wizard = request.args.get("wizard") == "1" or request.form.get("wizard") == "1"

    if request.method == "POST":
        submitted_games = {
            r_num: request.form.get(f"game_{r_num}", "")
            for r_num in (1, 2, 3, 4)
        }
        try:
            tournament.set_all_games(submitted_games)
            repo.save(tournament)
        except ValueError as e:
            flash(f"Fehler bei der Spieleingabe: {e}", "danger")
            return render_template(
                "games.html",
                tournament=tournament,
                wizard=is_wizard or (not tournament.has_all_games()),
                form_data=submitted_games,
            )

        if is_wizard:
            flash(
                "Spiele erfolgreich gespeichert! Schritt 2 abgeschlossen. Erfasse nun als Nächstes die Spieler.",
                "success",
            )
            return redirect(url_for("main.players", t_id=t_id, wizard=1))

        flash("Spiele erfolgreich gespeichert.", "success")
        return redirect(url_for("main.tournament_dashboard", t_id=t_id))

    return render_template(
        "games.html",
        tournament=tournament,
        wizard=is_wizard or (not tournament.has_all_games()),
    )


@bp.route("/tournaments/<t_id>/rounds/generate", methods=["POST"])
def generate_seating(t_id: str):
    repo = get_repo()
    tournament = get_tournament_or_404(t_id)
    is_wizard = request.form.get("wizard") == "1" or request.args.get("wizard") == "1"
    try:
        tournament.generate_seating_plan()
        repo.save(tournament)
        if is_wizard:
            flash("Turnier-Setup erfolgreich abgeschlossen! Tischverteilung für alle 4 Runden wurde berechnet.", "success")
        else:
            flash("Tischverteilung für alle 4 Runden erfolgreich berechnet!", "success")
    except ValueError as e:
        flash(f"Fehler bei der Tischberechnung: {e}", "danger")
    return redirect(url_for("main.round_detail", t_id=t_id, round_num=1))


@bp.route("/tournaments/<t_id>/rounds/<int:round_num>")
def round_detail(t_id: str, round_num: int):
    if round_num not in (1, 2, 3, 4):
        flash("Ungültige Rundennummer.", "danger")
        return redirect(url_for("main.tournament_dashboard", t_id=t_id))

    tournament = get_tournament_or_404(t_id)
    tables = tournament.rounds.get(round_num, [])
    game = tournament.get_game(round_num)

    return render_template(
        "round.html",
        tournament=tournament,
        round_num=round_num,
        game=game,
        tables=tables,
    )


@bp.route("/tournaments/<t_id>/rounds/<int:round_num>/tables/<int:table_num>/result", methods=["POST"])
def submit_table_result(t_id: str, round_num: int, table_num: int):
    repo = get_repo()
    tournament = get_tournament_or_404(t_id)
    tables = tournament.rounds.get(round_num, [])
    table = next((t for t in tables if t.table_number == table_num), None)
    if not table:
        flash("Tisch nicht gefunden.", "danger")
        return redirect(url_for("main.round_detail", t_id=t_id, round_num=round_num))

    placements_data: List[Tuple[int, int, Optional[float]]] = []
    try:
        for seat in table.seats:
            p_num = seat.player_number
            rank_str = request.form.get(f"rank_{p_num}", "").strip()
            score_str = request.form.get(f"score_{p_num}", "").strip()

            if not rank_str:
                raise ValueError(f"Bitte Platzierung für Spieler #{p_num} angeben.")

            rank = int(rank_str)
            raw_score = float(score_str) if score_str else None
            placements_data.append((p_num, rank, raw_score))

        tournament.record_table_result(round_num, table_num, placements_data)
        repo.save(tournament)
        flash(f"Ergebnisse für Tisch {table.table_label} (Runde {round_num}) gespeichert.", "success")
    except (ValueError, TypeError) as e:
        flash(f"Fehler bei der Ergebniseingabe: {e}", "danger")

    return redirect(url_for("main.round_detail", t_id=t_id, round_num=round_num))


@bp.route("/tournaments/<t_id>/rounds/<int:round_num>/tables/<int:table_num>/clear", methods=["POST"])
def clear_table_result(t_id: str, round_num: int, table_num: int):
    repo = get_repo()
    tournament = get_tournament_or_404(t_id)
    table = next((t for t in tournament.rounds.get(round_num, []) if t.table_number == table_num), None)
    t_label = table.table_label if table else str(table_num)
    tournament.clear_table_result(round_num, table_num)
    repo.save(tournament)
    flash(f"Ergebnis für Tisch {t_label} (Runde {round_num}) zurückgesetzt.", "info")
    return redirect(url_for("main.round_detail", t_id=t_id, round_num=round_num))


@bp.route("/tournaments/<t_id>/standings")
def standings(t_id: str):
    tournament = get_tournament_or_404(t_id)
    standings_list = tournament.get_standings()
    return render_template(
        "standings.html",
        tournament=tournament,
        standings=standings_list,
    )


@bp.route("/tournaments/<t_id>/export/json")
def export_json(t_id: str):
    tournament = get_tournament_or_404(t_id)
    data = json.dumps(tournament.to_dict(), indent=2, ensure_ascii=False)
    filename = f"turnier_{tournament.id}_export.json"
    return Response(
        data,
        mimetype="application/json",
        headers={"Content-Disposition": f"attachment;filename={filename}"},
    )


@bp.route("/tournaments/<t_id>/export/mediawiki")
def export_mediawiki(t_id: str):
    tournament = get_tournament_or_404(t_id)
    wiki_text = tournament.to_mediawiki_table()
    return Response(
        wiki_text,
        mimetype="text/plain; charset=utf-8",
    )


# --- Legacy / Shortcut Redirects (redirect to latest tournament) ---

@bp.route("/players")
def shortcut_players():
    repo = get_repo()
    latest = repo.get()
    if latest:
        return redirect(url_for("main.players", t_id=latest.id))
    return redirect(url_for("main.index"))


@bp.route("/games")
def shortcut_games():
    repo = get_repo()
    latest = repo.get()
    if latest:
        return redirect(url_for("main.games", t_id=latest.id))
    return redirect(url_for("main.index"))


@bp.route("/standings")
def shortcut_standings():
    repo = get_repo()
    latest = repo.get()
    if latest:
        return redirect(url_for("main.standings", t_id=latest.id))
    return redirect(url_for("main.index"))
