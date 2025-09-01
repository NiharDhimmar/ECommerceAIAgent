import os
import json
import uuid
import time
from datetime import datetime, timedelta
import logging
import requests
from collections import Counter
from flask import Flask, request, Response, session as flask_session, send_from_directory, jsonify
from flask_cors import CORS
from twilio.twiml.voice_response import VoiceResponse, Gather
from twilio.rest import Client
from dotenv import load_dotenv
from intent_core import load_saved_assets, predict_intent, analyze_conversation_intent
# Database functionality removed - using file system storage only
# PostgreSQL Database Manager
import psycopg2
from psycopg2.extras import RealDictCursor
import json

# Logging setup (moved up for DatabaseManager to use)
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

class PostgreSQLManager:
    def __init__(self):
        self.connection_string = os.getenv('DATABASE_URL') or \
            f"postgresql://{os.getenv('DB_USER', 'postgres')}:{os.getenv('DB_PASSWORD', '')}@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '5432')}/{os.getenv('DB_NAME', 'voiceai')}"
        self._init_database()
    
    def _init_database(self):
        """Initialize database and create tables if they don't exist"""
        try:
            with psycopg2.connect(self.connection_string) as conn:
                with conn.cursor() as cur:
                    # Create transcripts table
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS transcripts (
                            id SERIAL PRIMARY KEY,
                            call_sid VARCHAR(255) UNIQUE NOT NULL,
                            conversation_log TEXT,
                            intent_results JSONB,
                            final_status VARCHAR(50) DEFAULT 'completed',
                            from_number VARCHAR(50),
                            to_number VARCHAR(50),
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    
                    # Create recordings table
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS recordings (
                            id SERIAL PRIMARY KEY,
                            recording_sid VARCHAR(255) UNIQUE NOT NULL,
                            call_sid VARCHAR(255),
                            file_path TEXT,
                            file_size BIGINT,
                            duration INTEGER,
                            recording_url TEXT,
                            status VARCHAR(50) DEFAULT 'completed',
                            from_number VARCHAR(50),
                            to_number VARCHAR(50),
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    
                    conn.commit()
                    logger.info("PostgreSQL database initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    def _get_connection(self):
        """Get database connection"""
        return psycopg2.connect(self.connection_string)
    
    def save_transcript(self, call_sid, conversation_log, intent_results=None, final_status='completed', from_number=None, to_number=None):
        """Save transcript to database"""
        try:
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        INSERT INTO transcripts 
                        (call_sid, conversation_log, intent_results, final_status, 
                         from_number, to_number, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                        ON CONFLICT (call_sid) DO UPDATE SET
                            conversation_log = EXCLUDED.conversation_log,
                            intent_results = EXCLUDED.intent_results,
                            final_status = EXCLUDED.final_status,
                            from_number = EXCLUDED.from_number,
                            to_number = EXCLUDED.to_number,
                            updated_at = CURRENT_TIMESTAMP
                    """, (
                        call_sid, conversation_log, 
                        json.dumps(intent_results) if intent_results else None,
                        final_status, from_number, to_number
                    ))
                    conn.commit()
                    logger.info(f"Transcript saved to database for call {call_sid}")
        except Exception as e:
            logger.error(f"Failed to save transcript to database: {e}")
            raise
    
    def save_recording(self, recording_sid, call_sid, file_path, file_size, duration=None, recording_url=None, status='completed', from_number=None, to_number=None):
        """Save recording to database"""
        try:
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        INSERT INTO recordings 
                        (recording_sid, call_sid, file_path, file_size, duration,
                         recording_url, status, from_number, to_number, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                        ON CONFLICT (recording_sid) DO UPDATE SET
                            call_sid = EXCLUDED.call_sid,
                            file_path = EXCLUDED.file_path,
                            file_size = EXCLUDED.file_size,
                            duration = EXCLUDED.duration,
                            recording_url = EXCLUDED.recording_url,
                            status = EXCLUDED.status,
                            from_number = EXCLUDED.from_number,
                            to_number = EXCLUDED.to_number,
                            updated_at = CURRENT_TIMESTAMP
                    """, (
                        recording_sid, call_sid, file_path, file_size, duration,
                        recording_url, status, from_number, to_number
                    ))
                    conn.commit()
                    logger.info(f"Recording saved to database: {recording_sid}")
        except Exception as e:
            logger.error(f"Failed to save recording to database: {e}")
            raise
    
    def get_transcripts(self, limit=50, offset=0):
        """Get transcripts from database"""
        try:
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT call_sid, conversation_log, intent_results, final_status, 
                               from_number, to_number, created_at
                        FROM transcripts 
                        ORDER BY created_at DESC 
                        LIMIT %s OFFSET %s
                    """, (limit, offset))
                    rows = cur.fetchall()
                    result = []
                    for row in rows:
                        row_dict = dict(row)
                        # Parse intent_results JSON if it's a string
                        if row_dict['intent_results'] and isinstance(row_dict['intent_results'], str):
                            try:
                                row_dict['intent_results'] = json.loads(row_dict['intent_results'])
                            except:
                                row_dict['intent_results'] = None
                        result.append(row_dict)
                    return result
        except Exception as e:
            logger.error(f"Failed to get transcripts: {e}")
            return []
    
    def get_recordings(self, limit=50, offset=0):
        """Get recordings from database"""
        try:
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT recording_sid, call_sid, file_path, file_size, duration,
                               recording_url, status, from_number, to_number, created_at
                        FROM recordings 
                        ORDER BY created_at DESC 
                        LIMIT %s OFFSET %s
                    """, (limit, offset))
                    return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Failed to get recordings: {e}")
            return []
    
    def get_calls(self, limit=50, offset=0):
        """Get calls by joining transcripts and recordings"""
        try:
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT t.call_sid, t.conversation_log, t.intent_results, 
                               t.from_number, t.to_number, t.created_at,
                               r.recording_sid, r.duration as recording_duration, 
                               r.file_path, r.file_size
                        FROM transcripts t
                        LEFT JOIN recordings r ON t.call_sid = r.call_sid
                        ORDER BY t.created_at DESC 
                        LIMIT %s OFFSET %s
                    """, (limit, offset))
                    rows = cur.fetchall()
                    result = []
                    for row in rows:
                        row_dict = dict(row)
                        # Parse intent_results JSON if it's a string
                        if row_dict['intent_results'] and isinstance(row_dict['intent_results'], str):
                            try:
                                row_dict['intent_results'] = json.loads(row_dict['intent_results'])
                            except:
                                row_dict['intent_results'] = None
                        result.append(row_dict)
                    return result
        except Exception as e:
            logger.error(f"Failed to get calls: {e}")
            return []
    
    def get_call_by_sid(self, call_sid):
        """Get specific call/transcript by call_sid"""
        try:
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT call_sid, conversation_log, intent_results, final_status, 
                               from_number, to_number, created_at
                        FROM transcripts 
                        WHERE call_sid = %s
                    """, (call_sid,))
                    row = cur.fetchone()
                    if row:
                        row_dict = dict(row)
                        if row_dict['intent_results'] and isinstance(row_dict['intent_results'], str):
                            try:
                                row_dict['intent_results'] = json.loads(row_dict['intent_results'])
                            except:
                                row_dict['intent_results'] = None
                        return row_dict
                    return None
        except Exception as e:
            logger.error(f"Failed to get call by SID: {e}")
            return None
    
    def get_recording_by_sid(self, recording_sid):
        """Get specific recording by recording_sid"""
        try:
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT recording_sid, call_sid, file_path, file_size, duration,
                               recording_url, status, from_number, to_number, created_at
                        FROM recordings 
                        WHERE recording_sid = %s
                    """, (recording_sid,))
                    row = cur.fetchone()
                    return dict(row) if row else None
        except Exception as e:
            logger.error(f"Failed to get recording by SID: {e}")
            return None
    
    def get_call_metadata_by_sid(self, call_sid):
        """Get call metadata (phone numbers) by call_sid"""
        try:
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT from_number, to_number
                        FROM transcripts 
                        WHERE call_sid = %s
                    """, (call_sid,))
                    row = cur.fetchone()
                    return dict(row) if row else None
        except Exception as e:
            logger.error(f"Failed to get call metadata: {e}")
            return None
    
    def save_call_metadata(self, call_sid, from_number=None, to_number=None, call_status='in-progress', start_time=None):
        """Save call metadata to database"""
        try:
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        INSERT INTO transcripts 
                        (call_sid, from_number, to_number, final_status, updated_at)
                        VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
                        ON CONFLICT (call_sid) DO UPDATE SET
                            from_number = EXCLUDED.from_number,
                            to_number = EXCLUDED.to_number,
                            final_status = EXCLUDED.final_status,
                            updated_at = CURRENT_TIMESTAMP
                    """, (call_sid, from_number, to_number, call_status))
                    conn.commit()
        except Exception as e:
            logger.error(f"Failed to save call metadata: {e}")
            raise

# Initialize database manager
try:
    DatabaseManager = PostgreSQLManager()
    logger.info("PostgreSQL database manager initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize PostgreSQL database manager: {e}")
    logger.info("PostgreSQL is not available. Please install PostgreSQL or set up a cloud database.")
    logger.info("You can use services like:")
    logger.info("- Local: Install PostgreSQL from https://www.postgresql.org/download/")
    logger.info("- Cloud: AWS RDS, Heroku Postgres, Supabase, or Railway")
    logger.info("Set environment variables: DATABASE_URL or DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME")
    DatabaseManager = None
from requests.auth import HTTPBasicAuth

# Load environment variables
load_dotenv()
SECRET_KEY = os.getenv('SECRET_KEY', 'change_this_secret')
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
HUMAN_AGENT_NUMBER = os.getenv('HUMAN_AGENT_NUMBER')

# Flask setup
app = Flask(__name__)
try:
    # Allow local dashboard to call API and static assets directly if proxy is unavailable
    # More flexible CORS for development - allows any local network access
    CORS(app, resources={
        r"/api/*": {"origins": ["http://localhost:3000", "http://127.0.0.1:3000", "http://192.168.10.137:3000"]},
        r"/recordings/*": {"origins": ["http://localhost:3000", "http://127.0.0.1:3000", "http://192.168.10.137:3000"]},
        r"/transcripts/*": {"origins": ["http://localhost:3000", "http://127.0.0.1:3000", "http://192.168.10.137:3000"]},
    })
except Exception:
    pass
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
try:
    if load_saved_assets():
        logger.info("Intent model loaded successfully")
    else:
        logger.error("Failed to load intent model - model files may be missing or corrupted")
        logger.error("Please ensure intent_model.keras, tokenizer.json, and labels.json exist")
except Exception as e:
    logger.error(f"Error loading intent model: {e}")
    logger.error("The application may not function properly without the intent model")

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
            # Also persist to DB if configured
            if DatabaseManager is not None:
                try:
                    conversation_text = "\n".join(conversation_logs[call_sid])
                    
                    # Get phone numbers from call metadata
                    from_number = None
                    to_number = None
                    try:
                        call_metadata = DatabaseManager.get_call_metadata_by_sid(call_sid)
                        if call_metadata:
                            from_number = call_metadata.get('from_number')
                            to_number = call_metadata.get('to_number')
                    except Exception as e:
                        logger.error(f"Failed to get call metadata for transcript: {e}")
                    
                    # Analyze conversation intent
                    intent_results = None
                    try:
                        intent_results = analyze_conversation_intent(conversation_text)
                        logger.info(f"Intent analysis completed for call {call_sid}: {intent_results.get('primary_intent', 'unknown')}")
                    except Exception as intent_err:
                        logger.error(f"Failed to analyze intent for call {call_sid}: {intent_err}")
                    
                    DatabaseManager.save_transcript(
                        call_sid=call_sid,
                        conversation_log=conversation_text,
                        intent_results=intent_results,
                        final_status='completed',
                        from_number=from_number,
                        to_number=to_number
                    )
                    logger.info(f"Transcript saved to database for call {call_sid}")
                except Exception as db_err:
                    logger.error(f"Failed to save transcript to database: {db_err}")
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


def get_twilio_client():
    """Create and return a Twilio REST client, or raise a helpful error."""
    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
        raise RuntimeError("Twilio credentials are not configured. Set TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN in your environment.")
    return Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

@app.route("/")
def index():
    return "Twilio Voice Flask app is running."

# API Endpoints for Admin Dashboard (numbers + minimal settings)


@app.route("/api/twilio/available-numbers", methods=["GET"])
def search_available_numbers():
    """Search available Twilio phone numbers.

    Query params:
    - country: ISO alpha-2 (default: US)
    - type: local|tollfree|mobile (default: local)
    - area_code: e.g. 415 (only for local in some countries)
    - contains: pattern like *555*
    - voice_enabled, sms_enabled, mms_enabled: bool flags
    - limit: number of results (default 20, max 100)
    """
    try:
        client = get_twilio_client()

        country = (request.args.get("country") or "US").upper()
        number_type = (request.args.get("type") or "local").lower()
        contains = request.args.get("contains") or None
        area_code_param = request.args.get("area_code") or None

        def to_bool(v):
            if v is None:
                return None
            return str(v).lower() in ["1", "true", "yes", "y"]

        voice_enabled = to_bool(request.args.get("voice_enabled"))
        sms_enabled = to_bool(request.args.get("sms_enabled"))
        mms_enabled = to_bool(request.args.get("mms_enabled"))
        try:
            limit = int(request.args.get("limit") or 20)
        except ValueError:
            limit = 20
        limit = max(1, min(limit, 100))

        base = client.available_phone_numbers(country)
        if number_type == "tollfree" or number_type == "toll_free":
            searcher = base.toll_free
        elif number_type == "mobile":
            searcher = base.mobile
        else:
            searcher = base.local

        # Build search kwargs based on provided filters
        kwargs = {}
        if contains:
            kwargs["contains"] = contains
        if area_code_param and number_type == "local":
            try:
                kwargs["area_code"] = int(area_code_param)
            except ValueError:
                pass
        if voice_enabled is not None:
            kwargs["voice_enabled"] = voice_enabled
        if sms_enabled is not None:
            kwargs["sms_enabled"] = sms_enabled
        if mms_enabled is not None:
            kwargs["mms_enabled"] = mms_enabled

        numbers = searcher.list(limit=limit, **kwargs)

        results = []
        for n in numbers:
            results.append({
                "friendlyName": getattr(n, "friendly_name", None),
                "phoneNumber": getattr(n, "phone_number", None),
                "locality": getattr(n, "locality", None),
                "region": getattr(n, "region", None),
                "postalCode": getattr(n, "postal_code", None),
                "isoCountry": getattr(n, "iso_country", country),
                "capabilities": getattr(n, "capabilities", {}),
                "beta": getattr(n, "beta", False),
                "addressRequirements": getattr(n, "address_requirements", None),
            })

        return jsonify({
            "country": country,
            "type": number_type,
            "count": len(results),
            "numbers": results
        })
    except Exception as e:
        logger.error(f"Error searching available numbers: {e}")
        return jsonify({"error": "Failed to search available numbers", "details": str(e)}), 500


@app.route("/api/twilio/purchase-number", methods=["POST"])
def purchase_number():
    """Purchase (provision) a Twilio phone number and configure voice webhook."""
    try:
        client = get_twilio_client()
        data = request.get_json(force=True) or {}
        phone_number = data.get("phoneNumber")
        friendly_name = data.get("friendlyName") or "VoiceAI Number"
        body_voice_url = data.get("voiceUrl")
        voice_method = (data.get("voiceMethod") or "POST").upper()

        if not phone_number:
            return jsonify({"error": "phoneNumber is required"}), 400

        ngrok_url = os.getenv('NGROK_URL') or ''
        # If caller provided voiceUrl use it; otherwise default to NGROK_URL/voice when available
        voice_url = body_voice_url or (f"{ngrok_url}/voice" if ngrok_url else None)

        create_kwargs = {
            "phone_number": phone_number,
            "friendly_name": friendly_name,
        }
        if voice_url:
            create_kwargs.update({
                "voice_url": voice_url,
                "voice_method": voice_method,
            })

        incoming = client.incoming_phone_numbers.create(**create_kwargs)

        return jsonify({
            "sid": incoming.sid,
            "phoneNumber": incoming.phone_number,
            "friendlyName": incoming.friendly_name,
            "voiceUrl": getattr(incoming, "voice_url", None),
            "voiceMethod": voice_method if voice_url else None,
            "status": "purchased"
        })
    except Exception as e:
        logger.error(f"Error purchasing number: {e}")
        return jsonify({"error": "Failed to purchase number", "details": str(e)}), 500


@app.route("/api/twilio/my-numbers", methods=["GET"])
def list_owned_numbers():
    """List Twilio numbers owned by the account."""
    try:
        client = get_twilio_client()
        numbers = client.incoming_phone_numbers.list(limit=100)
        results = []
        for n in numbers:
            results.append({
                "sid": n.sid,
                "phoneNumber": n.phone_number,
                "friendlyName": n.friendly_name,
                "voiceUrl": getattr(n, "voice_url", None),
                "smsUrl": getattr(n, "sms_url", None),
                "dateCreated": getattr(n, "date_created", None).isoformat() if getattr(n, "date_created", None) else None,
            })
        return jsonify({"count": len(results), "numbers": results})
    except Exception as e:
        logger.error(f"Error listing owned numbers: {e}")
        return jsonify({"error": "Failed to list owned numbers", "details": str(e)}), 500


@app.route("/api/twilio/numbers/<sid>", methods=["DELETE"])
def release_number(sid):
    """Release (delete) a Twilio number by IncomingPhoneNumber SID."""
    try:
        client = get_twilio_client()
        ok = client.incoming_phone_numbers(sid).delete()
        return jsonify({"sid": sid, "released": bool(ok)})
    except Exception as e:
        logger.error(f"Error releasing number {sid}: {e}")
        return jsonify({"error": "Failed to release number", "details": str(e)}), 500


@app.route("/api/twilio/numbers/<sid>/voice-url", methods=["POST"])
def update_number_voice_url(sid):
    """Update the Voice URL (and method) for an owned Twilio number."""
    try:
        client = get_twilio_client()
        data = request.get_json(force=True) or {}
        voice_url = data.get("voiceUrl")
        voice_method = (data.get("voiceMethod") or "POST").upper()

        if not voice_url:
            # Convenience: if not provided, default to NGROK_URL/voice when available
            ngrok_url = os.getenv('NGROK_URL')
            if not ngrok_url:
                return jsonify({"error": "voiceUrl is required when NGROK_URL is not set"}), 400
            voice_url = f"{ngrok_url}/voice"

        updated = client.incoming_phone_numbers(sid).update(
            voice_url=voice_url,
            voice_method=voice_method,
        )

        return jsonify({
            "sid": updated.sid,
            "phoneNumber": updated.phone_number,
            "friendlyName": updated.friendly_name,
            "voiceUrl": getattr(updated, "voice_url", None),
            "voiceMethod": voice_method,
            "status": "updated"
        })
    except Exception as e:
        logger.error(f"Error updating voice URL for {sid}: {e}")
        return jsonify({"error": "Failed to update voice URL", "details": str(e)}), 500

## Removed mock endpoints: calls, recordings, transcripts, analytics

def _format_duration(seconds: int | None) -> str:
    try:
        total = int(seconds or 0)
        minutes = total // 60
        secs = total % 60
        return f"{minutes}:{secs:02d}" if total > 0 else "-"
    except Exception:
        return "-"

def _format_size(num_bytes: int | None) -> str:
    try:
        size = float(num_bytes or 0)
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024.0:
                return f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    except Exception:
        return "-"

def _to_iso(value) -> str:
    try:
        if hasattr(value, 'isoformat'):
            # Format datetime objects to YYYY-MM-DD HH:MM:SS
            return value.strftime('%Y-%m-%d %H:%M:%S')
        if isinstance(value, str):
            try:
                normalized = value.replace('Z', '+00:00')
                dt = datetime.fromisoformat(normalized)
                return dt.strftime('%Y-%m-%d %H:%M:%S')
            except Exception:
                return value
        return str(value)
    except Exception:
        return ""

@app.route("/api/recordings", methods=["GET"])
def api_get_recordings():
    try:
        if DatabaseManager is None:
            return jsonify([])
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        rows = DatabaseManager.get_recordings(limit=limit, offset=offset) or []
        data = []
        for r in rows:
            call_sid = r.get('call_sid')
            filename = os.path.basename(r.get('file_path') or f"{r.get('recording_sid') or ''}.mp3")
            # Use numbers directly from recordings table
            from_number = r.get('from_number') or ''
            to_number = r.get('to_number') or ''
            phone_number = to_number or from_number
            # Get intent from associated transcript
            intent = ""
            confidence = 0
            sentiment = "neutral"
            if call_sid and DatabaseManager is not None:
                try:
                    transcript = DatabaseManager.get_call_by_sid(call_sid)
                    if transcript and transcript.get('intent_results'):
                        intent_results = transcript.get('intent_results')
                        if isinstance(intent_results, dict):
                            intent = intent_results.get('primary_intent', '')
                            confidence = intent_results.get('primary_confidence', 0)
                            sentiment = intent_results.get('sentiment', 'neutral')
                except Exception as e:
                    logger.error(f"Failed to get intent for recording {r.get('recording_sid')}: {e}")
            
            data.append({
                "id": r.get('recording_sid'),
                "callId": call_sid,
                "filename": filename,
                "duration": _format_duration(r.get('duration')),
                "size": _format_size(r.get('file_size')),
                "timestamp": _to_iso(r.get('created_at')),
                "url": f"/recordings/{r.get('recording_sid')}.mp3",
                "phoneNumber": phone_number or "",
                "fromNumber": from_number or "",
                "toNumber": to_number or "",
                "intent": intent,
                "confidence": confidence,
                "sentiment": sentiment
            })
        return jsonify(data)
    except Exception as e:
        logger.error(f"Error getting recordings (DB): {e}")
        return jsonify({"error": "Failed to get recordings", "details": str(e)}), 500

@app.route("/api/transcripts", methods=["GET"])
def api_get_transcripts():
    try:
        if DatabaseManager is None:
            return jsonify([])
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        rows = DatabaseManager.get_transcripts(limit=limit, offset=offset) or []
        data = []
        for t in rows:
            call_sid = t.get('call_sid')
            # Read numbers directly from transcripts table
            from_number = t.get('from_number') or ''
            to_number = t.get('to_number') or ''
            phone_number = to_number or from_number
            created_at = t.get('created_at')
            
            # Parse intent results
            intent_results = t.get('intent_results')
            primary_intent = ""
            confidence = 0
            if intent_results and isinstance(intent_results, dict):
                primary_intent = intent_results.get('primary_intent', '')
                confidence = intent_results.get('primary_confidence', 0)
            
            # Build conversation array from log text
            conversation = []
            try:
                text = t.get('conversation_log') or ""
                for line in text.splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    # Expect lines like: [HH:MM:SS] USER: message
                    time_part = ""
                    msg = line
                    if line.startswith('[') and ']' in line:
                        time_part = line[1:line.find(']')]
                        msg = line[line.find(']') + 1:].strip()
                    speaker = 'system' if msg.lower().startswith('system:') else 'user' if msg.lower().startswith('user:') else 'system'
                    message = msg.split(':', 1)[1].strip() if ':' in msg else msg
                    conversation.append({
                        "speaker": speaker,
                        "message": message,
                        "time": time_part or ""
                    })
            except Exception:
                conversation = []
            data.append({
                "id": f"TR{call_sid}",
                "callId": call_sid,
                "filename": f"{call_sid}.txt",
                "timestamp": _to_iso(created_at),
                "phoneNumber": phone_number or "",
                "fromNumber": from_number or "",
                "toNumber": to_number or "",
                "intent": primary_intent,
                "confidence": confidence,
                "conversation": conversation,
            })
        return jsonify(data)
    except Exception as e:
        logger.error(f"Error getting transcripts (DB): {e}")
        return jsonify({"error": "Failed to get transcripts", "details": str(e)}), 500

@app.route("/api/transcripts/<call_sid>/intent", methods=["GET"])
def api_get_transcript_intent(call_sid):
    """Get detailed intent analysis for a specific transcript"""
    try:
        if DatabaseManager is None:
            return jsonify({"error": "Database not configured"}), 500
        
        # Get transcript from database
        transcript = DatabaseManager.get_call_by_sid(call_sid)
        if not transcript:
            return jsonify({"error": "Transcript not found"}), 404
        
        conversation_log = transcript.get('conversation_log', '')
        intent_results = transcript.get('intent_results')
        
        # If no intent results exist, analyze the conversation
        if not intent_results:
            try:
                intent_results = analyze_conversation_intent(conversation_log)
                # Save the analysis results back to database
                DatabaseManager.save_transcript(
                    call_sid=call_sid,
                    conversation_log=conversation_log,
                    intent_results=intent_results,
                    final_status=transcript.get('final_status', 'completed'),
                    from_number=transcript.get('from_number'),
                    to_number=transcript.get('to_number')
                )
                logger.info(f"Intent analysis completed and saved for call {call_sid}")
            except Exception as intent_err:
                logger.error(f"Failed to analyze intent for call {call_sid}: {intent_err}")
                return jsonify({"error": "Failed to analyze intent", "details": str(intent_err)}), 500
        
        return jsonify({
            "call_sid": call_sid,
            "intent_analysis": intent_results,
            "conversation_log": conversation_log[:500] + "..." if len(conversation_log) > 500 else conversation_log
        })
        
    except Exception as e:
        logger.error(f"Error getting transcript intent for {call_sid}: {e}")
        return jsonify({"error": "Failed to get transcript intent", "details": str(e)}), 500

@app.route("/api/transcripts/analyze", methods=["POST"])
def api_analyze_transcript():
    """Analyze a provided transcript text"""
    try:
        data = request.get_json()
        if not data or 'conversation_text' not in data:
            return jsonify({"error": "conversation_text is required"}), 400
        
        conversation_text = data['conversation_text']
        
        # Analyze the conversation
        intent_results = analyze_conversation_intent(conversation_text)
        
        return jsonify({
            "intent_analysis": intent_results,
            "analyzed_at": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error analyzing transcript: {e}")
        return jsonify({"error": "Failed to analyze transcript", "details": str(e)}), 500

@app.route("/api/intents/summary", methods=["GET"])
def api_get_intents_summary():
    """Get summary of all analyzed intents"""
    try:
        if DatabaseManager is None:
            return jsonify({"error": "Database not configured"}), 500
        
        # Get all transcripts with intent results
        transcripts = DatabaseManager.get_transcripts(limit=1000, offset=0) or []
        
        intent_summary = {
            "total_transcripts": len(transcripts),
            "analyzed_transcripts": 0,
            "intent_distribution": {},
            "sentiment_distribution": {},
            "urgency_distribution": {},
            "satisfaction_distribution": {},
            "top_topics": [],
            "recent_analyses": []
        }
        
        topic_counter = Counter()
        
        for transcript in transcripts:
            intent_results = transcript.get('intent_results')
            if intent_results and isinstance(intent_results, dict):
                intent_summary["analyzed_transcripts"] += 1
                
                # Count intents
                primary_intent = intent_results.get('primary_intent', 'unknown')
                intent_summary["intent_distribution"][primary_intent] = intent_summary["intent_distribution"].get(primary_intent, 0) + 1
                
                # Count sentiments
                sentiment = intent_results.get('sentiment', 'neutral')
                intent_summary["sentiment_distribution"][sentiment] = intent_summary["sentiment_distribution"].get(sentiment, 0) + 1
                
                # Count urgency levels
                urgency = intent_results.get('urgency_level', 'low')
                intent_summary["urgency_distribution"][urgency] = intent_summary["urgency_distribution"].get(urgency, 0) + 1
                
                # Count satisfaction levels
                satisfaction = intent_results.get('customer_satisfaction', 'neutral')
                intent_summary["satisfaction_distribution"][satisfaction] = intent_summary["satisfaction_distribution"].get(satisfaction, 0) + 1
                
                # Count topics
                key_topics = intent_results.get('key_topics', [])
                for topic in key_topics:
                    topic_name = topic.get('topic', 'Unknown')
                    topic_counter[topic_name] += 1
                
                # Add to recent analyses
                if len(intent_summary["recent_analyses"]) < 10:
                    intent_summary["recent_analyses"].append({
                        "call_sid": transcript.get('call_sid'),
                        "primary_intent": primary_intent,
                        "sentiment": sentiment,
                        "urgency": urgency,
                        "timestamp": _to_iso(transcript.get('created_at'))
                    })
        
        # Get top topics
        intent_summary["top_topics"] = [{"topic": topic, "count": count} for topic, count in topic_counter.most_common(10)]
        
        return jsonify(intent_summary)
        
    except Exception as e:
        logger.error(f"Error getting intents summary: {e}")
        return jsonify({"error": "Failed to get intents summary", "details": str(e)}), 500

@app.route("/api/calls", methods=["GET"])
def api_get_calls():
    """Get calls from database by joining transcripts and recordings"""
    try:
        if DatabaseManager is None:
            return jsonify([])
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        rows = DatabaseManager.get_calls(limit=limit, offset=offset) or []
        data = []
        for row in rows:
            # Extract call data from joined result
            call_sid = row.get('call_sid')
            from_number = row.get('from_number') or ''
            to_number = row.get('to_number') or ''
            phone_number = to_number or from_number
            
            # Get duration from recordings if available
            duration = row.get('recording_duration') or row.get('duration')
            
            # Determine status based on available data
            status = 'completed'
            if not row.get('conversation_log'):
                status = 'failed'
            elif not row.get('recording_sid'):
                status = 'in-progress'
            
            # Calculate start and end times
            created_at = row.get('created_at')
            start_time = _to_iso(created_at) if created_at else ''
            
            # Calculate end time based on duration
            end_time = ''
            if created_at and duration:
                try:
                    from datetime import timedelta
                    # Convert duration from seconds to timedelta
                    if isinstance(duration, str):
                        # Handle duration in format "MM:SS" or "HH:MM:SS"
                        parts = duration.split(':')
                        if len(parts) == 2:
                            minutes, seconds = map(int, parts)
                            duration_seconds = minutes * 60 + seconds
                        elif len(parts) == 3:
                            hours, minutes, seconds = map(int, parts)
                            duration_seconds = hours * 3600 + minutes * 60 + seconds
                        else:
                            duration_seconds = int(duration)
                    else:
                        duration_seconds = int(duration)
                    
                    end_time_dt = created_at + timedelta(seconds=duration_seconds)
                    end_time = _to_iso(end_time_dt)
                except:
                    end_time = start_time
            
            # Parse intent results
            intent_results = row.get('intent_results')
            primary_intent = ""
            confidence = 0
            sentiment = "neutral"
            if intent_results and isinstance(intent_results, dict):
                primary_intent = intent_results.get('primary_intent', '')
                confidence = intent_results.get('primary_confidence', 0)
                sentiment = intent_results.get('sentiment', 'neutral')
            
            data.append({
                "id": call_sid,
                "phoneNumber": phone_number,
                "fromNumber": from_number,
                "toNumber": to_number,
                "duration": _format_duration(duration),
                "status": status,
                "startTime": start_time,
                "endTime": end_time,
                "recordingUrl": f"/recordings/{row.get('recording_sid')}.mp3" if row.get('recording_sid') else None,
                "transcript": row.get('conversation_log', '')[:200] + '...' if row.get('conversation_log') and len(row.get('conversation_log', '')) > 200 else row.get('conversation_log', ''),
                "intent": primary_intent,
                "confidence": confidence,
                "sentiment": sentiment
            })
        return jsonify(data)
    except Exception as e:
        logger.error(f"Error getting calls (DB): {e}")
        return jsonify({"error": "Failed to get calls", "details": str(e)}), 500

## Calendar module removed per request

@app.route("/api/dashboard/stats", methods=["GET"])
def api_get_dashboard_stats():
    """Get dashboard statistics"""
    try:
        if DatabaseManager is None:
            return jsonify({
                "totalCalls": 0,
                "totalRecordings": 0,
                "totalTranscripts": 0,
                "avgCallDuration": 0,
                "successRate": 0,
                "activeAgents": 0
            })
        
        # Get calls data to calculate stats
        calls_data = DatabaseManager.get_calls(limit=1000, offset=0) or []
        
        total_calls = len(calls_data)
        total_recordings = len([call for call in calls_data if call.get('recording_sid')])
        total_transcripts = len([call for call in calls_data if call.get('conversation_log')])
        
        # Calculate average call duration
        durations = []
        for call in calls_data:
            duration = call.get('recording_duration') or call.get('duration')
            if duration:
                try:
                    if isinstance(duration, str):
                        # Handle duration in format "MM:SS" or "HH:MM:SS"
                        parts = duration.split(':')
                        if len(parts) == 2:
                            minutes, seconds = map(int, parts)
                            duration_seconds = minutes * 60 + seconds
                        elif len(parts) == 3:
                            hours, minutes, seconds = map(int, parts)
                            duration_seconds = hours * 3600 + minutes * 60 + seconds
                        else:
                            duration_seconds = int(duration)
                    else:
                        duration_seconds = int(duration)
                    durations.append(duration_seconds)
                except:
                    pass
        
        avg_call_duration = round(sum(durations) / len(durations) / 60, 1) if durations else 0
        
        # Calculate success rate (calls with transcripts)
        success_rate = round((total_transcripts / total_calls) * 100, 1) if total_calls > 0 else 0
        
        # Mock active agents (in real app, this would track actual active agents)
        active_agents = 1 if total_calls > 0 else 0
        
        stats = {
            "totalCalls": total_calls,
            "totalRecordings": total_recordings,
            "totalTranscripts": total_transcripts,
            "avgCallDuration": avg_call_duration,
            "successRate": success_rate,
            "activeAgents": active_agents
        }
        
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}")
        return jsonify({"error": "Failed to get dashboard stats", "details": str(e)}), 500

@app.route("/api/settings", methods=["GET"])
def get_settings():
    """Get system settings"""
    try:
        settings = {
            "twilio": {
                "accountSid": TWILIO_ACCOUNT_SID or "",
                "authToken": "••••••••••••••••••••••••••••••••",
                "fromNumber": os.getenv('TWILIO_FROM_NUMBER', ''),
                "toNumber": os.getenv('TWILIO_TO_NUMBER', ''),
                "ngrokUrl": os.getenv('NGROK_URL', '')
            },
            "ai": {
                "confidenceThreshold": 0.85,
                "maxResponseTime": 5000,
                "enableRecording": True,
                "enableTranscripts": True
            },
            "system": {
                "humanAgentNumber": HUMAN_AGENT_NUMBER or "",
                "maxCallDuration": 3600,
                "enableCallForwarding": True,
                "enableAnalytics": True
            },
            "security": {
                "enableHttps": True,
                "sessionTimeout": 3600,
                "maxLoginAttempts": 5,
                "enableAuditLog": True
            }
        }
        return jsonify(settings)
    except Exception as e:
        logger.error(f"Error getting settings: {e}")
        return jsonify({"error": "Failed to get settings"}), 500

@app.route("/api/settings", methods=["POST"])
def update_settings():
    """Update system settings"""
    try:
        data = request.get_json()
        # In real app, save settings to database or config file
        logger.info(f"Settings updated: {data}")
        return jsonify({"message": "Settings updated successfully"})
    except Exception as e:
        logger.error(f"Error updating settings: {e}")
        return jsonify({"error": "Failed to update settings"}), 500

@app.route("/voice", methods=["POST"])
def voice():
    try:
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
            # Persist call metadata (from/to, start_time)
            if DatabaseManager is not None:
                try:
                    from_number = request.form.get('From')
                    to_number = request.form.get('To')
                    DatabaseManager.save_call_metadata(
                        call_sid=call_sid,
                        from_number=from_number,
                        to_number=to_number,
                        call_status='in-progress',
                        start_time=datetime.utcnow()
                    )
                except Exception as db_err:
                    logger.error(f"Failed to save call metadata: {db_err}")
        
        logger.info("Started call. Asked first question.")
        return Response(str(resp), mimetype='text/xml')
    except Exception as e:
        logger.error(f"Error in voice route: {e}")
        # Return a simple error response
        resp = VoiceResponse()
        resp.say("Sorry, there was an error starting the call. Please try again.", voice='alice')
        resp.hangup()
        return Response(str(resp), mimetype='text/xml')

@app.route("/gather", methods=["POST"])
def gather():
    try:
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
                # Initialize intent and confidence variables
                intent = None
                confidence = 0.0
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
    except Exception as e:
        logger.error(f"Error in gather route: {e}")
        # Return a simple error response
        resp = VoiceResponse()
        resp.say("Sorry, there was an error processing your request. Please try again.", voice='alice')
        resp.hangup()
        return Response(str(resp), mimetype='text/xml')

@app.route("/recording-complete", methods=["POST"])
def recording_complete():
    recording_url = request.form.get("RecordingUrl")
    recording_sid = request.form.get("RecordingSid")
    call_sid = request.form.get("CallSid")
    recording_duration = request.form.get("RecordingDuration")

    # Get phone numbers from call metadata
    from_number = None
    to_number = None
    if call_sid and DatabaseManager is not None:
        try:
            call_metadata = DatabaseManager.get_call_metadata_by_sid(call_sid)
            if call_metadata:
                from_number = call_metadata.get('from_number')
                to_number = call_metadata.get('to_number')
        except Exception as e:
            logger.error(f"Failed to get call metadata: {e}")

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
                # Save to DB
                if DatabaseManager is not None:
                    try:
                        file_size = os.path.getsize(file_path)
                        DatabaseManager.save_recording(
                            recording_sid=recording_sid,
                            call_sid=call_sid or recording_sid,
                            file_path=file_path,
                            file_size=file_size,
                            duration=int(recording_duration) if (recording_duration and recording_duration.isdigit()) else None,
                            recording_url=f"/recordings/{recording_sid}.mp3",
                            status='completed',
                            from_number=from_number,
                            to_number=to_number
                        )
                    except Exception as db_err:
                        logger.error(f"Failed to save recording to database: {db_err}")
            else:
                logger.error(f"Failed to download recording. Status: {response.status_code}")
                if DatabaseManager is not None:
                    try:
                        DatabaseManager.save_recording(
                            recording_sid=recording_sid,
                            call_sid=call_sid or recording_sid,
                            recording_url=f"/recordings/{recording_sid}.mp3",
                            status='failed',
                            from_number=from_number,
                            to_number=to_number
                        )
                    except Exception as db_err:
                        logger.error(f"Failed to record DB failure status: {db_err}")
        except Exception as e:
            logger.error(f"Exception while downloading recording: {e}")
            if DatabaseManager is not None:
                try:
                    DatabaseManager.save_recording(
                        recording_sid=recording_sid,
                        call_sid=call_sid or recording_sid,
                        recording_url=f"/recordings/{recording_sid}.mp3",
                        status='failed',
                        from_number=from_number,
                        to_number=to_number
                    )
                except Exception as db_err:
                    logger.error(f"Failed to record DB exception status: {db_err}")
    else:
        logger.warning("No recording URL found.")
    return Response("Recording saved", status=200)



@app.route('/recordings/<filename>')
def serve_recording(filename):
    # Try to serve local file first
    local_path = os.path.join('recordings', filename)
    if os.path.exists(local_path):
        return send_from_directory('recordings', filename)
    # Attempt to stream from Twilio when local is missing
    try:
        recording_sid = os.path.splitext(filename)[0]
        db_row = DatabaseManager.get_recording_by_sid(recording_sid) if DatabaseManager else None
        db_url = (db_row or {}).get('recording_url') or ""
        # Always build Twilio URL for remote fetch to avoid recursion on app-relative URLs
        if db_url.startswith('http'):
            source_url = db_url
        else:
            source_url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Recordings/{recording_sid}.mp3"
        response = requests.get(
            source_url,
            auth=HTTPBasicAuth(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN),
            headers={"Accept": "audio/mpeg"},
            stream=True,
        )
        if response.status_code == 200:
            def generate():
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        yield chunk
            return Response(generate(), mimetype='audio/mpeg')
        else:
            logger.error(f"Twilio fetch failed {response.status_code} for {recording_sid}")
            return Response("Recording not found", status=404)
    except Exception as e:
        logger.error(f"Error proxying recording: {e}")
        return Response("Recording not available", status=404)

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
    app.run(debug=True, host='0.0.0.0', port=5000)
