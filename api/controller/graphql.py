from flask import request, jsonify
from ariadne.constants import PLAYGROUND_HTML
from ariadne import graphql_sync

from api.IOC import IOC
config = IOC.get("config")
schema = IOC.get("schema")


@config.graphql.auth.login_required(
    desc='GraphQL Playgroud',
    endpoint="{0}.{1}".format(config.app.name, config.graphql.url),
    url='{0}{1}'.format(config.export_url, config.graphql.url)
)
def playgroud():
    # On GET request serve GraphQL Playground
    # You don't need to provide Playground if you don't want to
    # but keep on mind this will not prohibit clients from
    # exploring your API using desktop GraphQL Playground app.
    return PLAYGROUND_HTML, 200


@config.graphql.auth.login_required(
    desc='GraphQL Post Query Endpoint',
    endpoint="{0}.{1}".format(config.app.name, config.graphql.url),
    url='{0}{1}'.format(config.export_url, config.graphql.url)
)
def post_query():
    # GraphQL queries are always sent as POST
    data = request.get_json()

    # Note: Passing the request to the context is optional.
    # In Flask, the current request is always accessible as flask.request
    success, result = graphql_sync(
        schema,
        data,
        context_value=request,
        # debug=app.debug
    )

    status_code = 200 if success else 400
    return jsonify(result), status_code