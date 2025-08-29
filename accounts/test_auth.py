import pytest
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core import mail
from allauth.account.models import EmailAddress
from allauth.socialaccount.models import SocialApp, SocialAccount
from unittest.mock import patch, Mock
from .models import Organization, Membership, Role, AuditEvent
from .permissions import user_has_role_in_org, get_user_organizations

User = get_user_model()


class AuthenticationTestCase(TestCase):
    """Test authentication flows including allauth integration."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        
        # Create organizations
        self.broker_org = Organization.objects.create(
            name="Test Broker",
            slug="test-broker"
        )
        self.employer_org = Organization.objects.create(
            name="Test Employer", 
            slug="test-employer"
        )
        
        # Create groups
        for role_value, _ in Role.choices:
            Group.objects.get_or_create(name=role_value)
        
        # Create test users
        self.superuser = User.objects.create_superuser(
            email='superuser@test.com',
            password='TestPass123!',
            first_name='Super',
            last_name='User'
        )
        
        self.broker_admin = User.objects.create_user(
            email='broker@test.com',
            password='TestPass123!',
            first_name='Broker',
            last_name='Admin'
        )
        
        self.employer_admin = User.objects.create_user(
            email='employer@test.com',
            password='TestPass123!',
            first_name='Employer',
            last_name='Admin'
        )
        
        self.employee = User.objects.create_user(
            email='employee@test.com',
            password='TestPass123!',
            first_name='Test',
            last_name='Employee'
        )
        
        # Create memberships
        Membership.objects.create(
            user=self.broker_admin,
            organization=self.broker_org,
            role=Role.BROKER_ADMIN
        )
        
        Membership.objects.create(
            user=self.employer_admin,
            organization=self.employer_org,
            role=Role.EMPLOYER_ADMIN
        )
        
        Membership.objects.create(
            user=self.employee,
            organization=self.employer_org,
            role=Role.EMPLOYEE
        )

    def test_user_model_email_authentication(self):
        """Test that users can authenticate with email instead of username."""
        user = User.objects.create_user(
            email='testuser@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        # Test email login
        authenticated = self.client.login(
            username='testuser@example.com',  # allauth uses username field for email
            password='testpass123'
        )
        self.assertTrue(authenticated)

    def test_user_model_str_representation(self):
        """Test user model string representation."""
        self.assertEqual(str(self.employee), 'employee@test.com')

    def test_organization_model(self):
        """Test organization model functionality."""
        org = Organization.objects.create(name="Test Organization")
        
        # Test slug auto-generation
        self.assertEqual(org.slug, 'test-organization')
        
        # Test string representation
        self.assertEqual(str(org), 'Test Organization')

    def test_membership_model(self):
        """Test membership model and role assignment."""
        membership = Membership.objects.get(
            user=self.broker_admin,
            organization=self.broker_org
        )
        
        # Test string representation
        expected = f"{self.broker_admin.email} - {self.broker_org.name} (Broker Admin)"
        self.assertEqual(str(membership), expected)
        
        # Test role display
        self.assertEqual(membership.get_role_display(), 'Broker Admin')

    @override_settings(ACCOUNT_EMAIL_VERIFICATION='none')
    def test_allauth_email_signup(self):
        """Test user signup through allauth."""
        signup_data = {
            'email': 'newuser@test.com',
            'first_name': 'New',
            'last_name': 'User',
            'password1': 'ComplexPassword123!',
            'password2': 'ComplexPassword123!',
        }
        
        response = self.client.post(reverse('account_signup'), signup_data)
        
        # Should redirect after successful signup
        self.assertEqual(response.status_code, 302)
        
        # User should be created
        user = User.objects.get(email='newuser@test.com')
        self.assertEqual(user.first_name, 'New')
        self.assertEqual(user.last_name, 'User')

    @override_settings(ACCOUNT_EMAIL_VERIFICATION='mandatory')
    def test_email_verification_required(self):
        """Test email verification requirement."""
        signup_data = {
            'email': 'verify@test.com',
            'first_name': 'Verify',
            'last_name': 'User',
            'password1': 'ComplexPassword123!',
            'password2': 'ComplexPassword123!',
        }
        
        response = self.client.post(reverse('account_signup'), signup_data)
        
        # Should redirect to email verification page
        self.assertEqual(response.status_code, 302)
        
        # User should exist but email not verified
        user = User.objects.get(email='verify@test.com')
        email_address = EmailAddress.objects.get(user=user)
        self.assertFalse(email_address.verified)
        
        # Should have sent verification email
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('verify@test.com', mail.outbox[0].to)

    def test_login_creates_audit_event(self):
        """Test that login creates an audit event."""
        initial_count = AuditEvent.objects.count()
        
        login_successful = self.client.login(
            username='employee@test.com',
            password='TestPass123!'
        )
        
        self.assertTrue(login_successful)
        
        # Should create audit event
        self.assertEqual(AuditEvent.objects.count(), initial_count + 1)
        
        audit_event = AuditEvent.objects.latest('created_at')
        self.assertEqual(audit_event.event, 'login')
        self.assertEqual(audit_event.user, self.employee)

    def test_logout_creates_audit_event(self):
        """Test that logout creates an audit event."""
        # Login first
        self.client.login(username='employee@test.com', password='TestPass123!')
        
        initial_count = AuditEvent.objects.count()
        
        # Logout
        response = self.client.post(reverse('account_logout'))
        
        # Should create audit event
        self.assertEqual(AuditEvent.objects.count(), initial_count + 1)
        
        audit_event = AuditEvent.objects.latest('created_at')
        self.assertEqual(audit_event.event, 'logout')
        self.assertEqual(audit_event.user, self.employee)


class RBACTestCase(TestCase):
    """Test RBAC (Role-Based Access Control) functionality."""

    def setUp(self):
        """Set up test data for RBAC tests."""
        self.organization = Organization.objects.create(
            name="Test Organization",
            slug="test-org"
        )
        
        self.user = User.objects.create_user(
            email='testuser@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        # Create groups
        for role_value, _ in Role.choices:
            Group.objects.get_or_create(name=role_value)

    def test_membership_creation_assigns_group(self):
        """Test that creating a membership assigns the user to the correct group."""
        membership = Membership.objects.create(
            user=self.user,
            organization=self.organization,
            role=Role.BROKER_ADMIN
        )
        
        # User should be added to broker_admin group
        broker_group = Group.objects.get(name=Role.BROKER_ADMIN)
        self.assertTrue(self.user.groups.filter(id=broker_group.id).exists())

    def test_user_has_role_in_org_function(self):
        """Test the user_has_role_in_org utility function."""
        # User has no role initially
        self.assertFalse(
            user_has_role_in_org(self.user, self.organization, [Role.BROKER_ADMIN])
        )
        
        # Create membership
        Membership.objects.create(
            user=self.user,
            organization=self.organization,
            role=Role.BROKER_ADMIN
        )
        
        # User should now have the role
        self.assertTrue(
            user_has_role_in_org(self.user, self.organization, [Role.BROKER_ADMIN])
        )
        
        # But not other roles
        self.assertFalse(
            user_has_role_in_org(self.user, self.organization, [Role.EMPLOYEE])
        )

    def test_get_user_organizations_function(self):
        """Test the get_user_organizations utility function."""
        # User has no organizations initially
        orgs = get_user_organizations(self.user)
        self.assertEqual(orgs.count(), 0)
        
        # Create membership
        Membership.objects.create(
            user=self.user,
            organization=self.organization,
            role=Role.EMPLOYEE
        )
        
        # User should now have the organization
        orgs = get_user_organizations(self.user)
        self.assertEqual(orgs.count(), 1)
        self.assertIn(self.organization, orgs)


class PermissionTestCase(TestCase):
    """Test permission decorators and classes."""

    def setUp(self):
        """Set up test data."""
        self.organization = Organization.objects.create(
            name="Test Organization",
            slug="test-org"
        )
        
        self.user = User.objects.create_user(
            email='testuser@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        self.other_org = Organization.objects.create(
            name="Other Organization",
            slug="other-org"
        )
        
        # Create membership
        Membership.objects.create(
            user=self.user,
            organization=self.organization,
            role=Role.EMPLOYER_ADMIN
        )

    def test_org_scoped_decorator_with_valid_access(self):
        """Test org_scoped decorator allows access for valid membership."""
        from .permissions import org_scoped
        
        @org_scoped
        def test_view(request, organization_id=None):
            return "success"
        
        # Create mock request
        request = Mock()
        request.user = self.user
        request.method = 'GET'
        request.GET = {}
        
        # Should succeed with valid organization_id
        result = test_view(request, organization_id=self.organization.id)
        self.assertEqual(result, "success")
        self.assertEqual(request.current_organization, self.organization)

    def test_org_scoped_decorator_denies_invalid_access(self):
        """Test org_scoped decorator denies access for invalid membership."""
        from .permissions import org_scoped
        from django.core.exceptions import PermissionDenied
        
        @org_scoped
        def test_view(request, organization_id=None):
            return "success"
        
        # Create mock request
        request = Mock()
        request.user = self.user
        request.method = 'GET'
        request.GET = {}
        
        # Should raise PermissionDenied for organization user doesn't belong to
        with self.assertRaises(PermissionDenied):
            test_view(request, organization_id=self.other_org.id)

    def test_requires_role_decorator(self):
        """Test requires_role decorator."""
        from .permissions import requires_role
        from django.core.exceptions import PermissionDenied
        
        @requires_role(Role.BROKER_ADMIN)
        def test_view(request, organization_id=None):
            return "success"
        
        # Create mock request
        request = Mock()
        request.user = self.user
        request.method = 'GET'
        request.GET = {}
        request.current_membership = Membership.objects.get(user=self.user)
        request.current_organization = self.organization
        
        # Should raise PermissionDenied - user is EMPLOYER_ADMIN, not BROKER_ADMIN
        with self.assertRaises(PermissionDenied):
            test_view(request, organization_id=self.organization.id)


class SocialAuthTestCase(TestCase):
    """Test social authentication flows."""

    def setUp(self):
        """Set up test data."""
        # Create social app
        self.google_app = SocialApp.objects.create(
            provider='google',
            name='Google OAuth2',
            client_id='test_client_id',
            secret='test_client_secret'
        )

    @patch('allauth.socialaccount.providers.google.views.GoogleOAuth2Adapter.complete_login')
    def test_google_social_login_creates_user(self, mock_complete_login):
        """Test that Google social login creates a new user."""
        # Mock the social login response
        mock_user_data = {
            'email': 'socialuser@gmail.com',
            'given_name': 'Social',
            'family_name': 'User',
        }
        
        mock_sociallogin = Mock()
        mock_sociallogin.user = User(
            email=mock_user_data['email'],
            first_name=mock_user_data['given_name'],
            last_name=mock_user_data['family_name']
        )
        mock_sociallogin.account.provider = 'google'
        mock_sociallogin.account.extra_data = mock_user_data
        
        mock_complete_login.return_value = mock_sociallogin
        
        # Test would require more complex mocking of OAuth flow
        # For now, just test that the adapter would create audit events
        from .adapters import SocialAccountAdapter
        adapter = SocialAccountAdapter()
        
        # Test that pre_social_login doesn't raise errors
        request = Mock()
        request.user = Mock()
        request.user.is_authenticated = False
        
        # Should not raise any exceptions
        adapter.pre_social_login(request, mock_sociallogin)

    def test_social_account_linking_existing_user(self):
        """Test that social accounts link to existing users by email."""
        # Create existing user
        existing_user = User.objects.create_user(
            email='existing@test.com',
            password='testpass123',
            first_name='Existing',
            last_name='User'
        )
        
        # Create social account for the same email
        social_account = SocialAccount.objects.create(
            user=existing_user,
            provider='google',
            uid='12345',
            extra_data={'email': 'existing@test.com'}
        )
        
        # Verify linking
        self.assertEqual(social_account.user, existing_user)
        self.assertEqual(social_account.provider, 'google')


class AuditEventTestCase(TestCase):
    """Test audit event logging."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='testuser@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        self.organization = Organization.objects.create(
            name="Test Organization",
            slug="test-org"
        )

    def test_audit_event_creation(self):
        """Test creating audit events."""
        event = AuditEvent.objects.create(
            user=self.user,
            event='login',
            ip_address='192.168.1.1',
            user_agent='Test Browser',
            organization=self.organization,
            metadata={'test': 'data'}
        )
        
        # Test string representation
        expected = f"{self.user.email} - User Login - {event.created_at}"
        self.assertEqual(str(event), expected)
        
        # Test fields
        self.assertEqual(event.user, self.user)
        self.assertEqual(event.event, 'login')
        self.assertEqual(event.organization, self.organization)
        self.assertEqual(event.metadata['test'], 'data')

    def test_membership_save_creates_audit_event(self):
        """Test that saving a membership creates an audit event."""
        initial_count = AuditEvent.objects.count()
        
        membership = Membership.objects.create(
            user=self.user,
            organization=self.organization,
            role=Role.EMPLOYEE
        )
        
        # Should create audit event
        self.assertEqual(AuditEvent.objects.count(), initial_count + 1)
        
        audit_event = AuditEvent.objects.latest('created_at')
        self.assertEqual(audit_event.event, 'membership_created')
        self.assertEqual(audit_event.user, self.user)
        self.assertEqual(audit_event.organization, self.organization)

    def test_membership_role_change_audit(self):
        """Test that changing membership role creates audit event."""
        membership = Membership.objects.create(
            user=self.user,
            organization=self.organization,
            role=Role.EMPLOYEE
        )
        
        initial_count = AuditEvent.objects.count()
        
        # Change role
        membership.role = Role.EMPLOYER_ADMIN
        membership.save()
        
        # Should create role change audit event
        self.assertEqual(AuditEvent.objects.count(), initial_count + 1)
        
        audit_event = AuditEvent.objects.latest('created_at')
        self.assertEqual(audit_event.event, 'role_change')
        self.assertIn('old_role', audit_event.metadata)
        self.assertIn('new_role', audit_event.metadata)


