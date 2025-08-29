from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from accounts.models import UserProfile, Organization
from django.db import transaction

class Command(BaseCommand):
    help = 'Create test users for each persona type'

    def handle(self, *args, **options):
        self.stdout.write('Creating test users for each persona...')
        
        with transaction.atomic():
            # Create Organizations
            organizations = {}
            
            # Create Broker Organization
            broker_org, created = Organization.objects.get_or_create(
                name="TestBroker Insurance Group",
                defaults={
                    'type': 'broker',
                    'is_active': True
                }
            )
            organizations['broker'] = broker_org
            if created:
                self.stdout.write(f'Created broker organization: {broker_org.name}')

            # Create Employer Organization
            employer_org, created = Organization.objects.get_or_create(
                name="TechCorp Solutions",
                defaults={
                    'type': 'employer',
                    'is_active': True
                }
            )
            organizations['employer'] = employer_org
            if created:
                self.stdout.write(f'Created employer organization: {employer_org.name}')

            # Create Carrier Organization
            carrier_org, created = Organization.objects.get_or_create(
                name="HealthGuard Insurance",
                defaults={
                    'type': 'carrier',
                    'is_active': True
                }
            )
            organizations['carrier'] = carrier_org
            if created:
                self.stdout.write(f'Created carrier organization: {carrier_org.name}')

            # Test user data with specific credentials and personas
            test_users = [
                {
                    'username': 'superadmin@test.com',
                    'email': 'superadmin@test.com',
                    'password': 'SuperAdmin123!',
                    'first_name': 'System',
                    'last_name': 'Administrator',
                    'role': 'super_admin',
                    'organization': None,
                    'is_superuser': True,
                    'is_staff': True,
                    'description': 'Full system access, can manage all organizations and users'
                },
                {
                    'username': 'brokeradmin@test.com',
                    'email': 'brokeradmin@test.com',
                    'password': 'BrokerAdmin123!',
                    'first_name': 'Sarah',
                    'last_name': 'Johnson',
                    'role': 'broker_admin',
                    'organization': organizations['broker'],
                    'description': 'Manages broker operations, client relationships, and enrollment processes'
                },
                {
                    'username': 'brokeruser@test.com',
                    'email': 'brokeruser@test.com',
                    'password': 'BrokerUser123!',
                    'first_name': 'Mike',
                    'last_name': 'Rodriguez',
                    'role': 'broker_user',
                    'organization': organizations['broker'],
                    'description': 'Handles day-to-day broker tasks, client support, and enrollment assistance'
                },
                {
                    'username': 'employeradmin@test.com',
                    'email': 'employeradmin@test.com',
                    'password': 'EmployerAdmin123!',
                    'first_name': 'Jennifer',
                    'last_name': 'Chen',
                    'role': 'employer_admin',
                    'organization': organizations['employer'],
                    'description': 'Manages company benefits program, employee enrollment, and HR integration'
                },
                {
                    'username': 'hruser@test.com',
                    'email': 'hruser@test.com',
                    'password': 'HRUser123!',
                    'first_name': 'David',
                    'last_name': 'Thompson',
                    'role': 'employer_hr',
                    'organization': organizations['employer'],
                    'description': 'HR representative who assists with employee benefits questions and enrollment'
                },
                {
                    'username': 'carrieradmin@test.com',
                    'email': 'carrieradmin@test.com',
                    'password': 'CarrierAdmin123!',
                    'first_name': 'Lisa',
                    'last_name': 'Williams',
                    'role': 'carrier_admin',
                    'organization': organizations['carrier'],
                    'description': 'Insurance carrier representative managing plan details and eligibility'
                },
                {
                    'username': 'employee@test.com',
                    'email': 'employee@test.com',
                    'password': 'Employee123!',
                    'first_name': 'John',
                    'last_name': 'Smith',
                    'role': 'employee',
                    'organization': organizations['employer'],
                    'description': 'Regular employee who can view and enroll in benefits'
                },
                {
                    'username': 'guest@test.com',
                    'email': 'guest@test.com',
                    'password': 'Guest123!',
                    'first_name': 'Guest',
                    'last_name': 'User',
                    'role': 'guest',
                    'organization': None,
                    'description': 'Limited access user for demonstrations or temporary access'
                },
                {
                    'username': 'apiuser@test.com',
                    'email': 'apiuser@test.com',
                    'password': 'ApiUser123!',
                    'first_name': 'API',
                    'last_name': 'Integration',
                    'role': 'api_user',
                    'organization': organizations['broker'],
                    'description': 'System integration user for API access and automated processes'
                }
            ]

            # Create test users
            created_count = 0
            for user_data in test_users:
                user, created = User.objects.get_or_create(
                    username=user_data['username'],
                    defaults={
                        'email': user_data['email'],
                        'first_name': user_data['first_name'],
                        'last_name': user_data['last_name'],
                        'is_superuser': user_data.get('is_superuser', False),
                        'is_staff': user_data.get('is_staff', False),
                        'is_active': True,
                    }
                )
                
                if created:
                    user.set_password(user_data['password'])
                    user.save()
                    created_count += 1
                
                # Create or update user profile
                profile, profile_created = UserProfile.objects.get_or_create(
                    user=user,
                    defaults={
                        'role': user_data['role'],
                        'organization': user_data['organization'],
                        'phone': f"(555) {user_data['role'][:3]}-{hash(user_data['username']) % 10000:04d}"
                    }
                )
                
                if profile_created or created:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✓ Created user: {user_data["username"]} ({user_data["role"]})'
                        )
                    )

            self.stdout.write('\n' + '='*80)
            self.stdout.write(self.style.SUCCESS(f'Successfully created {created_count} test users!'))
            self.stdout.write('='*80 + '\n')
            
            # Print login credentials and persona descriptions
            self.stdout.write(self.style.WARNING('TEST LOGIN CREDENTIALS:'))
            self.stdout.write('-'*80)
            
            for user_data in test_users:
                self.stdout.write(f"\n{user_data['role'].upper().replace('_', ' ')}:")
                self.stdout.write(f"  Email/Username: {user_data['username']}")
                self.stdout.write(f"  Password: {user_data['password']}")
                self.stdout.write(f"  Name: {user_data['first_name']} {user_data['last_name']}")
                if user_data['organization']:
                    self.stdout.write(f"  Organization: {user_data['organization'].name}")
                self.stdout.write(f"  Description: {user_data['description']}")

            self.stdout.write('\n' + '='*80)
            self.stdout.write(self.style.SUCCESS('All test users are ready for login testing!'))
            self.stdout.write('='*80)