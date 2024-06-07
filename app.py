import streamlit as st
import spotipy
import openai
from openai import OpenAI
from spotipy.oauth2 import SpotifyOAuth
from collections import Counter
import lyricsgenius
import logging
from dotenv import load_dotenv
import os
import pandas as pd

st.set_page_config(layout="wide")

load_dotenv()

# Load environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")
GENIUS_ACCESS_TOKEN = os.getenv("GENIUS_ACCESS_TOKEN")

scope = "user-top-read"
auth_manager = SpotifyOAuth(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET,
    redirect_uri=SPOTIFY_REDIRECT_URI,
    scope=scope,
)

# Create an instance of the Genius API client
genius = lyricsgenius.Genius(GENIUS_ACCESS_TOKEN)

# Create a placeholder for the lyrics analysis
analysis_placeholder = st.empty()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_lyrics(song_title, artist_name):
    try:
        song = genius.search_song(song_title, artist_name)
        if song:
            return song.lyrics
    except Exception as e:
        st.write(f"Error retrieving lyrics: {str(e)}")
    return None

# Get top tracks in the US
def get_top_tracks(sp):
    top_tracks = sp.playlist_tracks("spotify:playlist:37i9dQZEVXbLRQDuF5jeBp", limit=10)
    return top_tracks["items"]

def get_top_artists(sp):
    # Since the Spotify API doesn't have a direct endpoint for global top artists,
    # this is approximated using the top tracks.
    top_tracks = sp.playlist_tracks("spotify:playlist:37i9dQZEVXbLRQDuF5jeBp", limit=100)
    all_artists = [track['track']['artists'] for track in top_tracks['items']]
    artist_freq = Counter([artist['name'] for sublist in all_artists for artist in sublist])
    top_artists = [sp.search(q=f'artist:{artist}', type='artist', limit=1)['artists']['items'][0] for artist, _ in
                   artist_freq.most_common(10)]
    return top_artists

def analyze_lyrics_with_openai(lyrics, prompt):
    try:
        client = OpenAI(api_key=openai.api_key)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that analyzes song lyrics."},
                {"role": "user", "content": f"{prompt}\n\nLyrics:\n{lyrics}"}
            ],
            max_tokens=550,
            n=1,
            stop=None,
            temperature=0.7,
        )
        analysis = response.choices[0].message.content.strip()
        logger.info(f"OpenAI API response: {response}")
        return analysis
    except Exception as e:
        logger.error(f"Error analyzing lyrics with OpenAI: {str(e)}")
        st.write(f"Error analyzing lyrics with OpenAI: {str(e)}")
        return None

