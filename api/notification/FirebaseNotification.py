import httplib2
from json import dumps


class FireBaseNotification:
    def __init__(self, resource, firebase_token, token_field='notification_token'):
        self.firebase_url = 'https://fcm.googleapis.com/fcm/send'
        self.firebase_token = firebase_token
        self.token_field = token_field

        self.resource = resource

    def send(self, user, title, message):

        _notification_token = None
        if callable(self.token_field):
            _notification_token = self.token_field(user)

        if hasattr(user, self.token_field):
            _notification_token = getattr(user, self.token_field)

        if _notification_token:

            notification = {
                'sound': 'default',
                'badge': '1',
                'title': title,
                'body': message
            }

            fields = {
                'to': _notification_token,
                'priority': 'high',
                'content_available': True,
                'notification': notification
            }

            response = httplib2.Http().request(
                uri= self.firebase_url,
                method='POST',
                headers={
                    'Authorization': 'key={0}'.format(self.firebase_token),
                    'Content-Type': 'application/json'},
                body=dumps(fields))
        else:
            raise  Exception("Unable to send notification via Firebase")