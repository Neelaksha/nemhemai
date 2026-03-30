"""
Database migration script to add model_used column to chat_history table.
This script safely adds the new column for tracking which LLM model was used.

Run this script once after updating to the new version:
    python migrate_db.py
"""

import sqlite3
import os
import sys

def migrate_database():
    """Add model_used column to chat_history table if it doesn't exist."""
    
    # Get the database path
    BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
    DATABASE_PATH = os.path.join(BACKEND_DIR, "users.db")
    
    if not os.path.exists(DATABASE_PATH):
        print(f"❌ Database not found at: {DATABASE_PATH}")
        print("Creating new database with updated schema...")
        # The tables will be created with the new schema when the app starts
        return True
    
    print(f"📂 Found database at: {DATABASE_PATH}")
    
    try:
        # Connect to the database
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Check if the column already exists
        cursor.execute("PRAGMA table_info(chat_history)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'model_used' in columns:
            print("✅ Column 'model_used' already exists in chat_history table.")
            print("No migration needed.")
            return True
        
        # Add the new column
        print("⏳ Adding 'model_used' column to chat_history table...")
        cursor.execute("""
            ALTER TABLE chat_history 
            ADD COLUMN model_used TEXT DEFAULT NULL
        """)
        
        conn.commit()
        print("✅ Successfully added 'model_used' column to chat_history table!")
        print("\n📝 What this means:")
        print("   • Chat history will now track which AI model generated each response")
        print("   • When you switch models, the new model will have context from previous conversations")
        print("   • Example: Switch from GPT-4 to Claude, and Claude will know about your previous chat")
        
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
        
    finally:
        if conn:
            conn.close()
            print("\n🔒 Database connection closed.")

def verify_migration():
    """Verify that the migration was successful."""
    
    BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
    DATABASE_PATH = os.path.join(BACKEND_DIR, "users.db")
    
    if not os.path.exists(DATABASE_PATH):
        return True  # New database will have the column
    
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Check the schema
        cursor.execute("PRAGMA table_info(chat_history)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}
        
        if 'model_used' not in columns:
            print("❌ Verification failed: model_used column not found")
            return False
        
        print(f"\n✅ Verification successful!")
        print(f"   Column 'model_used' type: {columns['model_used']}")
        
        # Count existing records
        cursor.execute("SELECT COUNT(*) FROM chat_history")
        count = cursor.fetchone()[0]
        print(f"   Total chat history records: {count}")
        
        if count > 0:
            print(f"\n💡 Note: Existing {count} chat records will have model_used=NULL")
            print("   New chats will automatically track the model used.")
        
        return True
        
    except Exception as e:
        print(f"❌ Verification error: {e}")
        return False
        
    finally:
        if conn:
            conn.close()

def main():
    """Main migration function."""
    
    print("=" * 60)
    print("🔄 NemHemAI Database Migration")
    print("=" * 60)
    print("\nAdding support for LLM model context switching...")
    print("\nThis will allow models to have context when you switch between them.")
    print("For example: Chat with Model A, then switch to Model B.")
    print("Model B will know about your conversation with Model A!\n")
    
    # Perform migration
    success = migrate_database()
    
    if not success:
        print("\n❌ Migration failed!")
        sys.exit(1)
    
    # Verify migration
    if not verify_migration():
        print("\n❌ Migration verification failed!")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("✅ Migration completed successfully!")
    print("=" * 60)
    print("\n🚀 You can now start your application:")
    print("   • Backend: python backend/main.py")
    print("   • Frontend: npm run dev")
    print("\n💬 Try it out:")
    print("   1. Start a conversation with one model")
    print("   2. Switch to a different model")
    print("   3. The new model will have context from your previous messages!")
    print()

if __name__ == "__main__":
    main()
