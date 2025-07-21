from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import ChatSession, Message, DatabaseSchema, QueryLog


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'created_at', 'updated_at', 'is_active', 'message_count']
    list_filter = ['is_active', 'created_at', 'updated_at', 'user']
    search_fields = ['title', 'user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at']
    actions = ['deactivate_sessions', 'activate_sessions', 'delete_sessions']

    def message_count(self, obj):
        return obj.get_message_count()
    message_count.short_description = 'Messages'

    def deactivate_sessions(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f"{queryset.count()} chat sessions deactivated.")
    deactivate_sessions.short_description = "Deactivate selected chat sessions"

    def activate_sessions(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f"{queryset.count()} chat sessions activated.")
    activate_sessions.short_description = "Activate selected chat sessions"

    def delete_sessions(self, request, queryset):
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f"{count} chat sessions deleted.")
    delete_sessions.short_description = "Delete selected chat sessions"


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['chat_session', 'role', 'content_preview', 'created_at', 'tokens_used', 'execution_time']
    list_filter = ['role', 'created_at', 'chat_session__user']
    search_fields = ['content', 'sql_query', 'chat_session__title', 'chat_session__user__username']
    readonly_fields = ['created_at', 'tokens_used', 'execution_time']
    fieldsets = (
        ('Basic Information', {
            'fields': ('chat_session', 'role', 'content')
        }),
        ('SQL Information', {
            'fields': ('sql_query', 'query_results', 'error_message'),
            'classes': ('collapse',)
        }),
        ('Performance', {
            'fields': ('tokens_used', 'execution_time'),
            'classes': ('collapse',)
        }),
    )

    def content_preview(self, obj):
        return obj.content[:100] + '...' if len(obj.content) > 100 else obj.content
    content_preview.short_description = 'Content'


@admin.register(DatabaseSchema)
class DatabaseSchemaAdmin(admin.ModelAdmin):
    list_display = ['table_name', 'column_name', 'data_type', 'is_nullable', 'updated_at']
    list_filter = ['data_type', 'is_nullable', 'table_name', 'updated_at']
    search_fields = ['table_name', 'column_name']
    readonly_fields = ['updated_at']
    ordering = ['table_name', 'column_name']


@admin.register(QueryLog)
class QueryLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'chat_session', 'is_safe', 'execution_success', 'execution_time', 'created_at']
    list_filter = ['is_safe', 'execution_success', 'created_at', 'user']
    search_fields = ['original_query', 'generated_sql', 'user__username', 'chat_session__title']
    readonly_fields = ['created_at', 'execution_time']
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'chat_session', 'created_at')
        }),
        ('Query Information', {
            'fields': ('original_query', 'generated_sql'),
            'classes': ('collapse',)
        }),
        ('Execution Results', {
            'fields': ('is_safe', 'execution_success', 'error_message', 'execution_time'),
            'classes': ('collapse',)
        }),
    )

    def has_add_permission(self, request):
        return False  # Query logs should only be created automatically


# Customize User admin to show related chat sessions
class ChatSessionInline(admin.TabularInline):
    model = ChatSession
    extra = 0
    readonly_fields = ['created_at', 'updated_at']
    fields = ['title', 'is_active', 'created_at', 'updated_at']


class QueryLogInline(admin.TabularInline):
    model = QueryLog
    extra = 0
    readonly_fields = ['created_at', 'execution_time']
    fields = ['is_safe', 'execution_success', 'execution_time', 'created_at']


# Extend User admin
admin.site.unregister(User)
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    inlines = [ChatSessionInline, QueryLogInline]
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_staff', 'chat_session_count']
    
    def chat_session_count(self, obj):
        return obj.chat_sessions.count()
    chat_session_count.short_description = 'Chat Sessions' 