def main():
    st.title("Spotify Analyzer")

    if not auth_manager.cache_handler.get_cached_token():
        auth_url = auth_manager.get_authorize_url()

        # Create a button link in the sidebar
        st.sidebar.markdown(
            f'<a href="{auth_url}" target="_blank"><button style="background-color: #1DB954; color: white; border: none; padding: 10px 20px; text-align: center; text-decoration: none; display: inline-block; font-size: 16px; margin: 4px 2px; cursor: pointer;">Authenticate with Spotify</button></a>',
            unsafe_allow_html=True)

        # Place the input box in the first column of the sidebar
        response_url = st.text_input("", value="", max_chars=None, key=None, type="default", help=None,
                                     autocomplete=None, on_change=None, args=None, kwargs=None,
                                     placeholder="Paste the Response URL", disabled=False)

        if response_url:
            try:
                code = auth_manager.parse_response_code(response_url)
                token_info = auth_manager.get_access_token(code, check_cache=False)

                # Check if token_info is a dictionary and contains 'access_token'
                if isinstance(token_info, dict) and 'access_token' in token_info:
                    access_token = token_info['access_token']
                else:
                    access_token = token_info

                auth_manager.cache_handler.save_token_to_cache({"access_token": access_token})
                st.rerun()

            except Exception as e:
                st.error("Authentication failed. Please check your Spotify credentials and try again.")
                st.write(e)  # Display the error message

    else:  # User is authenticated
        token_info = auth_manager.cache_handler.get_cached_token()
        sp = spotipy.Spotify(auth_manager=auth_manager)

        # Get Top Data
        results = {}
        for term in ['medium_term']:
            results[term] = {}
            results[term]['top_tracks'] = sp.current_user_top_tracks(time_range=term, limit=10)['items']
            results[term]['top_artists'] = sp.current_user_top_artists(time_range=term, limit=10)['items']

        # Display Results
        st.header('Personal Top Tracks & Artists',divider='rainbow')

        # Create columns for the personal track list and analysis results with custom widths
        col3, col4 = st.columns(2)  # Adjust the width ratio as needed

        with col3:
            with st.expander("Top Tracks"):
                for track in results['medium_term']['top_tracks']:
                    track_name = track['name']
                    artist_name = track['artists'][0]['name']

                    # Create columns for the track info and analyze button
                    track_col, button_col = st.columns([4, 1])

                    with track_col:
                        st.write(f"{track_name} - {artist_name}")

                    with button_col:
                        if st.button(f"Analyze", key=f"personal_{track_name}"):
                            analyze_track_lyrics(track_name, artist_name, analysis_placeholder)

        with col3:
            with st.expander("Top Artists"):
                personal_top_artists = results['medium_term']['top_artists']
                for artist in personal_top_artists:
                    st.subheader(artist['name'])
                    st.write(f"**Genres:** {', '.join(artist['genres'])}")
                    st.write(f"**Popularity:** {artist['popularity']}")
                    st.write(f"**Followers:** {artist['followers']['total']}")

                # Create a DataFrame for personal top artists' popularity
                personal_artist_data = {
                    'Artist': [artist['name'] for artist in personal_top_artists],
                    'Popularity': [artist['popularity'] for artist in personal_top_artists]
                }
                df_personal_artists = pd.DataFrame(personal_artist_data)
                df_personal_artists = df_personal_artists.sort_values('Popularity', ascending=False)

                # Display explanation message
                st.header('Popularity',divider='rainbow')
                st.write("The artist's popularity is calculated from the popularity of all the artist's tracks.")
                st.write("The popularity score is based on several factors, including:")
                st.write("- The total number of plays the artist has had across all their tracks.")
                st.write("- How recent those plays are.")
                st.write("- The number of positive and negative ratings the artist's tracks have received from users.")
        with col4:
            # Create a bar chart for personal top artists' popularity
            st.bar_chart(data=df_personal_artists, x='Artist', y='Popularity', width=600, height=400)

        # Display top tracks and playlists (unauthenticated)
        st.header('Global Top Tracks & Artists',divider='rainbow')

        # Create columns for the track list and analysis results
        col1, col2 = st.columns(2)

        with col1:
            top_tracks = get_top_tracks(sp)
            with st.expander("Top Tracks"):
                for track in top_tracks:
                    track_name = track['track']['name']
                    artist_name = track['track']['artists'][0]['name']

                    # Create columns for the track info and analyze button
                    track_col, button_col = st.columns([4, 1])

                    with track_col:
                        st.write(f"{track_name} - {artist_name}")

                    with button_col:
                        if st.button(f"Analyze", key=f"global_{track_name}"):
                            lyrics = get_lyrics(track_name, artist_name)
                            if lyrics:
                                prompt = (
                                    "Analyze the following lyrics and provide insights about the song's theme, "
                                    "emotions, and any figurative language used. Limit the analysis to two paragraphs. State your analysis without ever referring to the prompter."
                                )
                                analysis = analyze_lyrics_with_openai(lyrics, prompt)
                                if analysis:
                                    with col2:
                                        st.subheader("Analysis Results")
                                        st.write(f"**Track:** {track_name}")
                                        st.write(f"**Artist:** {artist_name}")
                                        st.write(analysis)
                            else:
                                st.write(f"Lyrics not found for {track_name} - {artist_name}")
        with col1:
            with st.expander("Top Artists"):
                top_artists = get_top_artists(sp)
                for artist in top_artists:
                    st.subheader(artist['name'])
                    st.write(f"**Genres:** {', '.join(artist['genres'])}")
                    st.write(f"**Popularity:** {artist['popularity']}")
                    st.write(f"**Followers:** {artist['followers']['total']}")

                # Create a DataFrame for top artists' popularity
                artist_data = {
                    'Artist': [artist['name'] for artist in top_artists],
                    'Popularity': [artist['popularity'] for artist in top_artists]
                }
                df_artists = pd.DataFrame(artist_data)
                df_artists = df_artists.sort_values('Popularity', ascending=False)

                # Display explanation message
                st.header('Popularity', divider='rainbow')
                st.write("The artist's popularity is calculated from the popularity of all the artist's tracks.")
                st.write("The popularity score is based on several factors, including:")
                st.write("- The total number of plays the artist has had across all their tracks.")
                st.write("- How recent those plays are.")
                st.write("- The number of positive and negative ratings the artist's tracks have received from users.")

        with col2:
            # Create a bar chart for top artists' popularity
            st.bar_chart(data=df_artists, x='Artist', y='Popularity', width=600, height=400)

def analyze_track_lyrics(track_name, artist_name, placeholder):
    lyrics = get_lyrics(track_name, artist_name)
    if lyrics:
        prompt = (
            "Analyze the following lyrics and provide insights about the song's theme, "
            "emotions, and any figurative language used. Limit the analysis to two paragraphs. State your analysis without ever referring to the prompter."
        )
        analysis = analyze_lyrics_with_openai(lyrics, prompt)
        if analysis:
            with placeholder.container():
                st.subheader("Analysis Results")
                st.write(f"**Track:** {track_name}")
                st.write(f"**Artist:** {artist_name}")
                st.write(analysis)
    else:
        with placeholder.container():
            st.write(f"Lyrics not found for {track_name} - {artist_name}")

if __name__ == "__main__":
    main()
