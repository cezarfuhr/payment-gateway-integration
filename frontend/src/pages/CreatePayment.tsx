import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import { paymentAPI } from '../services/api';

const CreatePayment: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    gateway: 'stripe',
    amount: '',
    currency: 'USD',
    customer_email: '',
    customer_name: '',
    description: '',
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const payload = {
        ...formData,
        amount: parseFloat(formData.amount),
        metadata: {},
      };

      await paymentAPI.create(payload);
      toast.success('Payment created successfully!');
      navigate('/payments');
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to create payment');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  return (
    <div>
      <h2>Create New Payment</h2>

      <div className="card payment-form">
        <form onSubmit={handleSubmit}>
          <div className="gateway-selector">
            {['stripe', 'paypal', 'mercadopago', 'pagseguro'].map(gateway => (
              <div
                key={gateway}
                className={`gateway-option ${formData.gateway === gateway ? 'selected' : ''}`}
                onClick={() => setFormData({ ...formData, gateway })}
              >
                <div className="icon">
                  {gateway === 'stripe' && '💳'}
                  {gateway === 'paypal' && '💰'}
                  {gateway === 'mercadopago' && '🏦'}
                  {gateway === 'pagseguro' && '🔐'}
                </div>
                <div>{gateway}</div>
              </div>
            ))}
          </div>

          <div className="form-group">
            <label>Amount</label>
            <input
              type="number"
              name="amount"
              value={formData.amount}
              onChange={handleChange}
              required
              step="0.01"
              min="0.01"
              placeholder="100.00"
            />
          </div>

          <div className="form-group">
            <label>Currency</label>
            <select name="currency" value={formData.currency} onChange={handleChange}>
              <option value="USD">USD</option>
              <option value="BRL">BRL</option>
              <option value="EUR">EUR</option>
            </select>
          </div>

          <div className="form-group">
            <label>Customer Email</label>
            <input
              type="email"
              name="customer_email"
              value={formData.customer_email}
              onChange={handleChange}
              placeholder="customer@example.com"
            />
          </div>

          <div className="form-group">
            <label>Customer Name</label>
            <input
              type="text"
              name="customer_name"
              value={formData.customer_name}
              onChange={handleChange}
              placeholder="John Doe"
            />
          </div>

          <div className="form-group">
            <label>Description</label>
            <textarea
              name="description"
              value={formData.description}
              onChange={handleChange}
              rows={3}
              placeholder="Payment description"
            />
          </div>

          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? 'Creating...' : 'Create Payment'}
          </button>
        </form>
      </div>
    </div>
  );
};

export default CreatePayment;
