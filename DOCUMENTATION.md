# CCIP — Crisis Intelligence Platform
## Documentation Technique Complète

**Version** : 1.0
**Date** : Avril 2026
**Organisation** : Centre Royal de Télédétection Spatiale (CRTS) — Rabat, Maroc
**Auteur** : Équipe CRTS / Intelligence Satellitaire

---

## Table des matières

1. [Introduction](#1-introduction)
2. [Architecture générale](#2-architecture-générale)
3. [Installation et démarrage](#3-installation-et-démarrage)
4. [Structure des fichiers](#4-structure-des-fichiers)
5. [Configuration — config.py](#5-configuration--configpy)
6. [Pipeline de traitement](#6-pipeline-de-traitement)
   - 6.1 [TP1 — Différence d'amplitude](#61-tp1--différence-damplitude-avantaprès)
   - 6.2 [TP2 — Seuillage image unique](#62-tp2--seuillage-image-unique)
   - 6.3 [TP3 — Vectorisation et statistiques](#63-tp3--vectorisation-et-statistiques)
7. [Interface utilisateur](#7-interface-utilisateur)
   - 7.1 [Page d'accueil — app.py](#71-page-daccueil--apppy)
   - 7.2 [Module Inondation — 1_Inondation.py](#72-module-inondation--1_inondationpy)
8. [Gestion des jobs](#8-gestion-des-jobs)
9. [Couverture géographique](#9-couverture-géographique)
10. [Déploiement Docker](#10-déploiement-docker)
11. [Structure des résultats](#11-structure-des-résultats)
12. [Cas d'utilisation — Gharb 2026](#12-cas-dutilisation--gharb-2026)
13. [Dépannage](#13-dépannage)
14. [Évolutions futures](#14-évolutions-futures)

---

## 1. Introduction

CCIP (Crisis Intelligence Platform) est une plateforme web de surveillance satellitaire des crises environnementales au Maroc. Elle permet le traitement automatisé d'images radar SAR (Synthetic Aperture Radar) Sentinel-1 pour la cartographie des zones inondées à l'échelle communale.

### Capacités actuelles

| Module | Statut | Description |
|--------|--------|-------------|
| Inondation | **Actif** | Cartographie SAR Sentinel-1, TP1/TP2/TP3 |
| Incendie | En développement | Sentinel-2, NDVI |
| Séisme | Planifié | InSAR, déformation terrain |
| Tempête | Planifié | Sentinel-1 wind |
| Sécheresse | Planifié | SPI, NDVI temporel |

### Points clés

- Traitement entièrement automatisé : de l'image brute Sentinel-1 aux statistiques par commune
- Interface web Streamlit accessible sans installation côté utilisateur
- Couverture nationale : 1 515 communes marocaines (GADM Level 4)
- Déployable en production via Docker sur Linux
- Résultats disponibles en ~2–3 minutes

---

## 2. Architecture générale

```
┌─────────────────────────────────────────────────────────────┐
│  COUCHE PRÉSENTATION                                         │
│  Streamlit 1.50 + st.components.v1.html()                   │
│  Interface multimodule  |  Sélecteur 50+ zones  |  DL CSV   │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────┐
│  COUCHE MÉTIER                                               │
│  Pipeline TP1 / TP2 / TP3  |  Gestion jobs (threading)     │
│  Rapports HTML auto-générés  |  Stats communes              │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────┐
│  COUCHE TRAITEMENT                                           │
│  ESA SNAP 13.0 GPT (Java, XML batch)                        │
│  GDAL / OGR Python API  |  QGIS Python 3.12  |  scipy      │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────┐
│  COUCHE DONNÉES                                              │
│  Sentinel-1 GRD (Copernicus)  |  GADM v4.1 Maroc L4        │
│  SRTM 1Sec HGT (DEM)                                        │
└─────────────────────────────────────────────────────────────┘
```

### Flux de données

```
Image SAR (.zip)
      │
      ▼
 SNAP GPT (XML graph)
      │ Apply-Orbit → TNR → Calibration → Speckle → TC → dB
      ▼
 Raster dB (.tif)
      │
      ├── TP1: différence amplitude (before - after > 3 dB)
      └── TP2: seuillage unique (σ₀_VH_dB < -26 dB)
             │
             ▼
        mask_water.tif (binaire)
             │
             ▼
        TP3: Lissage Gaussien → K-means → gdal.Polygonize()
             │
             ▼
        ZI_inondation.shp → OGR ∩ GADM L4 → CSV + rapport HTML
```

---

## 3. Installation et démarrage

### Prérequis macOS (développement)

```bash
# 1. ESA SNAP 13.0
# Télécharger depuis: https://step.esa.int/main/download/snap-download/
# Installer dans /Applications/esa-snap/

# 2. QGIS (pour Python + GDAL)
# Télécharger depuis: https://qgis.org/fr/site/forusers/download.html
# Installer dans /Applications/QGIS.app/

# 3. Dépendances Python
pip3 install streamlit==1.50.0 pandas>=2.0.0 pyarrow>=14.0.0 \
             altair>=5.0.0 numpy>=2.0.0 jsonschema>=4.0.0 \
             referencing>=0.30.0 rpds-py>=0.10.0

# Sur Apple Silicon (arm64), forcer la réinstallation si erreur architecture:
pip3 install --force-reinstall numpy pandas pyarrow rpds-py \
             charset-normalizer tornado
```

### Démarrage rapide

```bash
cd /chemin/vers/CCIP/platform
bash start.sh
# → http://localhost:8501
```

### Vérification de l'installation

```bash
# SNAP
/Applications/esa-snap/bin/gpt --version

# QGIS Python + GDAL
/Applications/QGIS.app/Contents/MacOS/python3.12 -c "from osgeo import gdal; print(gdal.VersionInfo())"

# Streamlit
python3 -m streamlit --version
```

### Variables d'environnement (optionnel)

| Variable | Défaut macOS | Description |
|----------|-------------|-------------|
| `SNAP_GPT_PATH` | `/Applications/esa-snap/bin/gpt` | Chemin vers SNAP GPT |
| `PYTHON_EXEC` | `/Applications/QGIS.app/Contents/MacOS/python3.12` | Python QGIS |
| `GDAL_BIN` | `/Applications/QGIS.app/Contents/MacOS` | Binaires GDAL |
| `PROJ_LIB` | `.../qgis/proj` | Données de projection |
| `GADM_PATH` | `../data/gadm/gadm41_MAR_4.shp` | Shapefile GADM L4 |
| `RESULTS_DIR` | `platform/results/` | Répertoire des résultats |

---

## 4. Structure des fichiers

```
CCIP/
├── platform/
│   ├── app.py                      # Page d'accueil Streamlit (577 lignes)
│   ├── start.sh                    # Script de démarrage
│   ├── server.py                   # Serveur alternatif (Flask)
│   ├── prefill_jobs.py             # Pré-remplissage jobs de démo
│   ├── pages/
│   │   └── 1_Inondation.py         # Module Inondation UI (703 lignes)
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py               # Configuration globale (66 lignes)
│   │   └── pipeline.py             # Pipeline de traitement (775 lignes)
│   ├── core/graphs/                # Graphes XML SNAP (générés dynamiquement)
│   ├── results/                    # Résultats des jobs
│   │   └── {job_id}/              # Un répertoire par job
│   │       ├── state.json
│   │       ├── before_dB.tif
│   │       ├── after_dB.tif
│   │       ├── amplitude_diff_dB.tif
│   │       ├── RGB_composite.tif
│   │       ├── mask_water.tif
│   │       ├── mask_water_smoothed.tif
│   │       ├── mask_water_reclass.tif
│   │       ├── ZI_inondation_raw.shp
│   │       ├── ZI_inondation.shp
│   │       ├── ZI_inondation_wgs84.shp
│   │       ├── statistiques_communes.csv
│   │       ├── provinces/
│   │       │   └── {Province}.csv
│   │       └── rapport.html
│   ├── static/
│   │   ├── css/app.css
│   │   └── js/app.js
│   └── templates/
│       └── index.html
├── data/
│   └── gadm/
│       ├── gadm41_MAR_4.shp        # GADM v4.1 Maroc Level 4
│       ├── gadm41_MAR_4.dbf
│       ├── gadm41_MAR_4.prj
│       └── gadm41_MAR_4.shx
├── docker/
│   ├── entrypoint.sh
│   └── snap_response.varfile       # Réponses install silencieuse SNAP
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .dockerignore
├── RAPPORT_TECHNIQUE_CCIP.md
└── DOCUMENTATION.md                # Ce fichier
```

---

## 5. Configuration — config.py

Le fichier `platform/core/config.py` centralise toute la configuration de la plateforme. Tous les chemins d'outils sont lus depuis des variables d'environnement, avec des valeurs de repli pour macOS.

### Chemins des outils

```python
SNAP_GPT    = os.environ.get("SNAP_GPT_PATH",    "/Applications/esa-snap/bin/gpt")
PYTHON_QGIS = os.environ.get("PYTHON_EXEC",      "/Applications/QGIS.app/Contents/MacOS/python3.12")
GDAL_BIN    = os.environ.get("GDAL_BIN",         "/Applications/QGIS.app/Contents/MacOS")
GADM_DEFAULT = os.environ.get("GADM_PATH",
    os.path.join(_BASE_DIR, "data", "gadm", "gadm41_MAR_4.shp"))
```

### Environnement QGIS (adaptatif)

Sur Linux/Docker, aucune variable QGIS spécifique n'est nécessaire (GDAL est installé via apt). Sur macOS, les variables sont injectées dans le sous-processus :

```python
if platform.system() == "Linux":
    QGIS_ENV = {}
else:
    QGIS_ENV = {
        "PYTHONHOME":          "/Applications/QGIS.app/Contents/Frameworks",
        "PYTHONPATH":          "/Applications/QGIS.app/Contents/Resources/python3.11/site-packages:...",
        "DYLD_FRAMEWORK_PATH": "/Applications/QGIS.app/Contents/Frameworks",
        "PROJ_DATA":           PROJ_DATA,
        "PROJ_LIB":            PROJ_DATA,
    }
```

### Paramètres de traitement par défaut

```python
DEFAULT_PARAMS = {
    "polarisation":   "VH",
    "pixel_spacing":  10.0,
    "dem":            "SRTM 1Sec HGT",
    "speckle_filter": "Refined Lee",
    "seuil_db":       -26.0,      # Seuil de détection eau (dB)
    "area_min_ha":    0.5,        # Surface minimale des polygones (ha)
    "epsg":           32629,      # UTM 29N (Maroc Nord-Ouest)
    "aoi": {
        "lon_min": -6.8, "lat_min": 33.5,
        "lon_max": -4.8, "lat_max": 35.8
    }
}
```

---

## 6. Pipeline de traitement

Le pipeline est implémenté dans `platform/core/pipeline.py` (775 lignes). Il est exécuté dans un thread background et met à jour un fichier `state.json` en temps réel.

### 6.1 TP1 — Différence d'amplitude (Avant/Après)

**Mode** : Utilisé quand deux images (avant et après crue) sont fournies.

**Principe** : Une baisse de rétrodiffusion SAR (σ₀) indique une surface d'eau (spéculaire → signal renvoyé loin du capteur). La différence `after_dB - before_dB < -3 dB` indique une inondation.

#### Étape 1 : Prétraitement SNAP (×2 images)

```xml
<!-- Graphe XML SNAP généré dynamiquement -->
<graph>
  <node id="Apply-Orbit-File">...</node>
  <node id="ThermalNoiseRemoval">...</node>
  <node id="Calibration">
    <parameters>
      <outputSigmaBand>true</outputSigmaBand>
    </parameters>
  </node>
  <node id="Speckle-Filter">
    <parameters>
      <filter>Refined Lee</filter>
      <filterSizeX>7</filterSizeX>
      <filterSizeY>7</filterSizeY>
    </parameters>
  </node>
  <node id="Terrain-Correction">
    <parameters>
      <demName>SRTM 1Sec HGT</demName>
      <pixelSpacingInMeter>10.0</pixelSpacingInMeter>
      <mapProjection>AUTO:42001</mapProjection>  <!-- UTM auto -->
    </parameters>
  </node>
  <node id="LinearToFromdB">...</node>
</graph>
```

**Entrée** : Fichier `.zip` Sentinel-1 GRD
**Sortie** : `before_dB.tif`, `after_dB.tif` (rasters en décibels, UTM)

#### Étape 2 : Calcul différence + RGB (script QGIS Python)

```python
# diff_rgb.py — exécuté via subprocess QGIS
# 1. Alignement rasters (gdal.Warp)
# 2. Calcul différence: diff = before_dB - after_dB
# 3. Seuillage: mask_water = (diff > 3.0).astype(np.uint8)
# 4. RGB composite:
#    - Rouge  (255, 0,   0  ): zones inondées
#    - Vert   (0,   100, 50 ): non-inondées
#    - Bleu   (0,   100, 200): eau permanente
```

**Sortie** : `amplitude_diff_dB.tif`, `mask_water.tif`, `RGB_composite.tif`

---

### 6.2 TP2 — Seuillage image unique

**Mode** : Utilisé quand une seule image post-crue est disponible.

**Principe** : L'eau présente un σ₀_VH < -26 dB de manière caractéristique (surface calme, réflexion spéculaire). Ce seuil est configurable.

#### Étape 1 : SNAP GPT + BandMaths

```xml
<node id="BandMaths">
  <parameters>
    <targetBands>
      <targetBand>
        <name>water_mask</name>
        <expression>Sigma0_VH_db &lt; -26.0 ? 1 : 0</expression>
        <!-- NOTE: &lt; est l'échappement XML de < -->
      </targetBand>
    </targetBands>
  </parameters>
</node>
```

> **Important** : Le caractère `<` doit être échappé en `&lt;` dans les graphes XML SNAP. Un `<` non échappé provoque une erreur SNAP code 1.

**Sortie** : `mask_water.tif` (binaire 0/1)

---

### 6.3 TP3 — Vectorisation et statistiques

TP3 est toujours exécuté après TP1 ou TP2. Il transforme le masque raster en données vectorielles et calcule les statistiques par commune et province.

#### A — Lissage Gaussien

```python
from scipy.ndimage import gaussian_filter
data_smoothed = gaussian_filter(mask_data.astype(float), sigma=2.0)
```

**Objectif** : Réduire le bruit pixel-à-pixel avant classification.
**Sortie** : `mask_water_smoothed.tif`

#### B — Reclassification K-means Natural Breaks

```python
# Trouver le seuil optimal par K-means sur les valeurs de pixels
from sklearn.cluster import KMeans  # ou implémentation manuelle
pixels = data_smoothed[data_smoothed > 0].reshape(-1, 1)
km = KMeans(n_clusters=2, random_state=0).fit(pixels)
threshold = (km.cluster_centers_[0][0] + km.cluster_centers_[1][0]) / 2
reclass = (data_smoothed >= threshold).astype(np.uint8)
```

**Sortie** : `mask_water_reclass.tif`

#### C — Vectorisation avec gdal.Polygonize()

```python
from osgeo import gdal, ogr, osr

ds_r    = gdal.Open(reclass_tif)
band_r  = ds_r.GetRasterBand(1)
drv_shp = ogr.GetDriverByName("ESRI Shapefile")

if os.path.exists(raw_shp):
    drv_shp.DeleteDataSource(raw_shp)

raw_ds  = drv_shp.CreateDataSource(raw_shp)
raw_srs = osr.SpatialReference()
raw_srs.ImportFromWkt(ds_r.GetProjection())
raw_lay = raw_ds.CreateLayer("zi", srs=raw_srs, geom_type=ogr.wkbPolygon)

fd = ogr.FieldDefn("gridcode", ogr.OFTInteger)
raw_lay.CreateField(fd)

gdal.Polygonize(band_r, band_r, raw_lay, 0, [], callback=None)
raw_ds.FlushCache()
raw_ds = None
ds_r   = None
```

> **Important** : Utiliser l'API Python `gdal.Polygonize()` directement, et **non** `subprocess.run(["gdal_polygonize.py", ...])`. Le script externe dépend de l'environnement Python système qui peut ne pas avoir GDAL.

**Sortie** : `ZI_inondation_raw.shp`

#### D — Filtrage par surface et intersection GADM

```python
# Filtrage polygones < area_min_ha
for feat in raw_layer:
    area_ha = feat.GetGeometryRef().GetArea() / 10000
    if area_ha >= area_min_ha:
        filtered_layer.CreateFeature(feat)

# Intersection OGR avec GADM Level 4
gadm_ds    = ogr.Open(gadm_path)
gadm_layer = gadm_ds.GetLayer()
filtered_layer.Intersection(gadm_layer, result_layer)
```

**Sortie** : `ZI_inondation.shp` (UTM), `ZI_inondation_wgs84.shp` (WGS84)

#### E — Calcul statistiques

```python
# Par commune
communes = {}
for feat in result_layer:
    commune  = feat.GetField("NAME_4")
    province = feat.GetField("NAME_3")
    region   = feat.GetField("NAME_1")
    area_ha  = feat.GetGeometryRef().GetArea() / 10000
    communes[(region, province, commune)] = communes.get(..., 0) + area_ha

# Export CSV
with open(stats_csv, "w") as f:
    f.write("Region,Province,Commune,Surface_ZI_ha\n")
    for (r,p,c), ha in sorted(communes.items(), key=lambda x:-x[1]):
        f.write(f"{r},{p},{c},{ha:.2f}\n")
```

**Sorties** : `statistiques_communes.csv`, `provinces/{Province}.csv`

---

### Paramètres du pipeline

| Paramètre | Type | Défaut | Description |
|-----------|------|--------|-------------|
| `image_before` | str | — | Chemin image Sentinel-1 avant (TP1) |
| `image_after` | str | — | Chemin image Sentinel-1 après |
| `polarisation` | str | `"VH"` | Polarisation SAR utilisée |
| `pixel_spacing` | float | `10.0` | Résolution de sortie (m) |
| `dem` | str | `"SRTM 1Sec HGT"` | Modèle numérique de terrain |
| `speckle_filter` | str | `"Refined Lee"` | Filtre de speckle SNAP |
| `seuil_db` | float | `-26.0` | Seuil eau en dB (TP2) |
| `area_min_ha` | float | `0.5` | Surface min polygones (ha) |
| `epsg` | int | `32629` | Code EPSG UTM (29N ou 30N) |
| `aoi` | dict | El Gharb | Zone d'intérêt (lon/lat min/max) |

---

## 7. Interface utilisateur

### 7.1 Page d'accueil — app.py

La page d'accueil utilise `st.components.v1.html()` pour injecter du HTML/CSS/JS complet dans un iframe Streamlit. Ce choix technique est nécessaire pour contourner le parser Markdown de Streamlit qui convertit notamment `--` (tirets CSS dans `style="--accent:#..."`) en tirets cadratins.

#### Structure HTML

```
├── <style>          CSS complet (thème sombre, animations)
├── <nav.navbar>     Navigation fixe
│   ├── .nav-left    Logo CRTS + nom plateforme
│   └── .nav-right   Liens de navigation
├── .left-brand      Logo CRTS + tag (positionné à gauche)
├── .main-content    Contenu centré
│   ├── .star-field  130 étoiles animées (JS)
│   ├── .orbital     Système orbital CSS
│   ├── h1           "Crisis Intelligence Platform"
│   ├── .pills       Tags technologie
│   └── .crisis-grid Grille 5 modules
└── <script>         Animation étoiles + orbital
```

#### Classes CSS des modules de crise

Les modules utilisent des classes dédiées au lieu de propriétés CSS personnalisées (`--accent`) qui sont incompatibles avec le parser Markdown :

| Classe | Couleur | Module |
|--------|---------|--------|
| `card-flood` | `#2196f3` (bleu) | Inondation (actif) |
| `card-fire` | `#ff5722` (orange-rouge) | Incendie |
| `card-quake` | `#9c27b0` (violet) | Séisme |
| `card-storm` | `#00bcd4` (cyan) | Tempête |
| `card-drought` | `#ff9800` (orange) | Sécheresse |

---

### 7.2 Module Inondation — 1_Inondation.py

#### Sidebar

```python
# Mode de traitement
mode = st.sidebar.selectbox("Mode", ["Avant/Après (TP1)", "Image unique (TP2)"])

# Sélecteur de zone géographique
zone = st.sidebar.selectbox("Zone géographique", list(MAROC_ZONES.keys()))
if MAROC_ZONES[zone]:
    lon_min, lat_min, lon_max, lat_max = MAROC_ZONES[zone]

# Détection UTM automatique
lon_center = (lon_min + lon_max) / 2
auto_epsg = 32629 if lon_center < -6.0 else 32630
utm_label = "UTM Zone 29N" if auto_epsg == 32629 else "UTM Zone 30N"
st.sidebar.caption(f"Projection détectée : **EPSG:{auto_epsg}** ({utm_label})")

# Paramètres avancés (expandable)
with st.sidebar.expander("Paramètres avancés"):
    seuil_db   = st.slider("Seuil eau (dB)", -35.0, -15.0, -26.0)
    area_min   = st.number_input("Surface min. (ha)", 0.1, 10.0, 0.5)
    pol        = st.selectbox("Polarisation", ["VH", "VV"])
```

#### Lancement et suivi d'un job

```python
if st.button("Lancer l'analyse"):
    job_id = start_pipeline(params)

# Boucle de suivi (refresh 2s)
while job["status"] == "running":
    st.progress(job["progress"] / 100)
    # Afficher les logs
    for log in job["logs"][-20:]:
        st.text(f"[{log['level']}] {log['msg']}")
    time.sleep(2)
    st.rerun()

# Résultats
if job["status"] == "done":
    df = pd.read_csv(job["results"]["stats_csv"])
    st.dataframe(df)
    st.download_button("Télécharger CSV", df.to_csv(), "statistiques.csv")
```

---

## 8. Gestion des jobs

### Cycle de vie

```
pending → running → done
                 └→ error
```

### Structure state.json

```json
{
  "id": "150438b22e24",
  "status": "done",
  "progress": 100,
  "logs": [
    {
      "ts": "22:05:32",
      "level": "INFO",
      "msg": "=== DÉMARRAGE DU PIPELINE INONDATION ==="
    },
    {
      "ts": "22:05:33",
      "level": "SNAP",
      "msg": "INFO: org.esa.snap... Initializing..."
    },
    {
      "ts": "22:07:57",
      "level": "QGIS",
      "msg": "Surface totale: 1,678,155.04 ha | 164 communes | 8 provinces"
    }
  ],
  "results": {
    "before_db":      "/path/to/before_dB.tif",
    "after_db":       "/path/to/after_dB.tif",
    "diff_db":        "/path/to/amplitude_diff_dB.tif",
    "rgb":            "/path/to/RGB_composite.tif",
    "mask_water":     "/path/to/mask_water.tif",
    "zones_inondees": "/path/to/ZI_inondation.shp",
    "stats_csv":      "/path/to/statistiques_communes.csv",
    "provinces_dir":  "/path/to/provinces/",
    "rapport":        "/path/to/rapport.html"
  },
  "params": {
    "image_before":  "/chemin/S1A_...avant.zip",
    "image_after":   "/chemin/S1A_...apres.zip",
    "polarisation":  "VH",
    "seuil_db":      -26.0,
    "pixel_spacing": 10.0,
    "dem":           "SRTM 1Sec HGT",
    "area_min_ha":   0.5,
    "epsg":          32630,
    "aoi": {"lon_min": -6.8, "lat_min": 33.5, "lon_max": -4.8, "lat_max": 35.8}
  },
  "created":  "2026-03-31T22:05:32.652361",
  "finished": "2026-03-31T22:07:57.249501"
}
```

### Niveaux de logs

| Niveau | Source | Description |
|--------|--------|-------------|
| `INFO` | Pipeline Python | Messages d'état général |
| `SNAP` | ESA SNAP GPT | Sorties Java SNAP filtrées |
| `QGIS` | Script QGIS Python | Résultats traitement géo |
| `ERROR` | Toute source | Erreurs bloquantes |

### Progression

| Étape | Progression | Description |
|-------|------------|-------------|
| Démarrage | 5% | Initialisation |
| SNAP AVANT | 5–25% | Traitement image avant (TP1) |
| SNAP APRÈS | 25–45% | Traitement image après (TP1) |
| QGIS TP1/TP2 | 45–50% | Différence ou seuillage |
| TP3 | 55–90% | Vectorisation + statistiques |
| Rapport | 95–100% | Génération HTML |

---

## 9. Couverture géographique

### Détection UTM automatique

```python
lon_center = (lon_min + lon_max) / 2
auto_epsg  = 32629 if lon_center < -6.0 else 32630
```

| Zone UTM | EPSG | Longitude centre | Provinces couvertes |
|----------|------|-----------------|---------------------|
| UTM 29N | 32629 | < -6.0° | Tanger, Larache, Rabat, Casablanca, Agadir, Laâyoune |
| UTM 30N | 32630 | > -6.0° | Fès, Meknès, Oujda, Errachidia, Dakhla |

### MAROC_ZONES — extrait

```python
MAROC_ZONES = {
    # Régions (12)
    "── Régions ──": None,
    "Tanger-Tétouan-Al Hoceïma": (-5.92, 34.78, -5.00, 35.93),
    "Oriental":                  (-2.50, 32.50,  2.30, 35.20),
    "Fès-Meknès":                (-5.80, 32.50, -2.50, 35.00),
    "Rabat-Salé-Kénitra":        (-6.90, 33.50, -5.40, 34.70),
    "Béni Mellal-Khénifra":      (-7.00, 31.80, -5.00, 33.00),
    "Casablanca-Settat":         (-7.80, 32.80, -6.50, 33.90),
    "Marrakech-Safi":            (-9.80, 30.80, -6.50, 32.50),
    "Drâa-Tafilalet":            (-6.50, 29.50, -3.00, 33.50),
    "Souss-Massa":               (-10.0, 29.30, -7.30, 31.20),
    "Guelmim-Oued Noun":         (-13.5, 27.50,-8.00, 29.50),
    "Laâyoune-Sakia El Hamra":   (-17.5, 26.00,-8.00, 28.00),
    "Dakhla-Oued Ed-Dahab":      (-17.5, 21.50,-8.00, 26.00),
    # Provinces (40+)
    "── Provinces ──": None,
    "Agadir-Ida-Ou-Tanane":      (-9.80, 30.10, -9.00, 30.70),
    "Al Hoceïma":                (-4.10, 34.80, -3.60, 35.30),
    "Béni Mellal":               (-6.50, 31.90, -5.90, 32.40),
    "Chefchaouen":               (-5.30, 34.80, -4.60, 35.30),
    # ... 40+ entrées
}
```

---

## 10. Déploiement Docker

### Dockerfile (résumé)

```dockerfile
FROM ubuntu:22.04
ARG INSTALL_SNAP=true

# Dépendances système
RUN apt-get update && apt-get install -y \
    python3.12 python3-pip python3-gdal \
    openjdk-17-jre-headless curl wget unzip \
    libgdal-dev gdal-bin python3-numpy python3-scipy

# Installation SNAP 13 (silencieuse)
COPY docker/snap_response.varfile /tmp/
RUN if [ "$INSTALL_SNAP" = "true" ]; then \
    wget -q https://download.esa.int/step/snap/13.0/installers/esa-snap_all_unix_13_0_0.sh && \
    bash esa-snap_all_unix_13_0_0.sh -q -varfile /tmp/snap_response.varfile; \
    fi

# Données GADM
COPY data/gadm/ /app/data/gadm/

# Application
COPY platform/ /app/platform/
COPY requirements.txt /app/
RUN pip3 install -r /app/requirements.txt

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

ENTRYPOINT ["/entrypoint.sh"]
```

### docker-compose.yml

```yaml
version: "3.9"
services:
  ccip:
    build: .
    ports:
      - "8501:8501"
    mem_limit: 16g
    shm_size: 2g
    volumes:
      - ./platform/results:/app/platform/results
      - sentinel_data:/data/sentinel
    environment:
      - RESULTS_DIR=/app/platform/results
      - GADM_PATH=/app/data/gadm/gadm41_MAR_4.shp

  ccip-dev:
    profiles: ["dev"]
    build:
      args:
        INSTALL_SNAP: "false"
    ports:
      - "8502:8501"
    volumes:
      - /Applications/esa-snap:/snap
      - ./platform:/app/platform
    environment:
      - SNAP_GPT_PATH=/snap/bin/gpt
```

### Commandes Docker

```bash
# Production
docker compose build
docker compose up -d ccip
docker compose logs -f ccip

# Développement (SNAP monté depuis macOS)
docker compose --profile dev up ccip-dev

# Rebuild complet
docker compose build --no-cache
docker compose down && docker compose up -d
```

---

## 11. Structure des résultats

### Fichiers de sortie par job

| Fichier | Format | Mode | Description |
|---------|--------|------|-------------|
| `before_dB.tif` | GeoTIFF | TP1 | Image avant prétraitée (dB) |
| `after_dB.tif` | GeoTIFF | TP1/TP2 | Image après prétraitée (dB) |
| `amplitude_diff_dB.tif` | GeoTIFF | TP1 | Différence before−after |
| `RGB_composite.tif` | GeoTIFF 3 bandes | TP1 | Composite fausses couleurs |
| `mask_water.tif` | GeoTIFF binaire | TP1/TP2 | Masque eau (0/1) |
| `mask_water_smoothed.tif` | GeoTIFF | TP3 | Masque lissé Gaussien |
| `mask_water_reclass.tif` | GeoTIFF binaire | TP3 | Masque reclassifié K-means |
| `ZI_inondation_raw.shp` | Shapefile | TP3 | Polygones bruts (avant filtre) |
| `ZI_inondation.shp` | Shapefile | TP3 | Zones inondées (UTM, filtré) |
| `ZI_inondation_wgs84.shp` | Shapefile | TP3 | Zones inondées (WGS84) |
| `statistiques_communes.csv` | CSV | TP3 | Surface ZI par commune |
| `provinces/{nom}.csv` | CSV | TP3 | Détail par province |
| `rapport.html` | HTML | TP3 | Rapport complet auto-généré |
| `state.json` | JSON | Tous | État et logs du job |

### Format statistiques_communes.csv

```csv
Region,Province,Commune,Surface_ZI_ha
Tanger - Tétouan,Chefchaouen,Bab Taza,30082.93
Tanger - Tétouan,Chefchaouen,Zoumi,28638.81
...
```

---

## 12. Cas d'utilisation — Gharb 2026

### Contexte

Inondations exceptionnelles dans le bassin du Gharb et du Loukkos suite aux fortes précipitations de janvier-février 2026.

### Données utilisées

| Paramètre | Valeur |
|-----------|--------|
| Image avant | S1A_IW_GRDH_1SDV_20260122T062746 |
| Image après | S1A_IW_GRDH_1SDV_20260203T062746 |
| Mode | TP1 (Avant/Après) |
| Polarisation | VH |
| AOI | lon [-6.8, -4.8], lat [33.5, 35.8] |
| Projection | EPSG:32630 (UTM 30N, auto-détectée) |
| DEM | SRTM 1Sec HGT |

### Résultats

| Métrique | Valeur |
|---------|--------|
| Surface inondée totale | 1 678 155 ha |
| Communes touchées | 165 |
| Provinces affectées | 9 |
| Temps de traitement | ~2.5 minutes |

### Top provinces

| Province | Surface (ha) | Part (%) |
|---------|-------------|---------|
| Chefchaouen | 417 584 | 24.9% |
| Larache | 277 017 | 16.5% |
| Sidi Kacem | 267 625 | 15.9% |
| Tétouan | 246 123 | 14.7% |
| Kénitra | 228 513 | 13.6% |
| Taounate | 111 730 | 6.7% |
| Tanger-Assilah | 91 337 | 5.4% |
| Fahs Anjra | 38 226 | 2.3% |

### ID Job

```
Job ID   : 150438b22e24
Créé     : 2026-03-31T22:05:32
Terminé  : 2026-03-31T22:07:57
Durée    : 2 min 25 sec
```

---

## 13. Dépannage

### Erreur : numpy/pyarrow incompatible (arm64)

**Symptôme** :
```
ImportError: dlopen(...numpy...cpython-39-darwin.so):
incompatible architecture (have 'x86_64', need 'arm64')
```

**Cause** : Packages installés sous Rosetta (x86_64) sur Mac Apple Silicon.

**Solution** :
```bash
pip3 install --upgrade --force-reinstall numpy pandas pyarrow rpds-py charset-normalizer tornado
```

---

### Erreur : SNAP code 1 (BandMaths)

**Symptôme** : `SNAP exited with code 1` lors de TP2.

**Cause** : Le caractère `<` non échappé dans le XML du graphe BandMaths.

**Solution** : Dans `pipeline.py`, utiliser `&lt;` :
```python
expr = f"Sigma0_{pol}_db &lt; {seuil_db} ? 1 : 0"
```

---

### Erreur : ZI_inondation_raw.shp not found

**Symptôme** :
```
FileNotFoundError: ZI_inondation_raw.shp: No such file or directory
```

**Cause** : L'appel `subprocess.run(["gdal_polygonize.py", ...])` échoue silencieusement si le Python système n'a pas GDAL.

**Solution** : Utiliser l'API Python `gdal.Polygonize()` directement (voir section 6.3.C).

---

### Erreur : JSONDecodeError sur state.json

**Symptôme** : `json.JSONDecodeError: Expecting value: line 1 column 1`

**Cause** : Lecture du fichier pendant qu'il est en cours d'écriture.

**Solution** :
```python
with open(state_file) as f:
    content = f.read().strip()
    state = json.loads(content) if content else {}
```

---

### SNAP — avertissement SRTM (normal)

```
WARNING: http error: http://step.esa.int/auxdata/dem/SRTMGL1/N35W008.SRTMGL1.hgt.zip
```

Ce message est **normal** si le fichier DEM est déjà en cache local. SNAP retente depuis le cache automatiquement.

---

### QGIS ENV sur Linux

Sur Linux/Docker, `QGIS_ENV = {}` (dictionnaire vide). Ne pas injecter les variables macOS dans l'environnement Linux.

---

## 14. Évolutions futures

### Court terme

- [ ] Téléchargement automatique depuis Copernicus Data Space Ecosystem (CDSE)
- [ ] Visualisation raster interactive (Leaflet.js + COG)
- [ ] Comparaison côte-à-côte avant/après dans l'UI
- [ ] Export PDF du rapport de crise
- [ ] Authentification utilisateurs (Auth0 ou LDAP)

### Moyen terme

- [ ] Module **Incendie** : Sentinel-2, indices NBR/NDVI, périmètre brûlé
- [ ] Module **Séisme** : InSAR différentiel, carte de déformation
- [ ] Base de données historique (PostgreSQL + PostGIS)
- [ ] API REST pour intégration avec d'autres systèmes
- [ ] Multi-jobs parallèles (Celery + Redis)
- [ ] Notifications email/SMS en fin de traitement

### Long terme

- [ ] Module **Sécheresse** : SPI, anomalie NDVI, suivi temporel
- [ ] Module **Tempête** : Sentinel-1 vitesse vent, trajectoires
- [ ] Détection automatique par Deep Learning (U-Net, segmentation)
- [ ] Intégration MODIS, Landsat, Sentinel-2
- [ ] Dashboard national temps réel (WebSocket)
- [ ] Application mobile (React Native)

---

## Annexe A — Spécifications Sentinel-1

| Paramètre | Valeur |
|-----------|--------|
| Satellite | Sentinel-1A / 1B |
| Mode | IW (Interferometric Wide Swath) |
| Produit | GRDH (Ground Range Detected High resolution) |
| Polarisation | VH (vertical émis, horizontal reçu) |
| Résolution spatiale | 10 × 10 m (après TC) |
| Fauchée | 250 km |
| Revisit | 6 jours (1A) / 12 jours (1B) |
| Source | Copernicus Open Access Hub (gratuit) |

## Annexe B — Chaîne de traitement SNAP détaillée

| Opérateur | Fonction | Paramètres clés |
|-----------|----------|-----------------|
| Apply-Orbit-File | Correction orbite précise | Auto (DORIS/RESORB) |
| ThermalNoiseRemoval | Suppression bruit thermique | removeThermalNoise=true |
| Calibration | Conversion DN → σ₀ | outputSigmaBand=true |
| Speckle-Filter | Réduction speckle | Refined Lee, 7×7 pixels |
| Terrain-Correction | Correction géométrique RTC | SRTM 1Sec HGT, 10m, AUTO:42001 |
| LinearToFromdB | Conversion linéaire → dB | σ₀ → 10·log₁₀(σ₀) |

## Annexe C — Fichier requirements.txt

```
streamlit==1.50.0
pandas>=2.0.0
pyarrow>=14.0.0
altair>=5.0.0
numpy>=2.0.0
jsonschema>=4.0.0
referencing>=0.30.0
rpds-py>=0.10.0
```

> Note : GDAL, numpy et scipy sont installés via `apt` (python3-gdal, python3-numpy, python3-scipy) dans Docker pour éviter la compilation depuis les sources.

---

*Documentation générée automatiquement — CRTS / CCIP v1.0 — Avril 2026*
