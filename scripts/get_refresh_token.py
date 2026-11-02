"""One-time helper: obtain a YouTube OAuth refresh token for the channel owner.

Run it on your own computer (not in CI):

    pip install google-auth-oauthlib
    python scripts/get_refresh_token.py

It asks for the OAuth client ID and secret (or reads YT_CLIENT_ID / YT_CLIENT_SECRET
from the environment), opens a browser for consent, and PRINTS the refresh token.
Nothing is written to disk. Copy the token into the GitHub secret YT_REFRESH_TOKEN.
"""
from __future__ import annotations

import os
from getpass import getpass

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",
]


def main() -> None:
    client_id = os.environ.get("YT_CLIENT_ID") or input("OAuth client ID: ").strip()
    client_secret = os.environ.get("YT_CLIENT_SECRET") or getpass("OAuth client secret (hidden): ").strip()
    config = {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost"],
        }
    }
    flow = InstalledAppFlow.from_client_config(config, SCOPES)
    creds = flow.run_local_server(port=0, access_type="offline", prompt="consent")
    if not creds.refresh_token:
        raise SystemExit("No refresh token returned. Remove the app's access at "
                         "https://myaccount.google.com/permissions and run again.")
    print("\nRefresh token (store it as the GitHub secret YT_REFRESH_TOKEN, do not commit it):\n")
    print(creds.refresh_token)


if __name__ == "__main__":
    main()
