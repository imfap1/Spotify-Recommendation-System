import spotipy
import spotipy.util as util
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import linear_kernel
import numpy as np
import joblib
import streamlit as st

class SpotipyClient():
    client = None
    client_id = None
    client_secret = None
    username = None
    redirect_uri = 'http://localhost:8080'

    def __init__(self, client_id, client_secret, username, redirect_uri, scope):
        self.client_id = client_id
        self.client_secret = client_secret
        self.username = username
        self.redirect_uri = redirect_uri
        self.scope = scope

    def client_auth(self):
        token = util.prompt_for_user_token(self.username, self.scope,
                                          self.client_id, self.client_secret, self.redirect_uri)
        self.client = spotipy.Spotify(auth=token)

    def get_top_tracks(self):
        # Use cache to store and retrieve top listened tracks
        cache_file = "top_tracks_cache.pkl"
        try:
            top_tracks = joblib.load(cache_file)
        except FileNotFoundError:
            top_tracks = self.client.current_user_top_tracks(time_range='short_term', limit=1)
            joblib.dump(top_tracks, cache_file)
        return top_tracks

    def create_tracks_dataframe(self, top_tracks):
        '''Get audio features of the top tracks listened by the user'''
        tracks = top_tracks['items']
        tracks_ids = [track['id'] for track in tracks]
        audio_features = self.client.audio_features(tracks_ids)
        top_tracks_df = pd.DataFrame(audio_features)
        top_tracks_df = top_tracks_df[["id", "acousticness", "danceability", 
            "duration_ms", "energy", "instrumentalness",  "key", "liveness", 
            "loudness", "mode", "speechiness", "tempo", "valence"]]

        return top_tracks_df

    def get_artists_ids(self, top_tracks):
        '''Get ids of the artists in "top_tracks"'''
        ids_artists = []

        for item in top_tracks['items']:
            artist_id = item['artists'][0]['id']
            artist_name = item['artists'][0]['name']
            ids_artists.append(artist_id)

        # Clean list to avoid repetitions
        ids_artists = list(set(ids_artists))

        return ids_artists

    def get_similar_artists_ids(self, ids_artists):
        '''Expand the list of "ids_artists" with similar artists'''
        ids_similar_artists = []
        for artist_id in ids_artists:
            artists = self.client.artist_related_artists(artist_id)['artists']
            for item in artists:
                artist_id = item['id']
                artist_name = item['name']
                ids_similar_artists.append(artist_id)

        ids_artists.extend(ids_similar_artists)

        # Clean list to avoid repetitions
        ids_artists = list(set(ids_artists))

        return ids_artists

    def get_new_releases_artists_ids(self, ids_artists):
        '''Expand the list of "ids_artists" with artists having new releases'''

        new_releases = self.client.new_releases(limit=1)['albums']
        for item in new_releases['items']:
            artist_id = item['artists'][0]['id']
            ids_artists.append(artist_id)

        # Clean list to avoid repetitions
        ids_artists = list(set(ids_artists))

        return ids_artists

    def get_albums_ids(self, ids_artists):
        '''Get a list of albums for each artist in "ids_artists"'''
        ids_albums = []
        for id_artist in ids_artists:
            album = self.client.artist_albums(id_artist, limit=1)['items'][0]
            ids_albums.append(album['id'])

        return ids_albums

    def get_albums_tracks(self, ids_albums):
        '''Extract 3 tracks for each album in "ids_albums"'''
        ids_tracks = []
        for id_album in ids_albums:
            album_tracks = self.client.album_tracks(id_album, limit=1)['items']
            for track in album_tracks:
                ids_tracks.append(track['id'])

        return ids_tracks

    def get_tracks_features(self, ids_tracks):
        # Use cache to store and retrieve track features
        cache_file = "tracks_features_cache.pkl"
        cached_features = {}
        new_ids = []

        for id_track in ids_tracks:
            if id_track in cached_features:
                cached_feature = cached_features[id_track]
            else:
                new_ids.append(id_track)

        if new_ids:
            features = self.client.audio_features(new_ids)
            for id_track, feature in zip(new_ids, features):
                cached_features[id_track] = feature

        # Create a DataFrame with track

        features
        features_list = [cached_features[id_track] for id_track in ids_tracks]
        candidates_df = pd.DataFrame(features_list)
        candidates_df = candidates_df[["id", "acousticness", "danceability", "duration_ms",
            "energy", "instrumentalness",  "key", "liveness", "loudness", "mode", 
            "speechiness", "tempo", "valence"]]

        return candidates_df
    
    def compute_cossim(self, top_tracks_df, candidates_df):
        '''Calculate cosine similarity between each top_track and each candidate track
        in candidates_df. Returns a matrix of n_top_tracks x n_candidates_df'''
        top_tracks_mtx = top_tracks_df.iloc[:,1:].values
        candidates_mtx = candidates_df.iloc[:,1:].values

        # Standardize each column of features: mu = 0, sigma = 1
        scaler = StandardScaler()
        top_tracks_scaled = scaler.fit_transform(top_tracks_mtx)
        candidates_scaled = scaler.fit_transform(candidates_mtx)

        # Normalize each feature vector (resulting magnitude = 1)
        top_tracks_norm = np.sqrt((top_tracks_scaled*top_tracks_scaled).sum(axis=1))
        candidates_norm = np.sqrt((candidates_scaled*candidates_scaled).sum(axis=1))

        n_top_tracks = top_tracks_scaled.shape[0]
        n_candidates = candidates_scaled.shape[0]
        top_tracks = top_tracks_scaled/top_tracks_norm.reshape(n_top_tracks,1)
        candidates = candidates_scaled/candidates_norm.reshape(n_candidates,1)

        # Calculate cosine similarities
        cos_sim = linear_kernel(top_tracks, candidates)

        return cos_sim

    def content_based_filtering(self, pos, cos_sim, ncands, threshold = 0.8):
        '''For a given top_track (pos = 0, 1, ...), extract "ncands" candidates,
        using "cos_sim" and as long as they exceed a similarity threshold'''

        # Get all candidate tracks above the threshold
        idx = np.where(cos_sim[pos,:] >= threshold)[0] # e.g., idx: [27, 82, 135]

        # Sort them in descending order (by higher to lower similarities)
        idx = idx[np.argsort(cos_sim[pos,idx])[::-1]]

        # If there are more than "ncands", return only a total of "ncands"
        if len(idx) >= ncands:
            cands = idx[0:ncands]
        else:
            cands = idx

        return cands
    
    def create_recommended_playlist(self):
        '''Create the recommended playlist on Spotify. Executes all previous methods'''

        # Authenticate
        self.client_auth()

        # Get candidates and compare them (cosine distances) with tracks
        # from the original playlist
        top_tracks = self.get_top_tracks()
        top_tracks_df = self.create_tracks_dataframe(top_tracks)
        ids_artists = self.get_artists_ids(top_tracks)
        ids_artists = self.get_similar_artists_ids(ids_artists)
        ids_artists = self.get_new_releases_artists_ids(ids_artists)
        ids_albums = self.get_albums_ids(ids_artists)
        ids_tracks = self.get_albums_tracks(ids_albums)
        candidates_df = self.get_tracks_features(ids_tracks)
        cos_sim = self.compute_cossim(top_tracks_df, candidates_df)

        # Create a list of ids with the recommendations
        ids_top_tracks = []
        ids_playlist = []

        for i in range(top_tracks_df.shape[0]):
            ids_top_tracks.append(top_tracks_df['id'][i])

            # Get a list of candidates (5) for this track
            cands = self.content_based_filtering(i, cos_sim, 5, threshold=0.7)

            # If there are related tracks, obtain the corresponding ids
            if len(cands) == 0:
                continue
            else:
                for j in cands:
                    id_cand = candidates_df['id'][j]
                    ids_playlist.append(id_cand)

        # Remove candidates that are already in top-tracks
        ids_playlist_filtered = [x for x in ids_playlist if x not in ids_top_tracks]

        # And remove possible repetitions
        ids_playlist_filtered = list(set(ids_playlist_filtered))

        # Create the playlist on Spotify!!!
        playlist = self.client.user_playlist_create(user = self.username,
            name = 'Spotipy Recommender Playlist',
            description = 'Playlist created with the recommendation system')
        self.client.playlist_add_items(playlist['id'], ids_playlist_filtered)
        
