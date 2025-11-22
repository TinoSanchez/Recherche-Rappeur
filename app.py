import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import wikipedia
from datetime import datetime
import lyricsgenius 
import time
import urllib.parse 
import json
import hashlib
import os
import requests # NOUVEAU : Pour récupérer les auditeurs mensuels
import re # NOUVEAU : Pour chercher le chiffre dans le texte
import streamlit.components.v1 as components 

# --- 1. CONFIGURATION GLOBALE ---
st.set_page_config(
    page_title="RAP DATA | ULTIMATE",
    page_icon="⚡",
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# --- 2. CSS DU FUTUR (DESIGN SPECTACULAIRE) ---
st.markdown("""
<style>
    /* --- IMPORTS --- */
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;500;900&family=Outfit:wght@300;700&display=swap');

    /* --- BACKGROUND ANIMÉ --- */
    .stApp {
        background: radial-gradient(circle at top left, #1a0b2e, #000000);
        background-image: 
            radial-gradient(at 0% 0%, hsla(253,16%,7%,1) 0, transparent 50%), 
            radial-gradient(at 50% 0%, hsla(225,39%,30%,1) 0, transparent 50%), 
            radial-gradient(at 100% 0%, hsla(339,49%,30%,1) 0, transparent 50%);
        color: white;
        font-family: 'Outfit', sans-serif;
    }
    
    /* --- TITRES --- */
    h1 {
        font-family: 'Montserrat', sans-serif;
        font-weight: 900 !important;
        text-transform: uppercase;
        letter-spacing: -2px;
        background: linear-gradient(to right, #1DB954, #00d2ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0 0 30px rgba(29, 185, 84, 0.3);
    }
    
    h2, h3 {
        font-family: 'Montserrat', sans-serif;
        font-weight: 700 !important;
        letter-spacing: -1px;
    }

    /* --- GLASSMORPHISM CARDS --- */
    .glass-panel {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border-radius: 24px;
        padding: 30px;
        box-shadow: 0 20px 50px rgba(0,0,0,0.5);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    .glass-panel:hover {
        transform: translateY(-5px);
        box-shadow: 0 30px 60px rgba(29, 185, 84, 0.15);
        border-color: rgba(29, 185, 84, 0.3);
    }

    /* --- INPUT RECHERCHE FUTURISTE --- */
    div[data-testid="stTextInput"] input {
        background-color: rgba(0,0,0,0.6) !important;
        color: white !important;
        border: 2px solid rgba(255,255,255,0.1) !important;
        border-radius: 50px !important;
        padding: 20px 30px !important;
        font-size: 1.2rem !important;
        transition: all 0.3s ease;
    }
    div[data-testid="stTextInput"] input:focus {
        border-color: #1DB954 !important;
        box-shadow: 0 0 30px rgba(29, 185, 84, 0.4);
        background-color: black !important;
    }

    /* --- BOUTONS NÉONS --- */
    div.stButton > button {
        background: linear-gradient(45deg, #1DB954, #00f260);
        color: black;
        border-radius: 50px;
        border: none;
        padding: 15px 40px;
        font-weight: 900;
        text-transform: uppercase;
        letter-spacing: 2px;
        box-shadow: 0 10px 30px rgba(29, 185, 84, 0.4);
        transition: all 0.3s ease;
        width: 100%;
    }
    div.stButton > button:hover {
        transform: scale(1.05);
        box-shadow: 0 15px 40px rgba(29, 185, 84, 0.6);
    }

    /* --- VINYLE 3D ANIMÉ --- */
    .vinyl-wrapper {
        position: relative;
        width: 300px;
        height: 300px;
        margin: auto;
        border-radius: 50%;
        background: #111;
        box-shadow: 0 20px 50px rgba(0,0,0,0.8);
        animation: spin 20s linear infinite;
        border: 2px solid #222;
    }
    .vinyl-art {
        width: 100%;
        height: 100%;
        border-radius: 50%;
        object-fit: cover;
        opacity: 1;
    }
    @keyframes spin { 100% { transform: rotate(360deg); } }

    /* --- TRACKLIST STYLISÉE --- */
    .track-item {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 15px;
        margin-bottom: 8px;
        background: rgba(255,255,255,0.02);
        border-radius: 12px;
        border-left: 3px solid transparent;
        transition: all 0.2s;
    }
    .track-item:hover {
        background: rgba(255,255,255,0.08);
        border-left: 3px solid #1DB954;
        padding-left: 20px;
    }
    
    /* --- LIENS BOUTONS (LOGOS) --- */
    a.custom-link {
        text-decoration: none;
        font-weight: 700;
        font-size: 0.9rem;
        padding: 10px 0;
        border-radius: 15px;
        transition: 0.3s;
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 10px;
        height: 50px;
        width: 100%;
    }
    .link-spotify { background: rgba(29, 185, 84, 0.15); border: 2px solid #1DB954; color: #1DB954 !important; }
    .link-spotify:hover { background: #1DB954; box-shadow: 0 0 20px #1DB954; color: black !important; }
    
    .link-genius { background: rgba(255, 255, 100, 0.15); border: 2px solid #FFFF64; color: #FFFF64 !important; }
    .link-genius:hover { background: #FFFF64; box-shadow: 0 0 20px #FFFF64; color: black !important; }

    .link-fnac { background: rgba(225, 168, 45, 0.15); border: 2px solid #E1A82D; color: #E1A82D !important; }
    .link-fnac:hover { background: #E1A82D; box-shadow: 0 0 20px #E1A82D; color: black !important; }

    .link-snep { background: rgba(255, 215, 0, 0.15); border: 2px solid #FFD700; color: #FFD700 !important; }
    .link-snep:hover { background: #FFD700; box-shadow: 0 0 20px #FFD700; color: black !important; }

    /* Petits boutons liste */
    a.mini-btn {
        text-decoration: none; font-size: 0.7rem; padding: 3px 8px;
        border-radius: 4px; margin-left: 5px; transition: 0.2s; font-weight: bold;
        border: 1px solid rgba(255,255,255,0.2);
    }
    a.btn-lyrics { background: #FFFF64; color: black !important; }
    a.btn-play { background: #1DB954; color: white !important; }
    a.mini-btn:hover { transform: scale(1.1); }

    /* --- SIDEBAR --- */
    section[data-testid="stSidebar"] {
        background-color: #050505;
        border-right: 1px solid #222;
    }
    
    /* HIDE DEFAULTS */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# CONFIGURATION & AUTHENTIFICATION
# ==============================================================================
USER_DB_FILE = "users_db.json"
SPOTIPY_CLIENT_ID = '797ca964aaeb4a93afd012b639e79d03'
SPOTIPY_CLIENT_SECRET = '4d8484cc53cc43aeb32610151a36594f'
GENIUS_ACCESS_TOKEN = 'VOTRE_TOKEN_GENIUS_ICI' 

def hash_password(password): return hashlib.sha256(password.encode()).hexdigest()

def load_users():
    if not os.path.exists(USER_DB_FILE):
        default_users = {"admin": hash_password("rapfr")}
        save_users(default_users)
        return default_users
    try: 
        with open(USER_DB_FILE, "r") as f: return json.load(f)
    except: return {}

def save_users(users):
    with open(USER_DB_FILE, "w") as f: json.dump(users, f)

if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'current_user' not in st.session_state: st.session_state.current_user = ""
if 'history' not in st.session_state: st.session_state.history = []
if 'search_result' not in st.session_state: st.session_state.search_result = None

# --- PAGE DE CONNEXION ---
def login_page():
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.5, 1])
    with c2:
        st.markdown("""
        <div class="glass-panel" style="text-align:center;">
            <h1 style="font-size: 4rem; margin-bottom:0;">ACCESS</h1>
            <p style="color: #888; letter-spacing: 3px; margin-bottom: 30px;">SECURE RAP DATABASE</p>
        </div>
        <br>
        """, unsafe_allow_html=True)
        
        tab_login, tab_signup = st.tabs(["LOGIN", "REGISTER"])
        users = load_users()
        
        with tab_login:
            u = st.text_input("IDENTIFIANT", key="log_u")
            p = st.text_input("MOT DE PASSE", type="password", key="log_p")
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("INITIALISER LE SYSTÈME", use_container_width=True):
                if u in users and users[u] == hash_password(p):
                    st.session_state.logged_in = True
                    st.session_state.current_user = u
                    st.rerun()
                else: st.error("ACCÈS REFUSÉ")
                
        with tab_signup:
            nu = st.text_input("NOUVEL ID", key="sign_u")
            np = st.text_input("NOUVEAU MDP", type="password", key="sign_p")
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("CRÉER L'ACCÈS", use_container_width=True):
                if nu in users: st.error("ID DÉJÀ PRIS")
                elif len(np) < 4: st.error("TROP COURT")
                else:
                    users[nu] = hash_password(np)
                    save_users(users)
                    st.success("ACCÈS CRÉÉ")
        
        st.markdown("<br><hr style='border-color:rgba(255,255,255,0.1);'><br>", unsafe_allow_html=True)
        if st.button("👀 ACCÈS VISITEUR (SANS COMPTE)", use_container_width=True):
            st.session_state.logged_in = True
            st.session_state.current_user = "Visiteur"
            st.rerun()

def logout():
    st.session_state.logged_in = False; st.session_state.current_user = ""; st.rerun()

if not st.session_state.logged_in: login_page(); st.stop()

# ==============================================================================
# LOGIQUE APP
# ==============================================================================
@st.cache_resource 
def init_apis():
    auth_manager = SpotifyClientCredentials(client_id=SPOTIPY_CLIENT_ID, client_secret=SPOTIPY_CLIENT_SECRET)
    sp = spotipy.Spotify(auth_manager=auth_manager)
    wikipedia.set_lang("fr")
    genius = lyricsgenius.Genius(GENIUS_ACCESS_TOKEN, verbose=False)
    return sp, genius

sp, genius = init_apis()

def safe_get(dct, path, default=""):
    try:
        for p in path.split("/"):
            if p.isdigit(): dct = dct[int(p)]
            else: dct = dct[p]
        return dct
    except: return default

# --- FONCTION POUR SCRAPER LES AUDITEURS MENSUELS ---
def scrape_monthly_listeners(artist_url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(artist_url, headers=headers)
        if response.status_code == 200:
            # On cherche le pattern "X monthly listeners" dans le code source
            # Ex: "Artist · 8.3M monthly listeners"
            match = re.search(r'Artist\s·\s([\d\.,]+[MK]?)\smonthly\slisteners', response.text)
            if match:
                return match.group(1)
    except:
        return "N/A"
    return "N/A"

@st.cache_data(show_spinner=False)
def get_artist_data(nom):
    try:
        results = sp.search(q=f'artist:{nom}', type='artist', limit=10)
        items = results['artists']['items']
    except Exception as e: return None, None, f"Erreur API : {e}"

    if not items: return None, None, "Artiste introuvable."

    valid_items = []
    keywords = ['french', 'francais', 'belge', 'suisse', 'rap', 'hip hop', 'urbaine', 'drill']
    for item in items:
        g = " ".join([x.lower() for x in item.get('genres', [])])
        if any(k in g for k in keywords): valid_items.append(item)
    
    if not valid_items: return None, None, "Cet artiste ne correspond pas aux critères Rap FR."
    
    valid_items.sort(key=lambda x: x.get('popularity', 0), reverse=True)
    artist = valid_items[0]
    
    formatted_name = urllib.parse.quote(artist['name'].replace(" ", "-").capitalize())
    
    data = {
        "name": artist['name'],
        "id": artist['id'],
        "img_url": safe_get(artist, "images/0/url", ""),
        "followers": artist.get('followers', {}).get('total', 0),
        "popularity": artist.get('popularity', 0),
        "genres": artist.get('genres', []),
        "spotify_url": safe_get(artist, "external_urls/spotify", "#"),
        "bio": "Bio indisponible.",
        "genius_url": f"https://genius.com/artists/{formatted_name}",
        "monthly_listeners": "N/A" # Placeholder
    }

    # SCRAPING AUDITEURS MENSUELS
    data["monthly_listeners"] = scrape_monthly_listeners(data["spotify_url"])

    try:
        wiki_res = wikipedia.search(data["name"], results=1)
        if wiki_res:
            page = wikipedia.page(wiki_res[0], auto_suggest=False)
            data["bio"] = page.summary[:800] + "..."
    except: pass

    try:
        albums = sp.artist_albums(data["id"], album_type='album', country='FR', limit=50)['items']
    except: albums = []
    
    unique_albums = {}
    for a in albums:
        if a['name'] not in unique_albums: unique_albums[a['name']] = a
    
    data["albums"] = sorted(unique_albums.values(), key=lambda x: x['release_date'], reverse=True)
    return data, artist['name'], None

def do_search():
    if st.session_state.rappeur_input_key:
        with st.spinner("Loading Data..."):
            data, name, err = get_artist_data(st.session_state.rappeur_input_key)
            st.session_state.search_result = {'data': data, 'error': err}
            if not err:
                if not st.session_state.history or st.session_state.history[-1] != name:
                    st.session_state.history.append(name)

def recall(name):
    st.session_state.rappeur_input_key = name
    do_search()

# ==============================================================================
# INTERFACE PRINCIPALE
# ==============================================================================

# SIDEBAR
with st.sidebar:
    st.markdown(f"<h3 style='text-align:center;'>👤 {st.session_state.current_user.upper()}</h3>", unsafe_allow_html=True)
    st.button("LOGOUT", on_click=logout, use_container_width=True)
    st.markdown("---")
    st.markdown("### RECENT DIGS")
    for h in reversed(st.session_state.history[-5:]):
        st.button(f"💿 {h}", key=f"h_{h}", on_click=recall, args=[h], use_container_width=True)

# HEADER
st.markdown("""
<div style="text-align:center; margin-bottom: 50px;">
    <h1 style="font-size: 5rem; margin-bottom: 0; line-height: 1;">RAP DATA</h1>
    <p style="font-size: 1.2rem; color: #00d2ff; letter-spacing: 5px; text-transform: uppercase;">Ultimate Database</p>
</div>
""", unsafe_allow_html=True)

# SEARCH BAR
col1, col2 = st.columns([4, 1])
with col1:
    st.text_input("SEARCH ARTIST", key="rappeur_input_key", on_change=do_search, placeholder="Ex: Booba, Gazo...")
with col2:
    st.button("GO", on_click=do_search, use_container_width=True)

# RESULTATS
if st.session_state.search_result:
    res = st.session_state.search_result
    if res['error']:
        st.error(res['error'])
    else:
        d = res['data']
        
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        # --- HERO SECTION ---
        c_img, c_info = st.columns([1, 2], gap="large")
        
        with c_img:
            st.markdown(f"""
            <div class="vinyl-wrapper">
                <img src="{d['img_url']}" class="vinyl-art">
            </div>
            """, unsafe_allow_html=True)
            
        with c_info:
            st.markdown(f"""
            <div class="glass-panel">
                <h1 style="font-size: 4rem; margin:0; background: linear-gradient(to right, #fff, #888); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">{d['name']}</h1>
                <p style="color: #1DB954; font-weight: bold; letter-spacing: 2px; text-transform: uppercase; margin-top:-10px;">
                    {", ".join(d['genres'][:3])}
                </p>
                <div style="display:flex; gap:20px; margin-top:20px;">
                    <div>
                        <h3 style="margin:0; color:#fff;">{d['popularity']}</h3>
                        <p style="color:#666; font-size:0.8rem;">POPULARITÉ</p>
                    </div>
                    <div style="border-left:1px solid #333; padding-left:20px;">
                        <h3 style="margin:0; color:#fff;">{d['followers']:,}</h3>
                        <p style="color:#666; font-size:0.8rem;">ABONNÉS</p>
                    </div>
                    <div style="border-left:1px solid #333; padding-left:20px;">
                        <h3 style="margin:0; color:#fff;">{d['monthly_listeners']}</h3>
                        <p style="color:#666; font-size:0.8rem;">AUDITEURS/MOIS</p>
                    </div>
                    <div style="border-left:1px solid #333; padding-left:20px;">
                        <h3 style="margin:0; color:#fff;">{len(d['albums'])}</h3>
                        <p style="color:#666; font-size:0.8rem;">ALBUMS</p>
                    </div>
                </div>
                <br>
                <p style="color: #ccc; line-height: 1.6; font-size: 0.95rem;">{d['bio']}</p>
                <br>
                <div style="display:flex; gap:10px; flex-wrap:wrap;">
                    <a href="{d['spotify_url']}" target="_blank" class="custom-link link-spotify">
                        <img src="https://upload.wikimedia.org/wikipedia/commons/1/19/Spotify_logo_without_text.svg" width="24"> Spotify
                    </a>
                    <a href="{d['genius_url']}" target="_blank" class="custom-link link-genius">
                        🟡 Genius
                    </a>
                    <a href="https://www.fnacspectacles.com/artist/{d['name'].replace(' ', '-').lower()}" target="_blank" class="custom-link link-fnac">
                        <img src="https://upload.wikimedia.org/wikipedia/commons/2/2e/Fnac_Logo.svg" width="24"> Fnac
                    </a>
                    <a href="https://snepmusique.com/les-certifications/?interprete={d['name'].replace(' ', '+')}" target="_blank" class="custom-link link-snep">
                        📀 Disques
                    </a>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("<h2>DISCOGRAPHIE</h2>", unsafe_allow_html=True)
        
        if not d['albums']:
            st.warning("Aucun album trouvé.")
        else:
            for album in d['albums']:
                with st.expander(f"{album['name']} ({album['release_date'][:4]})"):
                    c_alb_img, c_alb_tracks = st.columns([1, 3])
                    
                    with c_alb_img:
                        if len(album['images']) > 0:
                            st.image(album['images'][0]['url'], use_container_width=True)
                            st.caption("Cover Art")
                    
                    with c_alb_tracks:
                        components.iframe(f"https://open.spotify.com/embed/album/{album['id']}?theme=0", height=80)
                        st.markdown("<br>", unsafe_allow_html=True)
                        try:
                            tracks = sp.album_tracks(album["id"])["items"]
                            for t in tracks:
                                if t['name']:
                                    q = urllib.parse.quote(f"{t['name']} {d['name']}")
                                    gl = f"https://genius.com/search?q={q}"
                                    tl = safe_get(t, 'external_urls/spotify', '#')
                                    
                                    # LISTE DES TITRES PROPRE ET TRONQUÉE
                                    st.markdown(f"""
                                    <div class="track-row">
                                        <div class="track-info">
                                            <span class="track-number">{t['track_number']}.</span>
                                            <span class="track-title" title="{t['name']}">{t['name']}</span>
                                        </div>
                                        <div style="display:flex;">
                                            <a href="{gl}" target="_blank" class="mini-btn btn-lyrics">Paroles</a>
                                            <a href="{tl}" target="_blank" class="mini-btn btn-play">▶</a>
                                        </div>
                                    </div>
                                    """, unsafe_allow_html=True)
                        except: st.error("Info titres indisponible")

def generate_text_content(data):
    content = f"RAP DATA : {data['name'].upper()}\n{'='*30}\n"
    content += f"Popularité: {data['popularity']}/100 | Followers: {data['followers']:,}\n\nBIO:\n{data['bio']}\n\nDISCOGRAPHIE:\n"
    for album in data["albums"]:
        content += f"\n[{album['release_date']}] {album['name']}\n"
        try:
            tracks = sp.album_tracks(album["id"])["items"]
            for t in tracks:
                q = urllib.parse.quote(f"{t['name']} {data['name']}")
                content += f" - {t['name']} (https://genius.com/search?q={q})\n"
        except: continue
    return content

st.markdown("<br><br><br><center style='color:#333; font-size:0.8rem; letter-spacing:2px;'>DESIGNED BY FEVRIE, BETASTAR & RAITRO</center>", unsafe_allow_html=True)