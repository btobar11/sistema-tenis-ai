import requests

def debug_live_tennis():
    url = "https://live-tennis.eu/en/atp-live-ranking"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Referer": "https://www.google.com/",
        "Upgrade-Insecure-Requests": "1"
    }
    
    try:
        s = requests.Session()
        r = s.get(url, headers=headers, timeout=10)
        print(f"Status: {r.status_code}")
        if r.status_code == 200:
            print("Successfully accessed!")
            print(r.text[:500])
        else:
            print("Failed to access.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_live_tennis()
