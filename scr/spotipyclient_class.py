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
        '''Autenticación API de Spotify'''
        token = util.prompt_for_user_token(self.username,self.scope,
            self.client_id,self.client_secret,self.redirect_uri)
        self.client = spotipy.Spotify(auth=token)
        
    def client_auth(self):
        '''Autenticación API de Spotify'''
        token = util.prompt_for_user_token(self.username,self.scope,
            self.client_id,self.client_secret,self.redirect_uri)
        self.client = spotipy.Spotify(auth=token)
        
    
    def get_top_tracks(self):
        # Utilizar el caché para almacenar y recuperar las pistas más escuchadas
        cache_file = "top_tracks_cache.pkl"
        try:
            top_tracks = joblib.load(cache_file)
        except FileNotFoundError:
            top_tracks = self.client.current_user_top_tracks(time_range='short_term', limit=20)
            joblib.dump(top_tracks, cache_file)
        return top_tracks

    def create_tracks_dataframe(self, top_tracks):
        '''Obtener "audio features" de las pistas más escuchadas por el usuario'''
        tracks = top_tracks['items']
        tracks_ids = [track['id'] for track in tracks]
        audio_features = self.client.audio_features(tracks_ids)
        top_tracks_df = pd.DataFrame(audio_features)
        top_tracks_df = top_tracks_df[["id", "acousticness", "danceability", 
            "duration_ms", "energy", "instrumentalness",  "key", "liveness", 
            "loudness", "mode", "speechiness", "tempo", "valence"]]

        return top_tracks_df

    def get_artists_ids(self, top_tracks):
        '''Obtener ids de los artistas en "top_tracks"'''
        ids_artists = []

        for item in top_tracks['items']:
            artist_id = item['artists'][0]['id']
            artist_name = item['artists'][0]['name']
            ids_artists.append(artist_id)

        # Depurar lista para evitar repeticiones
        ids_artists = list(set(ids_artists))

        return ids_artists

    def get_similar_artists_ids(self, ids_artists):
        '''Expandir el listado de "ids_artists" con artistas similares'''
        ids_similar_artists = []
        for artist_id in ids_artists:
            artists = self.client.artist_related_artists(artist_id)['artists']
            for item in artists:
                artist_id = item['id']
                artist_name = item['name']
                ids_similar_artists.append(artist_id)

        ids_artists.extend(ids_similar_artists)

        # Depurar lista para evitar repeticiones
        ids_artists = list(set(ids_artists))

        return ids_artists

    def get_new_releases_artists_ids(self, ids_artists):
        '''Expandir el listado de "ids_artists" con artistas con nuevos lanzamientos'''

        new_releases = self.client.new_releases(limit=20)['albums']
        for item in new_releases['items']:
            artist_id = item['artists'][0]['id']
            ids_artists.append(artist_id)

        # Depurar lista para evitar repeticiones
        ids_artists = list(set(ids_artists))

        return ids_artists

    def get_albums_ids(self, ids_artists):
        '''Obtener listado de albums para cada artista en "ids_artists"'''
        ids_albums = []
        for id_artist in ids_artists:
            album = self.client.artist_albums(id_artist, limit=1)['items'][0]
            ids_albums.append(album['id'])

        return ids_albums

    def get_albums_tracks(self, ids_albums):
        '''Extraer 3 tracks para cada album en "ids_albums"'''
        ids_tracks = []
        for id_album in ids_albums:
            album_tracks = self.client.album_tracks(id_album, limit=1)['items']
            for track in album_tracks:
                ids_tracks.append(track['id'])

        return ids_tracks

    def get_tracks_features(self, ids_tracks):
        # Utilizar el caché para almacenar y recuperar las características de las pistas
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

        # Crear un DataFrame con las características de las pistas
        features_list = [cached_features[id_track] for id_track in ids_tracks]
        candidates_df = pd.DataFrame(features_list)
        candidates_df = candidates_df[["id", "acousticness", "danceability", "duration_ms",
            "energy", "instrumentalness",  "key", "liveness", "loudness", "mode", 
            "speechiness", "tempo", "valence"]]

        return candidates_df
    
    def compute_cossim(self, top_tracks_df, candidates_df):
        '''Calcula la similitud del coseno entre cada top_track y cada pista
        candidata en candidates_df. Retorna matriz de n_top_tracks x n_candidates_df'''
        top_tracks_mtx = top_tracks_df.iloc[:,1:].values
        candidates_mtx = candidates_df.iloc[:,1:].values

        # Estandarizar cada columna de features: mu = 0, sigma = 1
        scaler = StandardScaler()
        top_tracks_scaled = scaler.fit_transform(top_tracks_mtx)
        can_scaled = scaler.fit_transform(candidates_mtx)

        # Normalizar cada vector de características (magnitud resultante = 1)
        top_tracks_norm = np.sqrt((top_tracks_scaled*top_tracks_scaled).sum(axis=1))
        can_norm = np.sqrt((can_scaled*can_scaled).sum(axis=1))

        n_top_tracks = top_tracks_scaled.shape[0]
        n_candidates = can_scaled.shape[0]
        top_tracks = top_tracks_scaled/top_tracks_norm.reshape(n_top_tracks,1)
        candidates = can_scaled/can_norm.reshape(n_candidates,1)

        # Calcular similitudes del coseno
        cos_sim = linear_kernel(top_tracks,candidates)

        return cos_sim

    def content_based_filtering(self, pos, cos_sim, ncands, umbral = 0.8):
        '''Dada una pista de top_tracks (pos = 0, 1, ...) extraer "ncands" candidatos,
        usando "cos_sim" y siempre y cuando superen un umbral de similitud'''

        # Obtener todas las pistas candidatas por encima del umbral
        idx = np.where(cos_sim[pos,:]>=umbral)[0] # ejm. idx: [27, 82, 135]

        # Y organizarlas de forma descendente (por similitudes de mayor a menor)
        idx = idx[np.argsort(cos_sim[pos,idx])[::-1]]

        # Si hay más de "ncands", retornar únicamente un total de "ncands"
        if len(idx) >= ncands:
            cands = idx[0:ncands]
        else:
            cands = idx

        return cands
    
    def create_recommended_playlist(self):
        '''Crear la lista de recomendaciones en Spotify. Ejecuta todos los métodos
        anteriores'''

        # Autenticar
        self.client_auth()

        # Obtener candidatos y compararlos (distancias coseno) con las pistas
        # del playlist original
        top_tracks = self.get_top_tracks()
        top_tracks_df = self.create_tracks_dataframe(top_tracks)
        ids_artists = self.get_artists_ids(top_tracks)
        ids_artists = self.get_similar_artists_ids(ids_artists)
        ids_artists = self.get_new_releases_artists_ids(ids_artists)
        ids_albums = self.get_albums_ids(ids_artists)
        ids_tracks = self.get_albums_tracks(ids_albums)
        candidates_df = self.get_tracks_features(ids_tracks)
        cos_sim = self.compute_cossim(top_tracks_df, candidates_df)

        # Crear listado de ids con las recomendaciones
        ids_top_tracks = []
        ids_playlist = []

        for i in range(top_tracks_df.shape[0]):
            ids_top_tracks.append(top_tracks_df['id'][i])

            # Obtener listado de candidatos (5) para esta pista
            cands = self.content_based_filtering(i, cos_sim, 5, umbral=0.7)

            # Si hay pistas relacionadas obtener los ids correspondientes
            if len(cands)==0:
                continue
            else:
                for j in cands:
                    id_cand = candidates_df['id'][j]
                    ids_playlist.append(id_cand)

        # Eliminar candidatos que ya están en top-tracks
        ids_playlist_dep = [x for x in ids_playlist if x not in ids_top_tracks]

        # Y eliminar posibles repeticiones
        ids_playlist_dep = list(set(ids_playlist_dep))

        # Crear la playlist en spotify!!!
        pl = self.client.user_playlist_create(user = self.username,
            name = 'Spotipy Recommender Playlist',
            description = 'Playlist creada con el sistema de recomendación')
        self.client.playlist_add_items(pl['id'],ids_playlist_dep)