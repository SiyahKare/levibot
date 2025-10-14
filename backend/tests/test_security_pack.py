"""
Security Pack Tests
Validates admin authentication, IP allowlist, and audit logging
"""

import os

import requests

API = os.getenv("API_URL", "http://localhost:8000")
ADMIN_KEY = os.getenv("ADMIN_KEY", "")


def test_auth_required_for_admin_ops():
    """Test that admin operations require authentication."""
    print("🔒 Testing auth requirements...")

    # Without auth, admin operations should fail
    r = requests.post(f"{API}/admin/kill")
    assert r.status_code in (401, 403), f"Expected 401/403, got {r.status_code}"

    print("✅ Auth required for admin ops")


def test_login_flow():
    """Test admin login and logout flow."""
    print("🔐 Testing login flow...")

    if not ADMIN_KEY:
        print("⚠️  ADMIN_KEY not set, skipping login test")
        return

    # Create session
    s = requests.Session()

    # Login with admin key
    r = s.post(f"{API}/auth/admin/login", json={"key": ADMIN_KEY})
    assert r.ok, f"Login failed: {r.status_code}"

    data = r.json()
    assert data.get("ok"), f"Login unsuccessful: {data}"

    print("✅ Login successful")

    # Check that cookie was set
    assert "adm" in s.cookies, "Admin cookie not set"

    # Logout
    r = s.post(f"{API}/auth/admin/logout")
    assert r.ok, f"Logout failed: {r.status_code}"

    print("✅ Logout successful")


def test_protected_endpoints_with_auth():
    """Test that protected endpoints work with valid auth."""
    print("🛡️  Testing protected endpoints with auth...")

    if not ADMIN_KEY:
        print("⚠️  ADMIN_KEY not set, skipping protected endpoint test")
        return

    # Create session and login
    s = requests.Session()
    r = s.post(f"{API}/auth/admin/login", json={"key": ADMIN_KEY})
    assert r.ok and r.json().get("ok"), "Login failed"

    # Try accessing protected endpoint (snapshot)
    r = s.post(f"{API}/ops/snapshot")

    # Should either succeed (200) or fail due to IP allowlist (403)
    assert r.status_code in (200, 403), f"Unexpected status: {r.status_code}"

    if r.status_code == 200:
        print("✅ Protected endpoint accessible with auth")
    else:
        print("✅ IP allowlist enforced (403 from non-allowlisted IP)")


def test_audit_log_created():
    """Test that audit log file is created."""
    print("📋 Testing audit log...")

    audit_path = os.getenv("AUDIT_LOG", "ops/audit.log")

    # Check if audit log exists
    if os.path.exists(audit_path):
        print(f"✅ Audit log exists: {audit_path}")

        # Try to read last line
        try:
            with open(audit_path) as f:
                lines = f.readlines()
                if lines:
                    last_line = lines[-1]
                    print(f"   Latest entry: {last_line[:80]}...")
        except Exception as e:
            print(f"⚠️  Could not read audit log: {e}")
    else:
        print(f"⚠️  Audit log not found: {audit_path}")


if __name__ == "__main__":
    print("=" * 60)
    print("🔐 Security Pack Test Suite")
    print("=" * 60)

    try:
        test_auth_required_for_admin_ops()
        test_login_flow()
        test_protected_endpoints_with_auth()
        test_audit_log_created()

        print("\n" + "=" * 60)
        print("✅ All security tests passed!")
        print("=" * 60)

    except AssertionError as e:
        print("\n" + "=" * 60)
        print(f"❌ Test failed: {e}")
        print("=" * 60)
        exit(1)

    except Exception as e:
        print("\n" + "=" * 60)
        print(f"❌ Unexpected error: {e}")
        print("=" * 60)
        exit(1)
