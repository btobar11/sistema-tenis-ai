import json
import codecs

try:
    with codecs.open('scrapers/data.json', 'r', 'utf-16') as f:
        data = json.load(f)
except:
    with open('scrapers/data.json', 'r') as f:
        data = json.load(f)

values = []
for p in data:
    name = p['name'].replace("'", "''")
    rank = p['rank_single']
    # Schema: name, rank_single, plays_hand, country
    
    plays_hand = p.get('plays_hand', 'U')
    country = p.get('country', 'UNK')
    points = p.get('points', 0)
    
    values.append(f"('{name}', {rank}, '{plays_hand}', '{country}', {points})")

sql = f"INSERT INTO players (name, rank_single, plays_hand, country, points) VALUES {', '.join(values)} ON CONFLICT (name) DO UPDATE SET rank_single = EXCLUDED.rank_single, plays_hand = EXCLUDED.plays_hand, country = EXCLUDED.country, points = EXCLUDED.points;"
with open('scrapers/insert_utf8.sql', 'w', encoding='utf-8') as f:
    f.write(sql)
print("SQL written to scrapers/insert_utf8.sql")
