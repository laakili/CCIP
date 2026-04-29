# ============================================================
# CCIP – Crisis Intelligence Platform  (image autonome)
# Ubuntu 22.04 + OpenJDK 17 + ESA SNAP 13 Linux + GDAL 3
# Build 100 % automatique — aucun fichier à fournir manuellement
# ============================================================
FROM --platform=linux/amd64 ubuntu:22.04

LABEL maintainer="CRTS / Innodation" \
      version="2.1.0" \
      description="CCIP – image autonome, prête pour tout serveur Linux"

ARG DEBIAN_FRONTEND=noninteractive

ENV SNAP_GPT_PATH=/opt/snap/bin/gpt \
    PYTHON_EXEC=python3 \
    GDAL_BIN="" \
    GDAL_POLYGONIZE=gdal_polygonize.py \
    GADM_PATH=/app/data/gadm/gadm41_MAR_4.shp \
    RESULTS_DIR=/app/results \
    SENTINEL_DATA_DIR=/app/data/sentinel \
    SNAP_XMX=4G \
    USE_BLOCKS=1 \
    PROJ_LIB=/usr/share/proj \
    PROJ_DATA=/usr/share/proj \
    JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# ── 1. Packages système ───────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl wget ca-certificates \
        openjdk-17-jre-headless \
        gdal-bin python3-gdal \
        python3-numpy python3-scipy \
        python3-pip python3-setuptools python3-wheel \
        libglib2.0-0 libgomp1 zip unzip \
        nginx \
    && rm -rf /var/lib/apt/lists/*

# ── 2. ESA SNAP 13 — téléchargement automatique depuis ESA ───
# Aucun fichier à fournir manuellement
COPY docker/snap_response.varfile /tmp/snap_response.varfile
RUN echo ">>> Téléchargement ESA SNAP 13 (~1 Go) …" && \
    wget -q --show-progress \
        "https://download.esa.int/step/snap/13.0/installers/esa-snap_all_unix_13_0_0.sh" \
        -O /tmp/snap-installer.sh && \
    chmod +x /tmp/snap-installer.sh && \
    echo ">>> Installation SNAP …" && \
    /tmp/snap-installer.sh -q -varfile /tmp/snap_response.varfile && \
    rm /tmp/snap-installer.sh && \
    echo ">>> SNAP OK : $(/opt/snap/bin/gpt --version 2>&1 | head -1)"

# ── 3. Packages Python ────────────────────────────────────────
COPY requirements.txt /tmp/requirements.txt
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt

# ── 4. Application ────────────────────────────────────────────
WORKDIR /app
COPY platform/ /app/platform/

# ── 4b. Vigilance DMN fixtures (fallback offline) ────────────
RUN mkdir -p /app/frontend/src/features/vigilance-dmn/mocks
COPY frontend/src/features/vigilance-dmn/mocks/vigilances.fixtures.json \
     /app/frontend/src/features/vigilance-dmn/mocks/vigilances.fixtures.json

# ── 5. GADM Maroc — téléchargement automatique depuis GADM.org
# Télécharge le shapefile officiel niveau 4 (communes) du Maroc
RUN mkdir -p /app/data/gadm && \
    echo ">>> Téléchargement GADM Maroc niveau 4 …" && \
    wget -q "https://geodata.ucdavis.edu/gadm/gadm4.1/shp/gadm41_MAR_shp.zip" \
         -O /tmp/gadm_mar.zip && \
    unzip -j /tmp/gadm_mar.zip "gadm41_MAR_4.*" -d /app/data/gadm/ && \
    rm /tmp/gadm_mar.zip && \
    echo ">>> GADM OK :" && ls /app/data/gadm/

# ── 6. Tuiles SRTM DEM — téléchargement depuis serveur ESA/SNAP
# Couvre le Maroc : latitudes 33-36 N, longitudes 5-9 W
RUN mkdir -p "/root/.snap/auxdata/dem/SRTM 1Sec HGT" && \
    echo ">>> Téléchargement tuiles SRTM 1\" (zone Maroc) …" && \
    for LAT in 33 34 35 36; do \
      for LON in 005 006 007 008 009; do \
        TILE="N${LAT}W${LON}.SRTMGL1.hgt.zip"; \
        wget -q \
          "http://step.esa.int/auxdata/dem/SRTM%201Sec%20HGT/${TILE}" \
          -O "/root/.snap/auxdata/dem/SRTM 1Sec HGT/${TILE}" \
          && echo "  ✓ ${TILE}" \
          || echo "  ⚠ ${TILE} indisponible (SNAP le téléchargera au runtime)"; \
      done; \
    done

# ── 7. Résultats ──────────────────────────────────────────────
RUN mkdir -p /app/results /app/data/sentinel

# ── 8. Entrypoint + nginx ─────────────────────────────────────
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
COPY docker/nginx.conf /etc/nginx/sites-enabled/ccip
RUN rm -f /etc/nginx/sites-enabled/default

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

EXPOSE 8501 8502
ENTRYPOINT ["/entrypoint.sh"]
