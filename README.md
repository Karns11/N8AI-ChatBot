# N8AI - Natural Language to SQL Query Generator

A production-ready Django web application that allows users to ask natural language questions and get SQL query results from a PostgreSQL data warehouse. The application uses OpenAI's GPT models to translate natural language into SQL queries with comprehensive security validation.

## 🎯 Features

### Core Functionality
- **Natural Language to SQL**: Ask questions in plain English and get SQL results
- **Real-time Chat Interface**: ChatGPT-style interface with message history
- **Multiple Chat Sessions**: Create and manage multiple conversations
- **SQL Security Validation**: Comprehensive protection against dangerous queries
- **Database Schema Integration**: Automatic schema introspection for better query generation

### Security & Safety
- **Read-only Queries Only**: Blocks all destructive SQL operations (DROP, DELETE, UPDATE, etc.)
- **SQL Injection Protection**: Multiple layers of validation and sanitization
- **Query Logging**: Complete audit trail of all queries and results
- **User Authentication**: Secure user management with Django auth

### Admin Features
- **User Management**: View and manage all user accounts and chat sessions
- **Query Monitoring**: Real-time monitoring of all SQL queries
- **Database Status**: Connection status and schema information
- **Chat Management**: Admin can view, clear, or delete any user's chats

### User Experience
- **Modern UI**: Clean, responsive interface built with Bootstrap 5
- **Real-time Messaging**: AJAX-powered chat with typing indicators
- **Results Visualization**: Beautiful table display of query results
- **Chat History**: Persistent conversation history with context
- **Chat Management**: Rename, clear, and delete chat sessions

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- PostgreSQL database (for your data warehouse)
- OpenAI API key

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
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
   SECRET_KEY=your-secret-key-here
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
   ```
   ```python
   from chatbot.utils import DatabaseManager
   DatabaseManager.update_schema_cache()
   ```

9. **Run the development server**
   ```bash
   python manage.py runserver
   ```

10. **Access the application**
    - Main app: http://localhost:8000
    - Admin panel: http://localhost:8000/admin

## 📊 Database Configuration

### PostgreSQL Warehouse Setup

The application connects to two databases:
1. **SQLite** (default): Stores Django models, users, chat sessions
2. **PostgreSQL** (warehouse): Your data warehouse for SQL queries

Configure your PostgreSQL connection in `settings.py`:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    },
    'warehouse': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST'),
        'PORT': config('DB_PORT'),
    }
}
```

### Schema Caching

For optimal performance, the application caches your database schema:

```python
# Update schema cache
from chatbot.utils import DatabaseManager
DatabaseManager.update_schema_cache()
```

## 🔒 Security Features

### SQL Validation

The application implements multiple security layers:

1. **Keyword Blocking**: Prevents dangerous SQL keywords
   - DROP, TRUNCATE, DELETE, UPDATE, INSERT, ALTER, CREATE, etc.

2. **Function Blocking**: Blocks dangerous PostgreSQL functions
   - pg_read_file, pg_ls_dir, system, exec, etc.

3. **Pattern Detection**: Identifies SQL injection attempts
   - UNION attacks, always-true conditions, comments

4. **Statement Validation**: Ensures only SELECT statements are allowed

### Query Logging

All queries are logged for audit purposes:
- Original natural language query
- Generated SQL query
- Execution success/failure
- User and session information
- Execution time

## 🎨 Usage Examples

### Natural Language Queries

Users can ask questions like:

- "Show me all users who signed up last month"
- "What are the top 10 products by sales?"
- "How many orders were placed yesterday?"
- "Find customers who spent more than $1000"
- "Show me the average order value by month"

### Chat Interface

1. **Create a new chat** from the chat list
2. **Ask questions** in natural language
3. **View generated SQL** and results
4. **Continue the conversation** with follow-up questions
5. **Manage chats** by renaming, clearing, or deleting

## 🛠️ Admin Features

### User Management
- View all users and their chat sessions
- Monitor user activity and query patterns
- Manage user permissions

### Query Monitoring
- Real-time view of all SQL queries
- Success/failure rates
- Performance metrics
- Security alerts

