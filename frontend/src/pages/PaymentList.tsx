import React from 'react';
import { useQuery } from 'react-query';
import { paymentAPI } from '../services/api';

const PaymentList: React.FC = () => {
  const { data: payments, isLoading, refetch } = useQuery('payments', () =>
    paymentAPI.list().then(res => res.data)
  );

  if (isLoading) {
    return <div className="loading">Loading...</div>;
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h2>Payments</h2>
        <button className="btn btn-primary" onClick={() => refetch()}>
          Refresh
        </button>
      </div>

      <div className="card">
        <table className="table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Gateway</th>
              <th>Amount</th>
              <th>Customer</th>
              <th>Status</th>
              <th>Created</th>
            </tr>
          </thead>
          <tbody>
            {payments?.map((payment: any) => (
              <tr key={payment.id}>
                <td>{payment.id.substring(0, 8)}...</td>
                <td>
                  <span className="badge badge-info">{payment.gateway}</span>
                </td>
                <td>
                  ${payment.amount} {payment.currency}
                </td>
                <td>
                  <div>{payment.customer_name || '-'}</div>
                  <small style={{ color: '#666' }}>{payment.customer_email || '-'}</small>
                </td>
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

        {!payments || payments.length === 0 && (
          <div style={{ textAlign: 'center', padding: '40px', color: '#999' }}>
            No payments found
          </div>
        )}
      </div>
    </div>
  );
};

export default PaymentList;
