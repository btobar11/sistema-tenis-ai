import os
import json
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

# Wrapper to maintain compatibility with existing scraper code
class QueryBuilderWrapper:
    def __init__(self, query):
        self.query = query

    def select(self, columns='*'):
        self.query = self.query.select(columns)
        return self

    def eq(self, column, value):
        self.query = self.query.eq(column, value)
        return self
    
    def in_(self, column, values):
        self.query = self.query.in_(column, values)
        return self

    def gte(self, column, value):
        self.query = self.query.gte(column, value)
        return self

    def lte(self, column, value):
        self.query = self.query.lte(column, value)
        return self

    def or_(self, filters):
        # Official SDK syntax for OR: .or_('cond1,cond2')
        self.query = self.query.or_(filters)
        return self
        
    def order(self, column, desc=False):
        self.query = self.query.order(column, desc=desc)
        return self

    def limit(self, count):
        self.query = self.query.limit(count)
        return self
    
    def insert(self, data):
        self.query = self.query.insert(data)
        return self

    def upsert(self, data, on_conflict=None):
        opts = {}
        if on_conflict:
            opts['on_conflict'] = on_conflict
        self.query = self.query.upsert(data, **opts)
        return self

    def update(self, data):
        self.query = self.query.update(data)
        return self

    def execute(self):
        try:
            # Official SDK execute() returns APIResponse(data=..., count=...)
            response = self.query.execute()
            
            # Mimic the old Response object structure (data, error)
            class Response:
                def __init__(self, data, error=None):
                    self.data = data
                    self.error = error
            
            return Response(response.data, None)
        except Exception as e:
            # Handle SDK errors (which raise exceptions) and return as error object
            class Response:
                def __init__(self, data, error):
                    self.data = data
                    self.error = str(error)
            return Response(None, str(e))

class SupabaseFluentClient:
    def __init__(self, url, key):
        self.url = url
        self.key = key
        self.client: Client = create_client(url, key)

    def _request_with_retry(self, method, url, **kwargs):
        import requests
        import time
        headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}"
        }
        for attempt in range(3):
            try:
                if method.lower() == 'get':
                    return requests.get(url, headers=headers, **kwargs)
            except:
                time.sleep(1)
        return None

    def from_(self, table):
        # 'table' method initiates the query builder in official SDK
        return QueryBuilderWrapper(self.client.table(table))
        
    def table(self, table):
        # Alias for from_
        return self.from_(table)

    def get_or_create_player(self, name):
        """
        Resolves a player name to an ID, creating the player if they don't exist.
        """
        try:
            # Check if exists
            r = self.table('players').select('id').eq('name', name).execute()
            if r.data:
                return r.data[0]['id']
            
            # Create if not exists
            r = self.table('players').insert({"name": name}).execute()
            if r.data:
                return r.data[0]['id']
        except Exception as e:
            print(f"Sync Player Error ({name}): {e}")
        return None

    def insert_match(self, match_data):
        """
        Inserts a match into the database. 
        Checks for duplicates based on date, winner, and loser.
        Updates if exists, Inserts if new.
        """
        try:
            # Robust Date Check: Ignore time, check full day range
            try:
                # Handle ISO string "YYYY-MM-DDTHH:MM:SS..."
                date_str = match_data['date'].split('T')[0]
                day_start = f"{date_str}T00:00:00"
                day_end = f"{date_str}T23:59:59"
            except:
                # Fallback if format is weird
                day_start = match_data['date']
                day_end = match_data['date']

            p1 = match_data['player1_id']
            p2 = match_data['player2_id']

            # Check for existing match
            existing = self.table('matches')\
                .select('id, player1_id, player2_id')\
                .gte('date', day_start)\
                .lte('date', day_end)\
                .or_(f"player1_id.eq.{p1},player2_id.eq.{p1}")\
                .execute()
            
            match_id = None
            if existing.data:
                for m in existing.data:
                    if (m['player1_id'] == p1 and m['player2_id'] == p2) or \
                       (m['player1_id'] == p2 and m['player2_id'] == p1):
                        match_id = m['id']
                        break
            
            if match_id:
                # Update
                # Filter to known columns to avoid errors
                valid_cols = ['tournament_name', 'surface', 'round', 'winner_id', 'score_full', 'stats_json', 'status', 'prediction']
                update_data = {k: v for k, v in match_data.items() if k in valid_cols}
                
                res = self.table('matches').update(update_data).eq('id', match_id).execute()
                if hasattr(res, 'error') and res.error:
                    print(f"Update Failed: {res.error}")
                    return None
                return match_id
            else:
                # Insert
                # Filter to known columns
                valid_cols = ['tournament_name', 'surface', 'round', 'winner_id', 'score_full', 'stats_json', 'status', 'prediction']
                insert_data = {k: v for k, v in match_data.items() if k in valid_cols or k in ['date', 'player1_id', 'player2_id']}

                res = self.table('matches').insert(insert_data).execute()
                if res.data and len(res.data) > 0:
                    return res.data[0]['id']
                
                print(f"Insert Failed: {getattr(res, 'error', 'No Error Attr')}")
                return None
                
        except Exception as e:
            print(f"Insert Match Error: {e}")
            return False

class DatabaseClient:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseClient, cls).__new__(cls)
            cls._instance.client = cls._connect()
        return cls._instance

    @staticmethod
    def _connect():
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        
        if not url or not key:
            print("[DB] Error: SUPABASE_URL or SUPABASE_KEY missing.")
            return None
            
        # print("[DB] Using Official Supabase Client (Clean Adapter)")
        return SupabaseFluentClient(url, key)

def get_db_client():
    """
    Returns the Supabase Client (Mimicked).
    """
    db = DatabaseClient()
    return db.client

# Helper for resolving players using the new client
def get_or_create_player(client, name_raw):
    """
    Resolves a player name to an ID, creating the player if they don't exist.
    Extracts ranking if present in name like 'Sinner J. (1)'.
    """
    import re
    
    # 1. Extract Rank
    rank = None
    name = name_raw.strip()
    
    # Match (123) at end
    match = re.search(r'\s*\((\d+)\)$', name)
    if match:
        rank = int(match.group(1))
        name = name[:match.start()].strip()
        
    try:
        # 2. Check if exists
        r = client.table('players').select('id, rank_single').eq('name', name).execute()
        if r.data:
            pid = r.data[0]['id']
            # Update rank if we have a new one
            if rank:
                try:
                    client.table('players').update({'rank_single': rank}).eq('id', pid).execute()
                    # print(f"  Updated Rank for {name}: {rank}")
                except: pass
            return pid
        
        # 3. Create if not exists
        new_p = {"name": name, "hand": "R", "rank_single": rank}
        r = client.table('players').insert(new_p).execute()
        if r.data:
            return r.data[0]['id']
            
    except Exception as e:
        print(f"Sync Player Error ({name}): {e}")
        
        # Fallback: Try simple search again in case of race condition or error
        try:
             r = client.table('players').select('id').eq('name', name).execute()
             if r.data: return r.data[0]['id']
        except: pass
        
    return None
