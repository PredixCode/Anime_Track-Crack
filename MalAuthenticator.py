import os
import json
import requests, base64
from datetime import datetime, timedelta

import os
import time
import base64
import requests
import webbrowser
import json
import threading

from datetime import datetime, timedelta
from werkzeug.serving import make_server
from flask import Flask, request as flaskRequest

class TokenGenerator:
    def __init__(self, token_path):
        self.token = None
        self.token_path = token_path
        self.client_id, self.client_secret = self.getClientAuthData('src/auth.json')
        self.stop_event = threading.Event()  # Event to signal when to stop the Flask server

        self.redirect_uri = 'http://localhost:5000/callback'
        self.state = self.generate_state()
        self.code_verifier = self.generate_code_verifier()
        self.code_challenge = self.generate_code_challenge(self.code_verifier)

        self.auth_url = (
            f"https://myanimelist.net/v1/oauth2/authorize?response_type=code"
            f"&client_id={self.client_id}&state={self.state}&redirect_uri={self.redirect_uri}"
            f"&code_challenge={self.code_challenge}&code_challenge_method=plain"
        )

        # Use a separate Flask app for the Token Generator
        self.app = Flask(__name__)
        self.build_flask()
        self.server_thread = None
        self.server = None

    def getClientAuthData(self, auth_file_path):
        with open(auth_file_path, 'r') as f:
            data = json.load(f)
        return data['client_id'], data['client_secret']

    # Start the token generation and authorization flow
    def authenticate(self):
        webbrowser.open(self.auth_url)
        self.run()

    def generate_code_verifier(self):
        code_verifier = base64.urlsafe_b64encode(os.urandom(32)).rstrip(b'=').decode('utf-8')
        return code_verifier

    def generate_code_challenge(self, code_verifier):
        return code_verifier  # Using 'plain' method for PKCE

    def generate_state(self):
        state = base64.urlsafe_b64encode(os.urandom(16)).rstrip(b'=').decode('utf-8')
        return state

    def save_token(self, token):
        with open(self.token_path, 'w') as f:
            json.dump(token, f)

    # Build the Flask app to handle the callback
    def build_flask(self):
        @self.app.route('/')
        def index():
            return 'OAuth 2.0 Authorization Code Grant with PKCE'

        @self.app.route('/login')
        def login():
            return f'<a href="{self.auth_url}">Log in with MyAnimeList</a>'

        @self.app.route('/callback')
        def callback():
            auth_code = flaskRequest.args.get('code')
            if auth_code:
                token_url = "https://myanimelist.net/v1/oauth2/token"
                data = {
                    'client_id': self.client_id,
                    'client_secret': self.client_secret,
                    'grant_type': 'authorization_code',
                    'code': auth_code,
                    'redirect_uri': self.redirect_uri,
                    'code_verifier': self.code_verifier
                }

                headers = {
                    'Content-Type': 'application/x-www-form-urlencoded'
                }

                response = requests.post(token_url, data=data, headers=headers)
                token = response.json()
                self.token = token

                if 'error' not in token:
                    self.save_token(token)
                    self.stop_event.set()  # Signal to stop the Flask server
                    
                    return 'Token obtained and saved. You can close this window now.', 200
                else:
                    return 'Failed to obtain token.', 500
            else:
                return 'Authorization failed.', 500

    def run(self):
        def run_flask():
            self.server = make_server('localhost', 5000, self.app)
            self.server.serve_forever()

        flask_thread = threading.Thread(target=run_flask)
        flask_thread.start()

        # Wait for the stop event to shut down the Flask server
        self.stop_event.wait()
        print("Shutting down the Flask server...")

        # Stop the Flask server
        self.server.shutdown()
        flask_thread.join()


class TokenLoader:
    def __init__(self, tokens_path, auth_file_path='src/auth.json'):
        self.tokens_path = tokens_path
        self.access_token = None
        self.refresh_token = None
        self.expires_at = None
        self.client_id, self.client_secret = self.getClientAuthData(auth_file_path)
        self.load_tokens()

    def getClientAuthData(self, auth_file_path):
        with open(auth_file_path, 'r') as f:
            data = json.load(f)
        return data['client_id'], data['client_secret']

    def load_tokens(self):
        try:
            with open(self.tokens_path, 'r') as file:
                tokens = json.load(file)
                self.access_token = tokens.get('access_token')
                self.refresh_token = tokens.get('refresh_token')
                expires_in = tokens.get('expires_in')
                token_obtained_at = datetime.fromtimestamp(os.path.getmtime(self.tokens_path))
                self.expires_at = token_obtained_at + timedelta(seconds=expires_in)
        except FileNotFoundError:
            pass

    def ensure_valid_tokens(self):
        if self.access_token is None:
            return False
        elif datetime.now() >= self.expires_at:
            # Attempt to refresh the token
            if self.refresh_token:
                return self.refresh_tokens()
            else:
                return False
        else:
            return True

    def refresh_tokens(self):
        token_url = "https://myanimelist.net/v1/oauth2/token"
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'refresh_token',
            'refresh_token': self.refresh_token,
        }

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        response = requests.post(token_url, data=data, headers=headers)
        token = response.json()
        self.token = token

        if 'error' not in token:
            self.save_token(token)
            self.access_token = token.get('access_token')
            self.refresh_token = token.get('refresh_token')
            expires_in = token.get('expires_in')
            self.expires_at = datetime.now() + timedelta(seconds=expires_in)
            return True
        else:
            # Refresh token is invalid or expired
            return False

    def save_token(self, token):
        with open(self.tokens_path, 'w') as f:
            json.dump(token, f)

    def get_headers(self):
        return {
            'Authorization': f'Bearer {self.access_token}'
        }
