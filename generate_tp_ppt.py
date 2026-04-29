from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
import pptx.util as util
import os

# ── Couleurs ──────────────────────────────────────────────────
C_BG     = RGBColor(0x0b, 0x14, 0x22)
C_CARD   = RGBColor(0x0f, 0x1e, 0x30)
C_DARK   = RGBColor(0x06, 0x10, 0x1a)
C_ACCENT = RGBColor(0x21, 0x96, 0xf3)   # bleu
C_CYAN   = RGBColor(0x00, 0xe5, 0xff)
C_GREEN  = RGBColor(0x4c, 0xaf, 0x50)
C_ORANGE = RGBColor(0xff, 0x98, 0x00)
C_RED    = RGBColor(0xf4, 0x43, 0x36)
C_WHITE  = RGBColor(0xff, 0xff, 0xff)
C_TEXT   = RGBColor(0xd0, 0xdc, 0xe8)
C_MUTED  = RGBColor(0x60, 0x80, 0x9a)
C_CODE   = RGBColor(0x26, 0x32, 0x3e)
C_TP1    = RGBColor(0x21, 0x96, 0xf3)   # bleu TP1
C_TP2    = RGBColor(0xff, 0x98, 0x00)   # orange TP2
C_TP3    = RGBColor(0x4c, 0xaf, 0x50)   # vert TP3

prs = Presentation()
prs.slide_width  = Inches(13.33)
prs.slide_height = Inches(7.5)
blank = prs.slide_layouts[6]

def slide():
    s = prs.slides.add_slide(blank)
    s.background.fill.solid()
    s.background.fill.fore_color.rgb = C_BG
    return s

def rect(s, l, t, w, h, color, line=False):
    sh = s.shapes.add_shape(1, Inches(l), Inches(t), Inches(w), Inches(h))
    sh.fill.solid(); sh.fill.fore_color.rgb = color
    if line: sh.line.color.rgb = color
    else:    sh.line.fill.background()
    return sh

def txt(s, text, l, t, w, h, size=13, color=C_TEXT, bold=False,
        italic=False, align=PP_ALIGN.LEFT, font="Calibri"):
    tb = s.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h))
    tb.word_wrap = True
    tf = tb.text_frame; tf.word_wrap = True
    p = tf.paragraphs[0]; p.alignment = align
    r = p.add_run(); r.text = text
    r.font.size = Pt(size); r.font.color.rgb = color
    r.font.bold = bold; r.font.italic = italic; r.font.name = font
    return tb

def mtxt(s, lines, l, t, w, h, size=12, color=C_TEXT, bold=False,
         align=PP_ALIGN.LEFT, font="Calibri"):
    tb = s.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h))
    tb.word_wrap = True
    tf = tb.text_frame; tf.word_wrap = True
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        r = p.add_run(); r.text = line
        r.font.size = Pt(size); r.font.color.rgb = color
        r.font.bold = bold; r.font.name = font
    return tb

def code_block(s, lines, l, t, w, h, size=9.5):
    rect(s, l, t, w, h, C_CODE)
    rect(s, l, t, 0.04, h, C_ACCENT)
    for i, line in enumerate(lines):
        if t + 0.05 + i*0.28 + 0.26 > t + h: break
        color = C_CYAN if line.startswith("def ") or line.startswith("class ") else \
                C_GREEN if line.startswith("#") else \
                C_ORANGE if '=' in line and not line.strip().startswith('#') else C_TEXT
        txt(s, line, l+0.15, t+0.08+i*0.27, w-0.2, 0.26,
            size=size, color=color, font="Consolas")

def hline(s, l, t, w, color=C_ACCENT):
    sh = s.shapes.add_shape(1, Inches(l), Inches(t), Inches(w), Inches(0.025))
    sh.fill.solid(); sh.fill.fore_color.rgb = color
    sh.line.fill.background()

def header(s, title, subtitle="", color=C_ACCENT):
    rect(s, 0, 0, 13.33, 0.07, color)
    rect(s, 0, 0.07, 0.07, 7.43, color)
    txt(s, title, 0.25, 0.15, 11, 0.65, size=28, color=C_WHITE, bold=True, font="Calibri")
    if subtitle:
        txt(s, subtitle, 0.25, 0.78, 11, 0.35, size=13, color=C_MUTED)
    hline(s, 0.25, 1.12, 5.0, color)

def badge(s, text, l, t, color):
    rect(s, l, t, len(text)*0.11+0.3, 0.32, color)
    txt(s, text, l+0.1, t+0.02, len(text)*0.11+0.1, 0.28,
        size=10, color=C_BG, bold=True, align=PP_ALIGN.CENTER)

def footer(s):
    txt(s, "CRTS — Centre Royal de Télédétection Spatiale  |  CCIP v1.0  |  Avril 2026",
        0, 7.28, 13.33, 0.22, size=8, color=C_MUTED, align=PP_ALIGN.CENTER)

# ═══════════════════════════════════════════════════════════
# SLIDE 1 — TITRE
# ═══════════════════════════════════════════════════════════
s = slide()
rect(s, 0, 0, 13.33, 0.07, C_ACCENT)
c1 = s.shapes.add_shape(9, Inches(7.8), Inches(0.8), Inches(5.2), Inches(5.2))
c1.fill.solid(); c1.fill.fore_color.rgb = RGBColor(0x0a,0x18,0x28)
c1.line.color.rgb = C_ACCENT; c1.line.width = Pt(1.2)
c2 = s.shapes.add_shape(9, Inches(8.6), Inches(1.6), Inches(3.6), Inches(3.6))
c2.fill.background(); c2.line.color.rgb = C_CYAN; c2.line.width = Pt(0.7)

