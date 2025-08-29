from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.utils import user_email
from django.conf import settings
from django.contrib.auth import get_user_model
from .models import AuditEvent, Membership, Organization, Role

User = get_user_model()


class AccountAdapter(DefaultAccountAdapter):
    """
    Custom account adapter for django-allauth.
    Handles email verification, domain allowlists, and security controls.
    """

    def is_open_for_signup(self, request):
        """
        Control whether new signups are allowed.
        Can be customized based on domain, invitation codes, etc.
        """
        return True  # Allow open registration for now
    
    def get_email_confirmation_url(self, request, emailconfirmation):
        """
        Customize email confirmation URL if needed.
        """
        url = super().get_email_confirmation_url(request, emailconfirmation)
        return url
    
    def send_mail(self, template_prefix, email, context):
        """
        Override to customize email sending behavior.
        Could add custom templates, logging, etc.
        """
        # Log invitation sent
        if template_prefix == 'account/email/email_confirmation':
            AuditEvent.objects.create(
                event='invitation_sent',
                ip_address=self.get_client_ip(context.get('request')),
                user_agent=self.get_user_agent(context.get('request')),
                metadata={
                    'email': email,
                    'template': template_prefix
                }
            )
        
        return super().send_mail(template_prefix, email, context)
    
    def clean_email(self, email):
        """
        Validate and clean email address.
        Could add domain allowlists/blocklists here.
        """
        email = super().clean_email(email)
        
        # Example: Block certain domains (optional)
        blocked_domains = getattr(settings, 'BLOCKED_EMAIL_DOMAINS', [])
        domain = email.split('@')[1].lower() if '@' in email else ''
        
        if domain in blocked_domains:
            from django.core.exceptions import ValidationError
            raise ValidationError(f"Email domain '{domain}' is not allowed.")
        
        return email
    
    def save_user(self, request, user, form, commit=True):
        """
        Save user and create audit event.
        """
        user = super().save_user(request, user, form, commit=commit)
        
        if commit:
            # Create audit event for signup
            AuditEvent.objects.create(
                user=user,
                event='signup',
                ip_address=self.get_client_ip(request),
                user_agent=self.get_user_agent(request),
                metadata={
                    'email': user.email,
                    'signup_method': 'email'
                }
            )
        
        return user
    
    def get_client_ip(self, request):
        """Extract client IP address from request."""
        if not request:
            return None
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def get_user_agent(self, request):
        """Extract user agent from request."""
        if not request:
            return None
        return request.META.get('HTTP_USER_AGENT', '')


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Custom social account adapter for handling Google/Microsoft OAuth.
    Manages account linking, email verification, and audit logging.
    """

    def is_open_for_signup(self, request, sociallogin):
        """
        Control whether new signups via social accounts are allowed.
        """
        return True
    
    def pre_social_login(self, request, sociallogin):
        """
        Handle logic before social login.
        Link existing accounts if email matches.
        """
        # If user is already authenticated, we're linking accounts
        if request.user.is_authenticated:
            return
        
        # Try to link to existing user by email
        email = user_email(sociallogin.user)
        if email:
            try:
                existing_user = User.objects.get(email=email)
                sociallogin.connect(request, existing_user)
                
                # Create audit event for social account linking
                AuditEvent.objects.create(
                    user=existing_user,
                    event='social_account_added',
                    ip_address=self.get_client_ip(request),
                    user_agent=self.get_user_agent(request),
                    metadata={
                        'provider': sociallogin.account.provider,
                        'email': email
                    }
                )
            except User.DoesNotExist:
                # New user - will be handled in save_user
                pass
    
    def save_user(self, request, sociallogin, form=None):
        """
        Save social user and create audit event.
        """
        user = super().save_user(request, sociallogin, form)
        
        # Create audit event for social signup
        AuditEvent.objects.create(
            user=user,
            event='signup',
            ip_address=self.get_client_ip(request),
            user_agent=self.get_user_agent(request),
            metadata={
                'email': user.email,
                'signup_method': 'social',
                'provider': sociallogin.account.provider
            }
        )
        
        return user
    
    def populate_user(self, request, sociallogin, data):
        """
        Populate user fields from social account data.
        """
        user = super().populate_user(request, sociallogin, data)
        
        # Extract additional data from social providers
        if sociallogin.account.provider == 'google':
            extra_data = sociallogin.account.extra_data
            user.first_name = extra_data.get('given_name', '')
            user.last_name = extra_data.get('family_name', '')
        elif sociallogin.account.provider == 'microsoft':
            extra_data = sociallogin.account.extra_data
            user.first_name = extra_data.get('givenName', '')
            user.last_name = extra_data.get('surname', '')
        
        return user
    
    def get_client_ip(self, request):
        """Extract client IP address from request."""
        if not request:
            return None
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def get_user_agent(self, request):
        """Extract user agent from request."""
        if not request:
            return None
        return request.META.get('HTTP_USER_AGENT', '')