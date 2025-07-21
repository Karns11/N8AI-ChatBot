import re
import logging
import time
import json
from typing import Dict, List, Tuple, Optional, Any
from django.conf import settings
from django.db import connections
from django.db.utils import OperationalError
import sqlparse
from sqlparse.sql import Token, TokenList
from sqlparse.tokens import Keyword, DML, DDL
import decimal
import datetime

logger = logging.getLogger(__name__)


class SQLSecurityValidator:
    """Validates SQL queries for security and safety."""
    
    # Dangerous SQL keywords that should be blocked
    DANGEROUS_KEYWORDS = {
        'DROP', 'TRUNCATE', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE',
        'GRANT', 'REVOKE', 'EXECUTE', 'EXEC', 'EXECUTE IMMEDIATE',
        'MERGE', 'UPSERT', 'REPLACE', 'RENAME', 'MODIFY'
    }
    
    # Dangerous functions that could cause issues
    DANGEROUS_FUNCTIONS = {
        'pg_read_file', 'pg_ls_dir', 'pg_stat_file', 'pg_read_binary_file',
        'system', 'exec', 'eval', 'shell_exec', 'passthru'
    }
    
    # Patterns that indicate potential SQL injection
    INJECTION_PATTERNS = [
        r'--\s*$',  # SQL comments
        r'/\*.*?\*/',  # Multi-line comments
        r'UNION\s+ALL',  # UNION attacks
        r'UNION\s+SELECT',  # UNION attacks
        r'OR\s+1\s*=\s*1',  # Always true conditions
        r'OR\s+TRUE',  # Always true conditions
        r'AND\s+1\s*=\s*1',  # Always true conditions
    ]

    @classmethod
    def validate_sql(cls, sql_query: str) -> Tuple[bool, str]:
        """
        Validate SQL query for security and safety.
        
        Returns:
            Tuple[bool, str]: (is_safe, error_message)
        """
        try:
            # Normalize the query
            sql_query = sql_query.strip().upper()
            
            # Check for dangerous keywords (as whole words)
            for keyword in cls.DANGEROUS_KEYWORDS:
                # Use word boundaries to avoid false positives
                import re
                pattern = r'\b' + re.escape(keyword) + r'\b'
                if re.search(pattern, sql_query):
                    return False, f"Dangerous SQL keyword '{keyword}' is not allowed"
            
            # Check for dangerous functions
            for func in cls.DANGEROUS_FUNCTIONS:
                if func.upper() in sql_query:
                    return False, f"Dangerous function '{func}' is not allowed"
            
            # Check for injection patterns
            for pattern in cls.INJECTION_PATTERNS:
                if re.search(pattern, sql_query, re.IGNORECASE):
                    return False, f"Potentially dangerous SQL pattern detected: {pattern}"
            
            # Parse SQL to check structure
            parsed = sqlparse.parse(sql_query)
            if not parsed:
                return False, "Invalid SQL query"
            
            # Check if it's a SELECT statement
            statement = parsed[0]
            if not cls._is_select_statement(statement):
                return False, "Only SELECT statements are allowed"
            
            # Additional checks for complex queries
            if not cls._validate_statement_structure(statement):
                return False, "Query structure validation failed"
            
            return True, "Query is safe"
            
        except Exception as e:
            logger.error(f"SQL validation error: {str(e)}")
            return False, f"SQL validation error: {str(e)}"

    @classmethod
    def _is_select_statement(cls, statement) -> bool:
        """Check if the statement is a SELECT statement."""
        for token in statement.tokens:
            if token.ttype is DML and token.value.upper() == 'SELECT':
                return True
        return False

    @classmethod
    def _validate_statement_structure(cls, statement) -> bool:
        """Validate the structure of the SQL statement."""
        # Check for nested queries that might be dangerous
        if cls._has_nested_dml(statement):
            return False
        
        # Check for multiple statements
        if cls._has_multiple_statements(statement):
            return False
        
        return True

    @classmethod
    def _has_nested_dml(cls, token_list) -> bool:
        """Check for nested DML statements."""
        for token in token_list:
            if hasattr(token, 'tokens'):
                if cls._has_nested_dml(token):
                    return True
            elif token.ttype is DML and token.value.upper() != 'SELECT':
                return True
        return False

    @classmethod
    def _has_multiple_statements(cls, statement) -> bool:
        """Check for multiple SQL statements."""
        # Count semicolons that are not in strings
        sql_str = str(statement)
        semicolon_count = sql_str.count(';')
        
        # If there are multiple semicolons, it might be multiple statements
        if semicolon_count > 1:
            return True
        
        return False


