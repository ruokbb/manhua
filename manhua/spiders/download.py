# -*- coding: utf-8 -*-
import scrapy
from scrapy_redis.spiders import RedisSpider
from urllib.parse import urljoin
import re
import json
from manhua.items import manhua_download
import redis
from scrapy_splash import SplashRequest


class DownloadSpider(RedisSpider):
    name = 'download'
    allowed_domains = ['dmzj.com']
    redis_key = 'download:start_url'

    def parse(self, response):
        info = response.xpath('//div[@class="anim-main_list"]/table/tr')
        data = response.body.decode('utf-8', 'ignore')
        item = {}
        if len(info) > 2:  # 旧界面
            pat = 'id="comic_id">(.*?)<'
            id = re.compile(pat).findall(data)[0]
            url = 'https://v3api.dmzj.com/comic/comic_' + str(id) + '.json'
            item['is_old'] = 1
        else:  # 新界面
            pat = 'obj_id.=."(.*?)"'
            id = re.compile(pat).findall(data)[0]
            url = 'https://v3api.dmzj.com/comic/comic_' + str(id) + '.json'
            item['is_old'] = 0

        yield scrapy.Request(url, callback=self.next, meta={'item': item}, dont_filter=True)

    def next(self, response):
        jsondata = json.loads(response.body)
        item = {}
        item['is_old'] = response.meta['item']['is_old']
        scrapy_item = manhua_download()
        chapters_info = jsondata['chapters'][0]['data']
        scrapy_item['total_chapters'] = len(chapters_info)
        scrapy_item['id'] = int(jsondata['id'])
        conn = redis.Redis(host='139.199.0.99', port=6379, password='SHIqixin5682318!', db=5)
        redis_total_chapters = conn.hget('idToNum', int(jsondata['id']))
        if redis_total_chapters:
            if redis_total_chapters >= len(chapters_info):  # 无新章节
                return

        yield scrapy_item
        item['id'] = jsondata['id']
        item['name'] = jsondata['title']
        chapters_id = [i['chapter_id'] for i in chapters_info]
        chapters_name = [i['chapter_title'] for i in chapters_info]
        chapter_index = 0
        for i in range(len(chapters_id)):
            index = len(chapters_id) - i - 1

            url = urljoin(item['Referer'], str(chapters_id[index]) + ".shtml")
            # url = item['Referer'] + str(chapters_id[index]) + ".shtml"
            item['chapter_name'] = chapters_name[index]
            item['chapter_index'] = chapter_index
            chapter_index += 1
            yield SplashRequest(url, callback=self.find_imageurls, meta={'item': item}, dont_filter=True)

    def find_imageurls(self, response):
        images = response.xpath('//div[@class="btmBtnBox"]/select/option/@value').extract()
        item = response.meta['item']
        header = {"Referer": response.url}
        image_index = 0
        if item['is_old']:
            for i in images:
                url = urljoin("https://", i)
                item['image_index'] = image_index
                image_index += 1
                yield scrapy.Request(url, headers=header, callback=self.download, meta={"item": item}, dont_filter=True)

    def download(self, response):
        item = response.meta['item']
        item['image'] = response.body
