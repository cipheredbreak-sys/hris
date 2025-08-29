import React, { useState, useEffect } from 'react';
import { EmployeeEnrollmentSummary } from '../../types/enrollment';
import { enrollmentService } from '../../services/enrollmentService';

interface EmployeeEnrollmentListProps {
  periodId: string;
  onSelectEnrollment?: (enrollmentId: string) => void;
}

const EmployeeEnrollmentList: React.FC<EmployeeEnrollmentListProps> = ({ periodId, onSelectEnrollment }) => {
  const [enrollments, setEnrollments] = useState<EmployeeEnrollmentSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchEnrollments = async () => {
      try {
        setLoading(true);
        const enrollmentsData = await enrollmentService.getEmployeeEnrollmentsSummary(periodId);
        setEnrollments(enrollmentsData);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load employee enrollments');
      } finally {
        setLoading(false);
      }
    };

    if (periodId) {
      fetchEnrollments();
    }
  }, [periodId]);

  const getStatusBadgeColor = (status: string) => {
    switch (status) {
      case 'approved': return 'bg-green-100 text-green-800';
      case 'submitted': return 'bg-blue-100 text-blue-800';
      case 'in_progress': return 'bg-yellow-100 text-yellow-800';
      case 'not_started': return 'bg-gray-100 text-gray-800';
      case 'declined': return 'bg-red-100 text-red-800';
      case 'expired': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString();
  };

  if (loading) return <div className="text-center py-4">Loading employee enrollments...</div>;
  if (error) return <div className="text-red-600 py-4">Error: {error}</div>;

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-xl font-bold text-gray-900">Employee Enrollments</h3>
        <div className="text-sm text-gray-600">
          Total: {enrollments.length} employees
        </div>
      </div>
      
      {enrollments.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          No employee enrollments found
        </div>
      ) : (
        <div className="bg-white shadow overflow-hidden sm:rounded-md">
          <ul className="divide-y divide-gray-200">
            {enrollments.map((enrollment) => (
              <li
                key={enrollment.id}
                className="px-6 py-4 hover:bg-gray-50 cursor-pointer"
                onClick={() => onSelectEnrollment?.(enrollment.id)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center space-x-3">
                        <p className="text-lg font-medium text-gray-900 truncate">
                          {enrollment.employee_name}
                        </p>
                        <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusBadgeColor(enrollment.status)}`}>
                          {enrollment.status.replace('_', ' ')}
                        </span>
                        {enrollment.waived_coverage && (
                          <span className="px-2 py-1 text-xs font-medium rounded-full bg-orange-100 text-orange-800">
                            Waived
                          </span>
                        )}
                      </div>
                      <div className="mt-1 flex items-center space-x-4 text-sm text-gray-500">
                        <span>Plans: {enrollment.plan_enrollments_count}</span>
                        <span>Premium: {formatCurrency(enrollment.total_premium)}</span>
                        {enrollment.submitted_at && (
                          <span>Submitted: {formatDate(enrollment.submitted_at)}</span>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <svg className="w-5 h-5 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
                    </svg>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default EmployeeEnrollmentList;