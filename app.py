import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import wikipedia
from datetime import datetime
import lyricsgenius 
import time
import urllib.parse 

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="Rap Data | Fiches Artistes",
    page_icon="🔥",
    layout="wide", 
    initial_sidebar_state="expanded"
)

# --- STYLES CSS ---
st.markdown("""
<style>
    .stApp { background-color: #0E0E0E; color: white; }
    h1 { color: #1DB954 !important; font-weight: 800 !important; }
    div[data-testid="stMetricValue"] { color: #1DB954 !important; font-size: 2rem !important; }
    div.stButton > button:first-child {
        background-color: #1DB954; color: white; border-radius: 20px; border: none;
        padding: 10px 24px; font-weight: bold; transition: all 0.3s ease;
    }
    div.stButton > button:first-child:hover { background-color: #1ed760; transform: scale(1.05); }
    section[data-testid="stSidebar"] { background-color: #121212; }
    a.genius-link {
        color: #FFFF64 !important; text-decoration: none; font-size: 0.8em;
        border: 1px solid #FFFF64; padding: 2px 6px; border-radius: 4px;
    }
    a.genius-link:hover { background-color: #FFFF64; color: black !important; }
    .not-found { color: #ff4b4b; font-size: 0.8em; font-style: italic; }
</style>
""", unsafe_allow_html=True)

# --- GESTION DE L'ÉTAT ---
if 'history' not in st.session_state: st.session_state.history = []
if 'search_result' not in st.session_state: st.session_state.search_result = None

# --- CLÉS API (⚠️ TES CLÉS ICI) ---
SPOTIPY_CLIENT_ID = '797ca964aaeb4a93afd012b639e79d03'
SPOTIPY_CLIENT_SECRET = '4d8484cc53cc43aeb32610151a36594f'
GENIUS_ACCESS_TOKEN = 'VOTRE_TOKEN_GENIUS_ICI' 

# --- INITIALISATION ---
@st.cache_resource 
def init_apis():
    auth_manager = SpotifyClientCredentials(client_id=SPOTIPY_CLIENT_ID, client_secret=SPOTIPY_CLIENT_SECRET)
    sp = spotipy.Spotify(auth_manager=auth_manager)
    wikipedia.set_lang("fr")
    genius = lyricsgenius.Genius(GENIUS_ACCESS_TOKEN, verbose=False)
    return sp, genius

sp, genius = init_apis()

# --- UTILITAIRES ---
def safe_get(dct, path, default=""):
    try:
        for p in path.split("/"):
            if p.isdigit(): dct = dct[int(p)]
            else: dct = dct[p]
        return dct
    except: return default

