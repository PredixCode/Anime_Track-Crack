from Controller import AnimeController
import time, webbrowser

# TODO: Implement refresh not yet airerd anime for if they aired now. Request whole anime object
# TODO: Implement ThreadManagement
# TODO: Implement batch download --> ask user, weather to download this ep (,which he clicked on), entire Season or the whole Anime Lineage ()
# TODO: Implement auto resolution mode depending on bandwidth of the user


class AnimeSeasonsTracker:
    def __init__(self):
        self.animeController = AnimeController()
        time.sleep(2.5)
        webbrowser.open_new('http://127.0.0.1:5000/')

if __name__ == '__main__':
    main_app = AnimeSeasonsTracker()


