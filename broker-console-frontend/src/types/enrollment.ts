export interface EnrollmentPeriod {
  id: string;
  employer: string;
  employer_name: string;
  name: string;
  period_type: 'open_enrollment' | 'initial_enrollment' | 'qualifying_event' | 'special_enrollment';
  status: 'pending' | 'active' | 'closed' | 'cancelled';
  start_date: string;
  end_date: string;
  coverage_effective_date: string;
  allow_waive: boolean;
  require_all_plans: boolean;
  created_at: string;
  updated_at: string;
}

export interface EmployeeEnrollment {
  id: string;
  employee: string;
  employee_name: string;
  employee_last_name: string;
  employee_id: string;
  enrollment_period: string;
  enrollment_period_name: string;
  status: 'not_started' | 'in_progress' | 'submitted' | 'approved' | 'declined' | 'expired';
  started_at?: string;
  submitted_at?: string;
  approved_at?: string;
  approved_by?: string;
  notes: string;
  waived_coverage: boolean;
  waiver_reason: string;
  created_at: string;
  updated_at: string;
}

export interface PlanEnrollment {
  id: string;
  employee_enrollment: string;
  plan: string;
  plan_name: string;
  plan_type: 'medical' | 'dental' | 'vision' | 'life';
  carrier_name: string;
  status: 'enrolled' | 'waived' | 'declined' | 'terminated';
  coverage_tier: 'employee_only' | 'employee_spouse' | 'employee_children' | 'family';
  monthly_premium: number;
  employee_contribution: number;
  employer_contribution: number;
  effective_date: string;
  termination_date?: string;
  covered_dependents: string[];
  covered_dependents_details: Dependent[];
  created_at: string;
  updated_at: string;
}

export interface EnrollmentEvent {
  id: string;
  employee: string;
  employee_name: string;
  employee_last_name: string;
  event_type: 'enrollment' | 'change' | 'termination' | 'reinstatement' | 'dependent_add' | 'dependent_remove' | 'waiver';
  effective_date: string;
  plan_enrollment?: string;
  plan_name?: string;
  previous_coverage_tier: string;
  new_coverage_tier: string;
  reason: string;
  processed_by?: string;
  processed_by_name?: string;
  processed_at: string;
}

export interface Dependent {
  id: string;
  employee: string;
  first_name: string;
  last_name: string;
  middle_initial: string;
  ssn: string;
  date_of_birth: string;
  gender: 'M' | 'F';
  relationship: 'spouse' | 'child' | 'domestic_partner';
  medical_coverage: boolean;
  dental_coverage: boolean;
  vision_coverage: boolean;
}

export interface Plan {
  id: string;
  carrier: string;
  carrier_name: string;
  name: string;
  plan_type: 'medical' | 'dental' | 'vision' | 'life';
  external_code: string;
  is_active: boolean;
}

export interface EmployeeEnrollmentSummary {
  id: string;
  employee_name: string;
  status: string;
  enrollment_period_name: string;
  plan_enrollments_count: number;
  total_premium: number;
  submitted_at?: string;
  waived_coverage: boolean;
}