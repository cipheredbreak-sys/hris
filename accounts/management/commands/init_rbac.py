from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from accounts.models import Organization, Membership, Role, AuditEvent
from broker_console.models import Employee, BenefitPlan  # Import existing models

User = get_user_model()


class Command(BaseCommand):
    help = 'Initialize RBAC system with groups, permissions, and sample data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--create-superuser',
            action='store_true',
            help='Create a superuser account',
        )
        parser.add_argument(
            '--email',
            type=str,
            help='Email for the superuser account',
            default='admin@hris.com'
        )
        parser.add_argument(
            '--password',
            type=str,
            help='Password for the superuser account',
            default='Admin123!@#'
        )
        parser.add_argument(
            '--create-sample-orgs',
            action='store_true',
            help='Create sample organizations',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🚀 Initializing RBAC system...')
        )

        with transaction.atomic():
            # 1. Create Django Groups for each role
            self.create_groups()
            
            # 2. Assign permissions to groups
            self.assign_permissions()
            
            # 3. Create sample organizations if requested
            if options['create_sample_orgs']:
                self.create_sample_organizations()
            
            # 4. Create superuser if requested
            if options['create_superuser']:
                self.create_superuser(options['email'], options['password'])

        self.stdout.write(
            self.style.SUCCESS('✅ RBAC initialization completed!')
        )
        self.print_summary()

    def create_groups(self):
        """Create Django Groups for each role."""
        self.stdout.write('📋 Creating role groups...')
        
        groups_created = 0
        for role_value, role_display in Role.choices:
            group, created = Group.objects.get_or_create(name=role_value)
            if created:
                groups_created += 1
                self.stdout.write(
                    f'  ✓ Created group: {role_display} ({role_value})'
                )
            else:
                self.stdout.write(
                    f'  - Group already exists: {role_display} ({role_value})'
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'📋 Created {groups_created} new groups')
        )

    def assign_permissions(self):
        """Assign permissions to groups based on role hierarchy."""
        self.stdout.write('🔐 Assigning permissions to groups...')
        
        # Get content types for key models
        content_types = {
            'user': ContentType.objects.get_for_model(User),
            'organization': ContentType.objects.get_for_model(Organization),
            'membership': ContentType.objects.get_for_model(Membership),
            'auditevent': ContentType.objects.get_for_model(AuditEvent),
        }
        
        # Add broker_console content types if they exist
        try:
            content_types['employee'] = ContentType.objects.get_for_model(Employee)
            content_types['benefitplan'] = ContentType.objects.get_for_model(BenefitPlan)
        except:
            self.stdout.write(
                self.style.WARNING('⚠️  Broker console models not found, skipping those permissions')
            )

        # Define permission sets for each role
        permission_sets = {
            Role.SUPERUSER: self.get_superuser_permissions(content_types),
            Role.BROKER_ADMIN: self.get_broker_admin_permissions(content_types),
            Role.EMPLOYER_ADMIN: self.get_employer_admin_permissions(content_types),
            Role.EMPLOYEE: self.get_employee_permissions(content_types),
        }

        # Assign permissions to groups
        for role, permissions in permission_sets.items():
            group = Group.objects.get(name=role)
            group.permissions.clear()  # Clear existing permissions
            
            valid_permissions = []
            for perm_codename in permissions:
                try:
                    permission = Permission.objects.get(codename=perm_codename)
                    valid_permissions.append(permission)
                except Permission.DoesNotExist:
                    self.stdout.write(
                        self.style.WARNING(f'⚠️  Permission not found: {perm_codename}')
                    )
            
            group.permissions.set(valid_permissions)
            self.stdout.write(
                f'  ✓ {group.name}: {len(valid_permissions)} permissions assigned'
            )

    def get_superuser_permissions(self, content_types):
        """Get all permissions for superuser."""
        return [
            # User management
            'add_user', 'change_user', 'delete_user', 'view_user',
            # Organization management
            'add_organization', 'change_organization', 'delete_organization', 'view_organization',
            # Membership management
            'add_membership', 'change_membership', 'delete_membership', 'view_membership',
            # Audit access
            'view_auditevent',
            # Employee management (if available)
            'add_employee', 'change_employee', 'delete_employee', 'view_employee',
            # Benefit plan management (if available)
            'add_benefitplan', 'change_benefitplan', 'delete_benefitplan', 'view_benefitplan',
        ]

    def get_broker_admin_permissions(self, content_types):
        """Get permissions for broker admins."""
        return [
            # User management (limited)
            'add_user', 'change_user', 'view_user',
            # Organization management
            'add_organization', 'change_organization', 'view_organization',
            # Membership management
            'add_membership', 'change_membership', 'view_membership',
            # Employee management
            'add_employee', 'change_employee', 'view_employee',
            # Benefit plan management
            'add_benefitplan', 'change_benefitplan', 'view_benefitplan',
        ]

    def get_employer_admin_permissions(self, content_types):
        """Get permissions for employer admins."""
        return [
            # Limited user management
            'view_user', 'change_user',
            # Organization view
            'view_organization',
            # Membership management within their org
            'add_membership', 'change_membership', 'view_membership',
            # Employee management
            'add_employee', 'change_employee', 'view_employee',
            # Benefit plan view
            'view_benefitplan',
        ]

    def get_employee_permissions(self, content_types):
        """Get permissions for employees."""
        return [
            # Self-service permissions
            'view_user', 'change_user',  # Can view/edit own profile
            'view_organization',
            'view_membership',
            'view_employee',  # Can view own employee record
            'view_benefitplan',  # Can view available plans
        ]

    def create_sample_organizations(self):
        """Create sample organizations for testing."""
        self.stdout.write('🏢 Creating sample organizations...')
        
        sample_orgs = [
            {'name': 'Acme Benefits Brokers', 'slug': 'acme-benefits'},
            {'name': 'TechCorp Industries', 'slug': 'techcorp'},
            {'name': 'Healthcare Solutions Inc', 'slug': 'healthcare-solutions'},
        ]
        
        created_count = 0
        for org_data in sample_orgs:
            org, created = Organization.objects.get_or_create(
                slug=org_data['slug'],
                defaults={'name': org_data['name']}
            )
            if created:
                created_count += 1
                self.stdout.write(f'  ✓ Created organization: {org.name}')
            else:
                self.stdout.write(f'  - Organization already exists: {org.name}')
        
        self.stdout.write(
            self.style.SUCCESS(f'🏢 Created {created_count} new organizations')
        )

    def create_superuser(self, email, password):
        """Create a superuser account."""
        self.stdout.write('👤 Creating superuser account...')
        
        # Check if user already exists
        if User.objects.filter(email=email).exists():
            self.stdout.write(
                self.style.WARNING(f'⚠️  User with email {email} already exists')
            )
            return
        
        # Create superuser
        user = User.objects.create_superuser(
            email=email,
            password=password,
            first_name='System',
            last_name='Administrator'
        )
        
        # Add to superuser group
        superuser_group = Group.objects.get(name=Role.SUPERUSER)
        user.groups.add(superuser_group)
        
        self.stdout.write(
            self.style.SUCCESS(f'👤 Created superuser: {email}')
        )
        
        # Create membership in first organization if any exist
        first_org = Organization.objects.first()
        if first_org:
            membership, created = Membership.objects.get_or_create(
                user=user,
                organization=first_org,
                defaults={'role': Role.SUPERUSER}
            )
            if created:
                self.stdout.write(
                    f'  ✓ Added membership to: {first_org.name}'
                )

    def print_summary(self):
        """Print a summary of the RBAC system."""
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('📊 RBAC SYSTEM SUMMARY'))
        self.stdout.write('='*60)
        
        # Groups summary
        groups_count = Group.objects.count()
        self.stdout.write(f'👥 Groups: {groups_count}')
        for group in Group.objects.all():
            perm_count = group.permissions.count()
            self.stdout.write(f'   - {group.name}: {perm_count} permissions')
        
        # Organizations summary
        orgs_count = Organization.objects.count()
        self.stdout.write(f'🏢 Organizations: {orgs_count}')
        for org in Organization.objects.all():
            member_count = org.memberships.count()
            self.stdout.write(f'   - {org.name}: {member_count} members')
        
        # Users summary
        users_count = User.objects.count()
        superusers_count = User.objects.filter(is_superuser=True).count()
        self.stdout.write(f'👤 Users: {users_count} ({superusers_count} superusers)')
        
        # Memberships summary
        memberships_count = Membership.objects.count()
        self.stdout.write(f'🎫 Memberships: {memberships_count}')
        
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('✅ RBAC system is ready to use!'))
        self.stdout.write('='*60)
        
        # Usage instructions
        self.stdout.write('\n📖 USAGE INSTRUCTIONS:')
        self.stdout.write('1. Access admin panel: /admin/')
        self.stdout.write('2. Access authentication: /accounts/login/')
        self.stdout.write('3. API documentation: /swagger/')
        self.stdout.write('4. Create users through admin or API endpoints')
        self.stdout.write('5. Assign users to organizations via Membership model')
        
        if User.objects.filter(is_superuser=True).exists():
            superuser = User.objects.filter(is_superuser=True).first()
            self.stdout.write(f'\n🔑 Admin login: {superuser.email}')
        
        self.stdout.write('\n🎉 Happy coding!')