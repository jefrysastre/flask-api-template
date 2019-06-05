

class BaseAuth:

    def __init__(self):
        self.services = []

    def login_required(self, **kwargs):
        if 'url' in kwargs:
            if kwargs['url'] not in self.services:
                self.services.append(kwargs)

        return self.auth.login_required
