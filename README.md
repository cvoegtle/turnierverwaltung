# 🎲 Turnierverwaltung – Spieleclub Paderborn

Webbasierte Turnierverwaltung für das Samstagsturnier des Spieleclub Paderborns. An einem Turniertag werden vier Spielrunden an 4er- und 3er-Tischen ausgetragen, um den besten Spieler zu ermitteln.

Entwickelt mit **Python**, **Flask**, **Google Cloud Datastore** und bereit für **Google Cloud Run**.

---

## 📋 Ablauf & Regeln

### Turnierablauf
- **4 Spielrunden**: In jeder Runde wird an allen Tischen das gleiche Spiel gespielt.
- **Tische**: Es wird an 4er-Tischen gespielt, bzw. an 4er- und 3er-Tischen, wenn die Spieleranzahl nicht durch 4 teilbar ist. Die Anzahl der Tische ist immer $\lceil N / 4 \rceil$.
- **Tischverteilungs-Ziele (mit absteigender Wichtigkeit)**:
  1. Jeder Spieler soll möglichst gleich oft am 3er- und am 4er-Tisch spielen.
  2. Jeder Spieler soll einmal an jeder Position (1, 2, 3, 4) spielen.
  3. Jeder Spieler soll mit möglichst vielen unterschiedlichen Mitspielern spielen.

### Wertung am Tisch
- **4er-Tisch**: 1. Platz = 5 Pkt., 2. Platz = 3 Pkt., 3. Platz = 2 Pkt., 4. Platz = 1 Pkt.
- **3er-Tisch**: 1. Platz = 5 Pkt., 2. Platz = 3 Pkt., 3. Platz = 1 Pkt.
- **Gleichstand**: Bei Gleichstand werden die Punkte der geteilten Plätze addiert und durch die Anzahl der Spieler geteilt (z.B. zwei 1. Plätze am 4er-Tisch: $(5 + 3) / 2 = 4{,}0$ Punkte für beide).

### Turnierwertung
- Die Punkte aller 4 Runden werden addiert.
- **Kein Tie-Breaker**: Spieler mit gleicher Gesamtpunktzahl teilen sich den jeweiligen Rang.

---

## 🏗️ Architektur & Clean Code

Die Business-Logik ist vollständig unabhängig von UI und Persistenz implementiert:

```
turnierverwaltung/
├── src/
│   ├── domain/               # Reine Business-Logik & Domain-Modelle
│   │   ├── player.py         # Spieler-Entität & Punktesummen
│   │   ├── game.py           # Spiel-Entität (4 Spiele)
│   │   ├── table.py          # Tisch, Sitzplätze (1..4) & Ergebnisse
│   │   ├── scoring.py        # Punkteberechnung & Gleichstand-Auflösung
│   │   ├── seating.py        # Optimierer für die Tischverteilung über 4 Runden
│   │   └── tournament.py     # Aggregat-Root für das Turnier
│   ├── persistence/          # Persistenzschicht
│   │   ├── repository.py     # Abstraktes Repository-Interface & Factory
│   │   ├── memory_repo.py    # In-Memory-Speicher (für lokale Entwicklung & Tests)
│   │   └── datastore_repo.py # Google Cloud Datastore Implementierung
│   ├── web/                  # Flask Web-UI
│   │   ├── app.py            # App-Factory
│   │   ├── routes.py         # Routen für Dashboard, Spieler, Runden, Wertung
│   │   ├── templates/        # Responsive Jinja2 Templates
│   │   └── static/           # Modernes CSS & Print-Stylesheets
│   └── config.py             # Konfigurationsklasse (Umgebungsvariablen)
├── tests/                    # Automatisierte Unit- und Integrationstests (28 Tests)
├── Dockerfile                # Multi-Worker Cloud Run Container
├── requirements.txt          # Produktionsabhängigkeiten
├── run.py                    # Lokaler Einstiegspunkt
└── spec.md                   # Originalspezifikation
```

---

## 🚀 Lokale Ausführung

### 1. Virtuelle Umgebung aktivieren & Abhängigkeiten installieren
```bash
source .venv/bin/activate
pip install -r requirements-dev.txt
```

### 2. Tests ausführen
```bash
pytest tests/ -v
```

### 3. Server starten
```bash
python run.py
```
Öffne anschließend [http://localhost:8080](http://localhost:8080) im Browser.

> **Hinweis zur Persistenz:** Standardmäßig erkennt die Anwendung automatisch (`STORAGE_TYPE=auto`), ob Google Cloud Datastore konfiguriert ist. Lokal ohne GCP-Credentials wird nahtlos der In-Memory-Speicher verwendet, sodass kein GCP-Konto für Entwicklung und Tests erforderlich ist.

---

## ☁️ Google Cloud Run Deployment

Das Projekt enthält ein für Cloud Run optimiertes `Dockerfile` mit `gunicorn`.

### Konfiguration: Nur bei Bedarf starten & max. 1 Instanz
Um Kosten zu minimieren (0 € im Leerlauf) und sicherzustellen, dass nie mehr als eine Instanz läuft:
- `--min-instances 0`: Fährt den Container auf 0 herunter, wenn keine Anfragen anstehen (Cold Start bei Aufruf in ~1-2s).
- `--max-instances 1`: Verhindert jegliches horizontales Hochskalieren über 1 Container hinaus.
- `--concurrency 80`: Die einzelne Instanz verarbeitet bis zu 80 Anfragen gleichzeitig über Gunicorn-Worker/Threads.

### 1. Schnelles Deployment mit dem Skript `deploy.sh`:
```bash
# Nutzt das aktive gcloud-Projekt oder übergibt eine Project-ID:
./deploy.sh [DEINE_GCP_PROJECT_ID]
```

### 2. Oder manuell per Google Cloud CLI:
```bash
gcloud run deploy turnierverwaltung \
    --source . \
    --region europe-west3 \
    --platform managed \
    --min-instances 0 \
    --max-instances 1 \
    --concurrency 80 \
    --allow-unauthenticated
```

### 3. IAM & Berechtigungen
Das Service-Konto von Cloud Run benötigt die Rolle `roles/datastore.user` (Cloud Datastore-Nutzer) auf dem GCP-Projekt, um auf den Google Datastore zugreifen zu können.
