# Django Authentication Setup Guide

## Backend Setup (Django)

### 1. Install Required Packages

```bash
pip install django-allauth
pip install djangorestframework-simplejwt
pip install django-cors-headers
pip install python-social-auth[django]
pip install django-extensions
```

### 2. Update Django Settings

Add to your `settings.py`:

```python
# settings.py

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    
    # Third party
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.microsoft',
    
    # Your apps
    'accounts',  # Create this app for user management
    'core',      # Your existing apps
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'hris_broker'),
        'USER': os.getenv('DB_USER', 'postgres'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'password'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}

# REST Framework Configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 25,
}

# JWT Configuration
from datetime import timedelta
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
}

# CORS Configuration
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
CORS_ALLOW_CREDENTIALS = True

# Django Allauth Configuration
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

SITE_ID = 1

ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_EMAIL_VERIFICATION = 'optional'
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True

# Social Auth Settings
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        },
        'OAUTH_PKCE_ENABLED': True,
    },
    'microsoft': {
        'SCOPE': [
            'User.Read',
        ],
    }
}

# Google OAuth2 Configuration
GOOGLE_OAUTH2_CLIENT_ID = os.getenv('GOOGLE_OAUTH2_CLIENT_ID')
GOOGLE_OAUTH2_CLIENT_SECRET = os.getenv('GOOGLE_OAUTH2_CLIENT_SECRET')

# Microsoft OAuth2 Configuration  
MICROSOFT_AUTH_CLIENT_ID = os.getenv('MICROSOFT_AUTH_CLIENT_ID')
MICROSOFT_AUTH_CLIENT_SECRET = os.getenv('MICROSOFT_AUTH_CLIENT_SECRET')
```

### 3. Create Environment Variables

Create `.env` file:

```bash
# Database
DB_NAME=hris_broker
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432

# Google OAuth2
GOOGLE_OAUTH2_CLIENT_ID=your_google_client_id
GOOGLE_OAUTH2_CLIENT_SECRET=your_google_client_secret

# Microsoft OAuth2
MICROSOFT_AUTH_CLIENT_ID=your_microsoft_client_id
MICROSOFT_AUTH_CLIENT_SECRET=your_microsoft_client_secret

# Django
SECRET_KEY=your_secret_key
DEBUG=True
```

### 4. Create Django App for User Management

```bash
python manage.py startapp accounts
```

### 5. Create User Models

Create `accounts/models.py`:

```python
from django.contrib.auth.models import AbstractUser, Group
from django.db import models

class Organization(models.Model):
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

class UserProfile(models.Model):
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
    
    user = models.OneToOneField('auth.User', on_delete=models.CASCADE, related_name='profile')
    organization = models.ForeignKey(Organization, null=True, blank=True, on_delete=models.CASCADE)
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default='employee')
    title = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    timezone = models.CharField(max_length=50, default='UTC')
    language = models.CharField(max_length=10, default='en')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.role}"
```

### 6. Create Serializers

Create `accounts/serializers.py`:

```python
from rest_framework import serializers
from django.contrib.auth.models import User, Group, Permission
from .models import UserProfile, Organization

class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = '__all__'

class UserProfileSerializer(serializers.ModelSerializer):
    organization = OrganizationSerializer(read_only=True)
    
    class Meta:
        model = UserProfile
        fields = '__all__'

class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)
    groups = serializers.StringRelatedField(many=True, read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 
                 'is_active', 'is_staff', 'is_superuser', 'date_joined', 
                 'last_login', 'profile', 'groups']
        read_only_fields = ['date_joined', 'last_login']

class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = '__all__'

class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = '__all__'
```

### 7. Create API Views

Create `accounts/views.py`:

```python
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.contrib.auth.models import User, Group, Permission
from .models import UserProfile, Organization
from .serializers import (
    UserSerializer, UserProfileSerializer, OrganizationSerializer,
    GroupSerializer, PermissionSerializer
)

class UserListCreateView(generics.ListCreateAPIView):
    queryset = User.objects.all().select_related('profile')
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all().select_related('profile')
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def current_user(request):
    serializer = UserSerializer(request.user)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_permissions(request, user_id):
    try:
        user = User.objects.get(id=user_id)
        permissions = user.get_all_permissions()
        return Response({'permissions': list(permissions)})
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=404)
```

### 8. URL Configuration

Create `accounts/urls.py`:

```python
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from . import views

urlpatterns = [
    # JWT Authentication
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/user/', views.current_user, name='current_user'),
    
    # Social Auth
    path('auth/social/', include('allauth.urls')),
    
    # User Management
    path('users/', views.UserListCreateView.as_view(), name='user-list-create'),
    path('users/<int:pk>/', views.UserDetailView.as_view(), name='user-detail'),
    path('users/<int:user_id>/permissions/', views.user_permissions, name='user-permissions'),
]
```

### 9. Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

### 10. Google/Microsoft OAuth Setup

1. **Google Console**: https://console.developers.google.com/
   - Create OAuth 2.0 credentials
   - Add authorized redirect URI: `http://localhost:8000/accounts/google/login/callback/`

2. **Microsoft Azure**: https://portal.azure.com/
   - Register app in Azure AD
   - Add redirect URI: `http://localhost:8000/accounts/microsoft/login/callback/`

## Next Steps

The Django backend is now ready. The React frontend components are already created and will connect to these Django endpoints automatically through the `apiService`.

To test the setup:
1. Start Django server: `python manage.py runserver`
2. Start React app: `npm start`
3. Navigate to login page and test authentication