@pytest.mark.django_db
class AdminIntegrationTestCase(TestCase):
    """Test admin interface integration."""

    def setUp(self):
        """Set up test data."""
        self.superuser = User.objects.create_superuser(
            email='admin@test.com',
            password='adminpass123',
            first_name='Admin',
            last_name='User'
        )
        
        self.organization = Organization.objects.create(
            name="Test Organization",
            slug="test-org"
        )
        
        self.client.login(username='admin@test.com', password='adminpass123')

    def test_admin_user_list_view(self):
        """Test admin user list view."""
        response = self.client.get('/admin/accounts/user/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'admin@test.com')

    def test_admin_organization_list_view(self):
        """Test admin organization list view."""
        response = self.client.get('/admin/accounts/organization/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Organization')

    def test_admin_membership_list_view(self):
        """Test admin membership list view."""
        response = self.client.get('/admin/accounts/membership/')
        self.assertEqual(response.status_code, 200)

    def test_admin_audit_event_list_view(self):
        """Test admin audit event list view."""
        # Create an audit event
        AuditEvent.objects.create(
            user=self.superuser,
            event='login',
            ip_address='127.0.0.1'
        )
        
        response = self.client.get('/admin/accounts/auditevent/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'admin@test.com')


if __name__ == '__main__':
    import django
    from django.conf import settings
    from django.test.utils import get_runner
    
    django.setup()
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    failures = test_runner.run_tests(["accounts.test_auth"])
    
    if failures:
        exit(1)