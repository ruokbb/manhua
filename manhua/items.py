# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class ManhuaItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass

class HomePageItem(scrapy.Item):
    manhua_url = scrapy.Field()
    name = scrapy.Field()
    total_number = scrapy.Field()
    page = scrapy.Field()

class manhua_info(scrapy.Item):
    id = scrapy.Field()
    is_old = scrapy.Field()
    name = scrapy.Field()
    url = scrapy.Field()
    image = scrapy.Field()
    author = scrapy.Field()
    territory = scrapy.Field()
    state = scrapy.Field()
    hot_num = scrapy.Field()
    hit_num = scrapy.Field()
    subscriber_num = scrapy.Field()
    theme = scrapy.Field()
    classify = scrapy.Field()
    newest = scrapy.Field()
    description = scrapy.Field()
    total_section = scrapy.Field()

class manhua_download(scrapy.Item):
    total_chapters = scrapy.Field()
    id = scrapy.Field()