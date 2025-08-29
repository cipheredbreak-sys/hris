import { EnrollmentPeriod, EmployeeEnrollment, PlanEnrollment, EnrollmentEvent, EmployeeEnrollmentSummary } from '../types/enrollment';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

class EnrollmentService {
  private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
      ...options,
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();
  }

  // Enrollment Periods
  async getEnrollmentPeriods(): Promise<EnrollmentPeriod[]> {
    return this.request('/api/enrollment-periods/');
  }

  async getEnrollmentPeriod(id: string): Promise<EnrollmentPeriod> {
    return this.request(`/api/enrollment-periods/${id}/`);
  }

  async getEnrollmentPeriodsByEmployer(employerId: string): Promise<EnrollmentPeriod[]> {
    return this.request(`/api/enrollment-periods/by_employer/?employer_id=${employerId}`);
  }

  async getActiveEnrollmentPeriods(): Promise<EnrollmentPeriod[]> {
    return this.request('/api/enrollment-periods/active/');
  }

  async createEnrollmentPeriod(period: Partial<EnrollmentPeriod>): Promise<EnrollmentPeriod> {
    return this.request('/api/enrollment-periods/', {
      method: 'POST',
      body: JSON.stringify(period),
    });
  }

  async updateEnrollmentPeriod(id: string, period: Partial<EnrollmentPeriod>): Promise<EnrollmentPeriod> {
    return this.request(`/api/enrollment-periods/${id}/`, {
      method: 'PUT',
      body: JSON.stringify(period),
    });
  }

  // Employee Enrollments
  async getEmployeeEnrollments(): Promise<EmployeeEnrollment[]> {
    return this.request('/api/employee-enrollments/');
  }

  async getEmployeeEnrollment(id: string): Promise<EmployeeEnrollment> {
    return this.request(`/api/employee-enrollments/${id}/`);
  }

  async getEmployeeEnrollmentsByEmployee(employeeId: string): Promise<EmployeeEnrollment[]> {
    return this.request(`/api/employee-enrollments/by_employee/?employee_id=${employeeId}`);
  }

  async getEmployeeEnrollmentsByPeriod(periodId: string): Promise<EmployeeEnrollment[]> {
    return this.request(`/api/employee-enrollments/by_period/?period_id=${periodId}`);
  }

  async getEmployeeEnrollmentsSummary(periodId: string): Promise<EmployeeEnrollmentSummary[]> {
    return this.request(`/api/employee-enrollments/summary/?period_id=${periodId}`);
  }

  async createEmployeeEnrollment(enrollment: Partial<EmployeeEnrollment>): Promise<EmployeeEnrollment> {
    return this.request('/api/employee-enrollments/', {
      method: 'POST',
      body: JSON.stringify(enrollment),
    });
  }

  async updateEmployeeEnrollment(id: string, enrollment: Partial<EmployeeEnrollment>): Promise<EmployeeEnrollment> {
    return this.request(`/api/employee-enrollments/${id}/`, {
      method: 'PUT',
      body: JSON.stringify(enrollment),
    });
  }

  async startEnrollment(id: string): Promise<EmployeeEnrollment> {
    return this.request(`/api/employee-enrollments/${id}/start_enrollment/`, {
      method: 'POST',
    });
  }

  async submitEnrollment(id: string): Promise<EmployeeEnrollment> {
    return this.request(`/api/employee-enrollments/${id}/submit_enrollment/`, {
      method: 'POST',
    });
  }

  async approveEnrollment(id: string): Promise<EmployeeEnrollment> {
    return this.request(`/api/employee-enrollments/${id}/approve_enrollment/`, {
      method: 'POST',
    });
  }

  // Plan Enrollments
  async getPlanEnrollments(): Promise<PlanEnrollment[]> {
    return this.request('/api/plan-enrollments/');
  }

  async getPlanEnrollment(id: string): Promise<PlanEnrollment> {
    return this.request(`/api/plan-enrollments/${id}/`);
  }

  async getPlanEnrollmentsByEmployeeEnrollment(enrollmentId: string): Promise<PlanEnrollment[]> {
    return this.request(`/api/plan-enrollments/by_employee_enrollment/?enrollment_id=${enrollmentId}`);
  }

  async getPlanEnrollmentsByPlan(planId: string): Promise<PlanEnrollment[]> {
    return this.request(`/api/plan-enrollments/by_plan/?plan_id=${planId}`);
  }

  async createPlanEnrollment(planEnrollment: Partial<PlanEnrollment>): Promise<PlanEnrollment> {
    return this.request('/api/plan-enrollments/', {
      method: 'POST',
      body: JSON.stringify(planEnrollment),
    });
  }

  async updatePlanEnrollment(id: string, planEnrollment: Partial<PlanEnrollment>): Promise<PlanEnrollment> {
    return this.request(`/api/plan-enrollments/${id}/`, {
      method: 'PUT',
      body: JSON.stringify(planEnrollment),
    });
  }

  async terminatePlanEnrollment(id: string, terminationDate: string, reason: string): Promise<PlanEnrollment> {
    return this.request(`/api/plan-enrollments/${id}/terminate/`, {
      method: 'POST',
      body: JSON.stringify({
        termination_date: terminationDate,
        reason: reason,
      }),
    });
  }

  // Enrollment Events
  async getEnrollmentEvents(): Promise<EnrollmentEvent[]> {
    return this.request('/api/enrollment-events/');
  }

  async getEnrollmentEventsByEmployee(employeeId: string): Promise<EnrollmentEvent[]> {
    return this.request(`/api/enrollment-events/by_employee/?employee_id=${employeeId}`);
  }

  async getRecentEnrollmentEvents(): Promise<EnrollmentEvent[]> {
    return this.request('/api/enrollment-events/recent/');
  }
}

export const enrollmentService = new EnrollmentService();