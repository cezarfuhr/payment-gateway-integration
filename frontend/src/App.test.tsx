import React from 'react';
import { render, screen } from '@testing-library/react';
import App from './App';

test('renders payment gateway app', () => {
  render(<App />);
  const linkElement = screen.getByText(/Payment Gateway/i);
  expect(linkElement).toBeInTheDocument();
});
