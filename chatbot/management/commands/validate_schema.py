from django.core.management.base import BaseCommand
from chatbot.schema_manager import SchemaManager
import json


class Command(BaseCommand):
    help = 'Validate the YAML schema file'

    def add_arguments(self, parser):
        parser.add_argument(
            '--schema-file',
            type=str,
            help='Path to the schema YAML file (optional)',
        )
        parser.add_argument(
            '--show-summary',
            action='store_true',
            help='Show detailed schema summary',
        )

    def handle(self, *args, **options):
        schema_file = options.get('schema_file')
        show_summary = options.get('show_summary')

        # Initialize schema manager
        schema_manager = SchemaManager(schema_file)

        self.stdout.write(self.style.SUCCESS('🔍 Validating schema file...'))
        self.stdout.write(f'📁 Schema file: {schema_manager.schema_file_path}')

        # Validate schema file
        is_valid, error_message = schema_manager.validate_schema_file()

        if is_valid:
            self.stdout.write(self.style.SUCCESS('✅ Schema file is valid!'))
            
            if show_summary:
                self.stdout.write('\n📊 Schema Summary:')
                summary = schema_manager.get_schema_summary()
                
                self.stdout.write(f'   File exists: {summary["file_exists"]}')
                self.stdout.write(f'   Tables: {summary["table_count"]}')
                self.stdout.write(f'   Total columns: {summary["total_columns"]}')
                
                if summary['tables']:
                    self.stdout.write('\n📋 Tables:')
                    for table_name, table_info in summary['tables'].items():
                        self.stdout.write(f'   • {table_name} ({table_info["column_count"]} columns)')
                        for column in table_info['columns'][:5]:  # Show first 5 columns
                            self.stdout.write(f'     - {column}')
                        if len(table_info['columns']) > 5:
                            self.stdout.write(f'     ... and {len(table_info["columns"]) - 5} more')
                        self.stdout.write('')
        else:
            self.stdout.write(self.style.ERROR(f'❌ Schema file is invalid: {error_message}'))

        # Test loading schema
        self.stdout.write('\n🔄 Testing schema loading...')
        schema_info = schema_manager.load_schema_from_yaml()
        
        if schema_info:
            self.stdout.write(self.style.SUCCESS(f'✅ Successfully loaded {len(schema_info)} tables'))
        else:
            self.stdout.write(self.style.WARNING('⚠️  No schema information loaded'))

        # Show sample prompt format
        if schema_info and show_summary:
            self.stdout.write('\n📝 Sample prompt format:')
            prompt_schema = schema_manager.get_schema_for_prompt()
            if prompt_schema:
                # Show first table as example
                first_table = list(prompt_schema.keys())[0]
                self.stdout.write(f'Table: {first_table}')
                for column in prompt_schema[first_table][:3]:  # Show first 3 columns
                    nullable = "NULL" if column['is_nullable'] else "NOT NULL"
                    self.stdout.write(f'  - {column["column_name"]}: {column["data_type"]} {nullable}')
                if len(prompt_schema[first_table]) > 3:
                    self.stdout.write(f'  ... and {len(prompt_schema[first_table]) - 3} more columns') 