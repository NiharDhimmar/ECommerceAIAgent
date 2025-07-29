import requests

# Change this if your Flask app is running elsewhere
BASE_URL = 'http://localhost:5000'

def test_gather(speech):
    resp = requests.post(f'{BASE_URL}/gather', data={'SpeechResult': speech})
    print('Status:', resp.status_code)
    print('Response:', resp.text)

if __name__ == '__main__':
    # Example test
    test_gather('I want to check my order status') 