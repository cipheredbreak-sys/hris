#!/usr/bin/env python3
"""
Simple script to test HRIS endpoints after fixing 404 errors
Run this after starting the Django server to verify everything works
"""

import requests
import json
import sys
import time

# Base URL for the Django server
BASE_URL = "http://localhost:8089"

def test_endpoint(url, method="GET", data=None, expected_status=200, description=""):
    """Test an endpoint and return success/failure"""
    full_url = f"{BASE_URL}{url}"
    
    try:
        if method == "GET":
            response = requests.get(full_url, timeout=10)
        elif method == "POST":
            response = requests.post(full_url, json=data, timeout=10)
        
        success = response.status_code == expected_status
        status_icon = "✅" if success else "❌"
        
        print(f"{status_icon} {method} {url} - {response.status_code} - {description}")
        
        if not success:
            print(f"   Expected: {expected_status}, Got: {response.status_code}")
            if response.text:
                print(f"   Response: {response.text[:200]}...")
        
        return success
        
    except requests.exceptions.RequestException as e:
        print(f"❌ {method} {url} - Connection Error - {description}")
        print(f"   Error: {e}")
        return False

def main():
    print("🧪 Testing HRIS Endpoints")
    print("=" * 50)
    
    # Test if server is running
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        print(f"✅ Server is running at {BASE_URL}")
    except requests.exceptions.RequestException:
        print(f"❌ Server not accessible at {BASE_URL}")
        print("Please start the Django server first:")
        print("  python manage.py runserver 8089")
        return False
    
    print("\n📍 Testing Core Endpoints:")
    
    # Core endpoints
    tests = [
        # Basic pages
        ("/", "GET", None, 200, "API Root"),
        ("/admin/", "GET", None, 200, "Admin Interface"),
        ("/swagger/", "GET", None, 200, "Swagger Documentation"),
        ("/redoc/", "GET", None, 200, "ReDoc Documentation"),
        
        # Authentication pages
        ("/accounts/login/", "GET", None, 200, "Login Page"),
        ("/accounts/signup/", "GET", None, 200, "Signup Page"),
        
        # API endpoints (should require auth but return structured errors)
        ("/api/auth/user/", "GET", None, 401, "Current User (unauthenticated)"),
        ("/api/users/", "GET", None, 401, "Users List (unauthenticated)"),
        ("/api/organizations/", "GET", None, 401, "Organizations List (unauthenticated)"),
        ("/api/dashboard/stats/", "GET", None, 401, "Dashboard Stats (unauthenticated)"),
    ]
    
    success_count = 0
    total_tests = len(tests)
    
    for url, method, data, expected_status, description in tests:
        if test_endpoint(url, method, data, expected_status, description):
            success_count += 1
    
    print(f"\n📊 Results: {success_count}/{total_tests} tests passed")
    
    if success_count == total_tests:
        print("🎉 All endpoints are working correctly!")
        print("\n🚀 Next steps:")
        print("1. Access admin: http://localhost:8089/admin/")
        print("   Email: admin@hris.com")
        print("   Password: Admin123!@#")
        print("\n2. View API docs: http://localhost:8089/swagger/")
        print("\n3. Test authentication: http://localhost:8089/accounts/login/")
        return True
    else:
        print("❌ Some endpoints are not working properly")
        print("Check the Django server logs for detailed error messages")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)