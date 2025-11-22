import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import wikipedia
from datetime import datetime
import io

# --- GESTION DE L'ÉTAT (SESSION STATE) ---
if 'history' not in st.session_state:
    st.session_state.history = []
if 'search_term' not in st.session_state:
    st.session_state.search_term = ""

# --- CONFIGURATION ---
# ⚠️ ATTENTION : Vos clés sont visibles ici. Ne partagez pas ce fichier publiquement.
SPOTIPY_CLIENT_ID = '797ca964aaeb4a93afd012b639e79d03'
SPOTIPY_CLIENT_SECRET = '4d8484cc53cc43aeb32610151a36594f'

# Configuration des APIs
auth_manager = SpotifyClientCredentials(client_id=SPOTIPY_CLIENT_ID, client_secret=SPOTIPY_CLIENT_SECRET)
sp = spotipy.Spotify(auth_manager=auth_manager)
wikipedia.set_lang("fr")

# --- FONCTIONS UTILITAIRES ---
def safe_get(dct, path, default=""):
    try:
        for p in path.split("/"):
            if p.isdigit():
                dct = dct[int(p)]
            else:
                dct = dct[p]
        return dct
    except Exception:
        return default

def get_artist_data(nom_rappeur_saisi):
    """
    Récupère les données et retourne un dictionnaire complet + le nom de l'artiste trouvé.
    """
    
    # 1. Recherche Spotify
    try:
        results = sp.search(q=f'artist:{nom_rappeur_saisi}', type='artist', limit=10)
        items = results['artists']['items']
    except Exception as e:
        return None, None, f"Erreur Spotify : {e}"

    if not items:
        return None, None, "Artiste non trouvé."

    # Tri par popularité
    items.sort(key=lambda x: x.get('popularity', 0), reverse=True)
    artist = items[0]

    artist_name_trouve = artist.get('name', nom_rappeur_saisi)

    data = {
        "name": artist_name_trouve,
        "id": artist['id'],
        "img_url": safe_get(artist, "images/0/url", ""),
        "followers": artist.get('followers', {}).get('total', 0),
        "popularity": artist.get('popularity', 0),
        "spotify_url": safe_get(artist, "external_urls/spotify", "N/A"),
        "bio": "Description non disponible."
    }

    # 2. Infos Wikipédia
    data["wiki_url"] = "Non trouvé"
    try:
        page_wiki = wikipedia.page(data["name"]) 
        data["bio"] = wikipedia.summary(data["name"], sentences=4)
        data["wiki_url"] = page_wiki.url
    except Exception:
        pass

    # 3. Discographie
    try:
        albums_list = sp.artist_albums(data["id"], album_type='album', country='FR', limit=50)['items']
    except Exception:
        albums_list = []

    # Nettoyage doublons
    albums_dict = {}
    for album in albums_list:
        if album['name'] not in albums_dict or album['release_date'] > albums_dict[album['name']]['release_date']:
            albums_dict[album['name']] = album
    
    # MODIFICATION CLÉ ICI : reverse=True trie du plus récent au plus ancien
    data["albums"] = sorted(albums_dict.values(), key=lambda x: x['release_date'], reverse=True)
    
    return data, artist_name_trouve, None

def generate_text_content(data):
    """Génère le contenu du fichier TXT à partir des données"""
    content = f"""================================================================================
FICHE ARTISTE : {data['name'].upper()}
Généré le : {datetime.now().strftime("%d/%m/%Y")}
================================================================================

[INFOS GÉNÉRALES]
Nom de scène       : {data['name']}
Popularité Spotify : {data['popularity']}/100
Abonnés Spotify    : {data['followers']:,}
Lien Photo         : {data['img_url']}

[BIOGRAPHIE COURTE]
{data['bio']}

[LIENS UTILES]
🎵 Spotify Officiel : {data['spotify_url']}
📖 Wikipédia        : {data['wiki_url']}
🎟️ Billetterie      : https://www.google.com/search?q=concert+billetterie+{data['name'].replace(' ', '+')}
📀 Certifications   : https://snepmusique.com/les-certifications/?interprete={data['name'].replace(' ', '+')}

================================================================================
DISCOGRAPHIE (Albums Studio)
(Du plus récent au plus ancien)
================================================================================
"""
    for album in data["albums"]:
        try:
            content += f"\n📅 {album['release_date']} - {album['name']}\n"
            content += f"🔗 Lien : {safe_get(album, 'external_urls/spotify', '')}\n"
            content += "-" * 40 + "\n"
            
            # Récupération des tracks (API call)
            tracks = sp.album_tracks(album["id"])["items"]
            for track in tracks:
                content += f"   {track['track_number']}. {track['name']}\n"
            content += "\n"
        except:
            continue
            
    content += "\nFIN DU RAPPORT"
    return content

