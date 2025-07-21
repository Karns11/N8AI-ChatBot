from django.urls import path
from . import views

app_name = 'chatbot'

urlpatterns = [
    # Main chat views
    path('', views.home, name='home'),
    path('chat/', views.chat_list, name='chat_list'),
    path('chat/new/', views.new_chat, name='new_chat'),
    path('chat/<int:chat_id>/', views.chat_detail, name='chat_detail'),
    path('chat/<int:chat_id>/rename/', views.rename_chat, name='rename_chat'),
    path('chat/<int:chat_id>/delete/', views.delete_chat, name='delete_chat'),
    path('chat/<int:chat_id>/clear/', views.clear_chat, name='clear_chat'),
    
    # AJAX endpoints
    path('chat/<int:chat_id>/send/', views.send_message, name='send_message'),
    path('api/test-sql/', views.test_sql_query, name='test_sql_query'),
    
    # Admin views
    path('admin/chats/', views.AdminChatListView.as_view(), name='admin_chat_list'),
    path('admin/chats/<int:pk>/', views.AdminChatDetailView.as_view(), name='admin_chat_detail'),
    path('admin/chats/<int:chat_id>/delete/', views.admin_delete_user_chat, name='admin_delete_user_chat'),
    path('admin/chats/<int:chat_id>/clear/', views.admin_clear_user_chat, name='admin_clear_user_chat'),
    
    # Database management
    path('admin/database/', views.database_status, name='database_status'),
    path('admin/database/update-schema/', views.update_schema_cache, name='update_schema_cache'),
    
    # Query logs
    path('admin/query-logs/', views.QueryLogListView.as_view(), name='query_logs'),
    path('admin/query-logs/<int:log_id>/', views.query_log_detail, name='query_log_detail'),
] 