# --- RÉCUPÉRATION DES DONNÉES ---
@st.cache_data(show_spinner=False)
def get_artist_data(nom_rappeur_saisi):
    # 1. Recherche Spotify
    try:
        results = sp.search(q=f'artist:{nom_rappeur_saisi}', type='artist', limit=10)
        items = results['artists']['items']
    except Exception as e:
        return None, None, f"Erreur Spotify : {e}"

    if not items:
        return None, None, "Artiste non trouvé."

    # --- FILTRAGE STRICT ---
    valid_items = []
    geo_keywords = ['french', 'francais', 'français', 'francoton', 'belge', 'belgian', 'suisse', 'swiss']
    style_keywords = ['rap', 'hip hop', 'trap', 'drill', 'urbaine', 'urban', 'r&b', 'cloud']

    for item in items:
        genres_str = " ".join([g.lower() for g in item.get('genres', [])])
        has_geo = any(k in genres_str for k in geo_keywords)
        has_style = any(k in genres_str for k in style_keywords)
        if has_geo and has_style:
            valid_items.append(item)
    
    if not valid_items:
        return None, None, f"🚫 Artiste trouvé, mais identifié comme non-Français ou non-Rap."

    # Sélection
    valid_items.sort(key=lambda x: x.get('popularity', 0), reverse=True)
    artist = valid_items[0]
    artist_name_trouve = artist.get('name', nom_rappeur_saisi)

    # Construction du lien Genius par défaut
    formatted_name = urllib.parse.quote(artist_name_trouve.replace(" ", "-").capitalize())
    default_genius_url = f"https://genius.com/artists/{formatted_name}"

    data = {
        "name": artist_name_trouve,
        "id": artist['id'],
        "img_url": safe_get(artist, "images/0/url", ""),
        "followers": artist.get('followers', {}).get('total', 0),
        "popularity": artist.get('popularity', 0),
        "genres": artist.get('genres', []),
        "spotify_url": safe_get(artist, "external_urls/spotify", "N/A"),
        "bio": "Description non disponible.",
        "genius_url": default_genius_url,
        "wiki_url": "Non trouvé"
    }

    # 2. Genius (API)
    try:
        genius_artist = genius.search_artist(data["name"], max_songs=0, sort="popularity")
        if genius_artist: data["genius_url"] = genius_artist.url
    except: pass
    
    # 3. Wikipédia (VERSION CORRIGÉE ET ROBUSTE)
    try:
        # Étape A : On cherche une liste de pages potentielles
        search_results = wikipedia.search(data["name"], results=3)
        
        found_page = None
        # Mots-clés pour vérifier qu'on est sur la bonne page
        keywords = ["rappeur", "groupe", "hip-hop", "musique", "chanteur", "slam"]
        
        # Étape B : On teste les résultats un par un
        for res in search_results:
            try:
                # auto_suggest=False est crucial pour éviter que wiki devine mal
                page = wikipedia.page(res, auto_suggest=False)
                summary = page.summary.lower()
                
                # Vérifie si un mot clé est dans le résumé
                if any(k in summary for k in keywords):
                    data["bio"] = page.summary[:1000] + "..." # On coupe si trop long
                    data["wiki_url"] = page.url
                    found_page = True
                    break # On a trouvé, on arrête de chercher
            except (wikipedia.DisambiguationError, wikipedia.PageError):
                continue # Si erreur sur cette page, on teste la suivante
                
    except Exception as e:
        print(f"Erreur Wiki Globale: {e}")

    # 4. Discographie Spotify
    try:
        albums_list = sp.artist_albums(data["id"], album_type='album', country='FR', limit=50)['items']
    except: albums_list = []

    albums_dict = {}
    for album in albums_list:
        if album['name'] not in albums_dict or album['release_date'] > albums_dict[album['name']]['release_date']:
            albums_dict[album['name']] = album
    
    data["albums"] = sorted(albums_dict.values(), key=lambda x: x['release_date'], reverse=True)
    
    return data, artist_name_trouve, None

def generate_text_content(data):
    content = f"RAP DATA REPORT : {data['name'].upper()}\n"
    content += f"Généré le : {datetime.now().strftime('%d/%m/%Y')}\n"
    content += "="*50 + "\n\n"
    content += f"POPULARITÉ : {data['popularity']}/100\n"
    content += f"FOLLOWERS  : {data['followers']:,}\n\n"
    content += f"BIO :\n{data['bio']}\n\n"
    content += "="*50 + "\nDISCOGRAPHIE (Récents en premier)\n" + "="*50 + "\n"

    for album in data["albums"]:
        try:
            content += f"\n[ALBUM] {album['name']} ({album['release_date']})\n"
            tracks = sp.album_tracks(album["id"])["items"]
            for track in tracks:
                query = f"{track['name']} {data['name']}"
                encoded_query = urllib.parse.quote(query)
                genius_link = f"https://genius.com/search?q={encoded_query}"
                content += f"   - {track['track_number']}. {track['name']} (Genius: {genius_link})\n"
        except: continue
    return content

# --- LOGIQUE ---
def do_search():
    user_input = st.session_state.rappeur_input_key
    if user_input:
        with st.spinner(f"🎧 Analyse de {user_input} en cours..."):
            data, artist_trouve, error = get_artist_data(user_input)
            st.session_state.search_result = {'data': data, 'artist_trouve': artist_trouve, 'error': error, 'input': user_input}
            if not error:
                new_item = {'name': data['name'], 'time': datetime.now().strftime("%H:%M")}
                if not st.session_state.history or st.session_state.history[-1]['name'] != data['name']:
                    st.session_state.history.append(new_item)

def recall_history(name):
    st.session_state.rappeur_input_key = name
    do_search()

