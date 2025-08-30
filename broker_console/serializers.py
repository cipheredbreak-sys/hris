from rest_framework import serializers
from .models import (
    Broker, BrokerUser, Employer, Carrier, Plan, 
    PlanPremium, EmployerOffering, CarrierCsvTemplate, ExportJob,
    Employee, Dependent, EnrollmentPeriod, EmployeeEnrollment,
    PlanEnrollment, EnrollmentEvent, EmployeeFormSubmission, EmployeePortalUser
)

class BrokerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Broker
        fields = '__all__'

class CarrierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Carrier
        fields = '__all__'

class PlanSerializer(serializers.ModelSerializer):
    carrier_name = serializers.CharField(source='carrier.name', read_only=True)
    
    class Meta:
        model = Plan
        fields = '__all__'

class PlanPremiumSerializer(serializers.ModelSerializer):
    plan_name = serializers.CharField(source='plan.name', read_only=True)
    
    class Meta:
        model = PlanPremium
        fields = '__all__'

class EmployerSerializer(serializers.ModelSerializer):
    broker_name = serializers.CharField(source='broker.agency_name', read_only=True)
    
    class Meta:
        model = Employer
        fields = '__all__'

class EmployerOfferingSerializer(serializers.ModelSerializer):
    employer_name = serializers.CharField(source='employer.name', read_only=True)
    plan_name = serializers.CharField(source='plan.name', read_only=True)
    plan_type = serializers.CharField(source='plan.plan_type', read_only=True)
    carrier_name = serializers.CharField(source='plan.carrier.name', read_only=True)
    
    class Meta:
        model = EmployerOffering
        fields = '__all__'

class CarrierCsvTemplateSerializer(serializers.ModelSerializer):
    carrier_name = serializers.CharField(source='carrier.name', read_only=True)
    
    class Meta:
        model = CarrierCsvTemplate
        fields = '__all__'

class ExportJobSerializer(serializers.ModelSerializer):
    employer_name = serializers.CharField(source='employer.name', read_only=True)
    carrier_name = serializers.CharField(source='carrier.name', read_only=True)
    
    class Meta:
        model = ExportJob
        fields = '__all__'

# Detailed serializers for specific endpoints
class EmployerDetailSerializer(serializers.ModelSerializer):
    broker = BrokerSerializer(read_only=True)
    offerings = EmployerOfferingSerializer(many=True, read_only=True)
    
    class Meta:
        model = Employer
        fields = '__all__'

class PlanDetailSerializer(serializers.ModelSerializer):
    carrier = CarrierSerializer(read_only=True)
    premiums = PlanPremiumSerializer(many=True, read_only=True)
    
    class Meta:
        model = Plan
        fields = '__all__'

class DependentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dependent
        fields = '__all__'

class EmployeeSerializer(serializers.ModelSerializer):
    employer_name = serializers.CharField(source='employer.name', read_only=True)
    dependents = DependentSerializer(many=True, read_only=True)
    
    class Meta:
        model = Employee
        fields = '__all__'

class EmployeeDetailSerializer(serializers.ModelSerializer):
    employer = EmployerSerializer(read_only=True)
    dependents = DependentSerializer(many=True, read_only=True)
    
    class Meta:
        model = Employee
        fields = '__all__'

class EnrollmentPeriodSerializer(serializers.ModelSerializer):
    employer_name = serializers.CharField(source='employer.name', read_only=True)
    
    class Meta:
        model = EnrollmentPeriod
        fields = '__all__'

class EmployeeEnrollmentSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.first_name', read_only=True)
    employee_last_name = serializers.CharField(source='employee.last_name', read_only=True)
    employee_id = serializers.CharField(source='employee.employee_id', read_only=True)
    enrollment_period_name = serializers.CharField(source='enrollment_period.name', read_only=True)
    
    class Meta:
        model = EmployeeEnrollment
        fields = '__all__'

