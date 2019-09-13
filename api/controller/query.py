from flask import jsonify, request, g, abort
from functools import wraps
import traceback
import logging

from api.IOC import IOC
config = IOC.get("config")


class QueryBuilder:

    @staticmethod
    def build(fun, access_level):
        @wraps(fun)
        def result(**kwargs):

            if hasattr(config, "access_level"):
                user = g.user
                __user_level = config.access_level(user)

                if __user_level < access_level:
                    return jsonify({
                        "Worked": False,
                        "Message": "Insufficient Access Level"
                    }), 403

            query = fun(**kwargs)

            if 'limit' in request.args:
                query = query.limit(int(request.args['limit']))

            query = query.dicts()

            return jsonify({
                'rows': [item for item in query]
            }), 200

        return result

    @staticmethod
    def handle_error(fun):
        @wraps(fun)
        def result(*args, **kwargs):
            try:
                logging.debug("Executing method: {0}".format(fun))
                return fun(*args, **kwargs)
            except Exception as e:
                if hasattr(config, "telegram"):
                    # config.telegram.send(traceback.format_exc())
                    config.telegram.send_as_document(
                        message = traceback.format_exc(),
                        filename="exeption.gestao.leitos.txt"
                    )
                raise
                # return _return_exception(e)

        return result
