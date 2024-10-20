import os
import json
from Anime import Anime

class AnimeRepository:
    def __init__(self):
        self.animes = {}
        self.user_anime_list = None

    def add(self, anime):
        self.animes[anime.id] = anime

    def get_all_animes(self):
        return list(self.animes.values())
    
    def get_anime_by_id(self, id):
        try:
            return self.animes[id]
        except:
            return None
        
    def create_anime(self, info):
        if self.get_anime_by_id(info['id']) is None:
            new_anime = Anime(
                id=info['id'],
                title=info['title'],
                main_picture=info.get('main_picture', None),
                alternative_titles=info.get('alternative_titles', None),
                start_date=info.get('start_date', None),
                end_date=info.get('end_date', None),
                synopsis=info.get('synopsis', None),
                mean=info.get('mean', None),
                rank=info.get('rank', None),
                popularity=info.get('popularity', None),
                num_list_users=info.get('num_list_users', None),
                num_scoring_users=info.get('num_scoring_users', None),
                nsfw=info.get('nsfw', None),
                created_at=info.get('created_at', None),
                updated_at=info.get('updated_at', None),
                media_type=info.get('media_type', None),
                status=info.get('status', None),
                genres=info.get('genres', None),
                my_list_status=info.get('my_list_status', None),
                num_episodes=info.get('num_episodes', None),
                start_season=info.get('start_season', None),
                broadcast=info.get('broadcast', None),
                source=info.get('source', None),
                average_episode_duration=info.get('average_episode_duration', None),
                rating=info.get('rating', None),
                pictures=info.get('picture', None),
                background=info.get('background', None),
                related_anime=info.get('related_anime', []),
                related_manga=info.get('related_manga', []),
                recommendations=info.get('recommendations', []),
                studios=info.get('studios', None),
                statistics=info.get('statistics', None),
                prequel=info.get('prequel', None),
                sequel=info.get('sequel', None)
            )
            self.add(new_anime)
            self.save_anime(new_anime)


    def update_anime_list_status(self, all_anime):
        new_animes = []
        for anime in all_anime:
            id = anime.get('node', {}).get('id', None)
            list_status = anime.get('list_status', {})
            if id is not None:
                if self.get_anime_by_id(id) is not None:
                    self.animes[id].my_list_status = list_status # Update user list status for anime
                else:
                    new_animes.append(id) # Append to list, to create entirely new anime object later
        return new_animes


    def save_anime(self, anime):
        if not os.path.exists('animes'):
            os.makedirs('animes')
        
        anime_info = anime.to_dict()
        file_path = os.path.join('animes', f'{anime.id}.json')
        with open(file_path, 'w') as file:
            json.dump(anime_info, file, indent=4)

    def load_anime(self, anime_id):
        file_path = os.path.join('animes', f'{anime_id}.json')
        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                return json.load(file)
        return None
    
    def save_user_anime_list(self, all_anime): # actually: refresh user anime list
        ids = []
        for info in all_anime:
            ids.append(info['node']['id'])
        self.user_anime_list = ids

    def get_prequel_sequel(self):
        for anime in self.get_all_animes():
            for related in anime.related_anime:
                if related['relation_type'] == 'prequel' and anime.prequel is None:
                    anime.prequel = related['node']['id']
                elif related['relation_type'] == 'sequel' and anime.sequel is None:
                    anime.sequel = related['node']['id']

            if anime.prequel is None:
                anime.prequel = False
            if anime.sequel is None:
                anime.sequel = False

    def generate_anime_seasons_liniage(self):
        
        def get_complete_lineage(anime_id):
            if anime_id not in self.animes:
                return []
            anime = self.animes[anime_id]
            lineage = []

            # Traverse to the earliest prequel
            while anime.prequel:
                anime = self.animes.get(anime.prequel, None)
                if not anime:
                    break
                lineage.append(anime.id)
            
            lineage.reverse()  # Reverse to get chronological order

            # Reset to original anime and traverse through sequels
            anime = self.animes[anime_id]
            lineage.append(anime.id)
            while anime.sequel:
                anime = self.animes.get(anime.sequel, None)
                if not anime:
                    break
                lineage.append(anime.id)

            return lineage

        anime_lineages = {}
        for anime in self.get_all_animes():
            if anime.prequel is False:  # Starting points
                lineage = get_complete_lineage(anime.id)
                if len(lineage) > 0:
                    anime_lineages[anime.id] = lineage

        return anime_lineages