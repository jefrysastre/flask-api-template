from flask_httpauth import HTTPTokenAuth
from flask import make_response, jsonify, g, abort
from datetime import datetime

import jwt
from jwt.exceptions import DecodeError

from .base import BaseAuth


class TokenAuth(BaseAuth):
    def __init__(self, resource, secret_key, date_time_format, action="",
                token_field='token',token_expiration_time=120):

        self.auth = HTTPTokenAuth('Bearer')

        super(TokenAuth, self).__init__()

        self.action = action
        self._resource = resource
        self.token_field = token_field
        self.secret_key = secret_key
        self.token_expiration_time = token_expiration_time
        self.date_time_format = date_time_format

        self.type="token"

        @self.auth.verify_token
        def verify_token(token):
            try:

                data = jwt.decode(token, secret_key)
                if self.action:
                    if data['action'] != self.action or not 'user' in data:
                        abort(401, "Invalid Signature")

                if not 'exp_date' in data:
                    abort(401, "Invalid Signature")

                _exp_date = datetime.strptime(data['exp_date'], self.date_time_format)
                if _exp_date < datetime.now():
                    abort(401, "Session expired")

                query = self._resource.select()
                _field = getattr(self._resource, token_field)
                query = query.where(_field == token)
                if len(query) == 0:
                    return False
                item = query.get()
                g.user = item
                item.save()

                # update the token exp date in the database
                # if (datetime.now() - getattr(item,token_expiration_field)).total_seconds() > token_expiration_time :
                #     abort(401, "Session expired")
                # setattr(item, token_expiration_field, datetime.now() + timedelta(seconds=token_expiration_time))

                return True

            except DecodeError as e:
                abort(401, "Invalid Token")
            except Exception as e:
                raise e

        @self.auth.error_handler
        def unauthorized():
            return make_response(jsonify({'error': 'Unauthorized access'}), 401)

