# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class AppItem(scrapy.Item):
    # define the fields for your item here like:
    url = scrapy.Field()
    title = scrapy.Field()
    area = scrapy.Field()
    price = scrapy.Field()
    images = scrapy.Field()
    owner_name = scrapy.Field()
    owner_url = scrapy.Field()
    owner_info = scrapy.Field()
    id = scrapy.Field()
    room = scrapy.Field()
    description = scrapy.Field()
    listing_info = scrapy.Field()
    location = scrapy.Field()
    active = scrapy.Field()
    coordinates = scrapy.Field()
    spider = scrapy.Field()
    pass
