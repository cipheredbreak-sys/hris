from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date, timedelta
from broker_console.models import (
    Broker, Employer, Carrier, Plan, PlanPremium, EmployerOffering,
    Employee, Dependent
)

class Command(BaseCommand):
    help = 'Create sample data for testing the broker console'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample data...')

        # Create a sample broker
        broker, created = Broker.objects.get_or_create(
            agency_name='Alpha Benefits Group',
            defaults={
                'license_number': 'LIC-12345',
                'email': 'contact@alphabenefits.com',
                'phone': '(555) 123-4567',
                'address': '123 Insurance Way, Suite 100\nBoston, MA 02101'
            }
        )
        if created:
            self.stdout.write(f'Created broker: {broker.agency_name}')

        # Create Aetna carrier
        aetna, created = Carrier.objects.get_or_create(
            name='Aetna',
            defaults={
                'code': 'AETNA',
                'is_active': True
            }
        )
        if created:
            self.stdout.write(f'Created carrier: {aetna.name}')

        # Create sample plans
        plans_data = [
            {
                'name': 'Aetna PPO Basic',
                'plan_type': 'medical',
                'external_code': 'AETNA-PPO-BASIC',
                'premiums': {
                    'employee_only': 450.00,
                    'employee_spouse': 850.00,
                    'employee_children': 650.00,
                    'family': 1200.00
                }
            },
            {
                'name': 'Aetna HDHP',
                'plan_type': 'medical',
                'external_code': 'AETNA-HDHP-2024',
                'premiums': {
                    'employee_only': 350.00,
                    'employee_spouse': 650.00,
                    'employee_children': 500.00,
                    'family': 950.00
                }
            },
            {
                'name': 'Aetna Dental PPO',
                'plan_type': 'dental',
                'external_code': 'AETNA-DENTAL-PPO',
                'premiums': {
                    'employee_only': 45.00,
                    'employee_spouse': 85.00,
                    'employee_children': 65.00,
                    'family': 120.00
                }
            },
            {
                'name': 'Aetna Vision Basic',
                'plan_type': 'vision',
                'external_code': 'AETNA-VISION-BASIC',
                'premiums': {
                    'employee_only': 15.00,
                    'employee_spouse': 25.00,
                    'employee_children': 20.00,
                    'family': 35.00
                }
            }
        ]

        for plan_data in plans_data:
            plan, created = Plan.objects.get_or_create(
                carrier=aetna,
                external_code=plan_data['external_code'],
                defaults={
                    'name': plan_data['name'],
                    'plan_type': plan_data['plan_type'],
                    'is_active': True
                }
            )
            if created:
                self.stdout.write(f'Created plan: {plan.name}')

                # Create premiums for each tier
                for tier, premium in plan_data['premiums'].items():
                    PlanPremium.objects.create(
                        plan=plan,
                        coverage_tier=tier,
                        monthly_premium=premium,
                        effective_date=date(2024, 1, 1)
                    )

        # Create sample employers
        employers_data = [
            {
                'name': 'TechStart Inc.',
                'ein': '12-3456789',
                'size': 25,
                'status': 'active',
                'contact_name': 'Sarah Johnson',
                'contact_email': 'sarah.johnson@techstart.com',
                'address': '456 Tech Drive\nCambridge, MA 02139'
            },
            {
                'name': 'Green Energy Solutions',
                'ein': '98-7654321',
                'size': 45,
                'status': 'active',
                'contact_name': 'Mike Chen',
                'contact_email': 'mike.chen@greenenergy.com',
                'address': '789 Solar Lane\nSomerville, MA 02144'
            },
            {
                'name': 'Boston Consulting LLC',
                'ein': '45-6789012',
                'size': 12,
                'status': 'pending',
                'contact_name': 'Emma Rodriguez',
                'contact_email': 'emma.r@bostonconsult.com',
                'address': '321 Business Blvd\nBoston, MA 02115'
            },
            {
                'name': 'Creative Marketing Agency',
                'ein': '67-8901234',
                'size': 35,
                'status': 'active',
                'contact_name': 'David Kim',
                'contact_email': 'david@creativemarketing.com',
                'address': '555 Creative Way\nCambridge, MA 02138'
            }
        ]

        for emp_data in employers_data:
            employer, created = Employer.objects.get_or_create(
                ein=emp_data['ein'],
                defaults={
                    'broker': broker,
                    'name': emp_data['name'],
                    'size': emp_data['size'],
                    'status': emp_data['status'],
                    'effective_date': date(2024, 1, 1),
                    'renewal_date': date(2024, 12, 31),
                    'contact_name': emp_data['contact_name'],
                    'contact_email': emp_data['contact_email'],
                    'contact_phone': '(555) 000-0000',
                    'address': emp_data['address']
                }
            )
            if created:
                self.stdout.write(f'Created employer: {employer.name}')

                # Create sample offerings for active employers
                if employer.status == 'active':
                    medical_plan = Plan.objects.filter(carrier=aetna, plan_type='medical').first()
                    dental_plan = Plan.objects.filter(carrier=aetna, plan_type='dental').first()
                    vision_plan = Plan.objects.filter(carrier=aetna, plan_type='vision').first()

                    if medical_plan:
                        EmployerOffering.objects.get_or_create(
                            employer=employer,
                            plan=medical_plan,
                            defaults={
                                'is_active': True,
                                'contribution_mode': 'percent',
                                'contribution_value': 80.00  # 80% employer contribution
                            }
                        )

                    if dental_plan:
                        EmployerOffering.objects.get_or_create(
                            employer=employer,
                            plan=dental_plan,
                            defaults={
                                'is_active': True,
                                'contribution_mode': 'full',
                                'contribution_value': 0.00  # 100% employer paid
                            }
                        )

                    if vision_plan:
                        EmployerOffering.objects.get_or_create(
                            employer=employer,
                            plan=vision_plan,
                            defaults={
                                'is_active': True,
                                'contribution_mode': 'fixed',
                                'contribution_value': 10.00  # $10 employer contribution
                            }
                        )

        # Create sample employees for the first two employers
        active_employers = Employer.objects.filter(status='active')[:2]
        
        employees_data = [
            {
                'employee_id': 'EMP001',
                'first_name': 'John',
                'last_name': 'Smith',
                'middle_initial': 'A',
                'ssn': '123-45-6789',
                'date_of_birth': date(1985, 3, 15),
                'gender': 'M',
                'marital_status': 'married',
                'email': 'john.smith@company.com',
                'phone': '(555) 123-4567',
                'address_line1': '123 Main St',
                'city': 'Boston',
                'state': 'MA',
                'zip_code': '02101',
                'hire_date': date(2020, 1, 15),
                'job_title': 'Software Engineer',
                'department': 'Engineering',
                'salary': 95000.00,
                'medical_coverage_tier': 'family',
                'dental_coverage_tier': 'family',
                'vision_coverage_tier': 'family'
            },
            {
                'employee_id': 'EMP002',
                'first_name': 'Jane',
                'last_name': 'Doe',
                'middle_initial': 'M',
                'ssn': '987-65-4321',
                'date_of_birth': date(1990, 7, 22),
                'gender': 'F',
                'marital_status': 'single',
                'email': 'jane.doe@company.com',
                'phone': '(555) 987-6543',
                'address_line1': '456 Oak Ave',
                'city': 'Cambridge',
                'state': 'MA',
                'zip_code': '02139',
                'hire_date': date(2021, 6, 1),
                'job_title': 'Product Manager',
                'department': 'Product',
                'salary': 105000.00,
                'medical_coverage_tier': 'employee_only',
                'dental_coverage_tier': 'employee_only',
                'vision_coverage_tier': 'employee_only'
            },
            {
                'employee_id': 'EMP003',
                'first_name': 'Michael',
                'last_name': 'Johnson',
                'middle_initial': 'R',
                'ssn': '555-12-3456',
                'date_of_birth': date(1982, 11, 8),
                'gender': 'M',
                'marital_status': 'married',
                'email': 'michael.johnson@greenenergy.com',
                'phone': '(555) 456-7890',
                'address_line1': '789 Pine St',
                'city': 'Somerville',
                'state': 'MA',
                'zip_code': '02144',
                'hire_date': date(2019, 3, 10),
                'job_title': 'Sales Director',
                'department': 'Sales',
                'salary': 120000.00,
                'medical_coverage_tier': 'employee_spouse',
                'dental_coverage_tier': 'employee_spouse',
                'vision_coverage_tier': 'employee_spouse'
            }
        ]
        
        for i, emp_data in enumerate(employees_data):
            # Assign to different employers
            employer = active_employers[i % len(active_employers)]
            
            employee, created = Employee.objects.get_or_create(
                employer=employer,
                employee_id=emp_data['employee_id'],
                defaults=emp_data
            )
            if created:
                self.stdout.write(f'Created employee: {employee.first_name} {employee.last_name}')
                
                # Create dependents for married employees
                if employee.marital_status == 'married':
                    if employee.first_name == 'John':
                        # Create spouse and child
                        Dependent.objects.get_or_create(
                            employee=employee,
                            first_name='Mary',
                            last_name='Smith',
                            date_of_birth=date(1987, 5, 20),
                            gender='F',
                            relationship='spouse',
                            defaults={
                                'ssn': '111-22-3333',
                                'medical_coverage': True,
                                'dental_coverage': True,
                                'vision_coverage': True
                            }
                        )
                        Dependent.objects.get_or_create(
                            employee=employee,
                            first_name='Tommy',
                            last_name='Smith',
                            date_of_birth=date(2015, 8, 12),
                            gender='M',
                            relationship='child',
                            defaults={
                                'ssn': '444-55-6666',
                                'medical_coverage': True,
                                'dental_coverage': True,
                                'vision_coverage': True
                            }
                        )
                    elif employee.first_name == 'Michael':
                        # Create spouse only
                        Dependent.objects.get_or_create(
                            employee=employee,
                            first_name='Sarah',
                            last_name='Johnson',
                            date_of_birth=date(1984, 9, 15),
                            gender='F',
                            relationship='spouse',
                            defaults={
                                'ssn': '777-88-9999',
                                'medical_coverage': True,
                                'dental_coverage': True,
                                'vision_coverage': True
                            }
                        )

        self.stdout.write(
            self.style.SUCCESS('Successfully created sample data!')
        )
        self.stdout.write(f'Created:')
        self.stdout.write(f'  - {Broker.objects.count()} brokers')
        self.stdout.write(f'  - {Carrier.objects.count()} carriers')
        self.stdout.write(f'  - {Plan.objects.count()} plans')
        self.stdout.write(f'  - {Employer.objects.count()} employers')
        self.stdout.write(f'  - {EmployerOffering.objects.count()} employer offerings')
        self.stdout.write(f'  - {Employee.objects.count()} employees')
        self.stdout.write(f'  - {Dependent.objects.count()} dependents')