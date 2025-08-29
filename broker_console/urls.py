from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    BrokerViewSet, CarrierViewSet, PlanViewSet, 
    EmployerViewSet, EmployerOfferingViewSet, ExportJobViewSet,
    EmployeeViewSet, DependentViewSet, EnrollmentPeriodViewSet,
    EmployeeEnrollmentViewSet, PlanEnrollmentViewSet, EnrollmentEventViewSet
)

router = DefaultRouter()
router.register(r'brokers', BrokerViewSet)
router.register(r'carriers', CarrierViewSet)
router.register(r'plans', PlanViewSet)
router.register(r'employers', EmployerViewSet)
router.register(r'employer-offerings', EmployerOfferingViewSet)
router.register(r'export-jobs', ExportJobViewSet)
router.register(r'employees', EmployeeViewSet)
router.register(r'dependents', DependentViewSet)
router.register(r'enrollment-periods', EnrollmentPeriodViewSet)
router.register(r'employee-enrollments', EmployeeEnrollmentViewSet)
router.register(r'plan-enrollments', PlanEnrollmentViewSet)
router.register(r'enrollment-events', EnrollmentEventViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
]