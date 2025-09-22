import os
import json
import uuid
import time
import secrets
import smtplib
from datetime import datetime, timedelta
import logging
import requests
from collections import Counter
from flask import Flask, request, Response, session as flask_session, send_from_directory, jsonify, g
from flask_cors import CORS
from twilio.twiml.voice_response import VoiceResponse, Gather
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
from dotenv import load_dotenv
from intent_core import load_saved_assets, predict_intent, analyze_conversation_intent
# Database functionality removed - using file system storage only
# PostgreSQL Database Manager
import psycopg2
from psycopg2.extras import RealDictCursor
import json
import bcrypt
from itsdangerous import URLSafeTimedSerializer
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import email_validator

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
                    # Create users table
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS users (
                            id SERIAL PRIMARY KEY,
                            username VARCHAR(50) UNIQUE NOT NULL,
                            email VARCHAR(255) UNIQUE NOT NULL,
                            password_hash VARCHAR(255) NOT NULL,
                            is_active BOOLEAN DEFAULT TRUE,
                            is_admin BOOLEAN DEFAULT FALSE,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            last_login TIMESTAMP
                        )
                    """)
                    
                    # Create password reset tokens table
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS password_reset_tokens (
                            id SERIAL PRIMARY KEY,
                            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                            token VARCHAR(255) UNIQUE NOT NULL,
                            expires_at TIMESTAMP NOT NULL,
                            used BOOLEAN DEFAULT FALSE,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    
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

                    # Create clients table
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS clients (
                            id UUID PRIMARY KEY,
                            name VARCHAR(255),
                            phone VARCHAR(50) UNIQUE,
                            email VARCHAR(255),
                            company VARCHAR(255),
                            status VARCHAR(50) DEFAULT 'lead',
                            tags JSONB,
                            last_contact_at TIMESTAMP,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)

                    # Create client notes table
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS client_notes (
                            id UUID PRIMARY KEY,
                            client_id UUID REFERENCES clients(id) ON DELETE CASCADE,
                            body TEXT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            created_by VARCHAR(255)
                        )
                    """)
                    
                    # Create default admin user if it doesn't exist
                    self._create_default_admin()
                    
                    conn.commit()
                    logger.info("PostgreSQL database initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    def _create_default_admin(self):
        """Create default admin user if no users exist"""
        try:
            with psycopg2.connect(self.connection_string) as conn:
                with conn.cursor() as cur:
                    # Check if any users exist
                    cur.execute("SELECT COUNT(*) FROM users")
                    user_count = cur.fetchone()[0]
                    
                    if user_count == 0:
                        # Create default admin user
                        admin_username = os.getenv('ADMIN_USERNAME', 'admin')
                        admin_email = os.getenv('ADMIN_EMAIL', 'admin@voiceai.com')
                        admin_password = os.getenv('ADMIN_PASSWORD', 'admin123')
                        
                        # Hash the password
                        password_hash = bcrypt.hashpw(admin_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                        
                        cur.execute("""
                            INSERT INTO users (username, email, password_hash, is_admin, is_active)
                            VALUES (%s, %s, %s, %s, %s)
                        """, (admin_username, admin_email, password_hash, True, True))
                        
                        logger.info(f"Default admin user created: {admin_username}")
        except Exception as e:
            logger.error(f"Failed to create default admin user: {e}")
    
    def authenticate_user(self, username_or_email, password):
        """Authenticate user with username/email and password"""
        try:
            with psycopg2.connect(self.connection_string) as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT id, username, email, password_hash, is_active, is_admin
                        FROM users 
                        WHERE (username = %s OR email = %s) AND is_active = TRUE
                    """, (username_or_email, username_or_email))
                    
                    user = cur.fetchone()
                    if user and bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
                        # Update last login
                        cur.execute("""
                            UPDATE users SET last_login = CURRENT_TIMESTAMP 
                            WHERE id = %s
                        """, (user['id'],))
                        conn.commit()
                        return user
                    return None
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return None
    
    def get_user_by_id(self, user_id):
        """Get user by ID"""
        try:
            with psycopg2.connect(self.connection_string) as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT id, username, email, is_active, is_admin, created_at, last_login
                        FROM users WHERE id = %s AND is_active = TRUE
                    """, (user_id,))
                    return cur.fetchone()
        except Exception as e:
            logger.error(f"Get user error: {e}")
            return None
    
    def create_user(self, username, email, password, is_admin=False):
        """Create a new user"""
        try:
            with psycopg2.connect(self.connection_string) as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    # Check if username or email already exists
                    cur.execute("""
                        SELECT id FROM users WHERE username = %s OR email = %s
                    """, (username, email))
                    existing_user = cur.fetchone()
                    
                    if existing_user:
                        return None  # User already exists
                    
                    # Hash the password
                    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                    
                    # Insert new user
                    cur.execute("""
                        INSERT INTO users (username, email, password_hash, is_admin, is_active)
                        VALUES (%s, %s, %s, %s, %s)
                        RETURNING id, username, email, is_admin, created_at
                    """, (username, email, password_hash, is_admin, True))
                    
                    user = cur.fetchone()
                    conn.commit()
                    
                    logger.info(f"New user created: {username} (admin: {is_admin})")
                    return user
        except Exception as e:
            logger.error(f"Create user error: {e}")
            return None
    
    def create_password_reset_token(self, email):
        """Create password reset token for user"""
        try:
            with psycopg2.connect(self.connection_string) as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    # Get user by email
                    cur.execute("SELECT id FROM users WHERE email = %s AND is_active = TRUE", (email,))
                    user = cur.fetchone()
                    
                    if not user:
                        return None
                    
                    # Generate secure token
                    token = secrets.token_urlsafe(32)
                    expires_at = datetime.utcnow() + timedelta(hours=1)
                    
                    # Invalidate any existing tokens for this user
                    cur.execute("""
                        UPDATE password_reset_tokens 
                        SET used = TRUE 
                        WHERE user_id = %s AND used = FALSE
                    """, (user['id'],))
                    
                    # Create new token
                    cur.execute("""
                        INSERT INTO password_reset_tokens (user_id, token, expires_at)
                        VALUES (%s, %s, %s)
                    """, (user['id'], token, expires_at))
                    
                    conn.commit()
                    return token
        except Exception as e:
            logger.error(f"Create reset token error: {e}")
            return None
    
    def validate_reset_token(self, token):
        """Validate password reset token"""
        try:
            with psycopg2.connect(self.connection_string) as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT prt.user_id, u.username, u.email
                        FROM password_reset_tokens prt
                        JOIN users u ON prt.user_id = u.id
                        WHERE prt.token = %s 
                        AND prt.expires_at > CURRENT_TIMESTAMP 
                        AND prt.used = FALSE
                        AND u.is_active = TRUE
                    """, (token,))
                    return cur.fetchone()
        except Exception as e:
            logger.error(f"Validate reset token error: {e}")
            return None
    
    def reset_password(self, token, new_password):
        """Reset user password using token"""
        try:
            with psycopg2.connect(self.connection_string) as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    # Validate token
                    user_data = self.validate_reset_token(token)
                    if not user_data:
                        return False
                    
                    # Hash new password
                    password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                    
                    # Update password
                    cur.execute("""
                        UPDATE users 
                        SET password_hash = %s, updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                    """, (password_hash, user_data['user_id']))
                    
                    # Mark token as used
                    cur.execute("""
                        UPDATE password_reset_tokens 
                        SET used = TRUE 
                        WHERE token = %s
                    """, (token,))
                    
                    conn.commit()
                    return True
        except Exception as e:
            logger.error(f"Reset password error: {e}")
            return False
    
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

    # ===== Clients helpers =====
    def list_clients(self, search: str | None, status: str | None, limit: int, offset: int):
        try:
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    where = []
                    params = []
                    if search:
                        where.append("(LOWER(name) LIKE %s OR LOWER(phone) LIKE %s OR LOWER(email) LIKE %s OR LOWER(company) LIKE %s)")
                        like = f"%{search.lower()}%"
                        params.extend([like, like, like, like])
                    if status and status.lower() != 'all':
                        where.append("LOWER(status) = %s")
                        params.append(status.lower())
                    where_clause = (" WHERE " + " AND ".join(where)) if where else ""

                    # Compute last_contact and total_calls via transcripts
                    sql = f"""
                        SELECT c.id, c.name, c.phone, c.email, c.company, c.status, c.tags,
                               c.created_at, c.updated_at,
                               GREATEST(
                                   COALESCE(c.last_contact_at, to_timestamp(0)),
                                   COALESCE((SELECT MAX(t.created_at) FROM transcripts t WHERE t.from_number = c.phone OR t.to_number = c.phone), to_timestamp(0))
                               ) AS last_contact_at,
                               COALESCE((SELECT COUNT(1) FROM transcripts t WHERE t.from_number = c.phone OR t.to_number = c.phone), 0) AS total_calls
                        FROM clients c
                        {where_clause}
                        ORDER BY last_contact_at DESC NULLS LAST, created_at DESC
                        LIMIT %s OFFSET %s
                    """
                    params.extend([limit, offset])
                    cur.execute(sql, params)
                    rows = cur.fetchall()
                    return [dict(r) for r in rows]
        except Exception as e:
            logger.error(f"Failed to list clients: {e}")
            return []

    def get_client(self, client_id: str):
        try:
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("SELECT * FROM clients WHERE id = %s", (client_id,))
                    row = cur.fetchone()
                    return dict(row) if row else None
        except Exception as e:
            logger.error(f"Failed to get client: {e}")
            return None

    def get_client_by_phone(self, phone: str):
        try:
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("SELECT * FROM clients WHERE phone = %s", (phone,))
                    row = cur.fetchone()
                    return dict(row) if row else None
        except Exception as e:
            logger.error(f"Failed to get client by phone: {e}")
            return None
    
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

# Email service for password reset
class EmailService:
    def __init__(self):
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_username = os.getenv('SMTP_USERNAME', '')
        self.smtp_password = os.getenv('SMTP_PASSWORD', '')
        self.from_email = os.getenv('FROM_EMAIL', 'noreply@voiceai.com')
        self.app_url = os.getenv('APP_URL', 'http://localhost:3000')
    
    def send_password_reset_email(self, email, username, reset_token):
        """Send password reset email"""
        try:
            if not self.smtp_username or not self.smtp_password:
                logger.warning("SMTP credentials not configured, skipping email send")
                return True
            
            reset_url = f"{self.app_url}/reset-password/{reset_token}"
            
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = email
            msg['Subject'] = "VoiceAI - Password Reset Request"
            
            html_body = f"""
            <html>
                <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <div style="background-color: #3B82F6; color: white; padding: 20px; text-align: center;">
                        <h1>VoiceAI</h1>
                    </div>
                    <div style="padding: 30px;">
                        <h2>Password Reset Request</h2>
                        <p>Hello {username},</p>
                        <p>You have requested to reset your password for your VoiceAI account.</p>
                        <p>Click the button below to reset your password:</p>
                        <div style="text-align: center; margin: 30px 0;">
                            <a href="{reset_url}" 
                               style="background-color: #3B82F6; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
                                Reset Password
                            </a>
                        </div>
                        <p>If the button doesn't work, copy and paste this link into your browser:</p>
                        <p style="word-break: break-all; color: #666;">{reset_url}</p>
                        <p><strong>This link will expire in 1 hour for security reasons.</strong></p>
                        <p>If you didn't request this password reset, please ignore this email.</p>
                        <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
                        <p style="color: #666; font-size: 12px;">
                            This email was sent from VoiceAI. If you have any questions, please contact support.
                        </p>
                    </div>
                </body>
            </html>
            """
            
            msg.attach(MIMEText(html_body, 'html'))
            
            # Try different SMTP configurations
            try:
                # First try with STARTTLS (Gmail, Outlook)
                with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                    server.starttls()
                    server.login(self.smtp_username, self.smtp_password)
                    server.send_message(msg)
            except smtplib.SMTPNotSupportedError:
                # If STARTTLS not supported, try SSL (some servers)
                try:
                    with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as server:
                        server.login(self.smtp_username, self.smtp_password)
                        server.send_message(msg)
                except Exception as ssl_error:
                    logger.error(f"SSL connection failed: {ssl_error}")
                    # Try without encryption (not recommended but for testing)
                    try:
                        with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                            server.login(self.smtp_username, self.smtp_password)
                            server.send_message(msg)
                    except Exception as no_ssl_error:
                        logger.error(f"No SSL connection failed: {no_ssl_error}")
                        raise no_ssl_error
            
            logger.info(f"Password reset email sent to {email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send password reset email: {e}")
            return False

# Initialize database manager
try:
    email_service = EmailService()
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
    CORS(app, supports_credentials=True, resources={
        r"/api/*": {"origins": ["http://localhost:3000", "http://127.0.0.1:3000", "http://192.168.10.137:3000", "http://localhost:4000", "http://127.0.0.1:4000", "http://192.168.10.137:4000"]},
        r"/recordings/*": {"origins": ["http://localhost:3000", "http://127.0.0.1:3000", "http://192.168.10.137:3000", "http://localhost:4000", "http://127.0.0.1:4000", "http://192.168.10.137:4000"]},
        r"/transcripts/*": {"origins": ["http://localhost:3000", "http://127.0.0.1:3000", "http://192.168.10.137:3000", "http://localhost:4000", "http://127.0.0.1:4000", "http://192.168.10.137:4000"]},
    })
except Exception:
    pass
app.secret_key = SECRET_KEY
app.config['SESSION_COOKIE_HTTPONLY'] = True
# In local dev over HTTP, secure cookies break auth. Allow override via env.
app.config['SESSION_COOKIE_SECURE'] = os.getenv('SESSION_COOKIE_SECURE', 'false').lower() in ['1','true','yes']
app.config['SESSION_COOKIE_SAMESITE'] = os.getenv('SESSION_COOKIE_SAMESITE', 'Lax')
# Allow session cookies to work across different ports in development
app.config['SESSION_COOKIE_DOMAIN'] = None

# ===== Simple Admin Auth (session-based) =====
# Authentication helper functions
def is_authenticated() -> bool:
    try:
        return flask_session.get('user_id') is not None
    except:
        return False

def get_current_user():
    """Get current authenticated user"""
    try:
        user_id = flask_session.get('user_id')
        if user_id:
            return DatabaseManager.get_user_by_id(user_id)
        return None
    except:
        return None

@app.before_request
def protect_admin_api():
    # Allow non-API routes and auth endpoints
    path = request.path or ''
    if not path.startswith('/api/'):
        return None
    # Public API endpoints
    if path.startswith('/api/auth/'):
        return None
    # Preflight
    if request.method == 'OPTIONS':
        return None
    # Enforce session for admin dashboard APIs
    if not is_authenticated():
        return jsonify({"error": "Unauthorized"}), 401
    return None

@app.route('/api/auth/login', methods=['POST'])
def api_auth_login():
    try:
        data = request.get_json(force=True) or {}
        username_or_email = (data.get('username') or '').strip()
        password = data.get('password') or ''
        
        if not username_or_email or not password:
            return jsonify({"error": "Username/email and password are required"}), 400
        
        # Authenticate user against database
        user = DatabaseManager.authenticate_user(username_or_email, password)
        
        if user:
            # Store user info in session
            flask_session['user_id'] = user['id']
            flask_session['username'] = user['username']
            flask_session['is_admin'] = user['is_admin']
            flask_session.permanent = True
            app.permanent_session_lifetime = timedelta(seconds=int(os.getenv('SESSION_TIMEOUT', '3600')))
            
            logger.info(f"User {user['username']} logged in successfully")
            return jsonify({
                "ok": True, 
                "user": {
                    "id": user['id'],
                    "username": user['username'],
                    "email": user['email'],
                    "is_admin": user['is_admin']
                }
            })
        
        return jsonify({"error": "Invalid credentials"}), 401
        
    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({"error": "Login failed"}), 500

@app.route('/api/auth/register', methods=['POST'])
def api_auth_register():
    try:
        data = request.get_json(force=True) or {}
        username = (data.get('username') or '').strip()
        email = (data.get('email') or '').strip().lower()
        password = data.get('password') or ''
        
        if not username or not email or not password:
            return jsonify({"error": "Username, email, and password are required"}), 400
        
        if len(password) < 6:
            return jsonify({"error": "Password must be at least 6 characters long"}), 400
        
        # Validate email format
        try:
            email_validator.validate_email(email)
        except email_validator.EmailNotValidError:
            return jsonify({"error": "Invalid email format"}), 400
        
        # Create user (client by default)
        user = DatabaseManager.create_user(username, email, password, is_admin=False)
        
        if user:
            logger.info(f"New client user registered: {username}")
            return jsonify({
                "ok": True,
                "message": "User registered successfully",
                "user": {
                    "id": user['id'],
                    "username": user['username'],
                    "email": user['email'],
                    "is_admin": user['is_admin']
                }
            }), 201
        
        return jsonify({"error": "Username or email already exists"}), 409
        
    except Exception as e:
        logger.error(f"Registration error: {e}")
        return jsonify({"error": "Registration failed"}), 500

@app.route('/api/auth/logout', methods=['POST'])
def api_auth_logout():
    try:
        username = flask_session.get('username', 'Unknown')
        flask_session.clear()
        logger.info(f"User {username} logged out")
        return jsonify({"ok": True})
    except Exception as e:
        logger.error(f"Logout error: {e}")
        return jsonify({"ok": True})

@app.route('/api/auth/me', methods=['GET'])
def api_auth_me():
    try:
        if is_authenticated():
            user = get_current_user()
            if user:
                return jsonify({
                    "authenticated": True, 
                    "user": {
                        "id": user['id'],
                        "username": user['username'],
                        "email": user['email'],
                        "is_admin": user['is_admin']
                    }
                })
        
        return jsonify({"authenticated": False}), 401
    except Exception as e:
        logger.error(f"Auth check error: {e}")
        return jsonify({"authenticated": False}), 401

@app.route('/api/auth/forgot-password', methods=['POST'])
def api_forgot_password():
    try:
        data = request.get_json(force=True) or {}
        email = (data.get('email') or '').strip().lower()
        
        if not email:
            return jsonify({"error": "Email is required"}), 400
        
        # Validate email format
        try:
            email_validator.validate_email(email)
        except email_validator.EmailNotValidError:
            return jsonify({"error": "Invalid email format"}), 400
        
        # Create reset token
        reset_token = DatabaseManager.create_password_reset_token(email)
        
        if reset_token:
            # Get user info for email
            with DatabaseManager._get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("SELECT username FROM users WHERE email = %s", (email,))
                    user = cur.fetchone()
            
            if user:
                # Send email (will return True even if email fails to avoid revealing user existence)
                email_service.send_password_reset_email(email, user['username'], reset_token)
        
        # Always return success to prevent email enumeration
        return jsonify({
            "ok": True, 
            "message": "If the email exists, password reset instructions have been sent"
        })
        
    except Exception as e:
        logger.error(f"Forgot password error: {e}")
        return jsonify({"error": "Failed to process request"}), 500

# Client-specific API endpoints
@app.route('/api/client/dashboard', methods=['GET'])
def api_client_dashboard():
    """Get client dashboard statistics"""
    try:
        if not is_authenticated():
            return jsonify({"error": "Unauthorized"}), 401
        
        user = get_current_user()
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        # Get client-specific statistics
        stats = {
            "totalCalls": 0,
            "totalRecordings": 0,
            "totalTranscripts": 0,
            "successRate": 0,
            "avgCallDuration": 0,
            "recentCalls": []
        }
        
        if DatabaseManager:
            try:
                with DatabaseManager._get_connection() as conn:
                    with conn.cursor(cursor_factory=RealDictCursor) as cur:
                        # Get total calls for this user
                        cur.execute("""
                            SELECT COUNT(*) as total_calls FROM transcripts 
                            WHERE user_id = %s
                        """, (user['id'],))
                        result = cur.fetchone()
                        stats["totalCalls"] = result['total_calls'] if result else 0
                        
                        # Get total recordings
                        cur.execute("""
                            SELECT COUNT(*) as total_recordings FROM transcripts 
                            WHERE user_id = %s AND recording_url IS NOT NULL
                        """, (user['id'],))
                        result = cur.fetchone()
                        stats["totalRecordings"] = result['total_recordings'] if result else 0
                        
                        # Get total transcripts
                        stats["totalTranscripts"] = stats["totalCalls"]  # Same as calls for now
                        
                        # Get success rate (calls with successful completion)
                        cur.execute("""
                            SELECT COUNT(*) as successful_calls FROM transcripts 
                            WHERE user_id = %s AND status = 'completed'
                        """, (user['id'],))
                        result = cur.fetchone()
                        successful_calls = result['successful_calls'] if result else 0
                        
                        if stats["totalCalls"] > 0:
                            stats["successRate"] = round((successful_calls / stats["totalCalls"]) * 100, 1)
                        
                        # Get average call duration
                        cur.execute("""
                            SELECT AVG(EXTRACT(EPOCH FROM (end_time - start_time))/60) as avg_duration 
                            FROM transcripts 
                            WHERE user_id = %s AND start_time IS NOT NULL AND end_time IS NOT NULL
                        """, (user['id'],))
                        result = cur.fetchone()
                        stats["avgCallDuration"] = round(result['avg_duration'], 1) if result and result['avg_duration'] else 0
                        
                        # Get recent calls
                        cur.execute("""
                            SELECT call_sid, phone_number, start_time, end_time, status, intent, confidence
                            FROM transcripts 
                            WHERE user_id = %s 
                            ORDER BY start_time DESC 
                            LIMIT 5
                        """, (user['id'],))
                        recent_calls = cur.fetchall()
                        
                        stats["recentCalls"] = []
                        for call in recent_calls:
                            duration = "0:00"
                            if call['start_time'] and call['end_time']:
                                duration_seconds = int((call['end_time'] - call['start_time']).total_seconds())
                                minutes = duration_seconds // 60
                                seconds = duration_seconds % 60
                                duration = f"{minutes}:{seconds:02d}"
                            
                            stats["recentCalls"].append({
                                "id": call['call_sid'],
                                "phoneNumber": call['phone_number'] or "Unknown",
                                "duration": duration,
                                "status": call['status'] or "unknown",
                                "timestamp": call['start_time'].strftime('%Y-%m-%d %H:%M') if call['start_time'] else "Unknown",
                                "intent": call['intent'] or "Unknown",
                                "confidence": call['confidence'] or 0
                            })
                        
            except Exception as e:
                logger.error(f"Database error in client dashboard: {e}")
                # Return basic stats if database error
                pass
        
        return jsonify({"ok": True, "stats": stats})
        
    except Exception as e:
        logger.error(f"Client dashboard error: {e}")
        return jsonify({"error": "Failed to fetch dashboard data"}), 500

@app.route('/api/client/calls', methods=['GET'])
def api_client_calls():
    """Get client call history"""
    try:
        if not is_authenticated():
            return jsonify({"error": "Unauthorized"}), 401
        
        user = get_current_user()
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        # Get query parameters
        search = request.args.get('search', '')
        status_filter = request.args.get('status', 'all')
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('pageSize', 25, type=int)
        
        calls = []
        
        if DatabaseManager:
            try:
                with DatabaseManager._get_connection() as conn:
                    with conn.cursor(cursor_factory=RealDictCursor) as cur:
                        # Build query
                        query = """
                            SELECT call_sid, phone_number, start_time, end_time, status, intent, confidence
                            FROM transcripts 
                            WHERE user_id = %s
                        """
                        params = [user['id']]
                        
                        # Add search filter
                        if search:
                            query += " AND (phone_number ILIKE %s OR intent ILIKE %s)"
                            search_param = f"%{search}%"
                            params.extend([search_param, search_param])
                        
                        # Add status filter
                        if status_filter != 'all':
                            query += " AND status = %s"
                            params.append(status_filter)
                        
                        query += " ORDER BY start_time DESC"
                        
                        # Add pagination
                        offset = (page - 1) * page_size
                        query += " LIMIT %s OFFSET %s"
                        params.extend([page_size, offset])
                        
                        cur.execute(query, params)
                        results = cur.fetchall()
                        
                        for call in results:
                            duration = "0:00"
                            if call['start_time'] and call['end_time']:
                                duration_seconds = int((call['end_time'] - call['start_time']).total_seconds())
                                minutes = duration_seconds // 60
                                seconds = duration_seconds % 60
                                duration = f"{minutes}:{seconds:02d}"
                            
                            calls.append({
                                "id": call['call_sid'],
                                "phoneNumber": call['phone_number'] or "Unknown",
                                "duration": duration,
                                "status": call['status'] or "unknown",
                                "timestamp": call['start_time'].strftime('%Y-%m-%d %H:%M:%S') if call['start_time'] else "Unknown",
                                "intent": call['intent'] or "Unknown",
                                "confidence": call['confidence'] or 0
                            })
                        
            except Exception as e:
                logger.error(f"Database error in client calls: {e}")
        
        return jsonify({"ok": True, "calls": calls})
        
    except Exception as e:
        logger.error(f"Client calls error: {e}")
        return jsonify({"error": "Failed to fetch calls"}), 500

@app.route('/api/client/recordings', methods=['GET'])
def api_client_recordings():
    """Get client recordings"""
    try:
        if not is_authenticated():
            return jsonify({"error": "Unauthorized"}), 401
        
        user = get_current_user()
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        # Get query parameters
        search = request.args.get('search', '')
        
        recordings = []
        
        if DatabaseManager:
            try:
                with DatabaseManager._get_connection() as conn:
                    with conn.cursor(cursor_factory=RealDictCursor) as cur:
                        # Build query
                        query = """
                            SELECT call_sid, phone_number, start_time, end_time, status, intent, recording_url
                            FROM transcripts 
                            WHERE user_id = %s AND recording_url IS NOT NULL
                        """
                        params = [user['id']]
                        
                        # Add search filter
                        if search:
                            query += " AND (phone_number ILIKE %s OR intent ILIKE %s OR call_sid ILIKE %s)"
                            search_param = f"%{search}%"
                            params.extend([search_param, search_param, search_param])
                        
                        query += " ORDER BY start_time DESC"
                        
                        cur.execute(query, params)
                        results = cur.fetchall()
                        
                        for recording in results:
                            duration = "0:00"
                            if recording['start_time'] and recording['end_time']:
                                duration_seconds = int((recording['end_time'] - recording['start_time']).total_seconds())
                                minutes = duration_seconds // 60
                                seconds = duration_seconds % 60
                                duration = f"{minutes}:{seconds:02d}"
                            
                            # Calculate file size (mock for now)
                            file_size = "1.2 MB"  # In real implementation, get actual file size
                            
                            recordings.append({
                                "id": recording['call_sid'],
                                "callId": recording['call_sid'],
                                "phoneNumber": recording['phone_number'] or "Unknown",
                                "duration": duration,
                                "timestamp": recording['start_time'].strftime('%Y-%m-%d %H:%M:%S') if recording['start_time'] else "Unknown",
                                "intent": recording['intent'] or "Unknown",
                                "fileSize": file_size,
                                "url": recording['recording_url']
                            })
                        
            except Exception as e:
                logger.error(f"Database error in client recordings: {e}")
        
        return jsonify({"ok": True, "recordings": recordings})
        
    except Exception as e:
        logger.error(f"Client recordings error: {e}")
        return jsonify({"error": "Failed to fetch recordings"}), 500

@app.route('/api/client/transcripts', methods=['GET'])
def api_client_transcripts():
    """Get client transcripts"""
    try:
        if not is_authenticated():
            return jsonify({"error": "Unauthorized"}), 401
        
        user = get_current_user()
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        # Get query parameters
        search = request.args.get('search', '')
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('pageSize', 25, type=int)
        
        transcripts = []
        
        if DatabaseManager:
            try:
                with DatabaseManager._get_connection() as conn:
                    with conn.cursor(cursor_factory=RealDictCursor) as cur:
                        # Build query
                        query = """
                            SELECT call_sid, phone_number, start_time, end_time, status, intent, confidence, transcript_text
                            FROM transcripts 
                            WHERE user_id = %s
                        """
                        params = [user['id']]
                        
                        # Add search filter
                        if search:
                            query += " AND (phone_number ILIKE %s OR intent ILIKE %s OR transcript_text ILIKE %s)"
                            search_param = f"%{search}%"
                            params.extend([search_param, search_param, search_param])
                        
                        query += " ORDER BY start_time DESC"
                        
                        # Add pagination
                        offset = (page - 1) * page_size
                        query += " LIMIT %s OFFSET %s"
                        params.extend([page_size, offset])
                        
                        cur.execute(query, params)
                        results = cur.fetchall()
                        
                        for transcript in results:
                            duration = "0:00"
                            if transcript['start_time'] and transcript['end_time']:
                                duration_seconds = int((transcript['end_time'] - transcript['start_time']).total_seconds())
                                minutes = duration_seconds // 60
                                seconds = duration_seconds % 60
                                duration = f"{minutes}:{seconds:02d}"
                            
                            transcripts.append({
                                "id": transcript['call_sid'],
                                "callId": transcript['call_sid'],
                                "phoneNumber": transcript['phone_number'] or "Unknown",
                                "duration": duration,
                                "timestamp": transcript['start_time'].strftime('%Y-%m-%d %H:%M:%S') if transcript['start_time'] else "Unknown",
                                "intent": transcript['intent'] or "Unknown",
                                "confidence": transcript['confidence'] or 0,
                                "transcript": transcript['transcript_text'] or "No transcript available"
                            })
                        
            except Exception as e:
                logger.error(f"Database error in client transcripts: {e}")
        
        return jsonify({"ok": True, "transcripts": transcripts})
        
    except Exception as e:
        logger.error(f"Client transcripts error: {e}")
        return jsonify({"error": "Failed to fetch transcripts"}), 500

@app.route('/api/auth/reset-password', methods=['POST'])
def api_reset_password():
    try:
        data = request.get_json(force=True) or {}
        token = (data.get('token') or '').strip()
        new_password = data.get('password') or ''
        
        if not token or not new_password:
            return jsonify({"error": "Token and new password are required"}), 400
        
        if len(new_password) < 6:
            return jsonify({"error": "Password must be at least 6 characters long"}), 400
        
        # Reset password using token
        success = DatabaseManager.reset_password(token, new_password)
        
        if success:
            logger.info("Password reset successfully")
            return jsonify({"ok": True, "message": "Password reset successfully"})
        
        return jsonify({"error": "Invalid or expired reset token"}), 400
        
    except Exception as e:
        logger.error(f"Reset password error: {e}")
        return jsonify({"error": "Failed to reset password"}), 500

# Debug endpoint to get reset tokens (REMOVE IN PRODUCTION!)
@app.route('/api/debug/reset-tokens', methods=['GET'])
def api_debug_reset_tokens():
    """Debug endpoint to get recent reset tokens (ADMIN ONLY)"""
    try:
        if not is_authenticated():
            return jsonify({"error": "Authentication required"}), 401
        
        current_user = get_current_user()
        if not current_user or not current_user.get('is_admin'):
            return jsonify({"error": "Admin privileges required"}), 403
        
        with DatabaseManager._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT prt.token, prt.expires_at, prt.used, prt.created_at, u.username, u.email
                    FROM password_reset_tokens prt
                    JOIN users u ON prt.user_id = u.id
                    ORDER BY prt.created_at DESC
                    LIMIT 5
                """)
                tokens = cur.fetchall()
                
                tokens_list = []
                for token in tokens:
                    token_dict = dict(token)
                    token_dict['expires_at'] = token['expires_at'].isoformat() if token['expires_at'] else None
                    token_dict['created_at'] = token['created_at'].isoformat() if token['created_at'] else None
                    tokens_list.append(token_dict)
                
                return jsonify({
                    "ok": True,
                    "tokens": tokens_list
                })
        
    except Exception as e:
        logger.error(f"Debug tokens error: {e}")
        return jsonify({"error": "Failed to get tokens"}), 500

