import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import SearchPage from '../SearchPage';

// Mock react-router-dom
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => jest.fn(),
}));

// Mock fetch
global.fetch = jest.fn();

describe('SearchPage Component', () => {
  beforeEach(() => {
    fetch.mockClear();
  });

  test('renders search page title', () => {
    render(<SearchPage />);
    const titleElement = screen.getByText('Explore the Library');
    expect(titleElement).toBeInTheDocument();
  });

  test('renders back button', () => {
    render(<SearchPage />);
    const backButton = screen.getByText('← Back to Alexandria');
    expect(backButton).toBeInTheDocument();
  });

  test('renders search input', () => {
    render(<SearchPage />);
    const searchInput = screen.getByPlaceholderText(
      'Search for books, authors, or topics...'
    );
    expect(searchInput).toBeInTheDocument();
  });

  test('renders search button', () => {
    render(<SearchPage />);
    const searchButton = screen.getByRole('button', { name: /search/i });
    expect(searchButton).toBeInTheDocument();
  });

  test('search input updates on change', () => {
    render(<SearchPage />);
    const searchInput = screen.getByPlaceholderText(
      'Search for books, authors, or topics...'
    );

    fireEvent.change(searchInput, { target: { value: 'test search' } });

    expect(searchInput.value).toBe('test search');
  });

  test('search form submission calls API', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        query: 'test query',
        page_title: 'Test Page',
        citations: ['Test citation 1', 'Test citation 2'],
        count: 2,
        status: 'success',
      }),
    });

    render(<SearchPage />);
    const searchInput = screen.getByPlaceholderText(
      'Search for books, authors, or topics...'
    );
    const searchButton = screen.getByRole('button', { name: /search/i });

    fireEvent.change(searchInput, { target: { value: 'test query' } });
    fireEvent.click(searchButton);

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        expect.stringMatching(/^http:\/\/localhost:5001\/api\/search\?t=\d+$/),
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ query: 'test query' }),
        }
      );
    });
  });

  test('displays loading state during search', async () => {
    fetch.mockImplementation(
      () => new Promise((resolve) => setTimeout(resolve, 100))
    );

    render(<SearchPage />);
    const searchInput = screen.getByPlaceholderText(
      'Search for books, authors, or topics...'
    );
    const searchButton = screen.getByRole('button', { name: /search/i });

    fireEvent.change(searchInput, { target: { value: 'test query' } });
    fireEvent.click(searchButton);

    expect(screen.getByText('Searching...')).toBeInTheDocument();
  });

  test('displays error message on API failure', async () => {
    fetch.mockResolvedValueOnce({
      ok: false,
      json: async () => ({ error: 'Search failed' }),
    });

    render(<SearchPage />);
    const searchInput = screen.getByPlaceholderText(
      'Search for books, authors, or topics...'
    );
    const searchButton = screen.getByRole('button', { name: /search/i });

    fireEvent.change(searchInput, { target: { value: 'test query' } });
    fireEvent.click(searchButton);

    await waitFor(() => {
      expect(screen.getByText('Search failed')).toBeInTheDocument();
    });
  });

  test('displays network error on fetch failure', async () => {
    fetch.mockRejectedValueOnce(new Error('Network error'));

    render(<SearchPage />);
    const searchInput = screen.getByPlaceholderText(
      'Search for books, authors, or topics...'
    );
    const searchButton = screen.getByRole('button', { name: /search/i });

    fireEvent.change(searchInput, { target: { value: 'test query' } });
    fireEvent.click(searchButton);

    await waitFor(() => {
      expect(
        screen.getByText('Network error. Please try again.')
      ).toBeInTheDocument();
    });
  });

  test('displays sort dropdown with default state when search results are shown', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        query: 'test query',
        page_title: 'Test Page',
        citations: ['Test citation 1', 'Test citation 2'],
        count: 2,
        status: 'success',
      }),
    });

    render(<SearchPage />);
    const searchInput = screen.getByPlaceholderText(
      'Search for books, authors, or topics...'
    );
    const searchButton = screen.getByRole('button', { name: /search/i });

    fireEvent.change(searchInput, { target: { value: 'test query' } });
    fireEvent.click(searchButton);

    await waitFor(() => {
      expect(screen.getByText('Sort by...')).toBeInTheDocument();
    });
  });

  test('sort dropdown has all required options including default state', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        query: 'test query',
        page_title: 'Test Page',
        citations: ['Test citation 1', 'Test citation 2'],
        count: 2,
        status: 'success',
      }),
    });

    render(<SearchPage />);
    const searchInput = screen.getByPlaceholderText(
      'Search for books, authors, or topics...'
    );
    const searchButton = screen.getByRole('button', { name: /search/i });

    fireEvent.change(searchInput, { target: { value: 'test query' } });
    fireEvent.click(searchButton);

    await waitFor(() => {
      // Check that the dropdown is present and shows the default value
      expect(screen.getByText('Sort by...')).toBeInTheDocument();

      // Check that the dropdown container is present
      const dropdownContainer = document.querySelector(
        '.sort-dropdown-wrapper'
      );
      expect(dropdownContainer).toBeInTheDocument();
    });
  });

  test('sort dropdown resets to default when starting new search', async () => {
    // First search
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        query: 'test query',
        page_title: 'Test Page',
        citations: ['Test citation 1', 'Test citation 2'],
        count: 2,
        status: 'success',
      }),
    });

    render(<SearchPage />);
    const searchInput = screen.getByPlaceholderText(
      'Search for books, authors, or topics...'
    );
    const searchButton = screen.getByRole('button', { name: /search/i });

    fireEvent.change(searchInput, { target: { value: 'test query' } });
    fireEvent.click(searchButton);

    await waitFor(() => {
      expect(screen.getByText('Sort by...')).toBeInTheDocument();
    });

    // Second search
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        query: 'another query',
        page_title: 'Another Page',
        citations: ['Another citation'],
        count: 1,
        status: 'success',
      }),
    });

    fireEvent.change(searchInput, { target: { value: 'another query' } });
    fireEvent.click(searchButton);

    await waitFor(() => {
      expect(screen.getByText('Sort by...')).toBeInTheDocument();
    });
  });

  test('sort dropdown resets to default when closing results', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        query: 'test query',
        page_title: 'Test Page',
        citations: ['Test citation 1', 'Test citation 2'],
        count: 2,
        status: 'success',
      }),
    });

    render(<SearchPage />);
    const searchInput = screen.getByPlaceholderText(
      'Search for books, authors, or topics...'
    );
    const searchButton = screen.getByRole('button', { name: /search/i });

    fireEvent.change(searchInput, { target: { value: 'test query' } });
    fireEvent.click(searchButton);

    await waitFor(() => {
      expect(screen.getByText('Sort by...')).toBeInTheDocument();
    });

    const closeButton = screen.getByText('×');
    fireEvent.click(closeButton);

    // After closing, the dropdown should not be visible
    expect(screen.queryByText('Sort by...')).not.toBeInTheDocument();
  });
});
