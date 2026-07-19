import bcrypt
from models.user_model import get_user_by_email, update_user_password, create_user

email = "mohammedaasif1435@gmail.com"
new_password = "Aasif@1435"
pw_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()

user = get_user_by_email(email)
if user:
    update_user_password(email, pw_hash)
    print("Password reset successfully for existing user in PostgreSQL!")
else:
    create_user("Mohammed Aasif", email, pw_hash)
    print("User did not exist in PostgreSQL. Created a new user!")
