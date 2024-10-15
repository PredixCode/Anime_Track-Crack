class Anime:
    def __init__(self, **kwargs):
        self.get_fields()
        kwargs['mal_url'] = f'https://myanimelist.net/anime/{kwargs["id"]}/'

        for field in self.fields:
            setattr(self, field, kwargs.get(field, None))


    # Get, if the class has the user data anime info and or the generic info
    def get_data_completeness(self):
        pass

    def get_fields(self):
        self.request_fields = 'id,title,main_picture,alternative_titles,start_date,end_date,synopsis,mean,rank,popularity,num_list_users,num_scoring_users,nsfw,created_at,updated_at,media_type,status,genres,my_list_status,num_episodes,start_season,broadcast,source,average_episode_duration,rating,pictures,background,related_anime,related_manga,recommendations,studios,statistics,prequel,sequel'
        self.fields = self.request_fields.split(',')
        self.fields.append('mal_url')

    def set_prequel(self, prequel):
        self.prequel = prequel

    def set_sequel(self, sequel):
        self.sequel = sequel

    def to_dict(self):
        return {field: getattr(self, field) for field in self.fields}

    def __str__(self):
        return '\n'.join(f'{field}: {getattr(self, field)}' for field in self.fields)