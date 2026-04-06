#!/bin/bash
# ============================================================
# CCIP Docker — Build & Run
# Lancer ce script une fois Docker Desktop démarré
# ============================================================
set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

echo "======================================================"
echo "  CCIP Docker — Build & Run"
echo "======================================================"

# Vérifier Docker
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker n'est pas démarré."
    echo "   → Ouvrez Docker Desktop depuis le Launchpad"
    echo "   → Attendez que l'icône whale arrête de tourner"
    echo "   → Relancez ce script"
    exit 1
fi

echo "✓ Docker OK ($(docker version --format '{{.Server.Version}}' 2>/dev/null))"

# Stopper un éventuel container existant
docker stop ccip 2>/dev/null && echo "✓ Container précédent stoppé" || true
docker rm   ccip 2>/dev/null || true

# Build
echo ""
echo "▶ Build de l'image ccip:latest ..."
docker build -t ccip:latest .

echo ""
echo "✓ Image construite"

# Lancer
echo "▶ Lancement du container sur le port 8503 ..."
docker run -d \
    --name ccip \
    -p 8503:8501 \
    -v "$PROJECT_DIR/results:/app/results" \
    -v "/Applications/esa-snap:/opt/snap:ro" \
    -v "/Users/mac/Documents/Projet/CRTS/CCIP/data:/app/data/sentinel:ro" \
    -e SNAP_GPT_PATH=/opt/snap/bin/gpt \
    -e PYTHON_EXEC=python3 \
    -e GDAL_BIN="" \
    -e GDAL_POLYGONIZE=gdal_polygonize.py \
    -e GADM_PATH=/app/data/gadm/gadm41_MAR_4.shp \
    -e RESULTS_DIR=/app/results \
    -e PROJ_LIB=/usr/share/proj \
    -e PROJ_DATA=/usr/share/proj \
    -e JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64 \
    --memory=16g \
    --shm-size=2g \
    ccip:latest

echo ""
echo "======================================================"
echo "  ✓ CCIP Docker lancé !"
echo "  → http://localhost:8503"
echo "======================================================"

# Suivre les logs
echo ""
echo "▶ Logs (Ctrl+C pour quitter, le container continue) :"
docker logs -f ccip
