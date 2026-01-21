import requests
from bs4 import BeautifulSoup
import json

def debug_espn():
    url = "https://www.espn.com/tennis/rankings"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')
        tables = soup.find_all('table')
        
        for table in tables:
            headers_text = [th.get_text(strip=True).upper() for th in table.find_all('th')]
            if not any("RANK" in h or "RK" in h for h in headers_text):
                continue
                
            rows = table.find_all('tr')[1:] # Skip header
            if rows:
                first_row = rows[0]
                cols = first_row.find_all('td')
                print("First Row Columns:")
                for i, col in enumerate(cols):
                    print(f"Col {i}: {col.prettify()}")
                break
    except Exception as e:
        print(e)

if __name__ == "__main__":
    debug_espn()
