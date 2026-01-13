"""
Password Reset Utility for PolicyHub

This script allows you to reset a user's password directly in the database.
Use this when you've forgotten your password and need to regain access.
"""

import sqlite3
import bcrypt
import sys
from pathlib import Path


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def reset_password(db_path: str, username: str, new_password: str):
    """
    Reset a user's password in the database.
    
    Args:
        db_path: Path to the SQLite database
        username: Username to reset password for
        new_password: New password to set
    """
    # Check if database exists
    if not Path(db_path).exists():
        print(f"❌ Error: Database not found at {db_path}")
        return False
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute("SELECT user_id, username, full_name FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        
        if not user:
            print(f"❌ Error: User '{username}' not found in database")
            conn.close()
            return False
        
        user_id, username, full_name = user
        print(f"✓ Found user: {full_name} ({username})")
        
        # Hash the new password
        password_hash = hash_password(new_password)
        
        # Update the password
        cursor.execute(
            "UPDATE users SET password_hash = ? WHERE user_id = ?",
            (password_hash, user_id)
        )
        conn.commit()
        
        print(f"✓ Password successfully reset for user '{username}'")
        print(f"✓ New password: {new_password}")
        print("\n⚠️  Please change your password after logging in!")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error resetting password: {e}")
        return False


def main():
    """Main function to run the password reset utility."""
    print("=" * 60)
    print("PolicyHub Password Reset Utility")
    print("=" * 60)
    print()
    
    # Default database path
    db_path = "SharedFolderDB/data/policyhub.db"
    
    # Get username
    print("Enter the username to reset password for:")
    username = input("Username: ").strip()
    
    if not username:
        print("❌ Error: Username cannot be empty")
        return
    
    # Get new password
    print("\nEnter the new password:")
    new_password = input("New password: ").strip()
    
    if not new_password:
        print("❌ Error: Password cannot be empty")
        return
    
    if len(new_password) < 8:
        print("⚠️  Warning: Password is less than 8 characters (recommended minimum)")
        confirm = input("Continue anyway? (y/n): ").strip().lower()
        if confirm != 'y':
            print("Password reset cancelled")
            return
    
    print()
    # Reset the password
    reset_password(db_path, username, new_password)


if __name__ == "__main__":
    main()
