#!/usr/bin/env bash
# ==============================================================================
# Deployment-Skript für Google Cloud Run (Turnierverwaltung Spieleclub Paderborn)
#
# Einstellungen:
# - Min Instances: 0 (Startet nur bei Aufruf -> 0 € Kosten im Leerlauf)
# - Max Instances: 1 (Nie mehr als eine Instanz gleichzeitig aktiv)
# ==============================================================================

set -euo pipefail

REGION="${GCP_REGION:-europe-west1}"
SERVICE_NAME="${GCP_SERVICE_NAME:-turnierverwaltung}"
PROJECT_ID="spieleclub-turnier-verwaltung"

if [ -z "$PROJECT_ID" ]; then
    echo "❌ Fehler: Kein GCP-Projekt gefunden."
    echo "Verwendung: ./deploy.sh [DEINE_GCP_PROJECT_ID]"
    echo "Oder vorher Projekt setzen: gcloud config set project <DEINE_GCP_PROJECT_ID>"
    exit 1
fi

echo "============================================================"
echo " 🎲 Deploye Turnierverwaltung auf Google Cloud Run"
echo " Projekt:        $PROJECT_ID"
echo " Service:        $SERVICE_NAME"
echo " Region:         $REGION"
echo " Min-Instanzen:  0 (Startet nur bei Bedarf / 0 € im Leerlauf)"
echo " Max-Instanzen:  1 (Nie mehr als 1 Instanz gleichzeitig)"
echo "============================================================"

gcloud run deploy "$SERVICE_NAME" \
    --project "$PROJECT_ID" \
    --source . \
    --region "$REGION" \
    --platform managed \
    --min-instances 0 \
    --max-instances 1 \
    --concurrency 80 \
    --allow-unauthenticated \
    --quiet

echo ""
echo "✅ Deployment erfolgreich abgeschlossen!"
