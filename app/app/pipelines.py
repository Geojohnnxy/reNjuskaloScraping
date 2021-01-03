import json
import logging
import os
from datetime import datetime
from uuid import uuid4

import requests
from app.smarts.string_formatter import StringFormatter
from app.smarts.json_formatter import JsonFormatter
from app.smarts.float_formatter import FloatFormatter
from app.smarts.price_formatter import PriceFormatter
from app.smarts.url_formatter import UrlFormatter

from pprint import pprint

from scrapy import crawler
from scrapy.exceptions import CloseSpider
from scrapy.utils.serialize import ScrapyJSONEncoder


def create_session():
    s = requests.session()
    res = requests.post(os.getenv("LOGIN_URL"), data={"email": os.getenv("DJANGO_U"),
                                                      "password": os.getenv("DJANGO_P")})
    if res.status_code == 200:
        token = res.json()["token"]
        print(token)
        s.headers.update({
            "Authorization": "Token " + token
        })
    else:
        raise CloseSpider('API is down')
    return s


class ProcessingPipeline(object):
    active_properties = []
    subcategory_list = None
    nlp = None
    translation_list = None
    regex_pattern = None

    def get_active_properties(self, spider):
        r = requests.get("http://web.roomba.roombacat.xyz/api/active-properties/", params={"spider": spider.name})
        self.active_properties = r.json()
        return self.active_properties

    def open_spider(self, spider):
        spider.open_pipeline = self

    def process_item(self, item, spider):
        item["spider"] = spider.name
        item["title"] = StringFormatter(content=item["title"]).format()
        item["location"] = StringFormatter(content=item["location"]).format()
        item["owner_name"] = StringFormatter(content=item["owner_name"]).format()
        item["id"] = StringFormatter(content=item["id"], formatting="digit").format()
        item["description"] = StringFormatter(content=item["description"], formatting="multi").format()

        item["listing_info"] = JsonFormatter(data=item["listing_info"]).format()
        item["coordinates"] = JsonFormatter(data=item["coordinates"]).format()
        item["images"] = JsonFormatter(data=item["images"]).format()
        item["owner_info"] = JsonFormatter(data=item["owner_info"]).format()

        item["area"] = FloatFormatter(data=item["area"]).format()
        item["room"] = FloatFormatter(data=item["room"]).format()
        item["price"] = FloatFormatter(data=item["price"]).format()
        item["price"] = PriceFormatter(price=item["price"], area=item["area"]).format()

        item["url"] = UrlFormatter(url=item["url"]).format()
        item["owner_url"] = UrlFormatter(url=item["owner_url"]).format()
        item["active"] = True
        return item


class ExportPipeline(object):

    def __init__(self, stats):
        self.stats = stats
        self.job_detail = {}
        self.spider_data = []
        self.objects = []
        self.scraped_items = []

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.stats)

    def open_spider(self, spider):
        spider_name = spider.name
        try:
            job_id = os.environ['SCRAPY_JOB']
        except:
            job_id = "test"
        self.job_detail = {
            "job_id": job_id,
            "spider": spider_name,
            "start": datetime.utcnow(),
            "finish": None,
            "count": None,
            "log": None,
            "error": None
        }
        # requests.post(os.getenv("API_URL") + "job/", data=self.job_detail)

    def process_item(self, item, spider):
        try:
            res = requests.post("http://web.roomba.roombacat.xyz/api/scraped/", data=json.dumps(item, cls=ScrapyJSONEncoder), headers={"Content-Type":"application/json"})
        except Exception as e:
            logging.info(e)
        return item

    def close_spider(self, spider):
        self.job_detail["finish"] = datetime.utcnow()
        spider.crawler.engine.close_spider(self, reason='finished')
        # requests.post(os.getenv("API_URL") + "job/", data=self.job_detail)
