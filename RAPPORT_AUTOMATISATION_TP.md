# Rapport d'automatisation des Travaux Pratiques
## Plateforme CCIP — Crisis Intelligence Platform

**Centre Royal de Télédétection Spatiale (CRTS)**
**Date :** Avril 2026
**Auteur :** M. LAAKILI

---

## Introduction

Ce rapport détaille comment chaque étape des trois travaux pratiques (TP1, TP2, TP3) de traitement d'images SAR Sentinel-1 a été automatisée au sein de la plateforme CCIP. Pour chaque TP, on présente :

- L'objectif de l'étape
- Ce qui était fait manuellement dans SNAP / QGIS
- Comment cela a été codé et automatisé
- Les entrées et sorties

L'ensemble du pipeline est implémenté dans `platform/core/pipeline.py` et orchestré par la classe `FloodPipeline`.

---

## Architecture d'orchestration

Avant de détailler chaque TP, voici comment le pipeline est déclenché et suivi.

### Classe `Job` — suivi en temps réel

Chaque analyse lance un objet `Job` identifié par un UUID court :

```python
class Job:
    def __init__(self, job_id, params):
        self.id       = job_id          # ex: "150438b22e24"
        self.status   = "pending"       # pending → running → done / error
        self.progress = 0               # 0 à 100
        self.logs     = []              # logs horodatés
        self.results  = {}              # chemins fichiers de sortie
        self.outdir   = os.path.join(RESULTS_DIR, job_id)
        os.makedirs(self.outdir, exist_ok=True)
```

À chaque étape, l'état est sauvegardé dans `results/{job_id}/state.json` :

```python
def _save_state(self):
    state = {
        "id":       self.id,
        "status":   self.status,
        "progress": self.progress,
        "logs":     self.logs[-100:],
        "results":  self.results,
        "params":   self.params,
    }
    with open(os.path.join(self.outdir, "state.json"), "w") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
```

L'interface Streamlit lit ce fichier toutes les 2 secondes pour afficher la progression en temps réel.

### Point d'entrée `FloodPipeline.run()`

La sélection automatique entre TP1 et TP2 se fait sur la présence ou non d'une image avant :

```python
def run(self):
    if self.p.get("image_before") and self.p.get("image_after"):
        # Deux images → TP1 (différence d'amplitude)
        self._run_tp1()
    elif self.p.get("image_after"):
        # Une image → TP2 (seuillage direct)
        self._run_tp2()

    # TP3 toujours exécuté après TP1 ou TP2
    self._run_tp3()
    self._generate_report()
```

---

## TP1 — Différence d'amplitude (Avant / Après)

### Objectif

Détecter les zones inondées par comparaison de deux images Sentinel-1 : une image de référence (avant la crue) et une image post-événement (après la crue).

**Principe physique :** Une surface d'eau libre est spéculaire — elle renvoie le signal radar loin du capteur. La rétrodiffusion σ₀ diminue donc fortement après une inondation. Une baisse supérieure à 3 dB entre l'image avant et l'image après indique une zone inondée.

### Ce qui se faisait manuellement

1. Ouvrir SNAP, importer les deux images
2. Appliquer manuellement la chaîne : Apply-Orbit → TNR → Calibration → Speckle Filter → Terrain Correction → LinearToFromdB
3. Exporter les deux rasters en GeoTIFF
4. Dans QGIS : charger les deux rasters, calculer la différence avec la calculatrice raster
5. Appliquer un seuil manuellement (> 3 dB = inondé)
6. Créer un composite RGB à la main

### Comment c'est automatisé

#### Étape 1 — Génération automatique des graphes XML SNAP

Pour chaque image (avant et après), un graphe XML SNAP est généré dynamiquement avec les paramètres de la session :

