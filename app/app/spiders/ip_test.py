# -*- coding: utf-8 -*-
import json
import re

import scrapy
from scrapy import Request


class IpSpider(scrapy.Spider):
    name = 'ipcheck'
    allowed_domains = ['njuskalo.hr']
    start_urls = ["http://ipecho.net/"]*200

    def start_requests(self):
        for url in self.start_urls:
            yield Request(url=url, dont_filter=True)


    def parse(self, response):
        ip = response.css("body > main:nth-child(1) > div:nth-child(1) > h1:nth-child(1)::text").extract()
        print(ip)
