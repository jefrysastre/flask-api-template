from flask_httpauth import HTTPBasicAuth
from flask import make_response, jsonify, g

from .base import BaseAuth


class AnonymousAuth(BaseAuth):
    def __init__(self, default):
        self.auth = HTTPBasicAuth()
        self.default = default

        super(AnonymousAuth, self).__init__()
        self.type = ""

        @self.auth.verify_password
        def verify_password(username, password):
            g.user = self.default
            return True

