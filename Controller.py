import io, time, m3u8, os
import webbrowser
import threading
import logging
import requests
from datetime import datetime, timedelta

from flask import Flask, Response, request, session, redirect, url_for, stream_with_context, jsonify, render_template, g
from flask_session import Session
from werkzeug.serving import make_server

from MalAuthenticator import TokenGenerator, TokenLoader
from MalRequester import Requester
from AnimeScrape.VideoDownloader import VideoDownloader
from AnimeScrape.AnimeScraper import AnimeScraper


class AnimeController:
    logging.basicConfig(level=logging.info)

    def __init__(self):
        self.scraper = AnimeScraper()
        self.downloader = VideoDownloader()
        self.server = None
        self.app = Flask(__name__, template_folder='templates', static_folder='webapp/static')
        self.token_path = 'src/tokens.json'

        # Configure session
        self.app.secret_key = '3a4d8f5b6c9e827a0b9d7c8f3e5d1f8a2b4c6d8e9f7b3a1d5e7f9c0b8a1d2c3'
        self.app.config['SESSION_TYPE'] = 'filesystem' 
        self.app.config['SESSION_FILE_DIR'] = 'flask_session/'
        self.app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=100)
        Session(self.app)

        self.requesters = {}  # Store Requester objects per user
        self.build_flask()
        threading.Thread(target=self.run_flask).start()


    def proxy_ts_segment(self, segment_url):
        """
        Proxies the .ts segment to the client.
        """
        try:
            headers = {}  # Add any required headers here

            # Stream the content to the client
            req = requests.get(segment_url, headers=headers, stream=True)

            return Response(stream_with_context(req.iter_content(chunk_size=8192)), content_type=req.headers['Content-Type'])
        except Exception as e:
            logging.error(f"Error proxying segment {segment_url}: {e}")
            return str(e), 500
        

    def build_flask(self):
        @self.app.before_request
        def load_requester():
            if 'user_id' in session:
                user_id = session['user_id']
                g.user_id = user_id
                g.requester = self.requesters.get(user_id)
            else:
                g.user_id = None
                g.requester = None

        @self.app.route('/')
        def index():
            if 'user_id' not in session:
                session['user_id'] = os.urandom(8).hex()
            user_id = session['user_id']

            if 'tokens' not in session:
                return redirect(url_for('login'))

            tokens = session['tokens']
            tokens_loader = TokenLoader()
            tokens_loader.access_token = tokens['access_token']
            tokens_loader.refresh_token = tokens['refresh_token']
            tokens_loader.expires_at = tokens['expires_at']
            tokens_loader.client_id = tokens['client_id']
            tokens_loader.client_secret = tokens['client_secret']

            if not tokens_loader.ensure_valid_tokens():
                return redirect(url_for('login'))

            # Update tokens in session
            session['tokens']['access_token'] = tokens_loader.access_token
            session['tokens']['refresh_token'] = tokens_loader.refresh_token
            session['tokens']['expires_at'] = tokens_loader.expires_at

            if user_id not in self.requesters:
                requester = Requester(tokens_loader=tokens_loader)
                self.requesters[user_id] = requester
            else:
                requester = self.requesters[user_id]

            g.requester = requester
            return render_template('index.html')

        @self.app.route('/login')
        def login():
            # Step 1: Start the token generation flow
            token_generator = TokenGenerator()
            auth_url = token_generator.get_auth_url()

            # Step 2: Redirect the user to the authorization URL
            session['state'] = token_generator.state
            session['code_verifier'] = token_generator.code_verifier
            session['client_id'] = token_generator.client_id
            session['client_secret'] = token_generator.client_secret

            # Open the authorization URL in the user's browser
            webbrowser.open(auth_url)

            # Step 3: Wait for the token generator to complete (in a separate thread)
            token = token_generator.run()  # This will block until the token is generated

            # Step 4: Once the token is obtained, store it in the session
            if token:
                session['tokens'] = {
                    'access_token': token['access_token'],
                    'refresh_token': token.get('refresh_token'),
                    'expires_at': datetime.now() + timedelta(seconds=token['expires_in']),
                    'client_id': token_generator.client_id,
                    'client_secret': token_generator.client_secret
                }
                logging.info(f"Session with token successfully esthablished. Details: {session['tokens']}")
                return redirect(url_for('index'))
            else:
                return "Failed to log in.", 500

        @self.app.route('/callback')
        def callback():
            error = request.args.get('error')
            if error:
                return f'Error: {error}', 400

            state = request.args.get('state')
            if state != session.get('state'):
                return 'Invalid state parameter', 400

            code = request.args.get('code')
            if not code:
                return 'Authorization failed.', 400

            code_verifier = session.get('code_verifier')
            client_id = session.get('client_id')
            client_secret = session.get('client_secret')

            token_generator = TokenGenerator(self.token_path)
            token_generator.code_verifier = code_verifier
            token_generator.client_id = client_id
            token_generator.client_secret = client_secret

            token = token_generator.get_token(code)

            session['tokens'] = {
                'access_token': token['access_token'],
                'refresh_token': token.get('refresh_token'),
                'expires_at': datetime.now() + timedelta(seconds=token['expires_in']),
                'client_id': client_id,
                'client_secret': client_secret
            }

            return redirect(url_for('index'))
        
        @self.app.route('/api/save_playback_time', methods=['POST'])
        def save_playback_time():
            data = request.get_json()
            malAnimeId = str(data.get('malAnimeId'))
            episodeNumber = str(data.get('episodeNumber'))
            currentTime = data.get('currentTime')

            if not all([malAnimeId, episodeNumber, currentTime is not None]):
                return jsonify({'error': 'Missing data fields.'}), 400

            key = f"watched_{malAnimeId}_{episodeNumber}"
            session[key] = currentTime
            return jsonify({'message': 'Playback time saved.'}), 200

        @self.app.route('/api/get_playback_time', methods=['GET'])
        def get_playback_time():
            malAnimeId = request.args.get('malAnimeId')
            episodeNumber = request.args.get('episodeNumber')

            if not all([malAnimeId, episodeNumber]):
                return jsonify({'error': 'Missing query parameters.'}), 400

            key = f"watched_{malAnimeId}_{episodeNumber}"
            currentTime = session.get(key)

            if currentTime is not None:
                return jsonify({'currentTime': currentTime}), 200
            else:
                return jsonify({'currentTime': None}), 200

        @self.app.route('/api/remove_playback_time', methods=['POST'])
        def remove_playback_time():
            data = request.get_json()
            malAnimeId = str(data.get('malAnimeId'))
            episodeNumber = str(data.get('episodeNumber'))

            if not all([malAnimeId, episodeNumber]):
                return jsonify({'error': 'Missing data fields.'}), 400

            key = f"watched_{malAnimeId}_{episodeNumber}"
            session.pop(key, None)
            return jsonify({'message': 'Playback time removed.'}), 200

        @self.app.route('/api/save_last_watched', methods=['POST'])
        def save_last_watched():
            data = request.get_json()
            malAnimeId = str(data.get('malAnimeId'))
            episodeNumber = data.get('episodeNumber')

            if not all([malAnimeId, episodeNumber]):
                return jsonify({'error': 'Missing data fields.'}), 400

            key = f"last_watched_{malAnimeId}"
            session[key] = {
                'episodeNumber': episodeNumber,
                'timestamp': int(time.time() * 1000)  # Unix timestamp in milliseconds
            }
            return jsonify({'message': 'Last watched episode saved.'}), 200

        @self.app.route('/api/get_last_watched', methods=['GET'])
        def get_last_watched():
            malAnimeId = request.args.get('malAnimeId')

            if not malAnimeId:
                return jsonify({'error': 'Missing malAnimeId parameter.'}), 400

            key = f"last_watched_{malAnimeId}"
            last_watched = session.get(key)

            if last_watched:
                return jsonify({'lastWatched': last_watched}), 200
            else:
                return jsonify({'lastWatched': None}), 200

        @self.app.route('/api/clear_last_watched', methods=['POST']) #TODO: Implement in frontend when user decline 'resume last watched alert'.
        def clear_last_watched():
            data = request.get_json()
            malAnimeId = str(data.get('malAnimeId'))

            if not malAnimeId:
                return jsonify({'error': 'Missing malAnimeId field.'}), 400

            key = f"last_watched_{malAnimeId}"
            session.pop(key, None)
            return jsonify({'message': 'Last watched episode cleared.'}), 200

        @self.app.route('/api/get_last_watched_all', methods=['GET'])
        def get_last_watched_all():
            """
            Retrieves all last watched episodes from the session.
            """
            last_watched = {}
            for key in session:
                if key.startswith('last_watched_'):
                    malAnimeId = key.replace('last_watched_', '')
                    last_watched[malAnimeId] = session[key]
            return jsonify({'lastWatched': last_watched}), 200
        
        @self.app.route('/api/get_episode_data/<int:mal_anime_id>/<int:episode_number>', methods=['GET'])
        def get_episode_data(mal_anime_id, episode_number):
            """
            Retrieves both available episodes and the next airing date for a specific anime and episode.

            Parameters:
                mal_anime_id (int): The MyAnimeList (MAL) ID of the anime.
                episode_number (int): The episode number.

            Returns:
                JSON response containing 'availableEpisodes' and 'nextAiringDate'.
            """
            try:
                episode_data = self.scraper.get_episode_data(mal_anime_id)
                available_episodes = episode_data.get('availableEpisodes', [])
                next_airing_date = episode_data.get('nextAiringDate')

                # Save available episodes to session
                available_key = f"available_episodes_{mal_anime_id}"
                session[available_key] = available_episodes

                # Save next airing date to session
                if next_airing_date:
                    airing_key = f"next_airing_{mal_anime_id}_{episode_number}"
                    session[airing_key] = next_airing_date  # ISO format string
                else:
                    airing_key = f"next_airing_{mal_anime_id}_{episode_number}"
                    session.pop(airing_key, None)  # Remove if exists

                return jsonify({
                    'availableEpisodes': available_episodes,
                    'nextAiringDate': next_airing_date
                }), 200

            except Exception as e:
                logging.error(f"Error in get_episode_data API: {e}", exc_info=True)
                return jsonify({'error': 'Internal Server Error'}), 500
            
        from flask import jsonify, session

        @self.app.route('/api/get_all_episode_data', methods=['GET'])
        def get_all_episode_data():
            """
            Retrieves all the session data stored by the controller function.

            Returns:
                JSON response containing all stored 'availableEpisodes' and 'nextAiringDate' data.
            """
            try:
                all_episode_data = {}

                # Iterate over all session keys to find stored episodes and airing dates
                for key in session.keys():
                    if key.startswith("available_episodes_"):
                        anime_id = key.split("_")[-1]
                        all_episode_data[f"available_episodes_{anime_id}"] = session[key]

                    elif key.startswith("next_airing_"):
                        anime_id_episode = "_".join(key.split("_")[2:])
                        all_episode_data[f"next_airing_{anime_id_episode}"] = session[key]

                return jsonify(all_episode_data), 200

            except Exception as e:
                logging.error(f"Error in get_all_episode_data API: {e}", exc_info=True)
                return jsonify({'error': 'Internal Server Error'}), 500

            
        @self.app.route('/animes')
        def animes():
            requester = g.requester
            if not requester:
                return redirect(url_for('index'))
            try:
                anime_objs_json = {} 
                for anime in requester.anime_repo.get_all_animes():
                    anime_objs_json[anime.id] = anime.to_dict()

                return jsonify(anime_objs_json)

            except Exception as e:
                logging.error(f"Error rendering template: {e}")
                return str(e), 500   

        @self.app.route('/user_animes')
        def user_animes():
            requester = g.requester
            if not requester:
                return redirect(url_for('index'))
            try:
                return jsonify(requester.anime_repo.user_anime_list)

            except Exception as e:
                logging.error(f"Error rendering template: {e}")
                return str(e), 500  
            
        @self.app.route('/refresh_user_list_status')
        def refresh_user_list_status():
            requester = g.requester
            if not requester:
                return redirect(url_for('index'))
            try:
                requester.get_user_anime_list() # TODO: RENAME REFRESH ANIME
                return "SUCCESSFUL", 200

            except Exception as e:
                logging.error(f"Error rendering template: {e}")
                return str(e), 500  

        @self.app.route('/lineage_data')
        def lineage_data():
            requester = g.requester
            if not requester:
                return redirect(url_for('index'))
            try:
                lineage = requester.anime_repo.generate_anime_seasons_liniage()
                return jsonify(lineage)
            except Exception as e:
                logging.error(f"Error generating lineage data: {e}")
                return str(e), 500
            
            
        @self.app.route('/download_anime/<int:mal_anime_id>/<int:episode_number>')
        def download_anime(mal_anime_id, episode_number):
            try:
                # Step 1: Retrieve Anime Information
                anime_id, anime_name = self.scraper.get_anilist_id_from_mal(mal_anime_id)
                video_source_url = self.scraper.get_video_source_url_selenium(anime_id, episode_number)

                if not video_source_url:
                    logging.error(f"Video source URL not found for MAL ID {mal_anime_id}, Episode {episode_number}")
                    return "Video source URL not found", 404

                logging.info(f"Initiating download for Anime ID: {anime_id}, Name: {anime_name}")

                # Step 2: Download and Parse the .m3u8 Playlist with base_uri
                playlist_response = requests.get(video_source_url)
                if playlist_response.status_code != 200:
                    logging.error(f"Failed to download m3u8 playlist from {video_source_url}, Status Code: {playlist_response.status_code}")
                    return "Failed to download video playlist", 500

                playlist_content = playlist_response.text
                logging.debug(f"M3U8 Playlist Content:\n{playlist_content}")

                # Parse the playlist with base_uri set to video_source_url
                playlist = m3u8.loads(playlist_content, uri=video_source_url)
                logging.info(f"Parsed m3u8 playlist: {len(playlist.segments)} segments found")

                # Initialize variables
                total_size = 0
                segment_urls = []

                if playlist.is_variant:
                    logging.info("Playlist is a master playlist. Selecting the highest quality variant.")

                    # Sort variants by bandwidth in descending order and select the highest
                    variants = sorted(playlist.playlists, key=lambda p: p.stream_info.bandwidth, reverse=True)
                    selected_variant = variants[0]  # Highest bandwidth
                    variant_url = selected_variant.absolute_uri
                    logging.info(f"Selected variant playlist URL: {variant_url}")

                    # Download the variant playlist
                    variant_response = requests.get(variant_url)
                    if variant_response.status_code != 200:
                        logging.error(f"Failed to download variant playlist from {variant_url}, Status Code: {variant_response.status_code}")
                        return "Failed to download variant playlist", 500

                    variant_content = variant_response.text
                    logging.debug(f"Variant Playlist Content:\n{variant_content}")

                    # Parse the variant playlist with base_uri set to variant_url
                    variant_playlist = m3u8.loads(variant_content, uri=variant_url)
                    logging.info(f"Parsed variant playlist: {len(variant_playlist.segments)} segments found")

                    # Collect all segment URLs
                    for segment in variant_playlist.segments:
                        segment_urls.append(segment.absolute_uri)

                else:
                    # It's a media playlist
                    logging.info("Playlist is a media playlist.")
                    for segment in playlist.segments:
                        segment_urls.append(segment.absolute_uri)

                # Step 3: Calculate the total size by sending HEAD requests
                logging.info("Calculating total download size by sending HEAD requests to each segment.")
                for segment_url in segment_urls:
                    try:
                        head = requests.head(segment_url, allow_redirects=True)
                        if head.status_code == 200:
                            size = int(head.headers.get('Content-Length', 0))
                            total_size += size
                        else:
                            logging.warning(f"Failed to get Content-Length for {segment_url}, Status Code: {head.status_code}")
                    except Exception as e:
                        logging.warning(f"Error fetching HEAD for {segment_url}: {e}")

                if total_size == 0:
                    logging.warning("Could not determine total size. Proceeding without Content-Length.")
                    content_length = None
                else:
                    content_length = total_size

                # Step 4: Define the generator
                def generate():
                    for idx, segment_url in enumerate(segment_urls):
                        logging.info(f"Downloading segment {idx + 1}/{len(segment_urls)}: {segment_url}")

                        try:
                            segment_response = requests.get(segment_url, stream=True)
                            if segment_response.status_code != 200:
                                logging.warning(f"Failed to download segment {segment_url}, Status Code: {segment_response.status_code}")
                                continue  # Skip to the next segment

                            for chunk in segment_response.iter_content(chunk_size=8192):
                                if chunk:
                                    yield chunk  # Stream chunk to client

                        except Exception as e:
                            logging.warning(f"Error downloading segment {segment_url}: {e}")
                            continue  # Skip to the next segment

                # Step 5: Generate a Valid Filename
                anime_name_clean = self.downloader.get_valid_filename(anime_name)
                filename = f'{anime_name_clean}_episode_{episode_number}.ts'

                # Step 6: Create the Streaming Response
                headers = {
                    'Content-Disposition': f'attachment; filename="{filename}"',
                    'Content-Type': 'video/mp2t'
                }

                if content_length:
                    headers['Content-Length'] = str(content_length)

                logging.info(f"Serving file {filename} to the client with Content-Length={content_length}")

                return Response(
                    stream_with_context(generate()),
                    headers=headers,
                    mimetype='video/mp2t'
                )

            except Exception as e:
                logging.error(f"Error serving Anime ID {mal_anime_id}, Episode {episode_number}: {e}", exc_info=True)
                return "Internal Server Error", 500
            
        @self.app.route('/watch_anime/<int:mal_anime_id>/<int:episode_number>')
        def watch_anime(mal_anime_id, episode_number):
            try:
                saved_m3u8_link = self.downloader.get_m3u8_from_json(mal_anime_id, episode_number)
                if saved_m3u8_link:
                    video_source_url = saved_m3u8_link
                else:
                    # Get the AniList ID and anime name from MAL ID
                    print(f"SCRAPING ANIME: {mal_anime_id} - EP.{episode_number}...")
                    anime_id, anime_name = self.scraper.get_anilist_id_from_mal(mal_anime_id)
                    print(f"RECIEVED ANIME ID (AND NAME) TO SCRAPE WITH: ID: {anime_id} ({anime_name}).")
                    # Get the base m3u8 URL (master playlist)
                    m3u8_link = self.scraper.get_video_source_url_selenium(anime_id, episode_number)
                    if not m3u8_link:
                        return "Video source URL not found", 404
                    
                    # Compare episode number to requested episode number
                    actual_ep = self.scraper.extract_episode_from_video_url(m3u8_link)
                    if  int(actual_ep) - int(episode_number) != 0:
                        print(f'FOUND: EP{actual_ep}, BUT EXPECTED: EP{episode_number}')
                        return f"Requested episode {episode_number} not found, could only find episode: {actual_ep}.\n If the episode found is the previous of the requested episode,\n then the anime is still airing and the episode not available yet", 417

                    # Save the m3u8 URL to JSON to skip scraping for later requests
                    self.downloader.save_m3u8_to_json(mal_anime_id, episode_number, m3u8_link)
                    video_source_url = m3u8_link

                if not video_source_url:
                    return 'URL parameter is missing.', 400
                
                # Get the highest resolution m3u8 URL
                m3u8_url = self.downloader.get_highest_resolution_m3u8_url(video_source_url)

                # Fetch the m3u8 content
                m3u8_content = self.downloader.get_m3u8_content(m3u8_url)

                # Modify the m3u8 content if necessary (e.g., adjust segment URLs)
                modified_m3u8_content = self.downloader.modify_m3u8_content(m3u8_content, m3u8_url)

                # Return the m3u8 playlist
                return Response(modified_m3u8_content, mimetype='application/vnd.apple.mpegurl')

            except Exception as e:
                logging.error(f"Error serving anime scraped anime: {e}")
                return str(e), 500
            
        @self.app.route('/ts_segment')
        def ts_segment():
            # URL of the .ts segment to fetch
            segment_url = request.args.get('url')
            if not segment_url:
                return "Segment URL not provided", 400

            # Stream the .ts segment to the client
            return self.proxy_ts_segment(segment_url)
        
        @self.app.route('/check_available_episodes/<int:mal_anime_id>')
        def check_available_episodes(mal_anime_id):
            try:
                episodes_available = self.scraper.get_episodes_available(mal_anime_id)
                print("Episodes available:\n", episodes_available)
                return episodes_available, 200
            except Exception as e:
                return e, 500


    def run_flask(self):
        self.server = make_server('0.0.0.0', 5000, self.app)
        self.server.serve_forever()

