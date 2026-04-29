# RAPPORT TECHNIQUE — CRTS Crisis Intelligence Platform (CCIP)
## Module Gestion de Crise Inondation par Imagerie SAR Sentinel-1

---

| Champ            | Valeur                                                        |
|------------------|---------------------------------------------------------------|
| **Organisme**    | Centre Royal de Télédétection Spatiale (CRTS)                |
| **Projet**       | CRTS Crisis Intelligence Platform — CCIP v1.0                |
| **Module**       | Détection et cartographie des zones inondées                  |
| **Date**         | Mars 2026                                                     |
| **Version**      | 1.0.0                                                         |
| **Plateforme**   | Streamlit + ESA SNAP 13 + GDAL 3.12 + Python 3.12            |
| **Déploiement**  | Local macOS / Docker (Ubuntu 22.04)                          |

---

## TABLE DES MATIÈRES

1. [Introduction et contexte](#1-introduction-et-contexte)
2. [Architecture générale du système](#2-architecture-générale-du-système)
3. [Stack technologique](#3-stack-technologique)
4. [Données d'entrée](#4-données-dentrée)
5. [Pipeline de traitement — TP1 : Différence d'amplitude avant/après](#5-pipeline-tp1--différence-damplitude-avantaprès)
6. [Pipeline de traitement — TP2 : Seuillage image unique](#6-pipeline-tp2--seuillage-image-unique)
7. [Pipeline de traitement — TP3 : Vectorisation et statistiques](#7-pipeline-tp3--vectorisation-et-statistiques)
8. [Interface utilisateur](#8-interface-utilisateur)
9. [Gestion des jobs et persistance](#9-gestion-des-jobs-et-persistance)
10. [Résultats et sorties](#10-résultats-et-sorties)
11. [Résultats obtenus — Cas réel Maroc 2026](#11-résultats-obtenus--cas-réel-maroc-2026)
12. [Déploiement Docker](#12-déploiement-docker)
13. [Configuration et paramètres](#13-configuration-et-paramètres)
14. [Couverture géographique et projections](#14-couverture-géographique-et-projections)
15. [Limitations et recommandations](#15-limitations-et-recommandations)
16. [Structure des fichiers](#16-structure-des-fichiers)

---

## 1. Introduction et contexte

### 1.1 Contexte général

Les inondations constituent l'une des catastrophes naturelles les plus fréquentes et dévastatrices au Maroc, affectant régulièrement les plaines côtières (Gharb, Loukkos, Moulouya) et les zones de piedmont atlasiques. La cartographie rapide des zones inondées est un enjeu critique pour la gestion de crise, l'évaluation des dommages et l'aide à la décision.

L'imagerie radar à synthèse d'ouverture (SAR — Synthetic Aperture Radar) des satellites Sentinel-1 de l'ESA présente des avantages uniques pour ce contexte :
- **Indépendance des conditions météorologiques** : le radar traverse les nuages
- **Indépendance de l'éclairage solaire** : acquisition jour et nuit
- **Sensibilité à l'eau** : la surface d'eau libre produit une rétrodiffusion très faible (< −26 dB en polarisation VH)
- **Résolution décamétrique** : 10 m après correction terrain

### 1.2 Objectifs de la plateforme

La CRTS Crisis Intelligence Platform (CCIP) est une plateforme opérationnelle de gestion de crises environnementales par imagerie satellitaire. Son module inondation permet :

1. **Traitement automatisé** des images Sentinel-1 GRD (TP1 et TP2)
2. **Cartographie** des zones inondées à 10 m de résolution
3. **Vectorisation** des polygones d'inondation (TP3)
4. **Statistiques** par commune, province et région administrative
5. **Génération de rapports** HTML téléchargeables
6. **Historique des jobs** et traçabilité des traitements

### 1.3 Cas d'application

La plateforme a été développée et validée sur l'événement d'inondation de **janvier–février 2026** ayant affecté les régions du nord du Maroc (Gharb, Tanger-Tétouan-Al Hoceïma, Rabat-Salé-Kénitra).

---

## 2. Architecture générale du système

### 2.1 Vue d'ensemble

```
┌─────────────────────────────────────────────────────────────┐
│                    INTERFACE UTILISATEUR                     │
│              Streamlit (app.py + 1_Inondation.py)           │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                   PIPELINE CORE                              │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │   TP1/TP2    │  │     TP3      │  │    Rapport HTML   │  │
│  │  ESA SNAP    │  │  GDAL/QGIS   │  │   Génération     │  │
│  │  GPT Graphs  │  │  Python API  │  │   stats/cartes   │  │
│  └──────┬───────┘  └──────┬───────┘  └──────────────────┘  │
│         │                  │                                  │
└─────────┼──────────────────┼──────────────────────────────── ┘
          │                  │
┌─────────▼──────────────────▼──────────────────────────────── ┐
│                   DONNÉES                                     │
│  Sentinel-1 GRD  │  GADM v4.1 MAR  │  SRTM DEM  │  Results  │
└───────────────────────────────────────────────────────────────┘
```

### 2.2 Flux de données

```
Image S1 GRD (.zip/.SAFE)
        │
        ▼
[SNAP GPT] ─── Apply Orbit File
        │
        ▼
[SNAP GPT] ─── Thermal Noise Removal
        │
        ▼
[SNAP GPT] ─── Calibration → Sigma0 VH
        │
        ▼
[SNAP GPT] ─── Speckle Filter (Refined Lee 7×7)
        │
        ▼
[SNAP GPT] ─── Terrain Correction (SRTM, 10m, UTM 29/30N)
        │
        ▼
[SNAP GPT] ─── Linear → dB  (ou BandMaths seuillage TP2)
        │
        ▼  (TP1: différence avant/après)
[GDAL Python] ── Gaussian Smoothing σ=2.0
        │
        ▼
[GDAL Python] ── K-means Natural Breaks (2 classes)
        │
        ▼
[GDAL Python] ── gdal.Polygonize() → ZI_inondation.shp
        │
        ▼
[OGR Python] ─── Intersection avec GADM L4 (1515 communes)
        │
        ▼
[Python CSV] ─── statistiques_communes.csv
        │         provinces/ (CSV par province)
        ▼
[Jinja HTML] ─── rapport.html (téléchargeable)
```

### 2.3 Classes principales

#### `Job` (core/pipeline.py)
Représente un job de traitement. Gère l'état, les logs, la progression et la persistance sur disque.

| Attribut   | Type   | Description                                    |
|------------|--------|------------------------------------------------|
| `id`       | str    | Identifiant UUID 12 caractères                 |
| `status`   | str    | `pending` → `running` → `done` / `error`       |
| `progress` | int    | Pourcentage d'avancement (0–100)               |
| `logs`     | list   | Historique des messages horodatés              |
| `results`  | dict   | Chemins des fichiers produits                  |
| `params`   | dict   | Paramètres du traitement                       |
| `outdir`   | str    | Dossier de sortie `results/<job_id>/`          |

#### `FloodPipeline` (core/pipeline.py)
Orchestre le pipeline complet TP1 + TP2 + TP3.

| Méthode                     | Rôle                                         |
|-----------------------------|----------------------------------------------|
| `run()`                     | Point d'entrée, dispatch TP1 ou TP2 + TP3   |
| `_run_tp1()`                | Pipeline avant/après (différence amplitude)  |
| `_run_tp2()`                | Pipeline image unique (seuillage)            |
| `_run_tp3()`                | Vectorisation + statistiques spatiales       |
| `_write_snap_graph_tp2()`   | Génère le XML SNAP pour TP2                  |
| `_write_snap_graph_preprocess()` | Génère XML SNAP pour TP1 (avant/après) |
| `_write_diff_rgb_script()`  | Script GDAL pour composite RGB TP1          |
| `_write_tp3_script()`       | Script GDAL/OGR pour TP3                    |
| `_run_snap_graph()`         | Exécute SNAP GPT en subprocess              |
| `_run_qgis_script()`        | Exécute script Python QGIS en subprocess    |
| `_generate_report()`        | Génère le rapport HTML final                |
| `_find_gadm()`              | Localise le fichier GADM communes           |

---

## 3. Stack technologique

### 3.1 Logiciels et versions

| Composant          | Version  | Rôle                                              |
|--------------------|----------|---------------------------------------------------|
| **Python**         | 3.9      | Runtime Streamlit (interface)                     |
| **Python QGIS**    | 3.12     | Runtime GDAL/OGR/OSR (traitement géospatial)      |
| **Streamlit**      | 1.50.0   | Framework interface web                           |
| **ESA SNAP**       | 13.0.0   | Traitement SAR Sentinel-1 (GPT graphs)            |
| **GDAL**           | 3.12.0   | Traitement raster/vecteur                         |
| **QGIS**           | 3.44     | Environnement Python géospatial                   |
| **NumPy**          | 2.0.2    | Calcul matriciel raster                           |
| **SciPy**          | 1.17.0   | Lissage gaussien, K-means Natural Breaks          |
| **Pandas**         | 2.3.3    | Manipulation CSV et tableaux                      |
| **PyArrow**        | 21.0.0   | Serialisation données Streamlit                   |
| **Java (OpenJDK)** | 21       | Runtime ESA SNAP                                  |

### 3.2 Bibliothèques Python principales

```python
# Traitement raster
from osgeo import gdal, ogr, osr          # GDAL 3.12 (via QGIS)
from scipy.ndimage import gaussian_filter  # Lissage
from scipy.cluster.vq import kmeans        # Natural Breaks

# Interface
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd

# Système
import subprocess, threading, json, uuid, datetime
```

---

## 4. Données d'entrée

### 4.1 Images Sentinel-1

| Paramètre           | Valeur                                    |
|---------------------|-------------------------------------------|
| **Satellite**       | Sentinel-1A / 1B / 1C                    |
| **Mode**            | IW (Interferometric Wide swath)           |
| **Type produit**    | GRD (Ground Range Detected) — Level-1    |
| **Résolution native** | 20 × 22 m (azimut × range)             |
| **Polarisation**    | VH (défaut) ou VV                        |
| **Format**          | `.zip` (SAFE) ou `.SAFE/` (dossier)      |
| **Fauchée**         | 250 km                                   |
| **Orbite**          | Descendante ou montante                  |
| **Source**          | Copernicus Data Space (dataspace.copernicus.eu) |

#### Cas réel utilisé (validation)
| Rôle   | Fichier                                                                    | Date       |
|--------|---------------------------------------------------------------------------|------------|
| Avant  | `S1C_IW_GRDH_1SDV_20260128T062655_20260128T062720_006100_00C3CC_346B.SAFE` | 28/01/2026 |
| Après  | `S1A_IW_GRDH_1SDV_20260203T062727_20260203T062752_057870_07D0B6_77D8.zip`  | 03/02/2026 |

### 4.2 Données auxiliaires

#### MNT (Modèle Numérique de Terrain)
| Option           | Source                   | Résolution | Couverture      |
|------------------|--------------------------|------------|-----------------|
| SRTM 1Sec HGT   | NASA/USGS (auto-dl SNAP) | ~30 m      | ±60° lat (défaut) |
| SRTM 3Sec        | NASA/USGS                | ~90 m      | ±60° lat        |
| Copernicus 30m   | ESA/Copernicus           | 30 m       | Global          |

> **Note** : SNAP télécharge automatiquement les tuiles DEM nécessaires depuis les serveurs ESA. Une connexion internet est requise pour les zones non encore en cache.

#### Limites administratives GADM
| Paramètre   | Valeur                                                    |
|-------------|-----------------------------------------------------------|
| **Source**  | Database of Global Administrative Areas (GADM) v4.1      |
| **Pays**    | Maroc (MAR)                                               |
| **Niveau**  | 4 (communes)                                              |
| **Entités** | 1515 communes                                             |
| **Format**  | Shapefile ESRI (`.shp`, `.dbf`, `.prj`, `.shx`)          |
| **SCR**     | WGS84 géographique (EPSG:4326)                           |
| **Fichier** | `data/gadm/gadm41_MAR_4.shp`                             |
| **Champs**  | NAME_0–4 (pays → commune), GID_0–4 (identifiants)        |

---

## 5. Pipeline TP1 — Différence d'amplitude avant/après

### 5.1 Principe

La méthode de différence d'amplitude exploite le contraste SAR entre une image acquise **avant** l'événement (fond sec) et une image acquise **après** (zones inondées). Les surfaces d'eau présentent une rétrodiffusion spéculaire (très faible), ce qui se traduit par une forte diminution de la valeur dB après inondation.

**Critère de détection :**
```
Diff_dB = Avant_dB − Après_dB > 3 dB → pixel inondé
```

### 5.2 Chaîne de prétraitement SNAP (×2 images)

Chaque image (avant et après) est traitée par le graph SNAP suivant :

```xml
Read → Subset (AOI) → Apply-Orbit-File → ThermalNoiseRemoval
  → Calibration (Sigma0) → Speckle-Filter (Refined Lee 7×7)
  → Terrain-Correction (SRTM, pixelSpacing=10m, EPSG:32629/30)
  → LinearToFromdB → Write (GeoTIFF)
```

#### Détails des opérateurs

| Opérateur              | Paramètres clés                                   | Justification                              |
|------------------------|---------------------------------------------------|--------------------------------------------|
| **Subset**             | `geoRegion`: WKT POLYGON de l'AOI                | Limiter le traitement à la zone d'intérêt  |
| **Apply-Orbit-File**   | Sentinel Precise, polyDegree=3                   | Géolocalisation sub-métrique               |
| **ThermalNoiseRemoval**| selectedPolarisations: VH                        | Suppression bruit thermique antenne        |
| **Calibration**        | outputSigmaBand=true                             | Normalisation en coefficient de rétrodiffusion Sigma0 |
| **Speckle-Filter**     | Refined Lee, 7×7                                 | Réduction du chatoiement tout en préservant les structures |
| **Terrain-Correction** | SRTM 1Sec, 10m, UTM 29N/30N                     | Correction des distorsions topographiques, géoréférencement |
| **LinearToFromdB**     | Sigma0_VH → Sigma0_VH_db                        | Conversion en décibels pour le seuillage  |

### 5.3 Calcul différence + composite RGB

Script GDAL Python (`diff_rgb.py`) généré dynamiquement :

```python
# Calcul de la différence
diff_dB = before_dB - after_dB

# Masque eau : différence > 3 dB
mask_water = (diff_dB > 3.0).astype(uint8)

# Composite RGB (diagnostic visuel)
# R = avant (fond naturel)
# G = B = après (zones sombres = eau)
# → Zones inondées apparaissent en ROUGE
RGB = [stretch(before), stretch(after), stretch(after)]
```

### 5.4 Progression du job TP1

| Étape | Progression | Description                        |
|-------|-------------|------------------------------------|
| 1     | 5%          | Traitement image AVANT (SNAP)      |
| 2     | 25%         | Traitement image APRÈS (SNAP)      |
| 3     | 45%         | Calcul différence + RGB + masque   |
| 4     | 55%–90%     | TP3 (vectorisation + stats)        |
| 5     | 95%         | Génération rapport HTML            |
| 6     | 100%        | Terminé                            |

---

## 6. Pipeline TP2 — Seuillage image unique

### 6.1 Principe

La méthode de seuillage direct utilise une seule image post-événement. Elle exploite la signature radiométrique caractéristique de l'eau libre en bande C, polarisation VH :

- **Eau libre** : Sigma0_VH_dB < −26 dB (rétrodiffusion spéculaire)
- **Végétation/sol** : Sigma0_VH_dB > −20 dB
- **Zone humide/inondée** : −30 à −20 dB (selon contexte)

**Critère de détection :**
```
Sigma0_VH_dB < −26.0 dB → pixel inondé (valeur 1)
Sigma0_VH_dB ≥ −26.0 dB → pixel non inondé (valeur 0)
```

### 6.2 Chaîne SNAP complète (graph XML)

Le graph XML TP2 intègre prétraitement + seuillage en une seule exécution :

```xml
Read → Subset → Apply-Orbit-File → ThermalNoiseRemoval
  → Calibration → Speckle-Filter → Terrain-Correction
  → LinearToFromdB → BandMaths → Write
```

L'opérateur **BandMaths** exécute l'expression :
```
Sigma0_VH_db &lt; -26.0 ? 1 : 0
```
> **Note critique** : Le caractère `<` doit être échappé en `&lt;` dans le XML — c'est le bug qui causait l'échec silencieux de SNAP (code retour 1 sans message d'erreur).

### 6.3 Sortie TP2

- `mask_water.tif` : raster binaire Int8, 1=inondé, 0=non inondé
- Résolution : 10 m (ou 20/30 m selon paramètre)
- SCR : UTM 29N (EPSG:32629) ou 30N selon longitude centre AOI
- Taille typique : 300–500 MB pour l'El Gharb

---

## 7. Pipeline TP3 — Vectorisation et statistiques

### 7.1 Étape A — Lissage gaussien

```python
from scipy.ndimage import gaussian_filter
smoothed = gaussian_filter(mask_float64, sigma=2.0)
# Sauvegardé : mask_water_smoothed.tif (Float32)
```

**Objectif** : Réduire les artefacts de pixels isolés et lisser les contours avant classification.

### 7.2 Étape B — Reclassification Natural Breaks (K-means)

```python
from scipy.cluster.vq import kmeans
centers, _ = kmeans(sample_valid_pixels, k=2)
threshold = centers.mean()
# classe 2 = inondé (valeur haute)
# classe 1 = non inondé
reclass = where(data > threshold, 2, 1)
```

**Justification** : La méthode Natural Breaks (Jenks) identifie automatiquement le seuil optimal entre les deux populations radiométriques sans hypothèse a priori, plus robuste qu'un seuil fixe pour différentes zones.

### 7.3 Étape C — Vectorisation (gdal.Polygonize)

```python
# API GDAL Python native (pas de subprocess)
gdal.Polygonize(
    band_reclass,    # bande raster source
    band_reclass,    # masque (utiliser tous les pixels ≠ nodata)
    output_layer,    # couche vecteur destination
    field_index=0,   # champ gridcode
    options=[]
)
# Filtrage : polygones < area_min_ha supprimés (défaut 0.5 ha)
```

**Sortie** : `ZI_inondation.shp` — polygones de zones inondées avec attribut `Surface_ha`.

### 7.4 Étape D — Statistiques spatiales par commune

```python
# Reprojection ZI → WGS84 (même SCR que GADM)
# Pour chaque commune GADM L4 :
#   1. Filtrage spatial (bounding box)
#   2. Intersection géométrique ZI ∩ commune
#   3. Calcul surface intersectée en ha
# Agrégation par province, région
```

**Sortie** :
- `statistiques_communes.csv` : surface ZI par commune avec hiérarchie administrative
- `provinces/<Province>.csv` : CSV par province pour export ciblé

#### Structure du CSV statistiques

| Colonne           | Type    | Description                              |
|-------------------|---------|------------------------------------------|
| `Region`          | string  | Région administrative (GADM L1)          |
| `Province`        | string  | Province (GADM L3)                       |
| `Commune`         | string  | Commune (GADM L4)                        |
| `Surface_ZI_ha`   | float   | Surface zone inondée en hectares         |

---

## 8. Interface utilisateur

### 8.1 Page d'accueil — CCIP (app.py)

Implémentée via `streamlit.components.v1.html()` pour un rendu HTML/CSS complet sans interférence du parseur markdown Streamlit.

#### Composants visuels
- **Fond spatial animé** : 130 étoiles scintillantes, grille mouvante, système orbital (satellite 🛰️ en rotation)
- **Navbar fixe** : logo CRTS, liens de navigation par type de crise, indicateur S1 opérationnel
- **Identité CRTS** : logo animé (3 anneaux concentriques tournants), nom complet
- **Titre CCIP** : fonte Orbitron, gradient blanc→bleu→#2196f3
- **Status pills** : indicateurs temps réel (SENTINEL-1, SNAP, QGIS, GADM, JRC)
- **Grille de crises** : 5 cartes (Inondation active + 4 "bientôt")

#### Navigation multipage
```python
# Carte Inondation → lien href="/Inondation"
# Navbar item → lien href="/Inondation"
# Routing Streamlit natif via st.switch_page()
```

### 8.2 Module Inondation (pages/1_Inondation.py)

#### Sidebar — Formulaire de traitement

```
┌─────────────────────────────────┐
│  🛰️ Nouveau traitement          │
│                                 │
│  Mode: [Image unique TP2 ▼]    │
│        [Avant/Après TP1]        │
│                                 │
│  Images Sentinel-1:             │
│  Image après: [chemin...]       │
│  Image avant: [chemin...]       │  (TP1 seulement)
│                                 │
│  Zone d'intérêt:                │
│  Région/Province: [menu ▼]      │
│  Lon Min [-6.8] Lon Max [-4.8]  │
│  Lat Min [33.5] Lat Max [35.8]  │
│  → EPSG:32629 (UTM 29N)         │
│                                 │
│  ⚙️ Paramètres avancés          │
│    Polarisation: [VH ▼]         │
│    Seuil: [-26 dB]              │
│    Résolution: [10m ▼]          │
│    DEM: [SRTM 1Sec HGT ▼]      │
│    Surface min: [0.5 ha]        │
│                                 │
│  📋 Pipeline de traitement      │
│                                 │
│  [🚀 LANCER LE TRAITEMENT]      │
└─────────────────────────────────┘
```

#### Sélecteur géographique

50+ zones prédéfinies organisées en :
- **12 régions** : Tanger-Tétouan-Al Hoceïma, Oriental, Fès-Meknès, Rabat-Salé-Kénitra, Béni Mellal-Khénifra, Casablanca-Settat, Marrakech-Safi, Drâa-Tafilalet, Souss-Massa, Guelmim-Oued Noun, Laâyoune-Sakia El Hamra, Dakhla-Oued Ed-Dahab
- **40+ provinces** : Kénitra, Sidi Kacem, Nador, Oujda, Fès, Marrakech, Agadir, Ouarzazate, etc.

**Détection automatique UTM** :
```python
lon_center = (lon_min + lon_max) / 2
epsg = 32629 if lon_center < -6.0 else 32630
# UTM 29N (Maroc Ouest) ou UTM 30N (Oriental/Est)
```

#### Onglets principaux

| Onglet              | Contenu                                                      |
|---------------------|--------------------------------------------------------------|
| ⏳ Traitement actif | Barre de progression, logs temps réel (auto-refresh 3s)     |
| 📊 Résultats        | Métriques, tableau communes, graphique, téléchargements      |
| 🗂️ Historique       | Tableau des jobs passés avec accès aux résultats             |
| 📖 Documentation    | Guide utilisateur intégré                                    |

---

## 9. Gestion des jobs et persistance

### 9.1 Cycle de vie d'un job

```
CRÉATION (launch_job)
    │
    ├── uuid4().hex[:12] → job_id
    ├── Job(jid, params) → status = "pending"
    ├── Thread daemon → FloodPipeline(job).run()
    │
    ▼
EXÉCUTION (thread background)
    │
    ├── status = "running"
    ├── _save_state() à chaque log/progress
    │   → results/<jid>/state.json
    │
    ▼
TERMINAISON
    ├── status = "done" | "error"
    ├── finished = datetime.now().isoformat()
    └── state.json final
```

### 9.2 Structure state.json

```json
{
  "id": "a9c2ea92b30d",
  "status": "done",
  "progress": 100,
  "logs": [
    {"ts": "21:54:25", "level": "INFO", "msg": "=== DÉMARRAGE DU PIPELINE ==="},
    {"ts": "21:55:49", "level": "SNAP", "msg": "90% done."}
  ],
  "results": {
    "before_db": "/app/results/a9c2ea92b30d/before_dB.tif",
    "after_db": "/app/results/a9c2ea92b30d/after_dB.tif",
    "mask_water": "/app/results/a9c2ea92b30d/mask_water.tif",
    "zones_inondees": "/app/results/a9c2ea92b30d/ZI_inondation.shp",
    "stats_csv": "/app/results/a9c2ea92b30d/statistiques_communes.csv",
    "rapport": "/app/results/a9c2ea92b30d/rapport.html"
  },
  "created": "2026-03-31T21:54:25.123456",
  "finished": "2026-03-31T21:56:48.654321",
  "params": {
    "image_after": "/data/sentinel/S1A_...",
    "polarisation": "VH",
    "seuil_db": -26.0,
    "pixel_spacing": 10.0,
    "epsg": 32629,
    "aoi": {"lon_min": -6.8, "lat_min": 33.5, "lon_max": -4.8, "lat_max": 35.8}
  }
}
```

### 9.3 Gestion des erreurs

| Erreur                    | Cause                              | Traitement                                    |
|---------------------------|------------------------------------|-----------------------------------------------|
| SNAP code retour 1        | XML invalide (ex: `<` non échappé) | Capturé dans `_run_snap_graph()`, loggé       |
| JSON vide (state.json)    | Écriture interrompue               | `try/except` + contenu vide → `{}`            |
| GADM introuvable          | Chemin incorrect                   | Fallback vers stats globales (surface totale) |
| DEM non disponible        | Connexion réseau SNAP              | Warning dans logs, poursuite si possible      |

---

## 10. Résultats et sorties

### 10.1 Fichiers produits par job

| Fichier                      | Format      | Description                                  |
|------------------------------|-------------|----------------------------------------------|
| `before_dB.tif`              | GeoTIFF     | Image avant, corrigée, en dB (TP1 seulement) |
| `after_dB.tif`               | GeoTIFF     | Image après, corrigée, en dB                 |
| `amplitude_diff_dB.tif`      | GeoTIFF     | Différence before–after en dB (TP1)          |
| `RGB_composite.tif`          | GeoTIFF RGB | Composite R=avant, G=B=après (TP1)           |
| `mask_water.tif`             | GeoTIFF Int8| Masque binaire zones inondées                |
| `mask_water_smoothed.tif`    | GeoTIFF F32 | Masque lissé (σ=2.0)                         |
| `mask_water_reclass.tif`     | GeoTIFF I16 | Reclassifié Natural Breaks (1/2)             |
| `ZI_inondation_raw.shp`      | Shapefile   | Polygones bruts avant filtrage surface       |
| `ZI_inondation.shp`          | Shapefile   | Polygones filtrés (> area_min ha)            |
| `ZI_inondation_wgs84.shp`    | Shapefile   | Polygones en WGS84 (pour intersect GADM)     |
| `statistiques_communes.csv`  | CSV         | Stats par commune (Surface_ZI_ha)            |
| `provinces/<Prov>.csv`       | CSV         | Stats par province (export ciblé)            |
| `rapport.html`               | HTML        | Rapport complet téléchargeable               |
| `snap_graph_tp2.xml`         | XML         | Graph SNAP généré (traçabilité)              |
| `tp3_process.py`             | Python      | Script TP3 généré (traçabilité)              |
| `state.json`                 | JSON        | État du job (persistance)                    |

### 10.2 Métriques affichées dans l'interface

- **Surface totale ZI** (ha)
- **Nombre de communes** affectées
- **Nombre de provinces** affectées
- **Top 5 communes** les plus touchées (ha)
- **Graphique** surface par province (bar chart)
- **Tableau interactif** communes (tri, filtrage)

### 10.3 Téléchargements disponibles

- `statistiques_communes.csv`
- `ZI_inondation.shp` (+ .dbf, .prj, .shx en ZIP)
- `rapport.html`

---

## 11. Résultats obtenus — Cas réel Maroc 2026

### 11.1 Contexte de l'événement

Épisode d'inondation du **28 janvier – 3 février 2026** affectant principalement les régions du nord du Maroc après des pluies exceptionnelles.

### 11.2 Résultats TP2 (image unique — 03/02/2026)

| Indicateur                 | Valeur               |
|----------------------------|----------------------|
| Image traitée              | S1A — 03/02/2026     |
| Zone d'intérêt             | El Gharb + Tanger    |
| Seuil appliqué             | −26 dB (VH)          |
| **Surface ZI totale**      | **44 351 ha**        |
| Communes affectées         | 96 communes          |
| Provinces affectées        | 9 provinces          |
| Résolution cartographie    | 10 m                 |

#### Répartition par province

| Province          | Surface ZI (ha) | % du total |
|-------------------|-----------------|------------|
| Sidi Kacem        | 22 175          | 50.0 %     |
| Larache           | 6 659           | 15.0 %     |
| Tanger-Assilah    | 5 206           | 11.7 %     |
| Kénitra           | 3 496           | 7.9 %      |
| Chefchaouen       | 2 689           | 6.1 %      |
| Autres (4 prov.)  | 4 126           | 9.3 %      |

### 11.3 Résultats TP1 (avant/après — 28/01 vs 03/02/2026)

| Indicateur                 | Valeur               |
|----------------------------|----------------------|
| Image avant                | S1C — 28/01/2026     |
| Image après                | S1A — 03/02/2026     |
| Critère détection          | Diff > 3 dB          |
| **Surface ZI totale**      | **44 351 ha**        |
| Communes affectées         | 96 communes          |
| Provinces affectées        | 9 provinces          |

> **Cohérence TP1/TP2** : Les deux méthodes convergent sur **44 351 ha**, validant la robustesse du pipeline.

### 11.4 Analyse de la rétrodiffusion

```
Statistiques globales sur la scène S1 (03/02/2026) :
  − Pixels totaux analysés    : ~370 M
  − Valeur médiane Sigma0_VH  : ~−18 dB (sol/végétation)
  − Valeur minimale           : ~−35 dB (eau libre)
  − Pixels classés inondés    : ~3.2% de la scène
  − Différence amplitude TP1  : +3.53 dB en moyenne (zones inondées)
```

---

## 12. Déploiement Docker

### 12.1 Image Docker

```dockerfile
FROM ubuntu:22.04
# OpenJDK 17 (SNAP runtime)
# GDAL 3.x + python3-gdal + python3-scipy (via apt)
# ESA SNAP 13 (installation silencieuse via varfile)
# Python packages : streamlit, pandas, pyarrow, altair...
# GADM MAR L4 intégré dans l'image → /app/data/gadm/
EXPOSE 8501
HEALTHCHECK CMD curl -f http://localhost:8501/_stcore/health
```

### 12.2 Docker Compose

```yaml
services:
  ccip:                        # Production (SNAP intégré)
    build: .
    ports: ["8501:8501"]
    volumes:
      - ./data:/app/data/sentinel   # Images S1 (input)
      - ./results:/app/results       # Résultats (persistants)
    mem_limit: 16g
    shm_size: 2g

  ccip-dev:                    # Dev macOS (SNAP monté)
    build: { args: { INSTALL_SNAP: "false" } }
    volumes:
      - /Applications/esa-snap:/opt/snap:ro
    profiles: [dev]
    ports: ["8502:8501"]
```

### 12.3 Variables d'environnement

| Variable          | Défaut Docker          | Défaut macOS                              |
|-------------------|------------------------|-------------------------------------------|
| `SNAP_GPT_PATH`   | `/opt/snap/bin/gpt`    | `/Applications/esa-snap/bin/gpt`          |
| `PYTHON_EXEC`     | `python3`              | `/Applications/QGIS.app/.../python3.12`   |
| `GDAL_POLYGONIZE` | `gdal_polygonize.py`   | (détecté via `shutil.which`)              |
| `GADM_PATH`       | `/app/data/gadm/gadm41_MAR_4.shp` | `data/gadm/gadm41_MAR_4.shp` |
| `RESULTS_DIR`     | `/app/results`         | `platform/results/`                       |
| `PROJ_LIB`        | `/usr/share/proj`      | `/Applications/QGIS.app/.../qgis/proj`   |

### 12.4 Commandes de déploiement

```bash
# Production
docker compose up --build
# → http://localhost:8501

# Développement local macOS
docker compose --profile dev up --build ccip-dev
# → http://localhost:8502

# Sans SNAP (test UI)
docker build --build-arg INSTALL_SNAP=false -t ccip:ui .
```

---

## 13. Configuration et paramètres

### 13.1 Paramètres de traitement (DEFAULT_PARAMS)

| Paramètre         | Valeur défaut     | Description                              | Plage            |
|-------------------|-------------------|------------------------------------------|------------------|
| `polarisation`    | `VH`              | Canal SAR utilisé                        | VH, VV           |
| `pixel_spacing`   | `10.0`            | Résolution sortie (mètres)               | 10, 20, 30       |
| `dem`             | `SRTM 1Sec HGT`   | Modèle numérique de terrain              | 3 options        |
| `speckle_filter`  | `Refined Lee`     | Filtre de chatoiement                    | Refined Lee      |
| `seuil_db`        | `-26.0`           | Seuil de détection eau en dB             | −40 à −10        |
| `area_min_ha`     | `0.5`             | Surface minimale des polygones           | 0.1 ha +         |
| `epsg`            | `32629`           | Projection sortie (auto-détecté)         | 32629 / 32630    |
| `aoi`             | El Gharb          | Zone d'intérêt par défaut                | Toute bbox MAR   |

### 13.2 Réglage du seuil selon le contexte

| Contexte                    | Seuil recommandé | Justification                       |
|-----------------------------|------------------|-------------------------------------|
| Inondation plaine (défaut)  | −26 dB           | Eau libre, rétrodiffusion minimale  |
| Zone semi-aride             | −22 à −24 dB     | Sol sec très réflectif              |
| Zone forestière inondée     | −20 à −22 dB     | Diffusion volumique canopée         |
| Eau rugueuse (vent)         | −18 à −20 dB     | Bragg diffusion sur vagues          |

---

## 14. Couverture géographique et projections

### 14.1 Zones UTM Maroc

| Zone UTM    | EPSG   | Méridien central | Provinces couvertes                                        |
|-------------|--------|------------------|------------------------------------------------------------|
| UTM 29N     | 32629  | 9°W              | Laâyoune, Agadir, Marrakech, Casablanca, Rabat, Tanger     |
| UTM 30N     | 32630  | 3°W              | Oriental, Nador, Berkane, Oujda, Figuig, Drâa-Est         |

**Détection automatique** : Le système calcule la longitude centrale de l'AOI et sélectionne automatiquement l'EPSG optimal :
```python
lon_center = (lon_min + lon_max) / 2
epsg = 32629 if lon_center < -6.0 else 32630
```

### 14.2 Zones prédéfinies (50+ entrées)

Le module inclut les bounding boxes de :
- 12 régions administratives du Maroc
- 40+ provinces (Kénitra, Larache, Al Hoceïma, Nador, Oujda, Meknès, Fès, Casablanca, Marrakech, Agadir, Ouarzazate, Zagora, Tiznit, Taroudant, etc.)

---

## 15. Limitations et recommandations

### 15.1 Limitations techniques

| Limitation                        | Impact                                | Solution recommandée                    |
|-----------------------------------|---------------------------------------|-----------------------------------------|
| Téléchargement DEM SNAP (internet)| Ralentit si tuiles non cachées        | Pré-télécharger les tuiles SRTM locales |
| Mémoire RAM SNAP                  | 8–16 GB requis pour scènes complètes  | Réduire l'AOI ou augmenter `-Xmx`      |
| Végétation émergente              | Confusion eau/végétation haute        | Coupler avec masque NDVI Sentinel-2    |
| Zones urbaines                    | Double-rebond = forte rétrodiffusion  | Exclure zones bâties (OSM)              |
| Ombre radar                       | Zones de relief masquées              | Utiliser deux orbites (montante+desc.) |
| Cohérence TP1                     | Décalage spatial si orbites ≠         | Vérifier même relative orbit number    |

### 15.2 Recommandations d'amélioration

1. **Masque eaux permanentes JRC** : Intégrer le JRC Global Surface Water (occurrence > 90%) pour soustraire les eaux permanentes des zones inondées cartographiées.

2. **Fusion multi-dates** : Combiner plusieurs acquisitions post-événement pour réduire les faux positifs liés aux conditions d'acquisition.

3. **Validation terrain** : Coupler avec des relevés terrain GPS ou des signalements de crise pour valider la précision cartographique.

4. **Alerte automatique** : Mettre en place un déclencheur automatique basé sur les nouvelles acquisitions Sentinel-1 (API Copernicus).

5. **Export WMS/WFS** : Publier les résultats en services OGC pour intégration dans les SIG des acteurs de la gestion de crise.

6. **Carte interactive** : Intégrer Folium/Leaflet dans l'interface pour visualisation cartographique des résultats.

---

## 16. Structure des fichiers

```
CCIP/
│
├── Dockerfile                   # Image Ubuntu 22.04 + SNAP + GDAL
├── docker-compose.yml           # Services prod (8501) et dev (8502)
├── requirements.txt             # Dépendances Python pures
├── .dockerignore                # Exclusions build Docker
│
├── platform/                    # Code source plateforme
│   ├── app.py                   # Page d'accueil CCIP (577 lignes)
│   ├── prefill_jobs.py          # Import résultats historiques
│   ├── server.py                # Serveur HTTP secondaire (port 8080)
│   ├── start.sh                 # Script démarrage local macOS
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py            # Configuration (66 lignes)
│   │   └── pipeline.py          # Pipeline TP1+TP2+TP3 (775 lignes)
│   │
│   ├── pages/
│   │   └── 1_Inondation.py      # Module flood Streamlit (703 lignes)
│   │
│   ├── static/
│   │   ├── css/app.css
│   │   └── js/app.js
│   │
│   └── templates/
│       └── index.html
│
├── data/
│   ├── gadm/                    # Données administratives Maroc
│   │   ├── gadm41_MAR_4.shp     # 1515 communes (2.2 MB)
│   │   ├── gadm41_MAR_4.dbf     # Attributs (348 KB)
│   │   ├── gadm41_MAR_4.prj     # Projection WGS84
│   │   └── gadm41_MAR_4.shx     # Index spatial
│   │
│   └── sentinel/                # Déposer les images S1 ici
│       └── README.txt
│
├── docker/
│   ├── entrypoint.sh            # Point d'entrée Docker
│   └── snap_response.varfile    # Config install silencieuse SNAP
│
└── results/                     # Sorties générées (persistant)
    └── <job_id>/
        ├── state.json
        ├── mask_water.tif
        ├── ZI_inondation.shp
        ├── statistiques_communes.csv
        ├── provinces/
        └── rapport.html
```

---

## Annexe A — Glossaire

| Terme   | Définition                                                                        |
|---------|-----------------------------------------------------------------------------------|
| **SAR** | Synthetic Aperture Radar — radar à synthèse d'ouverture                           |
| **GRD** | Ground Range Detected — niveau 1 Sentinel-1, intensité géoréférencée             |
| **IW**  | Interferometric Wide — mode d'acquisition Sentinel-1 (250 km de fauchée)         |
| **VH**  | Polarisation croisée vertical-horizontal — sensible aux surfaces d'eau libre      |
| **Sigma0** | Coefficient de rétrodiffusion normalisé (σ⁰)                                  |
| **dB**  | Décibel — échelle logarithmique de rétrodiffusion                                 |
| **GPT** | Graph Processing Tool — outil en ligne de commande ESA SNAP                      |
| **SRTM**| Shuttle Radar Topography Mission — MNT global NASA à 30/90 m                    |
| **UTM** | Universal Transverse Mercator — système de projection cartésien                   |
| **AOI** | Area of Interest — zone d'intérêt                                                 |
| **GADM**| Global Administrative Areas — base de données limites administratives             |
| **ZI**  | Zone Inondée                                                                       |

## Annexe B — Références

1. ESA Sentinel-1 Technical Guide — https://sentinel.esa.int/web/sentinel/technical-guides/sentinel-1-sar
2. ESA SNAP 13.0 Documentation — https://step.esa.int/main/toolboxes/snap/
3. Copernicus Data Space — https://dataspace.copernicus.eu/
4. GADM v4.1 — https://gadm.org/
5. JRC Global Surface Water — https://global-surface-water.appspot.com/
6. Twele et al. (2016) — "Sentinel-1-based flood mapping: a fully automated processing chain", International Journal of Remote Sensing
7. Martinis et al. (2015) — "Towards operational near real-time flood detection using a split-based automatic thresholding procedure on high resolution TerraSAR-X data", Natural Hazards and Earth System Sciences

---

*CRTS Crisis Intelligence Platform (CCIP) — v1.0 | Centre Royal de Télédétection Spatiale — Division Études & Projets | ESA SNAP · QGIS/GDAL · Sentinel-1*
