"""Entry point for running the tournament web application locally."""

import logging
from src.config import Config
from src.web.app import create_app

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

app = create_app()

if __name__ == "__main__":
    cfg = Config()
    logging.info("Starte Turnierverwaltung auf Port %s (Storage: %s)...", cfg.PORT, cfg.STORAGE_TYPE)
    app.run(host="0.0.0.0", port=cfg.PORT, debug=True)