rect(s, 0.5, 0.8, 1.8, 0.42, C_ACCENT)
txt(s, "CRTS", 0.5, 0.8, 1.8, 0.42, size=17, color=C_BG, bold=True, align=PP_ALIGN.CENTER)

txt(s, "Automatisation des Travaux Pratiques", 0.5, 1.5, 9.5, 0.85, size=36, color=C_WHITE, bold=True)
txt(s, "TP1  ·  TP2  ·  TP3", 0.5, 2.35, 9.5, 0.65, size=28, color=C_ACCENT, bold=True)
hline(s, 0.5, 3.1, 5.0)

txt(s, "Traitement SAR Sentinel-1 — de l'étape manuelle au pipeline automatisé", 0.5, 3.25, 8.5, 0.5, size=15, color=C_TEXT)
txt(s, "ESA SNAP  ·  GDAL / OGR Python API  ·  scipy  ·  Streamlit", 0.5, 3.8, 8.5, 0.4, size=12, color=C_MUTED)

for i, (lbl, c) in enumerate([("TP1 : Différence amplitude", C_TP1), ("TP2 : Seuillage direct", C_TP2), ("TP3 : Vectorisation stats", C_TP3)]):
    badge(s, lbl, 0.5 + i*3.5, 4.5, c)

txt(s, "M. LAAKILI  —  Avril 2026", 0.5, 6.5, 6, 0.35, size=11, color=C_MUTED, italic=True)
rect(s, 0, 7.28, 13.33, 0.22, RGBColor(0x0a,0x14,0x20))
footer(s)

# ═══════════════════════════════════════════════════════════
# SLIDE 2 — ARCHITECTURE D'ORCHESTRATION
# ═══════════════════════════════════════════════════════════
s = slide(); header(s, "Architecture d'Orchestration", "Classe Job + FloodPipeline — pipeline.py")

# Classe Job
rect(s, 0.25, 1.25, 6.0, 2.7, C_CARD)
rect(s, 0.25, 1.25, 6.0, 0.38, C_ACCENT)
txt(s, "Classe  Job  — suivi en temps réel", 0.25, 1.25, 6.0, 0.38, size=13, color=C_BG, bold=True, align=PP_ALIGN.CENTER)
code_block(s, [
    "class Job:",
    "    self.id       = job_id       # ex: '150438b22e24'",
    "    self.status   = 'pending'    # pending→running→done/error",
    "    self.progress = 0            # 0 à 100%",
    "    self.logs     = []           # logs horodatés [ts,level,msg]",
    "    self.results  = {}           # chemins fichiers de sortie",
    "    self.outdir   = RESULTS_DIR / job_id",
], 0.3, 1.7, 5.9, 2.1)

# FloodPipeline entrée
rect(s, 6.6, 1.25, 6.45, 2.7, C_CARD)
rect(s, 6.6, 1.25, 6.45, 0.38, C_GREEN)
txt(s, "FloodPipeline.run() — sélection automatique", 6.6, 1.25, 6.45, 0.38, size=13, color=C_BG, bold=True, align=PP_ALIGN.CENTER)
code_block(s, [
    "def run(self):",
    "    # Deux images → TP1 (différence amplitude)",
    "    if image_before and image_after:",
    "        self._run_tp1()",
    "    # Une image → TP2 (seuillage direct)",
    "    elif image_after:",
    "        self._run_tp2()",
    "    # TP3 toujours exécuté après TP1 ou TP2",
    "    self._run_tp3()",
    "    self._generate_report()",
], 6.65, 1.7, 6.35, 2.1)

# Cycle de vie
rect(s, 0.25, 4.1, 12.8, 1.55, C_CARD)
txt(s, "Cycle de vie d'un Job", 0.4, 4.18, 4, 0.35, size=12, color=C_ACCENT, bold=True)
states = [("PENDING", C_MUTED), ("RUNNING", C_ORANGE), ("DONE", C_GREEN), ("ERROR", C_RED)]
for i, (st, c) in enumerate(states):
    x = 0.5 + i*3.15
    rect(s, x, 4.58, 2.5, 0.38, c)
    txt(s, st, x, 4.58, 2.5, 0.38, size=13, color=C_BG, bold=True, align=PP_ALIGN.CENTER)
    if i < 3:
        txt(s, "→", x+2.5, 4.65, 0.65, 0.28, size=16, color=C_MUTED, align=PP_ALIGN.CENTER)

txt(s, "Sauvegarde automatique : results/{job_id}/state.json  à chaque étape  |  Refresh UI : st.rerun() toutes les 2 secondes", 0.4, 5.05, 12.5, 0.35, size=11, color=C_MUTED, italic=True)
footer(s)

# ═══════════════════════════════════════════════════════════
# SLIDE 3 — TP1 : PRÉSENTATION
# ═══════════════════════════════════════════════════════════
s = slide(); header(s, "TP1 — Différence d'Amplitude", "Deux images Sentinel-1 (Avant / Après)", color=C_TP1)

