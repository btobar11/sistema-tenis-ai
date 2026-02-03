import scrapy

class MatchItem(scrapy.Item):
    tournament = scrapy.Field()
    date = scrapy.Field()
    player_a = scrapy.Field()
    player_b = scrapy.Field()
    score = scrapy.Field()
    round = scrapy.Field()
    url = scrapy.Field()