@app.route('/api/auth/profile', methods=['GET'])
def api_get_profile():
    """Get current user profile"""
    try:
        if not is_authenticated():
            return jsonify({"error": "Authentication required"}), 401
        
        user = get_current_user()
        if user:
            return jsonify({
                "ok": True,
                "user": {
                    "id": user['id'],
                    "username": user['username'],
                    "email": user['email'],
                    "is_admin": user['is_admin'],
                    "created_at": user['created_at'].isoformat() if user['created_at'] else None,
                    "last_login": user['last_login'].isoformat() if user['last_login'] else None
                }
            })
        
        return jsonify({"error": "User not found"}), 404
        
    except Exception as e:
        logger.error(f"Get profile error: {e}")
        return jsonify({"error": "Failed to get profile"}), 500

@app.route('/api/auth/profile', methods=['PUT'])
def api_update_profile():
    """Update user profile"""
    try:
        if not is_authenticated():
            return jsonify({"error": "Authentication required"}), 401
        
        current_user = get_current_user()
        if not current_user:
            return jsonify({"error": "User not found"}), 404
        
        data = request.get_json(force=True) or {}
        username = (data.get('username') or '').strip()
        email = (data.get('email') or '').strip().lower()
        
        if not username or not email:
            return jsonify({"error": "Username and email are required"}), 400
        
        # Validate email format
        try:
            email_validator.validate_email(email)
        except email_validator.EmailNotValidError:
            return jsonify({"error": "Invalid email format"}), 400
        
        # Check if email is already taken by another user
        with DatabaseManager._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT id FROM users 
                    WHERE email = %s AND id != %s AND is_active = TRUE
                """, (email, current_user['id']))
                
                if cur.fetchone():
                    return jsonify({"error": "Email is already taken"}), 400
                
                # Check if username is already taken by another user
                cur.execute("""
                    SELECT id FROM users 
                    WHERE username = %s AND id != %s AND is_active = TRUE
                """, (username, current_user['id']))
                
                if cur.fetchone():
                    return jsonify({"error": "Username is already taken"}), 400
                
                # Update user profile
                cur.execute("""
                    UPDATE users 
                    SET username = %s, email = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (username, email, current_user['id']))
                
                conn.commit()
                
                logger.info(f"User {current_user['username']} updated their profile")
                return jsonify({
                    "ok": True,
                    "message": "Profile updated successfully"
                })
        
    except Exception as e:
        logger.error(f"Update profile error: {e}")
        return jsonify({"error": "Failed to update profile"}), 500

