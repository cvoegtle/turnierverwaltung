"""Flask application factory."""

from __future__ import annotations
from typing import Optional

from flask import Flask

from src.config import Config
from src.persistence.repository import TournamentRepository, create_repository


def create_app(
    config: Optional[Config] = None,
    repository: Optional[TournamentRepository] = None,
) -> Flask:
    app = Flask(__name__)
    cfg = config or Config()

    app.config["SECRET_KEY"] = cfg.SECRET_KEY
    app.config["STORAGE_TYPE"] = cfg.STORAGE_TYPE

    # Initialize repository
    if repository is not None:
        app.extensions["repository"] = repository
    else:
        app.extensions["repository"] = create_repository(
            storage_type=cfg.STORAGE_TYPE,
            project_id=cfg.DATASTORE_PROJECT_ID,
            tournament_id=cfg.DATASTORE_TOURNAMENT_ID,
            file_path=cfg.LOCAL_DATA_FILE,
        )

    # Register template filters
    def format_german_date(date_val: Optional[str]) -> str:
        if not date_val:
            return ""
        try:
            parts = str(date_val).strip().split("-")
            if len(parts) == 3 and len(parts[0]) == 4:
                day_str = parts[2].split("T")[0].split(" ")[0]
                return f"{int(day_str):02d}.{int(parts[1]):02d}.{parts[0]}"
        except Exception:
            pass
        return str(date_val)

    app.jinja_env.filters["german_date"] = format_german_date

    # Register routes
    from src.web.routes import bp as main_bp
    app.register_blueprint(main_bp)

    return app
