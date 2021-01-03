# -*- coding: utf-8 -*-
import json
import logging
import re
from difflib import SequenceMatcher

import redis
import requests
from scrapy import Request
from scrapy.utils.serialize import ScrapyJSONEncoder
from scrapy_redis.spiders import RedisSpider

import scrapy

from app.items import AppItem
from scrapy.exceptions import CloseSpider


class NjuskaloUrlSpider(scrapy.Spider):
    name = 'njuskalo'
    allowed_domains = ['njuskalo.hr']
    start_urls = ['https://www.njuskalo.hr/prodaja-stanova/zagreb?page=1']
    pattern = re.compile('([^\s\w]|_)+')
    custom_settings = {
        'DUPEFILTER_CLASS': 'scrapy.dupefilters.RFPDupeFilter',
        'SCHEDULER': 'scrapy.core.scheduler.Scheduler',
        'DOWNLOAD_DELAY': 25,
        'RETRY_TIMES': 100,
    }

    def __init__(self, page=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.open_pipeline = None
        self.active_properties = {}
        self.property_objects = []
        self.urls_to_scrape = []
        self.urls_to_deactivate = []
        self.r = redis.StrictRedis(host='192.168.147.99', port=6379, db=0, password="redis")
        self.page = page

    # def start_requests(self):
    #     for url in self.start_urls:
    #         yield Request(
    #             url=url, meta={
    #                 "pyppeteer": True,
    #                 "headers": {
    #                     "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:84.0) Gecko/20100101 Firefox/84.0",
    #                 },
    #                 # "pyppeteer_page_coroutines": {
    #                 #     NavigationPageCoroutine("click", selector="div.PaginationContainer:nth-child(1) > nav:nth-child(1) > ul.Pagination-items > li:last-child > button"),
    #                 # },
    #             }
    #         )

    def start_requests(self):
        if self.page:
            url = f"https://www.njuskalo.hr/prodaja-stanova/zagreb?page={self.page}"
            yield scrapy.Request(url, callback=self.parse, dont_filter=True)
        else:
            for url in self.start_urls:
                yield scrapy.Request(url, callback=self.parse, dont_filter=True)

    def NextPageUrl_Extract_FromUrl(self, url):
        page_str = re.findall(r"page=+\d*", url)
        page_num_ = re.findall(r"\d+", page_str[0])
        page_num = int(page_num_[0]) + 1
        page_str_ = "page=" + str(page_num)
        url = url.replace(page_str[0], page_str_)
        return url, page_num

    def string_compare(self, string_1, string_2):
        string_1 = self.pattern.sub('', string_1)
        string_2 = self.pattern.sub('', string_2)
        similarity = SequenceMatcher(None, string_1, string_2).quick_ratio()
        return similarity

    def calculate_missing_urls(self):
        for property in self.property_objects:
            if self.active_properties.get(property.get("url")):
                logging.info(f"active property exists {property.get('url')}")
                if int(property["price"]) != int(self.active_properties.get(property.get("url")).get("price")):
                    self.urls_to_scrape.append(property.get("url"))
                    continue
                if self.string_compare(property["title"],
                                       self.active_properties.get(property.get("url")).get("title")) < 0.95:
                    self.urls_to_scrape.append(property.get("url"))
                    continue
            else:
                logging.info(f"new property: {property.get('url')}")
                self.urls_to_scrape.append(property.get("url"))
        active_properties = self.active_properties.keys()
        scraped_properties = [i["url"] for i in self.property_objects]
        self.urls_to_deactivate = list(set(active_properties) - set(scraped_properties))

    def parse(self, response):
        objects = response.css(".EntityList-item")
        urls = []
        for object in objects:
            url = object.css(".EntityList-item::attr('data-href')").extract()
            if not url:
                continue
            url = "https://www.njuskalo.hr" + url[0]
            price = object.css(".price--eur::text").extract()
            if len(price) > 0:
                price = price[0].strip().replace(".", "")
            title = object.css(".entity-title > a::text").extract()
            if len(title) > 0:
                title = title[0].strip()
            scraped_data = {
                "title": title,
                "price": price,
                "url": url
            }
            if len([i for i in scraped_data.values() if i]) < 3:
                continue
            self.property_objects.append(scraped_data)

        # for url in urls:
        #     yield scrapy.Request(url, callback=self.parse_object, dont_filter=True)

        if len(objects):
            next_page_url, page_num = self.NextPageUrl_Extract_FromUrl(response.url)
            yield scrapy.Request(next_page_url, callback=self.parse, dont_filter=True)
        else:
            if not self.active_properties:
                self.active_properties = self.open_pipeline.get_active_properties(spider=self)
            self.calculate_missing_urls()
            logging.info(f"total properties to scrape {len(self.urls_to_scrape)}")
            for url in self.urls_to_scrape:
                self.r.lpush('njuskalo:start_urls', url)

            items = []
            logging.info(f"total properties to deactivate {len(self.urls_to_deactivate)}")
            for property in self.urls_to_deactivate:
                items.append({
                    "url": property,
                    "spider": self.name,
                    "active": False
                })
            try:
                res = requests.post("http://web.roomba.roombacat.xyz/api/scraped/", data=json.dumps(items, cls=ScrapyJSONEncoder), headers={"Content-Type":"application/json"})
            except Exception as e:
                logging.info(e)


class NjuskaloPropertySpider(RedisSpider):
    name = 'njuskalo_property'
    redis_key = 'njuskalo:start_urls'

    custom_settings = {
        'DOWNLOAD_DELAY': 10,
        'RETRY_TIMES': 100,
    }

    def parse(self, response):
        try:
            item = AppItem()

            item["url"] = response.url
            item["title"] = response.css(".ClassifiedDetailSummary-title *::text").extract()
            if len(item["title"]) > 0:
                item["title"] = item["title"][0].replace("(prodaja)", "").replace("(iznajmljivanje)", "")
            item["price"] = response.css(".ClassifiedDetailSummary-priceForeign *::text").extract()
            item["id"] = response.css(".ClassifiedDetailSummary-adCode *::text").extract()

            item["description"] = response.css(".ClassifiedDetailDescription-text *::text").extract()

            item["owner_name"] = response.css(
                ".ClassifiedDetailOwnerDetailsWrap--positionPrimary .ClassifiedDetailOwnerDetails-title *::text").extract()
            item["owner_url"] = response.css(
                ".ClassifiedDetailOwnerDetailsWrap--positionPrimary .ClassifiedDetailOwnerDetails-linkAllAds::attr('href')").extract()
            item["owner_info"] = ""

            owner_info_dict = {}
            owner_info = response.css(
                ".ClassifiedDetailOwnerDetailsWrap--positionPrimary .ClassifiedDetailOwnerDetails-contactEntry")
            for info in owner_info:
                info_ = info.css("a::attr('href')").extract()
                if len(info_) > 0:
                    info_ = info_[0]
                    if info_ and "tel" in info_:
                        info_ = info_.replace("tel:", "")
                        txt = re.sub(r"[^a-zA-Z0-9]+", ' ', info.css("a *::text").extract()[0])
                        txt = [i for i in txt.split() if i.isalpha() and "Telefon" not in i]
                        if len(txt) > 0:
                            txt = " ".join(txt)
                            owner_info_dict[txt] = info_
                        else:
                            num_of_tels = len([i for i in owner_info_dict if "tel" in i])
                            owner_info_dict["tel{}".format(num_of_tels + 1)] = info_
                    elif info_ and "mail" in info_:
                        info_ = info_.replace("mailto:", "")
                        num_of_email = len([i for i in owner_info_dict if "email" in i])
                        owner_info_dict["email{}".format(num_of_email + 1)] = info_
                    elif info_:
                        num_of_web = len([i for i in owner_info_dict if "web" in i])
                        owner_info_dict["web{}".format(num_of_web + 1)] = info_
            item["owner_info"] = owner_info_dict

            extra_info = response.css(".ClassifiedDetailBasicDetails-listTerm")
            extra = {}
            for info in extra_info:
                name = " ".join(info.css("*::text").extract()).strip()
                value = " ".join(response.xpath(
                    "//dt[contains(.,'{}')]/following-sibling::*[1]/span/text()".format(name)).extract()).strip()
                d = {
                    name: value
                }
                extra.update(d)

            additional_info = response.css(".ClassifiedDetailPropertyGroups-group")
            for info in additional_info:
                title = info.css("h3 *::text").extract()[0]
                li_s = info.css("li *::text").extract()
                if len([i for i in li_s if ":" in i]) > 0:
                    li_s_dict = {}
                    for li in li_s:
                        li = li.strip()
                        li = li.split(":")
                        li_s_dict.update({li[0].strip(): li[1].strip()})
                    extra.update({title: li_s_dict})
                else:
                    li_s_list = []
                    for li in li_s:
                        li = li.strip()
                        li_s_list.append(li)
                    extra.update({title: li_s_list})

            images_ = []
            images = response.css(".ClassifiedDetailGallery-slideImage")
            for image in images:
                plan = False
                if "groundPlan" in image.css("::attr('class')").extract():
                    plan = True
                image = image.css("::attr('data-src')").extract()
                if image:
                    images_.append({
                        "plan": plan,
                        "url": image[0]
                    })
            item["images"] = images_

            item["location"] = extra.pop("Lokacija", None)
            item["room"] = extra.pop("Broj soba", None)
            item["area"] = extra.pop("Stambena površina", None)
            item["listing_info"] = extra

            item["coordinates"] = {}
            scripts = response.css("script")
            for script in scripts:
                text = script.extract()
                if "mapData" in text:
                    js = text.split("script")
                    js = js[1].replace('>\n    app.boot.push(', "")
                    js = js.replace(");\n</", "")
                    data = json.loads(js)
                    coordinates = data.get("values").get("mapData").get("center")
                    item["coordinates"] = {
                        "lat": coordinates[1],
                        "lon": coordinates[0]
                    }
                    break

            yield item

        except Exception as e:
            print("ERROR {}".format(e))
