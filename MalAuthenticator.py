import os
import base64
import requests
import webbrowser
import json
import threading

from datetime import datetime, timedelta
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

        self.app = Flask(__name__)
        self.build_flask()
        self.server_thread = None
        self.server = None

    def getClientAuthData(self, auth_file_path):
        with open(auth_file_path, 'r') as f:
            data = json.load(f)
        return data['client_id'], data['client_secret']

    # Use this function to start generating the token
    def authenticate(self):
        webbrowser.open(self.auth_url)
        self.run()

    def generate_code_verifier(self):
        code_verifier = base64.urlsafe_b64encode(os.urandom(32)).rstrip(b'=').decode('utf-8')
        return code_verifier

    def generate_code_challenge(self, code_verifier):
        return code_verifier

    def generate_state(self):
        state = base64.urlsafe_b64encode(os.urandom(16)).rstrip(b'=').decode('utf-8')
        return state

    def save_token(self, token):
        with open(self.token_path, 'w') as f:
            json.dump(token, f)

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
                    self.stop_event.set()  # Signal to stop the server
                    return 'Token obtained and saved. You can close this window now.'
                else:
                    return 'Failed to obtain token.'
            else:
                return 'Authorization failed.'

    def run(self):
        from werkzeug.serving import make_server

        def run_flask():
            self.server = make_server('localhost', 5000, self.app)
            self.server.serve_forever()

        flask_thread = threading.Thread(target=run_flask)
        flask_thread.start()

        # Wait for the stop event
        self.stop_event.wait()
        print("Shutting down the Flask server...")

        # Stop the Flask server
        self.server.shutdown()
        flask_thread.join()

class TokenLoader:
    def __init__(self, tokens_path):
        self.tokens_path = tokens_path
        self.login()

    def login(self):
        self.load_tokens()
        self.ensure_valid_tokens()

    def load_tokens(self):
        try:
            with open(self.tokens_path, 'r') as file:
                tokens = json.load(file)
        except FileNotFoundError as e:
            self.refresh_tokens()

        self.access_token = tokens.get('access_token')
        self.refresh_token = tokens.get('refresh_token')

        self.token_creation_time = self.get_access_token_creation_time(self.tokens_path)
        self.expires_at = self.token_creation_time + timedelta(seconds=tokens.get('expires_in'))

    def get_access_token_creation_time(self, path):
        creation_time = os.path.getctime(path)
        return datetime.fromtimestamp(creation_time)
    
    def ensure_valid_tokens(self):
        if datetime.now() >= self.expires_at:
            self.refresh_tokens()
        else:
            print("Tokens are successfully loaded and fresh")
    
    def refresh_tokens(self):
        print("Out of date tokens, refreshing...")
        if os.path.exists(self.tokens_path):
            os.remove(self.tokens_path)

        TokenGenerator(self.tokens_path).authenticate()

    def isAccessTokenValid(self):
        creation_time = os.path.getctime(self.tokens_path)
        datetime.fromtimestamp(creation_time)

    def get_headers(self):
        return {
            'Authorization': f'Bearer {self.access_token}'
        }

# EXAMPLE USAGE
if __name__ == "__main__":
    token_path = 'src/tokens.json'
    client_id = '23490afihawfn924urohwrq80wpwf4irmqof75r'
    client_secret = 'awuf3ghq08fhjq29pjf76oiha8oihgfjwp0k045tgtj8678ap9hfba'
    generator = TokenGenerator(client_id, client_secret, token_path)
    generator.authenticate()
    print(generator.token)
