import re

class FloatFormatter(object):

    def __init__(self, data):
        if not data:
            self.data = 0.0
        self.data = data

    def format(self):
        data = self.data
        if not data:
            return 0.0
        if isinstance(data, int):
            return float(data)
        if isinstance(data, list):
            data = " ".join([i for i in data if i])
        if isinstance(data, str):
            data = data.replace(".", "")
            data = data.replace(",", ".")
            data = data.strip()
            data = re.findall(r"[-+]?\d*\.\d+|\d+", data)
            if len(data) > 0:
                data = data[0]
                return float(data)
            else:
                data = 0.0
        return float(data)
