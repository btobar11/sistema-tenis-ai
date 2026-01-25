from curl_cffi import requests
from bs4 import BeautifulSoup
import time
import random

def check_robust(url):
    print(f"Checking {url} with impersonation...")
    try:
        # Impersonate Chrome 110 to look like a real browser
        r = requests.get(
            url, 
            impersonate="chrome110",
            timeout=15
        )
        print(f"Status: {r.status_code}")
        
        if r.status_code == 200:
            soup = BeautifulSoup(r.content, 'html.parser')
            title = soup.title.string if soup.title else "No Title"
            print(f"Title: {title}")
            print("SUCCESS! We bypassed the protection.")
            return True
        else:
            print("Failed to bypass.")
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    check_robust("https://live-tennis.eu/en/atp-live-ranking")
    time.sleep(random.uniform(2, 5))
    check_robust("https://live-tennis.eu/en/wta-live-ranking")
