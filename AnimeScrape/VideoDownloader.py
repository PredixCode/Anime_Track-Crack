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

    def __init__(self, headers_file="AnimeScrape/headers.json"):
        """
        Initialize the VideoDownloader instance.

        :param base_url: The URL of the base M3U8 file.
        :param output_file: The filename where the output video will be saved.
        :param headers_file: The path to the JSON file containing HTTP headers.
        """
        self.session = requests.Session()
        # Load headers from the JSON file
        self.session.headers.update(self._load_headers(headers_file))

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

    def get_highest_resolution_m3u8_url(self, base_url):
        """
        Fetches the base M3U8 file and returns the URL for the highest resolution stream.

        :return: The URL of the highest resolution M3U8 file.
        """
        response = self.session.get(base_url)
        response.raise_for_status()

        # Debug: Log the fetched M3U8 content
        logging.debug("Master M3U8 Content:")
        logging.debug(response.text)

        playlist = m3u8.loads(response.text)

        # Filter out playlists without resolution info
        playlists_with_resolution = [
            p for p in playlist.playlists if p.stream_info.resolution is not None
        ]

        if not playlists_with_resolution:
            raise Exception("No streams with resolution information found.")

        # Sort the streams based on resolution width (higher width = higher resolution)
        sorted_streams = sorted(
            playlists_with_resolution,
            key=lambda stream: stream.stream_info.resolution[0],  # Width
            reverse=True
        )

        # Select the highest resolution stream (first in the sorted list)
        highest_resolution_stream = sorted_streams[0]

        # Use urljoin to construct the URL correctly
        base_url_directory = base_url.rsplit('/', 1)[0] + '/'
        m3u8_url = urljoin(base_url_directory, highest_resolution_stream.uri)

        # Debug: Log the selected stream's M3U8 URL
        logging.debug(f"Selected M3U8 URL: {m3u8_url}")

        return m3u8_url

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

    def modify_m3u8_content(self, m3u8_content, m3u8_url):
        """
        Modifies the m3u8 content to adjust the segment URLs to point to our server.
        """
        playlist = m3u8.loads(m3u8_content)
        base_url = m3u8_url.rsplit('/', 1)[0]

        for segment in playlist.segments:
            segment_uri = segment.uri
            full_segment_url = urljoin(base_url + '/', segment_uri)
            # Encode the segment URL to be used as a query parameter
            encoded_segment_url = quote(full_segment_url, safe='')
            # Adjust the segment URI to point to our /ts_segment route
            segment.uri = f"/ts_segment?url={encoded_segment_url}"

        return playlist.dumps()

# Example usage:

if __name__ == "__main__":
    # Configure logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    logging.basicConfig(level=logging.INFO)
    base_url = "https://www118.anzeat.pro/streamhls"
    episode = 19
    base_m3u8_url = f"{base_url}/4f2c0f603aaa698fd0fd53de4d7cbe4e/ep.{episode}.1727517932.m3u8"
    downloader = VideoDownloader()
    downloader.download_video(base_m3u8_url, 'output')
