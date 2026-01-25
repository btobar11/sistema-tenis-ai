from datetime import datetime, timedelta
from scrapers.db_client import get_db_client

# ATP Tour Zones for travel calculation
TOUR_ZONES = {
    "North America": ["US Open", "Miami", "Indian Wells", "Cincinnati", "Washington", "Atlanta", "Winston-Salem", "Canadian Open", "Montreal", "Toronto"],
    "Europe": ["Roland Garros", "Wimbledon", "Rome", "Madrid", "Barcelona", "Monte Carlo", "Hamburg", "Munich", "Geneva", "Lyon", "Stuttgart", "Halle", "Queens", "Eastbourne", "Mallorca", "Vienna", "Basel", "Paris Masters", "Antwerp", "Stockholm", "Metz"],
    "Asia-Pacific": ["Australian Open", "Shanghai Masters", "Tokyo", "Beijing", "Seoul", "Hong Kong", "Brisbane", "Sydney", "Adelaide", "Auckland"],
    "South America": ["Rio", "Buenos Aires", "Santiago", "Sao Paulo", "Cordoba"],
    "Middle East/Africa": ["Dubai", "Doha", "ATP Finals", "Tel Aviv", "Marrakech"]
}

def get_zone(tournament_name):
    """Get zone for a tournament."""
    if not tournament_name:
        return "Unknown"
    t_lower = tournament_name.lower()
    for zone, tournaments in TOUR_ZONES.items():
        for t in tournaments:
            if t.lower() in t_lower:
                return zone
    return "Europe"  # Default

ZONE_DISTANCES = {
    ("North America", "Europe"): 6,
    ("North America", "Asia-Pacific"): 10,
    ("North America", "South America"): 4,
    ("North America", "Middle East/Africa"): 8,
    ("Europe", "Asia-Pacific"): 8,
    ("Europe", "South America"): 8,
    ("Europe", "Middle East/Africa"): 3,
    ("Asia-Pacific", "South America"): 12,
    ("Asia-Pacific", "Middle East/Africa"): 6,
    ("South America", "Middle East/Africa"): 10,
}

def get_travel_distance(zone1, zone2):
    """Get normalized travel score between zones (0-10)."""
    if zone1 == zone2:
        return 0
    key = tuple(sorted([zone1, zone2]))
    return ZONE_DISTANCES.get(key, 5)


class FatigueEngine:
    def __init__(self, db_client=None):
        self.db = db_client if db_client else get_db_client()

    def get_matches_in_window(self, player_id, days=14):
        """
        Count matches played in the last N days.
        """
        try:
            since_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            # Query matches where player was p1 or p2 and date >= since_date
            # Simple approach: query all recent matches for player
            query = f"or=(player1_id.eq.{player_id},player2_id.eq.{player_id})"
            endpoint = f"{self.db.url}/rest/v1/matches?select=id,date,score_full&{query}&date=gte.{since_date}"
            
            r = self.db._request_with_retry('get', endpoint)
            if r and r.status_code == 200:
                matches = r.json()
                return len(matches), matches
        except Exception as e:
            print(f"  [Fatigue] Error fetching matches for {player_id}: {e}")
        return 0, []

    def calculate_fatigue_index(self, player_id):
        """
        Returns a normalized fatigue index (0.0 to 1.0).
        Consider:
        - Recent Load (last 7 days matches)
        - Intensity (Sets played)
        - Duration (Estimated via sets if no minutes data)
        - "Grind Factor" (Tie-breaks or 7-5 sets)
        - Travel Factor (Zone changes in last 14 days)
        """
        matches_7d, list_7d = self.get_matches_in_window(player_id, 7)
        matches_14d, list_14d = self.get_matches_in_window(player_id, 14)
        
        # Base Load
        # 1 match ~ 1.0 unit
        load_score = len(list_7d) * 1.5 + (len(list_14d) - len(list_7d)) * 0.5
        
        # Intensity Calculation
        tie_breaks = 0
        total_sets = 0
        estimated_minutes = 0
        tournaments = []
        
        for m in list_14d:
            score = m.get('score_full', '')
            tournament = m.get('tournament', '')
            if tournament:
                tournaments.append(tournament)
            
            if not score: continue
            
            # Simple parser for sets and tie-breaks
            sets = score.strip().split(' ')
            num_sets = len(sets)
            total_sets += num_sets
            
            # Duration estimation: 3 sets ~90 min, 4 sets ~150 min, 5 sets ~200 min
            if num_sets == 2:
                estimated_minutes += 60
            elif num_sets == 3:
                estimated_minutes += 90
            elif num_sets == 4:
                estimated_minutes += 150
            elif num_sets == 5:
                estimated_minutes += 200
            
            for s in sets:
                if '7-6' in s or '6-7' in s:
                    tie_breaks += 1
                    estimated_minutes += 15  # TB adds time
                elif '7-5' in s or '5-7' in s:
                    tie_breaks += 0.5  # Long set
                    estimated_minutes += 10
        
        intensity_score = (total_sets * 0.4) + (tie_breaks * 0.6)
        
        # Duration Factor (normalize: 500 min = high fatigue)
        duration_factor = min(1.0, estimated_minutes / 500.0) * 2.0
        
        # Travel Factor
        travel_score = 0
        if len(tournaments) >= 2:
            zones = [get_zone(t) for t in tournaments]
            for i in range(1, len(zones)):
                travel_score += get_travel_distance(zones[i-1], zones[i]) * 0.1
        
        # Combine Raw Fatigue
        raw_fatigue = load_score + intensity_score + duration_factor + travel_score
        
        # Normalize (Heuristic max adjusted for new factors)
        norm_index = min(1.0, raw_fatigue / 15.0)
        
        return {
            "fatigue_index": round(norm_index, 2),
            "raw_score": round(raw_fatigue, 2),
            "matches_7d": matches_7d,
            "matches_14d": matches_14d,
            "sets_14d": total_sets,
            "grind_factor": tie_breaks,
            "estimated_minutes_14d": estimated_minutes,
            "travel_score": round(travel_score, 2),
            "last_calculated": datetime.now().isoformat()
        }

    def update_player_fatigue(self, player_id):
        """
        Calculate and update player metadata/stats table.
        Assuming we store this in 'players' metadata or a separate 'player_stats' table.
        For MVP, let's put it in a new 'fatigue_metrics' table or just return it for the AI to use.
        Let's create tracking table later. For now, we return it.
        """
        return self.calculate_fatigue_index(player_id)
