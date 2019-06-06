from flask import send_file, g, abort, request, jsonify
import os
import secrets
import logging

from werkzeug import secure_filename

from api.IOC import IOC
config = IOC.get("config")

# ALLOWED_EXTENSIONS = set(['png', 'jpg'])


def _allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in config.file_server.allowed_extensions


@config.file_server.auth.login_required(
    desc='Endpoint to download files from the server',
    endpoint="{0}.{1}".format(config.app.name, 'download'),
    url='{0}{1}'.format(config.export_url, 'download')
)
def download(filename):

    logging.debug("File-Download with id: {0}".format(filename))

    if hasattr(config.file_server, "access_level"):
        __access_level = config.file_server.access_level["GET"]

        if hasattr(config, "access_level"):
            user = g.user
            __user_level = config.access_level(user)

            if __user_level < __access_level:
                return jsonify({
                    "Worked": False,
                    "Message": "Insufficient Access Level"
                }), 403

    folder_path = config.file_server.path

    file_extension = filename.split('.')[-1]
    if folder_path[-1] == '/':
        file_path = folder_path + filename
    else:
        file_path = "{0}/{1}".format(folder_path,filename)

    if os.path.isfile(file_path):
        return send_file(file_path, mimetype='image/{0}'.format(file_extension))
    else:
        abort(404, "File not found: {0}".format(file_path))


@config.file_server.auth.login_required(
    desc='Endpoint to upload files to the server',
    endpoint="{0}.{1}".format(config.app.name, 'upload'),
    url='{0}{1}'.format(config.export_url, 'upload')
)
def upload():

    if hasattr(config.file_server, "access_level"):
        __access_level = config.file_server.access_level["POST"]

        if hasattr(config, "access_level"):
            user = g.user
            __user_level = config.access_level(user)

            if __user_level < __access_level:
                return jsonify({
                    "Worked": False,
                    "Message": "Insufficient Access Level"
                }), 403

    file = request.files['file']
    if file and _allowed_file(file.filename):
        folder_path = config.file_server.path

        filename = secure_filename(file.filename)
        file_extension = filename.split('.')[-1]
        hash = secrets.token_urlsafe(16)

        logging.debug("File-Uploaded with id: {0}".format(hash))

        if folder_path[-1] == '/':
            file_path = "{0}{1}.{2}".format(folder_path, hash, file_extension)
        else:
            file_path = "{0}/{1}.{2}".format(folder_path, hash, file_extension)

        file.save(file_path)

        return jsonify({
            "message": "Image saved",
            "url": "{0}download/{1}.{2}".format(
                config.export_url,
                hash,
                file_extension
            )
        }), 200
    else:
        abort(400)
