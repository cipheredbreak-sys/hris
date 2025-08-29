from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from accounts.models import Organization, UserProfile

class Command(BaseCommand):
    help = 'Create admin user and sample data'

    def handle(self, *args, **options):
        # Create superuser if it doesn't exist
        if not User.objects.filter(username='admin').exists():
            admin_user = User.objects.create_superuser(
                username='admin',
                email='admin@hris.com',
                password='admin123',
                first_name='Admin',
                last_name='User'
            )
            
            # Create a broker organization
            broker_org, created = Organization.objects.get_or_create(
                name='Demo Broker Organization',
                defaults={'type': 'broker'}
            )
            
            # Create admin profile
            UserProfile.objects.get_or_create(
                user=admin_user,
                defaults={
                    'role': 'super_admin',
                    'organization': broker_org,
                    'title': 'System Administrator'
                }
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created admin user: admin / admin123')
            )
        else:
            self.stdout.write(
                self.style.WARNING('Admin user already exists')
            )

        # Create sample organizations
        sample_orgs = [
            {'name': 'ABC Corporation', 'type': 'employer'},
            {'name': 'Tech Startup Inc', 'type': 'employer'},
            {'name': 'Blue Cross Blue Shield', 'type': 'carrier'},
            {'name': 'Aetna', 'type': 'carrier'},
        ]

        for org_data in sample_orgs:
            org, created = Organization.objects.get_or_create(
                name=org_data['name'],
                defaults={'type': org_data['type']}
            )
            if created:
                self.stdout.write(f'Created organization: {org.name}')

        # Create sample users
        sample_users = [
            {
                'username': 'broker_admin',
                'email': 'broker@demo.com',
                'password': 'demo123',
                'first_name': 'Broker',
                'last_name': 'Admin',
                'role': 'broker_admin',
                'title': 'Senior Broker'
            },
            {
                'username': 'employer_admin',
                'email': 'employer@demo.com',
                'password': 'demo123',
                'first_name': 'HR',
                'last_name': 'Manager',
                'role': 'employer_admin',
                'title': 'HR Director'
            },
            {
                'username': 'employee_demo',
                'email': 'employee@demo.com',
                'password': 'demo123',
                'first_name': 'John',
                'last_name': 'Doe',
                'role': 'employee',
                'title': 'Software Engineer'
            }
        ]

        broker_org = Organization.objects.filter(type='broker').first()
        employer_org = Organization.objects.filter(type='employer').first()
        
        if not broker_org:
            self.stdout.write(self.style.WARNING('No broker organization found, skipping sample users'))
            return

        for user_data in sample_users:
            if not User.objects.filter(username=user_data['username']).exists():
                user = User.objects.create_user(
                    username=user_data['username'],
                    email=user_data['email'],
                    password=user_data['password'],
                    first_name=user_data['first_name'],
                    last_name=user_data['last_name']
                )
                
                org = broker_org if 'broker' in user_data['role'] else employer_org
                
                UserProfile.objects.create(
                    user=user,
                    role=user_data['role'],
                    organization=org,
                    title=user_data['title']
                )
                
                self.stdout.write(f'Created user: {user.username}')

        self.stdout.write(
            self.style.SUCCESS('Sample data created successfully!')
        )