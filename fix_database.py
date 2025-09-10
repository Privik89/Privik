#!/usr/bin/env python3
"""
Fix Privik Database - Create tables with proper Base class
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import declarative_base

# Database URL
DATABASE_URL = "sqlite:///./privik.db"

# Create database engine
engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=300)

# Create shared base class
Base = declarative_base()

def fix_database():
    """Fix database by creating tables with shared Base class"""
    try:
        print("🗄️  Fixing Privik Database...")
        
        # Import models and recreate them with shared Base
        from backend.app.models.email import Email, EmailAttachment
        from backend.app.models.click import ClickEvent, LinkAnalysis
        from backend.app.models.sandbox import SandboxAnalysis
        from backend.app.models.user import User, UserRiskProfile
        from backend.app.models.threat import ThreatIntel, ThreatIndicator
        
        # Create tables using the shared Base
        Base.metadata.create_all(bind=engine)
        
        print("✅ Database tables created successfully!")
        print("📁 Database file: privik.db")
        
        # List created tables
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        print(f"📋 Created {len(tables)} tables:")
        for table in tables:
            print(f"   - {table}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error fixing database: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = fix_database()
    if success:
        print("\n🎉 Database fix completed!")
    else:
        print("\n💥 Database fix failed!")
        sys.exit(1)
