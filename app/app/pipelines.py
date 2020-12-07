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
    subcategory_list = None
    nlp = None
    translation_list = None
    regex_pattern = None

    def open_spider(self, item):
        # TODO fetch
        pass

    def process_item(self, item, spider):
        item["spider"] = spider.name
        item["title"] = StringFormatter(content=item["title"]).format()
        item["location"] = StringFormatter(content=item["location"]).format()
        item["owner"] = StringFormatter(content=item["owner"]).format()
        item["id"] = StringFormatter(content=item["id"], formatting="digit").format()
        item["description"] = StringFormatter(content=item["description"], formatting="multi").format()

        item["listing_info"] = JsonFormatter(data=item["listing_info"]).format()
        item["coordinates"] = JsonFormatter(data=item["coordinates"]).format()
        item["images"] = JsonFormatter(data=item["images"]).format()
        item["owner_info"] = JsonFormatter(data=item["owner_info"]).format()

        item["area"] = FloatFormatter(data=item["area"]).format()
        item["rooms"] = FloatFormatter(data=item["rooms"]).format()
        item["price"] = FloatFormatter(data=item["price"]).format()
        item["price"] = PriceFormatter(price=item["price"], area=item["area"]).format()

        item["url"] = UrlFormatter(url=item["url"]).format()
        item["owner_id"] = UrlFormatter(url=item["owner_id"]).format()
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
        # item_ = item.copy()
        # # for key in ["tags", "subcategory", "images"]:
        # #     item_[key] = json.dumps(item_[key])
        # if item_ not in self.scraped_items:
        #     res = requests.post(os.getenv("API_URL") + "object-bot/", json=json.dumps([item_], cls=ScrapyJSONEncoder))
        #     if res.status_code != 201:
        #         logging.error(res.text)
        #         logging.error("not imported")
        return item


    def close_spider(self, spider):
        self.job_detail["finish"] = datetime.utcnow()
        self.job_detail["scraped_count"] = self.stats.get_stats()["item_scraped_count"]
        # bulbasaur_ping(spider.name + " bot finished")
        # bulbasaur_ping(self.job_detail)
        scraped_count = self.stats.get_stats()["item_scraped_count"]
        previous_scraped_counts = [i["scraped_count"] for i in self.spider_data["job_set"] if i["scraped_count"] is not None]
        if len(previous_scraped_counts) > 0:
            avg = sum(previous_scraped_counts)/len(previous_scraped_counts)
            if scraped_count*0.8 < avg or scraped_count > avg:
                logging.debug("Deactivating missing objects")
                # deactivate_existing_objects()
        # requests.post(os.getenv("API_URL") + "job/", data=self.job_detail)