@app.route('/api/auth/change-password', methods=['PUT'])
def api_change_password():
    """Change user password"""
    try:
        if not is_authenticated():
            return jsonify({"error": "Authentication required"}), 401
        
        current_user = get_current_user()
        if not current_user:
            return jsonify({"error": "User not found"}), 404
        
        data = request.get_json(force=True) or {}
        current_password = data.get('currentPassword') or ''
        new_password = data.get('newPassword') or ''
        
        if not current_password or not new_password:
            return jsonify({"error": "Current password and new password are required"}), 400
        
        if len(new_password) < 6:
            return jsonify({"error": "New password must be at least 6 characters long"}), 400
        
        # Verify current password
        with DatabaseManager._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT password_hash FROM users WHERE id = %s
                """, (current_user['id'],))
                
                user_data = cur.fetchone()
                if not user_data:
                    return jsonify({"error": "User not found"}), 404
                
                # Check current password
                if not bcrypt.checkpw(current_password.encode('utf-8'), user_data['password_hash'].encode('utf-8')):
                    return jsonify({"error": "Current password is incorrect"}), 400
                
                # Hash new password
                password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                
                # Update password
                cur.execute("""
                    UPDATE users 
                    SET password_hash = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (password_hash, current_user['id']))
                
                conn.commit()
                
                logger.info(f"User {current_user['username']} changed their password")
                return jsonify({
                    "ok": True,
                    "message": "Password changed successfully"
                })
        
    except Exception as e:
        logger.error(f"Change password error: {e}")
        return jsonify({"error": "Failed to change password"}), 500

