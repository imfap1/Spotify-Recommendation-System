# Spotify Song Recommender

![Alt text](https://github.com/imfap1/Song-Recommender/blob/main/image/Spotify%20Song%20Recommender.png?raw=true)

## Project Description
This Spotify Recommendation System is a Streamlit-based web application designed to generate personalized music recommendations for Spotify users. The application utilizes Spotify's API to fetch users' top tracks listent the last weak and then recommends new songs based on their listening preferences.

## Workflow

![Alt text](https://github.com/imfap1/Song-Recommender/blob/main/image/workflow.png?raw=true)

## Requisites
- Python 3.6 or higher.
- A Spotify Developer account and a registered Spotify application to obtain the client ID and secret.

## Libraries used
- spotipy
- pandas
- scikit-learn
- numpy
- joblib
- streamlit

## Spotify Recommendation System Interface

![interfaz](https://github.com/imfap1/Song-Recommender/blob/main/image/4.png?raw=true)

The image above displays the user interface of our Spotify Recommendation System. Here's a step-by-step guide on how to use this interface:

Client ID: Enter the Client ID of your registered Spotify application. You can find or create your Spotify Client ID by visiting the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/).

Client Secret: Enter the Client Secret associated with your Client ID. Be cautious as this secret key should remain confidential. The interface will display this information, so it's crucial not to use your primary Spotify credentials.

Username: Input your Spotify username. This is necessary for the system to access your public playlists and recommend songs based on your music taste.

Redirect URI: This should be set to the URI you've registered in your Spotify app settings. The default provided here is http://localhost:8080, which is where the Spotify API will send the authorization code after a successful login.

Warnings:

Credential Security: The interface warns users to be mindful that the client secret will be visible on the screen. Therefore, it's strongly advised not to use your primary Spotify credentials and consider using temporary credentials for added security.

## User's Top Tracks Display

![Alt text](https://github.com/imfap1/Song-Recommender/blob/main/image/6.png?raw=true)

Following successful authentication, as indicated by the "Authentication successful" message at the top, the application retrieves and displays the user's top tracks. This is a crucial step before the recommendation process begins. Here's a breakdown of the displayed data:

Table of Top Tracks: This table is a reflection of the user's listening preferences, serving as the base dataset from which new song recommendations will be generated. It consists of the following columns:

- Artist: Shows the artist of each top track.

- Track Name: The title of the track.

- Album Name: The name of the album for each top track.

- Release Date: The release date of each track.

This data is essential for the recommendation algorithm, which will analyze these top tracks to identify patterns and characteristics that define the user's preferences. Based on this analysis, the system will then look for new songs with similar features to suggest to the user.

## Playlist Creation Confirmation

![Alt text](https://github.com/imfap1/Song-Recommender/blob/main/image/7.png?raw=true)

The displayed message, "Recommended playlist created successfully," signifies the successful generation of the user's personalized Spotify playlist. This confirmation indicates the process is complete, and the user can now access and enjoy their new music selection.

## Generated Playlist Snapshot

![Alt text](https://github.com/imfap1/Song-Recommender/blob/main/image/7.png)

The image showcases the Spotify interface with the generated "Spotify Recommender Playlist." It's a collection curated by our recommendation system, featuring a diverse array of tracks tailored to the user's musical preferences, ready for enjoyment.

## This is how it works

![Alt text](https://github.com/imfap1/Song-Recommender/blob/main/image/ezgif-5-3e174bd2bd.gif?raw=true)

## Steps to use the repository
1. Clone the repository:
   ```
   git clone https://github.com/imfap1/Song-Recommender
   ```
2. Navigate to the project directory:
   ```
   cd spotify_recommender
   ```
3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```
