#!/usr/bin/env python3
"""
Initialize Privik Database
Creates all necessary database tables
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def init_database():
    """Initialize the database with all tables"""
    try:
        print("🗄️  Initializing Privik Database...")
        
        # Use the existing database.py approach
        from backend.app.database import create_tables
        
        # Create all tables
        create_tables()
        
        print("✅ Database tables created successfully!")
        print("📁 Database file: privik.db")
        
        # List created tables
        from backend.app.database import engine
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        print(f"📋 Created {len(tables)} tables:")
        for table in tables:
            print(f"   - {table}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = init_database()
    if success:
        print("\n🎉 Database initialization completed!")
        print("You can now start the Privik backend server.")
    else:
        print("\n💥 Database initialization failed!")
        sys.exit(1)
