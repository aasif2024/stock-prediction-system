import sys
import os
sys.path.insert(0, '.')
from app import app
from models.user_model import get_user_by_email

# We want to catch stdout because our mock email prints to stdout
import io
import contextlib

client = app.test_client()

print("Testing Email SMTP Mock Reset Flow...")

# 1. Register user
client.post('/api/auth/register', json={"full_name": "Email User", "email": "smtp@example.com", "password": "oldpassword"})

# 2. Forgot Password (should print mock email)
f = io.StringIO()
with contextlib.redirect_stdout(f):
    res_forgot = client.post('/api/auth/forgot-password', json={"email": "smtp@example.com"})

stdout_output = f.getvalue()
print("Forgot Password Response:", res_forgot.get_json())
print("Console Output (Mock Email):\n", stdout_output)

# 3. Extract Token from printed mock email
token = None
for line in stdout_output.split('\n'):
    if "Reset Link" in line:
        url = line.split("Reset Link: ")[1]
        token = url.split("token=")[1]
        break

if token:
    print(f"Extracted Token: {token[:20]}...")
    
    # 4. Reset Password with token
    res_reset = client.post('/api/auth/reset-password', json={"token": token, "new_password": "securenewpassword"})
    print("Reset Password Response:", res_reset.get_json())
    
    # 5. Login with new password
    res_login = client.post('/api/auth/login', json={"email": "smtp@example.com", "password": "securenewpassword"})
    print("Login with new password:", "success" if res_login.status_code == 200 else "failed")
else:
    print("Failed to extract token from mock email!")
