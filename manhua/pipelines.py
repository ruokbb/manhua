# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import redis
from scrapy.pipelines.images import ImagesPipeline
import scrapy
from manhua.items import manhua_download
import json
import pymysql

class ManhuaPipeline(object):

    def open_spider(self,spider):
        self.conn = redis.Redis(host='139.199.0.99',port=6379,password='SHIqixin5682318!',db=5)

    def process_item(self, item, spider):
        if spider.name != 'dmzj_search_all':
            return item

        url_list = item['manhua_url']

        name_key = 'manhua_url'
        for i in url_list:
            self.conn.sadd(name_key,i)

        #重新导入
        self.url_header_set()

        #检查网页
        self.url_set(item['name'],item['total_number'],item['page'])


    def close_spider(self,spider):
        self.conn.close()

    # 检查dmzj_search_all:start_url是否为空，为空则填充字母url
    # https://manhua.dmzj.com/tags/a/1.shtml
    def url_header_set(self):

        if self.conn.llen('dmzj_search_all:start_url')!=0:
            return

        list = set('qwertyuiopasdfghjklmnbvcxz')

        for i in list:
            url = 'https://manhua.dmzj.com/tags/' + str(i) + '/1.shtml'
            self.conn.lpush('dmzj_search_all:start_url', url)


    # 检查本分类总数，初始0，如果有变化，更新本分类总数，
    # 清空dmzj_search_all:start_url，添加所有页码url
    # https://manhua.dmzj.com/tags/a/1.shtml
    # 没有变化就退出
    def url_set(self,name,total_number,page):

        redis_number = self.conn.hget('name_to_pages', name)

        if redis_number:
            redis_number = int(redis_number)
            # 以前爬过，保存了页数
            if redis_number == total_number:
                # 没有变化，直接返回
                return

        # 重新赋值
        self.conn.hset('name_to_pages', name, total_number)
        # 清空dmzj_search_all:start_url
        self.conn.ltrim('dmzj_search_all:start_url', 1, 0)
        # 添加队列
        for i in range(1, page + 1):
            url = 'https://manhua.dmzj.com/tags/' + name + '/' + str(i) + '.shtml'
            self.conn.lpush('dmzj_search_all:start_url', url)


class InfoPipeline(object):
    def open_spider(self,spider):
        self.conn = redis.Redis(host='139.199.0.99',port=6379,password='SHIqixin5682318!',db=5)
        self.mysql_conn = pymysql.connect(host='139.199.0.99',user='root',password='root',port=3306,database='rrmh',
                             charset='utf8')

    def close_spider(self,spider):
        self.conn.close()
        self.mysql_conn.close()

    def process_item(self, item, spider):
        if spider.name != 'dmzj_search_info':
            return item

        #判断之前是否已收录
        a = self.conn.sismember('idIncluded',item['id'])
        if a:
            item['included'] = 1
        else:
            item['included'] = 0
            self.conn.sadd('idIncluded',item['id'])

        #封装json传入数据库
        temp = json.dumps(item)
        cursor = self.mysql_conn.cursor()
        # sql = 'INSERT INTO json_cart_info VALUES (' + pymysql.escape_string(temp) + ')'
        cursor.execute('INSERT INTO json_cart_info (json) VALUES (%s)',(str(temp)))
        self.mysql_conn.commit()
        cursor.close()


     #调整逻辑对应存入接口
        #根据情况重置manhua_url，和dmzj_search_all：items,重新爬取更新信息
        #可能存在异步的错误，慎重
        if self.conn.llen('dmzj_search_info:start_url')==0:

            a = self.conn.smembers('manhua_url')
            for i in a:
                self.conn.lpush('dmzj_search_info:start_url',i)

            self.conn.ltrim('manhua_info', 1, 0)
            b = self.conn.lrange('dmzj_search_all：items', 0, -1)
            for i in b:
                self.conn.lpush('manhua_info', i)

            self.conn.ltrim('dmzj_search_all：items',1,0)



class DownloadPipeline(object):
    def open_spider(self,spider):
        self.conn = redis.Redis(host='139.199.0.99',port=6379,password='SHIqixin5682318!',db=5)

    def close_spider(self,spider):
        self.conn.close()

    def process_item(self, item, spider):
        if not isinstance(item,manhua_download):
            return item

        #爬取一遍之后重新填充start_url
        if self.conn.llen('download:start_url')==0:

            a = self.conn.smembers('manhua_url')
            for i in a:
                self.conn.lpush('download:start_url',i)

            self.conn.ltrim('download：items',1,0)

        self.conn.hset('idToNum',item['id'],int(item['total_chapters']))

        return item


class DownloadImagePipeline(ImagesPipeline):
    def get_media_requests(self, item, info):
        for i in item['image_urls']:
            header = {"Referer": item['Referer']}
            yield scrapy.Request(i, headers=header)