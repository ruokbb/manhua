# -*- coding: utf-8 -*-
from scrapy_redis.spiders import RedisSpider
from manhua.items import HomePageItem
import re
import time
import random

class SearchAllSpider(RedisSpider):
    name = 'dmzj_search_all'
    allowed_domains = ['dmzj.com']
    redis_key = 'dmzj_search_all:start_url'
    redis_batch_size = 1
    custom_settings = {
        'CLOSESPIDER_TIMEOUT' : 3600
    }

    def parse(self, response):

        data = response.body.decode('utf-8')
        # 获取漫画首字母及总数
        pat1 = '<strong>首字母\((.*?)\)<'
        name = str(re.compile(pat1).findall(data)[0]).lower()
        pat2 = '>.(.*?).</font>部漫画'
        total_number = int(re.compile(pat2).findall(data)[0])
        pat3 = '<A class="pselected" href="/tags/[a-z]/(.*?)\.shtml"'
        page = int(re.compile(pat3).findall(data)[-1])

        # 构造当前页漫画的url
        url_list = self.url_manhua_made(data)

        myitem = HomePageItem()
        myitem['manhua_url'] = url_list
        myitem['name'] = name
        myitem['total_number'] = total_number
        myitem['page'] = page

        time.sleep(random.randint(1,3))

        yield myitem

    # 构造漫画url,yield item
    def url_manhua_made(self,data):

        url_list=[]
        pat = '<li><a href="(.*?)" target=\'_blank\' title='
        url_name_list = re.compile(pat).findall(data)
        header = 'https://manhua.dmzj.com'
        for i in url_name_list:
            url = header+i
            url_list.append(url)

        return url_list