def clean_recommendations_json(recommendations_json):
    cleaned_data = []
    
    # Verificar si hay datos en 'items'
    if 'items' in recommendations_json:
        items = recommendations_json['items']
        
        for item in items:
            track_data = item.get('track', {})
            added_at = item.get('added_at', 'Unknown')
            added_by = item.get('added_by', {}).get('external_urls', {}).get('spotify', 'Unknown')
            
            # Extraer información relevante del álbum y el artista
            album_data = track_data.get('album', {})
            artist_data = album_data.get('artists', [{}])[0]
            artist_url = artist_data.get('external_urls', {}).get('spotify', 'Unknown')
            
            # Crear un diccionario con los datos limpios
            cleaned_track = {
                'Added At': added_at,
                'Added By': added_by,
                'Artist URL': artist_url
            }
            
            cleaned_data.append(cleaned_track)
    
    return cleaned_data

def generate_recommendations():
    with st.spinner('Generating recommendations, please wait...'):
        try:
            # Access spotipy_client from the session state
            recommended_tracks = st.session_state['spotipy_client'].create_recommended_playlist()
            if recommended_tracks and 'items' in recommended_tracks:
                st.subheader('Recommendations:')
                display_top_tracks(recommended_tracks)
            else:
                st.write('No recommendations found.')
        except Exception as e:
            st.error('An error occurred while generating recommendations.')
            st.error(str(e))
        finally:
            st.success('Recommendations generated!')


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

    st.dataframe(tracks_df)

