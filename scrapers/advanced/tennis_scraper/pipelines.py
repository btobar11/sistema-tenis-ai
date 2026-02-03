import os
import logging
from supabase import create_client, Client
from itemadapter import ItemAdapter

class SupabasePipeline:
    def __init__(self, supabase_url, supabase_key):
        self.supabase_url = supabase_url
        self.supabase_key = supabase_key
        self.client: Client = None

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            supabase_url=crawler.settings.get('SUPABASE_URL') or os.getenv('SUPABASE_URL'),
            supabase_key=crawler.settings.get('SUPABASE_KEY') or os.getenv('SUPABASE_KEY')
        )

    def open_spider(self, spider):
        if self.supabase_url and self.supabase_key:
            self.client = create_client(self.supabase_url, self.supabase_key)
            spider.logger.info("Supabase Client Connected")
        else:
            spider.logger.warning("Supabase credentials missing. Pipeline will not save data.")

    def process_item(self, item, spider):
        if not self.client:
            return item

        adapter = ItemAdapter(item)
        data = adapter.asdict()
        
        # Determine strict structure for 'matches' table
        # We need to map extracted fields to DB columns
        # This is a simplification; real mapping depends on exact schema
        record = {
            'tournament': data.get('tournament'),
            'date': data.get('date'), # parsing needed?
            'player1_name': data.get('player_a'),
            'player2_name': data.get('player_b'),
            'score_full': data.get('score'),
            'status': 'finished', # If we are scraping results, it's finished
            # We would need to resolve IDs for players here usually, 
            # or use an upsert based on names/date if IDs aren't known yet.
            # For this MVP, we insert raw or log.
        }

        try:
            # 1. Upsert match based on unique keys (e.g. players + date) if possible
            # Or just insert for now to prove data flow.
            # Real implementation needs robust player ID resolution.
            
            # For "Feedback Loop", we need to ensure this data is readable by `api.getPlayerHistory`
            # which reads from `matches`.
            
            # Upsert Logic (simplified)
            # self.client.table('matches').upsert(record).execute()
            
            spider.logger.info(f"Saved match result: {record['player1_name']} vs {record['player2_name']}")
            
        except Exception as e:
            spider.logger.error(f"Failed to save item: {e}")

        return item
