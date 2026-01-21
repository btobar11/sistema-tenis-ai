def main():
    with open('scrapers/data.json', 'r', encoding='utf-8') as f:
        import json
        data = json.load(f)
    
    # Chunk size 200
    chunk_size = 200
    for i in range(0, len(data), chunk_size):
        chunk = data[i:i+chunk_size]
        values = []
        for p in chunk:
            name = p['name'].replace("'", "''")
            rank = p['rank_single']
            plays_hand = p.get('plays_hand', 'U')
            country = p.get('country', 'UNK')
            points = p.get('points', 0)
            values.append(f"('{name}', {rank}, '{plays_hand}', '{country}', {points})")
        
        sql = f"INSERT INTO players (name, rank_single, plays_hand, country, points) VALUES {', '.join(values)} ON CONFLICT (name) DO UPDATE SET rank_single = EXCLUDED.rank_single, plays_hand = EXCLUDED.plays_hand, country = EXCLUDED.country, points = EXCLUDED.points;"
        
        filename = f"scrapers/part_{i//chunk_size + 1}.sql"
        with open(filename, 'w', encoding='utf-8') as f_out:
            f_out.write(sql)
        print(f"Created {filename} with {len(chunk)} rows.")

if __name__ == "__main__":
    main()
