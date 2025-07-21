from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import json


class ChatSession(models.Model):
    """Model for chat sessions that users can create and manage."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_sessions')
    title = models.CharField(max_length=200, default='New Chat')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.user.username} - {self.title}"

    def get_message_count(self):
        return self.messages.count()

    def get_last_message(self):
        return self.messages.last()


class Message(models.Model):
    """Model for individual messages in chat sessions."""
    ROLE_CHOICES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
        ('system', 'System'),
    ]

    chat_session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    sql_query = models.TextField(blank=True, null=True)
    query_results = models.JSONField(blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    tokens_used = models.IntegerField(default=0)
    execution_time = models.FloatField(default=0.0)  # in seconds

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.chat_session.title} - {self.role} - {self.created_at}"

    def get_formatted_results(self):
        """Return formatted query results for display."""
        if not self.query_results:
            return None
        
        try:
            if isinstance(self.query_results, str):
                return json.loads(self.query_results)
            return self.query_results
        except (json.JSONDecodeError, TypeError):
            return self.query_results


class DatabaseSchema(models.Model):
    """Model to cache database schema information for prompt tuning."""
    table_name = models.CharField(max_length=100)
    column_name = models.CharField(max_length=100)
    data_type = models.CharField(max_length=50)
    is_nullable = models.BooleanField(default=True)
    column_default = models.TextField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['table_name', 'column_name']
        ordering = ['table_name', 'column_name']

    def __str__(self):
        return f"{self.table_name}.{self.column_name} ({self.data_type})"


class QueryLog(models.Model):
    """Model to log all SQL queries for audit and debugging purposes."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='query_logs')
    chat_session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='query_logs')
    original_query = models.TextField()
    generated_sql = models.TextField()
    is_safe = models.BooleanField(default=False)
    execution_success = models.BooleanField(default=False)
    error_message = models.TextField(blank=True, null=True)
    execution_time = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.created_at}" 