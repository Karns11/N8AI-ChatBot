import json
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db import transaction
from django.utils import timezone
from .models import ChatSession, Message, DatabaseSchema, QueryLog
from .openai_service import ChatService
from .utils import DatabaseManager

logger = logging.getLogger(__name__)


def home(request):
    """Home page."""
    if request.user.is_authenticated:
        return redirect('chatbot:chat_list')
    return render(request, 'home.html')


@login_required
def chat_list(request):
    """Display list of user's chat sessions."""
    chat_sessions = ChatSession.objects.filter(user=request.user, is_active=True)
    return render(request, 'chatbot/chat_list.html', {
        'chat_sessions': chat_sessions
    })


@login_required
def chat_detail(request, chat_id):
    """Display a specific chat session."""
    chat_session = get_object_or_404(ChatSession, id=chat_id, user=request.user, is_active=True)
    chat_messages = chat_session.messages.all().order_by('created_at')
    chat_sessions = request.user.chat_sessions.filter(is_active=True)
    return render(request, 'chatbot/chat_detail.html', {
        'chat_session': chat_session,
        'chat_messages': chat_messages,
        'chat_sessions': chat_sessions,
    })


@login_required
def new_chat(request):
    """Create a new chat session."""
    if request.method == 'POST':
        title = request.POST.get('title', 'New Chat')
        chat_session = ChatSession.objects.create(
            user=request.user,
            title=title
        )
        return redirect('chatbot:chat_detail', chat_id=chat_session.id)
    
    return render(request, 'chatbot/new_chat.html')


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def send_message(request, chat_id):
    """Handle sending a message via AJAX."""
    try:
        chat_session = get_object_or_404(ChatSession, id=chat_id, user=request.user, is_active=True)
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return JsonResponse({
                'success': False,
                'error': 'Message cannot be empty'
            })
        
        # Create user message
        user_msg = Message.objects.create(
            chat_session=chat_session,
            role='user',
            content=user_message
        )
        
        # Process with OpenAI
        chat_service = ChatService()
        success, error_msg, response_data = chat_service.process_user_message(
            user_message, chat_session, request.user
        )
        
        if not success:
            # Create error message
            Message.objects.create(
                chat_session=chat_session,
                role='assistant',
                content=f"Sorry, I encountered an error: {error_msg}",
                error_message=error_msg
            )
            
            sql_query = response_data.get('sql_query', '') if response_data else ''
            return JsonResponse({
                'success': False,
                'error': error_msg,
                'sql_query': sql_query,
                'message_html': render(request, 'chatbot/partials/message.html', {
                    'message': {
                        'role': 'assistant',
                        'content': f"Sorry, I encountered an error: {error_msg}",
                        'error_message': error_msg,
                        'sql_query': sql_query
                    }
                }).content.decode('utf-8')
            })
        
        # Create assistant response
        assistant_msg = chat_service.create_chat_response(
            user_message, response_data, chat_session, request.user
        )
        
        # Update chat session timestamp
        chat_session.updated_at = timezone.now()
        chat_session.save()
        
        # Render the assistant message
        message_html = render(request, 'chatbot/partials/message.html', {
            'message': assistant_msg
        }).content.decode('utf-8')
        
        return JsonResponse({
            'success': True,
            'message_html': message_html,
            'sql_query': response_data.get('sql_query', ''),
            'results': response_data.get('results'),
            'error': response_data.get('error'),
        })
        
    except Exception as e:
        logger.error(f"Error in send_message: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
def rename_chat(request, chat_id):
    """Rename a chat session."""
    chat_session = get_object_or_404(ChatSession, id=chat_id, user=request.user, is_active=True)
    
    if request.method == 'POST':
        new_title = request.POST.get('title', '').strip()
        if new_title:
            chat_session.title = new_title
            chat_session.save()
            messages.success(request, 'Chat renamed successfully.')
            return redirect('chatbot:chat_detail', chat_id=chat_session.id)
        else:
            messages.error(request, 'Title cannot be empty.')
    
    return render(request, 'chatbot/rename_chat.html', {
        'chat_session': chat_session
    })


@login_required
def delete_chat(request, chat_id):
    """Delete a chat session."""
    chat_session = get_object_or_404(ChatSession, id=chat_id, user=request.user, is_active=True)
    
    if request.method == 'POST':
        chat_session.is_active = False
        chat_session.save()
        messages.success(request, 'Chat deleted successfully.')
        return redirect('chatbot:chat_list')
    
    return render(request, 'chatbot/delete_chat.html', {
        'chat_session': chat_session
    })


@login_required
def clear_chat(request, chat_id):
    """Clear all messages from a chat session."""
    chat_session = get_object_or_404(ChatSession, id=chat_id, user=request.user, is_active=True)
    
    if request.method == 'POST':
        chat_session.messages.all().delete()
        messages.success(request, 'Chat cleared successfully.')
        return redirect('chatbot:chat_detail', chat_id=chat_session.id)
    
    return render(request, 'chatbot/clear_chat.html', {
        'chat_session': chat_session
    })


# Admin views for managing all users' chats
class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff


class AdminChatListView(AdminRequiredMixin, ListView):
    model = ChatSession
    template_name = 'chatbot/admin/chat_list.html'
    context_object_name = 'chat_sessions'
    paginate_by = 20
    
    def get_queryset(self):
        return ChatSession.objects.filter(is_active=True).select_related('user')


class AdminChatDetailView(AdminRequiredMixin, DetailView):
    model = ChatSession
    template_name = 'chatbot/admin/chat_detail.html'
    context_object_name = 'chat_session'
    
    def get_queryset(self):
        return ChatSession.objects.select_related('user')


@login_required
def admin_delete_user_chat(request, chat_id):
    """Admin function to delete any user's chat."""
    if not request.user.is_staff:
        messages.error(request, 'Access denied.')
        return redirect('chatbot:chat_list')
    
    chat_session = get_object_or_404(ChatSession, id=chat_id)
    
    if request.method == 'POST':
        chat_session.is_active = False
        chat_session.save()
        messages.success(request, f'Chat "{chat_session.title}" deleted successfully.')
        return redirect('chatbot:admin_chat_list')
    
    return render(request, 'chatbot/admin/delete_chat.html', {
        'chat_session': chat_session
    })


@login_required
def admin_clear_user_chat(request, chat_id):
    """Admin function to clear any user's chat."""
    if not request.user.is_staff:
        messages.error(request, 'Access denied.')
        return redirect('chatbot:chat_list')
    
    chat_session = get_object_or_404(ChatSession, id=chat_id)
    
    if request.method == 'POST':
        chat_session.messages.all().delete()
        messages.success(request, f'Chat "{chat_session.title}" cleared successfully.')
        return redirect('chatbot:admin_chat_detail', chat_id=chat_session.id)
    
    return render(request, 'chatbot/admin/clear_chat.html', {
        'chat_session': chat_session
    })


# Database management views
@login_required
def database_status(request):
    """Display database connection status and schema information."""
    if not request.user.is_staff:
        messages.error(request, 'Access denied.')
        return redirect('chatbot:chat_list')
    
    try:
        # Test database connection
        connection = DatabaseManager.get_warehouse_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT version();")
            db_version = cursor.fetchone()[0]
        
        # Get YAML schema info
        from .schema_manager import SchemaManager
        schema_manager = SchemaManager()
        schema_info = schema_manager.load_schema_from_yaml()
        schema_summary = schema_manager.get_schema_summary()
        
        # Validate schema file
        is_valid, validation_message = schema_manager.validate_schema_file()
        
        context = {
            'db_connected': True,
            'db_version': db_version,
            'schema_info': schema_info,
            'schema_summary': schema_summary,
            'schema_valid': is_valid,
            'validation_message': validation_message,
            'table_count': len(schema_info)
        }
        
    except Exception as e:
        context = {
            'db_connected': False,
            'error': str(e)
        }
    
    return render(request, 'chatbot/admin/database_status.html', context)


@login_required
def update_schema_cache(request):
    """Update the cached database schema."""
    if not request.user.is_staff:
        messages.error(request, 'Access denied.')
        return redirect('chatbot:chat_list')
    
    if request.method == 'POST':
        try:
            DatabaseManager.update_schema_cache()
            messages.success(request, 'Schema cache updated successfully.')
        except Exception as e:
            messages.error(request, f'Error updating schema cache: {str(e)}')
        
        return redirect('chatbot:database_status')
    
    return render(request, 'chatbot/admin/update_schema.html')


# Query log views
class QueryLogListView(AdminRequiredMixin, ListView):
    model = QueryLog
    template_name = 'chatbot/admin/query_logs.html'
    context_object_name = 'query_logs'
    paginate_by = 50
    
    def get_queryset(self):
        return QueryLog.objects.select_related('user', 'chat_session').order_by('-created_at')


@login_required
def query_log_detail(request, log_id):
    """Display details of a specific query log."""
    if not request.user.is_staff:
        messages.error(request, 'Access denied.')
        return redirect('chatbot:chat_list')
    
    query_log = get_object_or_404(QueryLog, id=log_id)
    
    return render(request, 'chatbot/admin/query_log_detail.html', {
        'query_log': query_log
    })


# API endpoints for AJAX requests
@login_required
@csrf_exempt
@require_http_methods(["POST"])
def test_sql_query(request):
    """Test a SQL query without saving it."""
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Access denied'})
    
    try:
        data = json.loads(request.body)
        sql_query = data.get('sql_query', '').strip()
        
        if not sql_query:
            return JsonResponse({'success': False, 'error': 'SQL query cannot be empty'})
        
        # Execute the query
        success, results, error = DatabaseManager.execute_query(sql_query)
        
        if success:
            formatted_results = QueryFormatter.format_results(results)
            return JsonResponse({
                'success': True,
                'results': formatted_results
            })
        else:
            return JsonResponse({
                'success': False,
                'error': error
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Unexpected error: {str(e)}'
        })


# Error handlers
def handler404(request, exception):
    return render(request, 'chatbot/404.html', status=404)


def handler500(request):
    return render(request, 'chatbot/500.html', status=500) 