import requests
from bs4 import BeautifulSoup

def c(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        print(f"Checking {url}...")
        r = requests.get(url, headers=headers, timeout=10)
        print(f"Status: {r.status_code}")
        if r.status_code == 200:
            soup = BeautifulSoup(r.content, 'html.parser')
            title = soup.title.string if soup.title else "No Title"
            print(f"Title: {title}")
            # Check for table length
            rows = soup.find_all('tr')
            print(f"Total Rows: {len(rows)}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    c("https://live-tennis.eu/en/atp-live-ranking")
    c("https://live-tennis.eu/en/wta-live-ranking")
