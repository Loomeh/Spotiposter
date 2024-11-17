# Spotiposter

> [!NOTE]
> This program was made as part of a college assignment. As a result, I will likely not review any issues or pull requests (unless I feel like coming back to it in the future for whatever reason).

## About
Let your friends know about your awful music taste... \
 \
Spotiposter is a program that grabs whatever song you're currently listening to on Spotify and posts it to Twitter/X and Bluesky.

![rsz_new_project](https://github.com/user-attachments/assets/627b2081-4f27-43b8-bd48-c5a94221af4d) ![rsz_673930b76bde1](https://github.com/user-attachments/assets/0d72b0e9-3731-4eba-923b-b6543db342c1)

## How it works
The Spotiposter script (`main.py`) first authenticates with the Spotify API, the Twitter API and Bluesky and then opens a socket on port `5001` and waits to receive a `b'\x01'` byte from any client. \
Upon receiving said byte, it grabs the track data from Spotify and uploads it to Twitter and Bluesky (with album cover and alt text attached).

An example script for sending the `b'\x01'` byte is included in the repository as `client.py`.

> [!CAUTION]
> As the program accepts data from *any* client with no sort of identity check, it means that anybody on your local network can trigger the script (provided they know your local IP address). Take this into consideration.

## Authentication
Spotify API, Twitter API and Bluesky credentials are read from environment variables, either on the host OS or in a `.env` file. Here are the environment values you need to add:
```
SPOTIFY_CLIENT_ID
SPOTIFY_CLIENT_SECRET
TWITTER_ACCESS_TOKEN
TWITTER_ACCESS_TOKEN_SECRET
TWITTER_CONSUMER_KEY
TWITTER_CONSUMER_SECRET
TWITTER_BEARER_TOKEN
BLUESKY_HANDLE
BLUESKY_PASSWORD
```

## How to run
**Step 1 - Install dependencies**
```
pip install -r requirements.txt
```

**Step 2 - Run script**
```
python main.py
```
