import time

from AnimeRepository import AnimeRepository
from MalRequests import Requester
from Controller import AnimeController

from AnimeScrape.AnimeScraper import AnimeScraper


class AnimeSeasonsTracker:
    def __init__(self):
        self.start_t = time.time()
        self.anime_repo = AnimeRepository() 
        self.requester = Requester(self.anime_repo)
        self.scraper = AnimeScraper()

        self.main()


    def main(self):
        # Get starting point by generating all Anime objects for a users anime list
        while self.requester.anime_repo.user_anime_list == None:
            self.requester.get_user_anime_list()
            try:
                for id in self.requester.anime_repo.user_anime_list:
                    self.requester.get_anime_info_by_id(id)
            except TypeError as e:
                print(e)
                print('API LIMIT HAS BEEN REACHED OR ANOTHER ERROR IS OCCURING, THAT PREVENTS MAL-API COMMUNICATION, TRYING AGAIN IN 1 MINUTE...')
                time.sleep(60)

        # Get the immediate prequel and sequel id of every anime in AnimeRepository and create a new Anime object from those ids in AnimeRepository
        print('- Animes in AnimeRepository at start:', len(self.requester.anime_repo.get_all_animes()))
        self.generate_all_relation_levels()

        # Start anime data controller
        self.animeController = AnimeController(self.anime_repo, self.requester, self.scraper)

        # End message
        self.print_end_messages()

    def generate_all_relation_levels(self):
        i, new_animes_num = 0, 1
        while(new_animes_num > 0):
            new_animes_num = self.generate_next_relations_level(i+1)
            i+=1

    def generate_next_relations_level(self,i):
        print(f'Generating next relationship level: {i}. ROUND -->')
        last_animes_num = len(self.requester.anime_repo.get_all_animes())
        self.requester.anime_repo.get_prequel_sequel()

        for anime in self.requester.anime_repo.get_all_animes():
            self.requester.get_anime_info_by_id(anime.prequel)
            self.requester.get_anime_info_by_id(anime.sequel)

        current_animes_num = len(self.requester.anime_repo.get_all_animes())
        new_animes_num = current_animes_num-last_animes_num
        print('- New Animes in AnimeRepository:', new_animes_num)
        return new_animes_num
    
    def print_prequel_sequel(self):
            for anime in self.requester.anime_repo.get_all_animes():
                print(anime.title)
                print(anime.prequel)
                print(anime.sequel)
                print('\n--<================================================================>--\n')

    def print_end_messages(self):
        print('\nPROGRAM INITIATED...')
        print(f'- Time elapsed: {time.time() - self.start_t:.2f} s  \n- API calls made: {self.requester.num_api_calls} \n- HTTP Errors: {len(self.requester.errors)}')
        print('- Number of animes in Repository', len(self.requester.anime_repo.animes))
        

if __name__ == '__main__':
    main_app = AnimeSeasonsTracker()


