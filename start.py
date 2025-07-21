#!/usr/bin/env python
"""
N8AI Startup Script
This script helps you get the N8AI running quickly.
"""

import os
import sys
import subprocess
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors."""
    print(f"\n{description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✓ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed:")
        print(f"  Error: {e.stderr}")
        return False

def check_file_exists(filename):
    """Check if a file exists."""
    return Path(filename).exists()

def main():
    """Main startup function."""
    print("🚀 N8AI Startup")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not check_file_exists('manage.py'):
        print("✗ Error: manage.py not found. Please run this script from the project root directory.")
        return
    
    # Check if .env file exists
    if not check_file_exists('.env'):
        print("⚠️  .env file not found. Creating from template...")
        if check_file_exists('env.example'):
            try:
                import shutil
                shutil.copy('env.example', '.env')
                print("✓ .env file created from template")
                print("  Please edit .env with your configuration before continuing")
                return
            except Exception as e:
                print(f"✗ Failed to create .env file: {e}")
                return
        else:
            print("✗ env.example not found. Please create a .env file manually.")
            return
    
    # Run setup commands
    commands = [
        ("python manage.py makemigrations", "Creating database migrations"),
        ("python manage.py migrate", "Running database migrations"),
        ("python manage.py setup_schema --force", "Setting up database schema cache"),
    ]
    
    success = True
    for command, description in commands:
        if not run_command(command, description):
            success = False
            break
    
    if success:
        print("\n" + "=" * 50)
        print("🎉 Setup completed successfully!")
        print("\nNext steps:")
        print("1. Create a superuser (optional):")
        print("   python manage.py createsuperuser")
        print("\n2. Start the development server:")
        print("   python manage.py runserver")
        print("\n3. Open your browser to:")
        print("   http://localhost:8000")
        print("\n4. For admin access:")
        print("   http://localhost:8000/admin")
        
        # Ask if user wants to start the server
        response = input("\nWould you like to start the development server now? (y/n): ")
        if response.lower() in ['y', 'yes']:
            print("\nStarting development server...")
            print("Press Ctrl+C to stop the server")
            try:
                subprocess.run("python manage.py runserver", shell=True)
            except KeyboardInterrupt:
                print("\nServer stopped.")
    else:
        print("\n❌ Setup failed. Please check the errors above and try again.")

if __name__ == '__main__':
    main() 