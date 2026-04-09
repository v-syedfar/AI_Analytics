#!/usr/bin/env python3
"""
Complete Blob Storage Debugging Script
Run this to diagnose all Blob Storage issues
"""
import os
import sys
import json

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def check_env_vars():
    print_section("1. Environment Variables")
    
    vars_to_check = [
        'BLOB_CONNECTION_STRING',
        'BLOB_CONTAINER_NAME',
        'BLOB_CURRENT_FILE',
        'BLOB_PREVIOUS_FILE'
    ]
    
    all_set = True
    for var in vars_to_check:
        value = os.environ.get(var)
        if value:
            if var == 'BLOB_CONNECTION_STRING':
                print(f"✅ {var}: {value[:50]}...")
            else:
                print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: NOT SET")
            all_set = False
    
    return all_set

def check_local_settings():
    print_section("2. local.settings.json")
    
    try:
        with open('local.settings.json', 'r') as f:
            settings = json.load(f)
            
        if 'Values' in settings:
            values = settings['Values']
            if 'BLOB_CONNECTION_STRING' in values:
                print(f"✅ BLOB_CONNECTION_STRING found")
                print(f"   {values['BLOB_CONNECTION_STRING'][:50]}...")
            else:
                print(f"❌ BLOB_CONNECTION_STRING not in local.settings.json")
            
            for key in ['BLOB_CONTAINER_NAME', 'BLOB_CURRENT_FILE', 'BLOB_PREVIOUS_FILE']:
                if key in values:
                    print(f"✅ {key}: {values[key]}")
                else:
                    print(f"❌ {key}: not in local.settings.json")
        else:
            print("❌ 'Values' section not found in local.settings.json")
        
        return True
    except FileNotFoundError:
        print("❌ local.settings.json not found")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ local.settings.json is invalid JSON: {e}")
        return False

def check_env_file():
    print_section("3. .env File")
    
    try:
        with open('.env', 'r') as f:
            content = f.read()
        
        if 'BLOB_CONNECTION_STRING' in content:
            print("✅ .env file found with BLOB_CONNECTION_STRING")
        else:
            print("⚠️  .env file found but BLOB_CONNECTION_STRING not set")
        
        return True
    except FileNotFoundError:
        print("⚠️  .env file not found (using local.settings.json instead)")
        return True

def check_blob_connection():
    print_section("4. Blob Storage Connection")
    
    connection_string = os.environ.get('BLOB_CONNECTION_STRING')
    
    if not connection_string:
        print("❌ BLOB_CONNECTION_STRING not set")
        return False
    
    try:
        from azure.storage.blob import BlobServiceClient
        
        client = BlobServiceClient.from_connection_string(connection_string)
        print("✅ Successfully connected to Blob Storage")
        
        # List containers
        containers = list(client.list_containers())
        print(f"✅ Found {len(containers)} container(s)")
        for container in containers:
            print(f"   - {container.name}")
        
        return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        
        error_str = str(e)
        if "AuthenticationFailed" in error_str or "403" in error_str:
            print("\n💡 Hint: Authentication failed - check AccountKey")
        elif "InvalidConnectionString" in error_str:
            print("\n💡 Hint: Connection string format is invalid")
        
        return False

def check_container():
    print_section("5. Container & Files")
    
    connection_string = os.environ.get('BLOB_CONNECTION_STRING')
    container_name = os.environ.get('BLOB_CONTAINER_NAME', 'planning-data')
    current_file = os.environ.get('BLOB_CURRENT_FILE', 'current.csv')
    previous_file = os.environ.get('BLOB_PREVIOUS_FILE', 'previous.csv')
    
    if not connection_string:
        print("❌ BLOB_CONNECTION_STRING not set")
        return False
    
    try:
        from azure.storage.blob import BlobServiceClient
        
        client = BlobServiceClient.from_connection_string(connection_string)
        container_client = client.get_container_client(container_name)
        
        if container_client.exists():
            print(f"✅ Container '{container_name}' exists")
            
            # List blobs
            blobs = list(container_client.list_blobs())
            print(f"✅ Found {len(blobs)} blob(s)")
            
            for blob in blobs:
                print(f"   - {blob.name} ({blob.size} bytes)")
            
            # Check specific files
            print(f"\nChecking required files:")
            current_blob = container_client.get_blob_client(current_file)
            if current_blob.exists():
                props = current_blob.get_blob_properties()
                print(f"✅ {current_file} exists ({props.size} bytes)")
            else:
                print(f"❌ {current_file} NOT FOUND")
            
            previous_blob = container_client.get_blob_client(previous_file)
            if previous_blob.exists():
                props = previous_blob.get_blob_properties()
                print(f"✅ {previous_file} exists ({props.size} bytes)")
            else:
                print(f"❌ {previous_file} NOT FOUND")
            
            return True
        else:
            print(f"❌ Container '{container_name}' does NOT exist")
            return False
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def check_file_parsing():
    print_section("6. File Parsing")
    
    connection_string = os.environ.get('BLOB_CONNECTION_STRING')
    container_name = os.environ.get('BLOB_CONTAINER_NAME', 'planning-data')
    current_file = os.environ.get('BLOB_CURRENT_FILE', 'current.csv')
    
    if not connection_string:
        print("❌ BLOB_CONNECTION_STRING not set")
        return False
    
    try:
        from azure.storage.blob import BlobServiceClient
        import pandas as pd
        import io
        
        client = BlobServiceClient.from_connection_string(connection_string)
        blob_client = client.get_blob_client(container=container_name, blob=current_file)
        
        if not blob_client.exists():
            print(f"❌ {current_file} not found")
            return False
        
        # Download
        data = blob_client.download_blob().readall()
        print(f"✅ Downloaded {current_file} ({len(data)} bytes)")
        
        # Parse
        df = pd.read_csv(io.BytesIO(data), dtype=str)
        print(f"✅ Parsed CSV: {len(df)} rows, {len(df.columns)} columns")
        
        # Check columns
        required = {"LOCID", "PRDID", "GSCEQUIPCAT"}
        columns_upper = {c.upper() for c in df.columns}
        missing = required - columns_upper
        
        if missing:
            print(f"❌ Missing required columns: {missing}")
            print(f"   Found: {sorted(columns_upper)}")
            return False
        else:
            print(f"✅ All required columns present")
            return True
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_api_endpoint():
    print_section("7. API Endpoint Test")
    
    try:
        import requests
        
        url = "http://localhost:7071/api/daily-refresh"
        print(f"Testing: {url}")
        
        response = requests.post(url, json={"source": "blob"}, timeout=10)
        
        if response.status_code == 200:
            print(f"✅ API returned 200 OK")
            data = response.json()
            print(f"   Status: {data.get('status')}")
            print(f"   Total Records: {data.get('totalRecords')}")
            print(f"   Changed Records: {data.get('changedRecordCount')}")
            print(f"   Planning Health: {data.get('planningHealth')}")
            return True
        else:
            print(f"❌ API returned {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to backend")
        print(f"   Make sure backend is running: func start")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("\n" + "="*60)
    print("  BLOB STORAGE DEBUGGING TOOL")
    print("="*60)
    
    results = {
        "Environment Variables": check_env_vars(),
        "local.settings.json": check_local_settings(),
        ".env File": check_env_file(),
        "Blob Connection": check_blob_connection(),
        "Container & Files": check_container(),
        "File Parsing": check_file_parsing(),
        "API Endpoint": check_api_endpoint(),
    }
    
    print_section("SUMMARY")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Blob Storage is working correctly.")
        return 0
    else:
        print("\n⚠️  Some tests failed. See details above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