# Principe
rect(s, 0.25, 1.25, 6.1, 2.9, C_CARD)
rect(s, 0.25, 1.25, 0.07, 2.9, C_TP1)
txt(s, "Principe physique", 0.45, 1.32, 5.7, 0.38, size=13, color=C_TP1, bold=True)
mtxt(s, [
    "Une surface d'eau libre est spéculaire :",
    "le signal radar est renvoyé loin du capteur.",
    "",
    "→  σ₀ diminue fortement après une inondation",
    "→  Seuil : before_dB − after_dB  >  3 dB",
    "→  Pixels > seuil = zone inondée",
    "",
    "Résultat : masque binaire mask_water.tif",
], 0.45, 1.75, 5.7, 3.0, size=12, color=C_TEXT)

# Ce qui était manuel vs automatisé
rect(s, 6.6, 1.25, 6.45, 2.9, C_CARD)
rect(s, 6.6, 1.25, 0.07, 2.9, C_ORANGE)
txt(s, "Manuel  →  Automatisé", 6.8, 1.32, 6.1, 0.38, size=13, color=C_ORANGE, bold=True)
rows = [
    ("Ouvrir SNAP + importer", "Chemin image → paramètre JSON"),
    ("Appliquer 6 opérateurs", "Graphe XML auto-généré"),
    ("Exporter GeoTIFF", "Sortie directe pipeline"),
    ("Calc. diff. QGIS raster", "NumPy : bd − ad > seuil"),
    ("Créer RGB manuellement", "Script GDAL 3 bandes auto"),
]
for i, (man, auto) in enumerate(rows):
    y = 1.75 + i * 0.41
    bg = C_CARD if i%2==0 else RGBColor(0x12,0x24,0x38)
    rect(s, 6.6, y, 6.45, 0.39, bg)
    txt(s, "✗  " + man, 6.72, y+0.04, 3.0, 0.32, size=10, color=RGBColor(0xef,0x53,0x50))
    txt(s, "✓  " + auto, 9.75, y+0.04, 3.2, 0.32, size=10, color=C_GREEN)

# Flux
rect(s, 0.25, 4.25, 12.8, 1.2, C_CARD)
txt(s, "Flux d'exécution TP1", 0.4, 4.32, 4, 0.32, size=11, color=C_TP1, bold=True)
steps = [("Image\nAvant .zip", C_TP1),("SNAP GPT\nBEFORE", C_CARD),("Image\nAprès .zip", C_TP1),
         ("SNAP GPT\nAFTER", C_CARD),("Alignement\nGDALWarp", C_CARD),
         ("diff=bd−ad\n>3dB", C_TP1),("mask_water\n.tif", C_GREEN),("RGB\nComposite", C_GREEN)]
for i,(lbl,c) in enumerate(steps):
    x = 0.3 + i*1.62
    rect(s, x, 4.68, 1.35, 0.65, c)
    txt(s, lbl, x, 4.68, 1.35, 0.65, size=9, color=C_WHITE if c!=C_CARD else C_TEXT, bold=True, align=PP_ALIGN.CENTER)
    if i < 7:
        txt(s, ">", x+1.35, 4.84, 0.27, 0.3, size=12, color=C_MUTED, align=PP_ALIGN.CENTER)
footer(s)

# ═══════════════════════════════════════════════════════════
# SLIDE 4 — TP1 : GRAPHE SNAP XML
# ═══════════════════════════════════════════════════════════
s = slide(); header(s, "TP1 — Graphe XML SNAP auto-généré", "_write_snap_graph_preprocess()", color=C_TP1)

rect(s, 0.25, 1.25, 5.8, 5.5, C_CARD)
txt(s, "Chaîne de 8 opérateurs générée dynamiquement", 0.4, 1.32, 5.5, 0.38, size=12, color=C_TP1, bold=True)
ops = [
    ("1", "Read",               "Lecture image Sentinel-1 .zip",          C_MUTED),
    ("2", "Subset",             "Découpage AOI (polygon WKT)",             C_MUTED),
    ("3", "Apply-Orbit-File",   "Correction orbitale précise (DORIS)",     C_ACCENT),
    ("4", "ThermalNoiseRemoval","Suppression bruit thermique",             C_ACCENT),
    ("5", "Calibration",        "DN → σ₀ (Sigma0) linéaire",              C_ORANGE),
    ("6", "Speckle-Filter",     "Refined Lee 7×7 pixels",                 C_ORANGE),
    ("7", "Terrain-Correction", "Géocodage RTC  SRTM 10m  UTM auto",      C_GREEN),
    ("8", "LinearToFromdB",     "σ₀ → 10·log₁₀(σ₀)  en décibels",        C_GREEN),
]
for i,(num,op,desc,c) in enumerate(ops):
    y = 1.75 + i*0.55
    rect(s, 0.3, y, 0.35, 0.42, c)
    txt(s, num, 0.3, y, 0.35, 0.42, size=11, color=C_BG, bold=True, align=PP_ALIGN.CENTER)
    txt(s, op, 0.72, y+0.04, 2.2, 0.35, size=11, color=C_WHITE, bold=True, font="Consolas")
    txt(s, desc, 2.98, y+0.04, 2.9, 0.35, size=10, color=C_MUTED)
    if i < 7:
        txt(s, "↓", 0.38, y+0.42, 0.28, 0.13, size=8, color=c, align=PP_ALIGN.CENTER)