```python
def _write_snap_graph_preprocess(self, img, aoi, pol, px, dem, epsg, out_tif):
    path = os.path.join(self.outdir, f"snap_graph_{Path(out_tif).stem}.xml")
    with open(path, "w") as f:
        f.write(f"""<graph id="Preprocess_{slug}">
  <version>1.0</version>

  <!-- 1. Lecture de l'image Sentinel-1 GRD -->
  <node id="Read">
    <operator>Read</operator>
    <parameters><file>{img}</file></parameters>
  </node>

  <!-- 2. Découpage sur la zone d'intérêt (AOI) -->
  <node id="Subset">
    <operator>Subset</operator>
    <parameters>
      <geoRegion>POLYGON(({aoi['lon_min']} {aoi['lat_min']},
                           {aoi['lon_max']} {aoi['lat_min']},
                           {aoi['lon_max']} {aoi['lat_max']},
                           {aoi['lon_min']} {aoi['lat_max']},
                           {aoi['lon_min']} {aoi['lat_min']}))</geoRegion>
      <copyMetadata>true</copyMetadata>
    </parameters>
  </node>

  <!-- 3. Correction orbitale précise (fichiers DORIS/RESORB) -->
  <node id="Apply-Orbit-File">
    <operator>Apply-Orbit-File</operator>
    <parameters>
      <orbitType>Sentinel Precise (Auto Download)</orbitType>
      <polyDegree>3</polyDegree>
      <continueOnFail>false</continueOnFail>
    </parameters>
  </node>

  <!-- 4. Suppression du bruit thermique -->
  <node id="ThermalNoiseRemoval">
    <operator>ThermalNoiseRemoval</operator>
    <parameters>
      <selectedPolarisations>{pol}</selectedPolarisations>
      <removeThermalNoise>true</removeThermalNoise>
    </parameters>
  </node>

  <!-- 5. Calibration radiométrique → σ₀ (Sigma0) -->
  <node id="Calibration">
    <operator>Calibration</operator>
    <parameters>
      <selectedPolarisations>{pol}</selectedPolarisations>
      <outputSigmaBand>true</outputSigmaBand>
    </parameters>
  </node>

  <!-- 6. Filtre de speckle Refined Lee 7×7 -->
  <node id="Speckle-Filter">
    <operator>Speckle-Filter</operator>
    <parameters>
      <sourceBands>Sigma0_{pol}</sourceBands>
      <filter>Refined Lee</filter>
      <filterSizeX>7</filterSizeX>
      <filterSizeY>7</filterSizeY>
    </parameters>
  </node>

  <!-- 7. Correction terrain (géocodage RTC) avec DEM SRTM -->
  <node id="Terrain-Correction">
    <operator>Terrain-Correction</operator>
    <parameters>
      <sourceBands>Sigma0_{pol}</sourceBands>
      <demName>{dem}</demName>
      <demResamplingMethod>BILINEAR_INTERPOLATION</demResamplingMethod>
      <imgResamplingMethod>BILINEAR_INTERPOLATION</imgResamplingMethod>
      <pixelSpacingInMeter>{px}</pixelSpacingInMeter>
      <mapProjection>EPSG:{epsg}</mapProjection>
      <nodataValueAtSea>false</nodataValueAtSea>
    </parameters>
  </node>

  <!-- 8. Conversion linéaire → décibels : 10·log₁₀(σ₀) -->
  <node id="LinearToFromdB">
    <operator>LinearToFromdB</operator>
    <parameters>
      <sourceBands>Sigma0_{pol}</sourceBands>
    </parameters>
  </node>

  <!-- 9. Écriture GeoTIFF de sortie -->
  <node id="Write">
    <operator>Write</operator>
    <parameters>
      <file>{out_tif}</file>
      <formatName>GeoTIFF</formatName>
    </parameters>
  </node>
</graph>""")
    return path
```

Le graphe est ensuite exécuté via un appel subprocess à `gpt` (SNAP Graph Processing Tool) :

```python
def _run_snap_graph(self, graph_xml, label="SNAP"):
    cmd = [SNAP_GPT, graph_xml, "-c", "4G", "-q", "4"]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True)
    for line in proc.stdout:
        line = line.strip()
        if any(k in line for k in ["INFO","WARNING","Exception","%","cause-"]):
            self.job.log(line, "SNAP")
    proc.wait()
    return proc.returncode == 0
```

#### Étape 2 — Calcul de la différence et masque eau (script Python QGIS)

Après SNAP, un script Python est généré et exécuté dans l'environnement QGIS (qui embarque GDAL) :

