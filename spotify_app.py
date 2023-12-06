import streamlit as st
import pandas as pd
from scr.spotipyclient import SpotipyClient

def display_top_tracks(top_tracks_json):
    tracks_data = []

    for track in top_tracks_json['items']:
        track_info = {
            'Artist': track['album']['artists'][0]['name'],  
            'Track Name': track['name'], 
            'Album Name': track['album']['name'],  
            'Release Date': track['album']['release_date'],  
        }
        tracks_data.append(track_info)

    tracks_df = pd.DataFrame(tracks_data)

    st.table(tracks_df[['Artist', 'Track Name', 'Album Name', 'Release Date']])

st.set_page_config(page_title='Spotify Recommendation System', page_icon='🎵')

st.markdown("""
<style>
body {
    background-color: #f7f7f7;
    color: #333;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    height: 100vh;
    margin: 0; /* Remove default margin to center logo */
}
.stButton > button {
    background-color: #1DB954;
    color: white;
    font-weight: bold;
    border: none;
    border-radius: 5px;
    padding: 10px 20px;
}
.stButton > button:hover {
    background-color: #218838;
}
</style>
""", unsafe_allow_html=True)

st.image('./imagen/Spotify.png', width=200)

st.title('Spotify Recommendation System')

st.write("⚠️ Do not use your primary Spotify credentials if possible. Consider using temporary credentials.")

client_id = st.sidebar.text_input('Client ID')
client_secret = st.sidebar.text_input('Client Secret', type='password')
username = st.sidebar.text_input('Username')
redirect_uri = st.sidebar.text_input('Redirect URI', 'http://localhost:8080')
scope = 'user-top-read playlist-modify-public playlist-modify-private'

if client_id and client_secret and username:
    global spotipy_client
    spotipy_client = SpotipyClient(client_id, client_secret, username, redirect_uri, scope)

    if st.sidebar.button('Log in to Spotify'):
        with st.spinner('Logging in...'):
            try:
                spotipy_client.authenticate_spotify()
                st.success('Authentication successful')
                
                top_tracks = spotipy_client.get_top_tracks()
                
                st.subheader('Top Tracks')
                display_top_tracks(top_tracks)
                
            except Exception as e:
                st.error('An error occurred during authentication')
                st.error(str(e))
    
    if st.sidebar.button('Generate Recommendations'):
        with st.spinner('Generating recommendations...'):
            if spotipy_client is not None:
                recommended_playlist_id = spotipy_client.create_recommended_playlist()
                st.success('Recommended playlist created successfully!')
            else:
                st.error('Spotify not authenticated. Please log in first.')
