import sys
sys.path.insert(0, '.')
from app import app
from models.user_model import get_user_by_email

client = app.test_client()

print("Testing reset password for dummy user...")

# Create a test user first or test with an invalid one
res1 = client.post('/api/auth/reset-password', json={"email": "nonexistent@example.com", "new_password": "newpassword123"})
print("Reset nonexistent:", res1.get_json())

# Register a new test user
res2 = client.post('/api/auth/register', json={"full_name": "Test User", "email": "testreset@example.com", "password": "oldpassword"})
print("Register:", res2.get_json())

# Reset password for test user
res3 = client.post('/api/auth/reset-password', json={"email": "testreset@example.com", "new_password": "newpassword123"})
print("Reset existing:", res3.get_json())

# Try logging in with the new password
res4 = client.post('/api/auth/login', json={"email": "testreset@example.com", "password": "newpassword123"})
print("Login with new password:", "success" if res4.status_code == 200 else "failed")