```python
# --- Alignement des deux rasters ---
# L'image avant est reprojetée pour avoir exactement la même
# grille (même étendue et résolution) que l'image après
ds_after  = gdal.Open(after_db)
gt        = ds_after.GetGeoTransform()
xs, ys    = ds_after.RasterXSize, ds_after.RasterYSize

subprocess.run([gdalwarp,
    "-t_srs", f"EPSG:{epsg}",
    "-tr", str(abs(gt[1])), str(abs(gt[5])),   # même résolution
    "-te", str(gt[0]), str(gt[3]+ys*gt[5]),     # même étendue
           str(gt[0]+xs*gt[1]), str(gt[3]),
    "-r", "bilinear", "-overwrite",
    before_db, before_aligned])

# --- Lecture des arrays numpy ---
bd = ds_before.GetRasterBand(1).ReadAsArray().astype(np.float32)
ad = ds_after.GetRasterBand(1).ReadAsArray().astype(np.float32)

# Découper au minimum commun
rows = min(bd.shape[0], ad.shape[0])
cols = min(bd.shape[1], ad.shape[1])
bd, ad = bd[:rows, :cols], ad[:rows, :cols]

# --- Calcul différence (avant - après) ---
# Une inondation = diminution de σ₀ après la crue
# donc diff = before_dB - after_dB  → valeur positive si inondé
diff = bd - ad
save(diff_tif, diff)   # sauvegarde GeoTIFF

# --- Seuillage : diff > 3 dB = inondé ---
SEUIL = 3.0  # configurable (valeur absolue de la différence)
mask  = (diff > SEUIL).astype(np.int8)
# mask = 1 (inondé), 0 (non inondé)
save(out_mask, mask, gdal.GDT_Byte, nodata=255)
```

#### Étape 3 — Composite RGB fausses couleurs

```python
def stretch(a):
    # Étirement 2%–98% pour améliorer le contraste visuel
    v    = a[np.isfinite(a)]
    lo   = np.percentile(v, 2)
    hi   = np.percentile(v, 98)
    s    = np.clip((a - lo) / (hi - lo + 1e-10) * 255, 0, 255)
    s[~np.isfinite(a)] = 0
    return s.astype(np.uint8)

# RGB 3 bandes :
# Bande Rouge  = image avant étirée  (zones avant = rouge si inondé)
# Bande Verte  = image après étirée
# Bande Bleue  = image après étirée
# Résultat : zones inondées apparaissent en rouge
o = drv.Create(rgb_tif, cols, rows, 3, gdal.GDT_Byte)
o.GetRasterBand(1).WriteArray(stretch(bd))  # Rouge = avant
o.GetRasterBand(2).WriteArray(stretch(ad))  # Vert  = après
o.GetRasterBand(3).WriteArray(stretch(ad))  # Bleu  = après
```

### Fichiers produits par TP1

| Fichier | Description |
|---------|-------------|
| `before_dB.tif` | Image avant prétraitée (σ₀ en dB, UTM) |
| `after_dB.tif` | Image après prétraitée (σ₀ en dB, UTM) |
| `before_dB_aligned.tif` | Image avant reprojetée sur la grille de l'image après |
| `amplitude_diff_dB.tif` | Différence before − after (dB) |
| `mask_water.tif` | Masque binaire (1=inondé, 0=non inondé) |
| `RGB_composite.tif` | Composite fausses couleurs 3 bandes |
| `snap_graph_before_dB.xml` | Graphe SNAP image avant |
| `snap_graph_after_dB.xml` | Graphe SNAP image après |

---

## TP2 — Seuillage image unique

### Objectif

Détecter les zones inondées à partir d'une seule image SAR post-événement, en exploitant la valeur absolue du coefficient de rétrodiffusion σ₀.

**Principe physique :** L'eau libre présente un signal SAR VH caractéristiquement faible (surface spéculaire lisse). En polarisation VH, le seuil empirique σ₀_VH_dB < −26 dB permet d'identifier les surfaces en eau.

### Ce qui se faisait manuellement

1. Appliquer la même chaîne de prétraitement SNAP
2. Ajouter un opérateur BandMaths dans SNAP avec l'expression `Sigma0_VH_db < -26 ? 1 : 0`
3. Exporter le masque binaire

### Comment c'est automatisé

TP2 intègre la totalité dans **un seul graphe SNAP**, incluant le seuillage via l'opérateur BandMaths :

