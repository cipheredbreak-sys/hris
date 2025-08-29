from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp
from django.conf import settings
import os


class Command(BaseCommand):
    help = 'Set up social authentication apps (Google, Microsoft) for django-allauth'

    def add_arguments(self, parser):
        parser.add_argument(
            '--update-site',
            action='store_true',
            help='Update the default site domain and name',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🔧 Setting up social authentication apps...')
        )

        # Update site if requested
        if options['update_site']:
            self.update_site()

        # Setup social apps
        self.setup_google_app()
        self.setup_microsoft_app()

        self.stdout.write(
            self.style.SUCCESS('✅ Social authentication setup completed!')
        )
        self.print_instructions()

    def update_site(self):
        """Update the default site configuration."""
        self.stdout.write('🌐 Updating site configuration...')
        
        site_domain = getattr(settings, 'SITE_DOMAIN', 'localhost:8089')
        
        try:
            site = Site.objects.get(id=1)
            site.domain = site_domain
            site.name = 'HRIS Group Benefits'
            site.save()
            
            self.stdout.write(
                self.style.SUCCESS(f'✓ Updated site: {site.name} ({site.domain})')
            )
        except Site.DoesNotExist:
            site = Site.objects.create(
                id=1,
                domain=site_domain,
                name='HRIS Group Benefits'
            )
            self.stdout.write(
                self.style.SUCCESS(f'✓ Created site: {site.name} ({site.domain})')
            )

    def setup_google_app(self):
        """Set up Google OAuth2 social app."""
        self.stdout.write('📱 Setting up Google OAuth2...')
        
        client_id = getattr(settings, 'GOOGLE_CLIENT_ID', None) or os.getenv('GOOGLE_CLIENT_ID')
        client_secret = getattr(settings, 'GOOGLE_CLIENT_SECRET', None) or os.getenv('GOOGLE_CLIENT_SECRET')
        
        if not client_id or not client_secret:
            self.stdout.write(
                self.style.WARNING(
                    '⚠️  Google OAuth2 credentials not found in settings/environment variables.\n'
                    '   Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET to enable Google login.'
                )
            )
            return

        # Create or update Google social app
        google_app, created = SocialApp.objects.get_or_create(
            provider='google',
            defaults={
                'name': 'Google OAuth2',
                'client_id': client_id,
                'secret': client_secret,
            }
        )

        if not created:
            google_app.client_id = client_id
            google_app.secret = client_secret
            google_app.save()

        # Add all sites to the social app
        google_app.sites.set(Site.objects.all())

        action = 'Created' if created else 'Updated'
        self.stdout.write(
            self.style.SUCCESS(f'✓ {action} Google OAuth2 app')
        )

    def setup_microsoft_app(self):
        """Set up Microsoft OAuth2 social app."""
        self.stdout.write('📱 Setting up Microsoft OAuth2...')
        
        client_id = getattr(settings, 'MS_CLIENT_ID', None) or os.getenv('MS_CLIENT_ID')
        client_secret = getattr(settings, 'MS_CLIENT_SECRET', None) or os.getenv('MS_CLIENT_SECRET')
        
        if not client_id or not client_secret:
            self.stdout.write(
                self.style.WARNING(
                    '⚠️  Microsoft OAuth2 credentials not found in settings/environment variables.\n'
                    '   Set MS_CLIENT_ID and MS_CLIENT_SECRET to enable Microsoft login.'
                )
            )
            return

        # Create or update Microsoft social app
        microsoft_app, created = SocialApp.objects.get_or_create(
            provider='microsoft',
            defaults={
                'name': 'Microsoft OAuth2',
                'client_id': client_id,
                'secret': client_secret,
            }
        )

        if not created:
            microsoft_app.client_id = client_id
            microsoft_app.secret = client_secret
            microsoft_app.save()

        # Add all sites to the social app
        microsoft_app.sites.set(Site.objects.all())

        action = 'Created' if created else 'Updated'
        self.stdout.write(
            self.style.SUCCESS(f'✓ {action} Microsoft OAuth2 app')
        )

    def print_instructions(self):
        """Print setup instructions."""
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('📋 SOCIAL AUTH SETUP INSTRUCTIONS'))
        self.stdout.write('='*60)

        self.stdout.write('\n🔑 ENVIRONMENT VARIABLES NEEDED:')
        self.stdout.write('Add these to your .env file or environment:')
        self.stdout.write('')
        
        # Show current values (masked)
        google_id = getattr(settings, 'GOOGLE_CLIENT_ID', None) or os.getenv('GOOGLE_CLIENT_ID')
        google_secret = getattr(settings, 'GOOGLE_CLIENT_SECRET', None) or os.getenv('GOOGLE_CLIENT_SECRET')
        ms_id = getattr(settings, 'MS_CLIENT_ID', None) or os.getenv('MS_CLIENT_ID')
        ms_secret = getattr(settings, 'MS_CLIENT_SECRET', None) or os.getenv('MS_CLIENT_SECRET')

        # Google OAuth2
        self.stdout.write('# Google OAuth2')
        if google_id:
            masked_id = google_id[:4] + '*' * (len(google_id) - 8) + google_id[-4:]
            self.stdout.write(f'GOOGLE_CLIENT_ID={masked_id}  # ✓ Configured')
        else:
            self.stdout.write('GOOGLE_CLIENT_ID=your_google_client_id_here  # ❌ Not configured')
        
        if google_secret:
            self.stdout.write('GOOGLE_CLIENT_SECRET=***masked***  # ✓ Configured')
        else:
            self.stdout.write('GOOGLE_CLIENT_SECRET=your_google_client_secret_here  # ❌ Not configured')

        self.stdout.write('')

        # Microsoft OAuth2
        self.stdout.write('# Microsoft OAuth2')
        if ms_id:
            masked_id = ms_id[:4] + '*' * (len(ms_id) - 8) + ms_id[-4:]
            self.stdout.write(f'MS_CLIENT_ID={masked_id}  # ✓ Configured')
        else:
            self.stdout.write('MS_CLIENT_ID=your_microsoft_client_id_here  # ❌ Not configured')
        
        if ms_secret:
            self.stdout.write('MS_CLIENT_SECRET=***masked***  # ✓ Configured')
        else:
            self.stdout.write('MS_CLIENT_SECRET=your_microsoft_client_secret_here  # ❌ Not configured')

        self.stdout.write('')

        # Other settings
        self.stdout.write('# Other Settings')
        site_domain = getattr(settings, 'SITE_DOMAIN', 'localhost:8089')
        self.stdout.write(f'SITE_DOMAIN={site_domain}')
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com')
        self.stdout.write(f'DEFAULT_FROM_EMAIL={from_email}')

        self.stdout.write('\n🌐 OAUTH2 SETUP INSTRUCTIONS:')
        self.stdout.write('')
        
        self.stdout.write('📗 GOOGLE OAUTH2 SETUP:')
        self.stdout.write('1. Go to Google Cloud Console: https://console.cloud.google.com/')
        self.stdout.write('2. Create a new project or select existing one')
        self.stdout.write('3. Enable Google+ API')
        self.stdout.write('4. Go to "Credentials" and create "OAuth 2.0 Client ID"')
        self.stdout.write('5. Set authorized redirect URIs:')
        current_domain = Site.objects.get(id=1).domain
        self.stdout.write(f'   - http://{current_domain}/accounts/google/login/callback/')
        self.stdout.write(f'   - https://{current_domain}/accounts/google/login/callback/')
        self.stdout.write('6. Copy Client ID and Client Secret to environment variables')
        self.stdout.write('')

        self.stdout.write('📘 MICROSOFT OAUTH2 SETUP:')
        self.stdout.write('1. Go to Azure Portal: https://portal.azure.com/')
        self.stdout.write('2. Go to "Azure Active Directory" > "App registrations"')
        self.stdout.write('3. Click "New registration"')
        self.stdout.write('4. Set redirect URIs:')
        self.stdout.write(f'   - http://{current_domain}/accounts/microsoft/login/callback/')
        self.stdout.write(f'   - https://{current_domain}/accounts/microsoft/login/callback/')
        self.stdout.write('5. Go to "Certificates & secrets" and create a client secret')
        self.stdout.write('6. Copy Application (client) ID and secret to environment variables')
        self.stdout.write('')

        self.stdout.write('🔄 AFTER SETUP:')
        self.stdout.write('1. Restart your Django server')
        self.stdout.write('2. Run: python manage.py setup_social_apps --update-site')
        self.stdout.write('3. Test login at: /accounts/login/')
        self.stdout.write('')

        # Show current status
        apps_configured = 0
        total_apps = 0
        
        for provider in ['google', 'microsoft']:
            total_apps += 1
            if SocialApp.objects.filter(provider=provider).exists():
                apps_configured += 1

        self.stdout.write(f'📊 STATUS: {apps_configured}/{total_apps} social apps configured')
        
        if apps_configured == total_apps:
            self.stdout.write(self.style.SUCCESS('🎉 All social authentication apps are ready!'))
        else:
            self.stdout.write(
                self.style.WARNING(
                    f'⚠️  {total_apps - apps_configured} apps still need configuration'
                )
            )

        self.stdout.write('\n' + '='*60)