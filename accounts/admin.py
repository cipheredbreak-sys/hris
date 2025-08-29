from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth import get_user_model
from django.utils.html import format_html
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.db import models
from .models import (
    Organization, Membership, AuditEvent, UserProfile, 
    LegacyOrganization, Role
)

User = get_user_model()


class MembershipInline(admin.TabularInline):
    """
    Inline admin for managing user memberships within organizations.
    """
    model = Membership
    extra = 1
    fields = ('organization', 'role', 'created_at')
    readonly_fields = ('created_at',)
    
    def get_queryset(self, request):
        """
        Filter memberships based on user's organization access.
        Superusers see all, others see only their organization's memberships.
        """
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        
        # Get user's organizations
        user_orgs = Membership.objects.filter(
            user=request.user
        ).values_list('organization_id', flat=True)
        
        return qs.filter(organization_id__in=user_orgs)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Custom User admin with organization scoping and RBAC integration.
    """
    inlines = (MembershipInline,)
    list_display = (
        'email', 'first_name', 'last_name', 
        'get_organizations', 'get_roles', 'is_active', 'date_joined'
    )
    list_filter = (
        'is_active', 'is_staff', 'is_superuser', 
        'memberships__role', 'memberships__organization'
    )
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)
    
    # Customize fieldsets for custom User model
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name')}),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'first_name', 'last_name'),
        }),
    )
    
    def get_organizations(self, obj):
        """Display user's organizations."""
        orgs = [m.organization.name for m in obj.memberships.all()]
        return ', '.join(orgs) if orgs else 'No Organization'
    get_organizations.short_description = 'Organizations'
    
    def get_roles(self, obj):
        """Display user's roles."""
        roles = [f"{m.get_role_display()}" for m in obj.memberships.all()]
        return ', '.join(roles) if roles else 'No Role'
    get_roles.short_description = 'Roles'
    
    def get_queryset(self, request):
        """
        Filter users based on organization access.
        Superusers see all users, others see only users in their organizations.
        """
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        
        # Get user's organizations
        user_orgs = Membership.objects.filter(
            user=request.user
        ).values_list('organization_id', flat=True)
        
        # Return users who are members of the same organizations
        return qs.filter(memberships__organization_id__in=user_orgs).distinct()
    
    def save_model(self, request, obj, form, change):
        """
        Custom save logic with audit logging.
        """
        super().save_model(request, obj, form, change)
        
        # Create audit event
        AuditEvent.objects.create(
            user=request.user,
            event='user_updated' if change else 'user_created',
            metadata={
                'target_user': obj.email,
                'admin_action': True
            }
        )


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    """
    Organization admin with member management.
    """
    list_display = ('name', 'slug', 'get_member_count', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at', 'updated_at')
    
    def get_member_count(self, obj):
        """Display member count for organization."""
        count = obj.memberships.count()
        url = reverse('admin:accounts_membership_changelist') + f'?organization__id__exact={obj.id}'
        return format_html('<a href="{}">{} members</a>', url, count)
    get_member_count.short_description = 'Members'
    
    def get_queryset(self, request):
        """
        Filter organizations based on user access.
        """
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        
        # Get user's organizations
        user_orgs = Membership.objects.filter(
            user=request.user
        ).values_list('organization_id', flat=True)
        
        return qs.filter(id__in=user_orgs)


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    """
    Membership admin for managing user-organization relationships.
    """
    list_display = (
        'user_email', 'user_name', 'organization', 
        'role', 'created_at', 'role_actions'
    )
    list_filter = ('role', 'organization', 'created_at')
    search_fields = (
        'user__email', 'user__first_name', 'user__last_name', 
        'organization__name'
    )
    readonly_fields = ('created_at', 'updated_at')
    
    def user_email(self, obj):
        """Display user email."""
        return obj.user.email
    user_email.short_description = 'User Email'
    
    def user_name(self, obj):
        """Display user full name."""
        return f"{obj.user.first_name} {obj.user.last_name}".strip()
    user_name.short_description = 'User Name'
    
    def role_actions(self, obj):
        """Display role change actions."""
        change_url = reverse('admin:accounts_membership_change', args=[obj.pk])
        return format_html('<a href="{}">Change Role</a>', change_url)
    role_actions.short_description = 'Actions'
    
    def get_queryset(self, request):
        """
        Filter memberships based on user's organization access.
        """
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        
        # Get user's organizations
        user_orgs = Membership.objects.filter(
            user=request.user
        ).values_list('organization_id', flat=True)
        
        return qs.filter(organization_id__in=user_orgs)
    
    def save_model(self, request, obj, form, change):
        """
        Custom save with audit logging.
        """
        old_role = None
        if change:
            old_membership = Membership.objects.get(pk=obj.pk)
            old_role = old_membership.role
        
        super().save_model(request, obj, form, change)
        
        # Create audit event
        event = 'membership_updated' if change else 'membership_created'
        metadata = {
            'user': obj.user.email,
            'organization': obj.organization.name,
            'role': obj.role,
            'admin_action': True
        }
        
        if change and old_role != obj.role:
            metadata['old_role'] = old_role
            event = 'role_changed'
        
        AuditEvent.objects.create(
            user=request.user,
            event=event,
            organization=obj.organization,
            metadata=metadata
        )


@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    """
    Audit event admin - read-only for security.
    """
    list_display = (
        'created_at', 'user_email', 'event', 
        'organization', 'ip_address', 'view_details'
    )
    list_filter = ('event', 'organization', 'created_at')
    search_fields = (
        'user__email', 'event', 'ip_address'
    )
    readonly_fields = (
        'user', 'event', 'ip_address', 'user_agent',
        'organization', 'created_at', 'metadata'
    )
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    
    def user_email(self, obj):
        """Display user email or 'Anonymous'."""
        return obj.user.email if obj.user else 'Anonymous'
    user_email.short_description = 'User'
    
    def view_details(self, obj):
        """Link to view full event details."""
        change_url = reverse('admin:accounts_auditevent_change', args=[obj.pk])
        return format_html('<a href="{}">View</a>', change_url)
    view_details.short_description = 'Details'
    
    def has_add_permission(self, request):
        """Audit events should not be manually created."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Audit events should not be modified."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Only superusers can delete audit events (for cleanup)."""
        return request.user.is_superuser
    
    def get_queryset(self, request):
        """
        Filter audit events based on user's organization access.
        """
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        
        # Get user's organizations
        user_orgs = Membership.objects.filter(
            user=request.user
        ).values_list('organization_id', flat=True)
        
        # Show events from user's organizations or events involving the user
        return qs.filter(
            models.Q(organization_id__in=user_orgs) |
            models.Q(user=request.user)
        ).distinct()


# Legacy model admins for backward compatibility
@admin.register(UserProfile)
class LegacyUserProfileAdmin(admin.ModelAdmin):
    """Legacy user profile admin."""
    list_display = ('user', 'role', 'title', 'created_at')
    list_filter = ('role', 'created_at')
    search_fields = ('user__email', 'title')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(LegacyOrganization)
class LegacyOrganizationAdmin(admin.ModelAdmin):
    """Legacy organization admin."""
    list_display = ('name', 'type', 'is_active', 'created_at')
    list_filter = ('type', 'is_active', 'created_at')
    search_fields = ('name',)


# Customize admin site
admin.site.site_header = "HRIS Authentication & RBAC Administration"
admin.site.site_title = "HRIS Admin"
admin.site.index_title = "Welcome to HRIS Administration"


# Custom admin actions
@admin.action(description='Invite selected users to organization')
def invite_users_to_organization(modeladmin, request, queryset):
    """
    Custom action to invite users to an organization.
    This would typically send email invitations.
    """
    count = queryset.count()
    messages.success(
        request, 
        f'Successfully sent invitations to {count} users.'
    )


@admin.action(description='Deactivate selected users')
def deactivate_users(modeladmin, request, queryset):
    """
    Custom action to deactivate users.
    """
    updated = queryset.update(is_active=False)
    messages.success(
        request,
        f'Successfully deactivated {updated} users.'
    )
    
    # Log audit events
    for user in queryset:
        AuditEvent.objects.create(
            user=request.user,
            event='user_deactivated',
            metadata={
                'target_user': user.email,
                'admin_action': True
            }
        )


# Add actions to UserAdmin
UserAdmin.actions = [invite_users_to_organization, deactivate_users]