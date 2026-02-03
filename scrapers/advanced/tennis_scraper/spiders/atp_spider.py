import scrapy
from ..items import MatchItem

class ATPSpider(scrapy.Spider):
    name = "atp_tour"
    allowed_domains = ["atptour.com"]
    start_urls = ["https://www.atptour.com/en/scores/current"]

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url,
                meta={
                    'playwright': True,
                    'wait_for': '.scores-table-row' # Wait for the score table to render
                }
            )

    def parse(self, response):
        self.logger.info(f"Parsing ATP Tour Page: {response.url}")
        
        # Example Selector Logic (This depends on actual ATP site structure which changes)
        # Assuming table rows for matches
        matches = response.css('.scores-table-row')
        
        for match in matches:
            item = MatchItem()
            item['tournament'] = match.css('.tournament-name::text').get()
            item['player_a'] = match.css('.player-left .name::text').get()
            item['player_b'] = match.css('.player-right .name::text').get()
            item['score'] = match.css('.scores::text').get()
            
            # Basic validation
            if item['player_a'] and item['player_b']:
                yield item
        
        # Follow pagination or other links if needed
        # yield response.follow(next_page, meta={'playwright': True})