rect(s, 6.35, 1.25, 6.7, 5.5, C_DARK)
txt(s, "Extrait XML généré", 6.5, 1.32, 6.4, 0.35, size=12, color=C_ACCENT, bold=True)
code_block(s, [
    "def _write_snap_graph_preprocess(",
    "      self, img, aoi, pol, px, dem, epsg, out):",
    "  # AOI → Polygone WKT automatique",
    "  geom = f'POLYGON(({aoi[lon_min]} {aoi[lat_min]},",
    "          {aoi[lon_max]} {aoi[lat_min]}, ...))'",
    "  # Exécution via subprocess",
    "  cmd = [SNAP_GPT, graph_xml,",
    '         "-c", "16G", "-q", "16"]',
    "  proc = subprocess.Popen(cmd, ...)",
    "  # Log filtré ligne par ligne",
    "  for line in proc.stdout:",
    '      if "%" in line or "INFO" in line:',
    "          job.log(line, 'SNAP')",
    "  return proc.returncode == 0",
], 6.4, 1.7, 6.6, 4.9)
footer(s)

# ═══════════════════════════════════════════════════════════
# SLIDE 5 — TP1 : DIFFÉRENCE + RGB
# ═══════════════════════════════════════════════════════════
s = slide(); header(s, "TP1 — Calcul Différence & Composite RGB", "Script QGIS Python  diff_rgb.py  généré dynamiquement", color=C_TP1)

rect(s, 0.25, 1.25, 6.1, 5.5, C_DARK)
txt(s, "Alignement + Différence NumPy", 0.4, 1.32, 5.8, 0.35, size=12, color=C_TP1, bold=True)
code_block(s, [
    "# 1. Aligner l'image avant sur la grille après",
    "subprocess.run([gdalwarp,",
    '  "-t_srs", f"EPSG:{epsg}",',
    '  "-tr", str(abs(gt[1])), str(abs(gt[5])),',
    '  "-te", xmin, ymin, xmax, ymax,',
    '  "-r", "bilinear", before_db, aligned])',
    "",
    "# 2. Lire les arrays NumPy",
    "bd = ds_before.GetRasterBand(1).ReadAsArray()",
    "ad = ds_after.GetRasterBand(1).ReadAsArray()",
    "bd, ad = bd[:rows,:cols], ad[:rows,:cols]",
    "",
    "# 3. Différence dB et seuillage",
    "diff = bd - ad   # positif = perte signal = eau",
    "mask = (diff > SEUIL).astype(np.int8)",
    "# SEUIL = 3.0 dB (configurable)",
], 0.3, 1.72, 5.9, 4.8)

rect(s, 6.6, 1.25, 6.45, 5.5, C_DARK)
txt(s, "Composite RGB fausses couleurs", 6.75, 1.32, 6.1, 0.35, size=12, color=C_GREEN, bold=True)
code_block(s, [
    "def stretch(a):",
    "    # Étirement linéaire 2%–98%",
    "    lo = np.percentile(a[np.isfinite(a)], 2)",
    "    hi = np.percentile(a[np.isfinite(a)], 98)",
    "    s = np.clip((a-lo)/(hi-lo)*255, 0, 255)",
    "    return s.astype(np.uint8)",
    "",
    "# 3 bandes GeoTIFF",
    "o = drv.Create(rgb_tif, cols, rows, 3,",
    "               gdal.GDT_Byte)",
    "# Bande 1 Rouge  = avant (zones inondées)",
    "o.GetRasterBand(1).WriteArray(stretch(bd))",
    "# Bande 2 Verte  = après",
    "o.GetRasterBand(2).WriteArray(stretch(ad))",
    "# Bande 3 Bleue  = après",
    "o.GetRasterBand(3).WriteArray(stretch(ad))",
    "# → zones inondées apparaissent en ROUGE",
], 6.65, 1.72, 6.35, 4.8)
footer(s)

# ═══════════════════════════════════════════════════════════
# SLIDE 6 — TP2 : PRÉSENTATION + XML
# ═══════════════════════════════════════════════════════════
s = slide(); header(s, "TP2 — Seuillage Image Unique", "_write_snap_graph_tp2()  —  un seul graphe SNAP", color=C_TP2)

rect(s, 0.25, 1.25, 3.5, 5.5, C_CARD)
rect(s, 0.25, 1.25, 0.07, 5.5, C_TP2)
txt(s, "Principe & différence avec TP1", 0.45, 1.32, 3.2, 0.38, size=12, color=C_TP2, bold=True)
mtxt(s, [
    "Une seule image post-événement.",
    "",
    "L'eau libre en polarisation VH",
    "présente un σ₀ très faible :",
    "surface spéculaire calme.",
    "",
    "Seuil absolu :",
    "σ₀_VH_dB  <  −26 dB  →  eau",
    "",
    "Intégré directement dans",
    "le graphe SNAP via BandMaths.",
    "",
    "Pas de script QGIS secondaire.",
], 0.45, 1.75, 3.2, 4.8, size=12, color=C_TEXT)

rect(s, 4.0, 1.25, 4.3, 2.5, C_CARD)
rect(s, 4.0, 1.25, 0.07, 2.5, C_ORANGE)
txt(s, "Point critique — Échappement XML", 4.15, 1.32, 4.0, 0.38, size=12, color=C_ORANGE, bold=True)
code_block(s, [
    "# INCORRECT → SNAP code 1 (silencieux)",
    "expr = f'Sigma0_{pol}_db < {seuil}'",
    "",
    "# CORRECT — < échappé en &lt;",
    "expr = f'Sigma0_{pol}_db &lt; {seuil}'",
    "# &lt; = entité XML pour le char <",
], 4.05, 1.7, 4.2, 1.9)

