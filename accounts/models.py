from django.contrib.auth.models import AbstractUser, Group
from django.db import models
from django.utils.text import slugify


class User(AbstractUser):
    """
    Custom User model with email as username field.
    Replaces Django's default User model.
    """
    username = None
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    def __str__(self):
        return self.email


class Organization(models.Model):
    """
    Organization model representing tenants in the system.
    Each user belongs to one or more organizations through Membership.
    """
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Organization"
        verbose_name_plural = "Organizations"


class Role(models.TextChoices):
    """
    Role enumeration for RBAC system.
    Maps to Django Groups for permission management.
    """
    SUPERUSER = "superuser", "Superuser"
    BROKER_ADMIN = "broker_admin", "Broker Admin"
    EMPLOYER_ADMIN = "employer_admin", "Employer Admin"
    EMPLOYEE = "employee", "Employee"


class Membership(models.Model):
    """
    Many-to-many relationship between User and Organization with role.
    Enforces per-tenant access control.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='memberships')
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='memberships')
    role = models.CharField(max_length=32, choices=Role.choices)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "organization")
        verbose_name = "Membership"
        verbose_name_plural = "Memberships"

    def __str__(self):
        return f"{self.user.email} - {self.organization.name} ({self.get_role_display()})"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Sync user to appropriate Django group
        self._sync_user_groups()

    def _sync_user_groups(self):
        """
        Sync user's group membership based on their roles.
        Adds user to Django group corresponding to their role.
        """
        try:
            group = Group.objects.get(name=self.role)
            self.user.groups.add(group)
        except Group.DoesNotExist:
            # Group will be created by management command
            pass


class AuditEvent(models.Model):
    """
    Audit trail for important security and business events.
    """
    EVENT_CHOICES = [
        ('login', 'User Login'),
        ('logout', 'User Logout'),
        ('signup', 'User Signup'),
        ('password_change', 'Password Change'),
        ('email_change', 'Email Change'),
        ('role_change', 'Role Change'),
        ('membership_created', 'Membership Created'),
        ('membership_deleted', 'Membership Deleted'),
        ('social_account_added', 'Social Account Added'),
        ('social_account_removed', 'Social Account Removed'),
        ('invitation_sent', 'Invitation Sent'),
        ('invitation_accepted', 'Invitation Accepted'),
        ('data_export', 'Data Export'),
        ('permission_denied', 'Permission Denied'),
    ]

    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    event = models.CharField(max_length=64, choices=EVENT_CHOICES)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    organization = models.ForeignKey(Organization, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Audit Event"
        verbose_name_plural = "Audit Events"

    def __str__(self):
        user_info = self.user.email if self.user else "Anonymous"
        return f"{user_info} - {self.get_event_display()} - {self.created_at}"


# Compatibility models for existing data
class UserProfile(models.Model):
    """
    Legacy model maintained for backward compatibility.
    New implementations should use Membership model instead.
    """
    ROLE_CHOICES = [
        ('super_admin', 'Super Admin'),
        ('broker_admin', 'Broker Admin'),
        ('broker_user', 'Broker User'),
        ('employer_admin', 'Employer Admin'),
        ('employer_hr', 'Employer HR'),
        ('employee', 'Employee'),
        ('carrier_admin', 'Carrier Admin'),
        ('carrier_user', 'Carrier User'),
        ('readonly_user', 'Readonly User'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='legacy_profile')
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default='employee')
    title = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    timezone = models.CharField(max_length=50, default='UTC')
    language = models.CharField(max_length=10, default='en')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_role_display()}"

    class Meta:
        verbose_name = "Legacy User Profile"
        verbose_name_plural = "Legacy User Profiles"


class LegacyOrganization(models.Model):
    """
    Legacy organization model maintained for backward compatibility.
    """
    ORGANIZATION_TYPES = [
        ('broker', 'Broker'),
        ('employer', 'Employer'), 
        ('carrier', 'Carrier'),
    ]
    
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=20, choices=ORGANIZATION_TYPES)
    parent_organization = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Legacy Organization"
        verbose_name_plural = "Legacy Organizations"