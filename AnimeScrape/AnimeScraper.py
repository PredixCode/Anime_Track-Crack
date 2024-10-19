import requests
import logging
import time
import json
from bs4 import BeautifulSoup as bs
from urllib.parse import urljoin
from AnimeScrape.VideoDownloader import VideoDownloader
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class AnimeScraper:
    def __init__(self):
        logging.basicConfig(level=logging.INFO)
        logging.getLogger('selenium').setLevel(logging.WARNING)
        logging.getLogger('urllib3').setLevel(logging.WARNING)

    def init_driver(self):
        self.driver = None
        options = Options()
        options.add_argument('--headless')  # Run Chrome in headless mode if you don't want the browser to be visible

        # Initialize the Chrome driver (Selenium manages the driver)
        self.driver = webdriver.Chrome(options=options)
        self.headers = self._load_headers("AnimeScrape/headers.json")

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

    
    def get_video_source_url_selenium(self, anime_id, episode):
        """
        Uses Selenium to load the page fully, including any JavaScript elements, and extracts the video source URL.
        """
        self.init_driver()
        ep_url = f"https://shiroko.co/en/anime/watch?id={anime_id}&n={episode}&prv=gogoanime"
        try:
            logging.info(f"Loading page {ep_url} with Selenium...")
            self.driver.get(ep_url)

            # Wait for the <video> tag to be present (adjust the condition based on your case)
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, 'video'))
            )

            max_tries, tries = 10, 0
            while tries < max_tries:
                html = bs(self.driver.page_source, 'lxml')

                # Find the first <video> tag (adjust the attributes if needed)
                video = html.find('video', {"aria-hidden": "true"})

                # From the <video> tag, find the nested <source> tag
                if video:
                    source_tag = video.find('source')
                    if source_tag and source_tag.get('src'):
                        video_src = source_tag['src']
                        print(f"Video source URL found: {video_src}")
                        return video_src
                    else:
                        print("No source tag or src attribute found inside the video tag.")
                else:
                    print("No video tag found.")

                tries += 1
                time.sleep(0.5)  # Wait a second before retrying

            return None

        except Exception as e:
            logging.error(f"Failed to extract video source URL using Selenium: {e}")
            return None

        finally:
            if self.driver:
                self.driver.quit()

    def get_anilist_id_from_mal(self, mal_id):
        # GraphQL query to search AniList using the MyAnimeList ID
        query = '''
        query ($idMal: Int) {
        Media(idMal: $idMal, type: ANIME) {
            id
            title {
            romaji
            english
            }
        }
        }
        '''

        # Set up variables for the GraphQL query
        variables = {
            'idMal': mal_id
        }

        # AniList GraphQL API URL
        url = 'https://graphql.anilist.co'

        # Make the POST request
        response = requests.post(url, json={'query': query, 'variables': variables})

        # Parse the response JSON
        data = response.json()

        # Check if the request was successful and an ID was found
        if 'data' in data and data['data']['Media']:
            anilist_id = data['data']['Media']['id']
            title_romaji = data['data']['Media']['title']['romaji']
            title_english = data['data']['Media']['title']['english']
            return anilist_id, title_english
        else:
            return None

    def scrape_episode(self, anime_id, anime_name, episode):
        """
        Main method to scrape and download the video.
        """
        
        file_name = f'downloaded_animes/{anime_name}/{episode}'
        video_source_url = self.get_video_source_url_selenium(anime_id, episode)
        if not video_source_url:
            logging.error("Cannot proceed without a video source URL.")
            return

        self.downloader = VideoDownloader()
        self.downloader.download_video(video_source_url,file_name)

    def extract_episode_from_video_url(self, video_source_url):
        return video_source_url.split('/ep.')[1].split('.')[0]
    
    def get_episodes_available(self, mal_anime_id):
        """
        Retrieves all episode URLs for a given MAL anime ID from shiroko.co.

        Parameters:
            mal_anime_id (int): The MyAnimeList (MAL) ID of the anime.

        Returns:
            List[str]: A list of episode URLs containing the anilist_id.
        """
        # Retrieve the AniList ID from MAL ID

        self.init_driver()
        try:
            anilist_id, title_english = self.get_anilist_id_from_mal(mal_anime_id)
            if not anilist_id:
                print(f"Failed to retrieve AniList ID for MAL ID {mal_anime_id}")
                return []

            # Construct the Anime URL
            anime_url = f"https://shiroko.co/en/anime/{anilist_id}"


            # Fetch the Anime Page
            self.driver.get(anime_url)

            # Wait for the <video> tag to be present (adjust the condition based on your case)
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, 'Episode List'))
            )
            time.sleep(2)

            # Parse the HTML Content
            soup = bs(self.driver.page_source, 'html.parser')

            # Extract All `a` Tags with `href` Attributes
            a_tags = soup.find_all('a', href=True)


            # Filter Links Containing the `anilist_id`
            filtered_links = []
            for tag in a_tags:
                href = tag['href']
                # Make the URL absolute if it's relative
                full_url = urljoin(anime_url, href)
                if str(anilist_id) in full_url and 'watch?id' in full_url:
                    filtered_links.append(full_url)

            # Deduplicate the list
            unique_filtered_links = list(set(filtered_links))

            print(f"Found {len(unique_filtered_links)} episode links containing AniList ID {anilist_id}")

            return unique_filtered_links
        
        except Exception as e:
            logging.error(f"Failed to extract video source URL using Selenium: {e}")
            return None

        finally:
            if self.driver:
                self.driver.quit()


if __name__ == "__main__":
    scraper = AnimeScraper()
    anime_id, anime_name = scraper.get_anilist_id_from_mal()
    scraper.scrape_episode(anime_id, anime_name, 10)
