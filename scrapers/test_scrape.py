import requests
from bs4 import BeautifulSoup
import json

def scrape_espn_rankings():
    url = "https://www.espn.com/tennis/rankings"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        tables = soup.find_all('table')
        players = []
        
        for table in tables:
            headers_text = [th.get_text(strip=True).upper() for th in table.find_all('th')]
            if not any("RANK" in h or "RK" in h for h in headers_text):
                continue
                
            rows = table.find_all('tr')[1:]
            for row in rows:
                cols = row.find_all('td')
                if len(cols) < 3:
                    continue
                    
                rank_text = cols[0].get_text(strip=True)
                name_col = cols[2]
                player_link = name_col.find('a')
                player_name = player_link.get_text(strip=True) if player_link else name_col.get_text(strip=True)
                points_text = cols[3].get_text(strip=True).replace(',', '')
                
                try:
                    rank = int(rank_text)
                except:
                    continue
                    
                players.append({
                    "name": player_name,
                    "rank_single": rank,
                    "points": int(points_text) if points_text.isdigit() else 0,
                    "hand": "U",
                    "nationality": "UNK"
                })
            if players:
                 break
        return players
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    data = scrape_espn_rankings()
    print(json.dumps(data))
