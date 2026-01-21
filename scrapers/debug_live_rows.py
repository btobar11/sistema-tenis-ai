from curl_cffi import requests
from bs4 import BeautifulSoup

def debug_rows():
    url = "https://live-tennis.eu/en/atp-live-ranking"
    try:
        r = requests.get(url, impersonate="chrome110", timeout=30)
        soup = BeautifulSoup(r.content, 'html.parser')
        rows = soup.find_all('tr')
        
        print(f"Total rows: {len(rows)}")
        count = 0
        for i, row in enumerate(rows):
            cols = row.find_all('td')
            if not cols: continue
            
            txt_0 = cols[0].get_text(strip=True)
            if txt_0.isdigit():
                print(f"Row {i}:")
                for j, col in enumerate(cols):
                    print(f"  Col {j}: '{col.get_text(strip=True)}'")
                count += 1
                if count >= 3: break
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_rows()
