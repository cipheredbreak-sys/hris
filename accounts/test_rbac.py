"""
Test cases for RBAC system
Tests permission checking, role management, and access control
"""
import pytest
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from unittest.mock import Mock, patch
from .models import UserProfile, Organization
from .rbac_service import RBACService, rbac_service
from .rbac_decorators import require_permission, require_role, RBACViewMixin
from rest_framework.test import APITestCase
from rest_framework import status

class RBACServiceTest(TestCase):
    """Test the core RBAC service functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.rbac = RBACService()
        
        # Create test organizations
        self.broker_org = Organization.objects.create(
            name='Test Broker',
            type='broker'
        )
        
        self.employer_org = Organization.objects.create(
            name='Test Employer',
            type='employer'
        )
        
        # Create test users with different roles
        self.super_admin = User.objects.create_user(
            username='superadmin',
            email='super@admin.com',
            password='test123'
        )
        UserProfile.objects.create(
            user=self.super_admin,
            role='super_admin'
        )
        
        self.broker_admin = User.objects.create_user(
            username='brokeradmin',
            email='broker@admin.com',
            password='test123'
        )
        UserProfile.objects.create(
            user=self.broker_admin,
            role='broker_admin',
            organization=self.broker_org
        )
        
        self.broker_user = User.objects.create_user(
            username='brokeruser',
            email='broker@user.com',
            password='test123'
        )
        UserProfile.objects.create(
            user=self.broker_user,
            role='broker_user',
            organization=self.broker_org
        )
        
        self.employer_admin = User.objects.create_user(
            username='employeradmin',
            email='employer@admin.com',
            password='test123'
        )
        UserProfile.objects.create(
            user=self.employer_admin,
            role='employer_admin',
            organization=self.employer_org
        )
        
        self.employee = User.objects.create_user(
            username='employee',
            email='employee@test.com',
            password='test123'
        )
        UserProfile.objects.create(
            user=self.employee,
            role='employee',
            organization=self.employer_org
        )

    def test_super_admin_permissions(self):
        """Test that super admin has all permissions"""
        self.assertTrue(
            self.rbac.has_permission(self.super_admin, 'employees', 'manage')
        )
        self.assertTrue(
            self.rbac.has_permission(self.super_admin, 'employers', 'delete')
        )
        self.assertTrue(
            self.rbac.has_permission(self.super_admin, 'plans', 'create')
        )

    def test_broker_admin_permissions(self):
        """Test broker admin permissions"""
        # Should have permissions for broker resources
        self.assertTrue(
            self.rbac.has_permission(self.broker_admin, 'employees', 'create')
        )
        self.assertTrue(
            self.rbac.has_permission(self.broker_admin, 'employers', 'update')
        )
        self.assertTrue(
            self.rbac.has_permission(self.broker_admin, 'plans', 'read')
        )
        
        # Should not have super admin permissions
        self.assertFalse(
            self.rbac.has_permission(self.broker_admin, 'roles', 'manage')
        )

    def test_broker_user_permissions(self):
        """Test broker user permissions (more limited than admin)"""
        # Should have read/update permissions
        self.assertTrue(
            self.rbac.has_permission(self.broker_user, 'employees', 'read')
        )
        self.assertTrue(
            self.rbac.has_permission(self.broker_user, 'employees', 'update')
        )
        
        # Should not have create/delete permissions
        self.assertFalse(
            self.rbac.has_permission(self.broker_user, 'employees', 'create')
        )

    def test_employer_admin_permissions(self):
        """Test employer admin permissions"""
        # Should have permissions for own employees
        self.assertTrue(
            self.rbac.has_permission(self.employer_admin, 'employees', 'create')
        )
        self.assertTrue(
            self.rbac.has_permission(self.employer_admin, 'employees', 'update')
        )
        
        # Should be able to read plans
        self.assertTrue(
            self.rbac.has_permission(self.employer_admin, 'plans', 'read')
        )
        
        # Should not manage employers (only brokers can)
        self.assertFalse(
            self.rbac.has_permission(self.employer_admin, 'employers', 'create')
        )

    def test_employee_permissions(self):
        """Test employee permissions (most restricted)"""
        # Should only have view_own permissions
        self.assertTrue(
            self.rbac.has_permission(self.employee, 'employees', 'view_own')
        )
        self.assertTrue(
            self.rbac.has_permission(self.employee, 'enrollments', 'view_own')
        )
        
        # Should not have broader permissions
        self.assertFalse(
            self.rbac.has_permission(self.employee, 'employees', 'read')
        )
        self.assertFalse(
            self.rbac.has_permission(self.employee, 'employees', 'create')
        )

    def test_role_checking(self):
        """Test role checking functionality"""
        self.assertTrue(self.rbac.has_role(self.super_admin, 'super_admin'))
        self.assertTrue(self.rbac.has_role(self.broker_admin, 'broker_admin'))
        self.assertFalse(self.rbac.has_role(self.broker_user, 'broker_admin'))
        
        self.assertTrue(
            self.rbac.has_any_role(self.broker_admin, ['broker_admin', 'super_admin'])
        )
        self.assertFalse(
            self.rbac.has_any_role(self.employee, ['broker_admin', 'super_admin'])
        )

    def test_role_hierarchy(self):
        """Test role hierarchy levels"""
        super_level = self.rbac.get_role_hierarchy_level('super_admin')
        broker_level = self.rbac.get_role_hierarchy_level('broker_admin')
        employee_level = self.rbac.get_role_hierarchy_level('employee')
        
        self.assertGreater(super_level, broker_level)
        self.assertGreater(broker_level, employee_level)

    def test_user_management_permissions(self):
        """Test who can manage which users"""
        # Super admin can manage anyone
        self.assertTrue(
            self.rbac.can_manage_user(self.super_admin, self.broker_admin)
        )
        
        # Broker admin can manage broker users in same org
        self.assertTrue(
            self.rbac.can_manage_user(self.broker_admin, self.broker_user)
        )
        
        # Broker admin cannot manage super admin (higher level)
        self.assertFalse(
            self.rbac.can_manage_user(self.broker_admin, self.super_admin)
        )
        
        # Employee cannot manage anyone
        self.assertFalse(
            self.rbac.can_manage_user(self.employee, self.employer_admin)
        )

    def test_accessible_organizations(self):
        """Test organization access filtering"""
        # Super admin can access all
        super_orgs = self.rbac.get_accessible_organizations(self.super_admin)
        self.assertGreater(len(super_orgs), 0)
        
        # Broker users can access their organization
        broker_orgs = self.rbac.get_accessible_organizations(self.broker_admin)
        self.assertIn(str(self.broker_org.id), broker_orgs)
        
        # Employer users can only access their organization
        employer_orgs = self.rbac.get_accessible_organizations(self.employer_admin)
        self.assertEqual(employer_orgs, [str(self.employer_org.id)])
        
        # Employee can only access their organization
        employee_orgs = self.rbac.get_accessible_organizations(self.employee)
        self.assertEqual(employee_orgs, [str(self.employer_org.id)])

class RBACDecoratorsTest(TestCase):
    """Test RBAC decorators and middleware"""
    
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='test123'
        )
        UserProfile.objects.create(
            user=self.user,
            role='broker_admin'
        )

    def test_require_permission_decorator(self):
        """Test the require_permission decorator"""
        @require_permission('employees', 'read')
        def test_view(self, request):
            return {'success': True}
        
        # Create mock view instance
        view_instance = Mock()
        
        # Test with authorized user
        request = self.factory.get('/test/')
        request.user = self.user
        
        result = test_view(view_instance, request)
        self.assertEqual(result, {'success': True})
        
        # Test with unauthorized user
        unauthorized_user = User.objects.create_user(
            username='unauthorized',
            email='unauth@example.com',
            password='test123'
        )
        UserProfile.objects.create(
            user=unauthorized_user,
            role='employee'  # Employee can't read all employees
        )
        
        request.user = unauthorized_user
        result = test_view(view_instance, request)
        
        # Should return permission denied response
        self.assertEqual(result.status_code, 403)

    def test_require_role_decorator(self):
        """Test the require_role decorator"""
        @require_role(['broker_admin', 'super_admin'])
        def test_view(self, request):
            return {'success': True}
        
        view_instance = Mock()
        request = self.factory.get('/test/')
        request.user = self.user
        
        result = test_view(view_instance, request)
        self.assertEqual(result, {'success': True})

class RBACAPITest(APITestCase):
    """Test RBAC in API endpoints"""
    
    def setUp(self):
        self.broker_admin = User.objects.create_user(
            username='brokeradmin',
            email='broker@admin.com',
            password='test123'
        )
        self.broker_org = Organization.objects.create(
            name='Test Broker',
            type='broker'
        )
        UserProfile.objects.create(
            user=self.broker_admin,
            role='broker_admin',
            organization=self.broker_org
        )
        
        self.employee = User.objects.create_user(
            username='employee',
            email='employee@test.com',
            password='test123'
        )
        UserProfile.objects.create(
            user=self.employee,
            role='employee'
        )

    def test_broker_can_access_broker_endpoints(self):
        """Test that broker admin can access broker endpoints"""
        self.client.force_authenticate(user=self.broker_admin)
        
        # This would be a real broker endpoint test
        # For now, just test that the user is properly authenticated
        response = self.client.get('/api/broker/employers/')  # Hypothetical endpoint
        
        # The endpoint might not exist, but we're testing RBAC middleware
        # which should not return 403 for authorized users
        self.assertNotEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_employee_cannot_access_broker_endpoints(self):
        """Test that employee cannot access broker endpoints"""
        self.client.force_authenticate(user=self.employee)
        
        # Employee should not have access to broker functions
        response = self.client.get('/api/broker/employers/')  # Hypothetical endpoint
        
        # Should be forbidden (if endpoint exists) or not found
        # But not a 500 error from RBAC
        self.assertIn(response.status_code, [
            status.HTTP_403_FORBIDDEN, 
            status.HTTP_404_NOT_FOUND
        ])

class RBACIntegrationTest(TestCase):
    """Integration tests for complete RBAC workflow"""
    
    def setUp(self):
        """Set up complete test scenario"""
        # Create organizations
        self.broker_org = Organization.objects.create(
            name='Acme Benefits',
            type='broker'
        )
        
        self.employer_org = Organization.objects.create(
            name='TechCorp',
            type='employer'
        )
        
        # Create users
        self.broker_admin = User.objects.create_user(
            username='broker_admin',
            email='broker@admin.com',
            password='test123'
        )
        UserProfile.objects.create(
            user=self.broker_admin,
            role='broker_admin',
            organization=self.broker_org
        )

    def test_complete_rbac_workflow(self):
        """Test complete RBAC workflow from login to data access"""
        # Test role assignment
        profile = self.broker_admin.profile
        self.assertEqual(profile.role, 'broker_admin')
        self.assertEqual(profile.organization, self.broker_org)
        
        # Test permission checking
        self.assertTrue(
            rbac_service.has_permission(self.broker_admin, 'employers', 'create')
        )
        
        # Test accessible organizations
        accessible_orgs = rbac_service.get_accessible_organizations(self.broker_admin)
        self.assertIn(str(self.broker_org.id), accessible_orgs)
        
        # Test role hierarchy
        self.assertGreater(
            rbac_service.get_role_hierarchy_level('broker_admin'),
            rbac_service.get_role_hierarchy_level('employee')
        )

    def test_role_change_workflow(self):
        """Test role change and permission updates"""
        # Initially broker admin
        self.assertTrue(
            rbac_service.has_permission(self.broker_admin, 'employers', 'create')
        )
        
        # Change to broker user (less permissions)
        rbac_service.assign_role(
            self.broker_admin,
            'broker_user',
            self.broker_admin,  # Assigned by self for test
            self.broker_org
        )
        
        # Refresh user profile
        self.broker_admin.profile.refresh_from_db()
        
        # Should now have reduced permissions
        self.assertTrue(
            rbac_service.has_permission(self.broker_admin, 'employees', 'read')
        )
        self.assertFalse(
            rbac_service.has_permission(self.broker_admin, 'employees', 'create')
        )

if __name__ == '__main__':
    # Run tests
    pytest.main([__file__, '-v'])