# Conversation logging
conversation_logs = {}
whatsapp_handoffs = {}
whatsapp_session_call_sid = {}
whatsapp_session_state = {}

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

def format_wa(number: str) -> str:
    try:
        n = number or ""
        return n if n.startswith("whatsapp:") else f"whatsapp:{n}"
    except Exception:
        return number

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

# ========= WhatsApp Integration =========

@app.route("/whatsapp/incoming", methods=["POST"])
def whatsapp_incoming():
    try:
        from_number = request.values.get("From") or ""
        to_number = request.values.get("To") or ""
        body = (request.values.get("Body") or "").strip()
        wa_from = from_number.replace("whatsapp:", "")

        resp = MessagingResponse()

        # Log incoming WhatsApp message to terminal
        try:
            logger.info(f"WA INCOMING from {wa_from} -> '{body}'")
        except Exception:
            pass

        if not body:
            resp.message("I didn't receive any text. Please type your message.")
            return Response(str(resp), mimetype='text/xml')

        # Detect customer service escalations first
        if check_customer_service_request(body):
            # Store handoff flag for this user so future messages are just relayed
            whatsapp_handoffs[wa_from] = True
            human_number = os.getenv('WHATSAPP_HUMAN_AGENT') or HUMAN_AGENT_NUMBER or ''
            if human_number:
                # Notify user and agent
                resp.message("I will connect you with a human agent here. Please wait.")
                try:
                    client = get_twilio_client()
                    client.messages.create(
                        to=format_wa(human_number),
                        from_=to_number if to_number.startswith('whatsapp:') else format_wa(os.getenv('TWILIO_WHATSAPP_FROM', '')),
                        body=f"New WhatsApp support request from {wa_from}: '{body}'"
                    )
                except Exception as send_err:
                    logger.error(f"Failed to notify human agent on WhatsApp: {send_err}")
            else:
                resp.message("No human agent configured. Please try again later.")
            return Response(str(resp), mimetype='text/xml')

        # If user is already in handoff mode, relay their messages to the agent
        if whatsapp_handoffs.get(wa_from):
            human_number = os.getenv('WHATSAPP_HUMAN_AGENT') or HUMAN_AGENT_NUMBER or ''
            if human_number:
                try:
                    client = get_twilio_client()
                    client.messages.create(
                        to=format_wa(human_number),
                        from_=to_number if to_number.startswith('whatsapp:') else format_wa(os.getenv('TWILIO_WHATSAPP_FROM', '')),
                        body=f"User {wa_from}: {body}"
                    )
                    resp.message("Message sent to human agent.")
                except Exception as relay_err:
                    logger.error(f"Failed to relay message to agent: {relay_err}")
                    resp.message("Failed to send to agent. Please try again.")
            else:
                resp.message("No human agent configured.")
            return Response(str(resp), mimetype='text/xml')

        # Initialize session state if needed
        state = whatsapp_session_state.get(wa_from) or {}

        # End conditions
        if any(w in body.lower() for w in ["goodbye", "exit", "quit"]):
            reply = "Thank you for your responses. Goodbye!"
            # Persist and clear session
            call_sid = state.get('call_sid') or whatsapp_session_call_sid.get(wa_from)
            if call_sid:
                add_conversation_log(call_sid, "SYSTEM: Thank you for your responses. Goodbye!")
                try:
                    save_conversation_log(call_sid)
                except Exception:
                    pass
            whatsapp_session_state.pop(wa_from, None)
            whatsapp_session_call_sid.pop(wa_from, None)
            resp.message(reply)
            return Response(str(resp), mimetype='text/xml')

        # Run intent detection and craft reply similar to voice flow
        try:
            result = predict_intent(body)
            intent = result.get("intent")
            confidence = float(result.get("confidence") or 0)
            # Log predicted intent to terminal
            try:
                logger.info(f"WA INTENT for {wa_from}: {intent} (confidence={confidence:.2f})")
            except Exception:
                pass
            if intent and confidence > 0.8:
                reply = intent
                state['last_prompt'] = intent
            else:
                last_prompt = state.get('last_prompt') or questions[0]
                reply = f"I could not understand. Please try again.\n\n{last_prompt}"
        except Exception as e:
            logger.error(f"WhatsApp intent error: {e}")
            reply = "Sorry, there was an error processing your message."

        # Persist lightweight transcript-like log per WhatsApp user
        call_sid = (state.get('call_sid')
                    or whatsapp_session_call_sid.get(wa_from))
        if not call_sid:
            call_sid = f"WA{uuid.uuid4().hex[:24]}"
            whatsapp_session_call_sid[wa_from] = call_sid
            state['call_sid'] = call_sid
            add_conversation_log(call_sid, f"SYSTEM: WhatsApp session started with {wa_from}")
        add_conversation_log(call_sid, f"USER: {body}")
        add_conversation_log(call_sid, f"SYSTEM: {reply}")
        # Save periodically to file/db
        if len(conversation_logs.get(call_sid, [])) % 6 == 0:
            try:
                save_conversation_log(call_sid)
            except Exception:
                pass
        whatsapp_session_state[wa_from] = state

        resp.message(reply)
        return Response(str(resp), mimetype='text/xml')
    except Exception as e:
        logger.error(f"Error in WhatsApp incoming route: {e}")
        resp = MessagingResponse()
        resp.message("An error occurred. Please try again later.")
        return Response(str(resp), mimetype='text/xml')


