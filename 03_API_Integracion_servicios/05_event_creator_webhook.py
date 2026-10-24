import hashlib
import hmac
import json
import os
import time

from dotenv import load_dotenv


load_dotenv()
    
secret_key = os.getenv("MY_SECRET_KEY")


event = {
    "emitted_at": int(time.time()),
    "event_type": "user.created",
    "data": {
        "user_id": 123,
        "name": "John Doe",
        "email": "john.doe@example.com"
    }
}

event_str = json.dumps(event)
timestamp = str(int(time.time()))
if secret_key is None:
    raise ValueError("MY_SECRET_KEY environment variable is not set.")
signature = hmac.new(secret_key.encode(), event_str.encode(), hashlib.sha256).hexdigest()
signature_header = f"t={timestamp},v1={signature}"
print("event_str:", event_str)
print("Signature:", signature)

# ! We got the signature header, now we can send the request to the webhook endpoint with the signature header included.
# ! We need to use postman the webhook endpoint.