### Database Management
- Connection status monitoring
- Schema information display
- Cache management
- Query testing interface

## 📁 Project Structure

```
sql_chatbot/
├── manage.py                 # Django management script
├── requirements.txt          # Python dependencies
├── env.example              # Environment variables template
├── README.md                # This file
├── sql_chatbot/             # Main Django project
│   ├── __init__.py
│   ├── settings.py          # Django settings
│   ├── urls.py              # Main URL configuration
│   ├── wsgi.py              # WSGI configuration
│   └── asgi.py              # ASGI configuration
├── chatbot/                 # Main application
│   ├── __init__.py
│   ├── admin.py             # Django admin configuration
│   ├── apps.py              # App configuration
│   ├── models.py            # Database models
│   ├── views.py             # View functions
│   ├── urls.py              # URL routing
│   ├── utils.py             # SQL validation and database utilities
│   └── openai_service.py    # OpenAI integration
└── templates/               # HTML templates
    ├── base.html            # Base template
    └── chatbot/             # App-specific templates
        ├── chat_list.html
        ├── chat_detail.html
        ├── new_chat.html
        └── partials/
            └── message.html
```

## 🔧 Configuration Options

### OpenAI Settings

```python
# In settings.py
OPENAI_API_KEY = config('OPENAI_API_KEY')
OPENAI_MODEL = config('OPENAI_MODEL', default='gpt-4')
```

### Database Settings

```python
# PostgreSQL warehouse connection
DATABASES = {
    'warehouse': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST'),
        'PORT': config('DB_PORT'),
    }
}
```

### Security Settings

```python
# Query timeout (seconds)
QUERY_TIMEOUT = 30

# Maximum results to display
MAX_RESULTS = 100

# Allowed SQL keywords (only SELECT-related)
ALLOWED_SQL_KEYWORDS = ['SELECT', 'FROM', 'WHERE', 'JOIN', 'GROUP BY', 'ORDER BY', 'LIMIT']
```

## 🚀 Deployment

### Production Setup

1. **Set production environment variables**
   ```env
   DEBUG=False
   SECRET_KEY=your-production-secret-key
   ALLOWED_HOSTS=your-domain.com
   ```

2. **Configure static files**
   ```bash
   python manage.py collectstatic
   ```

3. **Use production database**
   - Configure PostgreSQL for Django database
   - Set up proper database connections

4. **Deploy with Gunicorn**
   ```bash
   pip install gunicorn
   gunicorn sql_chatbot.wsgi:application
   ```

### Docker Deployment

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN python manage.py collectstatic --noinput

EXPOSE 8000
CMD ["gunicorn", "sql_chatbot.wsgi:application", "--bind", "0.0.0.0:8000"]
```

## 🧪 Testing

### Run Tests
```bash
python manage.py test
```

### Test SQL Generation
```python
from chatbot.openai_service import OpenAIService

service = OpenAIService()
success, sql, error, tokens = service.generate_sql(
    "Show me all users", 
    [], 
    schema_info={}
)
print(f"SQL: {sql}")
```

## 📝 API Endpoints

### Chat Endpoints
- `GET /chat/` - List user's chat sessions
- `POST /chat/new/` - Create new chat session
- `GET /chat/<id>/` - View specific chat
- `POST /chat/<id>/send/` - Send message (AJAX)

### Admin Endpoints
- `GET /admin/chats/` - View all chats (admin only)
- `GET /admin/query-logs/` - View query logs (admin only)
- `GET /admin/database/` - Database status (admin only)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
1. Check the documentation
2. Review the admin panel for system status
3. Check the logs in `logs/django.log`
4. Open an issue on GitHub

## 🔄 Updates

### Schema Updates
When your database schema changes:
1. Update the schema cache via admin panel
2. Or run: `DatabaseManager.update_schema_cache()`

### Model Updates
When updating Django models:
```bash
python manage.py makemigrations
python manage.py migrate
```

---

**Built with ❤️ using Django, OpenAI, and PostgreSQL** #   N 8 A I - C h a t B o t  
 