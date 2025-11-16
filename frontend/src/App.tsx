import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from 'react-query';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

import Dashboard from './pages/Dashboard';
import CreatePayment from './pages/CreatePayment';
import PaymentList from './pages/PaymentList';
import Reports from './pages/Reports';
import './App.css';

const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <div className="App">
          <nav className="navbar">
            <div className="container">
              <h1 className="logo">Payment Gateway</h1>
              <ul className="nav-links">
                <li><Link to="/">Dashboard</Link></li>
                <li><Link to="/payments">Payments</Link></li>
                <li><Link to="/create-payment">New Payment</Link></li>
                <li><Link to="/reports">Reports</Link></li>
              </ul>
            </div>
          </nav>

          <main className="container">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/payments" element={<PaymentList />} />
              <Route path="/create-payment" element={<CreatePayment />} />
              <Route path="/reports" element={<Reports />} />
            </Routes>
          </main>

          <ToastContainer position="top-right" autoClose={3000} />
        </div>
      </Router>
    </QueryClientProvider>
  );
}

export default App;
