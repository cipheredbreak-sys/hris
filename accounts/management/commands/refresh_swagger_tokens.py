from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken
from datetime import timedelta
import os

class Command(BaseCommand):
    help = 'Refresh tokens in Swagger settings automatically'

    def handle(self, *args, **options):
        try:
            # Get users
            super_admin = User.objects.get(email='superadmin@test.com')
            employee = User.objects.get(email='employee@test.com')
            
            # Generate new tokens
            super_admin_refresh = RefreshToken.for_user(super_admin)
            super_admin_refresh.set_exp(lifetime=timedelta(days=30))
            super_admin_token = super_admin_refresh.access_token
            super_admin_token.set_exp(lifetime=timedelta(days=30))
            
            employee_refresh = RefreshToken.for_user(employee)
            employee_refresh.set_exp(lifetime=timedelta(days=30))
            employee_token = employee_refresh.access_token
            employee_token.set_exp(lifetime=timedelta(days=30))
            
            # Read current settings.py
            settings_path = '/Users/jeanpierre-louis/Desktop/hris/group_benefits_backend/settings.py'
            
            with open(settings_path, 'r') as file:
                content = file.read()
            
            # Find and replace tokens in SWAGGER_SETTINGS
            import re
            
            # Replace super admin token
            super_admin_pattern = r'(Bearer eyJ[^`\n]*?)(?=```\n\n\*\*👤 EMPLOYEE)'
            new_super_admin = f'Bearer {str(super_admin_token)}'
            content = re.sub(super_admin_pattern, new_super_admin, content, flags=re.DOTALL)
            
            # Replace employee token
            employee_pattern = r'(\*\*👤 EMPLOYEE \(Limited Access\):\*\*\n```\nBearer )(eyJ[^`\n]*?)(?=```)'
            new_employee = f'\\1{str(employee_token)}'
            content = re.sub(employee_pattern, new_employee, content)
            
            # Write back to file
            with open(settings_path, 'w') as file:
                file.write(content)
            
            self.stdout.write('='*80)
            self.stdout.write(self.style.SUCCESS('✅ Swagger tokens refreshed!'))
            self.stdout.write('='*80)
            self.stdout.write(f'🔑 New Super Admin Token: Bearer {str(super_admin_token)}')
            self.stdout.write(f'👤 New Employee Token: Bearer {str(employee_token)}')
            self.stdout.write('='*80)
            self.stdout.write('🔄 Django server will auto-reload with new tokens')
            self.stdout.write('📖 Visit http://localhost:8000/swagger/ to use updated tokens')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error refreshing tokens: {str(e)}')
            )