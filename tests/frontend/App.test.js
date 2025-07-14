import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import App from './App';

// Mock the image imports
jest.mock('./library.jpg', () => 'mocked-library-image');
jest.mock('./parchment.jpg', () => 'mocked-parchment-image');

// Mock react-router-dom
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => jest.fn(),
}));

describe('App Component', () => {
  test('renders without crashing', () => {
    render(<App />);
  });

  test('renders Alexandria title in curved text', () => {
    render(<App />);
    const letters = 'Alexandria'.split('');
    letters.forEach((letter) => {
      const elements = screen.getAllByText(letter);
      expect(elements.length).toBeGreaterThan(0);
    });
  });

  test('renders Explore the Library button', () => {
    render(<App />);
    const button = screen.getByRole('button', { name: /explore the library/i });
    expect(button).toBeInTheDocument();
  });

  test('button has correct styling classes', () => {
    render(<App />);
    const button = screen.getByRole('button', { name: /explore the library/i });
    expect(button).toHaveClass('explore-library-btn');
  });

  test('curved text container exists', () => {
    render(<App />);
    const curvedTextContainer = document.querySelector('.curved-text');
    expect(curvedTextContainer).toBeInTheDocument();
  });

  test('all letter spans have correct classes', () => {
    render(<App />);
    for (let i = 0; i < 10; i++) {
      const letterSpan = document.querySelector(`.letter-${i}`);
      expect(letterSpan).toBeInTheDocument();
    }
  });
});
