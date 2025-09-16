"""
Management command to seed the database with sample data for development.
Replace 'your_main_app' in the file path with your actual Django app name.
"""

from django.core.management.base import BaseCommand
from users.models import User
from django.core.management import call_command
from django.db import transaction
import os

class Command(BaseCommand):
    help = 'Seed database with sample data for development environment'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--no-fixtures',
            action='store_true',
            help='Skip loading fixtures, only create basic data',
        )
        
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force recreate sample data even if it exists',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Starting database seeding for development...')
        )

        try:
            with transaction.atomic():
                # Create development superuser
                self.create_superuser(options['force'])
                
                # Load fixtures if available and requested
                if not options['no_fixtures']:
                    self.load_fixtures()
                
                # Create additional sample data
                self.create_sample_data(options['force'])
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error during database seeding: {str(e)}')
            )
            raise
        
        self.stdout.write(
            self.style.SUCCESS('Database seeding completed successfully!')
        )
        self.stdout.write('   Login credentials:')
        self.stdout.write('   Username: admin')
        self.stdout.write('   Password: admin123')
        self.stdout.write('   Email: admin@example.com')

    def create_superuser(self, force=False):
        """Create a development superuser"""
        username = 'admin'
        
        if User.objects.filter(username=username).exists():
            if force:
                User.objects.filter(username=username).delete()
                self.stdout.write('Existing admin user deleted')
            else:
                self.stdout.write('Admin user already exists')
                return
        
        User.objects.create_superuser(
            username=username,
            email='admin@example.com',
            password='admin123',
            role="admin"
        )
        self.stdout.write('Created development admin user')

    def load_fixtures(self):
        """Load fixture files if they exist"""
        fixtures_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'fixtures')
        
        fixture_files = [
            'users.json',
            'sample_data.json',
            'initial_data.json'
        ]
        
        loaded_any = False
        
        for fixture_file in fixture_files:
            fixture_path = os.path.join(fixtures_dir, fixture_file)
            if os.path.exists(fixture_path):
                try:
                    call_command('loaddata', fixture_file, verbosity=0)
                    self.stdout.write(f'Loaded fixture: {fixture_file}')
                    loaded_any = True
                except Exception as e:
                    self.stdout.write(f'Failed to load fixture {fixture_file}: {str(e)}')
        
        if not loaded_any:
            self.stdout.write('No fixture files found to load')

    def create_sample_data(self, force=False):
        """Create sample data programmatically"""
        
        # Add your custom sample data creation here
        # Example:
        
        # from your_app.models import YourModel
        
        # if not YourModel.objects.exists() or force:
        #     if force:
        #         YourModel.objects.all().delete()
        #     
        #     sample_items = [
        #         {'name': 'Sample Item 1', 'description': 'First sample item'},
        #         {'name': 'Sample Item 2', 'description': 'Second sample item'},
        #         {'name': 'Sample Item 3', 'description': 'Third sample item'},
        #     ]
        #     
        #     for item_data in sample_items:
        #         YourModel.objects.create(**item_data)
        #     
        #     self.stdout.write(f'Created {len(sample_items)} sample items')
        # else:
        #     self.stdout.write('Sample data already exists')
        
        # Create test users
        self.create_test_users(force)

    def create_test_users(self, force=False):
        """Create test users for development"""
        test_users = [
            {'username': 'testuser1', 'email': 'test1@example.com', 'first_name': 'Test', 'last_name': 'User One', 'role':'engineer'},
            {'username': 'testuser2', 'email': 'test2@example.com', 'first_name': 'Test', 'last_name': 'User Two', 'role':'scientist'},
        ]
        
        created_count = 0
        
        for user_data in test_users:
            username = user_data['username']
            
            if User.objects.filter(username=username).exists():
                if force:
                    User.objects.filter(username=username).delete()
                else:
                    continue
            
            User.objects.create_user(
                username=user_data['username'],
                email=user_data['email'],
                password='testpass123',
                first_name=user_data['first_name'],
                last_name=user_data['last_name'],
                role=user_data['role']
            )
            created_count += 1
        
        if created_count > 0:
            self.stdout.write(f'Created {created_count} test users')
        else:
            self.stdout.write('Test users already exist')