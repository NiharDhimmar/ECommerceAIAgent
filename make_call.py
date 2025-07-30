from twilio.rest import Client
import os
from dotenv import load_dotenv

load_dotenv()

account_sid = os.getenv('TWILIO_ACCOUNT_SID')
auth_token = os.getenv('TWILIO_AUTH_TOKEN')
from_number = os.getenv('TWILIO_FROM_NUMBER')
to_number = os.getenv('TWILIO_TO_NUMBER')
ngrok_url = os.getenv('NGROK_URL')

client = Client(account_sid, auth_token)

call = client.calls.create(
    to=to_number,
    from_=from_number,
    url=f'{ngrok_url}/voice',
    record=True,
    recording_status_callback=f'{ngrok_url}/recording-complete',
    recording_status_callback_method='POST',
    recording_status_callback_event=['completed']
)

print(f"Call initiated. SID: {call.sid}")
