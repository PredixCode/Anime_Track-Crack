import os
import requests

from AnimeRepository import AnimeRepository
from MalAuthenticator import TokenLoader

class Requester:
    def __init__(self, tokens_path='src/tokens.json'):
        self.num_api_calls = 0
        self.errors = []
        self.base_url = 'https://api.myanimelist.net/v2/'
        self.tokens_loader = TokenLoader(tokens_path)
        self.headers = self.tokens_loader.get_headers()
        self.anime_repo = AnimeRepository()
            

    def get_user_anime_list(self, username='@me', limit=100, status=None, sort='list_score'):       
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
                    # Use next URL for the next request
                    params = {}
                    base_user_list_url = next_url
                else:
                    self.errors.append( {'url':base_user_list_url, 'error_code':response.status_code, 'at': f'get_user_anime_list({username})'} )
                    if retry == False:
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
                        self.errors.append( {'url':anime_details_url, 'error_code':response.status_code, 'at': f'get_anime_info_by_id({anime_id})'} )
                        if ([len(http_error_codes) for http_error_codes in self.errors.error_code if http_error_codes == 443] >= 10): {
                            self.tokens_loader.refresh_tokens()
                        }
                        return None
                except:
                    return None
            else:
                if self.anime_repo.get_anime_by_id(anime_id) is None:
                    info = self.anime_repo.load_anime(anime_id)
                    self.anime_repo.create_anime(info)