class PlanEnrollmentSerializer(serializers.ModelSerializer):
    plan_name = serializers.CharField(source='plan.name', read_only=True)
    plan_type = serializers.CharField(source='plan.plan_type', read_only=True)
    carrier_name = serializers.CharField(source='plan.carrier.name', read_only=True)
    employee_name = serializers.CharField(source='employee_enrollment.employee.first_name', read_only=True)
    employee_last_name = serializers.CharField(source='employee_enrollment.employee.last_name', read_only=True)
    covered_dependents_details = DependentSerializer(source='covered_dependents', many=True, read_only=True)
    
    class Meta:
        model = PlanEnrollment
        fields = '__all__'

class EnrollmentEventSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.first_name', read_only=True)
    employee_last_name = serializers.CharField(source='employee.last_name', read_only=True)
    processed_by_name = serializers.CharField(source='processed_by.email', read_only=True)
    plan_name = serializers.CharField(source='plan_enrollment.plan.name', read_only=True)
    
    class Meta:
        model = EnrollmentEvent
        fields = '__all__'

class EnrollmentPeriodDetailSerializer(serializers.ModelSerializer):
    employer = EmployerSerializer(read_only=True)
    employee_enrollments = EmployeeEnrollmentSerializer(many=True, read_only=True)
    
    class Meta:
        model = EnrollmentPeriod
        fields = '__all__'

class EmployeeEnrollmentDetailSerializer(serializers.ModelSerializer):
    employee = EmployeeSerializer(read_only=True)
    enrollment_period = EnrollmentPeriodSerializer(read_only=True)
    plan_enrollments = PlanEnrollmentSerializer(many=True, read_only=True)
    
    class Meta:
        model = EmployeeEnrollment
        fields = '__all__'

class EmployeeEnrollmentSummarySerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()
    plan_enrollments_count = serializers.SerializerMethodField()
    total_premium = serializers.SerializerMethodField()
    enrollment_period_name = serializers.CharField(source='enrollment_period.name', read_only=True)
    
    class Meta:
        model = EmployeeEnrollment
        fields = ['id', 'employee_name', 'status', 'enrollment_period_name', 
                 'plan_enrollments_count', 'total_premium', 'submitted_at', 'waived_coverage']
    
    def get_employee_name(self, obj):
        return f"{obj.employee.first_name} {obj.employee.last_name}"
    
    def get_plan_enrollments_count(self, obj):
        return obj.plan_enrollments.filter(status='enrolled').count()
    
    def get_total_premium(self, obj):
        return sum(pe.employee_contribution for pe in obj.plan_enrollments.filter(status='enrolled'))

class EmployeeFormSubmissionSerializer(serializers.ModelSerializer):
    employer_name = serializers.CharField(source='employer.name', read_only=True)
    reviewed_by_name = serializers.CharField(source='reviewed_by.email', read_only=True)
    
    class Meta:
        model = EmployeeFormSubmission
        fields = '__all__'

class EmployeeFormSubmissionListSerializer(serializers.ModelSerializer):
    employer_name = serializers.CharField(source='employer.name', read_only=True)
    
    class Meta:
        model = EmployeeFormSubmission
        fields = ['id', 'first_name', 'last_name', 'email', 'status', 'created_at', 'employer_name']

class EmployeePortalUserSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()
    status = serializers.ReadOnlyField()
    employee_data = EmployeeSerializer(source='employee', read_only=True)
    form_submission_data = EmployeeFormSubmissionSerializer(source='form_submission', read_only=True)
    
    class Meta:
        model = EmployeePortalUser
        fields = ['id', 'email', 'full_name', 'status', 'is_active', 'last_login', 
                 'email_verified', 'employee_data', 'form_submission_data', 'created_at']
        extra_kwargs = {
            'password_hash': {'write_only': True},
        }

class EmployeePortalLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    
class EmployeePortalRegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    form_submission_id = serializers.UUIDField(required=False)