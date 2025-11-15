import React from 'react';
import { useQuery } from 'react-query';
import { reportAPI } from '../services/api';

const Dashboard: React.FC = () => {
  const { data: stats, isLoading } = useQuery('dashboard-stats', () =>
    reportAPI.dashboard().then(res => res.data)
  );

  if (isLoading) {
    return <div className="loading">Loading...</div>;
  }

  return (
    <div>
      <h2>Dashboard</h2>

      <div className="dashboard-stats">
        <div className="stat-card success">
          <h3>Today's Payments</h3>
          <div className="value">{stats?.today?.count || 0}</div>
          <p>${(stats?.today?.amount || 0).toFixed(2)}</p>
        </div>

        <div className="stat-card info">
          <h3>Total Payments</h3>
          <div className="value">{stats?.total?.count || 0}</div>
          <p>${(stats?.total?.amount || 0).toFixed(2)}</p>
        </div>

        <div className="stat-card warning">
          <h3>Success Rate</h3>
          <div className="value">
            {stats?.total?.count > 0
              ? ((stats.total.count / stats.total.count) * 100).toFixed(1)
              : 0}%
          </div>
        </div>

        <div className="stat-card">
          <h3>Active Gateways</h3>
          <div className="value">4</div>
          <p>Stripe, PayPal, MercadoPago, PagSeguro</p>
        </div>
      </div>

      <div className="card recent-payments">
        <h3>Recent Payments</h3>
        <table className="table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Amount</th>
              <th>Gateway</th>
              <th>Status</th>
              <th>Created</th>
            </tr>
          </thead>
          <tbody>
            {stats?.recent_payments?.map((payment: any) => (
              <tr key={payment.id}>
                <td>{payment.id.substring(0, 8)}...</td>
                <td>${payment.amount.toFixed(2)}</td>
                <td>{payment.gateway}</td>
                <td>
                  <span className={`payment-status ${payment.status}`}>
                    {payment.status}
                  </span>
                </td>
                <td>{new Date(payment.created_at).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default Dashboard;
