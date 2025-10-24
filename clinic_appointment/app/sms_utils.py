import os
from twilio.rest import Client

def send_sms(to, body):
    sid = os.getenv('TWILIO_ACCOUNT_SID')
    token = os.getenv('TWILIO_AUTH_TOKEN')
    from_num = os.getenv('TWILIO_FROM_NUMBER')
    if not (sid and token and from_num):
        return None
    client = Client(sid, token)
    msg = client.messages.create(body=body, from_=from_num, to=to)
    return msg.sid
