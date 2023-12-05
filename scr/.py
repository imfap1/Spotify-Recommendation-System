from spotipyclient_ import SpotipyClient


client_id = "dd47dbfc5ec3421d98bfb9eac3b78510"
client_secret = "546f24c41f3146d4b806331aa8bddee7"
username = "31yxuvapn3lfzdhax4es457pyutq"
redirect_uri = "http://localhost:8080"
scope = 'user-top-read playlist-modify-public playlist-modify-private'

sp_client = SpotipyClient(client_id, client_secret, username, redirect_uri, scope)

sp_client.authenticate_spotify()

top_tracks = sp_client.get_top_tracks()

top_tracks_df = sp_client.create_tracks_dataframe(top_tracks)

ids_artists = sp_client.get_artists_ids(top_tracks)

ids_artists = sp_client.get_similar_artists_ids(ids_artists)

ids_artists = sp_client.get_new_releases_artists_ids(ids_artists)

ids_albums = sp_client.get_albums_ids(ids_artists)

ids_tracks = sp_client.get_albums_tracks(ids_albums)

candidates_df = sp_client.get_tracks_features(ids_tracks)

cos_sim = sp_client.compute_cossim(top_tracks_df, candidates_df)

sp_client.create_recommended_playlist()