@app.route("/api/whatsapp/send", methods=["POST"])
def api_whatsapp_send():
    try:
        data = request.get_json(force=True) or {}
        to_number = data.get('to') or ''
        body = data.get('body') or ''
        from_number = os.getenv('TWILIO_WHATSAPP_FROM', '')
        if not to_number or not body or not from_number:
            return jsonify({"error": "to, body, and TWILIO_WHATSAPP_FROM are required"}), 400
        client = get_twilio_client()
        msg = client.messages.create(
            to=format_wa(to_number),
            from_=format_wa(from_number),
            body=body
        )
        return jsonify({"sid": msg.sid, "status": msg.status})
    except Exception as e:
        logger.error(f"Failed to send WhatsApp message: {e}")
        return jsonify({"error": "Failed to send message", "details": str(e)}), 500


@app.route("/api/whatsapp/start", methods=["POST"])
def api_whatsapp_start():
    """Start a WhatsApp conversation with the same first question used for calls."""
    try:
        data = request.get_json(force=True) or {}
        to_number = data.get('to') or ''
        first_question = questions[0]
        from_number = os.getenv('TWILIO_WHATSAPP_FROM', '')
        if not to_number or not from_number:
            return jsonify({"error": "to and TWILIO_WHATSAPP_FROM are required"}), 400

        client = get_twilio_client()
        wa_to = to_number
        msg = client.messages.create(
            to=format_wa(wa_to),
            from_=format_wa(from_number),
            body=first_question
        )

        # Initialize session state for recipient
        wa_key = to_number
        state = {
            'call_sid': f"WA{uuid.uuid4().hex[:24]}",
            'last_prompt': first_question,
            'first_question_repeated': False
        }
        whatsapp_session_call_sid[wa_key] = state['call_sid']
        whatsapp_session_state[wa_key] = state
        add_conversation_log(state['call_sid'], f"SYSTEM: Initial greeting and first question: '{first_question}'")

        return jsonify({"sid": msg.sid, "status": msg.status, "call_sid": state['call_sid']})
    except Exception as e:
        logger.error(f"Failed to start WhatsApp conversation: {e}")
        return jsonify({"error": "Failed to start conversation", "details": str(e)}), 500

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

