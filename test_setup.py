#!/usr/bin/env python
"""
Test script to verify the N8AI setup.
Run this after installation to check if everything is working.
"""

import os
import sys
import django
from pathlib import Path

# Add the project directory to Python path
project_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(project_dir))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sql_chatbot.settings')
django.setup()

def test_imports():
    """Test if all required modules can be imported."""
    print("Testing imports...")
    
    try:
        from chatbot.models import ChatSession, Message, DatabaseSchema, QueryLog
        print("✓ Models imported successfully")
    except ImportError as e:
        print(f"✗ Error importing models: {e}")
        return False
    
    try:
        from chatbot.utils import SQLSecurityValidator, DatabaseManager, QueryFormatter
        print("✓ Utilities imported successfully")
    except ImportError as e:
        print(f"✗ Error importing utilities: {e}")
        return False
    
    try:
        from chatbot.openai_service import OpenAIService, ChatService
        print("✓ OpenAI service imported successfully")
    except ImportError as e:
        print(f"✗ Error importing OpenAI service: {e}")
        return False
    
    return True

def test_database_connection():
    """Test database connections."""
    print("\nTesting database connections...")
    
    try:
        from django.db import connections
        from django.db.utils import OperationalError
        
        # Test default database (SQLite)
        default_db = connections['default']
        with default_db.cursor() as cursor:
            cursor.execute("SELECT 1")
            print("✓ Default database connection successful")
    except Exception as e:
        print(f"✗ Default database connection failed: {e}")
        return False
    
    try:
        # Test warehouse database
        warehouse_db = connections['warehouse']
        with warehouse_db.cursor() as cursor:
            # Try PostgreSQL version first
            try:
                cursor.execute("SELECT version()")
                version = cursor.fetchone()[0]
                print(f"✓ Warehouse database connection successful (PostgreSQL {version.split()[1]})")
            except:
                # Fallback for SQLite
                cursor.execute("SELECT sqlite_version()")
                version = cursor.fetchone()[0]
                print(f"✓ Warehouse database connection successful (SQLite {version})")
    except Exception as e:
        print(f"✗ Warehouse database connection failed: {e}")
        print("  This is expected if database is not configured yet")
    
    return True

def test_sql_validation():
    """Test SQL validation functionality."""
    print("\nTesting SQL validation...")
    
    from chatbot.utils import SQLSecurityValidator
    
    # Test safe queries
    safe_queries = [
        "SELECT * FROM users",
        "SELECT name, email FROM customers WHERE active = true",
        "SELECT COUNT(*) FROM orders WHERE created_at > '2024-01-01'"
    ]
    
    for query in safe_queries:
        is_safe, error = SQLSecurityValidator.validate_sql(query)
        if is_safe:
            print(f"✓ Safe query validated: {query[:50]}...")
        else:
            print(f"✗ Safe query failed validation: {error}")
            return False
    
    # Test dangerous queries
    dangerous_queries = [
        "DROP TABLE users",
        "DELETE FROM customers",
        "UPDATE users SET password = 'hacked'",
        "INSERT INTO logs VALUES ('test')"
    ]
    
    for query in dangerous_queries:
        is_safe, error = SQLSecurityValidator.validate_sql(query)
        if not is_safe:
            print(f"✓ Dangerous query blocked: {query[:50]}...")
        else:
            print(f"✗ Dangerous query not blocked: {query}")
            return False
    
    return True

def test_openai_configuration():
    """Test OpenAI configuration."""
    print("\nTesting OpenAI configuration...")
    
    from django.conf import settings
    
    if not settings.OPENAI_API_KEY:
        print("✗ OpenAI API key not configured")
        print("  Set OPENAI_API_KEY in your .env file")
        return False
    
    if settings.OPENAI_API_KEY == 'your-openai-api-key-here':
        print("✗ OpenAI API key not set (using placeholder)")
        print("  Update OPENAI_API_KEY in your .env file")
        return False
    
    print(f"✓ OpenAI API key configured (model: {settings.OPENAI_MODEL})")
    return True

def test_django_admin():
    """Test Django admin configuration."""
    print("\nTesting Django admin...")
    
    try:
        from django.contrib import admin
        from chatbot.models import ChatSession, Message, DatabaseSchema, QueryLog
        
        # Check if models are registered
        registered_models = []
        for model in admin.site._registry.values():
            if hasattr(model, '__name__'):
                registered_models.append(model.__name__)
            else:
                registered_models.append(model.__class__.__name__)
        
        required_models = ['ChatSession', 'Message', 'DatabaseSchema', 'QueryLog']
        
        for model in required_models:
            if model in registered_models:
                print(f"✓ {model} registered in admin")
            else:
                print(f"✗ {model} not registered in admin")
                return False
        
        return True
    except Exception as e:
        print(f"✗ Admin configuration error: {e}")
        return False

def main():
    """Run all tests."""
    print("N8AI Setup Test")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_database_connection,
        test_sql_validation,
        test_openai_configuration,
        test_django_admin
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"✗ Test {test.__name__} failed with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print(" 89 All tests passed! Your N8AI is ready to use.")
        print("\nNext steps:")
        print("1. Run: python manage.py runserver")
        print("2. Visit: http://localhost:8000")
        print("3. Create a superuser: python manage.py createsuperuser")
        print("4. Set up schema cache: python manage.py setup_schema")
    else:
        print("❌ Some tests failed. Please check the configuration.")
        print("\nCommon issues:")
        print("- Check your .env file configuration")
        print("- Ensure PostgreSQL is running and accessible")
        print("- Verify OpenAI API key is valid")
        print("- Run migrations: python manage.py migrate")

if __name__ == '__main__':
    main() 