# -*- coding: utf-8 -*-
import scrapy
from scrapy_redis.spiders import RedisSpider
from manhua.items import manhua_info
import re
import json

class SearchInfoSpider(RedisSpider):
    name = 'dmzj_search_info'
    allowed_domains = ['dmzj.com']
    redis_key = 'dmzj_search_info:start_url'

    def parse(self, response):
        data = response.body.decode('utf-8','ignore')
        item = manhua_info()
        item['url'] = response.url
        info = response.xpath('//div[@class="anim-main_list"]/table/tr')
        if len(info) > 2:  #第一种界面
            item['is_old'] = 1
            item['author'] = info[2].xpath('./td/a/text()').extract_first()
            item['territory'] = info[3].xpath('./td/a/text()').extract_first()
            item['state'] = info[4].xpath('./td/a/text()').extract_first()
            item['theme'] = info[6].xpath('./td/a/text()').extract()
            item['classify'] = info[7].xpath('./td/a/text()').extract_first()

            pat = 'id="comic_id">(.*?)<'
            id = re.compile(pat).findall(data)[0]
            url = 'https://v3api.dmzj.com/comic/comic_' + str(id) + '.json'
            yield scrapy.Request(url=url, callback=self.more_info_parse, meta={'item': item})
        else:#第二种新界面
            item['is_old'] = 0
            item['classify'] = re.compile('类别：(.*?)<').findall(data)[0]

            pat = 'obj_id.=."(.*?)"'
            id = re.compile(pat).findall(data)[0]
            url = 'https://v3api.dmzj.com/comic/comic_' + str(id) + '.json'
            yield scrapy.Request(url=url, callback=self.more_info_parse, meta={'item': item})

    def more_info_parse(self,response):
        item = response.meta['item']
        jsondata = json.loads(response.body)

        item['id'] = jsondata['id']
        item['name'] = jsondata['title']
        item['hot_num'] = jsondata['hot_num']
        item['hit_num'] = jsondata['hit_num']
        item['description'] = jsondata['description']
        item['subscriber_num'] = jsondata['subscribe_num']
        item['newest'] = jsondata['last_updatetime']
        item['image'] = jsondata['cover']

        if item['is_old'] == 0:
            item['author'] = jsondata['authors']['0']['tag_name']
            item['territory'] = '中国'
            item['state'] = jsondata['status']['0']['tag_name']

            a = jsondata['type']
            temp = []
            for i in a:
                temp.append(i['tag_name'])
            item['theme'] = temp


        yield item