@app.route("/api/clients", methods=["GET", "POST"])
def api_clients():
    try:
        if request.method == 'POST':
            if DatabaseManager is None:
                return jsonify({"error": "Database not configured"}), 500
            data = request.get_json(force=True) or {}
            client_id = str(uuid.uuid4())
            name = data.get('name')
            phone = data.get('phone')
            email = data.get('email')
            company = data.get('company')
            status = (data.get('status') or 'lead').lower()
            tags = data.get('tags') or []
            try:
                with DatabaseManager._get_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            """
                            INSERT INTO clients (id, name, phone, email, company, status, tags, last_contact_at)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, NULL)
                            """,
                            (client_id, name, phone, email, company, status, json.dumps(tags))
                        )
                        conn.commit()
                return jsonify({"id": client_id, "status": "created"}), 201
            except Exception as e:
                logger.error(f"Failed to create client: {e}")
                return jsonify({"error": "Failed to create client", "details": str(e)}), 500

        # GET
        search = request.args.get('search')
        status = request.args.get('status')
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('pageSize', 25, type=int)
        limit = max(1, min(page_size, 100))
        offset = max(0, (page - 1) * limit)

        if DatabaseManager is None:
            return jsonify({"items": [], "total": 0})
        items = DatabaseManager.list_clients(search=search, status=status, limit=limit, offset=offset) or []
        # For now, total is approximate as count not implemented; return filtered length
        return jsonify({"items": items, "total": len(items)})
    except Exception as e:
        logger.error(f"Error in /api/clients: {e}")
        return jsonify({"error": "Failed to process request", "details": str(e)}), 500

