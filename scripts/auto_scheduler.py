"""
Auto Scheduler for Tennis Scrapers
Runs match_scraper.py every 15 minutes to keep data fresh.
"""
import subprocess
import time
import sys
from datetime import datetime

INTERVAL_MINUTES = 15

def run_scraper():
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Running match_scraper...")
    try:
        result = subprocess.run(
            [sys.executable, "scrapers/match_scraper.py"],
            capture_output=True,
            text=True,
            timeout=120  # 2 min timeout
        )
        if result.returncode == 0:
            print(f"  ✓ Scraper completed successfully")
            # Print last few lines of output
            lines = result.stdout.strip().split('\n')[-3:]
            for line in lines:
                print(f"    {line}")
        else:
            print(f"  ✗ Scraper failed: {result.stderr[-200:]}")
    except subprocess.TimeoutExpired:
        print("  ✗ Scraper timed out (>2 min)")
    except Exception as e:
        print(f"  ✗ Error: {e}")

def main():
    print("=" * 50)
    print("  TENNIS DATA AUTO-SCHEDULER")
    print(f"  Interval: Every {INTERVAL_MINUTES} minutes")
    print("  Press Ctrl+C to stop")
    print("=" * 50)
    
    while True:
        run_scraper()
        print(f"\n  Next run in {INTERVAL_MINUTES} minutes...")
        time.sleep(INTERVAL_MINUTES * 60)

if __name__ == "__main__":
    main()
