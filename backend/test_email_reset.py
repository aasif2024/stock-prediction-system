import sys
import os
import time
sys.path.insert(0, '.')
from app import app
from models.user_model import get_user_by_email

import io
import contextlib

client = app.test_client()

print("Testing OTP Reset Flow...")

# 1. Register user
client.post('/api/auth/register', json={"full_name": "OTP User", "email": "otp@example.com", "password": "oldpassword"})

# 2. Forgot Password (should print mock email with OTP)
f = io.StringIO()
with contextlib.redirect_stdout(f):
    res_forgot = client.post('/api/auth/forgot-password', json={"email": "otp@example.com"})

stdout_output = f.getvalue()
print("Forgot Password Response:", res_forgot.get_json())
print("Console Output (Mock Email):\n", stdout_output)

# 3. Extract OTP
otp = None
for line in stdout_output.split('\n'):
    if "Your OTP is:" in line:
        otp = line.split("Your OTP is: ")[1].strip()
        break

if otp:
    print(f"Extracted OTP: {otp}")
    
    # Test Invalid OTP
    res_invalid = client.post('/api/auth/reset-password', json={"email": "otp@example.com", "otp": "000000", "new_password": "securenewpassword"})
    print("Invalid OTP Response:", res_invalid.get_json())

    # 4. Reset Password with correct OTP
    res_reset = client.post('/api/auth/reset-password', json={"email": "otp@example.com", "otp": otp, "new_password": "securenewpassword"})
    print("Correct OTP Response:", res_reset.get_json())
    
    # 5. Login with new password
    res_login = client.post('/api/auth/login', json={"email": "otp@example.com", "password": "securenewpassword"})
    print("Login with new password:", "success" if res_login.status_code == 200 else "failed")
else:
    print("Failed to extract OTP from mock email!")
