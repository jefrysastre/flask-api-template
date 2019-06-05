from flask import g, jsonify, abort, request
from datetime import datetime, timedelta
import logging
import jwt

from IOC import IOC
config = IOC.get("config")


@config.login.auth.login_required(
    desc='Endpoint to login and receive a token',
    endpoint="{0}.{1}".format(config.app.endpoint, 'login'),
    url='{0}{1}'.format(config.export_url, 'login')
)
def login():
    user = g.user
    _token_exp_date = None

    try:
        data = jwt.decode(user.token, config.auth.token.secret_key)
        _token_exp_date = datetime.strptime(data['exp_date'], config.login.date_time_format)
    except Exception as e:
        pass

    logging.debug("User logged in with id: {0}".format(user.id))

    if _token_exp_date and _token_exp_date > datetime.now():
        logging.info("User {0} token valid for {1}".format(user.id, _token_exp_date - datetime.now()))

    else:
        logging.info("Generating new user token.")
        _exp_date = datetime.now() + timedelta(seconds=config.login.expires_miliseconds)

        _token = jwt.encode(
            {
                'user': user.id,
                'exp_date': _exp_date.strftime(config.login.date_time_format)
            }, config.auth.token.secret_key)

        setattr(user, config.login.token_field, _token.decode("utf-8"))
        user.save()

    # Retrieve the config.
    return jsonify(
        {
            'id': user.id,
            'email': user.email,
            'services': config.login.services,
            'token': user.token,
        }), 200


@config.auth.token.login_required(
    desc='Endpoint to logout and disable the current token',
    endpoint="{0}.{1}".format(config.app.endpoint, 'logout'),
    url='{0}{1}'.format(config.export_url, 'logout')
)
def logout():
    user = g.user
    setattr(user, config.login.token_field, "logout")

    logging.debug("User logged out with id: {0}".format(user.id))

    user.save()
    return jsonify({
        "Worked": True,
        "Message": "You are out!"
    }),200



