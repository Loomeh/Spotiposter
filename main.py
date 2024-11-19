from dotenv import load_dotenv
from os import getenv, path
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import tweepy
import socket
import sys
import requests
import atproto
from io import BytesIO, BufferedReader
from PIL import Image

# Check if .env file exists
if path.isfile(".env"):
    load_dotenv()
    print("Loaded .env file!")

def setup_spotify():
    try:
        spotify_scope = 'user-read-currently-playing user-read-playback-state'
        sp = spotipy.Spotify(
            auth_manager=SpotifyOAuth(
                client_id=getenv("SPOTIFY_CLIENT_ID"),
                client_secret=getenv("SPOTIFY_CLIENT_SECRET"),
                redirect_uri="http://localhost:5000/callback",
                scope=spotify_scope,
                open_browser=False
            )
        )
        return sp
    except Exception as e:
        print(f"Error setting up Spotify: {e}")
        sys.exit(1)

def setup_twitter_client():
    try:
        twt_client = tweepy.Client(
            bearer_token=getenv("TWITTER_BEARER_TOKEN"),
            consumer_key=getenv("TWITTER_CONSUMER_KEY"),
            consumer_secret=getenv("TWITTER_CONSUMER_SECRET"),
            access_token=getenv("TWITTER_ACCESS_TOKEN"),
            access_token_secret=getenv("TWITTER_ACCESS_TOKEN_SECRET"),
            wait_on_rate_limit=True
        )
        return twt_client
    except Exception as e:
        print(f"Error setting up Twitter client: {e}")
        sys.exit(1)

def setup_twitter_api():
    try:
        auth = tweepy.OAuthHandler(getenv("TWITTER_CONSUMER_KEY"), getenv("TWITTER_CONSUMER_SECRET"))
        auth.set_access_token(getenv("TWITTER_ACCESS_TOKEN"), getenv("TWITTER_ACCESS_TOKEN_SECRET"))
        twitter_api = tweepy.API(auth)
        return twitter_api
    except Exception as e:
        print(f"Error setting up Twitter API: {e}")
        sys.exit(1)

def setup_bluesky():
    try:
        bsky_client = atproto.Client()
        bsky_profile = bsky_client.login(getenv('BLUESKY_HANDLE'), getenv('BLUESKY_PASSWORD'))
        print('Logged into Bluesky as: ', bsky_profile.display_name)
        return bsky_client
    except Exception as e:
        print(f"Error setting up Bluesky: {e}")
        sys.exit(1)

def main():
    # Initialize APIs
    sp = setup_spotify()
    twt_client= setup_twitter_client()
    twt_api = setup_twitter_api()
    bsky_client = setup_bluesky()
    
    # Set up TCP Server
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server_socket.bind(("127.0.0.1", 5001))
        server_socket.listen(1)
        print("Server listening on 127.0.0.1:5001")
        
        # Main loop
        while True:
            try:
                conn, addr = server_socket.accept()
                with conn:
                    print(f"Connected by {addr}")
                    while True:
                        data = conn.recv(1)
                        if not data:
                            break
                        if data == b'\x01':
                            print("Update signal received!")
                            # Get currently playing track
                            data = sp.currently_playing()

                            if data and "item" in data:
                                track = data["item"]
                                album = data["item"]["album"]
                                track_name = track.get("name", "Unknown track")
                                artist_name = ", ".join(artist["name"] for artist in track["artists"])
                                album_name = album["name"]
                                image_url = next((img["url"] for img in album["images"] if img["height"] == 640 and img["width"] == 640), None)

                                track_timestamp = data["progress_ms"]

                                con_sec, con_min = convertMillis(int(track_timestamp))

                                post_text = f"Currently playing: '{track_name}' by {artist_name} ({con_min:02d}:{con_sec:02d})\n\n(𝘈𝘶𝘵𝘰𝘮𝘢𝘵𝘦𝘥 𝘗𝘰𝘴𝘵)"
                                alt_text = f"Album cover for '{album_name}' by {next((artist["name"] for artist in album["artists"]), None)}."

                                # Download album cover from Spotify and save into memory
                                r = requests.get(image_url).content
                                cover_img = Image.open(BytesIO(r))
                                buf = BytesIO()
                                cover_img.save(buf, "PNG")
                                buf.seek(0)
                                cover_fp = BufferedReader(buf)

                                # Bluesky upload
                                bsky_client.send_image(post_text, cover_fp, image_alt=alt_text)
                                print("Uploaded to Bluesky!")
                                
                                # Twitter upload
                                cover = twt_api.media_upload(filename='DUMMY', file=cover_fp)
                                cover_mID = cover.media_id
                                print("Uploaded cover!")
                                twt_api.create_media_metadata(cover_mID, alt_text=alt_text)
                                print("Created metadata!")
                                twt_client.create_tweet(text=post_text, media_ids=[cover_mID])
                                print("Created tweet!")
                                
                            else:
                                print("No track is currently playing.")
                            break
            except socket.error as e:
                print(f"Socket error: {e}")
                continue
            except Exception as e:
                print(f"Unexpected error: {e}")
                continue
    except Exception as e:
        print(f"Error: {e}")
    finally:
        server_socket.close()


# Helper functions
def convertMillis(millis):
    seconds=int(millis/1000)%60
    minutes=int(millis/(1000*60))%60
    return seconds, minutes

if __name__ == "__main__":
    main()