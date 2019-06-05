from uuid import uuid4

methods_order = ["GET", "POST", "PUT", "PATCH", "DELETE", "COPY", "HEAD",
                 "OPTIONS", "LINK", "UNLINK", "PURGE"]


class Collection:

    def __init__(self, id, name):
        # self._folders = []
        self._items = []

        self.info = {
            "_postman_id": id,
            "name": name,
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
        }

    def add_item(self, item):
        self._items.append(item)

    @property
    def order(self):
        return [item.id for item in self._items]

    @property
    def item(self):
        return [item.to_dict() for item in self._items]

    def to_dict(self):
        d = {
            "info": self.info,
            "item": self.item
        }
        return d