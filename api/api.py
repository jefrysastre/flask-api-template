from flask import Flask
import flask_restful
import json
from flask_cors import CORS

from .IOC import IOC

import api.postman as postman


class API(object):
    def __init__(self, config):
        IOC.set("config", config)

        self.export_url = config.export_url
        self.base_url = config.app.base_url
        if self.base_url[-1] != '/':
            self.base_url += '/'

        # create a PostMan Collection
        self.postman_collection = postman.Collection(
            config.postman.id,
            config.app.name
        )
        self.postman_config = config.postman

        # Create the Flask App
        self.endpoint = config.app.endpoint
        self.app = Flask(config.app.name)

        self.api = flask_restful.Api(self.app)
        self.resources = []

        # Create login endpoints
        if hasattr(config, "login"):
            self.enable_login()

        # Create file server endpoints
        if hasattr(config, "file_server"):
            self.enable_file_server()

        # Create loggin configuration
        if hasattr(config, "logger"):
            import logging
            import logging.handlers
            from flask.logging import default_handler
            from flask import request

            file_handler = logging.handlers.TimedRotatingFileHandler(
                filename=config.logger.filename,
                when=config.logger.when,
                backupCount=config.logger.backupCount
            )

            file_handler.suffix = "%Y.%m.%d.%H.%M.%S.log"
            file_handler.setLevel(config.logger.level)

            logging.basicConfig(level=logging.DEBUG, handlers=[default_handler, file_handler])

            @self.app.after_request
            def after(response):
                logging.info("{0} {1} : {2}".format(
                    request.method,
                    request.url,
                    response.status
                ))
                return response

        # Create Generic Controllers
        for _resource in config.resources:
            _resource_model = _resource["model"]
            self.add_service(resource_model=_resource_model, **_resource)

        # Create Generic Stored Procedures
        for _query in config.queries:

            if 'url' not in _query:
                raise Exception("Missing url in Query")

            if 'method' not in _query:
                raise Exception("Invalid Query {0}. Missing method".format(_query["url"]))

            if 'query' not in _query:
                raise Exception("Invalid Stored Query {0}. Missing query parameter".format(_query["url"]))

            self.add_query(**_query)

        # Enable CORS operations
        if config.CORS:
            cors = CORS(self.app, resources=config.CORS_resources)

        # This hook ensures that a connection is opened to handle any queries
        # generated by the request.
        @self.app.before_request
        def _db_connect():
            if config.db.is_closed():
                config.db.connect()

        # This hook ensures that the connection is closed when we've finished
        # processing the request.
        @self.app.teardown_request
        def _db_close(exc):
            if not config.db.is_closed():
                config.db.close()

        # Set debug options
        if config.app.mode.lower() == 'debug':
            self.app.debug = True
        elif config.app.mode.lower() == 'server':
            self.app.debug = False

    def enable_login(self):
        from .controller.login import login, logout

        self.app.route(self.base_url + 'login', methods=["GET"])(login)
        self.app.route(self.base_url + 'logout', methods=["GET"])(logout)

        self.postman_collection.add_item(
            item=postman.Request(
                name="Login",
                auth="basic",
                url="{0}login".format(self.postman_config.base_url),
                method="GET",
                description='Endpoint to login and receive a token'
            )
        )

        self.postman_collection.add_item(
            item=postman.Request(
                name="Logout",
                url="{0}logout".format(self.postman_config.base_url),
                method="GET",
                auth="token",
                description='Endpoint to logout'
            )
        )

    def enable_file_server(self):
        from .controller.file import download, upload

        self.app.route(self.base_url + 'download/<string:filename>', methods=["GET"])(download)
        self.app.route(self.base_url + 'upload', methods=["POST"])(upload)

        self.postman_collection.add_item(
            item=postman.Request(
                name="Download",
                url="{0}download/{{SampleFile.jpg}}".format(self.postman_config.base_url),
                method="GET",
                auth="token",
                description='Endpoint to download a file'
            )
        )

        self.postman_collection.add_item(
            item=postman.Request(
                name="Upload",
                url="{0}upload".format(self.postman_config.base_url),
                method="POST",
                auth="token",
                description='Endpoint to upload a file',
                body={
                    "mode": "formdata",
                    "formdata": [
                        {
                            "key": "file",
                            "value": None,
                            "type": "file"
                        }
                    ]
                }
            )
        )

    def add_service(self, resource_model, **kwargs):
        from .controller.resource import ServiceBuilder

        if "url" in kwargs:
            url_partial = kwargs["url"]
        else:
            url_partial = kwargs["table"]

        _service, _service_list = ServiceBuilder.build(resource_model, **kwargs)

        self.resources.append((
                _service_list,
                "{0}{1}".format(self.base_url, url_partial),
                "{}_list".format(url_partial)
            )
        )

        _params = ""
        for _param in kwargs["params"]:
            _params = "{0}/{1}".format(_params, _param)

        self.resources.append((
                _service,
                "{0}{1}{2}".format(self.base_url, url_partial, _params),
                "{}_item".format(url_partial)
            )
        )

        # Geneate Postman Folder
        _folder = postman.Folder(url_partial.capitalize())

        # Include the Get request
        _folder.add_item(
            item=postman.Request(
                name="Get_{0}".format(url_partial.capitalize()),
                url="{0}{1}".format(self.postman_config.base_url, url_partial),
                auth=kwargs['auth'].type if 'auth' in kwargs else None,
                method="GET",
                description="Get the {0} items".format(url_partial.capitalize())
            )
        )

        # Include the Post request
        _folder.add_item(
            item=postman.Request(
                name="Post_{0}".format(url_partial.capitalize()),
                url="{0}{1}".format(self.postman_config.base_url, url_partial),
                auth=kwargs['auth'].type if 'auth' in kwargs else None,
                method="POST",
                description="Post a {0} item".format(url_partial.capitalize()),
                headers=[{
                    "key": "Content-Type",
                    "name": "Content-Type",
                    "type": "text",
                    "value": "application/json"
                }],
                body={
                    "mode": "raw",
                    "raw": json.dumps({
                        key: field.field_type for key, field in resource_model._meta.fields.items()
                    }, indent=4)
                }
            )
        )

        # Include the Put request
        _folder.add_item(
            item=postman.Request(
                name="Put_{0}".format(url_partial.capitalize()),
                url="{0}{1}/{{id}}".format(self.postman_config.base_url, url_partial),
                auth=kwargs['auth'].type if 'auth' in kwargs else None,
                method="PUT",
                description="Put a {0} item".format(url_partial.capitalize()),
                headers=[{
                    "key": "Content-Type",
                    "name": "Content-Type",
                    "type": "text",
                    "value": "application/json"
                }],
                body={
                    "mode": "raw",
                    "raw": json.dumps({
                        key: field.field_type for key, field in resource_model._meta.fields.items()
                    }, indent=4)
                }
            )
        )

        # Include the Delete request
        _folder.add_item(
            item=postman.Request(
                name="Delete_{0}".format(url_partial.capitalize()),
                url="{0}{1}/{{id}}".format(self.postman_config.base_url, url_partial),
                auth=kwargs['auth'].type if 'auth' in kwargs else None,
                method="DELETE",
                description="Delete a {0} item".format(url_partial.capitalize())
            )
        )

        self.postman_collection.add_item(item=_folder)

    def add_query(self, query, url, method, auth=None, desc="", access_level=0):
        from .controller.query import QueryBuilder

        # Encapsulate the query into a method
        _func = QueryBuilder.build(query, access_level)

        # Set the auth decorator
        if auth is not None:
            _func = auth.login_required(
                desc= desc,
                endpoint="{0}.{1}".format(self.endpoint, url),
                url='{0}{1}'.format(self.export_url, url)
            )(_func)

        # Set a handle error function as decorator as well
        _func = QueryBuilder.handle_error(_func)

        self.postman_collection.add_item(
            item=postman.Request(
                name=url.capitalize(),
                url="{0}{1}".format(self.postman_config.base_url, url),
                auth=auth.type,
                method=method,
                description=desc
            )
        )

        # Create the endpoint
        self.app.route(rule=self.base_url + url, methods=[method], endpoint=url)(_func)

    def add_method(self, callback, url, method, auth=None, desc=""):
        from .controller.query import QueryBuilder

        _func = callback
        if auth is not None:
            _func = auth.login_required(
                desc= desc,
                endpoint="{0}.{1}".format(self.endpoint, url),
                url='{0}{1}'.format(self.export_url, url)
            )(callback)

        _func = QueryBuilder.handle_error(_func)

        self.postman_collection.add_item(
            item=postman.Request(
                name=url.capitalize(),
                url="{0}{1}".format(self.postman_config.base_url, url),
                auth=auth.type,
                method=method,
                description=desc
            )
        )

        self.app.route(self.base_url + url, methods=[method])(_func)

    def run(self):
        for _resource, _url, _end_point in self.resources:
            self.api.add_resource(_resource, _url, endpoint = _end_point)

    def generate_postman_collection(self, path):
        with open(path, 'w') as outfile:
            json.dump(
                obj=self.postman_collection.to_dict(),
                fp=outfile,
                indent=4,
                sort_keys=True
            )
