# Tennis AI Scrapers & Automation

This directory contains the data ingestion and analysis pipeline for the Tennis AI system.

## 🚀 Quick Start

To run the full pipeline (Live Monitor + Upcoming + AI + Value Bets):

```bash
python scrapers/cron_job.py
```

Arguments:
- `--mode all` (Default) Runs everything.
- `--mode live` Runs only the Live Monitor (Scores + ELO + AI Trigger).
- `--mode upcoming` Runs only the Upcoming Matches scraper.
- `--mode value` Runs only the Value Bet Analysis.

## 📂 Individual Scripts

If you need to run specific parts manually:

### 1. Upcoming Matches
Scrapes scheduled matches from TennisExplorer and saves them to the DB.
```bash
python scrapers/upcoming_scraper.py
```

### 2. Live Monitor
Continuously checks for finished matches, updates scores, calculates ELO, and triggers the AI.
```bash
python scrapers/live_monitor.py
```

### 3. AI Prediction
Generates win probabilities for all "scheduled" matches in the DB.
```bash
python scrapers/ai_engine/predict.py
```

### 4. Value Bet Engine
Compares AI probabilities against live bookmaker odds to find positive EV bets.
```bash
python metrics/value.py
```

## 🛠 Troubleshooting

- **"0 matches found" in MatchComparison**: Ensure `upcoming_scraper.py` has run.
- **"Operation canceled"**: Usually a network timeout. The scripts are designed to be resilient, just re-run.
- **No Value Bets**: The Odds API might be empty (check `check_odds.py`) or no matches have high enough EV.

## ⚙️ Configuration
Ensure your `.env` file in the root directory contains:
- `SUPABASE_URL`
- `SUPABASE_KEY`
- `ODDS_API_KEY`
