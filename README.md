<<<<<<< HEAD
<<<<<<< HEAD
# Twilio Voice Python Project

This project demonstrates basic voice communication using Twilio and Python.

## Features
- Make outbound calls using Twilio
- Receive inbound calls and respond with a message (Flask webhook)

## Setup
1. **Clone the repository** (if not already in the folder)
2. **Create and activate a virtual environment**
   ```sh
   python -m venv venv
   venv\Scripts\activate  # On Windows
   # source venv/bin/activate  # On Mac/Linux
   ```
3. **Install dependencies**
   ```sh
   pip install -r requirements.txt
   ```
4. **Configure Twilio credentials**
   - Edit `make_call.py` and replace the placeholders with your Twilio Account SID, Auth Token, Twilio phone number, and the destination phone number.

## Running the Flask App (for inbound calls)
```sh
python app.py
```
- The webhook endpoint will be available at `http://localhost:5000/voice`.
- Configure your Twilio phone number's Voice webhook to point to this URL (use a tool like [ngrok](https://ngrok.com/) for public access).

## Making an Outbound Call
```sh
python make_call.py
```
- This will initiate a call from your Twilio number to the destination number and play a demo message.

## Notes
- You need a Twilio account and a Twilio phone number.
- For production, secure your credentials and use environment variables. 
=======
# ECommerceAIAgent
>>>>>>> 82f64d4da33e2b72346244d92e07693018d6131c
=======
# ECommerceAIAgent
>>>>>>> 82f64d4da33e2b72346244d92e07693018d6131c
