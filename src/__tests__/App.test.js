import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import App from '../App';

// Mock the image imports
jest.mock('../library.jpg', () => 'mocked-library-image');
jest.mock('../parchment.jpg', () => 'mocked-parchment-image');
jest.mock('../scroll_logo.png', () => 'mocked-scroll-logo');

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
    expect(button).toHaveClass('explore-button');
  });

  test('title container exists', () => {
    render(<App />);
    const titleContainer = document.querySelector('.title');
    expect(titleContainer).toBeInTheDocument();
  });

  test('all letter spans have correct classes', () => {
    render(<App />);
    const letterSpans = document.querySelectorAll('.letter');
    expect(letterSpans.length).toBe(10); // "Alexandria" has 10 letters
  });
});
