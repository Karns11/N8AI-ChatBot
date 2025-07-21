from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from chatbot.models import ChatSession, Message, QueryLog


class Command(BaseCommand):
    help = 'Delete all chat sessions and related data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user',
            type=str,
            help='Delete chats for specific user (username)',
        )
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Skip confirmation prompt',
        )

    def handle(self, *args, **options):
        username = options.get('user')
        confirm = options.get('confirm')
        
        if username:
            try:
                user = User.objects.get(username=username)  # type: ignore
                chat_sessions = ChatSession.objects.filter(user=user)  # type: ignore
                self.stdout.write(f"Found {chat_sessions.count()} chat sessions for user '{username}'")
            except User.DoesNotExist:  # type: ignore
                self.stdout.write(self.style.ERROR(f"User '{username}' not found"))  # type: ignore
                return
        else:
            chat_sessions = ChatSession.objects.all()  # type: ignore
            self.stdout.write(f"Found {chat_sessions.count()} total chat sessions")
        
        if not confirm:
            response = input("Are you sure you want to delete all chat sessions? (yes/no): ")
            if response.lower() != 'yes':
                self.stdout.write("Operation cancelled.")
                return
        
        # Delete related data first
        chat_ids = list(chat_sessions.values_list('id', flat=True))
        if not chat_ids:
            self.stdout.write(self.style.WARNING('No chat sessions to delete.'))  # type: ignore
            return
        # Delete messages
        messages_deleted = Message.objects.filter(chat_session_id__in=chat_ids).delete()[0]  # type: ignore
        self.stdout.write(f"Deleted {messages_deleted} messages")
        
        # Delete query logs
        query_logs_deleted = QueryLog.objects.filter(chat_session_id__in=chat_ids).delete()[0]  # type: ignore
        self.stdout.write(f"Deleted {query_logs_deleted} query logs")
        
        # Delete chat sessions
        chats_deleted = chat_sessions.delete()[0]  # type: ignore
        self.stdout.write(f"Deleted {chats_deleted} chat sessions")
        
        self.stdout.write(
            self.style.SUCCESS(  # type: ignore
                f"Successfully deleted all chat data: {chats_deleted} chats, {messages_deleted} messages, {query_logs_deleted} query logs"
            )  # type: ignore
        )  # type: ignore 