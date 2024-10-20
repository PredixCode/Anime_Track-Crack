from Controller import AnimeController

# TODO: Implement refresh not yet airerd anime for if they aired now. Request whole anime object
# TODO: Implement user login and security, also multiple sessions like spring seccurity & redis
# TODO: FRONTEND: Place switch (wacth/downlaod) in every anime box, left, next to refresh available ep's, instead of lame modal that pops up and asks for this


class AnimeSeasonsTracker:
    def __init__(self):
        self.animeController = AnimeController()

if __name__ == '__main__':
    main_app = AnimeSeasonsTracker()


