import streamlit as st
from functools import lru_cache
import spotipy
import openai
from openai import OpenAI
from spotipy.oauth2 import SpotifyOAuth
from collections import Counter
import lyricsgenius
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
import logging
from dotenv import load_dotenv
import os

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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Download required NLTK resources
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')


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
    top_tracks = sp.playlist_tracks("spotify:playlist:37i9dQZEVXbLRQDuF5jeBp", limit=100)  # Fetch more tracks
    all_artists = [track['track']['artists'] for track in top_tracks['items']]
    artist_freq = Counter([artist['name'] for sublist in all_artists for artist in sublist])
    return artist_freq.most_common(10)


def preprocess_lyrics(lyrics):
    # Tokenize the lyrics
    words = word_tokenize(lyrics)
    # Convert to lowercase
    words = [word.lower() for word in words]
    # Remove stopwords
    stop_words = set(stopwords.words("english"))
    words = [word for word in words if word not in stop_words]
    # Lemmatize the words
    lemmatizer = WordNetLemmatizer()
    words = [lemmatizer.lemmatize(word) for word in words]
    return words


@lru_cache(maxsize=None)
def analyze_lyrics_with_openai(lyrics, prompt):
    try:
        client = OpenAI(api_key=openai.api_key)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that analyzes song lyrics."},
                {"role": "user", "content": f"{prompt}\n\nLyrics:\n{lyrics}"}
            ],
            max_tokens=250,
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
    st.set_page_config(layout="wide")
    st.title("Spotify Analyzer")

    if not auth_manager.cache_handler.get_cached_token():
        auth_url = auth_manager.get_authorize_url()

        # Create a button link in the sidebar
        st.sidebar.markdown(
            f'<a href="{auth_url}" target="_blank"><button style="background-color: #1DB954; color: white; border: none; padding: 10px 20px; text-align: center; text-decoration: none; display: inline-block; font-size: 16px; margin: 4px 2px; cursor: pointer;">Authenticate with Spotify</button></a>',
            unsafe_allow_html=True)

        # Create a sidebar column with a width of 33%
        sidebar_col = st.sidebar.columns(3)

        # Place the input box in the first column of the sidebar
        response_url = st.text_input("", value="", max_chars=None, key=None, type="default", help=None,
                                     autocomplete=None, on_change=None, args=None, kwargs=None,
                                     placeholder="Paste the Response URL", disabled=False)

        if response_url:
            try:
                code = auth_manager.parse_response_code(response_url)
                token_info = auth_manager.get_access_token(code, check_cache=False)
                auth_manager.cache_handler.save_token_to_cache(token_info)
                st.experimental_rerun()

            except Exception as e:
                st.error("Authentication failed. Please check your Spotify credentials and try again.")
                st.write(e)  # Display the error message

    else:  # User is authenticated
        token_info = auth_manager.cache_handler.get_cached_token()
        sp = spotipy.Spotify(auth_manager=auth_manager)

        # Display top tracks and playlists (unauthenticated)
        st.title("Global Top Tracks & Artists")

        # Create columns for the track list and analysis results
        col1, col2 = st.columns([2, 3])

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
                                    "emotions, and any figurative language used. Limit the analysis to two paragraphs"
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

        with st.expander("Top Artists"):
            top_artists = get_top_artists(sp)
            for i, (artist, count) in enumerate(top_artists):
                st.write(f"{i + 1}. {artist}")

        # Get Top Data
        results = {}
        for term in ['short_term', 'medium_term']:
            results[term] = {}
            results[term]['top_tracks'] = sp.current_user_top_tracks(time_range=term, limit=10)['items']
            results[term]['top_artists'] = sp.current_user_top_artists(time_range=term, limit=10)['items']

        # Display Results
        st.title("Personal Top Tracks & Artists")

        # Create columns for the personal track list and analysis results with custom widths
        col3, col4 = st.columns([2, 3])  # Adjust the width ratio as needed

        with col3:
            with st.expander("Top Tracks"):
                for track in results['short_term']['top_tracks']:
                    track_name = track['name']
                    artist_name = track['artists'][0]['name']

                    # Create columns for the track info and analyze button
                    track_col, button_col = st.columns([4, 1])

                    with track_col:
                        st.write(f"{track_name} - {artist_name}")

                    with button_col:
                        if st.button(f"Analyze", key=f"personal_{track_name}"):
                            analyze_track_lyrics(track_name, artist_name, col4)

        with st.expander("Top Artists"):
            for artist in results['short_term']['top_artists']:
                st.write(artist['name'])


def analyze_track_lyrics(track_name, artist_name, col):
    lyrics = get_lyrics(track_name, artist_name)
    if lyrics:
        prompt = (
            "Analyze the following lyrics and provide insights about the song's theme, "
            "emotions, and any figurative language used. Limit the analysis to two paragraphs"
        )
        analysis = analyze_lyrics_with_openai(lyrics, prompt)
        if analysis:
            with col:
                st.subheader("Analysis Results")
                st.write(f"**Track:** {track_name}")
                st.write(f"**Artist:** {artist_name}")
                st.write(analysis)
    else:
        st.write(f"Lyrics not found for {track_name} - {artist_name}")


if __name__ == "__main__":
    main()
