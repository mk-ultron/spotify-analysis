# Spotify Analyzer

The Spotify Analyzer is a Streamlit application that allows users to analyze their personal top tracks and artists, as well as explore the global top tracks and artists. It integrates with the Spotify API to retrieve user data, the Genius API to fetch song lyrics, and the OpenAI API to provide insights and analysis of the lyrics.

## Features

- User authentication with Spotify
- Retrieval of personal top tracks and artists
- Display of global top tracks and artists
- Lyrics retrieval for selected tracks
- Lyrics analysis using OpenAI's language model
- Data visualization of artist popularity scores
- User-friendly interface with interactive components

## Project Dependencies

The Spotify Analyzer relies on the following dependencies and platforms:

- Python 3.7+
- Streamlit
- Spotipy
- OpenAI
- Genius
- python-dotenv
- Pandas

## Installation

1. Clone the repository:

   ```
   git clone https://github.com/yourusername/spotify-analyzer.git
   ```

2. Navigate to the project directory:

   ```
   cd spotify-analyzer
   ```

3. Install the required dependencies:

   ```
   pip install -r requirements.txt
   ```

4. Set up the necessary API credentials:

   - Create a Spotify Developer account and register a new application to obtain the client ID, client secret, and redirect URI.
   - Sign up for an OpenAI API key.
   - Obtain a Genius API access token.

5. Create a `.env` file in the project root and add the following environment variables:

   ```
   OPENAI_API_KEY=your_openai_api_key
   SPOTIFY_CLIENT_ID=your_spotify_client_id
   SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
   SPOTIFY_REDIRECT_URI=your_spotify_redirect_uri
   GENIUS_ACCESS_TOKEN=your_genius_access_token
   ```

   Replace the placeholders with your actual API credentials.

## Usage

1. Run the Streamlit application:

   ```
   streamlit run app.py
   ```

2. Open the provided URL in your web browser.
3. Click on the "Authenticate with Spotify" button to initiate the authentication process.
4. Follow the authentication flow and grant the necessary permissions.
5. Once authenticated, the application will display your personal top tracks and artists.
6. Explore the global top tracks and artists sections.
7. Click on the "Analyze" button next to a track to retrieve its lyrics and get insights from the OpenAI API.
8. Interact with the data visualizations to gain a better understanding of artist popularity.

## Contributing

Contributions to the Spotify Analyzer project are welcome! If you find any bugs, have suggestions for improvements, or would like to add new features, please open an issue or submit a pull request.

## Acknowledgements

The Spotify Analyzer project makes use of the following APIs and libraries:
- [Spotify API](https://developer.spotify.com/)
- [Genius API](https://docs.genius.com/)
- [OpenAI API](https://openai.com/)
- [Streamlit](https://streamlit.io/)
- [Spotipy](https://spotipy.readthedocs.io/)
- [python-dotenv](https://github.com/theskumar/python-dotenv)

Special thanks to the developers and communities behind these tools for their valuable contributions.
