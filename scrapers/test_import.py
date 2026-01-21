print("Testing imports...")
try:
    from supabase import create_client
    print("Supabase imported successfully.")
except Exception as e:
    print(f"Supabase import failed: {e}")
except AttributeError as e:
    print(f"Supabase import attribute error: {e}")

print("Done.")
