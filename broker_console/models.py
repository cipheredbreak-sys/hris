from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid

User = get_user_model()

class TimeStampedModel(models.Model):
    """Base model with created_at and updated_at fields"""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True

class Broker(TimeStampedModel):
    """Broker/Agency model"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agency_name = models.CharField(max_length=255)
    license_number = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    
    def __str__(self):
        return self.agency_name
    
    class Meta:
        ordering = ['agency_name']

class BrokerUser(TimeStampedModel):
    """Users belonging to a broker"""
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('user', 'User'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    broker = models.ForeignKey(Broker, on_delete=models.CASCADE, related_name='users')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.user.email} ({self.broker.agency_name})"
    
    class Meta:
        unique_together = ['user', 'broker']

class Employer(TimeStampedModel):
    """Employer/Company model"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('terminated', 'Terminated'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    broker = models.ForeignKey(Broker, on_delete=models.CASCADE, related_name='employers')
    name = models.CharField(max_length=255)
    ein = models.CharField(max_length=11, unique=True, help_text="Format: XX-XXXXXXX")
    size = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        help_text="Number of employees (max 100 for small group)"
    )
    effective_date = models.DateField()
    renewal_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    
    # Contact information
    contact_name = models.CharField(max_length=255, blank=True)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.name} ({self.size} employees)"
    
    class Meta:
        ordering = ['name']

class Carrier(TimeStampedModel):
    """Insurance carriers (Aetna, etc.)"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=10, unique=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']

class Plan(TimeStampedModel):
    """Insurance plans offered by carriers"""
    PLAN_TYPES = [
        ('medical', 'Medical'),
        ('dental', 'Dental'),
        ('vision', 'Vision'),
        ('life', 'Life/AD&D'),
    ]
    
    COVERAGE_TIERS = [
        ('employee_only', 'Employee Only'),
        ('employee_spouse', 'Employee + Spouse'),
        ('employee_children', 'Employee + Child(ren)'),
        ('family', 'Family'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    carrier = models.ForeignKey(Carrier, on_delete=models.CASCADE, related_name='plans')
    name = models.CharField(max_length=255)
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPES)
    external_code = models.CharField(max_length=50, help_text="Carrier's plan code")
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.carrier.name} - {self.name}"
    
    class Meta:
        ordering = ['carrier__name', 'plan_type', 'name']
        unique_together = ['carrier', 'external_code']

class PlanPremium(TimeStampedModel):
    """Premium rates for plans by coverage tier"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE, related_name='premiums')
    coverage_tier = models.CharField(max_length=20, choices=Plan.COVERAGE_TIERS)
    monthly_premium = models.DecimalField(max_digits=10, decimal_places=2)
    effective_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.plan.name} - {self.coverage_tier}: ${self.monthly_premium}"
    
    class Meta:
        ordering = ['plan', 'coverage_tier', 'effective_date']

class EmployerOffering(TimeStampedModel):
    """Plans offered by an employer with contribution settings"""
    CONTRIBUTION_MODES = [
        ('full', 'Full (100%)'),
        ('percent', 'Percentage'),
        ('fixed', 'Fixed Amount'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employer = models.ForeignKey(Employer, on_delete=models.CASCADE, related_name='offerings')
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    
    # Contribution settings
    contribution_mode = models.CharField(max_length=10, choices=CONTRIBUTION_MODES, default='full')
    contribution_value = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        help_text="Percentage (0-100) or fixed dollar amount"
    )
    
    def __str__(self):
        return f"{self.employer.name} - {self.plan.name}"
    
    class Meta:
        unique_together = ['employer', 'plan']
        ordering = ['employer', 'plan']

class CarrierCsvTemplate(TimeStampedModel):
    """CSV export templates for different carriers"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    carrier = models.ForeignKey(Carrier, on_delete=models.CASCADE, related_name='csv_templates')
    name = models.CharField(max_length=100)
    coverage_type = models.CharField(max_length=20, choices=Plan.PLAN_TYPES)
    template_fields = models.JSONField(help_text="Array of field definitions")
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.carrier.name} - {self.name}"
    
    class Meta:
        ordering = ['carrier', 'coverage_type', 'name']

class ExportJob(TimeStampedModel):
    """Track export job status and errors"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employer = models.ForeignKey(Employer, on_delete=models.CASCADE, related_name='export_jobs')
    carrier = models.ForeignKey(Carrier, on_delete=models.CASCADE)
    coverage_type = models.CharField(max_length=20, choices=Plan.PLAN_TYPES)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    file_name = models.CharField(max_length=255, blank=True)
    error_details = models.JSONField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"Export {self.id} - {self.employer.name} ({self.status})"
    
    class Meta:
        ordering = ['-created_at']

class Employee(TimeStampedModel):
    """Employee records for census export"""
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
    ]
    
    MARITAL_STATUS_CHOICES = [
        ('single', 'Single'),
        ('married', 'Married'),
        ('divorced', 'Divorced'),
        ('widowed', 'Widowed'),
    ]
    
    COVERAGE_TIER_CHOICES = [
        ('employee_only', 'Employee Only'),
        ('employee_spouse', 'Employee + Spouse'),
        ('employee_children', 'Employee + Child(ren)'),
        ('family', 'Family'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employer = models.ForeignKey(Employer, on_delete=models.CASCADE, related_name='employees')
    
    # Personal Information
    employee_id = models.CharField(max_length=50, help_text="Employer's employee ID")
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    middle_initial = models.CharField(max_length=1, blank=True)
    ssn = models.CharField(max_length=11, help_text="Format: XXX-XX-XXXX")
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    marital_status = models.CharField(max_length=10, choices=MARITAL_STATUS_CHOICES, default='single')
    
    # Contact Information
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=2)
    zip_code = models.CharField(max_length=10)
    
    # Employment Information
    hire_date = models.DateField()
    job_title = models.CharField(max_length=100, blank=True)
    department = models.CharField(max_length=100, blank=True)
    salary = models.DecimalField(max_digits=10, decimal_places=2, help_text="Annual salary")
    hours_per_week = models.DecimalField(max_digits=4, decimal_places=1, default=40.0)
    employment_status = models.CharField(max_length=20, default='active')
    
    # Benefit Elections
    medical_coverage_tier = models.CharField(max_length=20, choices=COVERAGE_TIER_CHOICES, blank=True)
    dental_coverage_tier = models.CharField(max_length=20, choices=COVERAGE_TIER_CHOICES, blank=True)
    vision_coverage_tier = models.CharField(max_length=20, choices=COVERAGE_TIER_CHOICES, blank=True)
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.employee_id})"
    
    class Meta:
        ordering = ['employer', 'last_name', 'first_name']
        unique_together = ['employer', 'employee_id']

