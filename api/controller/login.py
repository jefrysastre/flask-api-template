from flask import g, jsonify, abort, request
from datetime import datetime, timedelta
import logging
import secrets
import jwt

from api.IOC import IOC
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
                'type': 'login',
                'hash': secrets.token_urlsafe(16),
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


@config.auth.anonymous.login_required(
    desc='Endpoint to send a recovery password email',
    endpoint="{0}.{1}".format(config.app.endpoint, 'recovery'),
    url='{0}{1}'.format(config.export_url, 'recovery')
)
def recovery():
    # Create file server endpoints
    if not hasattr(config, "email"):
        return jsonify({
            "Worked": False,
            "Message": "Missing Email Server Configuration"
        }), 400

    # Check for the element data
    if not request.json:
        return jsonify({
            "Worked": False,
            "Message": "Missing json"
        }), 400

    for _attribute in ['email']:
        if _attribute not in request.json:
            return jsonify({
                "Worked": False,
                "Message": "Missing {0} in json".format(_attribute)
            }), 400

    _email = request.json['email']
    _resource = config.login.model
    select_query = _resource.select()\
        .where(_resource.email == _email)

    if len(select_query) == 0:
        return jsonify({
            "Worked": False,
            "Message": "Email not found"
        }), 404

    if len(select_query) > 1:
        return jsonify({
            "Worked": False,
            "Message": "Multiple emails found"
        }), 404

    if len(select_query) == 1:
        # get the user
        user = select_query.get()

        # create a recovery hash code.
        _hash = secrets.token_urlsafe(16)

        # save the token in the db
        setattr(user, config.login.recovery_field, _hash)
        user.save()

        # create the email body message
        _message = """ <html> <header> </header> <body> <p> Hi, <strong> {0} </strong>  </p></br>
        <p> We received a new password recovery request for this account. </p> </br>
        <p> If it wasn't you, please ignore this email. To proceed and create a new password use the following code: </p>
        </br> <div style="text-align: center;"> <h2> {1} </h2> </div> </br>
        <p> Thanks. </p> """.format(user.name, _hash)

        # send the email with the link
        result = config.email.send(
            email_to=user.email,
            subject="Password recovery email",
            message=_message
        )

        if result.status_code == 201:
            logging.debug("Email recovery sent to user {0}".format(user.id))

            return jsonify({
                "Worked": True,
                "Message": "An email was sent to your inbox. Please follow the instructions we sent on the email to reset your password."
            }),200

        else:
            return jsonify({
                "Worked": False,
                "Message": "Error sending email"
            }), 200


@config.auth.anonymous.login_required(
    desc='Endpoint to validate recovery codes',
    endpoint="{0}.{1}".format(config.app.endpoint, 'validate'),
    url='{0}{1}'.format(config.export_url, 'validate')
)
def validate_code():
    # Check for the element data
    if not request.json:
        return jsonify({
            "Worked": False,
            "Message": "Missing json"
        }), 400

    for _attribute in ['code']:
        if _attribute not in request.json:
            return jsonify({
                "Worked": False,
                "Message": "Missing {0} in json".format(_attribute)
            }), 400

    _code = request.json['code']
    _resource = config.login.model
    _recovery_field = getattr(_resource, config.login.recovery_field)

    select_query = _resource.select() \
        .where(_recovery_field == _code)

    if len(select_query) == 0:
        return jsonify({
            "Worked": False,
            "Message": "Code not found"
        }), 404

    if len(select_query) > 1:
        return jsonify({
            "Worked": False,
            "Message": "Multiple codes found"
        }), 404

    if len(select_query) == 1:
        user = select_query.get()

        # generate a new token valid for 200 sec
        _exp_date = datetime.now() + timedelta(seconds=200)
        _token = jwt.encode(
            {
                'user': user.id,
                'type': 'password reset',
                'hash': secrets.token_urlsafe(16),
                'exp_date': _exp_date.strftime(config.login.date_time_format)
            }, config.auth.token.secret_key)

        setattr(user, config.login.token_field, _token.decode("utf-8"))
        # reset the user password validation code
        setattr(user, config.login.recovery_field, secrets.token_urlsafe(16))

        user.save()

        # Retrieve the config.
    return jsonify(
        {
            'id': user.id,
            'email': user.email,
            'token': user.token,
            'valid': 180
        }), 200


@config.auth.token.login_required(
    desc='Endpoint to reset password',
    endpoint="{0}.{1}".format(config.app.endpoint, 'reset'),
    url='{0}{1}'.format(config.export_url, 'reset')
)
def reset():
    user = g.user

    # Check for the element data
    if not request.json:
        return jsonify({
            "Worked": False,
            "Message": "Missing json"
        }), 400

    for _attribute in ['password']:
        if _attribute not in request.json:
            return jsonify({
                "Worked": False,
                "Message": "Missing {0} in json".format(_attribute)
            }), 400

    _password = request.json['password']

    setattr(user, config.login.password_field, _password)
    setattr(user, config.login.recovery_field, secrets.token_urlsafe(16))

    user.save()

    return jsonify({
        "Worked": True,
        "Message": "Password Reset"
    }),200