def get_and_display_top_tracks():
    try:
        # Access spotipy_client from the session state
        top_tracks_json = st.session_state['spotipy_client'].get_top_tracks()
        if 'items' in top_tracks_json and top_tracks_json['items']:
            st.subheader('Top Tracks:')
            tracks_df = display_top_tracks(top_tracks_json)
            
            # Clear the previous DataFrame
            st.empty()
            
            # Display the new DataFrame
            st.dataframe(tracks_df)
        else:
            st.write('No top tracks data found.')
    except Exception as e:
        st.error('An error occurred while getting top tracks.')
        st.error(str(e))


# Función principal
def main():
    st.title('Spotify Recommendation System')

    # Define the scope and redirect_uri outside the session state
    scope = 'user-top-read playlist-modify-public playlist-modify-private'
    redirect_uri = 'http://localhost:8080'

    # Input fields for Spotify credentials
    client_id = st.text_input('Client ID', 'Your Client ID')
    client_secret = st.text_input('Client Secret', 'Your Client Secret')
    username = st.text_input('Username', 'Your Spotify Username')

    if client_id and client_secret and username:
        if 'spotipy_client' not in st.session_state:
            st.session_state.spotipy_client = SpotipyClient(client_id, client_secret, username, redirect_uri, scope)

        if st.button('Log in to Spotify'):
            try:
                st.session_state.spotipy_client.client_auth()
                st.success('Authentication successful')
                get_and_display_top_tracks()  # Modify this function to use st.session_state.spotipy_client
            except Exception as e:
                st.error('An error occurred during authentication')
                st.error(str(e))

        # Button for generating recommendations
        if 'spotipy_client' in st.session_state and st.session_state.spotipy_client.client:
            if st.button('Generate Recommendations'):
                try:
                    generate_recommendations()  # Modify this function to use st.session_state.spotipy_client
                except Exception as e:
                    st.error('An error occurred while generating recommendations.')
                    st.error(str(e))

if __name__ == '__main__':
    main()