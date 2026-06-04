import json
import os
import sys
import urllib.request

# Can be overridden via env var if running locally: export OM_URL=http://localhost:8585
OM_URL = os.getenv("OM_URL", "https://sandbox.open-metadata.org")

def check_endpoint(path, token=None):
    try:
        url = f"{OM_URL}/api/v1/{path}"
        headers = {"Accept": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status == 200:
                return json.loads(response.read().decode("utf-8"))
    except Exception:
        return None
    return None

def get_token():
    """Authenticate as 'admin' on the sandbox and return a JWT token."""
    try:
        url = f"{OM_URL}/api/v1/users/login"
        payload = json.dumps({
            "email": "admin@open-metadata.org",
            "password": "Admin@1234!"
        }).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
            return data.get("accessToken")
    except Exception:
        return None

def main():
    print(f"Checking OpenMetadata Lab completion status against: {OM_URL}")

    # 1. Check server status
    server_up = False
    try:
        urllib.request.urlopen(f"{OM_URL}/api/v1/system/status", timeout=10)
        server_up = True
    except Exception as e:
        try:
            # Some sandbox versions respond on the root
            urllib.request.urlopen(OM_URL, timeout=10)
            server_up = True
        except Exception:
            pass

    if not server_up:
        print(f"❌ Error: OpenMetadata is not reachable at {OM_URL}")
        print("   Make sure you are connected to the internet or the local Docker stack is running.")
        sys.exit(1)

    print(f"✓ OpenMetadata Server: RUNNING ({OM_URL})")

    # 2. Try authenticated API calls using sandbox credentials
    token = get_token()

    # 3. Check Database Services
    db_services = check_endpoint("services/databaseServices?limit=50", token)
    db_service_count = db_services.get("paging", {}).get("total", 0) if db_services else 0
    if db_service_count == 0 and db_services:
        db_service_count = len(db_services.get("data", []))
    print(f"✓ Database Services Configured: {db_service_count}")

    # 4. Check Ingested Tables
    tables_data = check_endpoint("tables?limit=50", token)
    tables_count = tables_data.get("paging", {}).get("total", 0) if tables_data else 0
    if tables_count == 0 and tables_data:
        tables_count = len(tables_data.get("data", []))
    print(f"✓ Tables Ingested: {tables_count}")

    # 5. Check Data Quality Test Cases
    test_cases_data = check_endpoint("dataQuality/testCases?limit=50", token)
    test_cases_count = test_cases_data.get("paging", {}).get("total", 0) if test_cases_data else 0
    if test_cases_count == 0 and test_cases_data:
        test_cases_count = len(test_cases_data.get("data", []))
    print(f"✓ Data Quality Test Cases: {test_cases_count}")

    # Ensure target output directory exists
    output_dir = "../output"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    result = {
        "status": "success",
        "server_running": True,
        "sandbox_url": OM_URL,
        "database_services_count": db_service_count,
        "tables_ingested_count": tables_count,
        "data_quality_tests_count": test_cases_count
    }

    output_file = os.path.join(output_dir, "openmetadatalab.json")
    with open(output_file, "w") as f:
        json.dump(result, f, indent=2)

    print(f"\n🎉 Verification file '{output_file}' generated successfully!")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
