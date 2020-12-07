import re

class PriceFormatter(object):

    def __init__(self, price, area):
        if not area:
            area = 0.0
        self.area = area
        if not price:
            price = 0.0
        self.price = price

    def format(self):
        price = self.price
        area = self.area
        if price > 5000:
            return price
        if price and price > 100 and price < 5000 and area and area > 10:
            return price * area
        return 0
