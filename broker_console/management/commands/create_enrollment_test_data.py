from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date, timedelta
from broker_console.models import (
    Broker, Employer, Carrier, Plan, PlanPremium, EmployerOffering,
    Employee, EnrollmentPeriod, EmployeeEnrollment
)


class Command(BaseCommand):
    help = 'Create test data for enrollment functionality'

    def handle(self, *args, **options):
        self.stdout.write("Creating enrollment test data...")

        # Create or get carrier
        carrier, created = Carrier.objects.get_or_create(
            name='Aetna',
            defaults={'code': 'AETNA', 'is_active': True}
        )
        if created:
            self.stdout.write(f"Created carrier: {carrier.name}")

        # Create or get broker
        broker, created = Broker.objects.get_or_create(
            agency_name='Test Broker Agency',
            defaults={
                'license_number': 'LIC123456',
                'phone': '555-123-4567',
                'email': 'broker@test.com',
                'address': '123 Broker St, Test City, TC 12345'
            }
        )
        if created:
            self.stdout.write(f"Created broker: {broker.agency_name}")

        # Create or get employer
        employer, created = Employer.objects.get_or_create(
            name='Test Company LLC',
            ein='12-3456789',
            defaults={
                'broker': broker,
                'size': 25,
                'effective_date': date.today(),
                'renewal_date': date.today() + timedelta(days=365),
                'status': 'active',
                'contact_name': 'HR Manager',
                'contact_email': 'hr@testcompany.com',
                'contact_phone': '555-987-6543',
                'address': '456 Company Ave, Test City, TC 12345'
            }
        )
        if created:
            self.stdout.write(f"Created employer: {employer.name}")

        # Create plans
        plan_configs = [
            {'name': 'Aetna Basic Medical', 'plan_type': 'medical', 'external_code': 'AETNA-MED-001'},
            {'name': 'Aetna Premium Medical', 'plan_type': 'medical', 'external_code': 'AETNA-MED-002'},
            {'name': 'Aetna Dental', 'plan_type': 'dental', 'external_code': 'AETNA-DEN-001'},
            {'name': 'Aetna Vision', 'plan_type': 'vision', 'external_code': 'AETNA-VIS-001'},
        ]

        plans = []
        for config in plan_configs:
            plan, created = Plan.objects.get_or_create(
                carrier=carrier,
                external_code=config['external_code'],
                defaults={
                    'name': config['name'],
                    'plan_type': config['plan_type'],
                    'is_active': True
                }
            )
            plans.append(plan)
            if created:
                self.stdout.write(f"Created plan: {plan.name}")

                # Create premium rates for each coverage tier
                coverage_tiers = [
                    ('employee_only', 150.00),
                    ('employee_spouse', 300.00),
                    ('employee_children', 250.00),
                    ('family', 450.00),
                ]

                for tier, premium in coverage_tiers:
                    PlanPremium.objects.get_or_create(
                        plan=plan,
                        coverage_tier=tier,
                        defaults={
                            'monthly_premium': premium,
                            'effective_date': date.today(),
                        }
                    )

        # Create employer offerings
        for plan in plans:
            offering, created = EmployerOffering.objects.get_or_create(
                employer=employer,
                plan=plan,
                defaults={
                    'is_active': True,
                    'contribution_mode': 'percent',
                    'contribution_value': 80.0,  # 80% employer contribution
                }
            )
            if created:
                self.stdout.write(f"Created offering: {employer.name} - {plan.name}")

        # Create enrollment period
        start_date = date.today()
        end_date = start_date + timedelta(days=30)
        effective_date = start_date + timedelta(days=45)

        enrollment_period, created = EnrollmentPeriod.objects.get_or_create(
            employer=employer,
            name='2024 Open Enrollment',
            defaults={
                'period_type': 'open_enrollment',
                'status': 'active',
                'start_date': start_date,
                'end_date': end_date,
                'coverage_effective_date': effective_date,
                'allow_waive': True,
                'require_all_plans': False,
            }
        )
        if created:
            self.stdout.write(f"Created enrollment period: {enrollment_period.name}")

        # Create test employees
        employees_data = [
            {
                'employee_id': 'EMP001',
                'first_name': 'John',
                'last_name': 'Smith',
                'email': 'john.smith@testcompany.com',
                'date_of_birth': date(1985, 3, 15),
                'gender': 'M',
                'hire_date': date(2020, 1, 15),
                'salary': 75000.00,
                'address_line1': '123 Main St',
                'city': 'Test City',
                'state': 'TC',
                'zip_code': '12345',
            },
            {
                'employee_id': 'EMP002',
                'first_name': 'Jane',
                'last_name': 'Doe',
                'email': 'jane.doe@testcompany.com',
                'date_of_birth': date(1990, 7, 22),
                'gender': 'F',
                'hire_date': date(2021, 6, 1),
                'salary': 85000.00,
                'address_line1': '456 Oak Ave',
                'city': 'Test City',
                'state': 'TC',
                'zip_code': '12345',
            },
            {
                'employee_id': 'EMP003',
                'first_name': 'Mike',
                'last_name': 'Johnson',
                'email': 'mike.johnson@testcompany.com',
                'date_of_birth': date(1988, 11, 8),
                'gender': 'M',
                'hire_date': date(2019, 9, 10),
                'salary': 92000.00,
                'address_line1': '789 Pine Rd',
                'city': 'Test City',
                'state': 'TC',
                'zip_code': '12345',
            },
        ]

        employees = []
        for emp_data in employees_data:
            employee, created = Employee.objects.get_or_create(
                employer=employer,
                employee_id=emp_data['employee_id'],
                defaults=emp_data
            )
            employees.append(employee)
            if created:
                self.stdout.write(f"Created employee: {employee.first_name} {employee.last_name}")

                # Create employee enrollment for the enrollment period
                employee_enrollment, enrollment_created = EmployeeEnrollment.objects.get_or_create(
                    employee=employee,
                    enrollment_period=enrollment_period,
                    defaults={
                        'status': 'not_started',
                    }
                )
                if enrollment_created:
                    self.stdout.write(f"Created enrollment for: {employee.first_name} {employee.last_name}")

        self.stdout.write(self.style.SUCCESS('Successfully created enrollment test data!'))
        self.stdout.write(f"Created:")
        self.stdout.write(f"- 1 Carrier: {carrier.name}")
        self.stdout.write(f"- 1 Broker: {broker.agency_name}")
        self.stdout.write(f"- 1 Employer: {employer.name}")
        self.stdout.write(f"- {len(plans)} Plans")
        self.stdout.write(f"- {len(plans)} Employer Offerings")
        self.stdout.write(f"- 1 Enrollment Period: {enrollment_period.name}")
        self.stdout.write(f"- {len(employees)} Employees")
        self.stdout.write(f"- {len(employees)} Employee Enrollments")