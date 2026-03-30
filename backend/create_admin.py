#!/usr/bin/env python3
"""Script to create an admin user or promote existing user to admin."""

import os
import sys
import getpass

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from models import User, SessionLocal, engine, Base
    from auth import get_password_hash
    
    # Ensure database tables exist
    Base.metadata.create_all(bind=engine)
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("Make sure you're running this from the backend directory.")
    sys.exit(1)

def create_admin(username: str, password: str = None):
    """Create a new admin user or promote existing user to admin."""
    db = SessionLocal()
    try:
        # Check if user exists
        user = db.query(User).filter(User.username == username).first()
        
        if user:
            # Promote existing user to admin
            if user.role == "admin":
                print(f"ℹ️  User '{username}' is already an admin!")
            else:
                user.role = "admin"
                db.commit()
                print(f"✅ User '{username}' promoted to admin!")
        else:
            # Create new admin user
            if not password:
                password = getpass.getpass("Enter password for new admin user: ")
                confirm = getpass.getpass("Confirm password: ")
                if password != confirm:
                    print("❌ Passwords don't match!")
                    return
            
            if len(password) < 6:
                print("❌ Password must be at least 6 characters long!")
                return
            
            user = User(
                username=username,
                password_hash=get_password_hash(password),
                role="admin"
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            print(f"✅ Admin user '{username}' created successfully!")
        
        # Show user info
        print(f"\n{'='*50}")
        print(f"User Details:")
        print(f"{'='*50}")
        print(f"  ID: {user.id}")
        print(f"  Username: {user.username}")
        print(f"  Role: {user.role}")
        print(f"  Created At: {user.created_at}")
        print(f"{'='*50}\n")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

def list_users():
    """List all users in the database."""
    db = SessionLocal()
    try:
        users = db.query(User).all()
        if not users:
            print("No users found in database.")
            return
        
        print(f"\n{'='*70}")
        print(f"{'ID':<5} {'Username':<20} {'Role':<10} {'Created At'}")
        print(f"{'='*70}")
        for user in users:
            print(f"{user.id:<5} {user.username:<20} {user.role:<10} {user.created_at}")
        print(f"{'='*70}\n")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Admin user management tool")
    parser.add_argument("--username", "-u", help="Username of admin user")
    parser.add_argument("--password", "-p", help="Password for new user (optional)")
    parser.add_argument("--list", "-l", action="store_true", help="List all users")
    
    args = parser.parse_args()
    
    if args.list:
        list_users()
    elif args.username:
        create_admin(args.username, args.password)
    else:
        print("Usage:")
        print("  Create/promote admin: python create_admin.py -u <username>")
        print("  List users:          python create_admin.py --list")
        parser.print_help()