# --- FONCTION DE RECHERCHE PRINCIPALE ---
def do_search():
    """
    Exécute la recherche principale en utilisant la valeur stockée
    dans st.session_state.rappeur_input_key.
    """
    # On récupère la valeur du champ de texte stockée par la clé 'rappeur_input_key'
    rappeur_input = st.session_state.rappeur_input_key
    
    if rappeur_input:
        with st.spinner(f"Recherche d'infos pour le nom saisi : **{rappeur_input}**..."):
            
            data, artist_trouve, error = get_artist_data(rappeur_input)
            
            # Stocke les résultats dans session_state pour qu'ils soient affichés
            st.session_state.search_result = {
                'data': data,
                'artist_trouve': artist_trouve,
                'error': error,
                'input': rappeur_input
            }
        
# --- GESTION DE L'AFFICHAGE DE LA RECHERCHE ---
def display_search_results():
    """Affiche les résultats si une recherche a été effectuée."""
    if 'search_result' not in st.session_state:
        return

    result = st.session_state.search_result
    data = result['data']
    artist_trouve = result['artist_trouve']
    rappeur_input = result['input']
    error = result['error']
    
    if error:
        st.error(error)
    else:
        # --- GESTION DE L'HISTORIQUE (Ajout de l'artiste) ---
        new_entry = {
            'name': data['name'],
            'url': data['spotify_url'],
            'time': datetime.now().strftime("%H:%M:%S")
        }
        
        if not st.session_state.history or st.session_state.history[-1]['name'] != data['name']:
            st.session_state.history.append(new_entry)
            st.rerun() 
        
        # --- VÉRIFICATION DE LA CORRECTION ---
        if rappeur_input.lower().strip() != artist_trouve.lower().strip():
            st.success(f"✅ Nom corrigé ! Nous avons trouvé : **{artist_trouve}**.")

        # --- AFFICHAGE VISUEL ---
        col1, col2 = st.columns([1, 2])
        
        with col1:
            if data["img_url"]:
                st.image(data["img_url"], caption=data["name"])
            else:
                st.warning("Pas d'image trouvée")
        
        with col2:
            st.header(data["name"])
            st.metric("Popularité Spotify", f"{data['popularity']}/100")
            st.metric("Abonnés", f"{data['followers']:,}")
            st.info(data["bio"])
            
            st.markdown(f"[🎵 Écouter sur Spotify]({data['spotify_url']}) | [📖 Wikipédia]({data['wiki_url']})")
            st.markdown(f"[🎟️ Billetterie](https://www.google.com/search?q=concert+billetterie+{data['name'].replace(' ', '+')}) | [📀 Certifications](https://snepmusique.com/les-certifications/?interprete={data['name'].replace(' ', '+')})")

        st.divider()
        st.subheader("💿 Discographie détectée (Du plus récent au plus ancien)")
        
        # On génère le texte en arrière-plan pour le téléchargement
        text_report = generate_text_content(data)
        
        # Bouton de téléchargement
        file_name = f"{data['name'].replace(' ', '_')}.txt"
        st.download_button(
            label="📥 Télécharger la Fiche (Format Texte)",
            data=text_report,
            file_name=file_name,
            mime="text/plain"
        )

        # Aperçu des albums
        for album in data["albums"]:
            with st.expander(f"📅 {album['release_date']} - {album['name']}"):
                st.write(f"Lien : {safe_get(album, 'external_urls/spotify', '')}")
                st.caption("Les titres sont inclus dans le fichier téléchargé.")

# --- INTERFACE STREAMLIT ---
st.set_page_config(page_title="Générateur Fiche Rappeur", page_icon="🎤")

st.title("🎤 Générateur de Fiche Rappeur")
st.markdown("Entrez un nom pour générer une fiche complète et télécharger le rapport.")

# --- AFFICHAGE ET GESTION DE L'HISTORIQUE (BARRE LATÉRALE) ---
st.sidebar.subheader("Historique des recherches 🔎")

if st.session_state.history:
    # On affiche les 5 dernières entrées, du plus récent au plus ancien
    for item in reversed(st.session_state.history[-5:]):
        st.sidebar.markdown(f"**{item['name']}** ([Lien]({item['url']})) - *{item['time']}*")
    
    # Bouton pour effacer l'historique
    if st.sidebar.button("Effacer l'historique"):
        st.session_state.history = []
        st.rerun() 
else:
    st.sidebar.info("Aucune recherche récente.")

# --- CORPS DE L'APPLICATION ---

# Champ de recherche. L'appui sur Entrée exécute do_search() via on_change
rappeur_input = st.text_input(
    "Nom de l'artiste", 
    placeholder="Ex: Ninho, Booba, Tiakola...",
    key='rappeur_input_key',
    on_change=do_search
)

# Le bouton appelle la même fonction do_search()
if st.button("Lancer la recherche 🚀"):
    do_search()

# Affiche les résultats si ils existent
display_search_results()