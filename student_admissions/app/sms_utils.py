import os
from twilio.rest import Client

def send_sms(to_number, body):
    sid = os.getenv('TWILIO_ACCOUNT_SID')
    token = os.getenv('TWILIO_AUTH_TOKEN')
    from_number = os.getenv('TWILIO_FROM_NUMBER')
    if not (sid and token and from_number):
        # optional: log or raise depending on your policy
        return False
    client = Client(sid, token)
    message = client.messages.create(body=body, from_=from_number, to=to_number)
    return message.sid
