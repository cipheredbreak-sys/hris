from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from .models import UserProfile, Organization, Membership, AuditEvent

User = get_user_model()

class OrganizationListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ['id', 'name', 'slug', 'created_at']
        read_only_fields = ['id', 'created_at']

class OrganizationDetailSerializer(serializers.ModelSerializer):
    member_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Organization
        fields = ['id', 'name', 'slug', 'created_at', 'member_count']
        read_only_fields = ['id', 'created_at']
    
    def get_member_count(self, obj):
        return obj.memberships.count()

class UserProfileSerializer(serializers.ModelSerializer):
    organization = OrganizationSerializer(read_only=True)
    organization_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    
    class Meta:
        model = UserProfile
        fields = '__all__'

class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ['id', 'name', 'content_type', 'codename']

class GroupListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ['id', 'name']

class GroupDetailSerializer(serializers.ModelSerializer):
    permissions = PermissionSerializer(many=True, read_only=True)
    permission_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = Group
        fields = ['id', 'name', 'permissions', 'permission_ids']

    def create(self, validated_data):
        permission_ids = validated_data.pop('permission_ids', [])
        group = Group.objects.create(**validated_data)
        if permission_ids:
            permissions = Permission.objects.filter(id__in=permission_ids)
            group.permissions.set(permissions)
        return group

    def update(self, instance, validated_data):
        permission_ids = validated_data.pop('permission_ids', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        if permission_ids is not None:
            permissions = Permission.objects.filter(id__in=permission_ids)
            instance.permissions.set(permissions)
            
        return instance

class UserListSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'is_active', 'date_joined']
        read_only_fields = ['id', 'date_joined']

class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'is_active']
        read_only_fields = ['id']

    def create(self, validated_data):
        # Extract profile data and group data
        group_ids = validated_data.pop('group_ids', [])
        password = validated_data.pop('password', None)
        
        profile_data = {
            'role': validated_data.pop('role', 'employee'),
            'organization_id': validated_data.pop('organization_id', None),
            'title': validated_data.pop('title', ''),
            'phone': validated_data.pop('phone', ''),
        }
        
        # Create user
        user = User.objects.create_user(**validated_data)
        if password:
            user.set_password(password)
            user.save()
        
        # Assign groups
        if group_ids:
            groups = Group.objects.filter(id__in=group_ids)
            user.groups.set(groups)
        
        # Create or update profile
        profile, created = UserProfile.objects.get_or_create(
            user=user,
            defaults=profile_data
        )
        if not created:
            for key, value in profile_data.items():
                if value is not None:
                    setattr(profile, key, value)
            profile.save()
        
        return user

    def update(self, instance, validated_data):
        # Extract profile data and group data
        group_ids = validated_data.pop('group_ids', None)
        password = validated_data.pop('password', None)
        
        profile_data = {}
        for field in ['role', 'organization_id', 'title', 'phone']:
            if field in validated_data:
                profile_data[field] = validated_data.pop(field)
        
        # Update user
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        if password:
            instance.set_password(password)
        
        instance.save()
        
        # Update groups
        if group_ids is not None:
            groups = Group.objects.filter(id__in=group_ids)
            instance.groups.set(groups)
        
        # Update profile
        if profile_data:
            profile, created = UserProfile.objects.get_or_create(
                user=instance,
                defaults=profile_data
            )
            if not created:
                for key, value in profile_data.items():
                    if value is not None:
                        setattr(profile, key, value)
                profile.save()
        
        return instance

class CreateUserSerializer(serializers.ModelSerializer):
    """Simplified serializer for user creation"""
    password = serializers.CharField(write_only=True)
    profile = UserProfileSerializer(required=False)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password', 'profile']

    def create(self, validated_data):
        profile_data = validated_data.pop('profile', {})
        password = validated_data.pop('password')
        
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        
        UserProfile.objects.create(user=user, **profile_data)
        return user

class AuditEventSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    
    class Meta:
        model = AuditEvent
        fields = ['id', 'user_email', 'event', 'created_at', 'ip_address', 'organization_name', 'metadata']

class MembershipSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    
    class Meta:
        model = Membership
        fields = ['id', 'user_email', 'organization_name', 'role', 'created_at']

# Serializer for login response
class LoginResponseSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()
    user = UserSerializer(read_only=True)

# Serializer for social auth
class SocialAuthSerializer(serializers.Serializer):
    provider = serializers.ChoiceField(choices=['google', 'microsoft'])
    access_token = serializers.CharField()

# Serializer for password change
class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField()
    new_password1 = serializers.CharField()
    new_password2 = serializers.CharField()

    def validate(self, attrs):
        if attrs['new_password1'] != attrs['new_password2']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs

# Serializer for password reset
class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()

class PasswordResetConfirmSerializer(serializers.Serializer):
    new_password1 = serializers.CharField()
    new_password2 = serializers.CharField()
    uid = serializers.CharField()
    token = serializers.CharField()

    def validate(self, attrs):
        if attrs['new_password1'] != attrs['new_password2']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs