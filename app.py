import os
import time
import logging
import requests
from flask import Flask, request, Response, session as flask_session, send_from_directory
from twilio.twiml.voice_response import VoiceResponse, Gather
from dotenv import load_dotenv
from intent_core import load_saved_assets, predict_intent
from requests.auth import HTTPBasicAuth

# Load environment variables
load_dotenv()
SECRET_KEY = os.getenv('SECRET_KEY', 'change_this_secret')
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
HUMAN_AGENT_NUMBER = os.getenv('HUMAN_AGENT_NUMBER') 



# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

# Flask setup
app = Flask(__name__)
app.secret_key = SECRET_KEY
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = True

# Conversation logging
conversation_logs = {}

# Sample questions
questions = [
    "We noticed an abandoned cart in our system—did you encounter any issues during checkout?",
    "I would like to cancel an order",
    "Can you help me to contact an agent?",
    "Is anybody available at customer service?",
    "How can I file a complaint?",
    "How to check your refund policy?",
    "Show me your allowed payment methods.",
    "Do you accept card?",
    "How can I find my invoice?",
    "Where can I make an order?"
]
question_index = 0

# Call forwarding configuration
CUSTOMER_SERVICE_KEYWORDS = [
    "customer service", "customer support", "human agent", "agent", 
    "representative", "operator", "live person", "speak to someone",
    "talk to someone", "human", "real person", "customer care",
    "support team", "help desk", "service desk"
]

# Load intent model
load_saved_assets()

# Helpers
def create_gather(prompt):
    gather = Gather(
        input='speech',
        timeout=0.5,
        speech_timeout='auto',
        action='/gather',
        language='en-US',
        hints='order,address,delivery,number,yes,no'
    )
    gather.say(prompt, voice='alice')
    return gather

def save_conversation_log(call_sid):
    """Save conversation log to file"""
    if call_sid in conversation_logs:
        try:
            os.makedirs("transcripts", exist_ok=True)
            file_path = os.path.join("transcripts", f"{call_sid}.txt")
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"Call SID: {call_sid}\n")
                f.write(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 50 + "\n\n")
                
                for entry in conversation_logs[call_sid]:
                    f.write(f"{entry}\n")
            
            logger.info(f"Conversation log saved: {file_path}")
            # Clean up the log from memory
            del conversation_logs[call_sid]
        except Exception as e:
            logger.error(f"Failed to save conversation log: {e}")

def add_conversation_log(call_sid, message):
    """Add a message to the conversation log"""
    if call_sid not in conversation_logs:
        conversation_logs[call_sid] = []
    conversation_logs[call_sid].append(f"[{time.strftime('%H:%M:%S')}] {message}")

def check_customer_service_request(speech):
    """Check if the user is requesting customer service or human agent"""
    speech_lower = speech.lower()
    return any(keyword in speech_lower for keyword in CUSTOMER_SERVICE_KEYWORDS)

def forward_to_human_agent(call_sid):
    """Forward the call to a human agent"""
    resp = VoiceResponse()
    
    # Log the forwarding action
    if call_sid:
        add_conversation_log(call_sid, "SYSTEM: Forwarding call to human agent")
        save_conversation_log(call_sid)
    
    # Inform the user and transfer to human agent
    resp.say("I understand you'd like to speak with a human agent. Please hold while I transfer your call.", voice='alice')
    resp.dial(HUMAN_AGENT_NUMBER)
    
    logger.info(f"Call {call_sid} forwarded to human agent at {HUMAN_AGENT_NUMBER}")
    return resp

@app.route("/")
def index():
    return "Twilio Voice Flask app is running."



@app.route("/voice", methods=["POST"])
def voice():
    global question_index
    question_index = 0
    resp = VoiceResponse()
    resp.append(create_gather(questions[question_index]))

    # Add recording
    ngrok_url = os.getenv('NGROK_URL')
    resp.record(
        max_length=3600,
        play_beep=True,
        recording_status_callback=f"{ngrok_url}/recording-complete",
        recording_status_callback_method="POST",
        recording_status_callback_event=["completed"]
    )

    resp.say("We did not receive any input. Goodbye!", voice='alice')
    flask_session['gather_start'] = time.time()
    flask_session['first_question_repeated'] = False
    flask_session['last_prompt'] = questions[question_index]

    # Get call SID and start conversation logging
    call_sid = request.form.get('CallSid')
    if call_sid:
        add_conversation_log(call_sid, f"SYSTEM: Initial greeting and first question: '{questions[question_index]}'")
    
    logger.info("Started call. Asked first question.")
    return Response(str(resp), mimetype='text/xml')

