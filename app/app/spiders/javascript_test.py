# -*- coding: utf-8 -*-
import json
import re

# import pyppeteer
import scrapy
from scrapy import Request


class IpSpider(scrapy.Spider):
    name = 'jscheck'
    allowed_domains = ['njuskalo.hr']
    # start_urls = ["https://bot.sannysoft.com/"]
    start_urls = ["http://ipecho.net/"]*200

    def start_requests(self):
        for url in self.start_urls:
            yield Request(
                url=url, dont_filter=True, meta={
                    "pyppeteer": True,
                    "headers": {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:84.0) Gecko/20100101 Firefox/84.0",
                    }
                }
            )
    #
    # async def parse(self, response, page: pyppeteer.page.Page):
    #     await page.screenshot(options={"path": "quotes.png", "fullPage": True})

