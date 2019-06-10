import logging
from flask import g


class LogDBHandler(logging.Handler):
    """
    Customized logging handler that puts logs to the database.
    """
    def __init__(self, resource, params):
        logging.Handler.__init__(self)
        self._resource = resource
        self._params = params

    def emit(self, record):
        user = g.user

        params = {
            # 'user_id': user.id,
            # 'entry': record
        }

        for _key, _field in self._params:
            params[_key]: _field(user, record)

        # Creates the element in the database
        item = self._resource(**params)
        item.save(
            force_insert=True
        )