import os
import requests as http_requests
import json
from dotenv import load_dotenv

load_dotenv()

class QueryBuilder:
    def __init__(self, url, headers, table):
        self.url = url
        self.headers = headers
        self.table = table
        self.params = {}
        self.method = 'GET'
        self.json_body = None

    def select(self, columns='*'):
        self.method = 'GET'
        self.params['select'] = columns
        return self

    def eq(self, column, value):
        self.params[column] = f'eq.{value}'
        return self
    
    def in_(self, column, values):
        # values list -> (val1,val2)
        val_str = ','.join([str(v) for v in values])
        self.params[column] = f'in.({val_str})'
        return self

    def gte(self, column, value):
        self.params[column] = f'gte.{value}'
        return self

    def lte(self, column, value):
        self.params[column] = f'lte.{value}'
        return self
        
    def order(self, column, desc=False):
        direction = 'desc' if desc else 'asc'
        self.params['order'] = f'{column}.{direction}'
        return self

    def limit(self, count):
        self.params['limit'] = str(count)
        # Limit implies list response usually, but Supabase REST gives list.
        # Header Prefer: return=representation needed sometimes.
        return self
    
    def insert(self, data):
        self.method = 'POST'
        self.json_body = data
        self.headers['Prefer'] = 'return=representation' # To get data back
        return self

    def upsert(self, data, on_conflict=None):
        self.method = 'POST'
        self.json_body = data
        # Merge duplicates is the standard PostgREST upsert
        pref = 'return=representation,resolution=merge-duplicates'
        if on_conflict:
            # PostgREST 9+ supports on_conflict via strictly query param usually, 
            # but resolution=merge-duplicates uses PK constraint.
            pass 
        self.headers['Prefer'] = pref
        return self

    def update(self, data):
        self.method = 'PATCH'
        self.json_body = data
        self.headers['Prefer'] = 'return=representation'
        return self


    def execute(self):
        endpoint = f"{self.url}/rest/v1/{self.table}"
        try:
            r = None
            if self.method == 'GET':
                r = http_requests.get(endpoint, headers=self.headers, params=self.params)
            elif self.method == 'POST':
                r = http_requests.post(endpoint, headers=self.headers, json=self.json_body, params=self.params)
            elif self.method == 'PATCH':
                r = http_requests.patch(endpoint, headers=self.headers, json=self.json_body, params=self.params)
            
            # Mimic Supabase Response object
            class Response:
                def __init__(self, data, error=None):
                    self.data = data
                    self.error = error
            
            if r.status_code >= 200 and r.status_code < 300:
                return Response(r.json(), None)
            else:
                return Response(None, r.text)
                
        except Exception as e:
            return Response(None, str(e))

class SupabaseFluentClient:
    def __init__(self, url, key):
        self.url = url
        self.key = key
        self.headers = {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json"
        }

    def from_(self, table):
        return QueryBuilder(self.url, self.headers, table)
        
    def table(self, table):
        # Alias for from_
        return self.from_(table)

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
            
        print("[DB] Using Custom Fluent REST Client")
        return SupabaseFluentClient(url, key)

def get_db_client():
    """
    Returns the Supabase Client (Mimicked).
    """
    db = DatabaseClient()
    return db.client

# Helper for resolving players using the new client
def get_or_create_player(client, name):
    # This logic belongs in services, but kept here for scrapers reuse
    # Using the fluent syntax
    try:
        r = client.table('players').select('id').eq('name', name).execute()
        if r.data:
            return r.data[0]['id']
        
        r = client.table('players').insert({"name": name}).execute()
        if r.data:
            return r.data[0]['id']
    except Exception as e:
        print(f"Sync Player Error: {e}")
    return None
