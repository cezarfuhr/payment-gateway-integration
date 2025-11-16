import React, { useState } from 'react';
import { useQuery } from 'react-query';
import { reportAPI } from '../services/api';
import { toast } from 'react-toastify';

const Reports: React.FC = () => {
  const [reportType, setReportType] = useState('payment_summary');
  const [dateRange, setDateRange] = useState({
    start_date: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    end_date: new Date().toISOString().split('T')[0],
  });

  const { data: reports, isLoading } = useQuery('reports', () =>
    reportAPI.list().then(res => res.data)
  );

  const handleGenerateReport = async () => {
    try {
      const payload = {
        report_type: reportType,
        start_date: new Date(dateRange.start_date).toISOString(),
        end_date: new Date(dateRange.end_date).toISOString(),
      };

      await reportAPI.create(payload);
      toast.success('Report generated successfully!');
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to generate report');
    }
  };

  return (
    <div>
      <h2>Reports</h2>

      <div className="card">
        <h3>Generate New Report</h3>

        <div className="form-group">
          <label>Report Type</label>
          <select
            value={reportType}
            onChange={(e) => setReportType(e.target.value)}
          >
            <option value="payment_summary">Payment Summary</option>
            <option value="gateway_performance">Gateway Performance</option>
            <option value="transaction_volume">Transaction Volume</option>
          </select>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px' }}>
          <div className="form-group">
            <label>Start Date</label>
            <input
              type="date"
              value={dateRange.start_date}
              onChange={(e) => setDateRange({ ...dateRange, start_date: e.target.value })}
            />
          </div>

          <div className="form-group">
            <label>End Date</label>
            <input
              type="date"
              value={dateRange.end_date}
              onChange={(e) => setDateRange({ ...dateRange, end_date: e.target.value })}
            />
          </div>
        </div>

        <button className="btn btn-primary" onClick={handleGenerateReport}>
          Generate Report
        </button>
      </div>

      <div className="card">
        <h3>Recent Reports</h3>

        {isLoading ? (
          <div className="loading">Loading...</div>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>Type</th>
                <th>Period</th>
                <th>Created</th>
              </tr>
            </thead>
            <tbody>
              {reports?.map((report: any) => (
                <tr key={report.id}>
                  <td><span className="badge badge-info">{report.report_type}</span></td>
                  <td>
                    {new Date(report.start_date).toLocaleDateString()} -{' '}
                    {new Date(report.end_date).toLocaleDateString()}
                  </td>
                  <td>{new Date(report.created_at).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}

        {!isLoading && (!reports || reports.length === 0) && (
          <div style={{ textAlign: 'center', padding: '40px', color: '#999' }}>
            No reports found
          </div>
        )}
      </div>
    </div>
  );
};

export default Reports;