```python
def _write_snap_graph_tp2(self, img, aoi, pol, px, dem, seuil_db, epsg, out_mask):
    path = os.path.join(self.outdir, "snap_graph_tp2.xml")

    # IMPORTANT : le caractère < doit être échappé en &lt; dans le XML
    # Un < non échappé provoque une erreur "SNAP exited with code 1"
    expr = f"Sigma0_{pol}_db &lt; {seuil_db} ? 1 : 0"

    with open(path, "w") as f:
        f.write(f"""<graph id="TP2_InondationWorkflow">
  <version>1.0</version>
  <node id="Read">...</node>
  <node id="Subset">...</node>
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
      <demName>{dem}</demName>
      <pixelSpacingInMeter>{px}</pixelSpacingInMeter>
      <mapProjection>EPSG:{epsg}</mapProjection>
    </parameters>
  </node>
  <node id="LinearToFromdB">...</node>

  <!-- Seuillage intégré directement dans SNAP -->
  <node id="BandMaths">
    <operator>BandMaths</operator>
    <sources><sourceProduct refid="LinearToFromdB"/></sources>
    <parameters>
      <targetBands>
        <targetBand>
          <name>inondation</name>
          <type>int8</type>
          <!-- Expression : 1 si σ₀_VH_dB < seuil, sinon 0 -->
          <expression>{expr}</expression>
          <noDataValue>-1</noDataValue>
        </targetBand>
      </targetBands>
    </parameters>
  </node>

  <node id="Write">
    <parameters>
      <file>{out_mask}</file>
      <formatName>GeoTIFF</formatName>
    </parameters>
  </node>
</graph>""")
    return path
```

#### Point technique important — Échappement XML

L'opérateur de comparaison `<` dans l'expression BandMaths **doit être échappé** en `&lt;` dans le XML. Sans cet échappement, SNAP interprète le `<` comme l'ouverture d'une balise XML et retourne une erreur fatale (code 1) sans message explicite.

```python
# INCORRECT — provoque une erreur SNAP code 1
expr = f"Sigma0_{pol}_db < {seuil_db} ? 1 : 0"

# CORRECT — le parser XML accepte &lt; comme le caractère <
expr = f"Sigma0_{pol}_db &lt; {seuil_db} ? 1 : 0"
```

### Différence TP1 / TP2

| Aspect | TP1 | TP2 |
|--------|-----|-----|
| Images requises | 2 (avant + après) | 1 (après seulement) |
| Méthode | Différence d'amplitude | Seuil absolu σ₀ |
| Chaînes SNAP | 2 séparées | 1 seule avec BandMaths intégré |
| Seuil | 3 dB (relatif) | −26 dB (absolu) |
| Robustesse | Plus fiable (élimine les eaux permanentes) | Plus simple, peut inclure les eaux permanentes |

### Fichiers produits par TP2

| Fichier | Description |
|---------|-------------|
| `after_dB.tif` | Image unique prétraitée (σ₀ en dB, UTM) |
| `mask_water.tif` | Masque binaire (1=eau, 0=non eau) |
| `snap_graph_tp2.xml` | Graphe SNAP complet avec BandMaths |

---

## TP3 — Vectorisation et Statistiques

### Objectif

Transformer le masque raster binaire (issu de TP1 ou TP2) en données vectorielles géoréférencées, filtrer les artefacts, puis calculer les surfaces inondées par commune et par province sur l'ensemble du Maroc.

### Ce qui se faisait manuellement

1. Dans QGIS : appliquer un filtre de lissage sur le raster
2. Reclassifier manuellement le raster lissé
3. Lancer `gdal_polygonize` depuis le terminal
4. Dans QGIS : nettoyer les petits polygones (< 0.5 ha)
5. Intersection manuelle avec la couche GADM communes
6. Calculer les surfaces dans la table attributaire
7. Exporter les statistiques en CSV

### Comment c'est automatisé

TP3 est entièrement encapsulé dans un script Python généré dynamiquement et exécuté dans l'environnement QGIS (accès natif à GDAL/OGR).

#### Étape A — Lissage Gaussien

