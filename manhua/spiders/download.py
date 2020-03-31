# -*- coding: utf-8 -*-
import scrapy
from scrapy_redis.spiders import RedisSpider
from urllib.parse import urljoin
import re
import json
from manhua.items import manhua_download,image_download
import redis
from scrapy_splash import SplashRequest


class DownloadSpider(RedisSpider):
    name = 'dmzj_download'
    allowed_domains = ['dmzj.com']
    redis_key = 'download:start_url'
    redis_batch_size = 10

    def parse(self, response):
        info = response.xpath('//div[@class="anim-main_list"]/table/tr')
        data = response.body.decode('utf-8', 'ignore')
        item = dict()
        item['Referer'] = response.url
        if len(info) > 2:  # 旧界面
            pat = 'id="comic_id">(.*?)<'
            id = re.compile(pat).findall(data)[0]
            url = 'https://v3api.dmzj.com/comic/comic_' + str(id) + '.json'
            item['is_old'] = 1
            yield scrapy.Request(url, callback=self.next, meta={'item': item}, dont_filter=True)
        else:  # 新界面
            yield SplashRequest(response.url, callback=self.new_html, meta={'item': item}, dont_filter=True)

    def new_html(self,response):
        data = response.body.decode('utf-8','ignore')
        item = response.meta['item']
        try:
            pat = 'other_subscribe\((.*?),'
            id = re.compile(pat).findall(data)[0]
        except IndexError as e:
            print('新网页又找不到id')
            return
        url = 'https://v3api.dmzj.com/comic/comic_' + str(id) + '.json'
        item['is_old'] = 0
        yield scrapy.Request(url, callback=self.next, meta={'item': item}, dont_filter=True)


    def next(self, response):
        jsondata = json.loads(response.body)
        item = image_download()
        item['is_old'] = response.meta['item']['is_old']
        item['Referer'] = response.meta['item']['Referer']
        scrapy_item = manhua_download()
        chapters_info = jsondata['chapters'][0]['data']
        scrapy_item['total_chapters'] = len(chapters_info)
        scrapy_item['id'] = int(jsondata['id'])

        conn = redis.Redis(host='139.199.0.99', port=6379, password='SHIqixin5682318!', db=5)
        redis_total_chapters = conn.hget('idToNum', int(jsondata['id']))
        conn.close()

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
        item['Referer'] = response.url
        image_index = 0
        if item['is_old']:
            for i in images:
                image_urls = []
                url = urljoin("https://", i)
                image_urls.append(url)

                item['image_index'] = image_index
                item['image_urls'] = image_urls
                yield item
                image_index += 1