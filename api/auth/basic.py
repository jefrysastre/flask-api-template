from flask_httpauth import HTTPBasicAuth
from flask import make_response, jsonify, g, abort
import logging

from .base import BaseAuth


class BasicAuth(BaseAuth):
    def __init__(self, resource, user_field=['id'], password_field='password', _user_field= lambda user: user):
        self.auth = HTTPBasicAuth()

        super(BasicAuth, self).__init__()

        self._resource = resource
        self.user_field = user_field
        self.pass_field = password_field

        self.type="basic"

        @self.auth.get_password
        def get_password(username):
            _user_name = username

            item = None
            if type(user_field) in [str]:
                field_list = [user_field]
            else:
                field_list = user_field

            for _f in user_field:
                query = self._resource.select()
                _field = getattr(self._resource, _f)
                query = query.where(_field == _user_name)
                if len(query) == 1:
                    item = query.get()
                    break

            if item is None:
                # return None when user is not in the database
                return None

            if callable(_user_field):
                g.user = _user_field(item)
            else:
                g.user = getattr(item, _user_field)

            if callable(password_field):
                return password_field(item)
            else:
                return getattr(item, password_field)

        @self.auth.error_handler
        def unauthorized():
            return make_response(jsonify({'error': 'Unauthorized access'}), 401)
