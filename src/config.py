"""Configuration settings for Turnierverwaltung."""

import os
from typing import Optional


class Config:
    SECRET_KEY: str = os.environ.get("SECRET_KEY", "turnierverwaltung-paderborn-dev-key-2026")
    STORAGE_TYPE: str = os.environ.get("STORAGE_TYPE", "auto").lower()
    DATASTORE_PROJECT_ID: Optional[str] = os.environ.get("DATASTORE_PROJECT_ID")
    DATASTORE_TOURNAMENT_ID: str = os.environ.get("DATASTORE_TOURNAMENT_ID", "default")
    LOCAL_DATA_FILE: str = os.environ.get("LOCAL_DATA_FILE", "data/tournaments.json")
    PORT: int = int(os.environ.get("PORT", "8080"))
