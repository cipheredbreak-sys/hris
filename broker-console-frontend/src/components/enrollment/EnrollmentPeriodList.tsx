import React, { useState, useEffect } from 'react';
import { EnrollmentPeriod } from '../../types/enrollment';
import { enrollmentService } from '../../services/enrollmentService';

interface EnrollmentPeriodListProps {
  employerId?: string;
  onSelectPeriod?: (period: EnrollmentPeriod) => void;
}

const EnrollmentPeriodList: React.FC<EnrollmentPeriodListProps> = ({ employerId, onSelectPeriod }) => {
  const [periods, setPeriods] = useState<EnrollmentPeriod[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchPeriods = async () => {
      try {
        setLoading(true);
        let periodsData;
        if (employerId) {
          periodsData = await enrollmentService.getEnrollmentPeriodsByEmployer(employerId);
        } else {
          periodsData = await enrollmentService.getEnrollmentPeriods();
        }
        setPeriods(periodsData);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load enrollment periods');
      } finally {
        setLoading(false);
      }
    };

    fetchPeriods();
  }, [employerId]);

  const getStatusBadgeColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-800';
      case 'pending': return 'bg-yellow-100 text-yellow-800';
      case 'closed': return 'bg-gray-100 text-gray-800';
      case 'cancelled': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  if (loading) return <div className="text-center py-4">Loading enrollment periods...</div>;
  if (error) return <div className="text-red-600 py-4">Error: {error}</div>;

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900">Enrollment Periods</h2>
      </div>
      
      {periods.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          No enrollment periods found
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {periods.map((period) => (
            <div
              key={period.id}
              className="bg-white rounded-lg shadow-md p-6 cursor-pointer hover:shadow-lg transition-shadow"
              onClick={() => onSelectPeriod?.(period)}
            >
              <div className="flex justify-between items-start mb-4">
                <h3 className="text-lg font-semibold text-gray-900 truncate">
                  {period.name}
                </h3>
                <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusBadgeColor(period.status)}`}>
                  {period.status}
                </span>
              </div>
              
              <div className="space-y-2 text-sm text-gray-600">
                <div>
                  <strong>Type:</strong> {period.period_type.replace('_', ' ')}
                </div>
                <div>
                  <strong>Employer:</strong> {period.employer_name}
                </div>
                <div>
                  <strong>Period:</strong> {formatDate(period.start_date)} - {formatDate(period.end_date)}
                </div>
                <div>
                  <strong>Effective:</strong> {formatDate(period.coverage_effective_date)}
                </div>
              </div>
              
              <div className="mt-4 flex justify-between text-xs text-gray-500">
                <span>Allow Waive: {period.allow_waive ? 'Yes' : 'No'}</span>
                <span>Require All: {period.require_all_plans ? 'Yes' : 'No'}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default EnrollmentPeriodList;