import sys, io, contextlib
sys.path.insert(0, '.')
from app import app

client = app.test_client()

print("=== Testing OTP Flow (demo_otp in response) ===\n")

# 1. Register user
client.post('/api/auth/register', json={
    "full_name": "OTP Test User",
    "email": "otptest2@example.com",
    "password": "oldpassword"
})

# 2. Forgot Password
res = client.post('/api/auth/forgot-password', json={"email": "otptest2@example.com"})
data = res.get_json()
print("Step 1 - Forgot Password Response:", data)
otp = data.get("demo_otp")
print(f"OTP from response: {otp}\n")

if not otp:
    print("FAIL: demo_otp not returned!")
    sys.exit(1)

# 3. Wrong OTP → should fail
res2 = client.post('/api/auth/reset-password', json={
    "email": "otptest2@example.com",
    "otp": "000000",
    "new_password": "newpassword123"
})
print("Step 2 - Wrong OTP:", res2.get_json())

# 4. Correct OTP → should succeed
res3 = client.post('/api/auth/reset-password', json={
    "email": "otptest2@example.com",
    "otp": otp,
    "new_password": "newpassword123"
})
print("Step 3 - Correct OTP:", res3.get_json())

# 5. Login with new password
res4 = client.post('/api/auth/login', json={
    "email": "otptest2@example.com",
    "password": "newpassword123"
})
print("Step 4 - Login with new password:", "SUCCESS" if res4.status_code == 200 else f"FAILED ({res4.status_code})")

# 6. OTP reuse → should fail (cleared after use)
res5 = client.post('/api/auth/reset-password', json={
    "email": "otptest2@example.com",
    "otp": otp,
    "new_password": "anotherpassword"
})
print("Step 5 - Reuse used OTP:", res5.get_json())
