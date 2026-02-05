#!/usr/bin/env python3
"""
Tennis AI - Automated Data Scheduler
Keeps match data fresh by running scrapers at optimal intervals.

Schedule:
- Upcoming Matches: Every 30 minutes
- Live Monitor: Every 2 minutes (when matches are live)
- Value Bets: Every hour

Usage:
    python auto_scheduler.py          # Run in foreground (for testing)
    pythonw auto_scheduler.py         # Run in background (no console)
"""

import sys
import os
import time
import logging
from datetime import datetime

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Configure logging
log_file = os.path.join(current_dir, 'scheduler.log')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Import scheduler
try:
    from apscheduler.schedulers.blocking import BlockingScheduler
    from apscheduler.triggers.interval import IntervalTrigger
except ImportError:
    logger.error("APScheduler not installed. Run: pip install apscheduler")
    sys.exit(1)

def job_upcoming():
    """Scrape upcoming matches (today + tomorrow)"""
    logger.info("🎾 [UPCOMING] Starting upcoming matches scraper...")
    try:
        from upcoming_scraper import run_upcoming_scraper
        run_upcoming_scraper()
        logger.info("✅ [UPCOMING] Completed successfully")
    except Exception as e:
        logger.error(f"❌ [UPCOMING] Failed: {e}")

def job_live():
    """Monitor live matches and update scores"""
    logger.info("📡 [LIVE] Starting live monitor cycle...")
    try:
        from live_monitor import get_db_client, get_tracked_players, monitor_cycle
        db = get_db_client()
        tracked = get_tracked_players(db)
        if tracked:
            logger.info(f"   Tracking {len(tracked)} players")
            monitor_cycle(db, tracked)
        else:
            logger.info("   No active players to track")
        logger.info("✅ [LIVE] Completed successfully")
    except Exception as e:
        logger.error(f"❌ [LIVE] Failed: {e}")

def job_value():
    """Calculate value bets based on odds"""
    logger.info("💰 [VALUE] Starting value bet analysis...")
    try:
        from db_client import get_db_client
        db = get_db_client()
        # Import from metrics
        sys.path.insert(0, os.path.join(project_root, 'metrics'))
        from value import ValueBetEngine
        engine = ValueBetEngine(db)
        engine.process_value_bets()
        logger.info("✅ [VALUE] Completed successfully")
    except Exception as e:
        logger.error(f"❌ [VALUE] Failed: {e}")

def run_initial_sync():
    """Run all scrapers once at startup to ensure fresh data"""
    logger.info("=" * 50)
    logger.info("🚀 INITIAL SYNC - Loading fresh data...")
    logger.info("=" * 50)
    
    # Run upcoming first (most important for desktop)
    job_upcoming()
    time.sleep(2)
    
    # Then live
    job_live()
    time.sleep(2)
    
    # Then value bets
    job_value()
    
    logger.info("=" * 50)
    logger.info("✅ INITIAL SYNC COMPLETE")
    logger.info("=" * 50)

def main():
    logger.info("=" * 60)
    logger.info("🎾 TENNIS AI - AUTO SCHEDULER STARTING")
    logger.info(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"   Log: {log_file}")
    logger.info("=" * 60)
    
    # Create scheduler
    scheduler = BlockingScheduler()
    
    # Schedule jobs
    # Upcoming: Every 30 minutes
    scheduler.add_job(
        job_upcoming,
        IntervalTrigger(minutes=30),
        id='upcoming_scraper',
        name='Upcoming Matches Scraper',
        replace_existing=True
    )
    
    # Live: Every 2 minutes
    scheduler.add_job(
        job_live,
        IntervalTrigger(minutes=2),
        id='live_monitor',
        name='Live Match Monitor',
        replace_existing=True
    )
    
    # Value Bets: Every hour
    scheduler.add_job(
        job_value,
        IntervalTrigger(hours=1),
        id='value_bets',
        name='Value Bet Calculator',
        replace_existing=True
    )
    
    logger.info("\n📅 SCHEDULED JOBS:")
    logger.info("   • Upcoming Matches: Every 30 min")
    logger.info("   • Live Monitor: Every 2 min")
    logger.info("   • Value Bets: Every 1 hour")
    logger.info("\nPress Ctrl+C to stop\n")
    
    # Run initial sync
    run_initial_sync()
    
    # Start scheduler
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("\n🛑 Scheduler stopped by user")
        scheduler.shutdown()

if __name__ == "__main__":
    main()
