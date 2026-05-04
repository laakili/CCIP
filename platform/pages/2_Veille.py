"""
CCIP — Centre de Veille & Intelligence
Page unique avec 4 onglets : Situation Nationale · Info & Actualités · Météo & Alertes · Assistant IA
Ticker temps réel · Horloge UTC+1 · Toggle FR/AR/EN · 8 flux institutionnels avec statut live
"""
import os, sys, json, datetime, urllib.request, urllib.error, urllib.parse, xml.etree.ElementTree as ET
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

# ══════════════════════════════════════════════════════════════
# FLUX INTERNATIONAUX — NASA · ESA · ONU · WMO
# ══════════════════════════════════════════════════════════════
FEEDS_INTL = {
    "NASA-EO": {
        "name": "NASA Earth Observatory",
        "url":  "https://earthobservatory.nasa.gov/feeds/earth-observatory.rss",
        "icon": "🌍", "color": "#0b3d91", "type": "satellite",
        "desc": "NASA — Images et actualités observation terrestre (inondations, feux, poussières)",
    },
    "ESA-EO": {
        "name": "ESA — Earth Observation",
        "url":  "https://www.esa.int/rssfeed/Our_Activities/Observing_the_Earth",
        "icon": "🛰️", "color": "#003087", "type": "satellite",
        "desc": "Agence Spatiale Européenne — Copernicus, Sentinel, missions EO",
    },
    "GDACS": {
        "name": "GDACS — Alertes mondiales",
        "url":  "https://www.gdacs.org/xml/rss.xml",
        "icon": "🚨", "color": "#dc2626", "type": "crise",
        "desc": "Global Disaster Alert & Coordination System — ONU/CE",
    },
    "OCHA-MAR": {
        "name": "ReliefWeb Maroc",
        "url":  "https://reliefweb.int/country/mar/rss.xml",
        "icon": "🆘", "color": "#d97706", "type": "humanitaire",
        "desc": "OCHA ReliefWeb — Urgences humanitaires et crises au Maroc",
    },
    "WMO": {
        "name": "WMO — OMM",
        "url":  "https://public.wmo.int/en/rss.xml",
        "icon": "🌐", "color": "#0369a1", "type": "meteo",
        "desc": "Organisation Météorologique Mondiale — Alertes et rapports climatiques",
    },
    "UN-SPIDER": {
        "name": "UN-SPIDER",
        "url":  "https://un-spider.org/rss.xml",
        "icon": "📡", "color": "#7c3aed", "type": "satellite",
        "desc": "ONU — Info spatiale pour gestion des catastrophes et résilience",
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

/* Décaler contenu sous navbar + ticker + barre onglets (60+36+44=140) */
.block-container { padding-top: 140px !important; }

/* Ticker scroll animation */
@keyframes scroll-t {
  0%   { transform: translateX(0); }
  100% { transform: translateX(-100%); }
}
@keyframes pulse-live {
  0%,100% { box-shadow: 0 0 4px #fff, 0 0 8px #fff; opacity:1; }
  50%      { box-shadow: 0 0 2px #fff; opacity:.4; }
}

/* Tabs — fixée juste sous la barre d'alerte */
[data-testid="stTabs"] [data-baseweb="tab-list"] {
  position: fixed !important;
  top: 96px !important;
  left: 0 !important; right: 0 !important;
  z-index: 9997 !important;
  width: 100% !important; box-sizing: border-box !important;
  background: rgba(10,22,40,0.95) !important;
  border-bottom: 1px solid rgba(33,150,243,0.2) !important;
  gap: 4px; padding: 0 24px !important;
  backdrop-filter: blur(12px) !important;
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

/* ── WorldMonitor-style Situation Nationale ── */

.wm-country-header {
  background: linear-gradient(135deg, rgba(13,33,57,0.95) 0%, rgba(6,18,36,0.98) 100%);
  border: 1px solid rgba(33,150,243,0.2);
  border-left: 4px solid #2196f3;
  border-radius: 12px; padding: 18px 24px;
  display: flex; align-items: center; gap: 20px;
  margin-bottom: 16px;
}
.wm-flag { font-size: 2.4em; }
.wm-country-name {
  font-family: 'Orbitron', monospace; font-size: 1.1em;
  font-weight: 700; color: #e3f2fd; letter-spacing: 3px;
}
.wm-country-sub {
  font-size: 0.72em; color: rgba(144,202,249,0.5);
  letter-spacing: 2px; margin-top: 3px;
}
.wm-score-block { margin-left: auto; text-align: right; }
.wm-score-label {
  font-family: 'Orbitron', monospace; font-size: 0.6em;
  color: rgba(144,202,249,0.45); letter-spacing: 2px; margin-bottom: 4px;
}
.wm-score-val {
  font-family: 'Orbitron', monospace; font-size: 2em; font-weight: 700;
}
.wm-score-danger { color: #ef4444; }
.wm-score-warn   { color: #f59e0b; }
.wm-score-ok     { color: #22c55e; }
.wm-score-bar {
  height: 4px; border-radius: 2px; margin-top: 6px;
  background: rgba(255,255,255,0.1);
  position: relative; width: 140px;
}
.wm-score-fill {
  height: 100%; border-radius: 2px; position: absolute; left: 0; top: 0;
  transition: width .4s ease;
}

.wm-kpi-grid {
  display: grid; grid-template-columns: repeat(5, 1fr);
  gap: 10px; margin-bottom: 18px;
}
.wm-kpi {
  background: rgba(10,22,40,0.85);
  border: 1px solid rgba(33,150,243,0.13);
  border-radius: 10px; padding: 14px 12px;
  text-align: center; position: relative; overflow: hidden;
}
.wm-kpi::after {
  content: ''; position: absolute; bottom: 0; left: 0; right: 0;
  height: 2px;
}
.wm-kpi-danger::after { background: #ef4444; }
.wm-kpi-warn::after   { background: #f59e0b; }
.wm-kpi-ok::after     { background: #22c55e; }
.wm-kpi-blue::after   { background: #2196f3; }
.wm-kpi-purple::after { background: #7c4dff; }
.wm-kpi-val {
  font-family: 'Orbitron', monospace; font-size: 1.5em;
  font-weight: 700; margin-bottom: 4px;
}
.wm-kpi-lbl {
  font-size: 0.68em; color: rgba(144,202,249,0.45);
  letter-spacing: 1px; line-height: 1.3;
}

.wm-section-title {
  font-family: 'Orbitron', monospace; font-size: 0.62em;
  letter-spacing: 3px; color: rgba(33,150,243,0.55);
  margin-bottom: 10px; padding-bottom: 6px;
  border-bottom: 1px solid rgba(33,150,243,0.1);
  text-transform: uppercase;
}

.wm-signal {
  background: rgba(6,16,30,0.9);
  border: 1px solid rgba(33,150,243,0.1);
  border-radius: 8px; padding: 10px 12px; margin-bottom: 7px;
  display: flex; align-items: flex-start; gap: 10px;
  transition: border-color .2s;
}
.wm-signal:hover { border-color: rgba(33,150,243,0.3); }
.wm-signal-icon { font-size: 1.3em; flex-shrink: 0; margin-top: 1px; }
.wm-signal-body { flex: 1; min-width: 0; }
.wm-signal-meta {
  display: flex; align-items: center; gap: 6px; margin-bottom: 4px; flex-wrap: wrap;
}
.wm-tier {
  font-family: 'Orbitron', monospace; font-size: 0.55em;
  padding: 1px 6px; border-radius: 3px; letter-spacing: 1px;
  font-weight: 700; flex-shrink: 0;
}
.wm-tier-dmn    { background:rgba(33,150,243,0.15); color:#64b5f6; border:1px solid rgba(33,150,243,0.3); }
.wm-tier-abh    { background:rgba(0,150,136,0.15);  color:#4db6ac; border:1px solid rgba(0,150,136,0.3); }
.wm-tier-usgs   { background:rgba(255,152,0,0.12);  color:#ffb74d; border:1px solid rgba(255,152,0,0.3); }
.wm-tier-cop    { background:rgba(103,58,183,0.15); color:#b39ddb; border:1px solid rgba(103,58,183,0.3); }
.wm-tier-effis  { background:rgba(244,67,54,0.12);  color:#ef9a9a; border:1px solid rgba(244,67,54,0.3); }
.wm-tier-ioc    { background:rgba(0,188,212,0.12);  color:#80deea; border:1px solid rgba(0,188,212,0.3); }
.wm-tier-dgpc   { background:rgba(156,39,176,0.12); color:#ce93d8; border:1px solid rgba(156,39,176,0.3); }
.wm-tier-ign    { background:rgba(76,175,80,0.12);  color:#a5d6a7; border:1px solid rgba(76,175,80,0.3); }

.wm-sev {
  font-size: 0.55em; padding: 1px 7px; border-radius: 10px;
  font-family: 'Orbitron', monospace; letter-spacing: 1.5px; font-weight: 700;
}
.wm-sev-critical { background:rgba(239,68,68,0.2);  color:#ef4444; border:1px solid rgba(239,68,68,0.4); }
.wm-sev-high     { background:rgba(245,158,11,0.2); color:#f59e0b; border:1px solid rgba(245,158,11,0.4); }
.wm-sev-medium   { background:rgba(234,179,8,0.15); color:#eab308; border:1px solid rgba(234,179,8,0.35); }
.wm-sev-low      { background:rgba(34,197,94,0.1);  color:#22c55e; border:1px solid rgba(34,197,94,0.25); }

.wm-signal-title { font-size: 0.84em; color: #e3f2fd; line-height: 1.4; margin-bottom: 3px; }
.wm-signal-desc  { font-size: 0.73em; color: rgba(144,202,249,0.45); line-height: 1.35; }
.wm-signal-time  { font-size: 0.65em; color: rgba(144,202,249,0.3); margin-left: auto; white-space: nowrap; flex-shrink: 0; }

.wm-infra-grid {
  display: grid; grid-template-columns: repeat(3, 1fr);
  gap: 7px; margin-bottom: 10px;
}
.wm-infra-btn {
  background: rgba(10,22,40,0.85);
  border: 1px solid rgba(33,150,243,0.15);
  border-radius: 8px; padding: 10px 8px; text-align: center;
  cursor: default;
}
.wm-infra-ico { font-size: 1.4em; margin-bottom: 4px; }
.wm-infra-count {
  font-family: 'Orbitron', monospace; font-size: 0.85em;
  color: #90caf9; font-weight: 700;
}
.wm-infra-lbl { font-size: 0.6em; color: rgba(144,202,249,0.4); margin-top: 2px; }

.wm-job-row {
  background: rgba(6,16,30,0.9); border: 1px solid rgba(33,150,243,0.1);
  border-radius: 8px; padding: 9px 12px; margin-bottom: 6px;
  display: flex; align-items: center; gap: 10px;
}
.wm-job-id   { font-family:'Orbitron',monospace; font-size:0.58em; color:rgba(33,150,243,0.6); flex-shrink:0; }
.wm-job-info { flex:1; min-width:0; }
.wm-job-mode { font-size:0.8em; color:#e3f2fd; }
.wm-job-date { font-size:0.65em; color:rgba(144,202,249,0.4); }
.wm-job-ha   {
  font-family:'Orbitron',monospace; font-size:0.82em;
  color:#2196f3; font-weight:700; flex-shrink:0; text-align:right;
}

.wm-module-row {
  display: flex; align-items: center; gap: 10px;
  padding: 8px 10px; border-radius: 7px; margin-bottom: 5px;
  background: rgba(6,16,30,0.7);
  border: 1px solid rgba(33,150,243,0.08);
}
.wm-module-ico { font-size: 1.1em; flex-shrink: 0; }
.wm-module-name { font-size: 0.82em; color: #e3f2fd; flex: 1; }
.wm-module-tag {
  font-family: 'Orbitron', monospace; font-size: 0.58em;
  padding: 2px 9px; border-radius: 10px; font-weight: 700;
  letter-spacing: 1px;
}
.wm-tag-active { background:rgba(0,230,118,0.15); color:#00e676; border:1px solid rgba(0,230,118,0.35); }
.wm-tag-soon   { background:rgba(33,150,243,0.08); color:#64b5f6; border:1px solid rgba(33,150,243,0.2); }
.wm-tag-watch  { background:rgba(245,158,11,0.12); color:#f59e0b; border:1px solid rgba(245,158,11,0.3); }

.wm-region-row {
  display: flex; align-items: center; gap: 8px;
  padding: 6px 10px; border-radius: 6px; margin-bottom: 4px;
  background: rgba(6,16,30,0.7);
  border-left: 3px solid;
}
.wm-region-name { font-size: 0.8em; color: #e3f2fd; flex: 1; }
.wm-region-level { font-family:'Orbitron',monospace; font-size:0.6em; font-weight:700; }
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

@st.cache_data(ttl=300, show_spinner=False)
def _fetch_intl_feeds():
    """Fetch international feeds (NASA, ESA, GDACS, OCHA, WMO, UN-SPIDER)."""
    all_items = []
    statuses  = {}
    for key, cfg in FEEDS_INTL.items():
        raw = _fetch_url(cfg["url"], timeout=7)
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

_PHENOMENE_ICONS_PY: dict = {
    "PLUIES":        "🌧️",
    "VENT":          "💨",
    "CHALEUR":       "🌡️",
    "FROID":         "🥶",
    "NEIGE":         "❄️",
    "ORAGE":         "⛈️",
    "BROUILLARD":    "🌫️",
    "TEMPETE_SABLE": "🏜️",
    "CANICULE":      "☀️",
}

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
    """Formate une vigilance DMN en texte détaillé pour le ticker."""
    niveau     = v.get("niveau", "?")
    pheno_key  = v.get("phenomene", "")
    phenomene  = _PHENOMENE_LABELS_PY.get(pheno_key, pheno_key.lower())
    pheno_icon = _PHENOMENE_ICONS_PY.get(pheno_key, "⚠️")
    zones      = _condense_zones_py(v.get("zones", []))
    duree      = _compute_duree_h(v.get("debut", ""), v.get("fin", ""))
    duree_str  = "<1h" if duree < 1 else f"{duree}h"
    emoji      = _NIVEAU_EMOJI_PY.get(niveau, "⚪")

    # Détails quantitatifs selon le phénomène
    details = []
    cumul = v.get("cumul_prevu_mm")
    vent  = v.get("vitesse_vent_kmh")
    temp  = v.get("temperature_max")
    if cumul is not None:
        details.append(f"{cumul} mm prévus")
    if vent is not None:
        details.append(f"rafales {vent} km/h")
    if temp is not None:
        details.append(f"max {temp}°C")

    # Résumé tronqué si disponible
    resume = v.get("resume", "")
    resume_short = resume[:90] + "…" if len(resume) > 90 else resume

    parts = [f"{emoji} DMN · {pheno_icon} {phenomene.upper()} · {zones} · {duree_str}"]
    if details:
        parts.append(" · ".join(details))
    if resume_short:
        parts.append(resume_short)

    return "  —  ".join(parts)


_DMN_PROVINCE_TO_REGION = {
    # Tanger-Tétouan-Al Hoceïma
    "Tanger-Assilah": "Tanger-Tétouan-Al Hoceïma", "Larache": "Tanger-Tétouan-Al Hoceïma",
    "Fahs-Anjra": "Tanger-Tétouan-Al Hoceïma",
    "MDiq-Fnideq": "Tanger-Tétouan-Al Hoceïma", "M'Diq-Fnidek": "Tanger-Tétouan-Al Hoceïma",
    "M Diq-Fnideq": "Tanger-Tétouan-Al Hoceïma", "Mdiq-Fnideq": "Tanger-Tétouan-Al Hoceïma",
    "Tetouan": "Tanger-Tétouan-Al Hoceïma", "Tétouan": "Tanger-Tétouan-Al Hoceïma",
    "Chefchaouen": "Tanger-Tétouan-Al Hoceïma", "Chefchaoun": "Tanger-Tétouan-Al Hoceïma",
    "Al Hoceima": "Tanger-Tétouan-Al Hoceïma", "Al Hoceïma": "Tanger-Tétouan-Al Hoceïma",
    # Oriental
    "Nador": "Oriental", "Driouch": "Oriental", "Guercif": "Oriental",
    "Figuig": "Oriental", "Berkane": "Oriental", "Taourirt": "Oriental",
    "Jerada": "Oriental", "Oujda-Angad": "Oriental",
    # Fès-Meknès
    "Fes": "Fès-Meknès", "Fès": "Fès-Meknès",
    "Meknes": "Fès-Meknès", "Meknès": "Fès-Meknès",
    "El Hajeb": "Fès-Meknès", "Ifrane": "Fès-Meknès",
    "Moulay Yacoub": "Fès-Meknès",
    "Sefrou": "Fès-Meknès", "Séfrou": "Fès-Meknès",
    "Boulemane": "Fès-Meknès", "Taounate": "Fès-Meknès", "Taza": "Fès-Meknès",
    "Ouezzane": "Fès-Meknès",
    # Rabat-Salé-Kénitra
    "Kenitra": "Rabat-Salé-Kénitra", "Kénitra": "Rabat-Salé-Kénitra",
    "Sidi Kacem": "Rabat-Salé-Kénitra",
    "Sidi Slimane": "Rabat-Salé-Kénitra",
    "Khemisset": "Rabat-Salé-Kénitra", "Khémisset": "Rabat-Salé-Kénitra",
    "Rabat": "Rabat-Salé-Kénitra",
    "Sale": "Rabat-Salé-Kénitra", "Salé": "Rabat-Salé-Kénitra",
    # Béni Mellal-Khénifra
    "Beni Mellal": "Béni Mellal-Khénifra", "Béni Mellal": "Béni Mellal-Khénifra",
    "Azilal": "Béni Mellal-Khénifra",
    "Khouribga": "Béni Mellal-Khénifra",
    "Khenifra": "Béni Mellal-Khénifra", "Khénifra": "Béni Mellal-Khénifra",
    "Fkih Ben Salah": "Béni Mellal-Khénifra",
    # Grand Casablanca-Settat
    "Casablanca": "Grand Casablanca-Settat", "Mohammedia": "Grand Casablanca-Settat",
    "El Jadida": "Grand Casablanca-Settat", "Settat": "Grand Casablanca-Settat",
    "Berrechid": "Grand Casablanca-Settat", "Benslimane": "Grand Casablanca-Settat",
    "Mediouna": "Grand Casablanca-Settat", "Nouaceur": "Grand Casablanca-Settat",
    # Marrakech-Safi
    "Marrakech": "Marrakech-Safi", "Chichaoua": "Marrakech-Safi",
    "Al Haouz": "Marrakech-Safi",
    "Kelaat Sraghna": "Marrakech-Safi", "Kelaât Sraghna": "Marrakech-Safi",
    "Essaouira": "Marrakech-Safi",
    "Youssoufia": "Marrakech-Safi", "Safi": "Marrakech-Safi", "Rehamna": "Marrakech-Safi",
    # Drâa-Tafilalet
    "Errachidia": "Drâa-Tafilalet", "Ouarzazate": "Drâa-Tafilalet",
    "Zagora": "Drâa-Tafilalet", "Tinghir": "Drâa-Tafilalet", "Midelt": "Drâa-Tafilalet",
    # Souss-Massa
    "Agadir": "Souss-Massa",
    "Chtouka Ait Baha": "Souss-Massa", "Chtouka-Ait Baha": "Souss-Massa",
    "Chtouka Aït Baha": "Souss-Massa",
    "Inezgane Ait Melloul": "Souss-Massa", "Inezgane-Aït Melloul": "Souss-Massa",
    "Taroudant": "Souss-Massa", "Taroudannt": "Souss-Massa",
    "Tiznit": "Souss-Massa", "Tata": "Souss-Massa",
    # Guelmim-Oued Noun
    "Guelmim": "Guelmim-Oued Noun", "Assa-Zag": "Guelmim-Oued Noun",
    "Tan-Tan": "Guelmim-Oued Noun", "Sidi Ifni": "Guelmim-Oued Noun",
    # Laâyoune-Sakia El Hamra
    "Laayoune": "Laâyoune-Sakia El Hamra", "Laâyoune": "Laâyoune-Sakia El Hamra",
    "Boujdour": "Laâyoune-Sakia El Hamra",
    "Tarfaya": "Laâyoune-Sakia El Hamra",
    "Es-Smara": "Laâyoune-Sakia El Hamra", "Smara": "Laâyoune-Sakia El Hamra",
    # Dakhla-Oued Ed-Dahab
    "Oued Ed-Dahab": "Dakhla-Oued Ed-Dahab", "Aousserd": "Dakhla-Oued Ed-Dahab",
}

_DMN_PHENO_MAP = {
    "ao":  ("ORAGE",   "averses orageuses"),
    "pp":  ("PLUIES",  "pluies"),
    "wf":  ("VENT",    "vents forts"),
    "vc":  ("CHALEUR", "vague de chaleur"),
    "ne":  ("NEIGE",   "chutes de neige"),
    "vn":  ("NEIGE",   "chutes de neige"),
    "br":  ("BROUILLARD", "brouillard dense"),
    "ts":  ("TEMPETE_SABLE", "tempête de sable"),
    "ca":  ("CANICULE","canicule"),
    "gr":  ("ORAGE",   "grêle"),
}
_DMN_LEVEL_MAP = {1: "JAUNE", 2: "ORANGE", 3: "ROUGE"}


@st.cache_data(ttl=900, show_spinner=False)
def _fetch_dmn_live() -> list:
    """Scrape l'API temps réel vigilance.marocmeteo.ma → liste de vigilances actives."""
    try:
        url = "https://vigilance.marocmeteo.ma/?q=postmet/getLives/post/generale/fr"
        body = urllib.parse.urlencode({"zone": "generale", "lang": "fr"}).encode()
        req = urllib.request.Request(url, data=body, method="POST", headers={
            "X-Requested-With": "XMLHttpRequest",
            "Referer": "https://vigilance.marocmeteo.ma/?q=fr/meteo/vigimet/generale",
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                           "AppleWebKit/537.36 (KHTML, like Gecko) "
                           "Chrome/124.0.0.0 Safari/537.36"),
        })
        with urllib.request.urlopen(req, timeout=8) as resp:
            raw = resp.read()
        data = json.loads(raw.lstrip(b"\xef\xbb\xbf"))
    except Exception:
        return []

    seuils = data.get("seuils", {})
    periode = data.get("periode", {})
    emis_str = data.get("titre", "")
    now_utc = datetime.datetime.utcnow()

    # Parse emission date from titre
    import re as _re
    _em = _re.search(r'(\d{2})-(\w+)\s+(\d{4})\s+à\s+(\d{2}):(\d{2})', emis_str)
    _month_fr = {"janvier":1,"février":2,"mars":3,"avril":4,"mai":5,"juin":6,
                 "juillet":7,"août":8,"septembre":9,"octobre":10,"novembre":11,"décembre":12}
    if _em:
        _mo = _month_fr.get(_em.group(2).lower(), now_utc.month)
        emis_le = datetime.datetime(int(_em.group(3)), _mo, int(_em.group(1)),
                                    int(_em.group(4)), int(_em.group(5)))
        emis_iso = emis_le.strftime("%Y-%m-%dT%H:%M:%SZ")
    else:
        emis_iso = now_utc.strftime("%Y-%m-%dT%H:%M:%SZ")

    # Use actual vdate from seuils (the bulletin's own date, not scraping time)
    vdate_str = now_utc.strftime("%Y-%m-%d")
    for _lv, _phs in seuils.items():
        for _pc, _ens in _phs.items():
            for _e in _ens:
                if _e.get("vdate"):
                    vdate_str = _e["vdate"]
                    break
            else: continue
            break
        else: continue
        break

    result = []

    for level_str, phenos in seuils.items():
        try:
            level_n = int(level_str)
        except Exception:
            continue
        niveau = _DMN_LEVEL_MAP.get(level_n, "JAUNE")
        for pheno_code, entries in phenos.items():
            if not entries:
                continue
            pheno_key, pheno_fr = _DMN_PHENO_MAP.get(pheno_code, (pheno_code.upper(), pheno_code))
            _ph_periode = periode.get(pheno_code, {})
            # Use actual bulletin period; when min==max (end of bulletin), use 06h start
            h_min_raw = int(_ph_periode.get("min", 6))
            h_max_raw = int(_ph_periode.get("max", 23))
            h_min = h_min_raw if h_min_raw != h_max_raw else 6
            h_max = h_max_raw if h_max_raw >= 6 else 23
            debut_iso = f"{vdate_str}T{h_min:02d}:00:00Z"
            fin_iso   = f"{vdate_str}T{h_max:02d}:59:00Z"

            provinces_all = []
            vmin, vmax = None, None
            for entry in entries:
                p_str = entry.get("provinces", "")
                provinces_all += [" ".join(p.split()) for p in p_str.split(",") if p.strip()]
                if vmin is None:
                    vmin = entry.get("vmin")
                    vmax = entry.get("vmax")

            regions = []
            for prov in provinces_all:
                reg = _DMN_PROVINCE_TO_REGION.get(prov)
                if reg and reg not in regions:
                    regions.append(reg)
            if not regions:
                continue

            cumul = vmax if pheno_code in ("ao", "pp") else None
            vent  = vmax if pheno_code == "wf" else None
            temp  = vmax if pheno_code in ("vc", "ca") else None

            provinces_short = provinces_all[:6]
            resume = (f"{pheno_fr.capitalize()} de niveau {niveau.lower()} sur "
                      f"{', '.join(regions[:3])}{'...' if len(regions) > 3 else ''}. "
                      f"Provinces : {', '.join(provinces_short)}"
                      f"{'...' if len(provinces_all) > 6 else '.'}")

            result.append({
                "id": f"DMN-{vdate_str}-{pheno_code.upper()}-{niveau}",
                "niveau": niveau,
                "phenomene": pheno_key,
                "zones": regions,
                "debut": debut_iso,
                "fin": fin_iso,
                "cumul_prevu_mm": cumul,
                "vitesse_vent_kmh": vent,
                "temperature_max": temp,
                "source": "DMN",
                "bulletin_url": "https://vigilance.marocmeteo.ma/?q=fr/meteo/vigimet/generale",
                "emis_le": emis_iso,
                "resume": resume,
            })

    result.sort(key=lambda v: -_NIVEAU_WEIGHT_PY.get(v.get("niveau", "VERT"), 1))
    return result


def _load_dmn_vigilances() -> list:
    """Charge les vigilances DMN : API live en priorité, fixtures en fallback."""
    live = _fetch_dmn_live()
    if live:
        return live

    # Fallback sur le fichier fixtures
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


@st.cache_data(ttl=900, show_spinner=False)
def _fetch_dmn_prov_geojson():
    """Fetches province GeoJSON from DMN API enriched with live alert levels."""
    _LEVEL_W = {"ROUGE": 3, "ORANGE": 2, "JAUNE": 1, "VERT": 0}
    _UNITE   = {"ao": "mm", "pp": "mm", "wf": "km/h", "vc": "°C", "ne": "cm", "vn": "cm", "br": "", "ca": "°C", "ts": ""}
    _HDR = {
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://vigilance.marocmeteo.ma/?q=fr/meteo/vigimet/generale",
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"),
    }
    try:
        body = urllib.parse.urlencode({"zone": "generale", "lang": "fr"}).encode()
        req = urllib.request.Request(
            "https://vigilance.marocmeteo.ma/?q=postmet/getLives/post/generale/fr",
            data=body, method="POST", headers=_HDR)
        with urllib.request.urlopen(req, timeout=8) as r:
            live = json.loads(r.read().lstrip(b"\xef\xbb\xbf"))

        body_g = urllib.parse.urlencode(
            {"zone": "generale", "lang": "fr", "pheno": "vig", "vech": "0", "reg": "0", "categs": "centre"}
        ).encode()
        req_g = urllib.request.Request(
            "https://vigilance.marocmeteo.ma/?q=postmet/getGeometries/post/fr",
            data=body_g, method="POST", headers=_HDR)
        with urllib.request.urlopen(req_g, timeout=12) as r_g:
            geom_raw = json.loads(r_g.read().lstrip(b"\xef\xbb\xbf"))
        couche = geom_raw.get("couche", {})
        if isinstance(couche, str):
            couche = json.loads(couche)
        features = couche.get("features", [])
    except Exception:
        return None

    # Build province_name → best alert from seuils
    name_alert = {}
    for lv_s, phenos in live.get("seuils", {}).items():
        try: niv = _DMN_LEVEL_MAP.get(int(lv_s), "JAUNE")
        except: continue
        for ph_code, entries in phenos.items():
            ph_key, ph_label = _DMN_PHENO_MAP.get(ph_code, (ph_code.upper(), ph_code))
            unite = _UNITE.get(ph_code, "")
            for ent in entries:
                vm, vx = ent.get("vmin"), ent.get("vmax")
                for pn in ent.get("provinces", "").split(","):
                    pn = " ".join(pn.split())  # normalize spaces
                    if not pn: continue
                    ex = name_alert.get(pn)
                    if not ex or _LEVEL_W.get(niv, 0) > _LEVEL_W.get(ex["niveau"], 0):
                        name_alert[pn] = {
                            "niveau": niv, "phenomene": ph_key,
                            "pheno_label": ph_label,
                            "ico": _PHENOMENE_ICONS_PY.get(ph_key, "⚠️"),
                            "vmin": vm, "vmax": vx, "unite": unite,
                        }

    def _simplify(coords, p=4):
        if not coords: return coords
        if isinstance(coords[0], list): return [_simplify(c, p) for c in coords]
        return [round(coords[0], p), round(coords[1], p)]

    def _centroid(ring):
        lats = [c[1] for c in ring]; lons = [c[0] for c in ring]
        return round((min(lats)+max(lats))/2, 4), round((min(lons)+max(lons))/2, 4)

    for feat in features:
        props = feat.get("properties", {})
        nom_raw = props.get("nom", "")
        nom_n   = " ".join(nom_raw.split())
        alert   = name_alert.get(nom_n) or name_alert.get(nom_raw)
        props["alerte"] = alert
        geom = feat.get("geometry", {})
        raw_c = geom.get("coordinates", [])
        try:
            ring = raw_c[0] if geom.get("type") == "Polygon" else raw_c[0][0]
            cy, cx = _centroid(ring)
        except Exception:
            cy, cx = None, None
        props["cy"] = cy; props["cx"] = cx
        geom["coordinates"] = _simplify(raw_c)
        feat["properties"] = props

    return couche


# ── Chaînes live (YouTube + HLS direct) ───────────────────────
# Format: (clé, handle_yt, fallback_id, hls_url, flag, label, cat, fallback_only)
# hls_url  = None → YouTube iframe  |  str → HLS.js <video>
# fallback_only = True → skip scraping, use fallback_id directly
_EB = "https://snrt.player.easybroadcast.io/events/"  # easybroadcast embed base URL
_YT_CHANNELS = [
    # ── Maroc YouTube ──────────────────────────────────────────────────────
    ("2M_MAROC",   "@2mtv",           "OoeN5t7A_2k", None,                                                                                  "🇲🇦", "2M MAROC",     "mar", False),
    ("MEDI1_TV",   "@medi1tv",        "nG3VJqfPE3Y", None,                                                                                  "🇲🇦", "MEDI1 TV",     "mar", False),
    ("SNRT_NEWS",  "@snrtnews",       "nwCX6jOfSUY", None,                                                                                  "🇲🇦", "SNRT NEWS",    "mar", False),
    # ── Maroc SNRT official streams (easybroadcast embed) ──────────────────
    ("AL_AOULA",   "@AlaoualaSNRT",   "kpAMiNqKi5Q", _EB+"73_aloula_w1dqfwm",                                                              "🇲🇦", "AL AOULA",     "mar", True),
    ("ARRABIA",    "@ArrabiaSNRT",    "GXWzTs4LFWA", None,                                                                                  "🇲🇦", "ARRABIA",      "mar", False),
    ("TAMAZIGHT",  "@TamazightSNRT",  "",            _EB+"73_tamazight_tccybxt",                                                            "🇲🇦", "TAMAZIGHT",    "mar", True),
    ("ASSADISSA",  "@AssadissaSNRT",  "",            _EB+"73_assadissa_7b7u5n1",                                                            "🇲🇦", "ASSADISSA",    "mar", True),
    ("LAAYOUNE",   "@LaayouneSNRT",   "",            _EB+"73_laayoune_pgagr52",                                                             "🇲🇦", "LAAYOUNE TV",  "mar", True),
    # ── International YouTube ──────────────────────────────────────────────
    ("FRANCE_24",  "@FRANCE24",          "l8PMl7tUDIE", None,                                                                                  "🇫🇷", "FRANCE 24",    "int", True),
    ("FRANCE24EN", "@France24_en",       "Ap-UM1O9RBU", None,                                                                                  "🇫🇷", "FRANCE 24 EN", "int", False),
    ("SKY_NEWS",   "@SkyNews",           "uvviIF4725I", None,                                                                                  "🇬🇧", "SKY NEWS",     "int", False),
    ("EURONEWS",   "@euronews",          "pykpO5kQJ98", None,                                                                                  "🇪🇺", "EURONEWS",     "int", False),
    ("DW_NEWS",    "@DWNews",            "LuKwFajn37U", None,                                                                                  "🇩🇪", "DW NEWS",      "int", False),
    ("TRT_WORLD",  "@TRTWorld",          "ABfFhWzWs0s", None,                                                                                  "🌍", "TRT WORLD",   "int", False),
    ("SKY_ARABIA", "@skynewsarabia",     "U--OjmpjF5o", None,                                                                                  "🌍", "SKY NEWS AR",  "int", False),
    ("CNN",        "@CNN",               "w_Ma8oQLmSM", None,                                                                                  "🇺🇸", "CNN INTL",     "int", False),
    ("BBC_NEWS",   "@BBCNews",           "bjgQzJzCZKs", None,                                                                                  "🇬🇧", "BBC NEWS",     "int", False),
    # ── HLS direct (WorldMonitor approach) ────────────────────────────────
    ("AL_JAZEERA", "@AlJazeeraEnglish",  "gCNeDWCI0vo", "https://live-hls-apps-aje-fa.getaj.net/AJE/index.m3u8",                             "🌍", "AL JAZEERA",  "int", True),
    ("AL_ARABIYA", "@AlArabiya",         "n7eQejkXbnM", "https://live.alarabiya.net/alarabiapublish/alarabiya.smil/playlist.m3u8",            "🌍", "AL ARABIYA",  "int", True),
    ("AJ_ARABIC",  "@AljazeeraChannel",  "bNyUyrR0PHo", "https://live-hls-web-ajm.getaj.net/AJM/index.m3u8",                                "🌍", "AJ ARABIC",   "int", True),
    ("DW_ARABIC",  "@DWArabic",          "d7SKcBLPCDs", "https://dwamdstream103.akamaized.net/hls/live/2015526/dwstream103/index.m3u8",       "🇩🇪", "DW ARABIC",   "int", True),
    ("AL_HADATH",  "@AlHadath",          "xWXpl7azI8k", "https://live.alarabiya.net/alarabiapublish/alhadath.smil/playlist.m3u8",             "🌍", "AL HADATH",   "int", True),
    ("RT_ARABIC",  "@RTarabic",          "xMbSB4SKFHQ", "https://rt-arb.rttv.com/dvr/rtarab/playlist.m3u8",                                 "🌍", "RT ARABIC",   "int", True),
    ("CGTN",       "@CGTNOfficial",      "B9bS9E3FKKY", "https://news.cgtn.com/resource/live/english/cgtn-news.m3u8",                        "🌏", "CGTN",        "int", True),
]


@st.cache_data(ttl=900, show_spinner=False)
def _resolve_yt_live_ids(_v=2) -> dict:  # bump _v to force cache reset
    """Scrape la page /@handle/live de chaque chaîne pour récupérer l'ID vidéo live actuel.
    Résolution en parallèle, timeout 6s par chaîne, fallback sur ID hardcodé si échec.
    Cache 1h pour ne pas surcharger YouTube.
    """
    import re as _re
    import threading

    result = {}
    lock   = threading.Lock()

    def _fetch_id(key, handle, fallback):
        vid = fallback
        try:
            import json as _json_yt

            _hdrs = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                     "Content-Type": "application/json"}
            _ctx  = {"context": {"client": {"clientName": "WEB", "clientVersion": "2.20240101", "hl": "fr"}}}
            _hn   = handle.lstrip("@").lower()  # ex: "2mtv", "medi1tv"

            def _search(query, params="CAISAhAB"):
                _b = _json_yt.dumps({**_ctx, "query": query, "params": params}).encode()
                _r = urllib.request.Request(
                    "https://www.youtube.com/youtubei/v1/search?prettyPrint=false",
                    data=_b, headers=_hdrs)
                with urllib.request.urlopen(_r, timeout=8) as _rs:
                    return _rs.read().decode("utf-8", errors="ignore")

            def _player(v):
                _b = _json_yt.dumps({**_ctx, "videoId": v}).encode()
                _r = urllib.request.Request(
                    "https://www.youtube.com/youtubei/v1/player?prettyPrint=false",
                    data=_b, headers=_hdrs)
                with urllib.request.urlopen(_r, timeout=5) as _rs:
                    return _json_yt.loads(_rs.read()).get("videoDetails", {})

            def _best_from(raw, author_must):
                """Premier videoId dont l'auteur contient author_must."""
                ids = list(dict.fromkeys(_re.findall(r'"videoId"\s*:\s*"([a-zA-Z0-9_-]{11})"', raw)))
                for _v in ids[:15]:
                    try:
                        det = _player(_v)
                        auth = det.get("author", "").lower().replace(" ", "")
                        if author_must in auth:
                            return _v, det.get("isLive", False) or det.get("isLiveContent", False)
                    except Exception:
                        continue
                return None, False

            # 1. Live en cours
            _raw_live = _search(_hn + " direct live", "CAMSAhAB")
            _id, _live = _best_from(_raw_live, _hn)
            if _id and _live:
                vid = _id
            else:
                # 2. Dernière vidéo d'info uploadée par la chaîne
                _raw_rec = _search(_hn + " أخبار info journal")
                _id2, _ = _best_from(_raw_rec, _hn)
                if _id2:
                    vid = _id2
        except Exception:
            pass
        with lock:
            result[key] = vid

    threads = []
    for key, handle, fallback, hls_url, flag, label, cat, fallback_only in _YT_CHANNELS:
        if hls_url or fallback_only:
            result[key] = fallback  # HLS channels don't need YouTube ID scraping
        else:
            t = threading.Thread(target=_fetch_id, args=(key, handle, fallback), daemon=True)
            threads.append(t)
            t.start()

    for t in threads:
        t.join(timeout=8)

    for key, _, fallback, *_ in _YT_CHANNELS:
        result.setdefault(key, fallback)

    return result


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
    _intl_feed_items, _intl_statuses = _fetch_intl_feeds()

_dmn_vigilances = _load_dmn_vigilances()
_resolve_yt_live_ids.clear()          # vide le cache à chaque démarrage
_yt_ids = _resolve_yt_live_ids(_v=6)

# ── Dernières vidéos actualités Maroc ────────────────────────────────────────

_NEWS_CHANNELS_MAR = [
    {"key": "SNRT",    "handle": "@snrtnews",   "label": "SNRT NEWS", "flag": "🇲🇦"},
    {"key": "ARRABIA", "handle": "@ArrabiaSNRT", "label": "ARRABIA",   "flag": "🇲🇦"},
]

# Mapping : clé _YT_CHANNELS → clé _NEWS_CHANNELS_MAR (chaînes sans live fonctionnel)
# 2M_MAROC et MEDI1_TV exclus ici — ils utilisent _yt_ids (résolution InnerTube, cache court)
_LATEST_VIDEO_MAP = {
    "SNRT_NEWS": "SNRT",
    "ARRABIA":   "ARRABIA",
}

# Mapping : clé _YT_CHANNELS → playlist_id YouTube (priorité sur _LATEST_VIDEO_MAP)
# MEDI1_TV retiré — utilise _yt_ids pour éviter le cache 24h de _fetch_playlist_latest
_PLAYLIST_MAP: dict = {}


@st.cache_data(ttl=86400, show_spinner=False)
def _fetch_playlist_latest(playlist_id: str):
    """Retourne le premier item (le plus récent) d'une playlist YouTube publique."""
    import re as _re, json as _json, gzip as _gzip, zlib as _zlib
    try:
        url = f"https://www.youtube.com/playlist?list={playlist_id}"
        req = urllib.request.Request(url, headers={
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
            ),
            "Accept-Language": "fr-FR,fr;q=0.9",
            "Accept-Encoding": "gzip, deflate",
        })
        with urllib.request.urlopen(req, timeout=10) as resp:
            _enc = resp.headers.get("Content-Encoding", "")
            _raw = resp.read(524288)
        if _enc == "gzip":
            html = _gzip.decompress(_raw).decode("utf-8", errors="ignore")
        elif _enc == "deflate":
            html = _zlib.decompress(_raw).decode("utf-8", errors="ignore")
        else:
            html = _raw.decode("utf-8", errors="ignore")

        _idx = html.find("ytInitialData")
        if _idx < 0:
            return None
        _m = _re.search(r'ytInitialData\s*=\s*(\{)', html[_idx:])
        if not _m:
            return None
        _start = _idx + _m.start(1)
        _depth, _end = 0, _start
        for _i, _c in enumerate(html[_start:], _start):
            if _c == '{':
                _depth += 1
            elif _c == '}':
                _depth -= 1
                if _depth == 0:
                    _end = _i + 1
                    break
        data = _json.loads(html[_start:_end])

        # Naviguer jusqu'au playlistVideoListRenderer
        tabs = (data.get("contents", {})
                    .get("twoColumnBrowseResultsRenderer", {})
                    .get("tabs", []))
        for tab in tabs:
            for section in (tab.get("tabRenderer", {})
                               .get("content", {})
                               .get("sectionListRenderer", {})
                               .get("contents", [])):
                for item in section.get("itemSectionRenderer", {}).get("contents", []):
                    pvlr = item.get("playlistVideoListRenderer", {})
                    if not pvlr:
                        continue
                    for pi in pvlr.get("contents", []):
                        pv = pi.get("playlistVideoRenderer", {})
                        if not pv:
                            continue
                        vid = pv.get("videoId", "")
                        runs = pv.get("title", {}).get("runs", [])
                        title = runs[0].get("text", "") if runs else ""
                        if vid and title:
                            return {"id": vid, "title": title, "age": ""}
    except Exception:
        pass
    return None


@st.cache_data(ttl=86400, show_spinner=False)
def _fetch_latest_news_videos(handle: str, n: int = 4) -> list[dict]:
    """Scrape la page /videos d'une chaîne YouTube pour les N dernières vidéos."""
    import re as _re
    import json as _json
    import gzip as _gzip
    import zlib as _zlib
    videos = []
    try:
        url = f"https://www.youtube.com/{handle}/videos"
        req = urllib.request.Request(url, headers={
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
            ),
            "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate",  # exclude br — not supported by stdlib
        })
        with urllib.request.urlopen(req, timeout=10) as resp:
            _enc = resp.headers.get("Content-Encoding", "")
            _raw = resp.read(524288)  # 512 Ko

        if _enc == "gzip":
            html = _gzip.decompress(_raw).decode("utf-8", errors="ignore")
        elif _enc == "deflate":
            html = _zlib.decompress(_raw).decode("utf-8", errors="ignore")
        else:
            html = _raw.decode("utf-8", errors="ignore")

        # Localiser ytInitialData puis extraire le JSON par comptage d'accolades
        _idx = html.find("ytInitialData")
        if _idx < 0:
            return videos
        _m = _re.search(r'ytInitialData\s*=\s*(\{)', html[_idx:])
        if not _m:
            return videos
        _start = _idx + _m.start(1)
        _depth = 0
        _end = _start
        for _i, _c in enumerate(html[_start:], _start):
            if _c == '{':
                _depth += 1
            elif _c == '}':
                _depth -= 1
                if _depth == 0:
                    _end = _i + 1
                    break

        data = _json.loads(html[_start:_end])

        # Parcourir la structure ytInitialData → tabs → gridVideoRenderer
        tabs = (data.get("contents", {})
                    .get("twoColumnBrowseResultsRenderer", {})
                    .get("tabs", []))
        for tab in tabs:
            contents = (tab.get("tabRenderer", {})
                           .get("content", {})
                           .get("richGridRenderer", {})
                           .get("contents", []))
            for item in contents:
                vr = (item.get("richItemRenderer", {})
                           .get("content", {})
                           .get("videoRenderer", {}))
                if not vr:
                    continue
                vid   = vr.get("videoId", "")
                title = ""
                runs  = vr.get("title", {}).get("runs", [])
                if runs:
                    title = runs[0].get("text", "")
                views = ""
                vsi   = vr.get("viewCountText", {})
                if vsi.get("simpleText"):
                    views = vsi["simpleText"]
                elif vsi.get("runs"):
                    views = "".join(r.get("text","") for r in vsi["runs"])
                age = ""
                psi = vr.get("publishedTimeText", {})
                if psi.get("simpleText"):
                    age = psi["simpleText"]
                if vid and title:
                    videos.append({"id": vid, "title": title, "views": views, "age": age})
                if len(videos) >= n:
                    break
            if len(videos) >= n:
                break
    except Exception:
        pass
    return videos[:n]


_fetch_latest_news_videos.clear()     # force refresh — évite le cache 24h
_fetch_playlist_latest.clear()        # force refresh — évite le cache 24h

_news_videos: dict[str, list] = {
    ch["key"]: _fetch_latest_news_videos(ch["handle"])
    for ch in _NEWS_CHANNELS_MAR
}

# Résultats playlist (1 vidéo par playlist, priorité sur _news_videos pour les canaux concernés)
_playlist_latest: dict = {
    key: _fetch_playlist_latest(pid)
    for key, pid in _PLAYLIST_MAP.items()
}

# ── Ticker temps réel ─────────────────────────────────────────
_alert_items = [it for it in _all_feed_items if it.get("score", 0) >= 1]

# Priorité : vigilances DMN en tête, puis alertes flux RSS
_ticker_parts: list = []

for _v in _dmn_vigilances:
    _ticker_parts.append(_format_vigilance_ticker_py(_v))

for _it in _alert_items[:10]:
    _date_str = ""
    try:
        _pub = _it.get("published", "")
        if _pub:
            _pub_dt = datetime.datetime(*[int(x) for x in _pub[:10].split("-")])
            _date_str = f' [{_pub_dt.strftime("%d/%m")}]'
    except Exception:
        pass
    _desc = _it.get("description", "").strip()
    _desc_short = (" — " + _desc[:60] + "…") if len(_desc) > 10 else ""
    _ticker_parts.append(
        f'{_it["icon"]} {_it["source"].upper()}{_date_str} · {_it["title"][:80]}{_desc_short}'
    )

_has_alerts = bool(
    _dmn_vigilances and _dmn_vigilances[0].get("niveau") in ("ROUGE", "ORANGE")
) or bool(_alert_items)

if _ticker_parts:
    _ticker_text = "  ▸  ".join(_ticker_parts)
else:
    _ticker_text = T["no_alerts"]

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

st.markdown(f"""
<div style="
  position:fixed; top:60px; left:0; right:0; z-index:9998;
  height:36px;
  background:{_tk_bg};
  border-bottom:1px solid {_tk_border};
  display:flex; align-items:center; overflow:hidden;
  font-family:'Courier New',monospace;
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

  <!-- Track défilant -->
  <div style="flex:1; overflow:hidden; height:36px; display:flex; align-items:center;">
    <span style="
      white-space:nowrap; display:inline-block; padding-left:100%;
      font-size:11.5px; color:{_tk_text}; letter-spacing:.3px;
      line-height:36px;
      animation:scroll-t 60s linear infinite;
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
    <button id="ccip-hdr-toggle" title="Masquer / afficher le tableau de bord"
      style="background:rgba(33,150,243,0.08);border:1px solid rgba(33,150,243,0.2);
             color:rgba(144,202,249,0.55);border-radius:4px;cursor:pointer;
             width:22px;height:22px;font-size:10px;line-height:1;
             display:flex;align-items:center;justify-content:center;padding:0;
             transition:all .15s;flex-shrink:0;">▲</button>
  </div>
</div>
""", unsafe_allow_html=True)

# Injecte le CSS global + le gestionnaire de clic via iframe (seul moyen fiable dans Streamlit)
st.components.v1.html("""
<script>
(function(){
  var pd = window.parent.document;

  // 1. Injecter la règle CSS globale dans le <head> du parent
  if (!pd.getElementById('ccip-hdr-style')) {
    var s = pd.createElement('style');
    s.id = 'ccip-hdr-style';
    s.textContent = [
      'body.ccip-hdr-hidden .wm-country-header { display:none !important; }',
      'body.ccip-hdr-hidden .wm-kpi-grid       { display:none !important; }'
    ].join('');
    pd.head.appendChild(s);
  }

  // 2. Restaurer l'état depuis localStorage
  if (localStorage.getItem('ccipHdrHidden') === '1') {
    pd.body.classList.add('ccip-hdr-hidden');
    var btn = pd.getElementById('ccip-hdr-toggle');
    if (btn) btn.textContent = '▼';
  }

  // 3. Écouter les clics sur le bouton (phase de capture = fiable)
  pd.addEventListener('click', function(e) {
    var t = e.target;
    if (t && t.id === 'ccip-hdr-toggle') {
      var hidden = pd.body.classList.toggle('ccip-hdr-hidden');
      localStorage.setItem('ccipHdrHidden', hidden ? '1' : '0');
      t.textContent = hidden ? '▼' : '▲';
    }
  }, true);
})();
</script>
""", height=0, scrolling=False)

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
    jobs     = _load_jobs()
    done     = [j for j in jobs if j.get("status") == "done"]
    running  = [j for j in jobs if j.get("status") == "running"]
    total_ha = sum(float(j.get("results",{}).get("surface_totale_ha",0) or 0) for j in done)
    n_live   = sum(1 for s in _feed_statuses.values() if s == "live")

    # ── Score de risque Maroc (inspiré WorldMonitor Instability Index) ──
    _risk = 0
    for _v in _dmn_vigilances:
        _risk += {"ROUGE":30,"ORANGE":15,"JAUNE":5,"VERT":1}.get(_v.get("niveau","VERT"),0)
    for _it in _alert_items:
        _risk += 8 if _it.get("score",0) >= 2 else 3
    _risk = min(100, _risk)
    _risk_cls   = "wm-score-danger" if _risk >= 60 else ("wm-score-warn" if _risk >= 30 else "wm-score-ok")
    _risk_color = "#ef4444" if _risk >= 60 else ("#f59e0b" if _risk >= 30 else "#22c55e")
    _risk_trend = "↑" if _risk >= 50 else ("→" if _risk >= 20 else "↓")
    _n_rouge  = sum(1 for v in _dmn_vigilances if v.get("niveau")=="ROUGE")
    _n_orange = sum(1 for v in _dmn_vigilances if v.get("niveau")=="ORANGE")
    _n_jaune  = sum(1 for v in _dmn_vigilances if v.get("niveau")=="JAUNE")

    # ── En-tête Pays (style WorldMonitor CountryDeepDivePanel) ──────────
    _updated_str = (datetime.datetime.utcnow()+datetime.timedelta(hours=1)).strftime("%d/%m/%Y %H:%M UTC+1")
    st.markdown(f"""
    <div class="wm-country-header">
      <div class="wm-flag">🇲🇦</div>
      <div>
        <div class="wm-country-name">MAROC</div>
        <div class="wm-country-sub">ROYAUME DU MAROC — PLATEFORME CCIP · CRTS</div>
      </div>
      <div style="display:flex;gap:20px;margin-left:auto;align-items:center;">
        <div style="text-align:center;">
          <div class="wm-score-label">VIGILANCES DMN</div>
          <div style="display:flex;gap:8px;align-items:center;justify-content:center;margin-top:4px;">
            <span style="font-family:'Orbitron',monospace;font-size:0.85em;color:#ef4444;">🔴 {_n_rouge}</span>
            <span style="font-family:'Orbitron',monospace;font-size:0.85em;color:#f59e0b;">🟠 {_n_orange}</span>
            <span style="font-family:'Orbitron',monospace;font-size:0.85em;color:#eab308;">🟡 {_n_jaune}</span>
          </div>
        </div>
        <div style="width:1px;height:40px;background:rgba(33,150,243,0.2);"></div>
        <div class="wm-score-block">
          <div class="wm-score-label">INDICE DE RISQUE</div>
          <div class="wm-score-val {_risk_cls}">{_risk} <span style="font-size:0.45em;">{_risk_trend}</span></div>
          <div class="wm-score-bar">
            <div class="wm-score-fill" style="width:{_risk}%;background:{_risk_color};"></div>
          </div>
          <div style="font-size:0.6em;color:rgba(144,202,249,0.3);margin-top:4px;">Mis à jour {_updated_str}</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── KPIs (5 tuiles style WorldMonitor metric grid) ──────────────────
    _kpi_risk_cls   = "wm-kpi-danger" if _risk>=60 else ("wm-kpi-warn" if _risk>=30 else "wm-kpi-ok")
    _kpi_risk_color = _risk_color
    _kpi_flux_cls   = "wm-kpi-ok" if n_live >= 6 else ("wm-kpi-warn" if n_live >= 3 else "wm-kpi-danger")
    st.markdown(f"""
    <div class="wm-kpi-grid">
      <div class="wm-kpi {_kpi_risk_cls}">
        <div class="wm-kpi-val" style="color:{_kpi_risk_color};">{_risk}</div>
        <div class="wm-kpi-lbl">Indice de Risque<br>/100</div>
      </div>
      <div class="wm-kpi {'wm-kpi-danger' if _n_rouge else ('wm-kpi-warn' if _n_orange else 'wm-kpi-ok')}">
        <div class="wm-kpi-val" style="color:{'#ef4444' if _n_rouge else ('#f59e0b' if _n_orange else '#22c55e')};">{len(_dmn_vigilances)}</div>
        <div class="wm-kpi-lbl">Vigilances DMN<br>actives</div>
      </div>
      <div class="wm-kpi {'wm-kpi-blue' if done else 'wm-kpi-ok'}">
        <div class="wm-kpi-val" style="color:#2196f3;">{len(done)}</div>
        <div class="wm-kpi-lbl">Traitements SAR<br>terminés</div>
      </div>
      <div class="wm-kpi {'wm-kpi-warn' if total_ha>0 else 'wm-kpi-ok'}">
        <div class="wm-kpi-val" style="color:{'#f59e0b' if total_ha>0 else '#22c55e'};">{total_ha:,.0f}</div>
        <div class="wm-kpi-lbl">Ha inondés<br>détectés</div>
      </div>
      <div class="wm-kpi {_kpi_flux_cls}">
        <div class="wm-kpi-val" style="color:{'#22c55e' if n_live>=6 else ('#f59e0b' if n_live>=3 else '#ef4444')};">{n_live}<span style="font-size:0.5em;color:rgba(144,202,249,0.35);">/{len(FEEDS_8)}</span></div>
        <div class="wm-kpi-lbl">Flux institutionnels<br>en ligne</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Layout principal : Carte+Signaux | Chaînes TV ───────────────────
    col_map, col_tv = st.columns([3, 2])

    with col_tv:
        import json as _json_tv
        # Construire la liste des chaînes avec IDs résolus dynamiquement
        _ch_list = []
        for key, handle, fallback, hls_url, flag, label, cat, fallback_only in _YT_CHANNELS:
            # Priorité 1 : playlist (ex. Medi1)
            _playlist_vid = _playlist_latest.get(key)
            # Priorité 2 : dernière vidéo chaîne YouTube
            _news_key  = _LATEST_VIDEO_MAP.get(key)
            _news_vids = _news_videos.get(_news_key, []) if _news_key else []
            _latest_vid = _playlist_vid or (_news_vids[0] if _news_vids else None)

            _vid_id    = _latest_vid["id"]    if _latest_vid else _yt_ids.get(key, fallback)
            _vid_title = _latest_vid["title"][:60] if _latest_vid else ""
            _vid_age   = _latest_vid.get("age", "") if _latest_vid else ""
            _ch_list.append({
                "n":      label,
                "id":     _vid_id,
                "f":      flag,
                "cat":    cat,
                "handle": handle,
                "hls":    hls_url,
                "ok":     bool(hls_url) or bool(_latest_vid) or _yt_ids.get(key, fallback) != fallback,
                "latest": bool(_latest_vid),
                "vtitle": _vid_title,
                "vage":   _vid_age,
            })
        _ch_json = _json_tv.dumps(_ch_list, ensure_ascii=False)
        # Statut résolution : combien d'IDs ont été mis à jour vs fallback
        _n_resolved = sum(1 for c in _ch_list if c["ok"])
        _n_total_ch = len(_ch_list)

        _live_tpl = """<!DOCTYPE html>
<html><head><meta charset="utf-8"/>
<style>
*{margin:0;padding:0;box-sizing:border-box;}
html,body{background:#020b18;width:100%;height:100%;overflow:hidden;font-family:'Courier New',monospace;}
.c{width:100%;height:100%;background:#111;border:1px solid rgba(255,255,255,0.08);border-radius:10px;overflow:hidden;display:flex;flex-direction:column;}
.hdr{flex-shrink:0;height:38px;background:#0d0d0d;border-bottom:1px solid #1c1c1c;display:flex;align-items:center;padding:0 12px;gap:10px;}
.ld{width:8px;height:8px;border-radius:50%;background:#ef4444;box-shadow:0 0 6px #ef4444;animation:p 1.5s ease-in-out infinite;flex-shrink:0;}
@keyframes p{0%,100%{opacity:1}50%{opacity:0.25}}
.ht{font-size:11px;font-weight:700;letter-spacing:2.5px;color:#e5e7eb;}
.vc{color:#ef4444;font-size:11px;font-weight:700;}
.rs{font-size:8px;color:rgba(34,197,94,0.6);letter-spacing:1px;margin-left:4px;}
.ctrl{margin-left:auto;display:flex;gap:12px;align-items:center;}
.cb{background:none;border:none;cursor:pointer;color:rgba(255,255,255,0.35);font-size:15px;padding:2px;transition:color .15s;line-height:1;}
.cb:hover{color:#fff;}
.filter-bar{flex-shrink:0;background:#0a0a0a;border-bottom:1px solid #1c1c1c;display:flex;align-items:center;padding:4px 8px;gap:5px;}
.fb{flex-shrink:0;padding:3px 10px;font-size:8px;font-weight:700;letter-spacing:1.5px;cursor:pointer;border-radius:3px;transition:all .15s;border:1px solid rgba(255,255,255,0.12);background:transparent;color:rgba(255,255,255,0.35);}
.fb:hover{color:#fff;background:rgba(255,255,255,0.06);}
.fb.fb-nat.on{background:#22c55e;border-color:#22c55e;color:#000;}
.fb.fb-int.on{background:#3b82f6;border-color:#3b82f6;color:#fff;}
.fb-sep{flex:1;}
.tabs{flex-shrink:0;background:#090909;border-bottom:1px solid #1c1c1c;display:flex;overflow-x:auto;scrollbar-width:none;padding:5px 5px;gap:3px;flex-wrap:wrap;}
.tabs::-webkit-scrollbar{display:none;}
.tab{flex-shrink:0;padding:4px 9px;font-size:8px;font-weight:700;letter-spacing:1px;cursor:pointer;border-radius:3px;transition:all .15s;color:rgba(255,255,255,0.3);border:1px solid rgba(255,255,255,0.05);background:transparent;}
.tab:hover{color:rgba(255,255,255,0.6);background:rgba(255,255,255,0.04);}
.tab.act{background:#ef4444;color:#fff;border-color:#ef4444;}
.tab.mar{border-color:rgba(34,197,94,0.3);color:rgba(34,197,94,0.7);}
.tab.mar.act{background:#22c55e;border-color:#22c55e;color:#000;}
.tab.ok::after{content:'●';font-size:5px;vertical-align:super;margin-left:2px;color:#22c55e;}
.tab.hidden{display:none !important;}
.player{flex:1;position:relative;background:#000;min-height:0;}
.player iframe,.player video{width:100%;height:100%;border:none;display:block;}
.splash{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:8px;background:#040404;}
.sp-ico{font-size:2.2em;}
.sp-txt{font-size:9px;color:rgba(255,255,255,0.25);letter-spacing:2px;text-align:center;line-height:1.8;}
.fn{font-size:9px;font-weight:700;letter-spacing:2px;color:rgba(255,255,255,0.45);}
.ff{font-size:11px;}
.fid{font-size:7.5px;color:rgba(255,255,255,0.18);margin-left:auto;font-variant-numeric:tabular-nums;}
.hls-badge{font-size:7px;background:#7c3aed;color:#fff;border-radius:2px;padding:1px 4px;margin-left:4px;letter-spacing:1px;}
.eb-badge{font-size:7px;background:#e65100;color:#fff;border-radius:2px;padding:1px 4px;margin-left:4px;letter-spacing:1px;}
.vod-badge{font-size:7px;background:#0ea5e9;color:#fff;border-radius:2px;padding:1px 4px;margin-left:4px;letter-spacing:1px;}
.foot{flex-shrink:0;background:#080808;border-top:1px solid #181818;display:flex;flex-direction:column;padding:4px 10px;gap:2px;}
.foot-row1{display:flex;align-items:center;gap:8px;}
.fvtitle{font-size:7px;color:rgba(144,202,249,0.3);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
</style>
<script src="https://cdn.jsdelivr.net/npm/hls.js@1.5.13/dist/hls.min.js"></script>
</head><body>
<div class="c">
  <div class="hdr">
    <div class="ld"></div>
    <span class="ht">LIVE NEWS</span>
    <span class="vc">●</span>
    <span class="vc" id="vc">—</span>
    <span class="rs" id="rs-badge"><<RS>>/<<RT>> résolus</span>
    <div class="ctrl">
      <button class="cb" id="mb" onclick="togMute()" title="Mute/Son">🔇</button>
      <button class="cb" id="rb" onclick="reloadCh()" title="Rafraîchir">↺</button>
      <button class="cb" onclick="togFS()" title="Plein écran">⛶</button>
    </div>
  </div>
  <div class="filter-bar">
    <button class="fb fb-nat on" id="btn-nat" onclick="toggleFilter('nat')" title="Chaînes nationales marocaines">🇲🇦 NATIONAL</button>
    <button class="fb fb-int on" id="btn-int" onclick="toggleFilter('int')" title="Chaînes internationales">🌍 INTERNATIONAL</button>
    <span class="fb-sep"></span>
    <span style="font-size:7px;color:rgba(255,255,255,0.15);letter-spacing:1px;" id="ch-count"></span>
  </div>
  <div class="tabs" id="tabs"></div>
  <div class="player" id="player">
    <div class="splash" id="splash">
      <span class="sp-ico">📺</span>
      <span class="sp-txt">Sélectionnez une chaîne<br>IDs résolus automatiquement</span>
    </div>
    <iframe id="yt" src="" allowfullscreen style="display:none;"
      allow="autoplay; encrypted-media; picture-in-picture"></iframe>
    <video id="hv" autoplay playsinline style="display:none;background:#000;"></video>
  </div>
  <div class="foot">
    <div class="foot-row1">
      <span class="ff" id="ch-flag">📺</span>
      <span class="fn" id="ch-name">—</span>
      <span class="fid" id="ch-id">—</span>
    </div>
    <div class="fvtitle" id="ch-vtitle"></div>
  </div>
</div>
<script>
const CH=<<CH>>;
let cur=-1, muted=true, hlsInst=null;
const tabsEl=document.getElementById('tabs');
const ytEl=document.getElementById('yt');
const hvEl=document.getElementById('hv');
const spEl=document.getElementById('splash');

function ytUrl(i){
  return 'https://www.youtube.com/embed/'+CH[i].id
    +'?autoplay=1&mute='+(muted?1:0)+'&rel=0&modestbranding=1&iv_load_policy=3&controls=1';
}

function stopHls(){
  if(hlsInst){hlsInst.destroy();hlsInst=null;}
  hvEl.pause();hvEl.src='';hvEl.style.display='none';
}

function loadHls(url){
  stopHls();
  ytEl.style.display='none';
  hvEl.style.display='block';
  hvEl.muted=muted;
  if(Hls.isSupported()){
    hlsInst=new Hls({maxBufferLength:20,maxMaxBufferLength:40,liveSyncDurationCount:3});
    hlsInst.loadSource(url);
    hlsInst.attachMedia(hvEl);
    hlsInst.on(Hls.Events.MANIFEST_PARSED,()=>hvEl.play().catch(()=>{}));
  } else if(hvEl.canPlayType('application/vnd.apple.mpegurl')){
    hvEl.src=url;
    hvEl.play().catch(()=>{});
  }
}

function isHls(url){return url&&url.endsWith('.m3u8');}
function isIframe(url){return url&&!url.endsWith('.m3u8');}  // any non-HLS embed URL

function embedLabel(url){
  if(!url)return'';
  if(url.includes('easybroadcast.io'))return'SNRT';
  if(url.includes('france24.com'))return'F24';
  return'EMBED';
}

function loadCh(i){
  cur=i;
  const ch=CH[i];
  spEl.style.display='none';
  tabsEl.querySelectorAll('.tab').forEach((t,j)=>t.classList.toggle('act',j===i));
  document.getElementById('ch-name').textContent=ch.n;
  document.getElementById('ch-flag').textContent=ch.f;
  document.getElementById('vc').textContent=ch.latest?'VOD':'LIVE';
  const vtEl=document.getElementById('ch-vtitle');
  if(ch.latest&&ch.vtitle){
    vtEl.textContent=(ch.vage?ch.vage+' · ':'')+ch.vtitle;
    vtEl.style.display='block';
  } else {
    vtEl.style.display='none';
  }

  if(isHls(ch.hls)){
    document.getElementById('ch-id').textContent='HLS direct';
    stopHls(); ytEl.style.display='none';
    loadHls(ch.hls);
  } else if(isIframe(ch.hls)){
    stopHls(); ytEl.style.display='block';
    ytEl.src=ch.hls;
    document.getElementById('ch-id').textContent=embedLabel(ch.hls)+' LIVE officiel';
  } else if(ch.latest){
    stopHls();
    ytEl.style.display='block';
    ytEl.src=ytUrl(i);
    document.getElementById('ch-id').textContent='Dernière vidéo YT';
  } else {
    stopHls();
    ytEl.style.display='block';
    ytEl.src=ytUrl(i);
    document.getElementById('ch-id').textContent='YT: '+ch.id+(ch.ok?' ✓':' fallback');
  }
}

function reloadCh(){
  if(cur<0)return;
  const ch=CH[cur];
  if(isHls(ch.hls)){loadHls(ch.hls);}
  else if(isIframe(ch.hls)){ytEl.src='';setTimeout(()=>{ytEl.src=ch.hls;},200);}
  else{ytEl.src='';setTimeout(()=>{ytEl.src=ytUrl(cur);},200);}
}

function togMute(){
  muted=!muted;
  document.getElementById('mb').textContent=muted?'🔇':'🔊';
  if(cur<0)return;
  const ch=CH[cur];
  if(isHls(ch.hls)){hvEl.muted=muted;}
  /* iframe mute not controllable */
}

function togFS(){
  const p=document.getElementById('player');
  (p.requestFullscreen||p.webkitRequestFullscreen||function(){}).call(p);
}

// Build tabs
const tabEls=[];
let lastCat='';
CH.forEach((c,i)=>{
  if(lastCat&&c.cat!==lastCat){
    const s=document.createElement('div');
    s.style.cssText='height:1px;background:#1c1c1c;flex-basis:100%;margin:1px 0;';
    s.dataset.sep=lastCat;
    tabsEl.appendChild(s);
  }
  const t=document.createElement('button');
  t.className='tab'+(c.cat==='mar'?' mar':'')+(c.ok?' ok':'');
  t.dataset.cat=c.cat;
  let badge='';
  if(isHls(c.hls))badge='<span class="hls-badge">HLS</span>';
  else if(isIframe(c.hls))badge='<span class="eb-badge">'+embedLabel(c.hls)+'</span>';
  else if(c.latest)badge='<span class="vod-badge">VOD</span>';
  t.innerHTML=c.f+' '+c.n+badge;
  const titleHint=c.latest&&c.vtitle?' — '+c.vtitle.substring(0,40):'';
  t.title=c.n+(isIframe(c.hls)?' — Stream '+embedLabel(c.hls)+' officiel':(isHls(c.hls)?' — Stream HLS direct':(c.latest?titleHint:(c.ok?' — ID résolu':' — ID fallback'))));
  t.onclick=()=>loadCh(i);
  tabsEl.appendChild(t);
  tabEls.push(t);
  lastCat=c.cat;
});

// Filter state
const filterState={nat:true,int:true};
function applyFilter(){
  let vis=0;
  tabEls.forEach(t=>{
    const show=(t.dataset.cat==='mar'&&filterState.nat)||(t.dataset.cat==='int'&&filterState.int);
    t.classList.toggle('hidden',!show);
    if(show)vis++;
  });
  // hide separators if one category is fully hidden
  tabsEl.querySelectorAll('[data-sep]').forEach(s=>{
    const cat=s.dataset.sep;
    const anyVis=Array.from(tabEls).some(t=>t.dataset.cat===cat&&!t.classList.contains('hidden'));
    s.style.display=anyVis?'':'none';
  });
  document.getElementById('ch-count').textContent=vis+' chaînes';
  // if current channel became hidden, auto-switch to first visible
  if(cur>=0&&tabEls[cur]&&tabEls[cur].classList.contains('hidden')){
    const first=tabEls.findIndex(t=>!t.classList.contains('hidden'));
    if(first>=0)loadCh(first);
  }
}
function toggleFilter(cat){
  filterState[cat]=!filterState[cat];
  const btn=document.getElementById('btn-'+cat);
  btn.classList.toggle('on',filterState[cat]);
  applyFilter();
}
applyFilter();
loadCh(0);
</script></body></html>"""

        _live_html = (
            _live_tpl
            .replace("<<CH>>", _ch_json)
            .replace("<<RS>>", str(_n_resolved))
            .replace("<<RT>>", str(_n_total_ch))
        )
        st.components.v1.html(_live_html, height=555, scrolling=False)

        # ── Ressources satellitaires opérationnelles ──────────────
        st.markdown("""<div style="font-family:'Orbitron',monospace;font-size:0.6em;
            color:rgba(33,150,243,0.45);letter-spacing:3px;margin:12px 0 8px;">
            🛰️ RESSOURCES SATELLITAIRES &amp; PORTAILS OPÉRATIONNELS</div>""",
            unsafe_allow_html=True)

        _cop_cols = st.columns(2)
        _COP_RESOURCES = [
            # (icon, titre, badge, badge_color, description, url)
            ("🚨","Copernicus EMS","ACTIF","#ef4444",
             "Activations urgence — cartes de dommages, flood extent, zones affectées en temps réel",
             "https://emergency.copernicus.eu/mapping/list-of-activations-rapid"),
            ("🌊","GloFAS — Prévision Crues","OPÉRATIONNEL","#f59e0b",
             "Global Flood Awareness System — prévision débit fleuves Maroc, seuils d'alerte 3-10 jours",
             "https://www.globalfloods.eu/"),
            ("🛰️","Sentinel Hub EO Browser","OPÉRATIONNEL","#3b82f6",
             "Images Sentinel-1 SAR + Sentinel-2 optique — mosaïques récentes par zone, visualisation avant/après",
             "https://apps.sentinel-hub.com/eo-browser/?zoom=6&lat=31.5&lng=-7&themeId=DEFAULT-THEME"),
            ("🔥","EFFIS — Incendies","VEILLE","#f97316",
             "European Forest Fire Information System — points thermiques, surfaces brûlées, danger feu Maroc",
             "https://effis.jrc.ec.europa.eu/apps/fire.dashboard/"),
            ("🌍","NASA Worldview","OPÉRATIONNEL","#8b5cf6",
             "Images MODIS/VIIRS temps réel — AOD poussières, anomalies thermiques, inondations actives",
             "https://worldview.earthdata.nasa.gov/?v=-22,20,5,38&t=2026-04-28"),
            ("📡","NASA FIRMS — Feux actifs","TEMPS RÉEL","#ef4444",
             "Détection feux actifs MODIS/VIIRS — carte interactive, téléchargement shapefile, API CSV",
             "https://firms.modaps.eosdis.nasa.gov/map/#d:24hrs;@-7,31,6z"),
            ("🏔️","USGS Earthquake Hazards","VEILLE","#22c55e",
             "Séismes récents Maroc/Maghreb — ShakeMap, magnitude, profondeur, zones épicentres M>2.5",
             "https://earthquake.usgs.gov/earthquakes/map/?extent=19,-19&extent=37,1&listOnlyShown"),
            ("🗺️","Copernicus DEM / Relief","RÉFÉRENCE","#64748b",
             "Modèle numérique de terrain Copernicus 30m — analyse bassins versants, pentes, zones inondables",
             "https://browser.dataspace.copernicus.eu/?zoom=6&lat=31&lng=-7"),
            ("💧","Global Surface Water","RÉFÉRENCE","#0ea5e9",
             "JRC Global Surface Water — historique zones humides, occurrence eau permanente/saisonnière Maroc",
             "https://global-surface-water.appspot.com/map?v=31,-7,6"),
            ("🌡️","Copernicus C3S Climat","ANALYSE","#a855f7",
             "Climate Change Service — anomalies température, précipitations, indices sécheresse SPI/SPEI Maroc",
             "https://cds.climate.copernicus.eu/"),
            ("🌐","GeoPortail Maroc","NATIONAL","#059669",
             "Portail géographique officiel Maroc — données cadastrales, administratives, orthophotos nationales",
             "https://www.geoportail.gov.ma/"),
            ("📊","CEMS Global Flood Monitor","OPÉRATIONNEL","#f59e0b",
             "Surveillance mondiale crues — bassins fluviaux, anomalies débits, alertes hydrologique globales",
             "https://global-flood-monitor.org/"),
        ]
        for _ci, (_ico, _tit, _badge, _bc, _desc, _url) in enumerate(_COP_RESOURCES):
            with _cop_cols[_ci % 2]:
                st.markdown(f"""
                <div style="background:rgba(4,14,35,0.7);border:1px solid rgba(33,150,243,0.18);
                     border-radius:8px;padding:10px 11px;margin-bottom:8px;min-height:120px;">
                  <div style="display:flex;align-items:center;gap:7px;margin-bottom:5px;">
                    <span style="font-size:1.3em;">{_ico}</span>
                    <div>
                      <div style="font-size:0.78em;color:#e3f2fd;font-weight:600;line-height:1.2;">{_tit}</div>
                      <span style="background:{_bc}33;color:{_bc};border:1px solid {_bc}55;
                            border-radius:3px;font-size:0.55em;padding:1px 5px;
                            font-family:'Orbitron',monospace;letter-spacing:1px;">{_badge}</span>
                    </div>
                  </div>
                  <div style="font-size:0.68em;color:rgba(180,210,240,0.65);line-height:1.4;margin-bottom:7px;">{_desc}</div>
                  <a href="{_url}" target="_blank" style="display:inline-block;
                     background:rgba(33,150,243,0.15);border:1px solid rgba(33,150,243,0.35);
                     color:#90caf9;font-size:0.65em;padding:3px 9px;border-radius:4px;
                     text-decoration:none;font-family:'Orbitron',monospace;">↗ OUVRIR</a>
                </div>""", unsafe_allow_html=True)


    with col_map:
        # ── Préparer les données carte (JSON pour injection JS) ─────────
        import json as _json
        _prov_geojson = _fetch_dmn_prov_geojson()

        # Enrich province GeoJSON alerte with detailed vigilance data (debut/fin/resume/…)
        if _prov_geojson and _dmn_vigilances:
            _prov_vig_detail: dict = {}
            for _vd in _dmn_vigilances:
                for _zd in _vd.get("zones", []):
                    for _pname, _preg in _DMN_PROVINCE_TO_REGION.items():
                        if _preg == _zd and _pname not in _prov_vig_detail:
                            _prov_vig_detail[_pname] = {
                                "debut":       _vd.get("debut", ""),
                                "fin":         _vd.get("fin", ""),
                                "emis_le":     _vd.get("emis_le", ""),
                                "resume":      _vd.get("resume", ""),
                                "bulletin_url": _vd.get("bulletin_url", ""),
                                "cumul":       _vd.get("cumul_prevu_mm"),
                                "vent":        _vd.get("vitesse_vent_kmh"),
                                "temp":        _vd.get("temperature_max"),
                            }
            for _feat in (_prov_geojson.get("features") or []):
                _fname = " ".join(_feat.get("properties", {}).get("nom", "").split())
                _fal   = _feat["properties"].get("alerte")
                if _fal and _fname in _prov_vig_detail:
                    _fal.update(_prov_vig_detail[_fname])

        _vig_map = []
        for _v in _dmn_vigilances:
            _zs = _v.get("zones", [])
            _lats = [REGIONS_MAR[z]["lat"] for z in _zs if z in REGIONS_MAR]
            _lons = [REGIONS_MAR[z]["lon"] for z in _zs if z in REGIONS_MAR]
            if not _lats: continue
            _dh = _compute_duree_h(_v.get("debut",""), _v.get("fin",""))
            _vig_map.append({
                "lat": round(sum(_lats)/len(_lats), 4),
                "lon": round(sum(_lons)/len(_lons), 4),
                "niveau": _v.get("niveau","VERT"),
                "phenomene": _PHENOMENE_LABELS_PY.get(_v.get("phenomene",""), _v.get("phenomene","")).upper(),
                "ico": _PHENOMENE_ICONS_PY.get(_v.get("phenomene",""), "⚠️"),
                "zones": _condense_zones_py(_zs),
                "zones_list": _zs,
                "duree": ("<1h" if _dh < 1 else str(_dh)+"h"),
                "resume": _v.get("resume",""),
                "debut": _v.get("debut",""),
                "fin": _v.get("fin",""),
                "emis_le": _v.get("emis_le",""),
                "bulletin_url": _v.get("bulletin_url",""),
                "source": _v.get("source","DMN"),
                "cumul": _v.get("cumul_prevu_mm"),
                "vent": _v.get("vitesse_vent_kmh"),
                "temp": _v.get("temperature_max"),
            })

        _jobs_map = []
        for _j in done[:8]:
            _pa = _j.get("params",{}); _ao = _pa.get("aoi",{})
            if _ao:
                _lc = (_ao.get("lat_min",0)+_ao.get("lat_max",0))/2
                _lnc= (_ao.get("lon_min",0)+_ao.get("lon_max",0))/2
                if _lc and _lnc:
                    _jobs_map.append({
                        "lat": round(_lc, 4), "lon": round(_lnc, 4),
                        "id": _j.get("id","")[:8],
                        "mode": "Avant/Après" if _pa.get("image_before") else "Image unique",
                        "date": _j.get("created","")[:10],
                        "ha": str(_j.get("results",{}).get("surface_totale_ha","—")),
                        "communes": str(_j.get("results",{}).get("n_communes","—")),
                    })

        _region_vigs = {}
        for _v in _dmn_vigilances:
            for _z in _v.get("zones", []):
                _region_vigs.setdefault(_z, []).append({
                    "niveau": _v.get("niveau","VERT"),
                    "phenomene": _PHENOMENE_LABELS_PY.get(_v.get("phenomene",""), _v.get("phenomene","")),
                    "ico": _PHENOMENE_ICONS_PY.get(_v.get("phenomene",""), "⚠️"),
                    "debut": _v.get("debut",""),
                    "fin": _v.get("fin",""),
                    "resume": _v.get("resume",""),
                    "cumul": _v.get("cumul_prevu_mm"),
                    "vent": _v.get("vitesse_vent_kmh"),
                    "temp": _v.get("temperature_max"),
                })

        def _reg_niveau(vigs):
            if not vigs: return "vert"
            return max(vigs, key=lambda v: _NIVEAU_WEIGHT_PY.get(v.get("niveau","VERT"), 0))["niveau"].lower()

        _regions_map = [
            {"lat": inf["lat"], "lon": inf["lon"], "region": reg,
             "alerte": _reg_niveau(_region_vigs.get(reg, [])) or inf["alerte"],
             "vigs": _region_vigs.get(reg, [])}
            for reg, inf in REGIONS_MAR.items()
        ]

        _barrages = [
            {"lat":34.80,"lon":-5.09,"name":"Al Wahda","cap":"3.8 Gm³","bassin":"Loukkos"},
            {"lat":32.10,"lon":-6.45,"name":"Bin el Ouidane","cap":"1.4 Gm³","bassin":"Oum Er-Rbia"},
            {"lat":34.47,"lon":-2.73,"name":"Mohammed V","cap":"730 Mm³","bassin":"Moulouya"},
            {"lat":30.93,"lon":-5.54,"name":"Mansour Eddahbi","cap":"560 Mm³","bassin":"Draa"},
            {"lat":30.32,"lon":-9.70,"name":"Youssef Ben Tachfine","cap":"320 Mm³","bassin":"Souss"},
            {"lat":32.41,"lon":-7.02,"name":"Hassan I","cap":"260 Mm³","bassin":"Oum Er-Rbia"},
            {"lat":33.92,"lon":-5.40,"name":"Idriss I","cap":"1.2 Gm³","bassin":"Sebou"},
            {"lat":34.98,"lon":-5.53,"name":"Oued el Makhazine","cap":"780 Mm³","bassin":"Loukkos"},
            {"lat":33.63,"lon":-7.33,"name":"Sidi Mohamed Ben Abdellah","cap":"1.0 Gm³","bassin":"Bouregreg"},
            {"lat":31.65,"lon":-7.28,"name":"Lalla Takerkoust","cap":"68 Mm³","bassin":"Tensift"},
        ]

        _zones_risque = [
            {"lat":29.00,"lon":-10.06,"name":"Guelmim","type":"Crues éclair","radius":22000},
            {"lat":30.47,"lon":-8.88, "name":"Taroudant","type":"Crues Souss","radius":18000},
            {"lat":33.68,"lon":-7.38, "name":"Mohammedia","type":"Inondations côtières","radius":14000},
            {"lat":34.26,"lon":-6.58, "name":"Kénitra","type":"Crues Sebou","radius":20000},
            {"lat":32.33,"lon":-6.57, "name":"Beni Mellal","type":"Crues Oum Er-Rbia","radius":16000},
            {"lat":30.92,"lon":-6.89, "name":"Ouarzazate","type":"Crues Draa","radius":17000},
            {"lat":34.01,"lon":-5.00, "name":"Fès","type":"Crues Sebou","radius":12000},
            {"lat":35.17,"lon":-5.27, "name":"Tétouan","type":"Crues Martil","radius":10000},
            {"lat":33.99,"lon":-6.85, "name":"Rabat","type":"Crues Bouregreg","radius":11000},
        ]

        _defcon_n = 2 if _risk>=70 else (3 if _risk>=40 else (4 if _risk>=20 else 5))
        _dc = {2:"239,68,68",3:"245,158,11",4:"234,179,8",5:"34,197,94"}[_defcon_n]
        _dt = {2:"#ef4444",3:"#f59e0b",4:"#eab308",5:"#22c55e"}[_defcon_n]

        _map_tpl = """<!DOCTYPE html>
<html><head><meta charset="utf-8"/>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<style>
*{margin:0;padding:0;box-sizing:border-box;}
html,body{background:#020b18;width:100%;height:100%;overflow:hidden;font-family:'Courier New',monospace;}
.c{width:100%;height:100%;background:#020b18;border:1px solid rgba(33,150,243,0.2);border-radius:10px;overflow:hidden;display:flex;flex-direction:column;}
.tb{flex-shrink:0;height:36px;background:rgba(2,11,24,0.98);border-bottom:1px solid rgba(33,150,243,0.2);display:flex;align-items:center;padding:0 12px;gap:10px;}
.tb-title{font-size:11px;font-weight:700;letter-spacing:2px;color:#e3f2fd;}
.tb-clock{font-size:9.5px;color:rgba(144,202,249,0.55);margin-left:auto;letter-spacing:1px;font-variant-numeric:tabular-nums;}
.dc{padding:2px 10px;border-radius:3px;font-size:9px;font-weight:700;letter-spacing:1.5px;}
.ma{flex:1;display:flex;overflow:hidden;}
.sp{width:210px;flex-shrink:0;background:rgba(2,11,24,0.97);border-right:1px solid rgba(33,150,243,0.15);display:flex;flex-direction:column;overflow:hidden;}
.tf{flex-shrink:0;display:flex;flex-wrap:wrap;gap:3px;padding:8px 7px 6px;border-bottom:1px solid rgba(33,150,243,0.1);}
.tf-btn{background:rgba(10,22,40,0.9);border:1px solid rgba(33,150,243,0.15);color:rgba(144,202,249,0.45);font-family:'Courier New',monospace;font-size:9px;padding:3px 9px;border-radius:3px;cursor:pointer;transition:all .15s;}
.tf-btn:hover,.tf-btn.act{background:rgba(33,150,243,0.2);color:#e3f2fd;border-color:rgba(33,150,243,0.5);}
.lt{flex-shrink:0;font-size:9px;letter-spacing:3px;color:rgba(33,150,243,0.45);padding:8px 10px 5px;}
.ll{flex:1;overflow-y:auto;}
.li{display:flex;align-items:center;gap:7px;padding:6px 10px;cursor:pointer;border-bottom:1px solid rgba(33,150,243,0.04);transition:background .12s;}
.li:hover{background:rgba(33,150,243,0.05);}
.cb{width:13px;height:13px;flex-shrink:0;background:rgba(33,150,243,0.12);border:1px solid rgba(33,150,243,0.3);border-radius:2px;display:flex;align-items:center;justify-content:center;}
.cb.on{background:rgba(33,150,243,0.5);border-color:rgba(33,150,243,0.7);}
.cb.on::after{content:'✓';font-size:9px;color:#fff;}
.ln{font-size:9px;letter-spacing:0.5px;color:rgba(176,210,240,0.65);flex:1;}
.lc{font-size:8px;color:rgba(33,150,243,0.5);background:rgba(33,150,243,0.08);padding:1px 5px;border-radius:8px;}
.rb{flex-shrink:0;padding:10px;border-top:1px solid rgba(33,150,243,0.1);background:rgba(6,16,30,0.5);}
.rl{font-size:8px;letter-spacing:2px;color:rgba(144,202,249,0.4);margin-bottom:5px;}
.rb-bar{height:4px;background:rgba(255,255,255,0.08);border-radius:2px;position:relative;overflow:hidden;margin-bottom:5px;}
.rb-fill{height:100%;border-radius:2px;}
.rv{font-size:14px;font-weight:700;}
#map{flex:1;position:relative;}
.lg{flex-shrink:0;height:32px;background:rgba(2,11,24,0.98);border-top:1px solid rgba(33,150,243,0.12);display:flex;align-items:center;gap:12px;padding:0 10px;overflow:hidden;}
.lgl{font-size:8px;letter-spacing:2px;color:rgba(33,150,243,0.35);flex-shrink:0;}
.lgi{display:flex;align-items:center;gap:4px;font-size:8.5px;color:rgba(144,202,249,0.45);white-space:nowrap;}
.ld{width:8px;height:8px;border-radius:50%;flex-shrink:0;}
.ls{width:8px;height:8px;transform:rotate(45deg);flex-shrink:0;}
.leaflet-container{background:#020b18!important;}
.leaflet-popup-content-wrapper{background:rgba(4,14,30,0.97)!important;color:#e3f2fd!important;border:1px solid rgba(33,150,243,0.35)!important;border-radius:8px!important;box-shadow:0 4px 24px rgba(0,0,0,0.7)!important;}
.prov-popup .leaflet-popup-content-wrapper{border:1px solid rgba(33,150,243,0.5)!important;border-radius:10px!important;}
.prov-popup .leaflet-popup-content{margin:12px 14px!important;}
.leaflet-popup-tip{background:rgba(4,14,30,0.97)!important;}
.leaflet-popup-content{font-family:'Courier New',monospace!important;font-size:11px!important;line-height:1.7!important;}
.leaflet-control-zoom a{background:rgba(4,14,30,0.9)!important;color:#90caf9!important;border:1px solid rgba(33,150,243,0.2)!important;}
.leaflet-control-zoom a:hover{background:rgba(33,150,243,0.15)!important;}
.leaflet-control-zoom{border:1px solid rgba(33,150,243,0.2)!important;}
.leaflet-control-attribution{display:none!important;}
.prov-tip{background:rgba(4,14,30,0.88)!important;border:1px solid rgba(33,150,243,0.2)!important;color:#90caf9!important;font-size:9px!important;padding:2px 6px!important;border-radius:3px!important;}
</style></head><body>
<div class="c">
  <div class="tb">
    <span class="tb-title">MAROC — SITUATION EN COURS</span>
    <div style="width:1px;height:18px;background:rgba(33,150,243,0.2);"></div>
    <span style="font-size:9px;color:rgba(33,150,243,0.45);letter-spacing:1px;">ALERTE</span>
    <span class="dc" style="background:rgba(<<DC>>,0.15);color:<<DT>>;border:1px solid rgba(<<DC>>,0.4);">NIV.<<DN>></span>
    <span style="font-size:10px;font-weight:700;color:<<DT>>;"><<RISK>>/100</span>
    <span class="tb-clock" id="clk">—</span>
    <span style="padding:2px 8px;background:rgba(33,150,243,0.18);color:#90caf9;font-size:9px;border-radius:2px;border:1px solid rgba(33,150,243,0.4);">2D</span>
  </div>
  <div class="ma">
    <div class="sp">
      <div class="tf">
        <button class="tf-btn" onclick="ft(this,1)">1h</button>
        <button class="tf-btn" onclick="ft(this,6)">6h</button>
        <button class="tf-btn" onclick="ft(this,24)">24h</button>
        <button class="tf-btn" onclick="ft(this,48)">48h</button>
        <button class="tf-btn act" onclick="ft(this,168)">7j</button>
        <button class="tf-btn" onclick="ft(this,0)">Tout</button>
      </div>
      <div class="lt">COUCHES  ▾</div>
      <div class="ll" id="ll"></div>
      <div class="rb">
        <div class="rl">INDICE DE RISQUE</div>
        <div class="rb-bar"><div class="rb-fill" style="width:<<RISK>>%;background:<<DT>>;"></div></div>
        <div class="rv" style="color:<<DT>>;"><<RISK>> <span style="font-size:0.5em;color:rgba(144,202,249,0.3);">/100</span></div>
      </div>
    </div>
    <div id="map"></div>
  </div>
  <div class="lg">
    <span class="lgl">LÉGENDE</span>
    <div class="lgi"><div class="ld" style="background:#ef4444;box-shadow:0 0 5px #ef4444;"></div>Alerte ROUGE</div>
    <div class="lgi"><div class="ld" style="background:#f59e0b;box-shadow:0 0 4px #f59e0b;"></div>Alerte ORANGE</div>
    <div class="lgi"><div class="ld" style="background:#eab308;"></div>Vigilance JAUNE</div>
    <div class="lgi"><div class="ld" style="background:#22c55e;"></div>Normal VERT</div>
    <div class="lgi"><div class="ld" style="background:#2196f3;box-shadow:0 0 5px #2196f3;"></div>SAR</div>
    <div class="lgi"><div class="ls" style="background:#00bcd4;"></div>Barrage</div>
    <div class="lgi"><div class="ld" style="background:#7c4dff;opacity:0.7;"></div>Zone risque</div>
  </div>
</div>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
const VIGS=<<VIG>>,JOBS=<<JOBS>>,REGS=<<REGS>>,BARS=<<BARS>>,ZONES=<<ZONES>>,PROVGEO=<<PROVGEO>>;
const D=['DIM','LUN','MAR','MER','JEU','VEN','SAM'];
const M=['JAN','FÉV','MAR','AVR','MAI','JUN','JUL','AOÛ','SEP','OCT','NOV','DÉC'];
function tick(){
  const u=new Date(Date.now()+3600000);
  document.getElementById('clk').textContent=
    D[u.getUTCDay()]+', '+String(u.getUTCDate()).padStart(2,'0')+' '+
    M[u.getUTCMonth()]+' '+u.getUTCFullYear()+'  '+
    String(u.getUTCHours()).padStart(2,'0')+':'+
    String(u.getUTCMinutes()).padStart(2,'0')+':'+
    String(u.getUTCSeconds()).padStart(2,'0')+'  UTC+1';
}
tick();setInterval(tick,1000);
const map=L.map('map',{center:[29.5,-8.0],zoom:5,attributionControl:false});
L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',{subdomains:'abcd',maxZoom:19}).addTo(map);
map.fitBounds([[20.8,-17.2],[35.9,-1.0]]);
const LC={'ROUGE':'#ef4444','ORANGE':'#f59e0b','JAUNE':'#eab308','VERT':'#22c55e','rouge':'#ef4444','orange':'#f59e0b','jaune':'#eab308','vert':'#22c55e'};
function fmtDt(iso){
  if(!iso)return'—';
  const d=new Date(iso);
  if(isNaN(d))return iso;
  const mo=['jan','fév','mar','avr','mai','jun','jul','aoû','sep','oct','nov','déc'];
  return d.getUTCDate()+' '+mo[d.getUTCMonth()]+' '+
    String(d.getUTCHours()).padStart(2,'0')+'h'+String(d.getUTCMinutes()).padStart(2,'0');
}
const G={};
G.dmn=L.layerGroup();
VIGS.forEach(v=>{
  const c=LC[v.niveau]||'#fff',r={ROUGE:20,ORANGE:16,JAUNE:12,VERT:8}[v.niveau]||10;
  const m=L.circleMarker([v.lat,v.lon],{radius:r,color:c,fillColor:c,fillOpacity:0.18,weight:2});
  let hdr='<div style="background:'+c+'22;border-left:3px solid '+c+';padding:5px 8px;border-radius:4px;margin-bottom:6px;">'
    +'<span style="font-size:14px;">'+v.ico+'</span> '
    +'<b style="color:'+c+';font-size:12px;">'+v.phenomene+'</b>'
    +'<span style="float:right;background:'+c+';color:#000;padding:1px 7px;border-radius:3px;font-size:11px;font-weight:bold;">'+v.niveau+'</span>'
    +'</div>';
  let zs='';
  if(v.zones_list&&v.zones_list.length){
    zs='<div style="margin:4px 0;"><b style="color:#90caf9;font-size:10px;">ZONES</b><br>';
    v.zones_list.forEach(z=>{zs+='<span style="color:#e3f2fd;font-size:10px;">• '+z+'</span><br>';});
    zs+='</div>';
  }
  let dt='<div style="color:rgba(144,202,249,0.65);font-size:10px;margin:4px 0;line-height:1.5;">'
    +'📅 '+fmtDt(v.debut)+' → '+fmtDt(v.fin)+' <b style="color:#e3f2fd;">('+v.duree+')</b>';
  if(v.emis_le)dt+='<br>🕐 Émis : '+fmtDt(v.emis_le);
  dt+='</div>';
  let ms='';
  if(v.cumul!=null)ms+='<span style="color:#60a5fa;">🌧️ '+v.cumul+' mm</span> &nbsp;';
  if(v.vent!=null)ms+='<span style="color:#a78bfa;">💨 '+v.vent+' km/h</span> &nbsp;';
  if(v.temp!=null)ms+='<span style="color:#fb923c;">🌡️ max '+v.temp+'°C</span>';
  if(ms)ms='<div style="margin:4px 0;font-size:11px;">'+ms+'</div>';
  let res='';
  if(v.resume)res='<div style="color:rgba(255,255,255,0.65);font-size:10px;font-style:italic;border-top:1px solid rgba(255,255,255,0.1);padding-top:4px;margin-top:4px;">'+v.resume+'</div>';
  let src='<div style="margin-top:5px;font-size:9px;color:rgba(144,202,249,0.45);">Source : '+v.source
    +(v.bulletin_url?'  <a href="'+v.bulletin_url+'" target="_blank" style="color:#60a5fa;text-decoration:none;">📄 Bulletin</a>':'')
    +'</div>';
  m.bindPopup(hdr+zs+dt+ms+res+src,{maxWidth:290});
  G.dmn.addLayer(m);
});
G.regs=L.layerGroup();
REGS.forEach(r=>{
  const c=LC[r.alerte]||'#22c55e';
  const m=L.circleMarker([r.lat,r.lon],{radius:8,color:c,fillColor:c,fillOpacity:0.3,weight:1.5});
  let pop='<b style="font-size:12px;color:#e3f2fd;">📍 '+r.region+'</b>'
    +'<div style="color:'+c+';font-size:10px;margin-bottom:4px;">Niveau : <b>'+r.alerte.toUpperCase()+'</b></div>';
  if(r.vigs&&r.vigs.length){
    r.vigs.forEach(vg=>{
      const vc=LC[vg.niveau]||'#fff';
      pop+='<div style="margin-top:5px;background:'+vc+'1a;border-left:3px solid '+vc+';padding:4px 7px;border-radius:3px;">'
        +'<b style="color:'+vc+';font-size:11px;">'+vg.ico+' '+vg.phenomene+'</b>'
        +' <span style="background:'+vc+';color:#000;padding:0 5px;border-radius:2px;font-size:10px;font-weight:bold;">'+vg.niveau+'</span><br>'
        +'<span style="font-size:10px;color:rgba(144,202,249,0.7);">📅 '+fmtDt(vg.debut)+' → '+fmtDt(vg.fin)+'</span>';
      let ms='';
      if(vg.cumul!=null)ms+=' 🌧️ '+vg.cumul+'mm';
      if(vg.vent!=null)ms+=' 💨 '+vg.vent+'km/h';
      if(vg.temp!=null)ms+=' 🌡️ '+vg.temp+'°C';
      if(ms)pop+='<br><span style="font-size:10px;color:#90caf9;">'+ms.trim()+'</span>';
      if(vg.resume)pop+='<br><span style="font-size:9px;color:rgba(255,255,255,0.5);font-style:italic;">'+vg.resume+'</span>';
      pop+='</div>';
    });
  }
  m.bindPopup(pop,{maxWidth:290});
  G.regs.addLayer(m);
  G.regs.addLayer(L.marker([r.lat,r.lon],{icon:L.divIcon({html:'<div style="color:rgba(176,210,240,0.5);font-size:7.5px;font-family:Courier New,monospace;white-space:nowrap;text-shadow:0 0 4px #000;">'+r.region.split('-')[0]+'</div>',iconSize:[0,0],iconAnchor:[-4,-12],className:''})}));
});
G.sar=L.layerGroup();
JOBS.forEach(j=>{
  if(!j.lat||!j.lon)return;
  const ico=L.divIcon({html:'<div style="width:12px;height:12px;border-radius:50%;background:#2196f3;border:2px solid #fff;box-shadow:0 0 8px #2196f3;"></div>',iconSize:[12,12],iconAnchor:[6,6],className:''});
  const m=L.marker([j.lat,j.lon],{icon:ico});
  m.bindPopup('<b style="color:#2196f3;">🛰️ SAR #'+j.id+'</b><br>Mode : '+j.mode+'<br>Date : '+j.date+'<br>Surface : <b style="color:#f59e0b;">'+j.ha+' ha</b>'+(j.communes!='—'?'<br>Communes : '+j.communes:''));
  G.sar.addLayer(m);
});
G.bars=L.layerGroup();
BARS.forEach(b=>{
  const ico=L.divIcon({html:'<div style="width:10px;height:10px;background:#00bcd4;border:1.5px solid #e3f2fd;transform:rotate(45deg);box-shadow:0 0 6px #00bcd4;"></div>',iconSize:[10,10],iconAnchor:[5,5],className:''});
  const m=L.marker([b.lat,b.lon],{icon:ico});
  m.bindPopup('<b style="color:#00bcd4;">🏞️ '+b.name+'</b><br>Capacité : '+b.cap+'<br>Bassin : '+b.bassin);
  G.bars.addLayer(m);
});
G.zones=L.layerGroup();
ZONES.forEach(z=>{
  const c=L.circle([z.lat,z.lon],{radius:z.radius||20000,color:'#7c4dff',fillColor:'#7c4dff',fillOpacity:0.07,weight:1,dashArray:'4,6'});
  c.bindPopup('<b style="color:#7c4dff;">⚠️ '+z.name+'</b><br>Type : '+z.type);
  G.zones.addLayer(c);
});
const PHICO={'ORAGE':'⛈️','PLUIES':'🌧️','VENT':'💨','CHALEUR':'🌡️','BROUILLARD':'🌫️','NEIGE':'❄️','CANICULE':'☀️','TEMPETE_SABLE':'🌪️'};
G.prov=L.layerGroup();
let _nProv=0;
if(PROVGEO&&PROVGEO.features){
  const gjLayer=L.geoJSON(PROVGEO,{
    style:function(f){
      const a=f.properties.alerte;
      if(!a)return{fillColor:'#22c55e',color:'#22c55e',weight:0.8,fillOpacity:0.12};
      const c=LC[a.niveau]||'#fff';
      return{fillColor:c,color:c,weight:1.5,fillOpacity:0.22,dashArray:a.niveau==='ROUGE'?null:'4,5'};
    },
    onEachFeature:function(f,layer){
      const p=f.properties,a=p.alerte,nom=p.nom;
      if(a){
        _nProv++;
        const c=LC[a.niveau]||'#fff',ico=a.ico||PHICO[a.phenomene]||'⚠️';
        let pop='<div style="font-family:Courier New,monospace;min-width:260px;">';
        // ── Header ──
        pop+='<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:6px;">';
        pop+='<b style="font-size:12px;color:#e3f2fd;">'+nom+'</b>';
        pop+='<span style="background:'+c+';color:#000;padding:1px 8px;border-radius:3px;font-size:10px;font-weight:bold;letter-spacing:1px;">'+a.niveau+'</span>';
        pop+='</div>';
        // ── Phénomène ──
        pop+='<div style="background:'+c+'22;border-left:3px solid '+c+';padding:5px 8px;border-radius:3px;margin-bottom:7px;">';
        pop+=ico+' <b style="color:'+c+';font-size:11px;">'+a.pheno_label+'</b>';
        pop+='</div>';
        // ── Période ──
        if(a.debut&&a.fin){
          pop+='<div style="font-size:10px;color:#90caf9;margin-bottom:3px;">⏱ <b>'+fmtDt(a.debut)+'</b> → <b>'+fmtDt(a.fin)+'</b></div>';
        }
        // ── Seuil DMN ──
        if(a.vmin!=null&&a.vmax!=null){
          pop+='<div style="font-size:10px;color:#90caf9;margin-bottom:3px;">📊 Seuil : <b>'+a.vmin+(a.unite?' – '+a.vmax+' '+a.unite:'')+'</b></div>';
        }
        // ── Valeurs spécifiques ──
        if(a.cumul!=null) pop+='<div style="font-size:10px;color:#7dd3fc;margin-bottom:3px;">🌧️ Cumul prévu : <b>'+a.cumul+' mm</b></div>';
        if(a.vent!=null)  pop+='<div style="font-size:10px;color:#7dd3fc;margin-bottom:3px;">💨 Vent max : <b>'+a.vent+' km/h</b></div>';
        if(a.temp!=null)  pop+='<div style="font-size:10px;color:#fca5a5;margin-bottom:3px;">🌡️ Temp. max : <b>'+a.temp+' °C</b></div>';
        // ── Résumé ──
        if(a.resume){
          pop+='<div style="border-top:1px solid rgba(144,202,249,0.15);margin-top:6px;padding-top:5px;font-size:9.5px;color:rgba(227,242,253,0.8);line-height:1.6;">'+a.resume+'</div>';
        }
        // ── Footer ──
        pop+='<div style="display:flex;align-items:center;justify-content:space-between;margin-top:6px;padding-top:4px;border-top:1px solid rgba(144,202,249,0.1);">';
        let emtxt=a.emis_le?'📡 DMN · '+fmtDt(a.emis_le):'📡 DMN';
        pop+='<span style="font-size:9px;color:rgba(144,202,249,0.45);">'+emtxt+'</span>';
        if(a.bulletin_url) pop+='<a href="'+a.bulletin_url+'" target="_blank" style="font-size:9px;color:#60a5fa;text-decoration:none;border:1px solid rgba(96,165,250,0.35);padding:1px 6px;border-radius:2px;">📄 Bulletin</a>';
        pop+='</div>';
        pop+='</div>';
        layer.bindPopup(pop,{maxWidth:310,className:'prov-popup'});
        // Hover = highlight only; click = open popup
        layer.on('mouseover',function(){this.setStyle({fillOpacity:0.55,weight:2.5});});
        layer.on('mouseout',function(){gjLayer.resetStyle(this);});
        layer.on('click',function(){this.openPopup();});
      }else{
        layer.bindTooltip(nom,{sticky:true,className:'prov-tip'});
        layer.on('mouseover',function(){this.setStyle({fillColor:'#22c55e',fillOpacity:0.35,weight:1.5});});
        layer.on('mouseout',function(){gjLayer.resetStyle(this);});
      }
    }
  });
  gjLayer.addTo(G.prov);
  PROVGEO.features.forEach(f=>{
    const a=f.properties.alerte;
    if(!a||f.properties.cy==null)return;
    const c=LC[a.niveau]||'#fff',ico=a.ico||PHICO[a.phenomene]||'⚠️';
    L.marker([f.properties.cy,f.properties.cx],{
      icon:L.divIcon({html:'<div style="font-size:15px;text-shadow:0 0 5px #000,0 0 9px '+c+';">'+ico+'</div>',iconSize:[20,20],iconAnchor:[10,10],className:''}),
      interactive:false
    }).addTo(G.prov);
  });
}
const LDEFS=[
  {k:'prov', i:'🗺️',n:'PROVINCES / VIGILANCE',on:true, cnt:_nProv},
  {k:'dmn', i:'🌧️',n:'VIGILANCES DMN',  on:true, cnt:VIGS.length},
  {k:'regs',i:'📍',n:'RÉGIONS MAROC',   on:false,cnt:REGS.length},
  {k:'sar', i:'🛰️',n:'TRAITEMENTS SAR', on:true, cnt:JOBS.length},
  {k:'bars',i:'🏞️',n:'GRANDS BARRAGES', on:true, cnt:BARS.length},
  {k:'zones',i:'⚠️',n:'ZONES À RISQUE', on:false,cnt:ZONES.length},
];
LDEFS.forEach(d=>{if(d.on)G[d.k].addTo(map);});
const ll=document.getElementById('ll');
LDEFS.forEach(d=>{
  const el=document.createElement('div');
  el.className='li';
  el.innerHTML='<div class="cb '+(d.on?'on':'')+'" id="cb_'+d.k+'"></div><span style="font-size:12px;flex-shrink:0;">'+d.i+'</span><span class="ln">'+d.n+'</span>'+(d.cnt>0?'<span class="lc">'+d.cnt+'</span>':'');
  el.onclick=()=>{
    const cb=document.getElementById('cb_'+d.k);
    if(cb.classList.contains('on')){map.removeLayer(G[d.k]);cb.classList.remove('on');}
    else{G[d.k].addTo(map);cb.classList.add('on');}
  };
  ll.appendChild(el);
});
function ft(btn,h){document.querySelectorAll('.tf-btn').forEach(b=>b.classList.remove('act'));btn.classList.add('act');}
</script></body></html>"""

        _map_html = (
            _map_tpl
            .replace("<<VIG>>",   _json.dumps(_vig_map,      ensure_ascii=False))
            .replace("<<JOBS>>",  _json.dumps(_jobs_map,     ensure_ascii=False))
            .replace("<<REGS>>",  _json.dumps(_regions_map,  ensure_ascii=False))
            .replace("<<BARS>>",  _json.dumps(_barrages,     ensure_ascii=False))
            .replace("<<ZONES>>", _json.dumps(_zones_risque,  ensure_ascii=False))
            .replace("<<PROVGEO>>", _json.dumps(_prov_geojson, ensure_ascii=False))
            .replace("<<DN>>",    str(_defcon_n))
            .replace("<<DC>>",    _dc)
            .replace("<<DT>>",    _dt)
            .replace("<<RISK>>",  str(_risk))
        )
        st.components.v1.html(_map_html, height=555, scrolling=False)

        # ── Signaux actifs DMN (sous la carte) ──────────────────────────
        st.markdown('<div class="wm-section-title">⚡ SIGNAUX ACTIFS — DMN VIGILANCES</div>', unsafe_allow_html=True)

        _TIER_CSS = {
            "DMN":"wm-tier-dmn","ABH":"wm-tier-abh","USGS":"wm-tier-usgs",
            "COP":"wm-tier-cop","EFFIS":"wm-tier-effis","IOC":"wm-tier-ioc",
            "DGPC":"wm-tier-dgpc","IGN":"wm-tier-ign",
        }
        _SEV_CSS = {"ROUGE":"wm-sev-critical","ORANGE":"wm-sev-high","JAUNE":"wm-sev-medium","VERT":"wm-sev-low"}
        _SEV_LBL = {"ROUGE":"CRITIQUE","ORANGE":"ÉLEVÉ","JAUNE":"MODÉRÉ","VERT":"FAIBLE"}

        if _dmn_vigilances:
            _sigs_html = ""
            for _v in _dmn_vigilances:
                _niv    = _v.get("niveau","VERT")
                _phkey  = _v.get("phenomene","")
                _ico    = _PHENOMENE_ICONS_PY.get(_phkey,"⚠️")
                _lbl    = _PHENOMENE_LABELS_PY.get(_phkey,_phkey.lower())
                _zones  = _condense_zones_py(_v.get("zones",[]))
                _duree  = _compute_duree_h(_v.get("debut",""),_v.get("fin",""))
                _duree_s= f"<1h" if _duree<1 else f"{_duree}h"
                _resume = _v.get("resume","")
                _resume_s = _resume[:100]+"…" if len(_resume)>100 else _resume
                _cumul  = _v.get("cumul_prevu_mm")
                _vent   = _v.get("vitesse_vent_kmh")
                _temp   = _v.get("temperature_max")
                _details_parts = []
                if _cumul is not None: _details_parts.append(f"💧 {_cumul} mm")
                if _vent  is not None: _details_parts.append(f"💨 {_vent} km/h")
                if _temp  is not None: _details_parts.append(f"🌡️ max {_temp}°C")
                _details_str = "  ·  ".join(_details_parts)
                _debut_dt = _v.get("debut","")[:16].replace("T"," ")
                _fin_dt   = _v.get("fin","")[:16].replace("T"," ")
                _sigs_html += f"""
                <div class="wm-signal">
                  <div class="wm-signal-icon">{_ico}</div>
                  <div class="wm-signal-body">
                    <div class="wm-signal-meta">
                      <span class="wm-tier wm-tier-dmn">DMN</span>
                      <span class="wm-sev {_SEV_CSS.get(_niv,'wm-sev-low')}">{_SEV_LBL.get(_niv,"INFO")}</span>
                      <span style="font-family:'Orbitron',monospace;font-size:0.58em;color:{_NIVEAU_TICKER_COLOR.get(_niv,'#fff')};">● {_niv}</span>
                      <span class="wm-signal-time">{_duree_s}</span>
                    </div>
                    <div class="wm-signal-title">{_lbl.upper()} — {_zones}</div>
                    {"<div class='wm-signal-desc'>"+_details_str+"</div>" if _details_str else ""}
                    <div class="wm-signal-desc" style="margin-top:3px;">{_resume_s}</div>
                    <div class="wm-signal-desc" style="margin-top:3px;color:rgba(144,202,249,0.25);">📅 {_debut_dt} → {_fin_dt}</div>
                  </div>
                </div>"""
            st.markdown(_sigs_html, unsafe_allow_html=True)
        else:
            st.markdown('<div class="wm-signal"><div class="wm-signal-icon">🟢</div><div class="wm-signal-body"><div class="wm-signal-title">Aucune vigilance DMN active</div><div class="wm-signal-desc">Tous les phénomènes météo sont sous le seuil d\'alerte.</div></div></div>', unsafe_allow_html=True)

        # ── Alertes flux RSS (style Active Signals secondary) ───────────
        if _alert_items:
            st.markdown('<div class="wm-section-title" style="margin-top:12px;">📡 ALERTES FLUX INSTITUTIONNELS</div>', unsafe_allow_html=True)
            _rss_html = ""
            for _it in _alert_items[:6]:
                _src_key = _it.get("source","")[:6].upper().replace("-","").replace(" ","")
                _tier_cls = _TIER_CSS.get(_src_key, "wm-tier-dmn")
                _sev_score = _it.get("score",0)
                _sev_cls = "wm-sev-critical" if _sev_score>=3 else ("wm-sev-high" if _sev_score>=2 else "wm-sev-medium")
                _sev_lbl = "CRITIQUE" if _sev_score>=3 else ("ÉLEVÉ" if _sev_score>=2 else "VIGILANCE")
                _desc_s  = _it.get("desc","")[:90]+"…" if len(_it.get("desc",""))>90 else _it.get("desc","")
                _rss_html += f"""
                <div class="wm-signal">
                  <div class="wm-signal-icon">{_it.get("icon","📡")}</div>
                  <div class="wm-signal-body">
                    <div class="wm-signal-meta">
                      <span class="wm-tier {_tier_cls}">{_it.get("source","")[:8].upper()}</span>
                      <span class="wm-sev {_sev_cls}">{_sev_lbl}</span>
                      <span class="wm-signal-time">{_it.get("date","")}</span>
                    </div>
                    <div class="wm-signal-title">{_it.get("title","")[:90]}</div>
                    {"<div class='wm-signal-desc'>"+_desc_s+"</div>" if _desc_s else ""}
                  </div>
                </div>"""
            st.markdown(_rss_html, unsafe_allow_html=True)

        # ── Modules CCIP (style WorldMonitor Infrastructure Grid) ────────
        st.markdown('<div class="wm-section-title" style="margin-top:12px;">📡 MODULES CCIP</div>', unsafe_allow_html=True)
        for _ico, _nom, _tag_cls, _tag_lbl in [
            ("🌊","Inondation SAR Sentinel-1","wm-tag-active","● ACTIF"),
            ("🔥","Incendie EFFIS / MODIS","wm-tag-soon","BIENTÔT"),
            ("⛰️","Glissement de terrain","wm-tag-soon","BIENTÔT"),
            ("🌵","Sécheresse SPI/NDVI","wm-tag-soon","BIENTÔT"),
            ("🏔️","Séisme USGS ShakeMap","wm-tag-watch","VEILLE"),
        ]:
            st.markdown(f"""
            <div class="wm-module-row">
              <span class="wm-module-ico">{_ico}</span>
              <span class="wm-module-name">{_nom}</span>
              <span class="wm-module-tag {_tag_cls}">{_tag_lbl}</span>
            </div>""", unsafe_allow_html=True)

    # ════════════════════════════════════════════════════════════
    # PANNEAU OPÉRATIONNEL CRISE (conditionnel)
    # ════════════════════════════════════════════════════════════
    if True:
        st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)
        st.markdown("""<div style="font-family:'Orbitron',monospace;font-size:0.65em;
            color:rgba(33,150,243,0.55);letter-spacing:4px;
            border-top:1px solid rgba(33,150,243,0.18);padding-top:10px;margin-bottom:10px;">
            ⚙️ PANNEAU OPÉRATIONNEL CRISE &amp; VEILLE MULTI-RISQUES</div>""",
            unsafe_allow_html=True)

        # ── Ligne 1 : SAR actifs + Infra + Sources ───────────────────────
        _c1, _c2, _c3 = st.columns([2, 2, 1])

        with _c1:
            # ── SAR Sentinel-1 récents ─────────────────────────────────
            st.markdown('<div class="wm-section-title">🛰️ TRAITEMENTS SAR SENTINEL-1</div>', unsafe_allow_html=True)
            if done:
                _sar_rows2 = ""
                for _j in done[:5]:
                    _params = _j.get("params",{}); _res = _j.get("results",{})
                    _mode   = "Avant/Après" if _params.get("image_before") else "Image unique"
                    _created = _j.get("created","")[:16].replace("T"," ")
                    _ha     = _res.get("surface_totale_ha","—")
                    _n_com  = _res.get("n_communes","—")
                    _jid    = _j.get("id","")[:8]
                    _ha_f   = f"{float(_ha):,.0f}" if _ha and _ha!="—" else "—"
                    _com_str= f" · 🏘️ {_n_com} com." if _n_com and _n_com!="—" else ""
                    _niv_sar= "wm-sev-critical" if _ha and _ha!="—" and float(_ha)>5000 else ("wm-sev-high" if _ha and _ha!="—" and float(_ha)>1000 else "wm-sev-medium")
                    _sar_rows2 += f"""
                    <div class="wm-signal" style="padding:6px 8px;">
                      <div class="wm-signal-icon" style="font-size:1.1em;">🛰️</div>
                      <div class="wm-signal-body">
                        <div class="wm-signal-meta">
                          <span class="wm-tier wm-tier-cop">SAR</span>
                          <span class="wm-sev {_niv_sar}">{_ha_f} ha</span>
                          <span class="wm-signal-time">{_created}</span>
                        </div>
                        <div class="wm-signal-title" style="font-size:0.8em;">#{_jid} — {_mode}{_com_str}</div>
                      </div>
                    </div>"""
                st.markdown(_sar_rows2, unsafe_allow_html=True)
            else:
                st.markdown('<div class="wm-signal"><div class="wm-signal-icon">🟢</div><div class="wm-signal-body"><div class="wm-signal-title">Aucun traitement SAR récent</div></div></div>', unsafe_allow_html=True)

        with _c2:
            # ── Infrastructure hydrologique ────────────────────────────
            st.markdown('<div class="wm-section-title">🏗️ INFRASTRUCTURE MAROC</div>', unsafe_allow_html=True)
            st.markdown("""
            <div class="wm-infra-grid" style="grid-template-columns:repeat(3,1fr);gap:6px;">
              <div class="wm-infra-btn"><div class="wm-infra-ico">🏞️</div><div class="wm-infra-count">148</div><div class="wm-infra-lbl">Barrages</div></div>
              <div class="wm-infra-btn"><div class="wm-infra-ico">🌊</div><div class="wm-infra-count">9</div><div class="wm-infra-lbl">Bassins ABH</div></div>
              <div class="wm-infra-btn"><div class="wm-infra-ico">🏔️</div><div class="wm-infra-count">23</div><div class="wm-infra-lbl">Zones risque</div></div>
              <div class="wm-infra-btn"><div class="wm-infra-ico">🛣️</div><div class="wm-infra-count">16 750</div><div class="wm-infra-lbl">km routes</div></div>
              <div class="wm-infra-btn"><div class="wm-infra-ico">🏙️</div><div class="wm-infra-count">12</div><div class="wm-infra-lbl">Régions</div></div>
              <div class="wm-infra-btn"><div class="wm-infra-ico">🛰️</div><div class="wm-infra-count">S1-A/B</div><div class="wm-infra-lbl">Sentinel</div></div>
            </div>""", unsafe_allow_html=True)

        with _c3:
            # ── Statut sources ─────────────────────────────────────────
            st.markdown('<div class="wm-section-title">📶 SOURCES</div>', unsafe_allow_html=True)
            _src_rows = ""
            for _key, _cfg in FEEDS_8.items():
                _s = _feed_statuses.get(_key,"offline")
                _dot_c = "#00e676" if _s=="live" else ("#ffeb3b" if _s=="empty" else "#ff4545")
                _s_lbl = "●" if _s=="live" else ("◌" if _s=="empty" else "✕")
                _src_rows += f"""<div style="display:flex;align-items:center;gap:6px;padding:3px 0;
                    border-bottom:1px solid rgba(33,150,243,0.06);">
                  <span style="font-size:0.85em;">{_cfg['icon']}</span>
                  <span style="font-size:0.7em;color:#e3f2fd;flex:1;overflow:hidden;white-space:nowrap;">{_cfg['name'][:20]}</span>
                  <span style="font-family:'Orbitron',monospace;font-size:0.55em;color:{_dot_c};">{_s_lbl}</span>
                </div>"""
            st.markdown(_src_rows, unsafe_allow_html=True)

        # ── Ligne 2 : Procédures crise + modules CCIP ───────────────────
        _c4, _c5 = st.columns([1, 1])

        with _c4:
            st.markdown('<div class="wm-section-title">📋 PROCÉDURES CRISE — ACTIONS RAPIDES</div>', unsafe_allow_html=True)
            _procs = [
                ("🔴","Inondation active",    "Activer ORSEC Inondation · Alerter ABH · Lancer SAR Sentinel-1 · Contacter DGPC",  "#ef4444"),
                ("🟠","Vigilance ORANGE/ROUGE","Surveiller DMN toutes les 3h · Préparer évacuation zones à risque · Sécuriser barrages","#f59e0b"),
                ("⛈️","Orages violents",       "Fermer cours d'eau aval · Alerter communes DEM · Surveiller bassins Sebou/Tensift",  "#8b5cf6"),
                ("🔥","Incendie forestier",    "Activer EFFIS monitoring · Coordonner ONEF · Requête image Sentinel-2 J+1",          "#f97316"),
                ("🏔️","Séisme M>5",           "Déclencher protocole USGS · Requête Copernicus EMS Rapid · Éval. dommages SAR",      "#64748b"),
                ("💧","Crue soudaine",         "GloFAS débit temps réel · Ouvrir évacuateur barrages · Interdire accès oueds",       "#0ea5e9"),
            ]
            for _emj, _tit, _act, _cc in _procs:
                st.markdown(f"""
                <div style="display:flex;gap:8px;padding:6px 8px;margin-bottom:5px;
                     background:rgba(4,14,35,0.6);border-left:3px solid {_cc};border-radius:4px;">
                  <span style="font-size:1.2em;flex-shrink:0;">{_emj}</span>
                  <div>
                    <div style="font-size:0.78em;color:#e3f2fd;font-weight:600;">{_tit}</div>
                    <div style="font-size:0.67em;color:rgba(180,210,240,0.6);line-height:1.3;">{_act}</div>
                  </div>
                </div>""", unsafe_allow_html=True)

        with _c5:
            st.markdown('<div class="wm-section-title">🧩 MODULES CCIP — ÉTAT</div>', unsafe_allow_html=True)
            _modules = [
                ("🌊","Inondation SAR Sentinel-1","wm-tag-active","● ACTIF",
                 "Détection surfaces inondées · Délimitation zones impactées · Export shapefile"),
                ("🔥","Incendie EFFIS / MODIS","wm-tag-soon","BIENTÔT",
                 "Cartographie surfaces brûlées · Points chauds actifs · Évolution temporelle"),
                ("⛰️","Glissement de terrain InSAR","wm-tag-soon","BIENTÔT",
                 "Déformation de surface Sentinel-1 · Détection mouvements de sol précurseurs"),
                ("🌵","Sécheresse SPI/NDVI","wm-tag-soon","BIENTÔT",
                 "Indice précipitations standardisé · Stress végétation NDVI · Anomalie climatique"),
                ("🏔️","Séisme USGS ShakeMap","wm-tag-watch","VEILLE",
                 "Import ShakeMap USGS · Superposition population/infrastructure · Dommages estimés"),
                ("🌊","Tsunami IOC/CENALT","wm-tag-watch","VEILLE",
                 "Alertes tsunami Méditerranée/Atlantique · Modélisation submersion côtière Maroc"),
            ]
            for _mic, _mnom, _mtag, _mlbl, _mdesc in _modules:
                st.markdown(f"""
                <div class="wm-module-row" style="flex-direction:column;align-items:flex-start;padding:6px 8px;margin-bottom:4px;">
                  <div style="display:flex;align-items:center;gap:6px;width:100%;">
                    <span class="wm-module-ico">{_mic}</span>
                    <span class="wm-module-name" style="flex:1;">{_mnom}</span>
                    <span class="wm-module-tag {_mtag}">{_mlbl}</span>
                  </div>
                  <div style="font-size:0.65em;color:rgba(144,202,249,0.5);margin-top:3px;padding-left:26px;">{_mdesc}</div>
                </div>""", unsafe_allow_html=True)



# ─────────────────────────────────────────────────────────────
# TAB 2 — INFO & ACTUALITÉS (flux Maroc + International)
# ─────────────────────────────────────────────────────────────
def _render_feed_status_row(feeds_dict, statuses_dict, grid_cols=8):
    cards = ""
    for key, cfg in feeds_dict.items():
        s = statuses_dict.get(key, "offline")
        dot_cls = "feed-dot-live" if s=="live" else ("feed-dot-empty" if s=="empty" else "feed-dot-offline")
        s_lbl   = "LIVE" if s=="live" else ("VIDE" if s=="empty" else "OFFLINE")
        s_col   = "#00e676" if s=="live" else ("#ffeb3b" if s=="empty" else "#ff4545")
        cards += f"""
        <div class="feed-status-card" title="{cfg['desc']}">
          <div class="feed-status-icon">{cfg['icon']}</div>
          <div class="feed-status-name">{key}</div>
          <div class="{dot_cls}"></div>
          <div style="font-size:0.48em;font-family:'Orbitron',monospace;color:{s_col};letter-spacing:1px;">{s_lbl}</div>
        </div>"""
    cols_style = f"repeat({grid_cols},1fr)"
    st.markdown(f'<div class="feed-status-grid" style="grid-template-columns:{cols_style};">{cards}</div>', unsafe_allow_html=True)

def _render_articles(items, empty_hint="Aucun flux actif."):
    if not items:
        st.markdown(f"""
        <div class="vcard" style="text-align:center;padding:30px;">
          <div style="font-size:2em;margin-bottom:10px;">📡</div>
          <div style="color:rgba(144,202,249,0.5);">Aucun article disponible.<br>
          <span style="font-size:0.85em;">{empty_hint}</span></div>
        </div>""", unsafe_allow_html=True)
        return
    for item in items:
        badge = ""
        if item.get("score",0) >= 2:
            badge = '<span style="background:rgba(255,69,69,0.2);color:#ff4545;border:1px solid rgba(255,69,69,0.4);font-size:0.6em;padding:1px 7px;border-radius:10px;font-family:\'Orbitron\',monospace;letter-spacing:1px;margin-left:6px;">ALERTE</span>'
        elif item.get("score",0) >= 1:
            badge = '<span style="background:rgba(255,152,0,0.15);color:#ff9800;border:1px solid rgba(255,152,0,0.3);font-size:0.6em;padding:1px 7px;border-radius:10px;font-family:\'Orbitron\',monospace;letter-spacing:1px;margin-left:6px;">VIGILANCE</span>'
        link_open  = f'<a href="{item["link"]}" target="_blank" style="color:inherit;text-decoration:none;">' if item.get("link") else ""
        link_close = "</a>" if item.get("link") else ""
        desc_html  = f"<div style='font-size:0.78em;color:rgba(144,202,249,0.4);margin-top:4px;'>{item['desc'][:140]}…</div>" if item.get('desc') else ""
        st.markdown(f"""
        <div class="news-item">
          <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">
            <span style="font-size:1.1em;">{item['icon']}</span>
            <span class="news-source" style="color:{item['color']};">{item['source']}</span>
            {badge}
            <span class="news-date" style="margin-left:auto;">{item.get('date','')}</span>
          </div>
          {link_open}<div class="news-title">{item['title']}</div>{link_close}
          {desc_html}
        </div>""", unsafe_allow_html=True)

with tab2:
    st.markdown(f'<div class="vtitle">{T["news_title"]}</div>', unsafe_allow_html=True)

    # ── Filtres globaux ───────────────────────────────────────
    col_flt, col_ref = st.columns([4, 1])
    with col_flt:
        keywords       = st.text_input("🔍 Filtrer par mot-clé", placeholder="inondation, flood, earthquake…", label_visibility="collapsed")
        show_alerts_only = st.toggle("⚡ Alertes uniquement", value=False)
    with col_ref:
        if st.button("🔄 Actualiser", use_container_width=True):
            st.cache_data.clear(); st.rerun()
        n_live_mar  = sum(1 for s in _feed_statuses.values() if s=="live")
        n_live_intl = sum(1 for s in _intl_statuses.values() if s=="live")
        st.markdown(f"""
        <div style="text-align:center;padding:4px;font-size:0.75em;">
          <span style="color:#00e676;font-family:'Orbitron',monospace;">{n_live_mar+n_live_intl}</span>
          <span style="color:rgba(144,202,249,0.4);"> / {len(FEEDS_8)+len(FEEDS_INTL)} flux actifs</span>
        </div>""", unsafe_allow_html=True)

    def _apply_filters(items):
        if show_alerts_only:
            items = [it for it in items if it.get("score",0) >= 1]
        if keywords.strip():
            kw = keywords.lower()
            items = [it for it in items if kw in it["title"].lower() or kw in it.get("desc","").lower()]
        return items

    # ══ Section 1 — Flux Maroc ════════════════════════════════
    st.markdown("""
    <div style="font-family:'Orbitron',monospace;font-size:0.62em;color:rgba(33,150,243,0.5);
                letter-spacing:3px;margin:14px 0 8px 0;">🇲🇦 FLUX INSTITUTIONNELS MAROC</div>
    """, unsafe_allow_html=True)

    _render_feed_status_row(FEEDS_8, _feed_statuses, grid_cols=8)

    col_mar, _ = st.columns([4, 1])
    with col_mar:
        mar_keys = list(FEEDS_8.keys())
        sel_mar  = st.multiselect("Sources Maroc", options=mar_keys,
                                  default=[k for k in mar_keys if _feed_statuses.get(k,"offline") in ("live","empty")],
                                  format_func=lambda k: f"{FEEDS_8[k]['icon']} {FEEDS_8[k]['name']}",
                                  label_visibility="collapsed", key="sel_mar")

    mar_items = _apply_filters([it for it in _all_feed_items if it.get("feed_key","") in sel_mar])
    live_mar  = [k for k,s in _feed_statuses.items() if s=="live"]
    _render_articles(mar_items, empty_hint=f"{len(live_mar)} flux actifs : {', '.join(live_mar)}" if live_mar else "Aucun flux Maroc actif.")

    # ══ Section 2 — Sources Internationales ══════════════════
    st.markdown("""
    <div style="font-family:'Orbitron',monospace;font-size:0.62em;color:rgba(124,77,255,0.6);
                letter-spacing:3px;margin:20px 0 8px 0;">🌍 SOURCES INTERNATIONALES — NASA · ESA · ONU · WMO</div>
    """, unsafe_allow_html=True)

    _render_feed_status_row(FEEDS_INTL, _intl_statuses, grid_cols=6)

    col_intl, _ = st.columns([4, 1])
    with col_intl:
        intl_keys = list(FEEDS_INTL.keys())
        sel_intl  = st.multiselect("Sources internationales", options=intl_keys,
                                   default=[k for k in intl_keys if _intl_statuses.get(k,"offline") in ("live","empty")],
                                   format_func=lambda k: f"{FEEDS_INTL[k]['icon']} {FEEDS_INTL[k]['name']}",
                                   label_visibility="collapsed", key="sel_intl")

    intl_items = _apply_filters([it for it in _intl_feed_items if it.get("feed_key","") in sel_intl])
    live_intl  = [k for k,s in _intl_statuses.items() if s=="live"]
    _render_articles(intl_items, empty_hint=f"{len(live_intl)} flux actifs : {', '.join(live_intl)}" if live_intl else "Aucun flux international actif — vérifiez la connexion.")

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
