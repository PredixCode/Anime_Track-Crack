import os, time
import logging
import requests
from AnimeRepository import AnimeRepository


logging.basicConfig(level=logging.DEBUG)

class Requester:
    def __init__(self, tokens_loader):
        self.num_api_calls = 0
        self.errors = []
        self.base_url = 'https://api.myanimelist.net/v2/'
        self.tokens_loader = tokens_loader

        self.headers = self.tokens_loader.get_headers()
        self.anime_repo = AnimeRepository()
        self._generate_anime_database()

    def _generate_all_relation_levels(self):
        i, new_animes_num = 0, 1
        while(new_animes_num > 0):
            new_animes_num = self._generate_next_relations_level(i+1)
            i+=1

    def _generate_next_relations_level(self,i):
        logging.debug(f'Generating next relationship level: {i}. ROUND -->')
        last_animes_num = len(self.anime_repo.get_all_animes())
        self.anime_repo.get_prequel_sequel()

        for anime in self.anime_repo.get_all_animes():
            self.get_anime_info_by_id(anime.prequel)
            self.get_anime_info_by_id(anime.sequel)

        current_animes_num = len(self.anime_repo.get_all_animes())
        new_animes_num = current_animes_num-last_animes_num
        logging.debug(f'- New Animes in AnimeRepository: {new_animes_num}')
        return new_animes_num

    def _generate_anime_database(self):
        # -- MAIN STARTER LOGIC --
        while self.anime_repo.user_anime_list == None:
            self.get_user_anime_list()
            try:
                for id in self.anime_repo.user_anime_list:
                    self.get_anime_info_by_id(id)
            except TypeError as e:
                print(e)
                print('API LIMIT HAS BEEN REACHED OR ANOTHER ERROR IS OCCURING, THAT PREVENTS MAL-API COMMUNICATION, TRYING AGAIN IN 1 MINUTE...')
                time.sleep(60)

        # Get the immediate prequel and sequel id of every anime in AnimeRepository and create a new Anime object from those ids in AnimeRepository
        print('- Animes in AnimeRepository at start:', len(self.anime_repo.get_all_animes()))
        self._generate_all_relation_levels()

    def get_user_anime_list(self, username='@me', limit=1000, status=None, sort='list_score'):
        base_user_list_url = self.base_url + f'users/{username}/animelist'

        params = {
            'limit': limit,
            'fields': 'list_status'
        }
        if status:
            params['status'] = status
        if sort:
            params['sort'] = sort

        all_anime = []
        retry = False
        while True:
            try:
                response = requests.get(base_user_list_url, headers=self.headers, params=params, timeout=3)
                self.num_api_calls += 1
                if response.status_code == 200:
                    data = response.json()
                    all_anime.extend(data.get('data', []))
                    paging = data.get('paging', {})
                    next_url = paging.get('next')
                    if not next_url:
                        break
                    base_user_list_url = next_url
                elif response.status_code == 401:
                    # Unauthorized, attempt to refresh tokens
                    if self.tokens_loader.refresh_tokens():
                        self.headers = self.tokens_loader.get_headers()
                        continue  # Retry the request with new tokens
                    else:
                        # Tokens could not be refreshed, redirect to login
                        logging.error("Unauthorized access and token refresh failed.")
                        raise Exception("Authentication failed")
                else:
                    self.errors.append({'url': base_user_list_url, 'error_code': response.status_code, 'at': f'get_user_anime_list({username})'})
                    if not retry:
                        retry = True
                    else:
                        break
            except Exception as e:
                return e


        new_animes = self.anime_repo.update_anime_list_status(all_anime)
        for new_anime_id in new_animes:
            self.get_anime_info_by_id(new_anime_id)

        self.anime_repo.save_user_anime_list(all_anime)

    def get_anime_info_by_id(self, anime_id):
        if anime_id and anime_id is not None:
            if not os.path.exists(f'animes/{anime_id}.json'):
                print("Creating Anime:", anime_id)
                anime_details_url = self.base_url + f'anime/{anime_id}'

                params = {
                    'fields': 'id,title,main_picture,alternative_titles,start_date,end_date,synopsis,mean,rank,popularity,num_list_users,num_scoring_users,nsfw,created_at,updated_at,media_type,status,genres,num_episodes,start_season,broadcast,source,average_episode_duration,rating,pictures,background,related_anime,related_manga,recommendations,studios,statistics'
                }

                try:
                    response = requests.get(anime_details_url, headers=self.headers, params=params, timeout=2.5)
                    self.num_api_calls += 1
                    if response.status_code == 200:
                        info = response.json()
                        self.anime_repo.create_anime(info)
                    else:
                        self.errors.append({'url': anime_details_url, 'error_code': response.status_code, 'at': f'get_anime_info_by_id({anime_id})'})
                        if len([error for error in self.errors if error['error_code'] == 443]) >= 10:
                            self.tokens_loader.refresh_tokens()
                        return None
                except:
                    return None
            else:
                if self.anime_repo.get_anime_by_id(anime_id) is None:
                    info = self.anime_repo.load_anime(anime_id)
                    self.anime_repo.create_anime(info)
