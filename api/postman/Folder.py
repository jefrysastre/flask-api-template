

class Folder:
    def __init__(self, name):
        self._items = []
        self._name = name

    def add_item(self, item):
        self._items.append(item)

    @property
    def item(self):
        return [item.to_dict() for item in self._items]

    def to_dict(self):
        d = {
            "name": self._name,
            "item": self.item
        }
        return d
