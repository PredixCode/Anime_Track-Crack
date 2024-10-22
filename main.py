from Controller import AnimeController

# TODO: Implement refresh not yet airerd anime for if they aired now. Request whole anime object
# TODO: Move Local Storage implementations to Session!


class AnimeSeasonsTracker:
    def __init__(self):
        self.animeController = AnimeController()

if __name__ == '__main__':
    main_app = AnimeSeasonsTracker()


