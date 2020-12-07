# -*- coding: utf-8 -*-
import json
import re

import scrapy

from app.items import AppItem


class NjuskaloSpider(scrapy.Spider):
    name = 'njuskalo'
    allowed_domains = ['njuskalo.hr']
    start_urls = ['https://www.njuskalo.hr/prodaja-stanova/zagreb?page=1']

    def NextPageUrl_Extract_FromUrl(self, url):
        page_str = re.findall(r"page=+\d*", url)
        page_num_ = re.findall(r"\d+", page_str[0])
        page_num = int(page_num_[0]) + 1
        page_str_ = "page=" + str(page_num)
        url = url.replace(page_str[0], page_str_)
        return url

    def parse(self, response):
        object_urls = response.css(".EntityList-item--Regular::attr('data-href')").extract()
        for url in object_urls:
            url = "https://www.njuskalo.hr" + url
            yield scrapy.Request(url, callback=self.parse_object, dont_filter=True)

        # if len(object_urls):
        #     next_page_url = self.NextPageUrl_Extract_FromUrl(response.url)
        #     yield scrapy.Request(next_page_url, callback=self.parse)


    def parse_object(self, response):
        try:
            item = AppItem()

            item["url"] = response.url
            item["title"] = response.css(".ClassifiedDetailSummary-title *::text").extract()
            item["price"] = response.css(".ClassifiedDetailSummary-priceForeign *::text").extract()
            item["id"] = response.css(".ClassifiedDetailSummary-adCode *::text").extract()

            item["description"] = response.css(".ClassifiedDetailDescription-text *::text").extract()

            item["owner"] = response.css(".ClassifiedDetailOwnerDetailsWrap--positionPrimary .ClassifiedDetailOwnerDetails-title *::text").extract()
            item["owner_id"] = response.css(".ClassifiedDetailOwnerDetailsWrap--positionPrimary .ClassifiedDetailOwnerDetails-linkAllAds::attr('href')").extract()
            item["owner_info"] = ""

            owner_info_dict = {}
            owner_info = response.css(".ClassifiedDetailOwnerDetailsWrap--positionPrimary .ClassifiedDetailOwnerDetails-contactEntry")
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
                            owner_info_dict["tel{}".format(num_of_tels+1)] = info_
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
                value = " ".join(response.xpath("//dt[contains(.,'{}')]/following-sibling::*[1]/span/text()".format(name)).extract()).strip()
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
            item["rooms"] = extra.pop("Broj soba", None)
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
