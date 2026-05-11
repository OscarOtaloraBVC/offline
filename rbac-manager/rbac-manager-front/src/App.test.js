import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import App from './App';

const renderWithRouter = (ui) => {
  return render(<BrowserRouter>{ui}</BrowserRouter>);
};

test('renders app correctly', () => {
  renderWithRouter(<App />);
  
  // Verifica que el título principal exista
  expect(screen.getByText('RBAC Manager')).toBeInTheDocument();
  
  // Verifica que los elementos del menú existan
  expect(screen.getByText('Users')).toBeInTheDocument();
  expect(screen.getByText('Profiles')).toBeInTheDocument();
  
  // Verifica que el mensaje de bienvenida exista
  expect(screen.getByText(/Welcome to the RBAC Manager Portal/i)).toBeInTheDocument();
  
  // Verifica que los botones existan
  expect(screen.getByText('Go to Users')).toBeInTheDocument();
  expect(screen.getByText('Go to Profiles')).toBeInTheDocument();
});