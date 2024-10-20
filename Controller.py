import io, time, m3u8, os
import webbrowser
import threading
import logging
import requests
from datetime import timedelta


import redis
from flask import Flask, Response, request, session, redirect, url_for, stream_with_context, jsonify, render_template
from flask_session import Session
from werkzeug.serving import make_server

from MalAuthenticator import TokenGenerator, TokenLoader
from MalRequester import Requester
from AnimeScrape.VideoDownloader import VideoDownloader
from AnimeScrape.AnimeScraper import AnimeScraper


logging.basicConfig(level=logging.DEBUG)

class AnimeController:
    def __init__(self):
        self.scraper = AnimeScraper()
        self.downloader = VideoDownloader()
        self.server = None
        self.app = Flask(__name__, template_folder='templates', static_folder='webapp/static')
        self.token_path = 'src/tokens.json'
        self.build_flask()
        threading.Thread(target=self.run_flask).start()
        time.sleep(1)
        webbrowser.open_new('http://127.0.0.1:5000/')


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
        @self.app.route('/')
        def index():
            tokens_loader = TokenLoader(self.token_path)
            if not tokens_loader.ensure_valid_tokens():
                return redirect(url_for('login'))
            else:
                self.requester = Requester(tokens_loader=tokens_loader)
                return render_template('index.html')

        @self.app.route('/login')
        def login():
            token_generator = TokenGenerator(self.token_path)
            token_generator.authenticate()
            return redirect('/')

            
        @self.app.route('/animes')
        def animes():
            try:
                anime_objs_json = {} 
                for anime in self.requester.anime_repo.get_all_animes():
                    anime_objs_json[anime.id] = anime.to_dict()

                return jsonify(anime_objs_json)

            except Exception as e:
                logging.error(f"Error rendering template: {e}")
                return str(e), 500   

        @self.app.route('/user_animes')
        def user_animes():
            try:
                return jsonify(self.requester.anime_repo.user_anime_list)

            except Exception as e:
                logging.error(f"Error rendering template: {e}")
                return str(e), 500  
            
        @self.app.route('/refresh_user_list_status')
        def refresh_user_list_status():
            try:
                self.requester.get_user_anime_list()
                return "SUCCESSFUL", 200

            except Exception as e:
                logging.error(f"Error rendering template: {e}")
                return str(e), 500  

        @self.app.route('/lineage_data')
        def lineage_data():
            try:
                lineage = self.requester.anime_repo.generate_anime_seasons_liniage()
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
                # Get the AniList ID and anime name from MAL ID
                anime_id, anime_name = self.scraper.get_anilist_id_from_mal(mal_anime_id)
                # Get the base m3u8 URL (master playlist)
                video_source_url = self.scraper.get_video_source_url_selenium(anime_id, episode_number)
                if not video_source_url:
                    return "Video source URL not found", 404
                
                # Compare episode number to requested episode number
                actual_ep = self.scraper.extract_episode_from_video_url(video_source_url)
                if  int(actual_ep) - int(episode_number) != 0:
                    print(f'FOUND: EP{actual_ep}, BUT EXPECTED: EP{episode_number}')
                    return f"Requested episode {episode_number} not found, could only find episode: {actual_ep}.\n If the episode found is the previous of the requested episode,\n then the anime is still airing and the episode not available yet", 417


                # Get the highest resolution m3u8 URL
                m3u8_url = self.downloader.get_highest_resolution_m3u8_url(video_source_url)

                # Fetch the m3u8 content
                m3u8_content = self.downloader.get_m3u8_content(m3u8_url)

                # Modify the m3u8 content if necessary (e.g., adjust segment URLs)
                modified_m3u8_content = self.downloader.modify_m3u8_content(m3u8_content, m3u8_url)

                # Return the m3u8 playlist
                return Response(modified_m3u8_content, mimetype='application/vnd.apple.mpegurl')

            except Exception as e:
                logging.error(f"Error serving anime {anime_name} Episode {episode_number}: {e}")
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

