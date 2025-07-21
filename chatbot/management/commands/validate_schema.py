from django.core.management.base import BaseCommand
from chatbot.schema_manager import SchemaManager
import json
from chatbot.models import Message


class Command(BaseCommand):
    help = 'Validate schema (TEMP: print latest assistant message with chart)'

    def handle(self, *args, **options):
        msg = Message.objects.filter(role='assistant', show_chart=True).order_by('-created_at').first()
        if msg:
            print('chart_data:', msg.chart_data)
            print('show_chart:', msg.show_chart)
            print('content:', msg.content)
        else:
            print('No assistant message with show_chart=True found.') 