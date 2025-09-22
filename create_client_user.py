#!/usr/bin/env python3
"""
Script to create a client user for the VoiceAI system
Run this script to create a new client user account
"""

import os
import sys
import bcrypt
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_client_user():
    """Create a new client user"""
    
    # Database connection
    connection_string = os.getenv('DATABASE_URL') or \
        f"postgresql://{os.getenv('DB_USER', 'postgres')}:{os.getenv('DB_PASSWORD', '')}@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '5432')}/{os.getenv('DB_NAME', 'voiceai')}"
    
    try:
        with psycopg2.connect(connection_string) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                
                # Get user input
                print("=== Create Client User ===")
                username = input("Enter username: ").strip()
                email = input("Enter email: ").strip().lower()
                password = input("Enter password: ").strip()
                
                if not username or not email or not password:
                    print("Error: All fields are required!")
                    return False
                
                if len(password) < 6:
                    print("Error: Password must be at least 6 characters long!")
                    return False
                
                # Check if user already exists
                cur.execute("""
                    SELECT id FROM users WHERE username = %s OR email = %s
                """, (username, email))
                existing_user = cur.fetchone()
                
                if existing_user:
                    print("Error: Username or email already exists!")
                    return False
                
                # Hash the password
                password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                
                # Insert new user
                cur.execute("""
                    INSERT INTO users (username, email, password_hash, is_admin, is_active)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id, username, email, is_admin, created_at
                """, (username, email, password_hash, False, True))
                
                user = cur.fetchone()
                conn.commit()
                
                print(f"\n✅ Client user created successfully!")
                print(f"Username: {user['username']}")
                print(f"Email: {user['email']}")
                print(f"User ID: {user['id']}")
                print(f"Admin: {user['is_admin']}")
                print(f"Created: {user['created_at']}")
                print(f"\nYou can now login to the client dashboard with these credentials.")
                
                return True
                
    except Exception as e:
        print(f"Error creating user: {e}")
        return False

if __name__ == "__main__":
    success = create_client_user()
    sys.exit(0 if success else 1)
