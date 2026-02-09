from db_client import get_db_client
import json

def check():
    db = get_db_client()
    try:
        print("Checking analysis_results...")
        res = db.from_('analysis_results').select('*').limit(5).execute()
        if res.error:
            print(f"Error: {res.error}")
        else:
            print(f"Found {len(res.data)} analysis results.")
            if res.data:
                print(json.dumps(res.data[0], indent=2))
                
    except Exception as e:
        print(f"Script Error: {e}")

if __name__ == "__main__":
    check()
