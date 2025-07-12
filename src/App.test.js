import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import '@testing-library/jest-dom';
import App from './App';
import LandingPage from './LandingPage';
import SearchPage from './SearchPage';

// Mock the image imports
jest.mock('./library.jpg', () => 'mocked-library-image');
jest.mock('./parchment.jpg', () => 'mocked-parchment-image');

// Mock react-router-dom
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => jest.fn(),
}));

const renderWithRouter = (component) => {
  return render(
    <BrowserRouter>
      {component}
    </BrowserRouter>
  );
};

describe('App Component', () => {
  test('renders without crashing', () => {
    renderWithRouter(<App />);
  });
});

describe('LandingPage Component', () => {
  beforeEach(() => {
    // Mock console.log to avoid noise in tests
    jest.spyOn(console, 'log').mockImplementation(() => {});
  });

  afterEach(() => {
    console.log.mockRestore();
  });

  test('renders Alexandria title', () => {
    renderWithRouter(<LandingPage />);
    const titleElement = screen.getByText('Alexandria');
    expect(titleElement).toBeInTheDocument();
  });

  test('renders all 10 letters of Alexandria in curved text', () => {
    renderWithRouter(<LandingPage />);
    const letters = 'Alexandria'.split('');
    letters.forEach(letter => {
      expect(screen.getByText(letter)).toBeInTheDocument();
    });
  });

  test('renders Explore the Library button', () => {
    renderWithRouter(<LandingPage />);
    const button = screen.getByRole('button', { name: /explore the library/i });
    expect(button).toBeInTheDocument();
  });

  test('button has correct styling classes', () => {
    renderWithRouter(<LandingPage />);
    const button = screen.getByRole('button', { name: /explore the library/i });
    expect(button).toHaveClass('explore-library-btn');
  });

  test('button click handler is called', () => {
    renderWithRouter(<LandingPage />);
    const button = screen.getByRole('button', { name: /explore the library/i });
    
    fireEvent.click(button);
    
    expect(console.log).toHaveBeenCalledWith('Explore the Library button clicked');
  });

  test('button has parchment background style', () => {
    renderWithRouter(<LandingPage />);
    const button = screen.getByRole('button', { name: /explore the library/i });
    
    // Check that the button has the background style applied
    expect(button).toHaveStyle({
      backgroundSize: 'cover',
      backgroundPosition: 'center',
    });
  });

  test('renders with proper container structure', () => {
    renderWithRouter(<LandingPage />);
    const appContainer = document.querySelector('.App');
    expect(appContainer).toBeInTheDocument();
  });

  test('curved text container exists', () => {
    renderWithRouter(<LandingPage />);
    const curvedTextContainer = document.querySelector('.curved-text');
    expect(curvedTextContainer).toBeInTheDocument();
  });

  test('all letter spans have correct classes', () => {
    renderWithRouter(<LandingPage />);
    for (let i = 0; i < 10; i++) {
      const letterSpan = document.querySelector(`.letter-${i}`);
      expect(letterSpan).toBeInTheDocument();
    }
  });

  test('button is positioned correctly', () => {
    renderWithRouter(<LandingPage />);
    const button = screen.getByRole('button', { name: /explore the library/i });
    
    expect(button).toHaveStyle({
      position: 'absolute',
      left: '50%',
      top: '50%',
    });
  });

  test('button has circular shape', () => {
    renderWithRouter(<LandingPage />);
    const button = screen.getByRole('button', { name: /explore the library/i });
    
    expect(button).toHaveStyle({
      width: '200px',
      height: '200px',
      borderRadius: '50%',
    });
  });
});

describe('SearchPage Component', () => {
  beforeEach(() => {
    // Mock console.log to avoid noise in tests
    jest.spyOn(console, 'log').mockImplementation(() => {});
  });

  afterEach(() => {
    console.log.mockRestore();
  });

  test('renders search page title', () => {
    renderWithRouter(<SearchPage />);
    const titleElement = screen.getByText('Explore the Library');
    expect(titleElement).toBeInTheDocument();
  });

  test('renders back button', () => {
    renderWithRouter(<SearchPage />);
    const backButton = screen.getByText('← Back to Alexandria');
    expect(backButton).toBeInTheDocument();
  });

  test('renders search input', () => {
    renderWithRouter(<SearchPage />);
    const searchInput = screen.getByPlaceholderText('Search for books, authors, or topics...');
    expect(searchInput).toBeInTheDocument();
  });

  test('renders search button', () => {
    renderWithRouter(<SearchPage />);
    const searchButton = screen.getByRole('button', { name: /search/i });
    expect(searchButton).toBeInTheDocument();
  });

  test('renders popular searches section', () => {
    renderWithRouter(<SearchPage />);
    const popularSearches = screen.getByText('Popular Searches');
    expect(popularSearches).toBeInTheDocument();
  });

  test('renders suggestion tags', () => {
    renderWithRouter(<SearchPage />);
    const suggestionTags = ['Ancient History', 'Philosophy', 'Mathematics', 'Astronomy'];
    suggestionTags.forEach(tag => {
      expect(screen.getByText(tag)).toBeInTheDocument();
    });
  });

  test('search input updates on change', () => {
    renderWithRouter(<SearchPage />);
    const searchInput = screen.getByPlaceholderText('Search for books, authors, or topics...');
    
    fireEvent.change(searchInput, { target: { value: 'test search' } });
    
    expect(searchInput.value).toBe('test search');
  });

  test('suggestion tag click updates search input', () => {
    renderWithRouter(<SearchPage />);
    const searchInput = screen.getByPlaceholderText('Search for books, authors, or topics...');
    const philosophyTag = screen.getByText('Philosophy');
    
    fireEvent.click(philosophyTag);
    
    expect(searchInput.value).toBe('Philosophy');
  });

  test('search form submission logs search query', () => {
    renderWithRouter(<SearchPage />);
    const searchInput = screen.getByPlaceholderText('Search for books, authors, or topics...');
    const searchButton = screen.getByRole('button', { name: /search/i });
    
    fireEvent.change(searchInput, { target: { value: 'test query' } });
    fireEvent.click(searchButton);
    
    expect(console.log).toHaveBeenCalledWith('Searching for:', 'test query');
  });
}); 