@app.route("/gather", methods=["POST"])
def gather():
    global question_index
    speech = (request.values.get('SpeechResult') or '').strip().lower()
    speech = speech[:256]
    ngrok_url = os.getenv('NGROK_URL')

    gather_start = flask_session.get('gather_start')
    if gather_start:
        logger.info(f"Gather API time: {time.time() - gather_start:.3f}s")
    
    # Get call SID for logging
    call_sid = request.form.get('CallSid')
    
    if speech:
        logger.info(f"USER SAID: {speech}")
        if call_sid:
            add_conversation_log(call_sid, f"USER: {speech}")
    else:
        logger.info("USER SAID: [No speech detected]")
        if call_sid:
            add_conversation_log(call_sid, "USER: [No speech detected]")

    resp = VoiceResponse()
    if speech:
        # Check for customer service request first
        if check_customer_service_request(speech):
            logger.info(f"Customer service request detected: {speech}")
            if call_sid:
                add_conversation_log(call_sid, f"USER: {speech}")
            return Response(str(forward_to_human_agent(call_sid)), mimetype='text/xml')
        
        if any(word in speech for word in ["goodbye", "exit", "quit"]):
            resp.say("Thank you for your responses. Goodbye!", voice='alice')
            resp.hangup()
            if call_sid:
                add_conversation_log(call_sid, "SYSTEM: Thank you for your responses. Goodbye!")
                save_conversation_log(call_sid)
        else:
            try:
                result = predict_intent(speech)
                intent = result.get("intent")
                confidence = float(result.get("confidence") or 0)
                logger.info(f"Intent: {intent}, Confidence: {confidence}")
            except Exception as e:
                logger.error(f"Intent prediction error: {e}")
                resp.say("Sorry, there was an error processing your request.", voice='alice')
                resp.hangup()
                if call_sid:
                    add_conversation_log(call_sid, "SYSTEM: Sorry, there was an error processing your request.")
                    save_conversation_log(call_sid)
                return Response(str(resp), mimetype='text/xml')

            if intent and confidence > 0.8:
                resp.append(create_gather(intent))
                flask_session['gather_start'] = time.time()
                flask_session['last_prompt'] = intent
                if call_sid:
                    add_conversation_log(call_sid, f"SYSTEM: {intent}")
                
                # Add recording for ongoing conversation
                resp.record(
                    max_length=3600,
                    play_beep=True,
                    recording_status_callback=f"{ngrok_url}/recording-complete",
                    recording_status_callback_method="POST",
                    recording_status_callback_event=["completed"]
                )
            else:
                resp.say("I could not understand. Please try again.", voice='alice')
                last_prompt = flask_session.get('last_prompt', questions[question_index])
                resp.append(create_gather(last_prompt))
                flask_session['gather_start'] = time.time()
                if call_sid:
                    add_conversation_log(call_sid, f"SYSTEM: {last_prompt}")
                
                # Add recording for ongoing conversation
                resp.record(
                    max_length=3600,
                    play_beep=True,
                    recording_status_callback=f"{ngrok_url}/recording-complete",
                    recording_status_callback_method="POST",
                    recording_status_callback_event=["completed"]
                )
    else:
        if question_index == 0 and not flask_session.get('first_question_repeated', False):
            resp.say("Sorry, I did not understand. Let me repeat the question.", voice='alice')
            resp.append(create_gather(questions[question_index]))
            flask_session['gather_start'] = time.time()
            flask_session['first_question_repeated'] = True
            if call_sid:
                add_conversation_log(call_sid, f"SYSTEM: {questions[question_index]}")
            
            # Add recording for ongoing conversation
            resp.record(
                max_length=3600,
                play_beep=True,
                recording_status_callback=f"{ngrok_url}/recording-complete",
                recording_status_callback_method="POST",
                recording_status_callback_event=["completed"]
            )
        else:
            resp.say("We did not receive any input. Goodbye!", voice='alice')
            resp.hangup()
            if call_sid:
                add_conversation_log(call_sid, "SYSTEM: We did not receive any input. Goodbye!")
                save_conversation_log(call_sid)

    return Response(str(resp), mimetype='text/xml')

@app.route("/recording-complete", methods=["POST"])
def recording_complete():
    recording_url = request.form.get("RecordingUrl")
    recording_sid = request.form.get("RecordingSid")

    if recording_url:
        try:
            os.makedirs("recordings", exist_ok=True)
            file_path = os.path.join("recordings", f"{recording_sid}.mp3")

            response = requests.get(
                recording_url + ".mp3",
                auth=HTTPBasicAuth(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN),
                headers={"Accept": "audio/mpeg"}
            )

            if response.status_code == 200:
                with open(file_path, 'wb') as f:
                    f.write(response.content)
                logger.info(f"Recording saved at {file_path}")
            else:
                logger.error(f"Failed to download recording. Status: {response.status_code}")
        except Exception as e:
            logger.error(f"Exception while downloading recording: {e}")
    else:
        logger.warning("No recording URL found.")
    return Response("Recording saved", status=200)



@app.route('/recordings/<filename>')
def serve_recording(filename):
    return send_from_directory('recordings', filename)

@app.route('/transcripts/<filename>')
def serve_transcript(filename):
    return send_from_directory('transcripts', filename)

@app.route("/play/<recording_sid>")
def play_recording(recording_sid):
    file_url = f"/recordings/{recording_sid}.mp3"
    return f"""
    <html>
    <head><title>Play Recording</title></head>
    <body>
        <h2>Call Recording: {recording_sid}</h2>
        <audio controls autoplay>
            <source src="{file_url}" type="audio/mpeg">
            Your browser does not support the audio tag.
        </audio>
        <br>
        <a href="{file_url}" download>Download Recording</a>
    </body>
    </html>
    """

if __name__ == "__main__":
    app.run(debug=True)
