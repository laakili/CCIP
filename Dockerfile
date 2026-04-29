# ============================================================
# CCIP – Crisis Intelligence Platform  (image autonome)
# Ubuntu 22.04 + OpenJDK 17 + ESA SNAP 13 Linux + GDAL 3
# Aucun montage host requis — tout est dans l'image
# ============================================================
FROM --platform=linux/amd64 ubuntu:22.04

LABEL maintainer="CRTS / Innodation" \
      version="2.0.0" \
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

# ── 2. ESA SNAP 13 (Linux natif) ─────────────────────────────
# Placer l'installateur dans docker/snap_installer.sh avant de builder
# Télécharger depuis : https://step.esa.int/main/download/snap-download/
# → Unix (64-bit) → esa-snap_all_unix_*.sh
COPY docker/snap_response.varfile /tmp/snap_response.varfile
COPY docker/snap_installer.sh /tmp/snap-installer.sh
RUN chmod +x /tmp/snap-installer.sh \
    && /tmp/snap-installer.sh -q -varfile /tmp/snap_response.varfile \
    && rm /tmp/snap-installer.sh \
    && echo "SNAP installé : $(/opt/snap/bin/gpt --version 2>&1 | head -1)"

# ── 3. Packages Python ────────────────────────────────────────
COPY requirements.txt /tmp/requirements.txt
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt

# ── 4. Application ────────────────────────────────────────────
WORKDIR /app
COPY platform/ /app/platform/

# ── 4b. Vigilance DMN fixtures (fallback si API DMN inaccessible) ──────────
# 2_Veille.py les cherche à :
#   /app/frontend/src/features/vigilance-dmn/mocks/vigilances.fixtures.json
RUN mkdir -p /app/frontend/src/features/vigilance-dmn/mocks
COPY frontend/src/features/vigilance-dmn/mocks/vigilances.fixtures.json \
     /app/frontend/src/features/vigilance-dmn/mocks/vigilances.fixtures.json

# ── 5. GADM Maroc ─────────────────────────────────────────────
RUN mkdir -p /app/data/gadm
COPY data/gadm/ /app/data/gadm/

# ── 6. Tuiles SRTM DEM ────────────────────────────────────────
COPY snap_dem/ /tmp/srtm_tiles/
RUN mkdir -p "/root/.snap/auxdata/dem/SRTM 1Sec HGT" && \
    mv /tmp/srtm_tiles/* "/root/.snap/auxdata/dem/SRTM 1Sec HGT/" && \
    rmdir /tmp/srtm_tiles

# ── 7. Résultats ──────────────────────────────────────────────
RUN mkdir -p /app/results

# ── 8. Entrypoint ─────────────────────────────────────────────
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
COPY docker/nginx.conf /etc/nginx/sites-enabled/ccip
RUN rm -f /etc/nginx/sites-enabled/default

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

EXPOSE 8501 8502
ENTRYPOINT ["/entrypoint.sh"]
