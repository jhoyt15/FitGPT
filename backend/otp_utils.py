
import random
import time

otp_store = {}  # In-memory storage: {email: (otp, expiry_time)}

def generate_otp():
    return str(random.randint(100000, 999999))

def save_otp(email, otp, ttl=300):
    expiry = time.time() + ttl
    otp_store[email] = (otp, expiry)

def verify_otp(email, entered_otp):
    otp_data = otp_store.get(email)
    if not otp_data:
        return False
    otp, expiry = otp_data
    if time.time() > expiry:
        return False
    return otp == entered_otp
