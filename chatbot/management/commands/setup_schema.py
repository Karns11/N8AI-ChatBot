from django.core.management.base import BaseCommand
from chatbot.utils import DatabaseManager
from chatbot.models import DatabaseSchema


class Command(BaseCommand):
    help = 'Set up database schema cache for the chatbot'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force update even if schema cache exists',
        )

    def handle(self, *args, **options):
        self.stdout.write('Setting up database schema cache...')
        
        try:
            # Check if schema cache exists
            if DatabaseSchema.objects.exists() and not options['force']:
                self.stdout.write(
                    self.style.WARNING(
                        'Schema cache already exists. Use --force to update.'
                    )
                )
                return
            
            # Update schema cache
            DatabaseManager.update_schema_cache()
            
            # Count cached schemas
            schema_count = DatabaseSchema.objects.count()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully cached schema for {schema_count} columns'
                )
            )
            
            # Show some statistics
            tables = DatabaseSchema.objects.values_list('table_name', flat=True).distinct()
            self.stdout.write(f'Tables found: {", ".join(tables)}')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error setting up schema cache: {str(e)}')
            ) 