#!/bin/bash
# ============================================================
# CCIP entrypoint – starts the Streamlit application
# ============================================================
set -e

# Ensure the results directory exists (volume might be empty)
mkdir -p "${RESULTS_DIR:-/app/results}"

echo "======================================================"
echo "  CCIP – Crisis Intelligence Platform"
echo "======================================================"
echo "  SNAP GPT  : ${SNAP_GPT_PATH}"
echo "  GDAL poly : ${GDAL_POLYGONIZE}"
echo "  GADM path : ${GADM_PATH}"
echo "  Results   : ${RESULTS_DIR}"
echo "======================================================"

cd /app/platform

# Serveur d'upload (server.py) sur port 8080
PORT=8080 python3 server.py &

# Nginx proxy : écoute 8501, route /api/ → 8080, reste → 8510
nginx &

# Streamlit sur port interne 8510
exec python3 -m streamlit run app.py \
  --server.port 8510 \
  --server.headless true \
  --server.address 127.0.0.1 \
  --server.enableStaticServing true \
  --server.maxUploadSize 4096 \
  --server.enableCORS false \
  --server.enableXsrfProtection false \
  --browser.gatherUsageStats false \
  --theme.base dark \
  --theme.primaryColor "#2196f3" \
  --theme.backgroundColor "#020b18" \
  --theme.secondaryBackgroundColor "#0d2137" \
  --theme.textColor "#d0dce8"
