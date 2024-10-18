import os, time
import webbrowser
import threading
import logging
import requests


from flask import Flask, Response, send_file, request, stream_with_context, jsonify, render_template
from werkzeug.serving import make_server

from AnimeScrape.VideoDownloader import VideoDownloader


logging.basicConfig(level=logging.DEBUG)



class AnimeController:
    def __init__(self, anime_repo, requester, scraper):
        self.anime_repo = anime_repo
        self.requester = requester
        self.scraper = scraper
        self.downloader = VideoDownloader()
        self.server = None
        self.app = Flask(__name__, template_folder='templates', static_folder='webapp/static')

        self.build_flask()

        # Start the Flask server in a separate thread
        threading.Thread(target=self.run_flask).start()

        # Open the web browser
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
            try:
                return render_template('index.html')
            except Exception as e:
                logging.error(f"Error rendering template: {e}")
                return str(e), 500
            
        @self.app.route('/animes')
        def animes():
            try:
                anime_objs_json = {} 
                for anime in self.anime_repo.get_all_animes():
                    anime_objs_json[anime.id] = anime.to_dict()

                return jsonify(anime_objs_json)

            except Exception as e:
                logging.error(f"Error rendering template: {e}")
                return str(e), 500   

        @self.app.route('/user_animes')
        def user_animes():
            try:
                return jsonify(self.anime_repo.user_anime_list)

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
                lineage = self.anime_repo.generate_anime_seasons_liniage()
                return jsonify(lineage)
            except Exception as e:
                logging.error(f"Error generating lineage data: {e}")
                return str(e), 500
            
        @self.app.route('/download_anime/<int:mal_anime_id>/<int:episode_number>')
        def download_anime(mal_anime_id, episode_number):
            try:
                anime_id, anime_name = self.scraper.get_anilist_id_from_mal(mal_anime_id)
                print(f"DOWNLOADING ANIME: {anime_id, anime_name}")
                self.scraper.scrape_episode(anime_id, anime_name, episode_number)
                return f"Successfully started downloading {anime_name}", 200
            except Exception as e:
                logging.error(f"Error serving anime {mal_anime_id} Episode {episode_number}: {e}")
                return str(e), 500
            
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


    def run_flask(self):
        self.server = make_server('localhost', 5000, self.app)
        self.server.serve_forever()