```python
import numpy as np
from scipy.ndimage import gaussian_filter

# Lecture du masque eau
ds   = gdal.Open(mask_water)
data = ds.GetRasterBand(1).ReadAsArray().astype(np.float32)
gt   = ds.GetGeoTransform()
prj  = ds.GetProjection()

# Lissage Gaussien σ=2.0
# Réduit le bruit pixel à pixel, comble les petits trous,
# adoucit les contours avant vectorisation
sm = gaussian_filter(data.astype(np.float64), sigma=2.0)

# Sauvegarde du raster lissé
o = drv.Create(smoothed_tif, ds.RasterXSize, ds.RasterYSize, 1, gdal.GDT_Float32)
o.SetGeoTransform(gt)
o.SetProjection(prj)
o.GetRasterBand(1).WriteArray(sm.astype(np.float32))
o.FlushCache()
```

**Paramètre σ=2.0 :** un sigma de 2 pixels correspond à un rayon de lissage de ~20 m à 10 m/pixel, suffisant pour éliminer le speckle résiduel sans dégrader les contours des grandes zones inondées.

#### Étape B — Reclassification par K-means (Natural Breaks)

```python
from scipy.cluster.vq import kmeans

ds   = gdal.Open(smoothed_tif)
data = ds.GetRasterBand(1).ReadAsArray().astype(np.float64)

# Extraire les valeurs valides (éliminer NaN/Inf)
valid = data[np.isfinite(data)].flatten()

# Sous-échantillonner si > 500 000 pixels pour la performance
samp = valid if len(valid) < 500000 else \
       valid[np.random.choice(len(valid), 500000, replace=False)]

# K-means à 2 clusters (eau / non-eau)
centroides, _ = kmeans(samp, 2)

# Le seuil optimal = moyenne des deux centroïdes
# Cette approche "Natural Breaks" s'adapte automatiquement
# aux caractéristiques radiométriques de chaque image
thr = centroides.mean()
print(f"Seuil Natural Breaks: {thr:.4f}")

# Reclassification binaire
reclass = np.where(data > thr, 2, 1).astype(np.int16)
reclass[~np.isfinite(data)] = 0   # NoData = 0
```

**Avantage :** contrairement à un seuil fixe, le K-means s'adapte à chaque image. Il n'est pas nécessaire de recalibrer manuellement le seuil d'une scène à l'autre.

#### Étape C — Vectorisation avec l'API gdal.Polygonize()

```python
from osgeo import gdal, ogr, osr

# Ouverture du raster reclassifié
ds_r    = gdal.Open(reclass_tif)
band_r  = ds_r.GetRasterBand(1)

# Création du shapefile de sortie
drv_shp = ogr.GetDriverByName("ESRI Shapefile")
if os.path.exists(raw_shp):
    drv_shp.DeleteDataSource(raw_shp)  # supprimer si existant

raw_ds  = drv_shp.CreateDataSource(raw_shp)
raw_srs = osr.SpatialReference()
raw_srs.ImportFromWkt(ds_r.GetProjection())  # même projection que le raster
raw_lay = raw_ds.CreateLayer("zi", srs=raw_srs, geom_type=ogr.wkbPolygon)

# Champ attributaire gridcode
fd = ogr.FieldDefn("gridcode", ogr.OFTInteger)
raw_lay.CreateField(fd)

# Vectorisation : chaque groupe de pixels contigus de même valeur
# devient un polygone. Le deuxième paramètre (mask band) permet
# d'utiliser la même bande comme masque pour ne vectoriser que les
# pixels non-NoData
gdal.Polygonize(band_r, band_r, raw_lay, 0, [], callback=None)

raw_ds.FlushCache()
raw_ds = None
ds_r   = None
```

> **Note technique :** L'API Python `gdal.Polygonize()` est utilisée à la place de `subprocess.run(["gdal_polygonize.py", ...])`. Le script externe dépend du Python système qui peut ne pas avoir GDAL installé, ce qui provoquait un échec silencieux (pas de fichier créé, pas d'erreur). L'API Python garantit l'utilisation du GDAL chargé dans l'environnement courant.

#### Étape D — Filtrage par surface minimale