@app.route("/api/clients/<client_id>", methods=["GET", "PUT", "DELETE"])
def api_client_detail(client_id):
    try:
        if DatabaseManager is None:
            return jsonify({"error": "Database not configured"}), 500

        if request.method == 'GET':
            client = DatabaseManager.get_client(client_id)
            if not client:
                return jsonify({"error": "Client not found"}), 404
            return jsonify(client)

        if request.method == 'PUT':
            data = request.get_json(force=True) or {}
            fields = []
            params = []
            for key in ['name', 'phone', 'email', 'company', 'status']:
                if key in data:
                    fields.append(f"{key} = %s")
                    params.append(data.get(key))
            if 'tags' in data:
                fields.append("tags = %s")
                params.append(json.dumps(data.get('tags')))
            if not fields:
                return jsonify({"message": "No changes"})
            params.append(client_id)
            with DatabaseManager._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(f"UPDATE clients SET {', '.join(fields)}, updated_at = CURRENT_TIMESTAMP WHERE id = %s", params)
                    conn.commit()
            return jsonify({"id": client_id, "status": "updated"})

        # DELETE
        with DatabaseManager._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM clients WHERE id = %s", (client_id,))
                conn.commit()
        return jsonify({"id": client_id, "status": "deleted"})
    except Exception as e:
        logger.error(f"Error in /api/clients/<id>: {e}")
        return jsonify({"error": "Failed to process request", "details": str(e)}), 500

