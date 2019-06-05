from flask import abort, request, g
from flask_restful import Resource
from playhouse.shortcuts import model_to_dict
import datetime
import logging

from api.IOC import IOC
config = IOC.get("config")


class ServiceBuilder:
    @staticmethod
    def _init(self, *args, **kwargs):
        super(type(self), self).__init__()

    @staticmethod
    def build(resource, **kwargs):
        _fields_service = {
            "__init__": ServiceBuilder._init,
            "_resource": resource,
            "decorators":[],
        }

        if "url" in kwargs:
            url_partial = kwargs["url"]
        else:
            url_partial = kwargs["table"]

        for key, value in kwargs.items():
            _fields_service[key] = value

        if 'auth' in kwargs:
            _fields_service["decorators"] += [kwargs.get('auth').login_required(
                desc='Endpoint to perform CRUD operation on the {0} table'.format(url_partial),
                endpoint="{0}.{1}".format(config.app.endpoint, url_partial),
                url='{0}{1}'.format(config.export_url, url_partial)
            )]

        if 'view_model' in kwargs:
            _fields_service["_view_model"] = kwargs.get('view_model')

        return (
            type(resource._meta.name,(Service,),_fields_service),
            type(resource._meta.name+"List", (ServiceList,), _fields_service)
        )


class BaseResource(Resource):

    def __init__(self):
        self.type_parser = {
            datetime.date: lambda x, level: str(x),
            datetime.datetime: lambda x, level: x.strftime(config.login.date_time_format),
            dict: lambda x, level: self.make_result(x, level)
        }

    def make_result(self, item, level=0):

        if level > 2:
            return "Maximum recursion level achieved"

        for key, value in item.items():
            if type(value) in self.type_parser:
                item[key] = self.type_parser[type(value)](value, level+1)
        return item

    def make_response(self, item, code=200):
        # result = item
        # if hasattr(g, 'user') and hasattr(g.user, 'token'):
        #     result['token'] = g.user.token
        return item, code

    def check_access_level(self):
        __user = g.user
        if hasattr(self, "access_level"):
            if request.method in self.access_level:
                __access_level = self.access_level[request.method]

                if hasattr(config, "access_level"):
                    __user_level = config.access_level(__user)

                if __user_level < __access_level:
                    abort(404, "Insufficient Access Level")

    @staticmethod
    def handle_error(code, **kwargs):
        return kwargs, code


class ServiceList(BaseResource):
    def __init__(self):
        super(ServiceList, self).__init__()

    # Returns the list of elements
    def get(self, **kwargs):
        self.check_access_level()

        _limit = self.limit
        _start = 0

        if 'limit' in request.args.keys():
            if request.args['limit'].isdigit():
                _limit = int(request.args['limit'])
            else:
                return self.handle_error(code=400, **{
                    'message': "Invalid limit value: {}".format(request.args['limit']),
                })

        if 'start' in request.args.keys():
            if request.args['limit'].isdigit():
                _start = int(request.args['start'])
            else:
                return self.handle_error(code=400, **{
                    'message': "Invalid start value: {}".format(request.args['limit']),
                })

        # Apply fields selection
        if hasattr(self, 'select'):
            query = self.select()
        else:
            query = self._resource.select()

        # Apply filters
        if hasattr(self, 'filters'):
            for key, value in request.args.items():
                if key in self.filters:
                    _filter = self.filters[key]
                    # Modify the query to match the filter
                    query = _filter(query, value)

        _count = len(query)

        if _start != 0 and _start >= _count:
            return self.handle_error(code=404, **{
                'message': "Invalid start value {0} out of {1}".format(_start, _count),
            })

        query = query.limit(_limit).offset(_start).dicts()

        _previous = ""
        if _start >= _limit:
            _previous = "{0}{1}?start={2}&limit={3}".format(
                config.export_url,
                self.url,
                _start - _limit,
                _limit
            )

        _next = ""
        if _start + _limit < _count:
            _next = "{0}{1}?start={2}&limit={3}".format(
                config.export_url,
                self.url,
                _start+_limit,
                _limit
            )

        return self.make_response({
            "start": _start,
            "limit": _limit,
            "count": _count,
            "next": _next,
            "previous": _previous,
            'rows': [self.make_result(item) for item in query]
        })

    # Creates a new element in the database
    def post(self):
        self.check_access_level()

        # Check for the element data
        if not request.json:
            return self.handle_error(code=400, **{
                'message': "Missing json"
            })

        try:
            # Creates the element in the database

            # item, _created = self._resource.get_or_create(**request.json)
            # if _created:
            #     item.save()

            item = self._resource(**request.json)
            item.save(
                force_insert =True
            )

        except Exception as e:
            # Return the exception message
            return self.handle_error(code=400, **{
                'type': 'exception',
                'message': str(e),
            })

        # Return the newly created element
        return self.make_response({
            "created": True,
            "item":self.make_result(model_to_dict(item))
        }, 201)


