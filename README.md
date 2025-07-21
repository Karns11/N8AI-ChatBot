# N8AI - Natural Language to SQL Query Generator

A production-ready Django web application that allows users to ask natural language questions and get SQL query results from a PostgreSQL data warehouse. The application uses OpenAI's GPT models to translate natural language into SQL queries with comprehensive security validation.

## 🎯 Features

### Core Functionality

- **Natural Language to SQL**: Ask questions in plain English and get SQL results.
- **Real-time Chat Interface**: ChatGPT-style interface with message history.
- **Multiple Chat Sessions**: Create and manage multiple conversations.
- **SQL Security Validation**: Comprehensive protection against dangerous queries.
- **Database Schema Integration**: Automatic schema introspection for better query generation.

### Security & Safety

- **Read-only Queries Only**: Blocks all destructive SQL operations (DROP, DELETE, UPDATE, etc.).
- **SQL Injection Protection**: Multiple layers of validation and sanitization.
- **Query Logging**: Complete audit trail of all queries and results.

### User Authentication

Secure user management with Django auth.

### Admin Features

- **User Management**: View and manage all user accounts and chat sessions.
- **Query Monitoring**: Real-time monitoring of all SQL queries.
- **Database Status**: Connection status and schema information.
- **Chat Management**: Admin can view, clear, or delete any user's chats.

## User Experience

- **Modern UI**: Clean, responsive interface built with Bootstrap 5.
- **Real-time Messaging**: AJAX-powered chat with typing indicators.
- **Results Visualization**: Beautiful table display of query results.
- **Chat History**: Persistent conversation history with context.

## Quick Start

### Prerequisites

- Python 3.8+
- PostgreSQL database (for your data warehouse)
- OpenAI API key

### Installation

1. **Clone the repository**

    ```bash
    git clone <repo-url>
    cd sql_chatbot
    ```

2. **Create virtual environment**

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3. **Install dependencies**

    ```bash
    pip install -r requirements.txt
    ```

4. **Set up environment variables**

    ```bash
    cp env.example .env
    # Edit .env with your configuration
    ```

5. **Configure your .env file**

    ```env
    SECRET_KEY=your-secret-key
    DEBUG=True
    ALLOWED_HOSTS=localhost,127.0.0.1
    # PostgreSQL Warehouse Database
    DB_NAME=your_warehouse_db
    DB_USER=your_db_user
    DB_PASSWORD=your_db_password
    DB_HOST=your_db_host
    DB_PORT=5432
    # OpenAI API
    OPENAI_API_KEY=your-openai-api-key
    OPENAI_MODEL=gpt-4
    ```

6. **Run database migrations**

    ```bash
    python manage.py makemigrations
    python manage.py migrate
    ```

7. **Create a superuser**

    ```bash
    python manage.py createsuperuser
    ```

8. **Update database schema cache (optional)**

    ```bash
    python manage.py shell
    >>> from chatbot.utils import DatabaseManager
    >>> DatabaseManager.update_schema_cache()
    ```

9. **Run the development server**

    ```bash
    python manage.py runserver
    ```

10. **Access the application**

    - Main app: http://localhost:8000
    - Admin panel: http://localhost:8000/admin

---

## Database Configuration

### PostgreSQL Warehouse

Application connects to two databases:

- **SQLite**: Stores Django models, users, chat sessions.
- **PostgreSQL Warehouse**: Your data warehouse for SQL queries.

Configure your PostgreSQL connection in `settings.py`:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    },
    'warehouse': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'your_warehouse_db',
        'USER': 'your_db_user',
        'PASSWORD': 'your_db_password',
        'HOST': 'your_db_host',
        'PORT': '5432',
    },
}
```

---

## License

MIT