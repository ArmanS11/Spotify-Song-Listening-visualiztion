import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd
import numpy as np
import plotly.express as px
import streamlit as st
from collections import Counter
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv  # Import dotenv to load .env file

if os.path.exists('.cache'):
    os.remove('.cache')

load_dotenv()

# Spotify API credentials
client_id = os.getenv("SPOTIFY_CLIENT_ID")
client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
redirect_uri = 'http://127.0.0.1:8080/callback'

# Environment error check
if not client_id or not client_secret:
    print("Error: Environment variables are not set correctly.")
else:
    print(f"Client ID: {client_id}")

# Initialize Spotify client
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=client_id,
                                               client_secret=client_secret,
                                               redirect_uri=redirect_uri,
                                               scope=["user-read-recently-played", "user-library-read", "user-read-playback-state", "user-read-currently-playing"]))

# Function to fetch the songs listened to in the last night (24 hours ago)
def fetch_listened_songs():
    # Define the time range (previous 24 hours)
    end_time = datetime.now()
    start_time = end_time - timedelta(days=3)
    
    # Convert to Unix timestamps
    end_timestamp = int(end_time.timestamp())
    start_timestamp = int(start_time.timestamp())

    # Get the songs from the past 24 hours
    results = sp.current_user_recently_played(limit=50)
    songs = []
    
    for item in results['items']:
        played_at = item['played_at']
        played_time = datetime.strptime(played_at.split('.')[0], "%Y-%m-%dT%H:%M:%S")
        
        # Only consider songs played in the last 24 hours
        if played_time.timestamp() >= start_timestamp and played_time.timestamp() <= end_timestamp:
            track = item['track']
            song_name = track['name']
            artist_name = track['artists'][0]['name']
            song_id = track['id']
            
            # Get the genres (if available)
            artist_info = sp.artist(track['artists'][0]['uri'])
            genres = artist_info.get('genres', ['Unknown'])
            
            songs.append({
                'song': song_name,
                'artist': artist_name,
                'genres': genres,
                'played_at': played_time
            })

    return pd.DataFrame(songs)

# Fetch the data
song_data = fetch_listened_songs()

# Data Preprocessing (Extracting Genres and frequency)
genres = [genre for sublist in song_data['genres'] for genre in sublist]
genre_counts = Counter(genres)

# Convert to DataFrame for easy plotting
genre_df = pd.DataFrame(genre_counts.items(), columns=['Genre', 'Count'])

# Streamlit Web App Interface
st.title("Spotify Musical Journey Visualization")
st.subheader("Visualizing Songs Listened to in the Last 72 Hours")

# Genre Filter
genre_filter = st.multiselect(
    "Select Genres to Analyze", 
    genre_df['Genre'].unique().tolist(),
    default=genre_df['Genre'].unique().tolist()
)

# Filter the data based on selected genres
filtered_data = genre_df[genre_df['Genre'].isin(genre_filter)]

# Display the Genre Frequency 3D Plot
fig = px.scatter_3d(filtered_data, x='Genre', y='Count', z='Count', color='Count',
                    title="Genre Frequency of Songs Listened in Last 72 Hours",
                    labels={"Count": "Frequency", "Genre": "Genres"})
st.plotly_chart(fig)

# Frequency Analysis of Songs by Hour
song_data['hour'] = song_data['played_at'].dt.hour
hourly_counts = song_data['hour'].value_counts().sort_index()

# Hour Filter
hour_filter = st.slider(
    "Select Hour Range to Analyze", 
    min_value=0, 
    max_value=71, 
    value=(0, 71), 
    step=1
)

# Filter the hourly data
hourly_filtered_data = pd.DataFrame(hourly_counts.items(), columns=['Hour', 'Count'])
hourly_filtered_data = hourly_filtered_data[(hourly_filtered_data['Hour'] >= hour_filter[0]) & 
                                             (hourly_filtered_data['Hour'] <= hour_filter[1])]

# Display the Hourly Frequency 3D Plot
fig2 = px.scatter_3d(hourly_filtered_data, x='Hour', y='Count', z='Count', color='Count',
                     title="Frequency of Songs Played by Hour",
                     labels={"Count": "Frequency", "Hour": "Hour of Day"})
st.plotly_chart(fig2)

# Display Raw Data of Songs Listened
if st.checkbox('Show raw data of songs listened'):
    st.write(song_data)

# Display Genre Breakdown
st.subheader("Genre Breakdown")
st.write(genre_df)
