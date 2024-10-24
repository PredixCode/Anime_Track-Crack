import os
import re
import requests
import m3u8
import logging
import json
from urllib.parse import urljoin, quote

class VideoDownloader:
    """
    A class to download video chunks from a given base M3U8 URL.
    """

    def __init__(self, headers_file="AnimeScrape/headers.json",  m3u8_json_file_path='m3u8/episode_links.json'):
        """
        Initialize the VideoDownloader instance.

        :param base_url: The URL of the base M3U8 file.
        :param output_file: The filename where the output video will be saved.
        :param headers_file: The path to the JSON file containing HTTP headers.
        """
        self.session = requests.Session()
        # Load headers from the JSON file
        self.session.headers.update(self._load_headers(headers_file))

        self.json_file_path = m3u8_json_file_path
        if not os.path.exists(self.json_file_path):
            with open(self.json_file_path, 'w') as f:
                json.dump({}, f)

    def get_valid_filename(self,name):
        s = str(name).strip().replace(" ", "_")
        s = re.sub(r"(?u)[^-\w.]", "", s)
        if s in {"", ".", ".."}:
            raise Exception("Could not derive file name from '%s'" % name)
        return s


    def download_video(self, base_url, output_file):
        """
        Coordinates the download process: get the M3U8 URL and download chunks.
        """
        try:
            # Get the highest resolution M3U8 URL
            m3u8_url = self.get_highest_resolution_m3u8_url(base_url)

            # Download all chunks and write them to a file
            self._download_chunks(m3u8_url, output_file)

            logging.info(f"Download completed. Video saved as {output_file}")

        except Exception as e:
            logging.error(f"An error occurred: {e}")

    def download_video_to_memory(self, video_source_url, buffer):
        # Download the m3u8 playlist
        playlist_response = requests.get(video_source_url)
        if playlist_response.status_code != 200:
            logging.error(f"Failed to download m3u8 playlist from {video_source_url}, Status Code: {playlist_response.status_code}")
            return

        playlist_content = playlist_response.text
        logging.debug(f"M3U8 Playlist Content:\n{playlist_content}")

        # Parse the playlist
        playlist = m3u8.loads(playlist_content)
        logging.info(f"Parsed m3u8 playlist: {len(playlist.segments)} segments found")

        if playlist.is_variant:
            logging.info("Playlist is a master playlist. Selecting the first variant.")
            # Select the first variant playlist
            if not playlist.playlists:
                logging.error("No variant playlists found in the master playlist.")
                return
            variant = playlist.playlists[0]
            variant_url = variant.absolute_uri
            logging.info(f"Selected variant playlist URL: {variant_url}")
            # Recursively download the variant playlist
            self.download_video_to_memory(variant_url, buffer)
            return

        # Proceed if it's a media playlist
        for idx, segment in enumerate(playlist.segments):
            segment_url = segment.absolute_uri
            logging.info(f"Downloading segment {idx + 1}/{len(playlist.segments)}: {segment_url}")
            segment_response = requests.get(segment_url, stream=True)
            if segment_response.status_code != 200:
                logging.warning(f"Failed to download segment {segment_url}, Status Code: {segment_response.status_code}")
                continue  # Optionally handle retries or abort

            for chunk in segment_response.iter_content(chunk_size=8192):
                if chunk:
                    buffer.write(chunk)

    def _load_headers(self, headers_file):
        """
        Loads HTTP headers from a JSON file.

        :param headers_file: The path to the JSON file containing HTTP headers.
        :return: A dictionary of HTTP headers.
        """
        try:
            with open(headers_file, 'r', encoding='utf-8') as file:
                headers = json.load(file)
                logging.info(f"Loaded HTTP headers")
                return headers
        except FileNotFoundError:
            logging.error(f"Headers file '{headers_file}' not found.")
            return {}
        except json.JSONDecodeError as e:
            logging.error(f"Error parsing headers JSON file: {e}")
            return {}
        

        

    def get_available_resolutions(self, base_url):
        """
        Retrieves all available resolutions from the master M3U8 playlist.

        :param base_url: The URL of the master M3U8 file.
        :return: A list of tuples containing resolution and corresponding M3U8 URL.
        """
        response = self.session.get(base_url)
        response.raise_for_status()

        master_playlist = m3u8.loads(response.text)
        resolutions = []

        for playlist in master_playlist.playlists:
            resolution = playlist.stream_info.resolution
            if resolution:
                res_str = f"{resolution[1]}p"  # e.g., "720p"
                res_url = urljoin(base_url.rsplit('/', 1)[0] + '/', playlist.uri)
                resolutions.append((res_str, res_url))

        return resolutions

    def get_m3u8_url_by_resolution(self, base_url, desired_resolution):
        """
        Fetches the M3U8 URL for the specified resolution.

        :param base_url: The URL of the master M3U8 file.
        :param desired_resolution: The desired resolution (e.g., "720p").
        :return: The URL of the M3U8 file for the specified resolution.
        """
        response = self.session.get(base_url)
        response.raise_for_status()

        master_playlist = m3u8.loads(response.text)

        for playlist in master_playlist.playlists:
            resolution = playlist.stream_info.resolution
            if resolution:
                res_str = f"{resolution[1]}p"
                if res_str == desired_resolution:
                    return urljoin(base_url.rsplit('/', 1)[0] + '/', playlist.uri)

        raise ValueError(f"Resolution {desired_resolution} not found.")    

    def _download_chunks(self, m3u8_url, output_file):
        """
        Downloads the individual TS files from the M3U8 playlist and writes them to a single file.

        :param m3u8_url: The URL of the M3U8 file for the highest resolution stream.
        """
        response = self.session.get(m3u8_url)
        response.raise_for_status()

        # Debug: Log the fetched M3U8 content for the selected resolution
        logging.debug("Selected Resolution M3U8 Content:")

        playlist = m3u8.loads(response.text)

        # Handle potential encryption
        if playlist.keys and any(playlist.keys):
            key = playlist.keys[0]
            if key:
                # Fetch the encryption key
                key_uri = key.uri
                key_url = urljoin(m3u8_url, key_uri)
                key_response = self.session.get(key_url)
                key_response.raise_for_status()
                encryption_key = key_response.content
                logging.warning("Encryption detected but decryption is not implemented in this script.")
                return

        # Open the output file in binary write mode
        anime_episode_folder = output_file.split('/')[0]
        if not os.path.exists(anime_episode_folder):
            os.makedirs(anime_episode_folder)
        
        with open(output_file+'.ts', 'wb') as f:
            for segment in playlist.segments:
                chunk_url = urljoin(m3u8_url, segment.uri)
                try:
                    chunk_response = self.session.get(chunk_url)
                    chunk_response.raise_for_status()
                    chunk_data = chunk_response.content
                    f.write(chunk_data)
                except requests.RequestException as e:
                    logging.error(f"Failed to download {chunk_url}: {e}")
                    return e, 500
        return f"Success downloading {m3u8_url}", 200

    def get_m3u8_content(self, m3u8_url):
        """
        Fetches the m3u8 content from the given URL.
        """
        response = self.session.get(m3u8_url)
        response.raise_for_status()
        return response.text

    def modify_m3u8_content(self, m3u8_content, m3u8_url, resolution=None):
        """
        Modifies the m3u8 content to adjust the segment URLs to point to our server.
        Optionally modifies the resolution in the segment filenames.

        :param m3u8_content: Original m3u8 content.
        :param m3u8_url: URL of the original m3u8.
        :param resolution: Desired resolution (e.g., '720', '1080'). If None, retains original.
        :return: Modified m3u8 content as a string.
        """
        playlist = m3u8.loads(m3u8_content)
        base_url = m3u8_url.rsplit('/', 1)[0]

        for segment in playlist.segments:
            segment_uri = segment.uri
            if resolution:
                # Modify the segment URI to reflect the desired resolution
                # Example: ep.3.1729183757.720268.ts
                segment_uri = re.sub(r'\.\d{3}268\.ts$', f'.{resolution}268.ts', segment.uri)
            full_segment_url = urljoin(base_url + '/', segment_uri)
            # Encode the segment URL to be used as a query parameter
            encoded_segment_url = quote(full_segment_url, safe='')
            # Adjust the segment URI to point to our /ts_segment route
            segment.uri = f"/ts_segment?url={encoded_segment_url}"

        return playlist.dumps()
    

    # TODO: Implement database for saving m3u8 scraped links
    def save_m3u8_to_json(self, mal_anime_id, episode_number, m3u8_link):
        """Save the m3u8 link to a JSON file."""
        try:
            # Load the existing data from the JSON file
            with open(self.json_file_path, 'r') as f:
                data = json.load(f)
            
            # Check if the anime ID already exists in the JSON, if not, create an entry
            if str(mal_anime_id) not in data:
                data[str(mal_anime_id)] = []

            # Check if the episode is already stored, and update or append it
            episode_exists = False
            for episode in data[str(mal_anime_id)]:
                if episode.get(str(episode_number)):
                    episode[str(episode_number)] = m3u8_link
                    episode_exists = True
                    break

            if not episode_exists:
                # Append new episode and link
                data[str(mal_anime_id)].append({str(episode_number): m3u8_link})
            
            # Save the updated data back to the JSON file
            with open(self.json_file_path, 'w') as f:
                json.dump(data, f, indent=4)
        
        except Exception as e:
            print(f"Error saving m3u8 link to JSON: {e}")

    def get_m3u8_from_json(self, mal_anime_id, episode_number):
        """Retrieve the m3u8 link from the JSON file."""
        try:
            # Load the existing data from the JSON file
            with open(self.json_file_path, 'r') as f:
                data = json.load(f)
            
            # Find the anime ID and episode number
            anime_data = data.get(str(mal_anime_id), [])
            for episode in anime_data:
                if episode.get(str(episode_number)):
                    return episode[str(episode_number)]
            
            # If not found, return None
            return None
        
        except Exception as e:
            print(f"Error retrieving m3u8 link from JSON: {e}")
            return None