class DatabaseManager:
    """Manages database connections and operations."""
    
    @classmethod
    def get_warehouse_connection(cls):
        """Get connection to the warehouse database."""
        try:
            return connections['warehouse']
        except KeyError:
            logger.error("Warehouse database connection not configured")
            raise

    @classmethod
    def execute_query(cls, sql_query: str, timeout: int = 30) -> Tuple[bool, Any, str]:
        """
        Execute a SQL query safely.
        
        Returns:
            Tuple[bool, Any, str]: (success, results, error_message)
        """
        start_time = time.time()
        
        try:
            # Validate SQL first
            is_safe, error_msg = SQLSecurityValidator.validate_sql(sql_query)
            if not is_safe:
                return False, None, error_msg
            
            # Get connection
            connection = cls.get_warehouse_connection()
            
            # Execute query with timeout
            with connection.cursor() as cursor:
                cursor.execute(sql_query)
                
                # Fetch results
                if cursor.description:
                    columns = [desc[0] for desc in cursor.description]
                    rows = cursor.fetchall()
                    
                    # Convert to list of dictionaries
                    results = []
                    for row in rows:
                        results.append(dict(zip(columns, row)))
                    
                    execution_time = time.time() - start_time
                    logger.info(f"Query executed successfully in {execution_time:.2f}s")
                    return True, results, ""
                else:
                    execution_time = time.time() - start_time
                    logger.info(f"Query executed successfully (no results) in {execution_time:.2f}s")
                    return True, [], ""
                    
        except OperationalError as e:
            execution_time = time.time() - start_time
            error_msg = f"Database operation error: {str(e)}"
            logger.error(f"{error_msg} (execution time: {execution_time:.2f}s)")
            return False, None, error_msg
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"{error_msg} (execution time: {execution_time:.2f}s)")
            return False, None, error_msg

    @classmethod
    def get_schema_info(cls) -> Dict[str, List[Dict[str, Any]]]:
        """Get database schema information for prompt tuning."""
        try:
            connection = cls.get_warehouse_connection()
            
            # Query to get table and column information
            schema_query = """
                SELECT 
                    t.table_name,
                    c.column_name,
                    c.data_type,
                    c.is_nullable,
                    c.column_default
                FROM information_schema.tables t
                JOIN information_schema.columns c ON t.table_name = c.table_name
                WHERE t.table_schema = 'warehouse'
                AND t.table_type = 'BASE TABLE'
                ORDER BY t.table_name, c.ordinal_position
            """
            
            success, results, error = cls.execute_query(schema_query)
            if not success:
                logger.error(f"Failed to get schema info: {error}")
                return {}
            
            # Group by table
            schema_info = {}
            for row in results:
                table_name = row['table_name']
                if table_name not in schema_info:
                    schema_info[table_name] = []
                schema_info[table_name].append(row)
            
            return schema_info
            
        except Exception as e:
            logger.error(f"Error getting schema info: {str(e)}")
            return {}

    @classmethod
    def update_schema_cache(cls):
        """Update the cached schema information in the database."""
        try:
            from .models import DatabaseSchema
            
            # Clear existing cache
            DatabaseSchema.objects.all().delete()
            
            # Get fresh schema info
            schema_info = cls.get_schema_info()
            
            # Cache the schema
            schema_objects = []
            for table_name, columns in schema_info.items():
                for column in columns:
                    schema_objects.append(DatabaseSchema(
                        table_name=table_name,
                        column_name=column['column_name'],
                        data_type=column['data_type'],
                        is_nullable=column['is_nullable'] == 'YES',
                        column_default=column['column_default']
                    ))
            
            # Bulk create
            if schema_objects:
                DatabaseSchema.objects.bulk_create(schema_objects)
                logger.info(f"Cached schema for {len(schema_objects)} columns")
            
        except Exception as e:
            logger.error(f"Error updating schema cache: {str(e)}")


class QueryFormatter:
    """Formats query results for display."""
    
    @staticmethod
    def format_results(results: List[Dict[str, Any]], max_rows: int = 100) -> Dict[str, Any]:
        """Format query results for display."""
        if not results:
            return {
                'data': [],
                'columns': [],
                'row_count': 0,
                'truncated': False
            }
        
        # Get columns from first row
        columns = list(results[0].keys()) if results else []
        
        # Truncate if too many rows
        truncated = len(results) > max_rows
        display_results = results[:max_rows] if truncated else results

        # Convert Decimal, date, and datetime for JSON serialization
        def convert_value(val):
            if isinstance(val, decimal.Decimal):
                return float(val)
            if isinstance(val, (datetime.date, datetime.datetime)):
                return val.isoformat()
            return val
        display_results = [
            {k: convert_value(v) for k, v in row.items()} for row in display_results
        ]

        return {
            'data': display_results,
            'columns': columns,
            'row_count': len(results),
            'truncated': truncated,
            'display_count': len(display_results)
        }

    @staticmethod
    def format_sql_for_display(sql_query: str) -> str:
        """Format SQL query for display with syntax highlighting."""
        try:
            parsed = sqlparse.parse(sql_query)
            return sqlparse.format(str(parsed[0]), reindent=True, keyword_case='upper')
        except:
            return sql_query 