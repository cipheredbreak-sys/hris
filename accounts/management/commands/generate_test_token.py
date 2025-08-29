from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken
from datetime import timedelta
from rest_framework_simplejwt.settings import api_settings
import pytz
from django.utils import timezone

class Command(BaseCommand):
    help = 'Generate long-lived JWT tokens for testing API endpoints'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user',
            type=str,
            help='Username or email of the user to generate token for (default: superadmin@test.com)',
            default='superadmin@test.com'
        )
        parser.add_argument(
            '--days',
            type=int,
            help='Token lifetime in days (default: 30)',
            default=30
        )

    def handle(self, *args, **options):
        username = options['user']
        days = options['days']
        
        try:
            # Try to get user by email first, then by username
            try:
                user = User.objects.get(email=username)
            except User.DoesNotExist:
                user = User.objects.get(username=username)
                
            # Generate tokens
            refresh = RefreshToken.for_user(user)
            
            # Extend token lifetime for testing
            refresh.set_exp(lifetime=timedelta(days=days))
            access_token = refresh.access_token
            access_token.set_exp(lifetime=timedelta(days=days))
            
            self.stdout.write('='*80)
            self.stdout.write(self.style.SUCCESS(f'🎯 TEST TOKENS GENERATED FOR: {user.email}'))
            self.stdout.write('='*80)
            self.stdout.write(f'User: {user.get_full_name()} ({user.email})')
            self.stdout.write(f'Role: {getattr(user.profile, "role", "N/A")}')
            self.stdout.write(f'Organization: {getattr(user.profile, "organization", "N/A")}')
            self.stdout.write(f'Token Lifetime: {days} days')
            self.stdout.write('-'*80)
            
            self.stdout.write('\n🔑 ACCESS TOKEN (Use this for API testing):')
            self.stdout.write(self.style.WARNING(str(access_token)))
            
            self.stdout.write('\n🔄 REFRESH TOKEN (Use to get new access tokens):')
            self.stdout.write(self.style.WARNING(str(refresh)))
            
            self.stdout.write('\n📋 HOW TO USE:')
            self.stdout.write('1. Copy the ACCESS TOKEN above')
            self.stdout.write('2. In Swagger UI (http://localhost:8000/swagger/):')
            self.stdout.write('   - Click "Authorize" button')
            self.stdout.write('   - Enter: Bearer <ACCESS_TOKEN>')
            self.stdout.write('   - Click "Authorize"')
            self.stdout.write('\n3. For curl/API testing:')
            self.stdout.write('   curl -H "Authorization: Bearer <ACCESS_TOKEN>" http://localhost:8000/api/users/')
            self.stdout.write('\n4. For Postman/Insomnia:')
            self.stdout.write('   - Add header: Authorization: Bearer <ACCESS_TOKEN>')
            
            self.stdout.write('\n' + '='*80)
            self.stdout.write(self.style.SUCCESS('✅ Tokens ready for testing!'))
            self.stdout.write('='*80)
            
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'❌ User not found: {username}')
            )
            self.stdout.write('\n📋 Available test users:')
            test_users = User.objects.filter(email__contains='@test.com').values_list('email', 'first_name', 'last_name')
            for email, first_name, last_name in test_users:
                self.stdout.write(f'  - {email} ({first_name} {last_name})')
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error generating token: {str(e)}')
            )