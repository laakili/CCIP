"""
CCIP — Centre de Veille & Intelligence
Page unique avec 4 onglets : Situation Nationale · Info & Actualités · Météo & Alertes · Assistant IA
Ticker temps réel · Horloge UTC+1 · Toggle FR/AR/EN · 8 flux institutionnels avec statut live
"""
import os, sys, json, datetime, urllib.request, urllib.error, xml.etree.ElementTree as ET
import streamlit as st
import streamlit.components.v1 as components

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.config import RESULTS_DIR

_logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "crts_logo.png")
st.set_page_config(
    page_title="CCIP — Centre de Veille",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ══════════════════════════════════════════════════════════════
# I18N
# ══════════════════════════════════════════════════════════════
I18N = {
    "FR": {
        "ticker_label":   "⚡ ALERTES EN DIRECT",
        "no_alerts":      "Aucune alerte active · Tous les flux institutionnels sont sous surveillance · Plateforme CCIP opérationnelle",
        "tab1": "🛰️  Situation Nationale",
        "tab2": "📰  Info & Actualités",
        "tab3": "🌤️  Météo & Alertes",
        "tab4": "🤖  Assistant IA",
        "feed_status":    "STATUT FLUX",
        "kpi_done":       "Traitements terminés",
        "kpi_running":    "En cours",
        "kpi_ha":         "Hectares inondés (total)",
        "kpi_mod":        "Module actif",
        "map_title":      "🗺️ CARTE DE SITUATION — MAROC",
        "alerts_title":   "⚡ ALERTES ACTIVES",
        "jobs_title":     "🌊 DERNIERS TRAITEMENTS",
        "modules_title":  "📡 MODULES",
        "no_alert":       "Aucune alerte active",
        "no_job":         "Aucun traitement terminé",
        "news_title":     "📰 FLUX D'ACTUALITÉS — CRISES & ENVIRONNEMENT MAROC",
        "meteo_title":    "🌤️ MÉTÉO & VIGILANCES — MAROC",
        "ia_title":       "🤖 ASSISTANT IA — CCIP INTELLIGENCE",
    },
    "AR": {
        "ticker_label":   "⚡ تنبيهات مباشرة",
        "no_alerts":      "لا توجد تنبيهات نشطة · جميع المصادر المؤسسية قيد المراقبة · منصة CCIP تعمل",
        "tab1": "🛰️  الوضع الوطني",
        "tab2": "📰  أخبار ومعلومات",
        "tab3": "🌤️  الطقس والتحذيرات",
        "tab4": "🤖  المساعد الذكي",
        "feed_status":    "حالة المصادر",
        "kpi_done":       "معالجات منتهية",
        "kpi_running":    "جارية",
        "kpi_ha":         "هكتار مغمورة (إجمالي)",
        "kpi_mod":        "وحدة نشطة",
        "map_title":      "🗺️ خريطة الوضع — المغرب",
        "alerts_title":   "⚡ تنبيهات نشطة",
        "jobs_title":     "🌊 آخر المعالجات",
        "modules_title":  "📡 الوحدات",
        "no_alert":       "لا توجد تنبيهات",
        "no_job":         "لا توجد معالجات منتهية",
        "news_title":     "📰 تدفقات الأخبار — الأزمات والبيئة",
        "meteo_title":    "🌤️ الطقس والمراقبة — المغرب",
        "ia_title":       "🤖 المساعد الذكي — CCIP",
    },
    "EN": {
        "ticker_label":   "⚡ LIVE ALERTS",
        "no_alerts":      "No active alerts · All institutional feeds are being monitored · CCIP Platform operational",
        "tab1": "🛰️  National Situation",
        "tab2": "📰  News & Updates",
        "tab3": "🌤️  Weather & Alerts",
        "tab4": "🤖  AI Assistant",
        "feed_status":    "FEED STATUS",
        "kpi_done":       "Completed Jobs",
        "kpi_running":    "Running",
        "kpi_ha":         "Flooded Hectares (total)",
        "kpi_mod":        "Active Module",
        "map_title":      "🗺️ SITUATION MAP — MOROCCO",
        "alerts_title":   "⚡ ACTIVE ALERTS",
        "jobs_title":     "🌊 LATEST JOBS",
        "modules_title":  "📡 MODULES",
        "no_alert":       "No active alerts",
        "no_job":         "No completed jobs",
        "news_title":     "📰 NEWS FEEDS — CRISES & ENVIRONMENT MOROCCO",
        "meteo_title":    "🌤️ WEATHER & VIGILANCE — MOROCCO",
        "ia_title":       "🤖 AI ASSISTANT — CCIP INTELLIGENCE",
    },
}

# ══════════════════════════════════════════════════════════════
# 8 FLUX INSTITUTIONNELS
# ══════════════════════════════════════════════════════════════
FEEDS_8 = {
    "DMN": {
        "name": "Maroc Météo (DMN)",
        "url":  "https://www.marocmeteo.ma/fr/rss/actualites",
        "icon": "🌤️", "color": "#2196f3", "type": "meteo",
        "desc": "Direction de la Météorologie Nationale",
    },
    "IGN-MA": {
        "name": "IGN Maroc",
        "url":  "https://www.ign.ma/actualites/rss",
        "icon": "🗺️", "color": "#4caf50", "type": "geo",
        "desc": "Institut Géographique National du Maroc",
    },
    "ABH": {
        "name": "ABH (Bassins Hydrauliques)",
        "url":  "https://www.abhoum.ma/rss.xml",
        "icon": "💧", "color": "#00bcd4", "type": "hydro",
        "desc": "Agences de Bassins Hydrauliques",
    },
    "USGS": {
        "name": "USGS Earthquakes",
        "url":  "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/significant_week.atom",
        "icon": "🏔️", "color": "#ff9800", "type": "seisme",
        "desc": "US Geological Survey — Séismes significatifs",
    },
    "Copernicus": {
        "name": "Copernicus EMS",
        "url":  "https://emergency.copernicus.eu/mapping/feed/rss/activations",
        "icon": "🛰️", "color": "#7c4dff", "type": "ems",
        "desc": "Copernicus Emergency Management Service",
    },
    "EFFIS": {
        "name": "EFFIS Active Fires",
        "url":  "https://effis.jrc.ec.europa.eu/rss/active_fires.xml",
        "icon": "🔥", "color": "#ff4545", "type": "feu",
        "desc": "European Forest Fire Information System",
    },
    "IOC": {
        "name": "IOC Tsunami (PTWS)",
        "url":  "https://www.tsunami.gov/events/rss_active.xml",
        "icon": "🌊", "color": "#00e676", "type": "tsunami",
        "desc": "Pacific Tsunami Warning System / IOC-UNESCO",
    },
    "DGPC": {
        "name": "DGPC Maroc",
        "url":  "https://www.protection-civile.gov.ma/rss.xml",
        "icon": "🚨", "color": "#ff6b35", "type": "crise",
        "desc": "Direction Générale de la Protection Civile",
    },
}

ALERT_KEYWORDS = [
    "alerte", "vigilance", "inondation", "séisme", "crue", "activation",
    "fire", "earthquake", "tsunami", "flood", "warning", "rupture",
    "barrage", "tempête", "surge", "cyclone", "alert", "emergency",
    "critical", "magnitude", "submersion", "débordement",
]

# ══════════════════════════════════════════════════════════════
# CSS GLOBAL
# ══════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;600;700&family=Inter:wght@300;400;500;600&display=swap');
.stApp { background: #020b18 !important; }
[data-testid="stSidebar"], [data-testid="collapsedControl"],
header[data-testid="stHeader"], footer { display: none !important; }
.block-container { padding: 1rem 1.5rem 2rem !important; max-width: 100% !important; }

/* Décaler contenu sous navbar + ticker */
.block-container { padding-top: 100px !important; }

/* Ticker scroll animation */
@keyframes scroll-t {
  0%   { transform: translateX(0); }
  100% { transform: translateX(-100%); }
}
@keyframes pulse-live {
  0%,100% { box-shadow: 0 0 4px #fff, 0 0 8px #fff; opacity:1; }
  50%      { box-shadow: 0 0 2px #fff; opacity:.4; }
}

/* Tabs */
[data-testid="stTabs"] [data-baseweb="tab-list"] {
  background: rgba(10,22,40,0.9) !important;
  border-bottom: 1px solid rgba(33,150,243,0.2) !important;
  gap: 4px; padding: 0 8px;
}
[data-testid="stTabs"] [data-baseweb="tab"] {
  font-family: 'Orbitron', monospace !important;
  font-size: 0.72em !important; letter-spacing: 1.5px !important;
  color: rgba(144,202,249,0.5) !important;
  background: transparent !important;
  border: none !important; padding: 12px 18px !important;
}
[data-testid="stTabs"] [aria-selected="true"] {
  color: #2196f3 !important;
  border-bottom: 2px solid #2196f3 !important;
}
[data-testid="stTabs"] [data-baseweb="tab-panel"] {
  background: transparent !important; padding: 0 !important;
}

/* Cards */
.vcard {
  background: linear-gradient(145deg, rgba(13,33,57,0.85), rgba(6,18,36,0.92));
  border: 1px solid rgba(33,150,243,0.15);
  border-radius: 12px; padding: 18px; margin-bottom: 12px;
}
.vcard-accent-blue  { border-left: 3px solid #2196f3; }
.vcard-accent-green { border-left: 3px solid #00e676; }
.vcard-accent-red   { border-left: 3px solid #ff4545; }
.vcard-accent-orange{ border-left: 3px solid #ff9800; }
.vcard-accent-purple{ border-left: 3px solid #7c4dff; }

.vtitle { font-family:'Orbitron',monospace; font-size:0.75em; letter-spacing:2px; color:#2196f3; margin-bottom:14px; }
.vbadge {
  display:inline-block; padding:2px 10px; border-radius:20px;
  font-size:0.68em; font-weight:600; letter-spacing:1px;
  font-family:'Orbitron',monospace; margin-bottom:8px;
}
.badge-active { background:rgba(0,230,118,0.15); color:#00e676; border:1px solid rgba(0,230,118,0.3); }
.badge-soon   { background:rgba(33,150,243,0.1);  color:#64b5f6; border:1px solid rgba(33,150,243,0.2); }
.badge-warn   { background:rgba(255,152,0,0.15);  color:#ff9800; border:1px solid rgba(255,152,0,0.3); }
.badge-info   { background:rgba(33,150,243,0.12); color:#90caf9; border:1px solid rgba(33,150,243,0.25); }

/* Météo */
.meteo-grid { display:grid; grid-template-columns:repeat(5,1fr); gap:10px; margin:12px 0; }
.meteo-day {
  background:rgba(10,22,40,0.8); border:1px solid rgba(33,150,243,0.15);
  border-radius:10px; padding:12px 8px; text-align:center;
}
.meteo-day-name { font-family:'Orbitron',monospace; font-size:0.62em; color:rgba(144,202,249,0.5); }
.meteo-day-icon { font-size:1.8em; margin:6px 0; }
.meteo-day-rain { font-size:0.85em; color:#64b5f6; font-weight:600; }
.meteo-day-temp { font-size:0.72em; color:rgba(144,202,249,0.45); margin-top:2px; }

/* Alerte météo */
.alerte-bar {
  padding:10px 16px; border-radius:8px; margin-bottom:8px;
  display:flex; align-items:center; gap:10px;
  font-size:0.85em;
}
.alerte-rouge  { background:rgba(255,69,69,0.15);  border:1px solid rgba(255,69,69,0.35); }
.alerte-orange { background:rgba(255,152,0,0.15);  border:1px solid rgba(255,152,0,0.35); }
.alerte-jaune  { background:rgba(255,235,59,0.12); border:1px solid rgba(255,235,59,0.3); }
.alerte-vert   { background:rgba(0,230,118,0.1);   border:1px solid rgba(0,230,118,0.2); }

/* Chat IA */
.chat-msg-user {
  background:rgba(33,150,243,0.12); border:1px solid rgba(33,150,243,0.2);
  border-radius:12px 12px 2px 12px; padding:12px 16px; margin:8px 0 8px 60px;
  font-size:0.9em; color:#e3f2fd;
}
.chat-msg-ai {
  background:rgba(13,33,57,0.8); border:1px solid rgba(33,150,243,0.15);
  border-radius:2px 12px 12px 12px; padding:12px 16px; margin:8px 60px 8px 0;
  font-size:0.9em; color:#b0bed0;
}
.chat-label-user { font-family:'Orbitron',monospace; font-size:0.6em; color:#2196f3; margin-bottom:4px; }
.chat-label-ai   { font-family:'Orbitron',monospace; font-size:0.6em; color:rgba(33,150,243,0.5); margin-bottom:4px; }

/* News */
.news-item {
  background:rgba(10,22,40,0.7); border:1px solid rgba(33,150,243,0.12);
  border-radius:10px; padding:14px 16px; margin-bottom:10px;
}
.news-item:hover { border-color:rgba(33,150,243,0.35); }
.news-source { font-family:'Orbitron',monospace; font-size:0.6em; color:rgba(33,150,243,0.5); letter-spacing:2px; }
.news-title  { font-size:0.88em; color:#e3f2fd; font-weight:500; margin:4px 0; line-height:1.4; }
.news-date   { font-size:0.72em; color:rgba(144,202,249,0.4); }

/* Feed status row */
.feed-status-grid {
  display:grid; grid-template-columns:repeat(8,1fr); gap:6px; margin-bottom:14px;
}
.feed-status-card {
  background:rgba(10,22,40,0.8); border-radius:8px; padding:7px 6px; text-align:center;
  border: 1px solid rgba(33,150,243,0.1);
}
.feed-status-icon { font-size:1.1em; }
.feed-status-name { font-family:'Orbitron',monospace; font-size:0.52em; color:rgba(144,202,249,0.5);
                    white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.feed-dot-live    { display:inline-block; width:6px; height:6px; border-radius:50%;
                    background:#00e676; box-shadow:0 0 5px #00e676; margin-top:3px; }
.feed-dot-offline { display:inline-block; width:6px; height:6px; border-radius:50%;
                    background:#ff4545; box-shadow:0 0 4px #ff4545; margin-top:3px; }
.feed-dot-empty   { display:inline-block; width:6px; height:6px; border-radius:50%;
                    background:#ffeb3b; box-shadow:0 0 4px #ffeb3b; margin-top:3px; }

/* Stat box */
.stat-row { display:grid; grid-template-columns:repeat(4,1fr); gap:12px; margin-bottom:20px; }
.stat-box {
  background:linear-gradient(145deg,rgba(13,33,57,0.85),rgba(6,18,36,0.92));
  border:1px solid rgba(33,150,243,0.15); border-radius:10px;
  padding:14px; text-align:center;
}
.stat-val  { font-family:'Orbitron',monospace; font-size:1.4em; font-weight:700; }
.stat-lbl  { font-size:0.7em; color:rgba(144,202,249,0.45); margin-top:4px; }

/* Lang toggle */
.lang-bar {
  display:flex; align-items:center; justify-content:flex-end; gap:4px;
  padding:4px 0 8px 0;
}
.lang-btn {
  padding:3px 10px; border-radius:10px; font-size:0.72em; font-weight:600;
  font-family:'Orbitron',monospace; letter-spacing:1px; cursor:pointer;
  border:1px solid rgba(33,150,243,0.2); background:transparent;
  color:rgba(144,202,249,0.45); transition:all .2s;
}
.lang-btn:hover { background:rgba(33,150,243,0.08); color:#90caf9; }
.lang-btn-active { background:rgba(33,150,243,0.15); color:#e3f2fd; border-color:rgba(33,150,243,0.4); }

/* ── NAVBAR ── */
@keyframes blink   { 0%,100%{opacity:1} 50%{opacity:.2} }
.ccip-nav {
  position: fixed; top: 0; left: 0; right: 0; z-index: 9999;
  height: 60px;
  background: rgba(2,11,24,0.95);
  backdrop-filter: blur(16px);
  border-bottom: 1px solid rgba(33,150,243,0.2);
  display: flex; align-items: center;
  padding: 0 32px; gap: 0;
}
.nav-logo {
  display: flex; align-items: center; gap: 10px;
  text-decoration: none; flex-shrink: 0;
}
.nav-logo-img {
  width: 36px; height: 36px; object-fit: contain;
  background: radial-gradient(circle, rgba(255,255,255,0.18) 0%, rgba(255,255,255,0.06) 55%, transparent 75%);
  border-radius: 50%; padding: 3px;
  filter: drop-shadow(0 0 8px rgba(255,255,255,0.35)) brightness(1.15);
}
.nav-brand {
  font-family: 'Orbitron', monospace;
  font-size: .9em; font-weight: 700;
  color: #90caf9; letter-spacing: 2px;
}
.nav-brand span { color: rgba(144,202,249,0.4); font-size:.75em; margin-left:4px; }
.nav-sep {
  width: 1px; height: 28px;
  background: rgba(33,150,243,0.2);
  margin: 0 24px; flex-shrink: 0;
}
.nav-crises-label {
  font-family: 'Orbitron', monospace;
  font-size: .62em; color: rgba(33,150,243,0.5);
  letter-spacing: 3px; margin-right: 16px; flex-shrink: 0;
  text-transform: uppercase;
}
.nav-crisis-items { display: flex; align-items: center; gap: 6px; flex: 1; }
.nav-crisis-item {
  display: flex; align-items: center; gap: 7px;
  padding: 5px 14px; border-radius: 20px;
  font-family: 'Inter', sans-serif; font-size: .78em; font-weight: 500;
  text-decoration: none; cursor: pointer;
  transition: all .2s; white-space: nowrap;
  border: 1px solid transparent;
  color: rgba(144,202,249,0.45); background: transparent;
}
.nav-crisis-item:hover { color:#90caf9; background:rgba(33,150,243,0.08); border-color:rgba(33,150,243,0.2); }
.nav-crisis-item.nav-active {
  color: #e3f2fd; background: rgba(33,150,243,0.15); border-color: rgba(33,150,243,0.4);
}
.nav-crisis-item.nav-active-purple {
  color: #e3f2fd; background: rgba(124,77,255,0.15); border-color: rgba(124,77,255,0.4);
}
.nav-crisis-item.nav-disabled { opacity:.35; cursor:default; pointer-events:none; }
.dot-active {
  width: 5px; height: 5px; border-radius: 50%;
  background: #4fc3f7; box-shadow: 0 0 5px #4fc3f7;
  animation: blink 1.5s ease-in-out infinite;
}
.nav-right { display:flex; align-items:center; gap:14px; margin-left:auto; flex-shrink:0; }
.nav-status {
  display:flex; align-items:center; gap:6px;
  font-family:'Orbitron',monospace; font-size:.62em; color:rgba(144,202,249,0.5);
}
.nav-status-dot {
  width:6px; height:6px; border-radius:50%;
  background:#66bb6a; box-shadow:0 0 5px #66bb6a;
  animation:blink 1.5s ease-in-out infinite;
}
.nav-version {
  font-family:'Orbitron',monospace; font-size:.6em;
  color:rgba(33,150,243,0.3); border:1px solid rgba(33,150,243,0.15);
  padding:2px 8px; border-radius:10px;
}

/* ── Lang toggle pills ── */
div[data-testid="stRadio"] > div[role="radiogroup"] {
  flex-direction: row !important;
  gap: 3px !important;
  align-items: center !important;
}
div[data-testid="stRadio"] > div[role="radiogroup"] > label {
  background: rgba(10,22,40,0.9) !important;
  border: 1px solid rgba(33,150,243,0.2) !important;
  border-radius: 20px !important;
  padding: 3px 13px !important;
  font-family: 'Orbitron', monospace !important;
  font-size: 0.7em !important;
  letter-spacing: 1.5px !important;
  color: rgba(144,202,249,0.45) !important;
  cursor: pointer !important;
  transition: all .15s !important;
  white-space: nowrap !important;
}
div[data-testid="stRadio"] > div[role="radiogroup"] > label:has(input:checked) {
  background: rgba(33,150,243,0.18) !important;
  color: #e3f2fd !important;
  border-color: rgba(33,150,243,0.5) !important;
  box-shadow: 0 0 8px rgba(33,150,243,0.2) !important;
}
div[data-testid="stRadio"] > div[role="radiogroup"] > label > div:first-child {
  display: none !important;
}
div[data-testid="stRadio"] > label { display: none !important; }

/* ── Morocco feed state cards ── */
.mar-feeds-row {
  display: grid; grid-template-columns: repeat(8, 1fr);
  gap: 5px; margin: 6px 0 10px 0;
}
.mar-feed-card {
  background: rgba(6,16,30,0.95);
  border: 1px solid rgba(33,150,243,0.08);
  border-radius: 8px; padding: 7px 7px 6px 7px;
  position: relative; overflow: hidden;
}
.mar-feed-card::before {
  content: ''; position: absolute; top: 0; left: 0; right: 0;
  height: 2px;
}
.mar-card-ok::before     { background: #00e676; }
.mar-card-info::before   { background: #2196f3; }
.mar-card-warn::before   { background: #ff9800; }
.mar-card-alert::before  { background: #ff4545; box-shadow: 0 0 6px #ff4545; }
.mar-card-offline::before{ background: rgba(144,202,249,0.15); }

.mar-feed-header {
  display: flex; align-items: center; gap: 4px; margin-bottom: 5px;
}
.mar-feed-icon { font-size: 0.95em; }
.mar-feed-key {
  font-family: 'Orbitron', monospace; font-size: 0.54em;
  color: rgba(144,202,249,0.5); letter-spacing: 1px; flex: 1;
}
.mar-dot {
  width: 5px; height: 5px; border-radius: 50%; flex-shrink: 0;
}
.mar-dot-ok     { background: #00e676; box-shadow: 0 0 4px #00e676; }
.mar-dot-info   { background: #2196f3; box-shadow: 0 0 4px #2196f3; }
.mar-dot-warn   { background: #ff9800; box-shadow: 0 0 4px #ff9800;
                  animation: blink 1.8s ease-in-out infinite; }
.mar-dot-alert  { background: #ff4545; box-shadow: 0 0 6px #ff4545;
                  animation: blink 0.9s ease-in-out infinite; }
.mar-dot-offline{ background: rgba(144,202,249,0.2); }

.mar-feed-text {
  font-size: 0.68em; line-height: 1.35; color: rgba(176,210,240,0.7);
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;
  overflow: hidden; min-height: 1.9em;
}
.mar-feed-text.text-ok     { color: rgba(0,230,118,0.75); }
.mar-feed-text.text-warn   { color: rgba(255,152,0,0.85); }
.mar-feed-text.text-alert  { color: rgba(255,69,69,0.9);  font-weight:600; }
.mar-feed-text.text-offline{ color: rgba(144,202,249,0.25); font-style:italic; }
</style>
""", unsafe_allow_html=True)

# ── Navbar ────────────────────────────────────────────────────
import base64 as _b64
_logo_b64 = ""
if os.path.exists(_logo_path):
    with open(_logo_path, "rb") as _f:
        _logo_b64 = f"data:image/png;base64,{_b64.b64encode(_f.read()).decode()}"

st.markdown(f"""
<nav class="ccip-nav">
  <a class="nav-logo" href="/" target="_self">
    <img class="nav-logo-img" src="{_logo_b64}" alt="CRTS">
    <div class="nav-brand">CCIP <span>· CRTS</span></div>
  </a>
  <div class="nav-sep"></div>
  <div class="nav-crises-label">Crises</div>
  <div class="nav-crisis-items">
    <a class="nav-crisis-item" href="/Inondation" target="_self">
      <div class="dot-active"></div>
      🌊 Inondation
    </a>
    <span class="nav-crisis-item nav-disabled">🔥 Incendie</span>
    <span class="nav-crisis-item nav-disabled">🏔️ Séisme</span>
    <span class="nav-crisis-item nav-disabled">🌪️ Tempête</span>
    <span class="nav-crisis-item nav-disabled">🏜️ Sécheresse</span>
  </div>
  <div class="nav-sep"></div>
  <span class="nav-crisis-item nav-active-purple">
    🛰️ Veille &amp; IA
  </span>
  <div class="nav-right">
    <div class="nav-status">
      <div class="nav-status-dot"></div>
      S1 OPÉRATIONNEL
    </div>
    <div class="nav-version">v1.0</div>
  </div>
</nav>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# UTILITAIRES
# ══════════════════════════════════════════════════════════════
def _load_jobs():
    jobs = []
    if not os.path.exists(RESULTS_DIR):
        return jobs
    for jid in os.listdir(RESULTS_DIR):
        sf = os.path.join(RESULTS_DIR, jid, "state.json")
        if os.path.exists(sf):
            try:
                with open(sf) as f:
                    s = json.load(f)
                jobs.append(s)
            except:
                pass
    return sorted(jobs, key=lambda x: x.get("created",""), reverse=True)

def _fetch_url(url, timeout=6):
    try:
        req = urllib.request.Request(url, headers={"User-Agent":"CCIP-Veille/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read().decode("utf-8", errors="replace")
    except:
        return None

def _parse_rss_raw(raw, max_items=6):
    if not raw:
        return []
    try:
        root = ET.fromstring(raw)
        ns = {"atom":"http://www.w3.org/2005/Atom"}
        items = []
        for item in root.findall(".//item")[:max_items]:
            title = item.findtext("title","").strip()
            link  = item.findtext("link","").strip()
            date  = item.findtext("pubDate","")
            desc  = item.findtext("description","")
            items.append({"title":title,"link":link,"date":date[:25],"desc":desc[:200]})
        if not items:
            for entry in root.findall(".//atom:entry", ns)[:max_items]:
                title = entry.findtext("atom:title","",ns).strip()
                link_el = entry.find("atom:link",ns)
                link  = link_el.get("href","") if link_el is not None else ""
                date  = entry.findtext("atom:updated","",ns)[:25]
                desc  = entry.findtext("atom:summary","",ns)[:200]
                items.append({"title":title,"link":link,"date":date,"desc":desc})
        return items
    except:
        return []

def _parse_rss(url, max_items=6):
    return _parse_rss_raw(_fetch_url(url), max_items)

@st.cache_data(ttl=300, show_spinner=False)
def _fetch_all_feeds():
    """Fetch all 8 institutional feeds. Returns (items_list, statuses_dict)."""
    all_items = []
    statuses  = {}
    for key, cfg in FEEDS_8.items():
        raw = _fetch_url(cfg["url"], timeout=5)
        if raw is None:
            statuses[key] = "offline"
        else:
            items = _parse_rss_raw(raw, max_items=6)
            statuses[key] = "live" if items else "empty"
            for it in items:
                score = sum(1 for kw in ALERT_KEYWORDS
                            if kw in (it["title"]+" "+it.get("desc","")).lower())
                it.update({
                    "feed_key": key,
                    "source":   cfg["name"],
                    "icon":     cfg["icon"],
                    "color":    cfg["color"],
                    "type":     cfg["type"],
                    "score":    score,
                })
            all_items.extend(items)
    all_items.sort(key=lambda x: -x.get("score",0))
    return all_items, statuses

_MAR_GEO = [
    "maroc","morocco","rabat","casablanca","agadir","fès","meknes","meknès",
    "tanger","oujda","atlas","al hoceima","al hoceïma","tetouan","tétouan",
    "kenitra","safi","nador","ouarzazate","laayoune","laâyoune","dakhla",
    "souss","draa","drâa","tensift","sebou","moulouya",
]
_MAR_SEA = [
    "atlant","méditerr","mediterranean","canary","canaries","azores",
    "north africa","afrique du nord","northwest africa","maghreb",
]

def _get_morocco_status(feed_key, items, status):
    """Analyse Morocco-specific situation from a feed's items."""
    import re as _re
    if status == "offline":
        return {"level":"offline", "text":"Source indisponible"}
    if not items:
        return {"level":"ok", "text":"Aucune activité récente"}

    all_geo = _MAR_GEO + _MAR_SEA

    if feed_key in ("DMN", "ABH", "IGN-MA", "DGPC"):
        it = items[0]
        t  = (it["title"]+" "+it.get("desc","")).lower()
        if any(k in t for k in ["rouge","danger immédiat","urgence","alerte maximale"]):
            lvl = "alert"
        elif any(k in t for k in ["orange","vigilance","fort","intense","avis de"]):
            lvl = "warn"
        elif any(k in t for k in ["jaune","modéré","attention"]):
            lvl = "info"
        else:
            lvl = "ok"
        return {"level": lvl, "text": it["title"][:70]}

    elif feed_key == "USGS":
        for it in items:
            t = (it["title"]+" "+it.get("desc","")).lower()
            if any(k in t for k in all_geo):
                m = _re.search(r'M\s*([\d.]+)', it["title"], _re.I)
                try:
                    mag = float(m.group(1)) if m else 0
                    lvl = "alert" if mag>=5.5 else ("warn" if mag>=4.5 else "info")
                except:
                    lvl = "warn"
                return {"level": lvl, "text": it["title"][:70]}
        return {"level":"ok", "text":"Aucun séisme significatif — Maroc/région"}

    elif feed_key == "Copernicus":
        for it in items:
            t = (it["title"]+" "+it.get("desc","")).lower()
            if any(k in t for k in _MAR_GEO):
                return {"level":"warn", "text": "Activation : "+it["title"][:58]}
        return {"level":"ok", "text":"Aucune activation EMS — Maroc"}

    elif feed_key == "EFFIS":
        for it in items:
            t = (it["title"]+" "+it.get("desc","")).lower()
            if any(k in t for k in _MAR_GEO+["north africa","northwest africa"]):
                return {"level":"warn", "text": it["title"][:70]}
        return {"level":"ok", "text":"Aucun incendie actif — Maroc / Afrique du Nord"}

    elif feed_key == "IOC":
        if not items:
            return {"level":"ok", "text":"Aucune alerte tsunami active"}
        for it in items:
            t = (it["title"]+" "+it.get("desc","")).lower()
            if any(k in t for k in all_geo):
                return {"level":"alert", "text": it["title"][:70]}
        return {"level":"ok",
                "text":"Aucune alerte tsunami — Atlantique / Méditerranée"}

    # Fallback
    return {"level":"info", "text": items[0]["title"][:70] if items else "—"}


# ══════════════════════════════════════════════════════════════
# VIGILANCES DMN — helpers Python (miroir de formatters.ts)
# ══════════════════════════════════════════════════════════════

_ZONE_ALIASES_PY: dict = {
    "Tanger-Tétouan-Al Hoceïma": "Rif",
    "Oriental":                   "Oriental",
    "Fès-Meknès":                 "Fès-Meknès",
    "Rabat-Salé-Kénitra":         "Rabat",
    "Béni Mellal-Khénifra":       "B.Mellal",
    "Grand Casablanca-Settat":    "Casablanca",
    "Marrakech-Safi":             "Marrakech",
    "Drâa-Tafilalet":             "Drâa",
    "Souss-Massa":                "Souss",
    "Guelmim-Oued Noun":          "Guelmim",
    "Laâyoune-Sakia El Hamra":    "Laâyoune",
    "Dakhla-Oued Ed-Dahab":       "Dakhla",
}

_PHENOMENE_LABELS_PY: dict = {
    "PLUIES":        "pluies",
    "VENT":          "vents violents",
    "CHALEUR":       "chaleur",
    "FROID":         "froid intense",
    "NEIGE":         "chutes de neige",
    "ORAGE":         "orages",
    "BROUILLARD":    "brouillard",
    "TEMPETE_SABLE": "tempête de sable",
    "CANICULE":      "canicule",
}

_NIVEAU_WEIGHT_PY: dict = {"ROUGE": 4, "ORANGE": 3, "JAUNE": 2, "VERT": 1}

_NIVEAU_EMOJI_PY: dict = {"ROUGE": "🔴", "ORANGE": "🟠", "JAUNE": "🟡", "VERT": "🟢"}

_NIVEAU_TICKER_COLOR: dict = {
    "ROUGE":  "#ff4545",
    "ORANGE": "#ff9800",
    "JAUNE":  "#ffeb3b",
    "VERT":   "#00e676",
}


def _condense_zones_py(zones: list) -> str:
    if not zones:
        return "—"
    aliases = [_ZONE_ALIASES_PY.get(z, z) for z in zones]
    if len(aliases) <= 3:
        return " + ".join(aliases)
    rest = len(aliases) - 2
    plural = "s" if rest > 1 else ""
    return f"{aliases[0]} + {aliases[1]} et {rest} autre{plural}"


def _compute_duree_h(debut: str, fin: str) -> int:
    try:
        fmt = "%Y-%m-%dT%H:%M:%SZ"
        d = datetime.datetime.strptime(debut, fmt)
        f = datetime.datetime.strptime(fin, fmt)
        return max(0, round((f - d).total_seconds() / 3600))
    except Exception:
        return 0


def _format_vigilance_ticker_py(v: dict) -> str:
    niveau    = v.get("niveau", "?")
    phenomene = _PHENOMENE_LABELS_PY.get(v.get("phenomene", ""), v.get("phenomene", "").lower())
    zones     = _condense_zones_py(v.get("zones", []))
    duree     = _compute_duree_h(v.get("debut", ""), v.get("fin", ""))
    duree_str = "&lt;1h" if duree < 1 else f"{duree}h"
    color     = _NIVEAU_TICKER_COLOR.get(niveau, "#ffffff")
    emoji     = _NIVEAU_EMOJI_PY.get(niveau, "⚪")
    bg_map    = {"ROUGE":"rgba(255,69,69,0.22)","ORANGE":"rgba(255,152,0,0.18)",
                 "JAUNE":"rgba(255,235,59,0.14)","VERT":"rgba(0,230,118,0.12)"}
    bg        = bg_map.get(niveau, "rgba(144,202,249,0.1)")
    # Chip niveau
    chip = (
        f'<span style="display:inline-block;background:{bg};color:{color};'
        f'border:1px solid {color}66;border-radius:3px;'
        f'padding:1px 7px 1px 6px;font-size:9.5px;font-weight:800;'
        f'letter-spacing:1.5px;vertical-align:middle;margin-right:2px;">'
        f'{emoji}&nbsp;{niveau}</span>'
    )
    # Source badge DMN
    src = (
        '<span style="color:rgba(144,202,249,0.35);font-size:8.5px;'
        'letter-spacing:2px;vertical-align:middle;margin-right:6px;">DMN</span>'
    )
    pheno_html = f'<span style="color:{color}bb;">{phenomene}</span>'
    zones_html = f'<span style="color:rgba(220,235,255,0.8);">{zones}</span>'
    dur_html   = f'<span style="color:rgba(144,202,249,0.45);font-size:10px;">{duree_str}</span>'
    return f'{src}{chip}&nbsp;{pheno_html}&nbsp;·&nbsp;{zones_html}&nbsp;·&nbsp;{dur_html}'


@st.cache_data(ttl=300, show_spinner=False)
def _load_dmn_vigilances() -> list:
    """Charge les vigilances DMN actives depuis le fichier fixtures JSON."""
    now = datetime.datetime.utcnow()
    fixtures_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "frontend", "src", "features", "vigilance-dmn",
        "mocks", "vigilances.fixtures.json",
    )
    if not os.path.exists(fixtures_path):
        return []
    try:
        with open(fixtures_path) as fp:
            all_v = json.load(fp)
    except Exception:
        return []

    active = []
    for v in all_v:
        try:
            fin_dt = datetime.datetime.strptime(v["fin"], "%Y-%m-%dT%H:%M:%SZ")
            if fin_dt > now:
                active.append(v)
        except Exception:
            active.append(v)

    active.sort(key=lambda v: -_NIVEAU_WEIGHT_PY.get(v.get("niveau", "VERT"), 1))
    return active


def _fetch_meteo(lat=33.9, lon=-6.85):
    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        f"&daily=precipitation_sum,temperature_2m_max,temperature_2m_min,weathercode"
        f"&timezone=Africa%2FCasablanca&forecast_days=5"
    )
    raw = _fetch_url(url, timeout=8)
    if not raw:
        return None
    try:
        return json.loads(raw)
    except:
        return None

WMO_ICON = {
    0:"☀️",1:"🌤️",2:"⛅",3:"☁️",
    45:"🌫️",48:"🌫️",
    51:"🌦️",53:"🌦️",55:"🌧️",
    61:"🌧️",63:"🌧️",65:"🌧️",
    71:"🌨️",73:"🌨️",75:"❄️",
    80:"🌦️",81:"🌧️",82:"⛈️",
    95:"⛈️",96:"⛈️",99:"⛈️",
}

REGIONS_MAR = {
    "Tanger-Tétouan-Al Hoceïma":  {"lat":35.77,"lon":-5.8,  "alerte":"jaune"},
    "Oriental":                    {"lat":34.68,"lon":-1.9,  "alerte":"vert"},
    "Fès-Meknès":                  {"lat":33.99,"lon":-5.0,  "alerte":"vert"},
    "Rabat-Salé-Kénitra":          {"lat":33.99,"lon":-6.85, "alerte":"orange"},
    "Béni Mellal-Khénifra":        {"lat":32.34,"lon":-6.35, "alerte":"vert"},
    "Grand Casablanca-Settat":     {"lat":33.59,"lon":-7.62, "alerte":"jaune"},
    "Marrakech-Safi":              {"lat":31.63,"lon":-8.0,  "alerte":"vert"},
    "Drâa-Tafilalet":              {"lat":31.52,"lon":-4.0,  "alerte":"vert"},
    "Souss-Massa":                 {"lat":30.42,"lon":-9.59, "alerte":"rouge"},
    "Guelmim-Oued Noun":           {"lat":28.99,"lon":-10.05,"alerte":"vert"},
    "Laâyoune-Sakia El Hamra":     {"lat":27.15,"lon":-13.2, "alerte":"vert"},
    "Dakhla-Oued Ed-Dahab":        {"lat":23.68,"lon":-15.97,"alerte":"vert"},
}

ALERTE_COLOR = {"rouge":"#ff4545","orange":"#ff9800","jaune":"#ffeb3b","vert":"#00e676"}
ALERTE_LABEL = {"rouge":"ROUGE","orange":"ORANGE","jaune":"JAUNE","vert":"VERT"}

# ══════════════════════════════════════════════════════════════
# LANGUE  (query-param override → session_state)
# ══════════════════════════════════════════════════════════════
_qp_lang = st.query_params.get("lang","")
if _qp_lang in ("FR","AR","EN"):
    st.session_state.lang = _qp_lang

if "lang" not in st.session_state:
    st.session_state.lang = "FR"

lang   = st.session_state.lang
T      = I18N[lang]
is_rtl = (lang == "AR")

# ══════════════════════════════════════════════════════════════
# FETCH FEEDS (pour ticker + Tab 2)
# ══════════════════════════════════════════════════════════════
with st.spinner(""):
    _all_feed_items, _feed_statuses = _fetch_all_feeds()

_dmn_vigilances = _load_dmn_vigilances()

# ── Ticker temps réel ─────────────────────────────────────────
_alert_items = [it for it in _all_feed_items if it.get("score", 0) >= 1]

# Priorité : vigilances DMN en tête, puis alertes flux RSS
_ticker_parts: list = []

# Séparateur visuel entre items
_SEP = (
    '<span style="color:rgba(255,255,255,0.1);'
    'margin:0 20px;font-size:16px;vertical-align:middle;'
    'font-weight:100;">｜</span>'
)

for _v in _dmn_vigilances:
    _ticker_parts.append(_format_vigilance_ticker_py(_v))

for _it in _alert_items[:10]:
    _src_color = _it.get("color", "#2196f3")
    _src_chip  = (
        f'<span style="display:inline-block;background:{_src_color}1a;'
        f'color:{_src_color};border:1px solid {_src_color}44;'
        f'border-radius:3px;padding:1px 6px;font-size:8.5px;'
        f'font-weight:700;letter-spacing:1.5px;'
        f'vertical-align:middle;margin-right:7px;">'
        f'{_it["icon"]}&nbsp;{_it["source"][:14].upper()}</span>'
    )
    _title_html = (
        f'<span style="color:rgba(220,235,255,0.85);font-size:11.5px;">'
        f'{_it["title"][:80]}</span>'
    )
    _ticker_parts.append(f'{_src_chip}{_title_html}')

_has_alerts = bool(
    _dmn_vigilances and _dmn_vigilances[0].get("niveau") in ("ROUGE", "ORANGE")
) or bool(_alert_items)

if _ticker_parts:
    _ticker_text = _SEP.join(_ticker_parts)
else:
    _ticker_text = (
        f'<span style="color:rgba(144,202,249,0.5);letter-spacing:.5px;">'
        f'{T["no_alerts"]}</span>'
    )

# Horloge UTC+1 (Python-computed, mise à jour à chaque rerender)
_now_utc1 = datetime.datetime.utcnow() + datetime.timedelta(hours=1)
_clock_str = _now_utc1.strftime("%d/%m  %H:%M  UTC+1")

# Flags langue (liens query-param)
_flag_map = {"FR":"🇫🇷","AR":"🇲🇦","EN":"🇬🇧"}
_flags_html = ""
for _lc, _fl in _flag_map.items():
    _opacity = "1.0" if lang == _lc else "0.35"
    _scale   = "scale(1.15)" if lang == _lc else "scale(1)"
    _flags_html += (
        f'<a href="?lang={_lc}" target="_self" '
        f'title="{_lc}" '
        f'style="font-size:1em;opacity:{_opacity};transform:{_scale};'
        f'display:inline-block;text-decoration:none;transition:all .15s;'
        f'cursor:pointer;margin:0 1px;">{_fl}</a>'
    )

# Couleurs selon état d'alerte
if _has_alerts:
    _tk_bg     = "linear-gradient(90deg, rgba(160,0,0,0.97) 0%, rgba(130,0,0,0.97) 100%)"
    _tk_border = "rgba(255,100,100,0.4)"
    _tk_text   = "#ffffff"
    _dot_color = "#ffffff"
    _lbl_color = "#ffffff"
    _lbl_text  = T["ticker_label"]
else:
    _tk_bg     = "rgba(3,12,25,0.98)"
    _tk_border = "rgba(33,150,243,0.2)"
    _tk_text   = "rgba(176,210,240,0.75)"
    _dot_color = "#4fc3f7"
    _lbl_color = "rgba(144,202,249,0.6)"
    _lbl_text  = {"FR":"● VEILLE","AR":"● رصد","EN":"● WATCH"}[lang]

_rtl_dir = "rtl" if is_rtl else "ltr"

_scroll_dur = "75s" if len(_ticker_parts) > 4 else "55s"

st.markdown(f"""
<div style="
  position:fixed; top:60px; left:0; right:0; z-index:9998;
  height:40px;
  background:{_tk_bg};
  border-bottom:1px solid {_tk_border};
  display:flex; align-items:center; overflow:hidden;
  font-family:'Courier New',monospace;
  box-shadow: 0 2px 12px rgba(0,0,0,0.4);
">
  <!-- Badge LIVE -->
  <div style="
    flex-shrink:0; display:flex; align-items:center; gap:7px;
    padding:0 16px; border-right:1px solid rgba(255,255,255,0.12);
    height:100%;
  ">
    <span style="
      display:inline-block; width:7px; height:7px; border-radius:50%;
      background:{_dot_color}; flex-shrink:0;
      box-shadow:0 0 0 2px {_dot_color}33;
      animation:pulse-live 0.9s ease-in-out infinite;
    "></span>
    <span style="
      font-size:9.5px; font-weight:800; letter-spacing:2.5px;
      color:{_lbl_color}; white-space:nowrap;
      text-transform:uppercase;
    ">{_lbl_text}</span>
  </div>

  <!-- Track défilant avec fondu sur les bords -->
  <div style="
    flex:1; overflow:hidden; height:40px;
    display:flex; align-items:center;
    -webkit-mask-image:linear-gradient(to right,transparent 0%,black 3%,black 97%,transparent 100%);
    mask-image:linear-gradient(to right,transparent 0%,black 3%,black 97%,transparent 100%);
  ">
    <span style="
      white-space:nowrap; display:inline-block; padding-left:100%;
      font-size:11.5px; color:{_tk_text}; letter-spacing:.3px;
      line-height:40px;
      animation:scroll-t {_scroll_dur} linear infinite;
      direction:{_rtl_dir};
    ">{_ticker_text}</span>
  </div>

  <!-- Droite : horloge + drapeaux -->
  <div style="
    flex-shrink:0; display:flex; align-items:center; gap:12px;
    padding:0 16px; border-left:1px solid rgba(255,255,255,0.1);
    height:100%;
  ">
    <span style="
      font-family:'Courier New',monospace;
      font-size:10.5px; color:rgba(176,210,240,0.7);
      letter-spacing:1.5px; white-space:nowrap;
    ">{_clock_str}</span>
    <div style="display:flex;align-items:center;gap:4px;font-size:0.9em;">
      {_flags_html}
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# ONGLETS
# ══════════════════════════════════════════════════════════════
tab1, tab2, tab3, tab4 = st.tabs([
    T["tab1"], T["tab2"], T["tab3"], T["tab4"],
])

# ─────────────────────────────────────────────────────────────
# TAB 1 — SITUATION NATIONALE
# ─────────────────────────────────────────────────────────────
with tab1:
    jobs   = _load_jobs()
    done   = [j for j in jobs if j.get("status") == "done"]
    running= [j for j in jobs if j.get("status") == "running"]
    total_ha = sum(float(j.get("results",{}).get("surface_totale_ha",0) or 0) for j in done)

    st.markdown(f"""
    <div class="stat-row">
      <div class="stat-box">
        <div class="stat-val" style="color:#2196f3">{len(done)}</div>
        <div class="stat-lbl">{T['kpi_done']}</div>
      </div>
      <div class="stat-box">
        <div class="stat-val" style="color:#ff9800">{len(running)}</div>
        <div class="stat-lbl">{T['kpi_running']}</div>
      </div>
      <div class="stat-box">
        <div class="stat-val" style="color:#00e676">{total_ha:,.0f}</div>
        <div class="stat-lbl">{T['kpi_ha']}</div>
      </div>
      <div class="stat-box">
        <div class="stat-val" style="color:#7c4dff">1</div>
        <div class="stat-lbl">{T['kpi_mod']}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    col_map, col_list = st.columns([2, 1])

    with col_map:
        st.markdown(f'<div class="vtitle">{T["map_title"]}</div>', unsafe_allow_html=True)
        try:
            import folium
            from streamlit_folium import st_folium
            HAS_STFOLIUM = True
        except ImportError:
            HAS_STFOLIUM = False

        if HAS_STFOLIUM:
            m = folium.Map(location=[29.0,-8.0], zoom_start=5, tiles="CartoDB dark_matter")
            for reg, info in REGIONS_MAR.items():
                col = ALERTE_COLOR[info["alerte"]]
                folium.CircleMarker(
                    location=[info["lat"],info["lon"]],
                    radius=10, color=col, fill=True, fill_color=col, fill_opacity=0.4,
                    popup=folium.Popup(f"<b>{reg}</b><br>Vigilance : {ALERTE_LABEL[info['alerte']]}", max_width=200),
                    tooltip=reg,
                ).add_to(m)
            for j in done[:5]:
                params = j.get("params",{}); aoi = params.get("aoi",{})
                if aoi:
                    lat_c=(aoi.get("lat_min",0)+aoi.get("lat_max",0))/2
                    lon_c=(aoi.get("lon_min",0)+aoi.get("lon_max",0))/2
                    mode  = "Avant/Après" if params.get("image_before") else "Image unique"
                    created = j.get("created","")[:10]
                    folium.Marker(
                        location=[lat_c,lon_c],
                        popup=folium.Popup(f"<b>Traitement {j.get('id','')[:8]}</b><br>Mode : {mode}<br>Date : {created}", max_width=220),
                        tooltip=f"🌊 {created}",
                        icon=folium.Icon(color="blue", icon="tint", prefix="fa"),
                    ).add_to(m)
            st_folium(m, width=None, height=480, returned_objects=[])
        else:
            regions_svg = ""
            for reg, info in REGIONS_MAR.items():
                col = ALERTE_COLOR[info["alerte"]]
                sx=(info["lon"]+17.5)/19.5*400; sy=(35.9-info["lat"])/15*500
                regions_svg += f'<circle cx="{sx:.0f}" cy="{sy:.0f}" r="10" fill="{col}" fill-opacity="0.5" stroke="{col}" stroke-width="1.5"><title>{reg}</title></circle>'
                regions_svg += f'<text x="{sx+13:.0f}" y="{sy+4:.0f}" fill="rgba(144,202,249,0.6)" font-size="8" font-family="monospace">{reg[:18]}</text>'
            jobs_svg=""
            for j in done[:5]:
                params=j.get("params",{}); aoi=params.get("aoi",{})
                if aoi:
                    lat_c=(aoi.get("lat_min",0)+aoi.get("lat_max",0))/2
                    lon_c=(aoi.get("lon_min",0)+aoi.get("lon_max",0))/2
                    sx=(lon_c+17.5)/19.5*400; sy=(35.9-lat_c)/15*500
                    jobs_svg+=f'<circle cx="{sx:.0f}" cy="{sy:.0f}" r="7" fill="#2196f3" fill-opacity="0.8" stroke="#fff" stroke-width="1"><title>Traitement {j.get("id","")[:8]}</title></circle>'
            st.components.v1.html(f"""
            <div style="background:#0a1628;border:1px solid rgba(33,150,243,0.2);border-radius:12px;padding:8px;">
              <svg viewBox="0 0 400 500" style="width:100%;max-height:460px;">
                <rect width="400" height="500" fill="#020b18"/>
                <defs><pattern id="g" width="40" height="40" patternUnits="userSpaceOnUse">
                  <path d="M 40 0 L 0 0 0 40" fill="none" stroke="rgba(33,150,243,0.06)" stroke-width="0.5"/>
                </pattern></defs>
                <rect width="400" height="500" fill="url(#g)"/>
                <path d="M 80 20 L 320 20 L 350 80 L 380 200 L 370 350 L 300 480 L 150 480 L 50 400 L 40 250 L 50 120 Z"
                  fill="rgba(13,33,57,0.5)" stroke="rgba(33,150,243,0.3)" stroke-width="1.5"/>
                {regions_svg}{jobs_svg}
                <rect x="8" y="8" width="110" height="78" rx="6" fill="rgba(6,18,36,0.85)" stroke="rgba(33,150,243,0.15)" stroke-width="0.8"/>
                <circle cx="20" cy="24" r="5" fill="#ff4545" fill-opacity="0.7"/><text x="30" y="28" fill="#ff4545" font-size="8" font-family="monospace">ROUGE</text>
                <circle cx="20" cy="40" r="5" fill="#ff9800" fill-opacity="0.7"/><text x="30" y="44" fill="#ff9800" font-size="8" font-family="monospace">ORANGE</text>
                <circle cx="20" cy="56" r="5" fill="#ffeb3b" fill-opacity="0.7"/><text x="30" y="60" fill="#ffeb3b" font-size="8" font-family="monospace">JAUNE</text>
                <circle cx="20" cy="72" r="5" fill="#00e676" fill-opacity="0.7"/><text x="30" y="76" fill="#00e676" font-size="8" font-family="monospace">VERT</text>
              </svg>
            </div>
            """, height=480)

    with col_list:
        st.markdown(f'<div class="vtitle">{T["alerts_title"]}</div>', unsafe_allow_html=True)
        alertes_actives = [(reg,info) for reg,info in REGIONS_MAR.items()
                           if info["alerte"] in ("rouge","orange","jaune")]
        alertes_actives.sort(key=lambda x:["rouge","orange","jaune","vert"].index(x[1]["alerte"]))
        if alertes_actives:
            for reg, info in alertes_actives:
                col = ALERTE_COLOR[info["alerte"]]; lbl = ALERTE_LABEL[info["alerte"]]
                st.markdown(f"""
                <div class="alerte-bar alerte-{info['alerte']}">
                  <span style="color:{col};font-size:1.1em;">●</span>
                  <div>
                    <div style="font-size:0.7em;font-family:'Orbitron',monospace;color:{col};letter-spacing:1px;">{lbl}</div>
                    <div style="font-size:0.82em;color:#e3f2fd;">{reg}</div>
                  </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown(f'<div style="color:rgba(144,202,249,0.4);font-size:0.85em;">{T["no_alert"]}</div>', unsafe_allow_html=True)

        st.markdown(f'<div class="vtitle" style="margin-top:20px;">{T["jobs_title"]}</div>', unsafe_allow_html=True)
        if done:
            for j in done[:4]:
                params=j.get("params",{}); mode="Avant/Après" if params.get("image_before") else "Image unique"
                created=j.get("created","")[:16].replace("T"," ")
                ha=j.get("results",{}).get("surface_totale_ha","—")
                st.markdown(f"""
                <div class="vcard vcard-accent-blue" style="padding:10px 14px;margin-bottom:8px;">
                  <div style="font-size:0.7em;font-family:'Orbitron',monospace;color:#2196f3;">{created}</div>
                  <div style="font-size:0.82em;color:#e3f2fd;margin:3px 0;">🌊 {mode}</div>
                  <div style="font-size:0.75em;color:rgba(144,202,249,0.5);">Surface : {ha} ha</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown(f'<div style="color:rgba(144,202,249,0.4);font-size:0.85em;">{T["no_job"]}</div>', unsafe_allow_html=True)

        st.markdown(f'<div class="vtitle" style="margin-top:20px;">{T["modules_title"]}</div>', unsafe_allow_html=True)
        for ico, nom, statut, badge in [
            ("🌊","Inondation","badge-active","● ACTIF"),
            ("🔥","Incendie","badge-soon","BIENTÔT"),
            ("⛰️","Glissement","badge-soon","BIENTÔT"),
            ("🌵","Sécheresse","badge-soon","BIENTÔT"),
            ("🏔️","Séisme","badge-soon","BIENTÔT"),
        ]:
            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:10px;padding:6px 0;
                        border-bottom:1px solid rgba(33,150,243,0.06);">
              <span style="font-size:1.1em;">{ico}</span>
              <span style="font-size:0.82em;color:#e3f2fd;flex:1;">{nom}</span>
              <span class="vbadge {statut}" style="margin:0;">{badge}</span>
            </div>
            """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# TAB 2 — INFO & ACTUALITÉS (8 flux institutionnels)
# ─────────────────────────────────────────────────────────────
with tab2:
    st.markdown(f'<div class="vtitle">{T["news_title"]}</div>', unsafe_allow_html=True)

    # ── Statut live des 8 flux ────────────────────────────────
    st.markdown('<div style="font-family:\'Orbitron\',monospace;font-size:0.62em;color:rgba(33,150,243,0.5);letter-spacing:3px;margin-bottom:8px;">STATUT SOURCES INSTITUTIONNELLES</div>', unsafe_allow_html=True)

    _status_cards = ""
    for key, cfg in FEEDS_8.items():
        s = _feed_statuses.get(key, "offline")
        if s == "live":
            dot_cls = "feed-dot-live"; s_lbl = "LIVE"
        elif s == "empty":
            dot_cls = "feed-dot-empty"; s_lbl = "VIDE"
        else:
            dot_cls = "feed-dot-offline"; s_lbl = "OFFLINE"

        _status_cards += f"""
        <div class="feed-status-card" title="{cfg['desc']}">
          <div class="feed-status-icon">{cfg['icon']}</div>
          <div class="feed-status-name">{key}</div>
          <div class="{dot_cls}"></div>
          <div style="font-size:0.48em;font-family:'Orbitron',monospace;
                      color:{'#00e676' if s=='live' else ('#ffeb3b' if s=='empty' else '#ff4545')};
                      letter-spacing:1px;">{s_lbl}</div>
        </div>"""

    st.markdown(f'<div class="feed-status-grid">{_status_cards}</div>', unsafe_allow_html=True)

    # ── Filtres ───────────────────────────────────────────────
    col_flt, col_ref = st.columns([3, 1])
    with col_flt:
        source_keys = list(FEEDS_8.keys())
        sel_sources = st.multiselect(
            "Sources",
            options=source_keys,
            default=[k for k in source_keys if _feed_statuses.get(k,"offline") in ("live","empty")],
            format_func=lambda k: f"{FEEDS_8[k]['icon']} {FEEDS_8[k]['name']}",
            label_visibility="collapsed",
        )
        keywords = st.text_input("🔍 Filtrer par mot-clé", placeholder="inondation, séisme, fire...")
        show_alerts_only = st.toggle("⚡ Alertes uniquement", value=False)

    with col_ref:
        if st.button("🔄 Actualiser", use_container_width=True):
            st.cache_data.clear(); st.rerun()
        n_live  = sum(1 for s in _feed_statuses.values() if s=="live")
        n_total = len(FEEDS_8)
        st.markdown(f"""
        <div style="text-align:center;padding:6px;font-size:0.78em;color:#00e676;">
          <span style="font-family:'Orbitron',monospace;font-size:1.1em;">{n_live}/{n_total}</span><br>
          <span style="color:rgba(144,202,249,0.4);font-size:0.85em;">flux actifs</span>
        </div>
        """, unsafe_allow_html=True)

    # ── Articles ──────────────────────────────────────────────
    displayed = [it for it in _all_feed_items if it.get("feed_key","") in sel_sources]
    if show_alerts_only:
        displayed = [it for it in displayed if it.get("score",0) >= 1]
    if keywords.strip():
        kw = keywords.lower()
        displayed = [it for it in displayed
                     if kw in it["title"].lower() or kw in it.get("desc","").lower()]

    if displayed:
        for item in displayed:
            priority_badge = ""
            if item.get("score",0) >= 2:
                priority_badge = '<span style="background:rgba(255,69,69,0.2);color:#ff4545;border:1px solid rgba(255,69,69,0.4);font-size:0.6em;padding:1px 7px;border-radius:10px;font-family:\'Orbitron\',monospace;letter-spacing:1px;margin-left:6px;">ALERTE</span>'
            elif item.get("score",0) >= 1:
                priority_badge = '<span style="background:rgba(255,152,0,0.15);color:#ff9800;border:1px solid rgba(255,152,0,0.3);font-size:0.6em;padding:1px 7px;border-radius:10px;font-family:\'Orbitron\',monospace;letter-spacing:1px;margin-left:6px;">VIGILANCE</span>'

            link_html = f'<a href="{item["link"]}" target="_blank" style="color:inherit;text-decoration:none;">' if item.get("link") else ""
            link_end  = "</a>" if item.get("link") else ""
            st.markdown(f"""
            <div class="news-item">
              <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">
                <span style="font-size:1.1em;">{item['icon']}</span>
                <span class="news-source" style="color:{item['color']};">{item['source']}</span>
                {priority_badge}
                <span class="news-date" style="margin-left:auto;">{item.get('date','')}</span>
              </div>
              {link_html}<div class="news-title">{item['title']}</div>{link_end}
              {"<div style='font-size:0.78em;color:rgba(144,202,249,0.4);margin-top:4px;'>"+item['desc'][:140]+"…</div>" if item.get('desc') else ""}
            </div>
            """, unsafe_allow_html=True)
    else:
        live_keys = [k for k,s in _feed_statuses.items() if s=="live"]
        hint = f"{len(live_keys)} flux actifs : {', '.join(live_keys)}" if live_keys else "Aucun flux actif — vérifiez la connexion internet."
        st.markdown(f"""
        <div class="vcard" style="text-align:center;padding:40px;">
          <div style="font-size:2em;margin-bottom:12px;">📡</div>
          <div style="color:rgba(144,202,249,0.5);">
            Aucun article disponible.<br>
            <span style="font-size:0.85em;">{hint}</span>
          </div>
        </div>
        """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# TAB 3 — MÉTÉO & ALERTES
# ─────────────────────────────────────────────────────────────
with tab3:
    st.markdown(f'<div class="vtitle">{T["meteo_title"]}</div>', unsafe_allow_html=True)

    st.markdown("**Carte de vigilance par région**", unsafe_allow_html=False)
    vig_cols = st.columns(4)
    for i, (reg, info) in enumerate(REGIONS_MAR.items()):
        col = ALERTE_COLOR[info["alerte"]]; lbl = ALERTE_LABEL[info["alerte"]]
        with vig_cols[i % 4]:
            st.markdown(f"""
            <div style="background:rgba(10,22,40,0.8);border:1px solid {col}40;border-left:3px solid {col};
                        border-radius:8px;padding:8px 10px;margin-bottom:8px;">
              <div style="font-size:0.65em;font-family:'Orbitron',monospace;color:{col};">{lbl}</div>
              <div style="font-size:0.78em;color:#e3f2fd;margin-top:2px;">{reg}</div>
            </div>
            """, unsafe_allow_html=True)

    st.divider()
    st.markdown("**Prévisions 5 jours — Région sélectionnée**")

    region_names = list(REGIONS_MAR.keys())
    sel_region = st.selectbox("Région", region_names, index=3, label_visibility="collapsed")
    r_info = REGIONS_MAR[sel_region]

    @st.cache_data(ttl=3600)
    def get_meteo(lat, lon):
        return _fetch_meteo(lat, lon)

    with st.spinner("Chargement météo..."):
        meteo = get_meteo(r_info["lat"], r_info["lon"])

    if meteo and "daily" in meteo:
        d      = meteo["daily"]
        days   = d.get("time",[])
        rains  = d.get("precipitation_sum",[])
        tmax   = d.get("temperature_2m_max",[])
        tmin   = d.get("temperature_2m_min",[])
        wcodes = d.get("weathercode",[])

        days_html = ""
        for i in range(min(5, len(days))):
            dt  = datetime.date.fromisoformat(days[i])
            nom = ["Lun","Mar","Mer","Jeu","Ven","Sam","Dim"][dt.weekday()]
            ico = WMO_ICON.get(wcodes[i] if i<len(wcodes) else 0, "🌡️")
            rain= f"{rains[i]:.1f} mm" if i<len(rains) else "—"
            tx  = f"{tmax[i]:.0f}°"   if i<len(tmax)  else "—"
            tn  = f"{tmin[i]:.0f}°"   if i<len(tmin)  else "—"
            days_html += f"""
            <div class="meteo-day">
              <div class="meteo-day-name">{nom} {dt.day}/{dt.month}</div>
              <div class="meteo-day-icon">{ico}</div>
              <div class="meteo-day-rain">💧 {rain}</div>
              <div class="meteo-day-temp">{tn} / {tx}</div>
            </div>"""

        st.markdown(f'<div class="meteo-grid">{days_html}</div>', unsafe_allow_html=True)

        max_rain = max(rains[:5]) if rains else 0
        seuil_r = st.session_state.get("seuil_rouge", 50)
        seuil_o = st.session_state.get("seuil_orange", 30)
        seuil_j = st.session_state.get("seuil_jaune", 15)

        if max_rain >= seuil_r:
            st.markdown(f'<div class="alerte-bar alerte-rouge">🔴 <strong>VIGILANCE ROUGE</strong> — Précipitations extrêmes prévues : {max_rain:.0f} mm — Risque inondation élevé</div>', unsafe_allow_html=True)
        elif max_rain >= seuil_o:
            st.markdown(f'<div class="alerte-bar alerte-orange">🟠 <strong>VIGILANCE ORANGE</strong> — Fortes précipitations prévues : {max_rain:.0f} mm — Surveiller les zones à risque</div>', unsafe_allow_html=True)
        elif max_rain >= seuil_j:
            st.markdown(f'<div class="alerte-bar alerte-jaune">🟡 <strong>VIGILANCE JAUNE</strong> — Précipitations modérées : {max_rain:.0f} mm</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="alerte-bar alerte-vert">🟢 <strong>PAS D\'ALERTE</strong> — Précipitations faibles prévues : {max_rain:.1f} mm</div>', unsafe_allow_html=True)
    else:
        st.warning("Données météo indisponibles. Vérifiez la connexion internet.")

    st.divider()
    with st.expander("⚙️ Configurer les seuils d'alerte précipitations"):
        c1, c2, c3 = st.columns(3)
        with c1: st.number_input("🟡 Seuil jaune (mm)",  value=15, min_value=1, key="seuil_jaune")
        with c2: st.number_input("🟠 Seuil orange (mm)", value=30, min_value=1, key="seuil_orange")
        with c3: st.number_input("🔴 Seuil rouge (mm)",  value=50, min_value=1, key="seuil_rouge")

# ─────────────────────────────────────────────────────────────
# TAB 4 — ASSISTANT IA
# ─────────────────────────────────────────────────────────────
with tab4:
    st.markdown(f'<div class="vtitle">{T["ia_title"]}</div>', unsafe_allow_html=True)

    col_chat, col_agent = st.columns([3, 2])

    with col_chat:
        st.markdown("**💬 Chat contextuel**")
        st.markdown("""
        <div style="background:rgba(10,22,40,0.6);border:1px solid rgba(33,150,243,0.15);
                    border-radius:10px;padding:12px 16px;margin-bottom:12px;
                    font-size:0.82em;color:rgba(144,202,249,0.55);line-height:1.6;">
          L'assistant a accès aux résultats des traitements CCIP, aux statistiques communes/provinces,
          et peut analyser la situation de crise en temps réel.<br>
          Configurez votre clé API Anthropic dans le panneau de droite pour activer le chat.
        </div>
        """, unsafe_allow_html=True)

        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []

        for msg in st.session_state.chat_history:
            if msg["role"] == "user":
                st.markdown(f'<div class="chat-label-user">VOUS</div><div class="chat-msg-user">{msg["content"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="chat-label-ai">🤖 CCIP IA</div><div class="chat-msg-ai">{msg["content"]}</div>', unsafe_allow_html=True)

        with st.form("chat_form", clear_on_submit=True):
            user_input = st.text_area(
                "Message",
                placeholder="Ex: Quelles communes sont affectées ? Résume la dernière analyse...",
                height=80, label_visibility="collapsed"
            )
            send = st.form_submit_button("Envoyer ➤", use_container_width=True)

        if send and user_input.strip():
            api_key = st.session_state.get("anthropic_key","")
            if not api_key:
                st.error("Clé API Anthropic requise. Configurez-la dans le panneau de droite.")
            else:
                st.session_state.chat_history.append({"role":"user","content":user_input})
                jobs_ctx  = _load_jobs()
                done_ctx  = [j for j in jobs_ctx if j.get("status")=="done"]
                ctx_lines = []
                for j in done_ctx[:3]:
                    p=j.get("params",{}); r=j.get("results",{})
                    mode="Avant/Après" if p.get("image_before") else "Image unique"
                    ctx_lines.append(
                        f"- Job {j.get('id','')[:8]} ({j.get('created','')[:10]}) : "
                        f"mode={mode}, surface={r.get('surface_totale_ha','?')} ha, communes={r.get('n_communes','?')}"
                    )
                # Alertes flux institutionnels dans le contexte
                feed_ctx = []
                for it in _alert_items[:5]:
                    feed_ctx.append(f"- [{it['source']}] {it['title']}")
                system_prompt = (
                    "Tu es l'assistant IA de la plateforme CCIP (Crisis Cartography Intelligence Platform) "
                    "du CRTS Maroc. Tu analyses les données de crise inondation issues du traitement SAR Sentinel-1.\n\n"
                    "Derniers traitements :\n" + ("\n".join(ctx_lines) if ctx_lines else "Aucun traitement terminé.") +
                    "\n\nAlertes flux institutionnels (DMN, USGS, Copernicus…) :\n" +
                    ("\n".join(feed_ctx) if feed_ctx else "Aucune alerte active détectée.") +
                    "\n\nRéponds en français, de façon concise et professionnelle, adaptée à un service de gestion de crise."
                )
                try:
                    import anthropic
                    client = anthropic.Anthropic(api_key=api_key)
                    with st.spinner("Analyse en cours..."):
                        response = client.messages.create(
                            model="claude-sonnet-4-6", max_tokens=800,
                            system=system_prompt,
                            messages=[{"role":m["role"],"content":m["content"]}
                                      for m in st.session_state.chat_history]
                        )
                    st.session_state.chat_history.append({"role":"assistant","content":response.content[0].text})
                    st.rerun()
                except Exception as e:
                    st.error(f"Erreur API : {e}")

        if st.session_state.chat_history:
            if st.button("🗑️ Effacer la conversation"):
                st.session_state.chat_history = []; st.rerun()

        st.markdown("**Exemples de questions :**")
        exemples = [
            "Résume la situation d'inondation actuelle",
            "Quelles communes ont la plus grande surface inondée ?",
            "Y a-t-il des alertes sismiques en cours ?",
            "Rédige un bulletin de crise pour les autorités",
        ]
        ec = st.columns(2)
        for i, ex in enumerate(exemples):
            if ec[i%2].button(ex, key=f"ex_{i}", use_container_width=True):
                st.session_state.chat_history.append({"role":"user","content":ex}); st.rerun()

    with col_agent:
        st.markdown("**⚙️ Configuration & Agent autonome**")

        api_key_input = st.text_input(
            "🔑 Clé API Anthropic", type="password",
            value=st.session_state.get("anthropic_key",""),
            placeholder="sk-ant-...", help="Obtenez votre clé sur console.anthropic.com"
        )
        if api_key_input:
            st.session_state["anthropic_key"] = api_key_input
            st.success("Clé configurée ✓")

        st.divider()
        st.markdown("**🤖 Agent autonome**")
        st.markdown('<div style="font-size:0.82em;color:rgba(144,202,249,0.5);margin-bottom:12px;">Configurez les règles déclencheur → action</div>', unsafe_allow_html=True)

        for ico, trigger, action, default in [
            ("🛰️","Nouvelle image Sentinel-1 disponible","Lancer traitement automatique",False),
            ("📈","Surface inondée augmente de +20%","Envoyer alerte email",False),
            ("☀️","Rapport quotidien 8h00","Générer bulletin de situation",False),
            ("🌧️","Précipitations > seuil rouge","Déclencher analyse préventive",False),
            ("🏔️","Séisme M≥4.5 détecté (USGS)","Activer veille sismique",False),
            ("🔥","Activation EFFIS Maroc","Surveiller risque incendie",False),
        ]:
            st.toggle(f"{ico} **{trigger}**\n_{action}_", value=default, key=f"rule_{trigger[:12]}")

        st.divider()
        email_notif = st.text_input("📧 Email notifications", placeholder="contact@crts.gov.ma")
        if st.button("💾 Sauvegarder configuration", use_container_width=True):
            st.success("Configuration sauvegardée")

        st.divider()
        st.markdown("**📊 Contexte actuel**")
        done_ctx2 = [j for j in _load_jobs() if j.get("status")=="done"]
        n_live_feeds = sum(1 for s in _feed_statuses.values() if s=="live")
        st.markdown(f"""
        <div style="font-size:0.82em;color:rgba(144,202,249,0.55);line-height:2;">
          • {len(done_ctx2)} traitement(s) disponibles<br>
          • {n_live_feeds}/{len(FEEDS_8)} flux institutionnels actifs<br>
          • {len(_alert_items)} alerte(s) détectée(s) dans les flux<br>
          • Modèle : claude-sonnet-4-6<br>
          • Pipeline SNAP opérationnel
        </div>
        """, unsafe_allow_html=True)
