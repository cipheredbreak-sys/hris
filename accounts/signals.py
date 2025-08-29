from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from allauth.account.signals import user_signed_up, email_confirmed
from allauth.socialaccount.signals import social_account_added, social_account_removed
from django.contrib.auth import get_user_model
from .models import AuditEvent, Membership, Organization, Role

User = get_user_model()


def get_client_ip(request):
    """Extract client IP address from request."""
    if not request:
        return None
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_user_agent(request):
    """Extract user agent from request."""
    if not request:
        return None
    return request.META.get('HTTP_USER_AGENT', '')


@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    """
    Log user login events for audit trail.
    """
    AuditEvent.objects.create(
        user=user,
        event='login',
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        metadata={
            'email': user.email,
            'login_method': 'session'
        }
    )


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    """
    Log user logout events for audit trail.
    """
    if user and hasattr(user, 'email'):  # user might be AnonymousUser
        AuditEvent.objects.create(
            user=user,
            event='logout',
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            metadata={
                'email': user.email
            }
        )


@receiver(user_signed_up)
def handle_user_signup(sender, request, user, **kwargs):
    """
    Handle post-signup logic.
    Create default membership if invitation exists or auto-assign organization.
    """
    # Check if there's a pending invitation or organization assignment
    # This could be stored in session or database
    
    # For now, we'll create a basic employee membership if no organization exists
    # In production, this should be invitation-based
    
    # Create audit event (already handled by adapters, but keeping for completeness)
    AuditEvent.objects.create(
        user=user,
        event='signup',
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        metadata={
            'email': user.email,
            'signup_completed': True
        }
    )


@receiver(email_confirmed)
def handle_email_confirmation(sender, request, email_address, **kwargs):
    """
    Handle email confirmation.
    Mark user as verified and potentially activate memberships.
    """
    user = email_address.user
    
    AuditEvent.objects.create(
        user=user,
        event='email_verified',
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        metadata={
            'email': email_address.email,
            'verified': True
        }
    )


@receiver(social_account_added)
def handle_social_account_added(sender, request, sociallogin, **kwargs):
    """
    Handle social account linking.
    """
    user = sociallogin.user
    
    AuditEvent.objects.create(
        user=user,
        event='social_account_added',
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        metadata={
            'provider': sociallogin.account.provider,
            'email': user.email,
            'provider_uid': sociallogin.account.uid
        }
    )


@receiver(social_account_removed)
def handle_social_account_removed(sender, request, socialaccount, **kwargs):
    """
    Handle social account unlinking.
    """
    user = socialaccount.user
    
    AuditEvent.objects.create(
        user=user,
        event='social_account_removed',
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        metadata={
            'provider': socialaccount.provider,
            'email': user.email,
            'provider_uid': socialaccount.uid
        }
    )


@receiver(post_save, sender=Membership)
def handle_membership_created(sender, instance, created, **kwargs):
    """
    Handle membership creation and updates.
    Log role changes and sync group permissions.
    """
    if created:
        AuditEvent.objects.create(
            user=instance.user,
            event='membership_created',
            organization=instance.organization,
            metadata={
                'role': instance.role,
                'organization': instance.organization.name,
                'user_email': instance.user.email
            }
        )
    else:
        # Check if role was changed
        try:
            old_instance = Membership.objects.get(pk=instance.pk)
            if old_instance.role != instance.role:
                AuditEvent.objects.create(
                    user=instance.user,
                    event='role_change',
                    organization=instance.organization,
                    metadata={
                        'old_role': old_instance.role,
                        'new_role': instance.role,
                        'organization': instance.organization.name,
                        'user_email': instance.user.email
                    }
                )
        except Membership.DoesNotExist:
            # This shouldn't happen, but just in case
            pass


@receiver(post_delete, sender=Membership)
def handle_membership_deleted(sender, instance, **kwargs):
    """
    Handle membership deletion.
    """
    AuditEvent.objects.create(
        user=instance.user,
        event='membership_deleted',
        organization=instance.organization,
        metadata={
            'role': instance.role,
            'organization': instance.organization.name,
            'user_email': instance.user.email
        }
    )