@app.route("/api/clients/<client_id>/calls", methods=["GET"])
def api_client_calls_by_id(client_id):
    try:
      if DatabaseManager is None:
          return jsonify([])
      # Get client phone
      client = DatabaseManager.get_client(client_id)
      if not client:
          return jsonify([])
      phone = client.get('phone') or ''
      limit = request.args.get('limit', 50, type=int)
      offset = request.args.get('offset', 0, type=int)
      # Query calls where from/to equals client phone
      with DatabaseManager._get_connection() as conn:
          with conn.cursor(cursor_factory=RealDictCursor) as cur:
              cur.execute(
                  """
                  SELECT t.call_sid as id, t.from_number, t.to_number, t.created_at as start_time,
                         r.duration, r.recording_sid,
                         CASE WHEN t.conversation_log IS NULL THEN 'failed'
                              WHEN r.recording_sid IS NULL THEN 'in-progress'
                              ELSE 'completed' END as status
                  FROM transcripts t
                  LEFT JOIN recordings r ON r.call_sid = t.call_sid
                  WHERE t.from_number = %s OR t.to_number = %s
                  ORDER BY t.created_at DESC
                  LIMIT %s OFFSET %s
                  """,
                  (phone, phone, limit, offset)
              )
              rows = cur.fetchall() or []
              data = []
              for row in rows:
                  duration = row.get('duration')
                  data.append({
                      "id": row.get('id'),
                      "fromNumber": row.get('from_number') or '',
                      "toNumber": row.get('to_number') or '',
                      "duration": _format_duration(duration),
                      "status": row.get('status'),
                      "startTime": _to_iso(row.get('start_time')),
                      "endTime": '',
                  })
              return jsonify(data)
    except Exception as e:
        logger.error(f"Error in /api/clients/<id>/calls: {e}")
        return jsonify({"error": "Failed to get client calls", "details": str(e)}), 500

@app.route("/api/clients/<client_id>/recordings", methods=["GET"])
def api_client_recordings_by_id(client_id):
    try:
        if DatabaseManager is None:
            return jsonify([])
        client = DatabaseManager.get_client(client_id)
        if not client:
            return jsonify([])
        phone = client.get('phone') or ''
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        with DatabaseManager._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT r.recording_sid as id, r.call_sid, r.created_at, r.duration, r.file_size,
                           r.from_number, r.to_number
                    FROM recordings r
                    WHERE r.from_number = %s OR r.to_number = %s
                    ORDER BY r.created_at DESC
                    LIMIT %s OFFSET %s
                    """,
                    (phone, phone, limit, offset)
                )
                rows = cur.fetchall() or []
                data = []
                for r in rows:
                    data.append({
                        "id": r.get('id'),
                        "callId": r.get('call_sid'),
                        "timestamp": _to_iso(r.get('created_at')),
                        "duration": _format_duration(r.get('duration')),
                        "size": _format_size(r.get('file_size')),
                        "fromNumber": r.get('from_number') or '',
                        "toNumber": r.get('to_number') or '',
                    })
                return jsonify(data)
    except Exception as e:
        logger.error(f"Error in /api/clients/<id>/recordings: {e}")
        return jsonify({"error": "Failed to get client recordings", "details": str(e)}), 500

@app.route("/api/clients/<client_id>/transcripts", methods=["GET"])
def api_client_transcripts_by_id(client_id):
    try:
        if DatabaseManager is None:
            return jsonify([])
        client = DatabaseManager.get_client(client_id)
        if not client:
            return jsonify([])
        phone = client.get('phone') or ''
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        with DatabaseManager._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT t.call_sid as id, t.created_at, t.from_number, t.to_number, t.conversation_log
                    FROM transcripts t
                    WHERE t.from_number = %s OR t.to_number = %s
                    ORDER BY t.created_at DESC
                    LIMIT %s OFFSET %s
                    """,
                    (phone, phone, limit, offset)
                )
                rows = cur.fetchall() or []
                data = []
                for t in rows:
                    # Build simple conversation count
                    count = 0
                    try:
                        text = t.get('conversation_log') or ''
                        count = sum(1 for line in text.splitlines() if line.strip())
                    except Exception:
                        count = 0
                    data.append({
                        "id": t.get('id'),
                        "callId": t.get('id'),
                        "timestamp": _to_iso(t.get('created_at')),
                        "fromNumber": t.get('from_number') or '',
                        "toNumber": t.get('to_number') or '',
                        "messages": count,
                    })
                return jsonify(data)
    except Exception as e:
        logger.error(f"Error in /api/clients/<id>/transcripts: {e}")
        return jsonify({"error": "Failed to get client transcripts", "details": str(e)}), 500

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
        # Initialize intent and confidence variables at the start
        intent = None
        confidence = 0.0
        
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