# --- SIDEBAR ---
with st.sidebar:
    st.header("🕒 Historique")
    if st.session_state.history:
        for i, item in enumerate(reversed(st.session_state.history[-10:])): 
            st.button(f"🎵 {item['name']}", key=f"hist_{i}", on_click=recall_history, args=[item['name']], use_container_width=True)
        st.markdown("---")
        if st.button("🗑️ Effacer tout", key="clean"):
            st.session_state.history = []
            st.rerun()
    else: st.caption("Vos recherches apparaîtront ici.")

# --- MAIN ---
st.title("🔥 Rap Data Generator (FR Only)")
st.markdown("### L'outil ultime pour analyser le Rap Français")

col_search, col_btn = st.columns([4, 1])
with col_search:
    st.text_input("Entrez un nom d'artiste", placeholder="Ex: Ninho, Gazo...", key="rappeur_input_key", label_visibility="collapsed", on_change=do_search)
with col_btn:
    st.button("Analyser 🚀", on_click=do_search, use_container_width=True)

if st.session_state.search_result:
    res = st.session_state.search_result
    if res['error']:
        st.error(res['error'])
    else:
        data = res['data']
        if res['input'].lower().strip() != res['artist_trouve'].lower().strip():
            st.toast(f"Correction : {res['input']} → {res['artist_trouve']}", icon="✨")
        else: st.toast("Rappeur français identifié !", icon="🇫🇷")

        hero_col1, hero_col2 = st.columns([1, 2.5], gap="large")
        with hero_col1:
            if data['img_url']: st.image(data['img_url'], use_container_width=True)
            if data['genres']: st.markdown("**Genres :** " + ", ".join([f"`{g}`" for g in data['genres'][:3]]))
        with hero_col2:
            st.title(data['name'])
            m1, m2, m3 = st.columns(3)
            m1.metric("Popularité", f"{data['popularity']}/100")
            m2.metric("Followers", f"{data['followers']:,}".replace(",", " "))
            m3.metric("Albums", len(data['albums']))
            
            # Affichage de la Bio avec fallback si vide
            bio_text = data['bio'] if len(data['bio']) > 20 else "Biographie non disponible sur Wikipédia."
            st.markdown(f"_{bio_text}_")
            
            st.markdown("---")
            l1, l2, l3, l4 = st.columns(4)
            l1.link_button("💚 Spotify", data['spotify_url'])
            l2.link_button("🟡 Genius", data['genius_url']) 
            l3.link_button("🎟️ Concerts", f"https://www.google.com/search?q=concert+{data['name'].replace(' ', '+')}")
            l4.link_button("📀 Certifs", f"https://snepmusique.com/les-certifications/?interprete={data['name'].replace(' ', '+')}")

        st.markdown("###")
        tab1, tab2 = st.tabs(["💿 Discographie Détaillée", "📥 Exporter"])
        with tab1:
            if not data['albums']: st.info("Aucun album trouvé.")
            else:
                st.markdown("Cliquez pour voir les titres et **paroles**.")
                for album in data['albums']:
                    with st.expander(f"📅 {album['release_date'][:4]} - **{album['name']}**"):
                        c1, c2 = st.columns([1, 4])
                        with c1:
                            if len(album['images']) > 0: st.image(album['images'][1]['url'], width=100)
                        with c2:
                            try:
                                tracks = sp.album_tracks(album["id"])["items"]
                                for track in tracks:
                                    track_name = track['name']
                                    if track_name:
                                        search_query = f"{track_name} {data['name']}"
                                        encoded_query = urllib.parse.quote(search_query)
                                        genius_link = f"https://genius.com/search?q={encoded_query}"
                                        st.markdown(
                                            f"{track['track_number']}. **{track_name}** "
                                            f"<a href=\"{genius_link}\" target=\"_blank\" class=\"genius-link\">🟡 Paroles</a>", 
                                            unsafe_allow_html=True
                                        )
                                    else:
                                         st.markdown(f"{track['track_number']}. Titre Inconnu <span class='not-found'>❌ Paroles non trouvées</span>", unsafe_allow_html=True)
                            except: st.error("Erreur chargement titres")
        with tab2:
            txt = generate_text_content(data)
            st.download_button(f"📄 Télécharger Fiche {data['name']}", txt, f"{data['name']}.txt", "text/plain", use_container_width=True)

st.markdown("---")
st.markdown("<center style='color: grey;'>Développé avec ❤️ avec Fevrie, Betastar et Raitro</center>", unsafe_allow_html=True)