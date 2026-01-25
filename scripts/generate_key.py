from api.services.auth_service import AuthService

def create_key():
    auth = AuthService()
    print("Generating Enterprise Key...")
    
    org = input("Organization Name (e.g. AcmeFund): ") or "TestOrg"
    key = auth.create_key_record(org_id=org, scopes=["read:matches", "read:odds", "read:predictions"])
    
    if key:
        print("\n" + "="*40)
        print(f"✅ API KEY GENERATED FOR: {org}")
        print(f"🔑 KEY: {key}")
        print("⚠️  SAVE THIS NOW. IT WILL NOT BE SHOWN AGAIN.")
        print("="*40 + "\n")
    else:
        print("Failed to create key.")

if __name__ == "__main__":
    create_key()
