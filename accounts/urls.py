from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

app_name = 'accounts'

urlpatterns = [
    # JWT Authentication
    path('auth/login/', views.CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/logout/', views.logout_view, name='logout'),
    path('auth/user/', views.current_user, name='current_user'),
    path('auth/password/change/', views.change_password, name='change_password'),
    
    # Social Auth (placeholder for now)
    path('auth/social/login/', views.social_auth, name='social_auth'),
    
    # User Management
    path('users/', views.UserListCreateView.as_view(), name='user-list-create'),
    path('users/<int:pk>/', views.UserDetailView.as_view(), name='user-detail'),
    path('users/<int:user_id>/permissions/', views.user_permissions, name='user-permissions'),
    
    # Organizations
    path('organizations/', views.OrganizationListCreateView.as_view(), name='organization-list-create'),
    path('organizations/<int:pk>/', views.OrganizationDetailView.as_view(), name='organization-detail'),
    
    # Groups (Roles)
    path('auth/groups/', views.GroupListCreateView.as_view(), name='group-list-create'),
    path('auth/groups/<int:pk>/', views.GroupDetailView.as_view(), name='group-detail'),
    
    # Permissions
    path('auth/permissions/', views.PermissionListView.as_view(), name='permission-list'),
    
    # Role Permission Matrix
    path('roles/permissions/', views.RolePermissionMatrixListCreateView.as_view(), name='role-permissions'),
    
    # Audit Logs
    path('audit-logs/', views.AuditLogListView.as_view(), name='audit-logs'),
    
    # Dashboard Stats
    path('dashboard/stats/', views.dashboard_stats, name='dashboard-stats'),
    
]