class Dependent(TimeStampedModel):
    """Employee dependents for coverage"""
    RELATIONSHIP_CHOICES = [
        ('spouse', 'Spouse'),
        ('child', 'Child'),
        ('domestic_partner', 'Domestic Partner'),
    ]
    
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='dependents')
    
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    middle_initial = models.CharField(max_length=1, blank=True)
    ssn = models.CharField(max_length=11, blank=True, help_text="Format: XXX-XX-XXXX")
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    relationship = models.CharField(max_length=20, choices=RELATIONSHIP_CHOICES)
    
    # Coverage elections
    medical_coverage = models.BooleanField(default=False)
    dental_coverage = models.BooleanField(default=False)
    vision_coverage = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.relationship} of {self.employee})"
    
    class Meta:
        ordering = ['employee', 'relationship', 'last_name']

class EnrollmentPeriod(TimeStampedModel):
    """Open enrollment or qualifying event periods"""
    PERIOD_TYPES = [
        ('open_enrollment', 'Open Enrollment'),
        ('initial_enrollment', 'Initial Enrollment'),
        ('qualifying_event', 'Qualifying Life Event'),
        ('special_enrollment', 'Special Enrollment'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('closed', 'Closed'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employer = models.ForeignKey(Employer, on_delete=models.CASCADE, related_name='enrollment_periods')
    name = models.CharField(max_length=255)
    period_type = models.CharField(max_length=20, choices=PERIOD_TYPES)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    
    # Period dates
    start_date = models.DateField()
    end_date = models.DateField()
    coverage_effective_date = models.DateField()
    
    # Configuration
    allow_waive = models.BooleanField(default=True, help_text="Allow employees to waive coverage")
    require_all_plans = models.BooleanField(default=False, help_text="Require election for all plan types")
    
    def __str__(self):
        return f"{self.employer.name} - {self.name} ({self.coverage_effective_date})"
    
    class Meta:
        ordering = ['-coverage_effective_date', 'employer']

class EmployeeEnrollment(TimeStampedModel):
    """Employee's enrollment in a specific enrollment period"""
    STATUS_CHOICES = [
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('declined', 'Declined'),
        ('expired', 'Expired'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='enrollments')
    enrollment_period = models.ForeignKey(EnrollmentPeriod, on_delete=models.CASCADE, related_name='employee_enrollments')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='not_started')
    
    # Enrollment tracking
    started_at = models.DateTimeField(null=True, blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Enrollment data
    notes = models.TextField(blank=True)
    waived_coverage = models.BooleanField(default=False)
    waiver_reason = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.employee} - {self.enrollment_period.name} ({self.status})"
    
    class Meta:
        unique_together = ['employee', 'enrollment_period']
        ordering = ['-enrollment_period__coverage_effective_date', 'employee']

class PlanEnrollment(TimeStampedModel):
    """Employee's enrollment in a specific plan"""
    STATUS_CHOICES = [
        ('enrolled', 'Enrolled'),
        ('waived', 'Waived'),
        ('declined', 'Declined'),
        ('terminated', 'Terminated'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee_enrollment = models.ForeignKey(EmployeeEnrollment, on_delete=models.CASCADE, related_name='plan_enrollments')
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='enrolled')
    
    # Coverage details
    coverage_tier = models.CharField(max_length=20, choices=Plan.COVERAGE_TIERS)
    monthly_premium = models.DecimalField(max_digits=10, decimal_places=2)
    employee_contribution = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    employer_contribution = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Effective dates
    effective_date = models.DateField()
    termination_date = models.DateField(null=True, blank=True)
    
    # Covered dependents
    covered_dependents = models.ManyToManyField(Dependent, blank=True, help_text="Dependents covered under this enrollment")
    
    def __str__(self):
        return f"{self.employee_enrollment.employee} - {self.plan.name} ({self.status})"
    
    class Meta:
        unique_together = ['employee_enrollment', 'plan']
        ordering = ['employee_enrollment', 'plan']

class EnrollmentEvent(TimeStampedModel):
    """Track enrollment events and changes"""
    EVENT_TYPES = [
        ('enrollment', 'New Enrollment'),
        ('change', 'Plan Change'),
        ('termination', 'Coverage Termination'),
        ('reinstatement', 'Coverage Reinstatement'),
        ('dependent_add', 'Dependent Added'),
        ('dependent_remove', 'Dependent Removed'),
        ('waiver', 'Coverage Waived'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='enrollment_events')
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    effective_date = models.DateField()
    
    # Event details
    plan_enrollment = models.ForeignKey(PlanEnrollment, on_delete=models.SET_NULL, null=True, blank=True)
    previous_coverage_tier = models.CharField(max_length=20, choices=Plan.COVERAGE_TIERS, blank=True)
    new_coverage_tier = models.CharField(max_length=20, choices=Plan.COVERAGE_TIERS, blank=True)
    
    # Audit trail
    reason = models.TextField(blank=True)
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    processed_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.employee} - {self.event_type} ({self.effective_date})"
    
    class Meta:
        ordering = ['-effective_date', '-processed_at']

class EmployeeFormSubmission(TimeStampedModel):
    """Employee form submissions for employer review"""
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('changes_requested', 'Changes Requested'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employer = models.ForeignKey(Employer, on_delete=models.CASCADE, related_name='form_submissions')
    
    # Employee Information
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    date_of_birth = models.DateField()
    ssn = models.CharField(max_length=11, help_text="Format: XXX-XX-XXXX")
    
    # Address Information
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=2)
    zip_code = models.CharField(max_length=10)
    
    # Employment Information
    hire_date = models.DateField()
    job_title = models.CharField(max_length=100, blank=True)
    department = models.CharField(max_length=100, blank=True)
    salary = models.DecimalField(max_digits=10, decimal_places=2)
    hours_per_week = models.DecimalField(max_digits=4, decimal_places=1, default=40.0)
    
    # Emergency Contact
    emergency_contact_name = models.CharField(max_length=255, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)
    emergency_contact_relationship = models.CharField(max_length=50, blank=True)
    
    # Form Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    
    # If approved, link to created employee record
    created_employee = models.OneToOneField(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='form_submission')
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.employer.name} ({self.status})"
    
    class Meta:
        ordering = ['-created_at']

class EmployeePortalUser(TimeStampedModel):
    """Portal access for employees to check their status and manage profile"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.OneToOneField(Employee, on_delete=models.CASCADE, null=True, blank=True, related_name='portal_user')
    form_submission = models.OneToOneField(EmployeeFormSubmission, on_delete=models.CASCADE, null=True, blank=True, related_name='portal_user')
    
    # Authentication fields
    email = models.EmailField(unique=True)
    password_hash = models.CharField(max_length=255)
    
    # Access control
    is_active = models.BooleanField(default=True)
    last_login = models.DateTimeField(null=True, blank=True)
    password_reset_token = models.CharField(max_length=255, blank=True)
    password_reset_expires = models.DateTimeField(null=True, blank=True)
    
    # Verification status
    email_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=255, blank=True)
    
    def set_password(self, raw_password):
        """Hash and set password"""
        import hashlib
        self.password_hash = hashlib.sha256(raw_password.encode()).hexdigest()
    
    def check_password(self, raw_password):
        """Check if provided password matches stored hash"""
        import hashlib
        return self.password_hash == hashlib.sha256(raw_password.encode()).hexdigest()
    
    @property
    def full_name(self):
        if self.employee:
            return f"{self.employee.first_name} {self.employee.last_name}"
        elif self.form_submission:
            return f"{self.form_submission.first_name} {self.form_submission.last_name}"
        return self.email
    
    @property
    def status(self):
        if self.employee:
            return 'active_employee'
        elif self.form_submission:
            return self.form_submission.status
        return 'no_submission'
    
    def __str__(self):
        return f"{self.email} - {self.full_name}"
    
    class Meta:
        ordering = ['-created_at']
