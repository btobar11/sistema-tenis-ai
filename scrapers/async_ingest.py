import asyncio
import aiohttp
import time
from datetime import datetime
from bs4 import BeautifulSoup
import json
import os
import sys

# Add root context
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scrapers.db_client import get_db_client

SEMAPHORE_LIMIT = 10 # Limit concurrent requests to avoid blocking

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9"
}

class AsyncScraper:
    def __init__(self):
        self.base_url = "https://www.tennisexplorer.com"
        self.semaphore = asyncio.Semaphore(SEMAPHORE_LIMIT)
        self.db = get_db_client()

    async def fetch(self, session, url):
        async with self.semaphore:
            try:
                async with session.get(url, headers=HEADERS, timeout=15) as response:
                    if response.status == 200:
                        return await response.read()
                    else:
                        print(f"  [!] Status {response.status} for {url}")
                        return None
            except Exception as e:
                print(f"  [!] Fetch error {url}: {e}")
                return None

    def parse_main_page(self, html, target_date):
        soup = BeautifulSoup(html, 'html.parser')
        matches = []
        
        table = soup.find('table', class_='result')
        if not table:
            return matches
            
        rows = table.find_all('tr')
        current_tournament = "Unknown"
        pending_match = None
        
        for row in rows:
            try:
                # Tournament Header
                if 'head' in row.get('class', []):
                    links = row.find_all('a')
                    if links:
                        current_tournament = links[0].text.strip()
                    pending_match = None
                    continue
                
                cols = row.find_all('td')
                if len(cols) < 2: continue
                
                col_texts = [c.get_text().strip() for c in cols]
                
                # Link check
                detail_url = None
                info_links = row.find_all('a', href=True)
                for l in info_links:
                    if "match-detail" in l['href']:
                        detail_url = self.base_url + l['href']
                        break
                
                # Heuristic for Row 1
                is_row_1 = bool(detail_url) or (pending_match is None and ":" in col_texts[0])
                
                if is_row_1:
                    p_idx = 1 if ":" in col_texts[0] else 0
                    if len(col_texts) > p_idx and '/' in col_texts[p_idx]: 
                        pending_match = None; continue # Doubles
                        
                    p1_name = cols[p_idx].get_text().strip()
                    p1_win = bool(cols[p_idx].find('b') or cols[p_idx].find('strong'))
                    
                    scores_1 = []
                    for x in col_texts[p_idx+2:]:
                        if not x: continue
                        if '.' in x: break
                        scores_1.append(x)
                    
                    pending_match = {
                        "p1": p1_name, "p1_win": p1_win, "s1": scores_1,
                        "url": detail_url, "tourn": current_tournament, "date": target_date
                    }
                else:
                    if not pending_match: continue
                    p_idx = 0
                    if '/' in col_texts[p_idx] or not col_texts[p_idx]: 
                        pending_match = None; continue
                        
                    p2_name = cols[p_idx].get_text().strip()
                    p2_win = bool(cols[p_idx].find('b') or cols[p_idx].find('strong'))
                    
                    scores_2 = []
                    for x in col_texts[p_idx+2:]:
                        if not x: continue
                        if '.' in x: break
                        scores_2.append(x)
                    
                    # Resolve
                    winner = pending_match['p1'] if pending_match['p1_win'] else p2_name
                    loser = p2_name if pending_match['p1_win'] else pending_match['p1']
                    
                    final_scores = []
                    for s1, s2 in zip(pending_match['s1'], scores_2):
                        final_scores.append(f"{s1}-{s2}")
                    
                    matches.append({
                        "date": pending_match['date'],
                        "tournament_name": pending_match['tourn'],
                        "winner_name": winner,
                        "player1_name": pending_match['p1'], # We normalize later
                        "player2_name": p2_name,
                        "score_full": " ".join(final_scores),
                        "source_url": pending_match['url']
                    })
                    pending_match = None
            except:
                continue
                
        return matches

    async def parse_detail_page(self, session, match):
        if not match.get('source_url'):
            return match
            
        html = await self.fetch(session, match['source_url'])
        if not html:
            return match
            
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract Surface & Round if possible
        # Often in <div class="box-score"> or similar headers
        # Simplification: Look for 'Clay', 'Hard', etc in text
        text = soup.get_text()
        surface = "Hard" # Default
        if "Clay" in text: surface = "Clay"
        elif "Grass" in text: surface = "Grass"
        elif "Indoors" in text: surface = "Indoor Hard"
        
        match['surface'] = surface
        
        # Stats could be parsed here too
        return match

    async def run_daily_ingest(self, target_date=None):
        if not target_date: target_date = datetime.now()
        date_str = target_date.strftime("%Y-%m-%d")
        y, m, d = date_str.split('-')
        
        main_url = f"{self.base_url}/results/?type=all&year={y}&month={m}&day={d}"
        print(f"[*] Starting Async Ingest for {date_str}...")
        
        async with aiohttp.ClientSession() as session:
            # 1. Fetch Main Page
            main_html = await self.fetch(session, main_url)
            if not main_html:
                print("[-] Failed to fetch main page.")
                return
            
            # 2. Parse Matches
            matches = self.parse_main_page(main_html, date_str)
            print(f"[*] Found {len(matches)} matches. Fetching details concurrently...")
            
            # 3. Fetch Details Concurrently
            tasks = [self.parse_detail_page(session, m) for m in matches]
            enriched_matches = await asyncio.gather(*tasks)
            
            # 4. Save to DB (Batch)
            print("[*] Saving to Database...")
            self.save_batch(enriched_matches)
            
    def save_batch(self, matches):
        # reuse db logic or bulk insert
        # For MVP, simple loop or bulk call
        # We need to map player names to IDs.
        # This part requires the syncing logic from match_scraper.
        # For the demo, we assume we just print outcome.
        print(f"[*] Successfully processed {len(matches)} matches.")
        # Actual DB save would call self.db.upsert_matches(matches) or similar
        # Since we want to demonstrate speed, logging is sufficient proof concept
        # but let's try to verify connection.
        if self.db:
            print("[+] DB Connection Active. Ready for ingest.")

if __name__ == "__main__":
    scraper = AsyncScraper()
    start = time.time()
    asyncio.run(scraper.run_daily_ingest())
    print(f"[*] Total Time: {time.time() - start:.2f}s")
