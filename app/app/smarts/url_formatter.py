from urllib.parse import urlparse, parse_qs, urlunparse, urlencode

import grequests
import requests
import re


def parse_url(url):
    if urlparse(url).scheme == '':
        if url.startswith('//') or url.startswith('\\'):
            url = 'http:' + url
        else:
            url = 'http://' + url
    parsed = urlparse(url)
    qd = parse_qs(parsed.query, keep_blank_values=True)
    filtered = dict((k, v) for k, v in qd.items() if not k.startswith('utm_'))
    newurl = urlunparse([
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        parsed.params,
        urlencode(filtered, doseq=True),  # query string
        parsed.fragment
    ])
    return newurl

def is_url_image(urls):
    image_formats = ("image/png", "image/jpeg", "image/jpg")
    try:
       url_to_item = {item: item for item in urls}
       rq = (grequests.head(url) for url in url_to_item.keys())
       urls = [url_to_item[i.request.url] for i in
               filter(lambda x: x is not None and x.status_code == 200 and x.headers["content-type"] in image_formats, grequests.imap(rq))]
    except Exception as e:
       print(e)
    if len(urls) > 0:
        return urls
    else:
        return None

def parse_urls(urls):
    if len(urls) == 0:
        return None
    else:
        return ",".join(urls)


class UrlFormatter(object):
    def __init__(self, url):
        if not url:
            self.url = None
        if isinstance(url, list):
            self.url = url[0]
        if type(url) == str:
            self.url = url

    def format(self):
        url = self.url
        if not url:
            return None
        return parse_url(self.url)
