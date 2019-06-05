

_auth = {
    "basic": {
        "type": "basic",
        "basic": [
            {
                "key": "username",
                "value": "user",
                "type": "string"
            },
            {
                "key": "password",
                "value": "password",
                "type": "string"
            },
            {
                "key": "showPassword",
                "value": True,
                "type": "boolean"
            }
        ]
    },
    "token": {
        "type": "bearer",
        "bearer": [
            {
                "key": "token",
                "value": "{{token}}",
                "type": "string"
            }
        ]
    }
}


class Request:
    def __init__(self, name, url, method, auth=None, description="", headers=[], body=None):

        self._name = name

        self.method = method
        self.url = url
        self.headers = headers

        if auth:
            self.auth = _auth[auth]

        self.response = []
        self.description = description

        if body:
            self.body = body

    def to_dict(self):
        d = {
            "name": self._name,
            "request": {
                k: v for k, v in self.__dict__.items() if not k.startswith("_")
            }
        }

        return d
