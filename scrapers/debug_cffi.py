from curl_cffi import requests
from bs4 import BeautifulSoup

def debug_live_structure():
    url = "https://live-tennis.eu/en/atp-live-ranking"
    try:
        r = requests.get(url, impersonate="chrome110", timeout=10)
        soup = BeautifulSoup(r.content, 'html.parser')
        
        # Find the main table. Usually it has class 'table_live' or similar
        # Based on typical layout, let's look for tables and print classes
        tables = soup.find_all('table')
        print(f"Tables found: {len(tables)}")
        
        for i, table in enumerate(tables):
            # Check if it looks like the ranking table (has many rows)
            rows = table.find_all('tr')
            if len(rows) > 10:
                print(f"Table {i} has {len(rows)} rows. Potential match.")
                # Print headers
                headers = [th.get_text(strip=True) for th in table.find_all('th')]
                print(f"Headers: {headers}")
                
                # Print first data row
                if len(rows) > 1:
                    cols = rows[1].find_all('td')
                    print("First Row Cols:")
                    for j, col in enumerate(cols):
                        print(f"  Col {j}: {col.get_text(strip=True)}")
                break
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_live_structure()