rect(s, 4.0, 3.9, 4.3, 2.85, C_CARD)
txt(s, "Comparatif TP1 vs TP2", 4.15, 3.97, 4.0, 0.35, size=12, color=C_CYAN, bold=True)
comp = [("Images","2 (avant+après)","1 (après seul)"),
        ("Méthode","Diff. relative","Seuil absolu"),
        ("Chaînes SNAP","2 séparées","1 avec BandMaths"),
        ("Seuil","3 dB (relatif)","−26 dB (absolu)"),
        ("Eaux perm.","Éliminées","Incluses")]
for j,(lbl,v1,v2) in enumerate(comp):
    y = 4.38 + j*0.43
    bg = C_CARD if j%2==0 else RGBColor(0x12,0x24,0x38)
    rect(s, 4.05, y, 4.2, 0.41, bg)
    txt(s, lbl, 4.12, y+0.05, 1.3, 0.33, size=10, color=C_MUTED)
    txt(s, v1,  5.45, y+0.05, 1.3, 0.33, size=10, color=C_TP1)
    txt(s, v2,  6.8,  y+0.05, 1.4, 0.33, size=10, color=C_TP2)

rect(s, 8.55, 1.25, 4.5, 5.5, C_DARK)
txt(s, "Opérateur BandMaths dans le graphe XML", 8.7, 1.32, 4.2, 0.35, size=12, color=C_TP2, bold=True)
code_block(s, [
    "# Nœud BandMaths ajouté après LinearToFromdB",
    "<node id='BandMaths'>",
    "  <operator>BandMaths</operator>",
    "  <sources>",
    "    <sourceProduct refid='LinearToFromdB'/>",
    "  </sources>",
    "  <parameters>",
    "    <targetBands><targetBand>",
    "      <name>inondation</name>",
    "      <type>int8</type>",
    "      <!-- &lt; = < en XML -->",
    "      <expression>",
    "        Sigma0_VH_db &lt; -26.0 ? 1 : 0",
    "      </expression>",
    "      <noDataValue>-1</noDataValue>",
    "    </targetBand></targetBands>",
    "  </parameters>",
    "</node>",
], 8.6, 1.72, 4.4, 4.8)
footer(s)

# ═══════════════════════════════════════════════════════════
# SLIDE 7 — TP3 : PRÉSENTATION
# ═══════════════════════════════════════════════════════════
s = slide(); header(s, "TP3 — Vectorisation & Statistiques", "6 étapes — tp3_process.py généré dynamiquement", color=C_TP3)

