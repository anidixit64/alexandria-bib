import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import App from './App';

// Mock the image imports
jest.mock('./library.jpg', () => 'mocked-library-image');
jest.mock('./parchment.jpg', () => 'mocked-parchment-image');

describe('App Component', () => {
  beforeEach(() => {
    // Mock console.log to avoid noise in tests
    jest.spyOn(console, 'log').mockImplementation(() => {});
  });

  afterEach(() => {
    console.log.mockRestore();
  });

  test('renders Alexandria title', () => {
    render(<App />);
    const titleElement = screen.getByText('Alexandria');
    expect(titleElement).toBeInTheDocument();
  });

  test('renders all 10 letters of Alexandria in curved text', () => {
    render(<App />);
    const letters = 'Alexandria'.split('');
    letters.forEach(letter => {
      expect(screen.getByText(letter)).toBeInTheDocument();
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

  test('button click handler is called', () => {
    render(<App />);
    const button = screen.getByRole('button', { name: /explore the library/i });
    
    fireEvent.click(button);
    
    expect(console.log).toHaveBeenCalledWith('Explore the Library button clicked');
  });

  test('button has parchment background style', () => {
    render(<App />);
    const button = screen.getByRole('button', { name: /explore the library/i });
    
    // Check that the button has the background style applied
    expect(button).toHaveStyle({
      backgroundSize: 'cover',
      backgroundPosition: 'center',
    });
  });

  test('renders with proper container structure', () => {
    render(<App />);
    const appContainer = screen.getByRole('main');
    expect(appContainer).toBeInTheDocument();
    expect(appContainer).toHaveClass('App');
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

  test('button is positioned correctly', () => {
    render(<App />);
    const button = screen.getByRole('button', { name: /explore the library/i });
    
    expect(button).toHaveStyle({
      position: 'absolute',
      left: '50%',
      top: '50%',
    });
  });

  test('button has circular shape', () => {
    render(<App />);
    const button = screen.getByRole('button', { name: /explore the library/i });
    
    expect(button).toHaveStyle({
      width: '200px',
      height: '200px',
      borderRadius: '50%',
    });
  });
}); 