```python
# Seuil configurable (défaut : 0.5 ha)
AREA_MIN = 0.5  # en hectares

src     = ogr.Open(raw_shp)
src_lay = src.GetLayer()
out_lay = out_ds.CreateLayer("ZI", srs=srs, geom_type=ogr.wkbPolygon)

n_ok, n_skip = 0, 0
for feat in src_lay:
    # Ne garder que les polygones de classe 2 (eau = K-means cluster haut)
    if feat.GetField("gridcode") != 2:
        continue

    geom = feat.GetGeometryRef()
    if geom is None:
        continue

    # Calcul surface en hectares
    # geom.Area() retourne des m² (projection UTM)
    area_ha = geom.Area() / 10000.0

    if area_ha < AREA_MIN:
        n_skip += 1
        continue

    # Créer le polygone filtré avec sa surface en attribut
    of = ogr.Feature(out_lay.GetLayerDefn())
    of.SetGeometry(geom.Clone())
    of.SetField("Surface_ha", round(area_ha, 4))
    out_lay.CreateFeature(of)
    n_ok += 1

print(f"Polygones: {n_ok} conservés, {n_skip} supprimés (< {AREA_MIN} ha)")
```

#### Étape E — Intersection OGR avec GADM Level 4

```python
# Reprojection des zones inondées en WGS84 (même projection que GADM)
wgs84 = osr.SpatialReference()
wgs84.ImportFromEPSG(4326)
wgs84.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)

zi_ds  = ogr.Open(zi_shp)
zi_lay = zi_ds.GetLayer()
zi_srs = zi_lay.GetSpatialRef()
tr     = osr.CoordinateTransformation(zi_srs, wgs84)

# Création de l'union de toutes les zones inondées pour
# l'intersection globale (plus efficace qu'une intersection polygone par polygone)
zi_union = ogr.Geometry(ogr.wkbMultiPolygon)
for feat in zi_lay:
    g = feat.GetGeometryRef()
    if g:
        zi_union = zi_union.Union(g)

# Pré-filtrage spatial des communes (envelope de la zone inondée)
# pour éviter de tester les 1515 communes une par une
env = zi_union.GetEnvelope()  # (xmin, xmax, ymin, ymax)
com_lay.SetSpatialFilterRect(env[0], env[2], env[1], env[3])

# Calcul de la surface d'intersection par commune
# La conversion degrés → hectares tient compte de la latitude
lat0 = (env[2] + env[3]) / 2
cos_lat = math.cos(math.radians(lat0))
ha_per_sq_deg = (111000**2) * cos_lat / 10000

stats = defaultdict(float)
for com_feat in com_lay:
    cg    = com_feat.GetGeometryRef()
    inter = cg.Intersection(zi_union)  # OGR geometry intersection
    if inter is None or inter.IsEmpty():
        continue
    area_ha = inter.Area() * ha_per_sq_deg
    if area_ha < 0.01:
        continue
    # Récupération des attributs GADM
    region  = com_feat.GetField("NAME_1")  # Région
    province= com_feat.GetField("NAME_2")  # Province
    commune = com_feat.GetField("NAME_4")  # Commune (niveau 4)
    stats[(region, province, commune)] += area_ha
```

#### Étape F — Export CSV et découpage par province

```python
# CSV global toutes communes
with open(stats_csv, "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f)
    w.writerow(["Region", "Province", "Commune", "Surface_ZI_ha"])
    for (r, p, c), a in sorted(stats.items(), key=lambda x: (x[0][1], -x[1])):
        w.writerow([r, p, c, f"{a:.2f}"])
    w.writerow(["TOTAL", "", "", f"{sum(stats.values()):.2f}"])

# Un CSV par province (pour les détails opérationnels)
by_province = defaultdict(list)
for (r, p, c), a in stats.items():
    by_province[(r, p)].append((c, a))

for (r, p), communes in sorted(by_province.items()):
    fn = os.path.join(prov_dir, p.replace(" ", "_") + ".csv")
    with open(fn, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Province", "Commune", "Surface_ZI_ha"])
        for c, a in sorted(communes, key=lambda x: -x[1]):
            w.writerow([p, c, f"{a:.2f}"])
        w.writerow(["TOTAL", "", f"{sum(a for _, a in communes):.2f}"])

total = sum(stats.values())
print(f"Surface totale: {total:,.2f} ha | {len(stats)} communes | {len(by_province)} provinces")
```

### Fichiers produits par TP3