steps3 = [
    ("A", "Lissage Gaussien",     "scipy.ndimage.gaussian_filter  σ=2.0",     C_TP3),
    ("B", "Natural Breaks",       "K-means 2 clusters  seuil adaptatif",       C_TP3),
    ("C", "Polygonize",           "gdal.Polygonize()  API Python directe",      C_ACCENT),
    ("D", "Filtrage surface",     "Boucle OGR  area_ha >= 0.5 ha",             C_ACCENT),
    ("E", "Intersection GADM",    "ogr.Intersection()  1 515 communes L4",     C_ORANGE),
    ("F", "Export CSV + Rapport", "csv.writer  +  rapport.html auto",           C_GREEN),
]
for i,(lbl,title,desc,c) in enumerate(steps3):
    x = 0.25 + (i%3)*4.36
    y = 1.25 + (i//3)*2.85
    rect(s, x, y, 4.1, 2.6, C_CARD)
    rect(s, x, y, 4.1, 0.42, c)
    txt(s, f"{lbl}  —  {title}", x, y, 4.1, 0.42, size=12, color=C_BG, bold=True, align=PP_ALIGN.CENTER)
    txt(s, desc, x+0.15, y+0.5, 3.8, 0.35, size=11, color=C_CYAN)
    if lbl == "A":
        mtxt(s, ["- Sigma=2 ≈ rayon 20m à 10m/pixel","- Élimine speckle résiduel","- Adoucit contours avant vectorisation"], x+0.15, y+0.92, 3.8, 1.5, size=11, color=C_TEXT)
    elif lbl == "B":
        mtxt(s, ["- K-means sur pixels valides","- Seuil = moyenne des 2 centroïdes","- S'adapte à chaque image (pas fixe)"], x+0.15, y+0.92, 3.8, 1.5, size=11, color=C_TEXT)
    elif lbl == "C":
        mtxt(s, ["- API Python (pas subprocess)","- Évite dépendances Python système","- Garanti GDAL du bon environnement"], x+0.15, y+0.92, 3.8, 1.5, size=11, color=C_TEXT)
    elif lbl == "D":
        mtxt(s, ["- gridcode==2 → classe eau","- area_ha = geom.Area()/10000","- Configurable (défaut 0.5 ha)"], x+0.15, y+0.92, 3.8, 1.5, size=11, color=C_TEXT)
    elif lbl == "E":
        mtxt(s, ["- Reprojection WGS84 avant intersection","- SetSpatialFilterRect pour perf.","- ha_per_sq_deg selon latitude"], x+0.15, y+0.92, 3.8, 1.5, size=11, color=C_TEXT)
    elif lbl == "F":
        mtxt(s, ["- CSV global + 1 CSV par province","- Tri surface décroissante","- rapport.html auto depuis les stats"], x+0.15, y+0.92, 3.8, 1.5, size=11, color=C_TEXT)
footer(s)

# ═══════════════════════════════════════════════════════════
# SLIDE 8 — TP3 : CODE LISSAGE + NATURAL BREAKS
# ═══════════════════════════════════════════════════════════
s = slide(); header(s, "TP3 — Lissage Gaussien & Natural Breaks (A + B)", "Étapes de préparation du raster avant vectorisation", color=C_TP3)

rect(s, 0.25, 1.25, 6.1, 5.5, C_DARK)
txt(s, "A — Lissage Gaussien  (scipy.ndimage)", 0.4, 1.32, 5.8, 0.35, size=12, color=C_TP3, bold=True)
code_block(s, [
    "from scipy.ndimage import gaussian_filter",
    "",
    "# Lecture du masque eau (binaire 0/1)",
    "ds   = gdal.Open(mask_water)",
    "data = ds.GetRasterBand(1).ReadAsArray()",
    "gt   = ds.GetGeoTransform()",
    "prj  = ds.GetProjection()",
    "",
    "# sigma=2.0 → rayon ~20m à résolution 10m/px",
    "# Comble les petits trous, lisse les contours",
    "sm = gaussian_filter(",
    "         data.astype(np.float64),",
    "         sigma=2.0",
    "     )",
    "",
    "# Sauvegarde raster lissé (Float32)",
    "o = drv.Create(smoothed_tif, nx, ny, 1,",
    "               gdal.GDT_Float32)",
    "o.SetGeoTransform(gt)",
    "o.SetProjection(prj)",
    "o.GetRasterBand(1).WriteArray(sm)",
], 0.3, 1.72, 5.9, 4.8)

rect(s, 6.6, 1.25, 6.45, 5.5, C_DARK)
txt(s, "B — Reclassification K-means Natural Breaks", 6.75, 1.32, 6.1, 0.35, size=12, color=C_TP3, bold=True)
code_block(s, [
    "from scipy.cluster.vq import kmeans",
    "",
    "# Lire raster lissé",
    "data = gdal.Open(smoothed_tif)",
    "       .GetRasterBand(1).ReadAsArray()",
    "valid = data[np.isfinite(data)].flatten()",
    "",
    "# Sous-échantillon si > 500 000 pixels",
    "if len(valid) > 500_000:",
    "    idx   = np.random.choice(len(valid),",
    "                             500_000,",
    "                             replace=False)",
    "    samp  = valid[idx]",
    "",
    "# K-means 2 clusters (eau / non-eau)",
    "centroides, _ = kmeans(samp, 2)",
    "",
    "# Seuil = moyenne des 2 centroïdes",
    "# S'adapte à chaque image automatiquement",
    "thr     = centroides.mean()",
    "reclass = np.where(data > thr, 2, 1)",
    "# Classe 2 = eau  |  Classe 1 = non-eau",
], 6.65, 1.72, 6.35, 4.8)
footer(s)

# ═══════════════════════════════════════════════════════════
# SLIDE 9 — TP3 : POLYGONIZE + FILTRAGE
# ═══════════════════════════════════════════════════════════
s = slide(); header(s, "TP3 — Vectorisation & Filtrage (C + D)", "gdal.Polygonize() API — OGR surface filter", color=C_TP3)

rect(s, 0.25, 1.25, 6.1, 5.5, C_DARK)
txt(s, "C — gdal.Polygonize() API Python", 0.4, 1.32, 5.8, 0.35, size=12, color=C_ACCENT, bold=True)
code_block(s, [
    "from osgeo import gdal, ogr, osr",
    "",
    "# Ouvrir le raster reclassifié",
    "ds_r   = gdal.Open(reclass_tif)",
    "band_r = ds_r.GetRasterBand(1)",
    "",
    "# Créer le shapefile de sortie",
    "drv_shp = ogr.GetDriverByName('ESRI Shapefile')",
    "raw_ds  = drv_shp.CreateDataSource(raw_shp)",
    "raw_srs = osr.SpatialReference()",
    "raw_srs.ImportFromWkt(ds_r.GetProjection())",
    "raw_lay = raw_ds.CreateLayer('zi',",
    "              srs=raw_srs,",
    "              geom_type=ogr.wkbPolygon)",
    "fd = ogr.FieldDefn('gridcode', ogr.OFTInteger)",
    "raw_lay.CreateField(fd)",
    "",
    "# Vectorisation — pixels contigus → polygones",
    "# arg4=0 : champ gridcode reçoit la valeur pixel",
    "gdal.Polygonize(band_r, band_r, raw_lay,",
    "                0, [], callback=None)",
    "raw_ds.FlushCache(); raw_ds = None",
    "# NOTE: API Python, pas subprocess !",
], 0.3, 1.72, 5.9, 4.8)

rect(s, 6.6, 1.25, 6.45, 5.5, C_DARK)
txt(s, "D — Filtrage surface minimale  (OGR)", 6.75, 1.32, 6.1, 0.35, size=12, color=C_ACCENT, bold=True)
code_block(s, [
    "AREA_MIN = 0.5  # hectares (configurable)",
    "",
    "src_lay = ogr.Open(raw_shp).GetLayer()",
    "n_ok, n_skip = 0, 0",
    "",
    "for feat in src_lay:",
    "    # Garder seulement classe 2 (eau)",
    "    if feat.GetField('gridcode') != 2:",
    "        continue",
    "",
    "    geom = feat.GetGeometryRef()",
    "    if geom is None: continue",
    "",
    "    # Area() retourne m² (proj. UTM)",
    "    area_ha = geom.Area() / 10_000.0",
    "",
    "    if area_ha < AREA_MIN:",
    "        n_skip += 1",
    "        continue",
    "",
    "    # Créer polygone filtré + Surface_ha",
    "    of = ogr.Feature(out_lay.GetLayerDefn())",
    "    of.SetGeometry(geom.Clone())",
    "    of.SetField('Surface_ha', round(area_ha,4))",
    "    out_lay.CreateFeature(of)",
    "    n_ok += 1",
], 6.65, 1.72, 6.35, 4.8)
footer(s)

# ═══════════════════════════════════════════════════════════
# SLIDE 10 — TP3 : STATISTIQUES GADM
# ═══════════════════════════════════════════════════════════
s = slide(); header(s, "TP3 — Intersection GADM & Statistiques (E + F)", "OGR intersection  +  CSV par commune / province", color=C_TP3)

rect(s, 0.25, 1.25, 6.1, 5.5, C_DARK)
txt(s, "E — Intersection OGR avec GADM Level 4", 0.4, 1.32, 5.8, 0.35, size=12, color=C_ORANGE, bold=True)
code_block(s, [
    "# Reprojeter ZI en WGS84 (= proj. GADM)",
    "wgs84 = osr.SpatialReference()",
    "wgs84.ImportFromEPSG(4326)",
    "tr = osr.CoordinateTransformation(zi_srs, wgs84)",
    "",
    "# Union de tous les polygones ZI",
    "zi_union = ogr.Geometry(ogr.wkbMultiPolygon)",
    "for feat in zi_lay:",
    "    zi_union = zi_union.Union(feat.GetGeometryRef())",
    "",
    "# Pré-filtre spatial → évite 1515 intersections",
    "env = zi_union.GetEnvelope()   # xmin,xmax,ymin,ymax",
    "com_lay.SetSpatialFilterRect(",
    "    env[0], env[2], env[1], env[3])",
    "",
    "# Conversion degrés → ha selon latitude",
    "lat0      = (env[2]+env[3])/2",
    "cos_lat   = math.cos(math.radians(lat0))",
    "ha_per_deg = (111000**2)*cos_lat/10000",
    "",
    "stats = defaultdict(float)",
    "for com_feat in com_lay:",
    "    cg    = com_feat.GetGeometryRef()",
    "    inter = cg.Intersection(zi_union)",
    "    if inter and not inter.IsEmpty():",
    "        area = inter.Area() * ha_per_deg",
    "        stats[(region, province, commune)] += area",
], 0.3, 1.72, 5.9, 4.8)

rect(s, 6.6, 1.25, 6.45, 5.5, C_DARK)
txt(s, "F — Export CSV + Rapport HTML", 6.75, 1.32, 6.1, 0.35, size=12, color=C_GREEN, bold=True)
code_block(s, [
    "# CSV global toutes communes",
    "with open(stats_csv, 'w') as f:",
    "    w = csv.writer(f)",
    "    w.writerow(['Region','Province',",
    "                'Commune','Surface_ZI_ha'])",
    "    # Tri par surface décroissante",
    "    for (r,p,c),a in sorted(stats.items(),",
    "                    key=lambda x:(x[0][1],-x[1])):",
    "        w.writerow([r, p, c, f'{a:.2f}'])",
    "    w.writerow(['TOTAL','','',total])",
    "",
    "# Un CSV par province",
    "for (r, p), communes in by_province.items():",
    "    fn = prov_dir / f'{p}.csv'",
    "    # Communes triées par surface",
    "    for c, a in sorted(communes,",
    "                        key=lambda x: -x[1]):",
    "        w.writerow([p, c, f'{a:.2f}'])",
    "",
    "# Rapport HTML auto-généré",
    "html = self._build_report_html(rows, total)",
    "with open(rapport_html, 'w') as f:",
    "    f.write(html)",
    "# → tableau top communes + provinces",
    "#   paramètres du job + ID unique",
], 6.65, 1.72, 6.35, 4.8)
footer(s)

# ═══════════════════════════════════════════════════════════
# SLIDE 11 — TABLEAU RÉCAPITULATIF
# ═══════════════════════════════════════════════════════════
s = slide(); header(s, "Tableau Récapitulatif", "Manuel → Automatisé  pour chaque étape")

col_headers = ["Étape", "Action manuelle (SNAP/QGIS)", "Automatisation CCIP", "Technologie"]
col_w = [1.6, 3.8, 4.1, 3.0]
col_x = [0.25, 1.87, 5.7, 9.82]
for j,(h,w,cx) in enumerate(zip(col_headers,col_w,col_x)):
    rect(s, cx, 1.25, w, 0.36, C_ACCENT)
    txt(s, h, cx+0.06, 1.27, w-0.1, 0.32, size=11, color=C_BG, bold=True)

rows_data = [
    ("TP1 — SNAP",    "2x chaîne manuelle SNAP",      "2 graphes XML auto-générés",        "subprocess + gpt", C_TP1),
    ("TP1 — Diff.",   "Calculatrice raster QGIS",     "NumPy: bd−ad > 3dB",               "NumPy / GDAL",     C_TP1),
    ("TP1 — RGB",     "Outil RGB QGIS manuel",        "GDAL GeoTIFF 3 bandes + stretch",  "GDAL Python",      C_TP1),
    ("TP2 — SNAP",    "BandMaths SNAP manuel",        "BandMaths intégré au graphe XML",  "XML &lt; échappé", C_TP2),
    ("TP3 — Lissage", "Plugin lissage QGIS",          "gaussian_filter(sigma=2.0)",       "scipy.ndimage",    C_TP3),
    ("TP3 — Reclass", "Seuil visuel manuel",          "K-means 2 clusters adaptatif",     "scipy.cluster",    C_TP3),
    ("TP3 — Vect.",   "gdal_polygonize (terminal)",   "gdal.Polygonize() API Python",     "osgeo.gdal",       C_TP3),
    ("TP3 — Stats",   "Calc. champs + export QGIS",   "OGR Intersection GADM + CSV",      "osgeo.ogr",        C_TP3),
    ("Rapport",       "Rédaction manuelle",           "HTML auto depuis stats",           "Python + csv",     C_GREEN),
]
for i,(step,man,auto,tech,c) in enumerate(rows_data):
    y = 1.63 + i*0.55
    bg = C_CARD if i%2==0 else RGBColor(0x10,0x20,0x30)
    for w,cx in zip(col_w,col_x):
        rect(s, cx, y, w, 0.52, bg)
    rect(s, col_x[0], y, 0.06, 0.52, c)
    txt(s, step,  col_x[0]+0.1, y+0.08, col_w[0]-0.15, 0.36, size=10, color=c, bold=True)
    txt(s, "✗ "+man,  col_x[1]+0.05, y+0.08, col_w[1]-0.1,  0.36, size=10, color=RGBColor(0xef,0x53,0x50))
    txt(s, "✓ "+auto, col_x[2]+0.05, y+0.08, col_w[2]-0.1,  0.36, size=10, color=C_GREEN)
    txt(s, tech,  col_x[3]+0.05, y+0.08, col_w[3]-0.1,  0.36, size=10, color=C_CYAN)
footer(s)

# ═══════════════════════════════════════════════════════════
# SLIDE 12 — RÉSULTATS GHARB 2026
# ═══════════════════════════════════════════════════════════
s = slide(); header(s, "Résultats — Inondations Gharb 2026", "Validation du pipeline complet sur cas réel")

kpis = [("1 678 155","ha inondés",C_RED),("165","communes",C_ORANGE),("9","provinces",C_ACCENT),("2 min 25 s","durée total",C_GREEN)]
for i,(val,lbl,c) in enumerate(kpis):
    x = 0.25 + i*3.27
    rect(s, x, 1.25, 3.1, 1.1, C_CARD)
    rect(s, x, 1.25, 3.1, 0.08, c)
    txt(s, val, x, 1.38, 3.1, 0.55, size=26, color=c, bold=True, align=PP_ALIGN.CENTER)
    txt(s, lbl, x, 1.93, 3.1, 0.32, size=12, color=C_TEXT, align=PP_ALIGN.CENTER)

# Params job
rect(s, 0.25, 2.5, 5.8, 2.0, C_CARD)
txt(s, "Paramètres du job", 0.4, 2.57, 5.5, 0.35, size=12, color=C_ACCENT, bold=True)
mtxt(s, [
    "Image avant :  S1A_IW_GRDH_1SDV_20260122T062746",
    "Image après :  S1A_IW_GRDH_1SDV_20260203T062746",
    "Mode :  TP1 (Avant/Après)  |  Polar. : VH",
    "AOI :  lon [−6.8, −4.8]  lat [33.5, 35.8]",
    "EPSG :  32630 (UTM 30N — auto-détecté)",
], 0.4, 2.98, 5.6, 1.4, size=11, color=C_TEXT)

# Province table
rect(s, 6.35, 2.5, 6.7, 0.34, C_ACCENT)
for h,w,cx in [("Province",2.4,6.35),("Surface (ha)",1.7,8.77),("Part (%)",1.3,10.49),("Rang",0.55,11.82)]:
    txt(s, h, cx+0.05, 2.5, w-0.08, 0.34, size=10, color=C_BG, bold=True)

provs = [("Chefchaouen",417584,24.9),("Larache",277017,16.5),("Sidi Kacem",267625,15.9),
         ("Tétouan",246123,14.7),("Kénitra",228513,13.6),("Taounate",111730,6.7),
         ("Tanger-Assilah",91337,5.4),("Fahs Anjra",38226,2.3)]
max_ha = 417584
bar_colors = [C_RED,C_ORANGE,C_ORANGE,C_ACCENT,C_ACCENT,C_CYAN,C_CYAN,C_GREEN]
for i,(name,ha,pct) in enumerate(provs):
    y = 2.86 + i*0.52
    bg = C_CARD if i%2==0 else RGBColor(0x12,0x24,0x38)
    rect(s, 6.35, y, 6.7, 0.5, bg)
    bw = (ha/max_ha)*2.3
    rect(s, 6.37, y+0.08, bw, 0.33, bar_colors[i])
    txt(s, name, 6.42, y+0.09, 2.35, 0.32, size=10, color=C_WHITE)
    txt(s, f"{ha:,}", 8.82, y+0.09, 1.6, 0.32, size=10, color=C_CYAN, align=PP_ALIGN.CENTER)
    txt(s, f"{pct}%", 10.54, y+0.09, 1.2, 0.32, size=10, color=C_GREEN, align=PP_ALIGN.CENTER)
    txt(s, f"#{i+1}", 11.87, y+0.09, 0.45, 0.32, size=10, color=C_MUTED, align=PP_ALIGN.CENTER)

footer(s)

# ═══════════════════════════════════════════════════════════
# SAVE
# ═══════════════════════════════════════════════════════════
out = "/Users/mac/Documents/Projet/CRTS/CCIP/CCIP_Automatisation_TP.pptx"
prs.save(out)
print(f"Saved: {out}  ({len(prs.slides)} slides)")
import os; print(f"Size: {os.path.getsize(out):,} bytes")