class Service(BaseResource):
    def __init__(self):
        super(Service, self).__init__()

    def get(self, **kwargs):
        self.check_access_level()

        # Create the query
        query = self._resource.select()
        for key, value in kwargs.items():
            _field = getattr(self._resource, key)
            query = query.where(_field == value)

        # If the item does nto exist returns 404
        if len(query) == 0:
            return self.handle_error(code=404, **{
                'message': "{0} with primary key {1} not found".format(
                    self.url.capitalize(),
                    value)
            })

        # Retrieve the item and create the response object
        item = query.dicts().get()
        return self.make_response({"item": self.make_result(item)})

    def put(self, **kwargs):
        self.check_access_level()

        # Check for the element data
        if not request.json:
            return self.handle_error(code=400, **{
                'message': "Missing json"
            })

        # Create a the update query.
        try:
            update_query = self._resource.update(**request.json)
        except AttributeError as ae:
            # Return the exception message
            return self.handle_error(code=400, **{
                'type': 'error',
                'message': "{0} has no attribute {1}".format(
                    self.url.capitalize(),
                    ae.args
                ),
            })

        # Create a select query
        select_query = self._resource.select()
        for key, value in kwargs.items():
            _field = getattr(self._resource, key)
            select_query = select_query.where(_field == value)
            update_query = update_query.where(_field == value)
        _affected_rows = len(select_query)

        # Return 404 if there no element to update
        if _affected_rows == 0:
            return self.handle_error(code=404, **{
                'message': "{0} with primary key {1} not found".format(
                    self.url.capitalize(),
                    value)
            })

        # Update the selected item
        elif _affected_rows == 1:
            try:
                update_query.execute()
                item = select_query.get()

            except Exception as e:
                # Return the exception message
                return self.handle_error(code=500, **{
                    'type': 'exception',
                    'message': str(e),
                })

        else:

            # Returns an error if the query returns multiple items
            return self.handle_error(code=300, **{
                'message': "{0} with primary key {1} return multiple items".format(
                    self.url.capitalize(),
                    value)
            })

        # Return the newly updated element
        return self.make_response({
            "updated": True,
            "item": self.make_result(model_to_dict(item))
        }, 200)

    def delete(self, **kwargs):
        self.check_access_level()

        # Create a query and get the element to delete
        select_query = self._resource.select()
        delete_query = self._resource.delete()

        select_query = self._resource.select()
        for key, value in kwargs.items():
            _field = getattr(self._resource, key)
            select_query = select_query.where(_field == value)
            delete_query = delete_query.where(_field == value)
        _affected_rows = len(select_query)

        # Return 404 if there no element to update
        if _affected_rows == 0:
            return self.handle_error(code=404, **{
                'message': "{0} with primary key {1} not found".format(
                    self.url.capitalize(),
                    value)
            })

        # Returns an error if the query returns multiple items
        if _affected_rows > 1:
            return self.handle_error(code=300, **{
                'message': "{0} with primary key {1} return multiple items".format(
                    self.url.capitalize(),
                    value)
            })

        item = select_query.get()

        try:
            # delete the item in the database
            # item.delete_instance()
            delete_query.execute()

        except Exception as e:
            # Return the exception message
            return self.handle_error(code=500, **{
                'type': 'exception',
                'message': str(e),
            })

        # Return the newly updated element
        return self.make_response({
            "deleted": True,
            "item": self.make_result(model_to_dict(item))
        }, 200)