import unicodedata

class JsonFormatter(object):

    def __init__(self, data):
        if not data or not isinstance(data, dict) or isinstance(data, list):
            self.data = {}
        self.data = data

    def format(self):
        try:
            if isinstance(self.data, list):
                data = []
                for element in self.data:
                    data.append(format_dictionary(element))
                return data
            return format_dictionary(self.data)
        except Exception as e:
            print(e)


def format_dictionary(d):
    result = {}
    for k, v in d.items():
        if isinstance(v, dict):
            v = format_dictionary(v)
        key = k
        key = key.lower()
        key = unicodedata.normalize('NFD', key).encode('ascii', 'ignore').decode()
        key = key.replace(" ", "_")
        result[key] = v
    return result
