from Controller import AnimeController
import time, webbrowser

# TODO: Implement refresh not yet airerd anime for if they aired now. Request whole anime object
# TODO: Move Local Storage implementations to Session!


class AnimeSeasonsTracker:
    def __init__(self):
        self.animeController = AnimeController()
        time.sleep(2.5)
        webbrowser.open_new('http://127.0.0.1:5000/')

if __name__ == '__main__':
    main_app = AnimeSeasonsTracker()


