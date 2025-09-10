#!/usr/bin/env python3
"""
Create Working Database - Direct SQL approach
"""

import sqlite3
import os

def create_working_database():
    """Create database tables directly with SQL"""
    try:
        print("🗄️  Creating Working Database...")
        
        # Remove existing database
        if os.path.exists('privik.db'):
            os.remove('privik.db')
        
        # Create database connection
        conn = sqlite3.connect('privik.db')
        cursor = conn.cursor()
        
        # Create emails table
        cursor.execute('''
            CREATE TABLE emails (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id VARCHAR(255) UNIQUE,
                subject VARCHAR(500),
                sender VARCHAR(255),
                recipients TEXT,
                received_at DATETIME,
                content_type VARCHAR(100),
                body_text TEXT,
                body_html TEXT,
                threat_score FLOAT DEFAULT 0.0,
                is_suspicious BOOLEAN DEFAULT FALSE,
                ai_verdict VARCHAR(50),
                static_scan_result TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create email_attachments table
        cursor.execute('''
            CREATE TABLE email_attachments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email_id INTEGER,
                filename VARCHAR(255),
                content_type VARCHAR(100),
                file_size INTEGER,
                file_path VARCHAR(500),
                file_hash VARCHAR(64),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (email_id) REFERENCES emails (id)
            )
        ''')
        
        # Create click_events table
        cursor.execute('''
            CREATE TABLE click_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email_id INTEGER,
                user_id VARCHAR(255),
                original_url TEXT,
                proxy_url VARCHAR(500),
                clicked_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                threat_score FLOAT DEFAULT 0.0,
                is_suspicious BOOLEAN DEFAULT FALSE,
                ai_verdict VARCHAR(50),
                screenshot_path VARCHAR(500),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (email_id) REFERENCES emails (id)
            )
        ''')
        
        # Create link_analyses table
        cursor.execute('''
            CREATE TABLE link_analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                click_event_id INTEGER,
                page_title VARCHAR(500),
                page_content TEXT,
                page_screenshot VARCHAR(500),
                is_login_page BOOLEAN DEFAULT FALSE,
                is_phishing_page BOOLEAN DEFAULT FALSE,
                has_suspicious_forms BOOLEAN DEFAULT FALSE,
                redirect_chain TEXT,
                ai_intent VARCHAR(100),
                ai_confidence FLOAT DEFAULT 0.0,
                ai_details TEXT,
                http_status INTEGER,
                response_headers TEXT,
                load_time FLOAT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (click_event_id) REFERENCES click_events (id)
            )
        ''')
        
        # Create sandbox_analyses table
        cursor.execute('''
            CREATE TABLE sandbox_analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                attachment_id INTEGER,
                sandbox_id VARCHAR(255),
                analysis_started DATETIME,
                analysis_completed DATETIME,
                verdict VARCHAR(50),
                threat_score FLOAT DEFAULT 0.0,
                file_hash VARCHAR(64),
                file_type VARCHAR(50),
                file_size INTEGER,
                analysis_details TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (attachment_id) REFERENCES email_attachments (id)
            )
        ''')
        
        # Create users table
        cursor.execute('''
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username VARCHAR(255) UNIQUE,
                email VARCHAR(255) UNIQUE,
                full_name VARCHAR(255),
                role VARCHAR(50) DEFAULT 'user',
                is_active BOOLEAN DEFAULT TRUE,
                last_login DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create user_risk_profiles table
        cursor.execute('''
            CREATE TABLE user_risk_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                risk_score FLOAT DEFAULT 0.0,
                click_frequency FLOAT DEFAULT 0.0,
                suspicious_click_ratio FLOAT DEFAULT 0.0,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Create threat_intel table
        cursor.execute('''
            CREATE TABLE threat_intel (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                indicator VARCHAR(255),
                indicator_type VARCHAR(50),
                threat_type VARCHAR(50),
                confidence FLOAT DEFAULT 0.0,
                source VARCHAR(100),
                first_seen DATETIME,
                last_seen DATETIME,
                is_active BOOLEAN DEFAULT TRUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create threat_indicators table
        cursor.execute('''
            CREATE TABLE threat_indicators (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                threat_intel_id INTEGER,
                indicator_value VARCHAR(255),
                indicator_type VARCHAR(50),
                confidence FLOAT DEFAULT 0.0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (threat_intel_id) REFERENCES threat_intel (id)
            )
        ''')
        
        # Commit changes
        conn.commit()
        
        # Get table count
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print("✅ Database tables created successfully!")
        print("📁 Database file: privik.db")
        print(f"📋 Created {len(tables)} tables:")
        for table in tables:
            print(f"   - {table[0]}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error creating database: {e}")
        return False

if __name__ == "__main__":
    success = create_working_database()
    if success:
        print("\n🎉 Working database created!")
        print("You can now test the Privik backend.")
    else:
        print("\n💥 Database creation failed!")
        exit(1)
