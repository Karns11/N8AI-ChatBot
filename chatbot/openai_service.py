import logging
import time
import json
from typing import Dict, List, Optional, Tuple, Any
from django.conf import settings
from openai import OpenAI
from .utils import DatabaseManager, QueryFormatter
from .schema_manager import SchemaManager

logger = logging.getLogger(__name__)


class OpenAIService:
    """Service for interacting with OpenAI API to generate SQL queries."""
    
    def __init__(self, schema_file_path: Optional[str] = None):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL
        self.schema_manager = SchemaManager(schema_file_path)
    
    def generate_sql(self, user_query: str, chat_history: List[Dict], schema_info: Optional[Dict] = None) -> Tuple[bool, str, str, int]:  # type: ignore
        """
        Generate SQL query from natural language using OpenAI.
        
        Args:
            user_query: The natural language query
            chat_history: Previous messages in the chat
            schema_info: Database schema information
            
        Returns:
            Tuple[bool, str, str, int]: (success, sql_query, error_message, tokens_used)
        """
        start_time = time.time()
        
        try:
            # Build the prompt
            prompt = self._build_prompt(user_query, chat_history, schema_info)
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # Low temperature for more consistent SQL generation
                max_tokens=1000,
                stop=None
            )
            
            # Extract the response
            if not response.choices or not response.choices[0].message or not hasattr(response.choices[0].message, 'content') or response.choices[0].message.content is None:
                error_msg = "OpenAI API returned an unexpected response (no message content)"
                logger.error(error_msg)
                return False, "", error_msg, 0
            sql_query = response.choices[0].message.content.strip()

            if not hasattr(response, 'usage') or response.usage is None or not hasattr(response.usage, 'total_tokens') or response.usage.total_tokens is None:
                tokens_used = 0
            else:
                tokens_used = response.usage.total_tokens
            
            # Clean up the SQL query
            sql_query = self._clean_sql_query(sql_query)
            
            execution_time = time.time() - start_time
            logger.info(f"SQL generation completed in {execution_time:.2f}s, tokens: {tokens_used}")
            
            return True, sql_query, "", tokens_used
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"OpenAI API error: {str(e)}"
            logger.error(f"{error_msg} (execution time: {execution_time:.2f}s)")
            return False, "", error_msg, 0
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for SQL generation."""
        from datetime import datetime
        current_year = datetime.now().year
        
        return f"""You are an expert SQL developer. Your task is to convert natural language queries into safe, read-only SQL queries.

            IMPORTANT RULES:
            1. ONLY generate SELECT statements - no INSERT, UPDATE, DELETE, DROP, etc.
            2. Use proper SQL syntax for PostgreSQL
            3. Include appropriate WHERE clauses for filtering
            4. Use meaningful column aliases when needed
            5. Add LIMIT clauses for large result sets
            6. Use proper JOIN syntax when multiple tables are involved
            7. ALWAYS prefix table names with 'warehouse.' schema (e.g., warehouse.dim_player, warehouse.fact_player_stats)
            8. Pay attention to data types - use numeric values for numeric columns, strings for text columns
            9. For follow-up questions, use context from previous queries to make specific queries
            10. When referring to "that player" or similar, use the specific player information from chat history
            11. IMPORTANT: The current year is {current_year}. When users say "this year", "current year", "now", etc., use {current_year} in your queries
            12. Return ONLY the SQL query, no explanations or markdown formatting

            The user will provide:
            - A natural language query
            - Database schema information (if available)
            - Chat history for context

            Generate a clean, safe SQL query that answers the user's question."""

    def _build_prompt(self, user_query: str, chat_history: List[Dict], schema_info: Optional[Dict] = None) -> str:  # type: ignore
        """Build the prompt for OpenAI API."""
        prompt_parts = []
        
        # Add schema information if available
        if schema_info:
            prompt_parts.append("DATABASE SCHEMA:")
            for table_name, columns in schema_info.items():
                prompt_parts.append(f"\nTable: {table_name}")
                for column in columns:
                    nullable = "NULL" if column['is_nullable'] else "NOT NULL"
                    default = f" DEFAULT {column['column_default']}" if column['column_default'] else ""
                    prompt_parts.append(f"  - {column['column_name']}: {column['data_type']} {nullable}{default}")
            prompt_parts.append("")
        
        # Add chat history for context
        if chat_history:
            prompt_parts.append("CHAT HISTORY:")
            for msg in chat_history[-5:]:  # Last 5 messages for context
                role = "User" if msg['role'] == 'user' else "Assistant"
                content = msg['content']
                
                # Add SQL and results for assistant messages to provide better context
                if msg['role'] == 'assistant' and 'sql_query' in msg:
                    content += f" [SQL: {msg['sql_query']}]"
                if msg['role'] == 'assistant' and 'query_results' in msg:
                    content += f" [Results: {msg['query_results']}]"
                
                prompt_parts.append(f"{role}: {content}")
            prompt_parts.append("")
        
        # Add current year context
        from datetime import datetime
        current_year = datetime.now().year
        prompt_parts.append(f"CURRENT YEAR: {current_year}")
        
        # Add the current query
        prompt_parts.append(f"USER QUERY: {user_query}")
        prompt_parts.append("\nGenerate a SQL query to answer this question:")
        
        return "\n".join(prompt_parts)
    
    def _clean_sql_query(self, sql_query: str) -> str:
        """Clean and format the generated SQL query."""
        # Remove markdown code blocks if present
        if sql_query.startswith('```sql'):
            sql_query = sql_query[6:]
        if sql_query.startswith('```'):
            sql_query = sql_query[3:]
        if sql_query.endswith('```'):
            sql_query = sql_query[:-3]
        
        # Remove any leading/trailing whitespace
        sql_query = sql_query.strip()
        
        # Ensure it ends with semicolon
        if not sql_query.endswith(';'):
            sql_query += ';'
        
        return sql_query
    
    def get_schema_for_prompt(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get schema information formatted for prompt inclusion."""
        return self.schema_manager.get_schema_for_prompt()

    def generate_results_summary(self, user_query: str, formatted_results: dict) -> str:
        """Generate a summary of the results using OpenAI."""
        # Use only the first few rows for context
        sample_rows = formatted_results.get('data', [])[:3]
        columns = formatted_results.get('columns', [])
        prompt = (
            f"User question: {user_query}\n"
            f"Results (first few rows):\n"
        )
        for row in sample_rows:
            prompt += ", ".join(f"{col}: {row.get(col, '')}" for col in columns) + "\n"
        prompt += (
            "\nIn 1-2 sentences, confidently describe what the results show in plain English. "
            "Assume the SQL query and results already answer the user's question exactly. "
            "Do not hedge or express uncertainty—just state the answer as a fact. "
            "If the results are a list, summarize the key finding(s). If it's a single value, explain what it means.")
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that summarizes SQL query results for end users."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=120,
                stop=None
            )
            if response.choices and response.choices[0].message and hasattr(response.choices[0].message, 'content'):
                return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Error generating results summary: {str(e)}")
        return ""


class ChatService:
    """Service for managing chat interactions and SQL generation."""
    
    def __init__(self, schema_file_path: Optional[str] = None):
        self.openai_service = OpenAIService(schema_file_path)
    
    def process_user_message(self, user_query: str, chat_session, user) -> Tuple[bool, str, Dict]:
        """
        Process a user message and generate a response.
        
        Returns:
            Tuple[bool, str, Dict]: (success, error_message, response_data)
        """
        try:
            # Get chat history
            chat_history = self._get_chat_history(chat_session)
            # Get schema information
            schema_info = self.openai_service.get_schema_for_prompt()
            # Generate SQL
            sql_success, sql_query, sql_error, tokens_used = self.openai_service.generate_sql(
                user_query, chat_history, schema_info
            )
            if not sql_success:
                return False, sql_error, {}
            # Execute the SQL query
            db_success, results, db_error = DatabaseManager.execute_query(sql_query)
            # Format results
            formatted_results = QueryFormatter.format_results(results) if db_success else None
            # Generate summary if results exist
            summary = ""
            if db_success and formatted_results and formatted_results.get('data'):
                summary = self.openai_service.generate_results_summary(user_query, formatted_results)
            # Create response data
            response_data = {
                'sql_query': sql_query,
                'formatted_sql': QueryFormatter.format_sql_for_display(sql_query),
                'results': formatted_results,
                'error': db_error if not db_success else None,
                'tokens_used': tokens_used,
                'execution_success': db_success,
                'summary': summary
            }
            return True, "", response_data
        except Exception as e:
            error_msg = f"Error processing message: {str(e)}"
            logger.error(error_msg)
            return False, error_msg, {}

    def _get_chat_history(self, chat_session) -> List[Dict]:
        """Get chat history for the session."""
        messages = chat_session.messages.all().order_by('created_at')
        history = []
        
        for message in messages:
            msg_data = {
                'role': message.role,
                'content': message.content
            }
            
            # Add SQL and results for assistant messages to provide better context
            if message.role == 'assistant':
                if hasattr(message, 'sql_query') and message.sql_query:
                    msg_data['sql_query'] = message.sql_query
                if hasattr(message, 'query_results') and message.query_results:
                    msg_data['query_results'] = message.query_results
            
            history.append(msg_data)
        
        return history
    
    def create_chat_response(self, user_query: str, response_data: Dict, chat_session, user) -> 'Message':  # type: ignore
        """Create and save the assistant's response message."""
        from .models import Message, QueryLog
        
        # Create assistant message
        assistant_content = self._format_assistant_response(user_query, response_data)
        
        message = Message.objects.create(  # type: ignore
            chat_session=chat_session,
            role='assistant',
            content=assistant_content,
            sql_query=response_data.get('sql_query', ''),
            query_results=response_data.get('results'),
            error_message=response_data.get('error'),
            tokens_used=response_data.get('tokens_used', 0),
            execution_time=0.0  # Will be calculated if needed
        )
        
        # Log the query
        QueryLog.objects.create(  # type: ignore
            user=user,
            chat_session=chat_session,
            original_query=user_query,
            generated_sql=response_data.get('sql_query', ''),
            is_safe=True,  # Already validated
            execution_success=response_data.get('execution_success', False),
            error_message=response_data.get('error'),
            execution_time=0.0
        )
        
        return message
    
    def _format_assistant_response(self, user_query: str, response_data: Dict) -> str:
        """Format the assistant's response message."""
        parts = []
        if response_data.get('error'):
            parts.append(f"I encountered an error while processing your query: {response_data['error']}")
        # Only add the summary if present, no 'I found x results' lines
        elif response_data.get('summary'):
            parts.append(response_data['summary'])
        return " ".join(parts) 