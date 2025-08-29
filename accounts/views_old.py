from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import authenticate
from django.contrib.auth.models import User, Group, Permission
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.core.mail import send_mail
from django.conf import settings
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import UserProfile, Organization, RolePermissionMatrix, AuditLog
from .serializers import (
    UserSerializer, UserProfileSerializer, OrganizationSerializer,
    GroupSerializer, PermissionSerializer, CreateUserSerializer,
    RolePermissionMatrixSerializer, AuditLogSerializer,
    LoginResponseSerializer, SocialAuthSerializer,
    ChangePasswordSerializer, PasswordResetSerializer,
    PasswordResetConfirmSerializer
)
import logging

logger = logging.getLogger(__name__)

class CustomTokenObtainPairView(TokenObtainPairView):
    """Custom login view that returns user data along with tokens"""
    
    @swagger_auto_schema(
        operation_description="Login with email/username and password",
        operation_summary="User Login",
        tags=['Authentication'],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['email', 'password'],
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, description='Email or username'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, description='Password'),
            },
            example={
                'email': 'employee@test.com',
                'password': 'Employee123!'
            }
        ),
        responses={
            200: openapi.Response(
                description="Login successful",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'access': openapi.Schema(type=openapi.TYPE_STRING, description='JWT access token'),
                        'refresh': openapi.Schema(type=openapi.TYPE_STRING, description='JWT refresh token'),
                        'user': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'email': openapi.Schema(type=openapi.TYPE_STRING),
                                'first_name': openapi.Schema(type=openapi.TYPE_STRING),
                                'last_name': openapi.Schema(type=openapi.TYPE_STRING),
                                'profile': openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        'role': openapi.Schema(type=openapi.TYPE_STRING),
                                        'organization': openapi.Schema(type=openapi.TYPE_STRING),
                                    }
                                ),
                            }
                        ),
                    }
                )
            ),
            401: openapi.Response(description="Invalid credentials"),
        }
    )
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        
        if response.status_code == 200:
            # Get the user
            email = request.data.get('email') or request.data.get('username')
            user = None
            
            if email:
                try:
                    user = User.objects.get(email=email)
                except User.DoesNotExist:
                    try:
                        user = User.objects.get(username=email)
                    except User.DoesNotExist:
                        pass
            
            if user:
                # Log the login
                AuditLog.objects.create(
                    user=user,
                    action='login',
                    description=f'User logged in from {request.META.get("REMOTE_ADDR")}',
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
                
                # Add user data to response
                user_serializer = UserSerializer(user)
                response.data['user'] = user_serializer.data
        
        return response

class UserListCreateView(generics.ListCreateAPIView):
    queryset = User.objects.all().select_related('profile').prefetch_related('groups', 'user_permissions')
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateUserSerializer
        return UserSerializer
    
    def perform_create(self, serializer):
        user = serializer.save()
        
        # Log user creation
        AuditLog.objects.create(
            user=self.request.user,
            action='create',
            resource_type='User',
            resource_id=str(user.id),
            description=f'Created user: {user.username}',
            ip_address=self.request.META.get('REMOTE_ADDR'),
            user_agent=self.request.META.get('HTTP_USER_AGENT', '')
        )

class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all().select_related('profile').prefetch_related('groups', 'user_permissions')
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_update(self, serializer):
        user = serializer.save()
        
        # Log user update
        AuditLog.objects.create(
            user=self.request.user,
            action='update',
            resource_type='User',
            resource_id=str(user.id),
            description=f'Updated user: {user.username}',
            ip_address=self.request.META.get('REMOTE_ADDR'),
            user_agent=self.request.META.get('HTTP_USER_AGENT', '')
        )
    
    def perform_destroy(self, instance):
        # Log user deletion
        AuditLog.objects.create(
            user=self.request.user,
            action='delete',
            resource_type='User',
            resource_id=str(instance.id),
            description=f'Deleted user: {instance.username}',
            ip_address=self.request.META.get('REMOTE_ADDR'),
            user_agent=self.request.META.get('HTTP_USER_AGENT', '')
        )
        instance.delete()

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def current_user(request):
    """Get current user information"""
    serializer = UserSerializer(request.user)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout_view(request):
    """Logout user and blacklist refresh token"""
    try:
        refresh_token = request.data.get('refresh')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
        
        # Log logout
        AuditLog.objects.create(
            user=request.user,
            action='logout',
            description=f'User logged out from {request.META.get("REMOTE_ADDR")}',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return Response({'detail': 'Successfully logged out'})
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_permissions(request, user_id):
    """Get all permissions for a specific user"""
    try:
        user = User.objects.get(id=user_id)
        permissions = user.get_all_permissions()
        return Response({'permissions': list(permissions)})
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def change_password(request):
    """Change user password"""
    serializer = ChangePasswordSerializer(data=request.data)
    if serializer.is_valid():
        user = request.user
        
        if not user.check_password(serializer.validated_data['old_password']):
            return Response({'error': 'Invalid old password'}, status=status.HTTP_400_BAD_REQUEST)
        
        user.set_password(serializer.validated_data['new_password1'])
        user.save()
        
        # Log password change
        AuditLog.objects.create(
            user=user,
            action='update',
            description='Password changed',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return Response({'detail': 'Password changed successfully'})
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def social_auth(request):
    """Handle social authentication"""
    serializer = SocialAuthSerializer(data=request.data)
    if serializer.is_valid():
        provider = serializer.validated_data['provider']
        access_token = serializer.validated_data['access_token']
        
        # Here you would integrate with your social auth backend
        # For now, we'll return a placeholder response
        return Response({
            'detail': f'Social auth with {provider} not fully implemented yet',
            'provider': provider
        }, status=status.HTTP_501_NOT_IMPLEMENTED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Organization views
class OrganizationListCreateView(generics.ListCreateAPIView):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    permission_classes = [permissions.IsAuthenticated]

class OrganizationDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    permission_classes = [permissions.IsAuthenticated]

# Group views
class GroupListCreateView(generics.ListCreateAPIView):
    queryset = Group.objects.all().prefetch_related('permissions')
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAuthenticated]

class GroupDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Group.objects.all().prefetch_related('permissions')
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAuthenticated]

# Permission views
class PermissionListView(generics.ListAPIView):
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    permission_classes = [permissions.IsAuthenticated]

# Role Permission Matrix views
class RolePermissionMatrixListCreateView(generics.ListCreateAPIView):
    queryset = RolePermissionMatrix.objects.all()
    serializer_class = RolePermissionMatrixSerializer
    permission_classes = [permissions.IsAuthenticated]

# Audit Log views
class AuditLogListView(generics.ListAPIView):
    queryset = AuditLog.objects.all().select_related('user')
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user_id = self.request.query_params.get('user_id')
        action = self.request.query_params.get('action')
        
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        if action:
            queryset = queryset.filter(action=action)
            
        return queryset

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def dashboard_stats(request):
    """Get dashboard statistics"""
    stats = {
        'total_users': User.objects.filter(is_active=True).count(),
        'total_organizations': Organization.objects.filter(is_active=True).count(),
        'total_groups': Group.objects.count(),
        'recent_logins': AuditLog.objects.filter(action='login').count(),
        'user_roles': {}
    }
    
    # Get user role distribution
    for role_choice in UserProfile.ROLE_CHOICES:
        role_code, role_name = role_choice
        count = UserProfile.objects.filter(role=role_code).count()
        stats['user_roles'][role_name] = count
    
    return Response(stats)
