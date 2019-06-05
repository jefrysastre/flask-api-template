_data = {}


class IOC:

    @staticmethod
    def get(name):
        if name in _data:
            return _data[name]
        else:
            raise Exception("IOC does not have a \"{0}\" instance".format(name))

    @staticmethod
    def set(name, instance):
        _data[name] = instance
