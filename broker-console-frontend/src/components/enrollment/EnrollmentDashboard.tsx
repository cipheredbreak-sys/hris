import React, { useState, useEffect } from 'react';
import { EnrollmentPeriod, EmployeeEnrollmentSummary } from '../../types/enrollment';
import { enrollmentService } from '../../services/enrollmentService';
import EnrollmentPeriodList from './EnrollmentPeriodList';
import EmployeeEnrollmentList from './EmployeeEnrollmentList';

const EnrollmentDashboard: React.FC = () => {
  const [selectedPeriod, setSelectedPeriod] = useState<EnrollmentPeriod | null>(null);
  const [activePeriods, setActivePeriods] = useState<EnrollmentPeriod[]>([]);
  const [enrollmentStats, setEnrollmentStats] = useState({
    total: 0,
    notStarted: 0,
    inProgress: 0,
    submitted: 0,
    approved: 0,
    waived: 0
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchActivePeriods = async () => {
      try {
        const periods = await enrollmentService.getActiveEnrollmentPeriods();
        setActivePeriods(periods);
        if (periods.length > 0 && !selectedPeriod) {
          setSelectedPeriod(periods[0]);
        }
      } catch (error) {
        console.error('Failed to fetch active periods:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchActivePeriods();
  }, [selectedPeriod]);

  useEffect(() => {
    const fetchEnrollmentStats = async () => {
      if (!selectedPeriod) return;

      try {
        const enrollments = await enrollmentService.getEmployeeEnrollmentsSummary(selectedPeriod.id);
        
        const stats = enrollments.reduce((acc, enrollment) => {
          acc.total++;
          switch (enrollment.status) {
            case 'not_started':
              acc.notStarted++;
              break;
            case 'in_progress':
              acc.inProgress++;
              break;
            case 'submitted':
              acc.submitted++;
              break;
            case 'approved':
              acc.approved++;
              break;
          }
          if (enrollment.waived_coverage) {
            acc.waived++;
          }
          return acc;
        }, {
          total: 0,
          notStarted: 0,
          inProgress: 0,
          submitted: 0,
          approved: 0,
          waived: 0
        });

        setEnrollmentStats(stats);
      } catch (error) {
        console.error('Failed to fetch enrollment stats:', error);
      }
    };

    fetchEnrollmentStats();
  }, [selectedPeriod]);

  const handlePeriodSelect = (period: EnrollmentPeriod) => {
    setSelectedPeriod(period);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-lg text-gray-600">Loading enrollment dashboard...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="bg-white shadow rounded-lg p-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-6">Enrollment Dashboard</h1>
        
        {/* Active Periods Overview */}
        {activePeriods.length > 0 && (
          <div className="mb-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-3">Active Enrollment Periods</h2>
            <div className="grid gap-3 md:grid-cols-3">
              {activePeriods.map((period) => (
                <div
                  key={period.id}
                  className={`p-3 rounded border cursor-pointer transition-colors ${
                    selectedPeriod?.id === period.id
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:bg-gray-50'
                  }`}
                  onClick={() => handlePeriodSelect(period)}
                >
                  <div className="font-medium text-gray-900">{period.name}</div>
                  <div className="text-sm text-gray-600">{period.employer_name}</div>
                  <div className="text-xs text-gray-500">
                    {new Date(period.start_date).toLocaleDateString()} - {new Date(period.end_date).toLocaleDateString()}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Enrollment Statistics */}
        {selectedPeriod && (
          <div className="mb-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-3">
              Enrollment Statistics - {selectedPeriod.name}
            </h3>
            <div className="grid gap-4 md:grid-cols-6">
              <div className="bg-blue-50 p-4 rounded-lg">
                <div className="text-2xl font-bold text-blue-600">{enrollmentStats.total}</div>
                <div className="text-sm text-blue-800">Total Employees</div>
              </div>
              <div className="bg-gray-50 p-4 rounded-lg">
                <div className="text-2xl font-bold text-gray-600">{enrollmentStats.notStarted}</div>
                <div className="text-sm text-gray-800">Not Started</div>
              </div>
              <div className="bg-yellow-50 p-4 rounded-lg">
                <div className="text-2xl font-bold text-yellow-600">{enrollmentStats.inProgress}</div>
                <div className="text-sm text-yellow-800">In Progress</div>
              </div>
              <div className="bg-blue-50 p-4 rounded-lg">
                <div className="text-2xl font-bold text-blue-600">{enrollmentStats.submitted}</div>
                <div className="text-sm text-blue-800">Submitted</div>
              </div>
              <div className="bg-green-50 p-4 rounded-lg">
                <div className="text-2xl font-bold text-green-600">{enrollmentStats.approved}</div>
                <div className="text-sm text-green-800">Approved</div>
              </div>
              <div className="bg-orange-50 p-4 rounded-lg">
                <div className="text-2xl font-bold text-orange-600">{enrollmentStats.waived}</div>
                <div className="text-sm text-orange-800">Waived Coverage</div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Employee Enrollments List */}
      {selectedPeriod ? (
        <div className="bg-white shadow rounded-lg p-6">
          <EmployeeEnrollmentList 
            periodId={selectedPeriod.id} 
            onSelectEnrollment={(enrollmentId) => {
              console.log('Selected enrollment:', enrollmentId);
              // TODO: Navigate to enrollment details
            }}
          />
        </div>
      ) : (
        <div className="bg-white shadow rounded-lg p-6">
          <EnrollmentPeriodList onSelectPeriod={handlePeriodSelect} />
        </div>
      )}
    </div>
  );
};

export default EnrollmentDashboard;