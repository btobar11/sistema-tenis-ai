from curl_cffi import requests
from bs4 import BeautifulSoup

def c(url):
    try:
        print(f"Checking {url}...")
        # impersonate="chrome" mimics a real browser's TLS signature
        r = requests.get(url, impersonate="chrome110", timeout=10)
        print(f"Status: {r.status_code}")
        if r.status_code == 200:
            soup = BeautifulSoup(r.content, 'html.parser')
            print(f"Title: {soup.title.string}")
            print("First 200 chars:")
            print(r.text[:200])
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    c("https://live-tennis.eu/en/atp-live-ranking")
    c("https://live-tennis.eu/en/wta-live-ranking")