| Fichier | Description |
|---------|-------------|
| `mask_water_smoothed.tif` | Masque après lissage Gaussien (σ=2.0) |
| `mask_water_reclass.tif` | Masque reclassifié K-means (valeurs 1/2) |
| `ZI_inondation_raw.shp` | Polygones bruts avant filtrage surface |
| `ZI_inondation.shp` | Zones inondées filtrées (projection UTM) |
| `ZI_inondation_wgs84.shp` | Zones inondées en WGS84 (pour GADM) |
| `statistiques_communes.csv` | Surface ZI par commune et province |
| `provinces/{Province}.csv` | Détail par province (un fichier chacune) |

---

## Génération automatique du rapport HTML

Après TP3, un rapport HTML est généré automatiquement à partir des statistiques calculées :

```python
def _generate_report(self):
    # Lecture des statistiques
    rows  = []
    total = 0.0
    with open(stats_csv) as f:
        for row in csv.DictReader(f):
            if row.get("Commune") and row.get("Surface_ZI_ha"):
                area = float(row["Surface_ZI_ha"])
                rows.append(row)
                total += area

    # Tri par surface décroissante
    rows.sort(key=lambda r: -float(r.get("Surface_ZI_ha", 0)))

    # Construction HTML
    html = self._build_report_html(rows, total)
    with open(rapport_html, "w", encoding="utf-8") as f:
        f.write(html)
```

Le rapport contient : résumé exécutif, top communes, top provinces, paramètres de traitement, identifiant du job.

---

## Récapitulatif — Tableau des automatisations

| Étape | Action manuelle | Automatisation CCIP |
|-------|----------------|---------------------|
| Chargement image | Drag & drop dans SNAP | Chemin saisi dans l'UI → paramètre JSON |
| Découpage AOI | Outil Subset SNAP | Polygone WKT généré depuis les coordonnées saisies |
| Apply-Orbit-File | Opérateur SNAP manuel | Nœud XML auto-généré |
| ThermalNoiseRemoval | Opérateur SNAP manuel | Nœud XML auto-généré |
| Calibration σ₀ | Opérateur SNAP manuel | Nœud XML auto-généré |
| Filtre Speckle | Opérateur SNAP manuel | Nœud XML (Refined Lee 7×7) auto-généré |
| Terrain Correction | Opérateur SNAP manuel | Nœud XML (SRTM, UTM auto) auto-généré |
| LinearToFromdB | Opérateur SNAP manuel | Nœud XML auto-généré |
| Seuillage TP2 | BandMaths SNAP manuel | Expression `&lt;` intégrée dans le graphe XML |
| Différence TP1 | Calculatrice raster QGIS | Script NumPy `bd - ad > seuil` |
| Composite RGB | Outil QGIS manuel | Script NumPy stretch + GDAL GeoTIFF 3 bandes |
| Lissage Gaussien | Plugin QGIS | `scipy.ndimage.gaussian_filter(sigma=2.0)` |
| Reclassification | Outil QGIS manuel avec seuil visuel | K-means 2 clusters (Natural Breaks adaptatif) |
| Vectorisation | `gdal_polygonize` terminal | `gdal.Polygonize()` API Python directe |
| Filtrage surface | Sélection manuelle QGIS | Boucle OGR `area_ha >= AREA_MIN` |
| Intersection communes | Outil Intersection QGIS | `ogr.Geometry.Intersection()` sur GADM L4 |
| Statistiques | Calculatrice champs QGIS | `defaultdict(float)` + conversion degrés→ha |
| Export CSV | Sauvegarde manuelle | `csv.writer` automatique multi-niveaux |
| Rapport | Rédaction manuelle | HTML auto-généré depuis les stats |

---

## Résultats de validation — Gharb 2026

Le pipeline complet a été testé sur l'événement d'inondation du Gharb (janvier–février 2026) :

| Paramètre | Valeur |
|-----------|--------|
| Image avant | S1A_IW_GRDH_1SDV_20260122T062746 |
| Image après | S1A_IW_GRDH_1SDV_20260203T062746 |
| Mode | TP1 (Avant/Après) |
| AOI | lon [−6.8, −4.8] / lat [33.5, 35.8] |
| EPSG | 32630 (UTM 30N — auto-détecté) |
| **Surface inondée** | **1 678 155 ha** |
| **Communes touchées** | **165** |
| **Provinces affectées** | **9** |
| Durée totale pipeline | **2 min 25 sec** |

### Détail par province

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

---

*Rapport généré par M. LAAKILI — CRTS — Avril 2026*
