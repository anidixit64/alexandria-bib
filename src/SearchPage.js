import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Select from 'react-select';
import './SearchPage.css';

function SearchPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const [toggleStructured, setToggleStructured] = useState(false);
  const [parsedCitations, setParsedCitations] = useState({});
  const sortOptions = [
    { value: '', label: 'Sort by...' },
    { value: 'Title A - Z', label: 'Title A - Z' },
    { value: 'Title Z - A', label: 'Title Z - A' },
    { value: 'Author A - Z', label: 'Author A - Z' },
    { value: 'Author Z - A', label: 'Author Z - A' },
    { value: 'Year Increasing', label: 'Year Increasing' },
    { value: 'Year Decreasing', label: 'Year Decreasing' },
  ];

  const [sortDropdown, setSortDropdown] = useState(sortOptions[0]);
  const navigate = useNavigate();

  // Function to get sortable value from citation (structured or unstructured)
  const getSortableValue = (citation, index, sortType) => {
    if (toggleStructured && parsedCitations[index]) {
      const parsed = parsedCitations[index];

      switch (sortType) {
        case 'Title A - Z':
        case 'Title Z - A': {
          return (
            parsed.title || parsed.chapter_title || parsed.book_title || ''
          );
        }
        case 'Author A - Z':
        case 'Author Z - A': {
          return (
            parsed.authors ||
            parsed.chapter_authors ||
            parsed.book_authors ||
            ''
          );
        }
        case 'Year Increasing':
        case 'Year Decreasing': {
          return parsed.year ? parseInt(parsed.year) : 0;
        }
        default: {
          return '';
        }
      }
    } else {
      // For unstructured view, try to extract basic info from raw citation
      switch (sortType) {
        case 'Title A - Z':
        case 'Title Z - A': {
          // Try to extract title from raw citation
          const titleMatch = citation.match(/(?:\.\s*)([^.]+?)(?:\s*\.|$)/);
          return titleMatch ? titleMatch[1].trim() : citation;
        }
        case 'Author A - Z':
        case 'Author Z - A': {
          // Try to extract author from beginning of citation
          const authorMatch = citation.match(/^([^(]+?)(?:\s*\(|\.)/);
          return authorMatch ? authorMatch[1].trim() : citation;
        }
        case 'Year Increasing':
        case 'Year Decreasing': {
          // Try to extract year from citation
          const yearMatch = citation.match(/\b(19|20)\d{2}\b/);
          return yearMatch ? parseInt(yearMatch[0]) : 0;
        }
        default: {
          return '';
        }
      }
    }
  };

  // Function to sort citations based on selected option
  const sortCitations = (citations, sortType) => {
    if (!sortType || sortType === '') {
      return citations; // No sorting, return original order
    }

    const sortedCitations = [...citations].sort((a, b) => {
      const aIndex = citations.indexOf(a);
      const bIndex = citations.indexOf(b);

      const aValue = getSortableValue(a, aIndex, sortType);
      const bValue = getSortableValue(b, bIndex, sortType);

      // Handle numeric sorting for years
      if (sortType.includes('Year')) {
        if (sortType === 'Year Increasing') {
          return aValue - bValue;
        } else {
          return bValue - aValue;
        }
      }

      // Handle string sorting for titles and authors
      const comparison = aValue.localeCompare(bValue, undefined, {
        numeric: true,
        sensitivity: 'base',
      });

      if (sortType.includes('Z - A')) {
        return -comparison;
      } else {
        return comparison;
      }
    });

    return sortedCitations;
  };

  // Function to render structured citation
  const renderStructuredCitation = (citation, index) => {
    const parsed = parsedCitations[index];

    if (!parsed) {
      return (
        <div key={index} className="citation-item">
          <div className="citation-number">{index + 1}</div>
          <div className="citation-content">
            <div className="citation-text">{citation}</div>
          </div>
        </div>
      );
    }

    // Check if it's a chapter citation (has chapter_title)
    if (parsed.chapter_title) {
      return (
        <div key={index} className="citation-item structured">
          <div className="citation-number">{index + 1}</div>
          <div className="citation-content">
            <div className="book-title">
              {parsed.book_title || 'Unknown Book'}
            </div>
            <div className="book-author">
              <strong>Book Authors:</strong> {parsed.book_authors || 'Unknown'}
            </div>
            <div className="chapter-title">
              <strong>Chapter:</strong> {parsed.chapter_title}
            </div>
            <div className="book-author">
              <strong>Chapter Author:</strong>{' '}
              {parsed.chapter_authors || 'Unknown'}
            </div>
            {parsed.year && <div className="year">{parsed.year}</div>}
            {parsed.isbn && (
              <div className="isbn">
                <strong>ISBN:</strong> {parsed.isbn}
              </div>
            )}
            {parsed.remaining_text && (
              <div className="remaining-text">
                <strong>Additional Info:</strong> {parsed.remaining_text}
              </div>
            )}
          </div>
        </div>
      );
    } else {
      return (
        <div key={index} className="citation-item structured">
          <div className="citation-number">{index + 1}</div>
          <div className="citation-content">
            <div className="book-title">{parsed.title || 'Unknown Title'}</div>
            <div className="book-author">
              <strong>Author:</strong> {parsed.authors || 'Unknown'}
            </div>
            {parsed.editor && (
              <div className="book-author">
                <strong>Editor:</strong> {parsed.editor}
              </div>
            )}
            {parsed.year && <div className="year">{parsed.year}</div>}
            {parsed.isbn && (
              <div className="isbn">
                <strong>ISBN:</strong> {parsed.isbn}
              </div>
            )}
            {parsed.remaining_text && (
              <div className="remaining-text">
                <strong>Additional Info:</strong> {parsed.remaining_text}
              </div>
            )}
          </div>
        </div>
      );
    }
  };

  const handleSearch = async (e) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      setIsLoading(true);
      setError(null);
      setSearchResults(null);
      setParsedCitations({});
      setToggleStructured(false); // Reset toggle to off for new searches
      setSortDropdown(sortOptions[0]); // Reset sort to default

      try {
        const response = await fetch('http://localhost:5001/api/search', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ query: searchQuery }),
        });

        const data = await response.json();

        if (response.ok) {
          setSearchResults(data);
        } else {
          setError(data.error || 'Search failed');
        }
      } catch (err) {
        setError('Network error. Please try again.');
        console.error('Search error:', err);
      } finally {
        setIsLoading(false);
      }
    }
  };

  const handleBackToHome = () => {
    navigate('/');
  };

  const closeResults = () => {
    setSearchResults(null);
    setError(null);
    setParsedCitations({});
    setSortDropdown(sortOptions[0]); // Reset sort to default
  };

  const handleToggleStructured = async () => {
    const newToggleState = !toggleStructured;
    setToggleStructured(newToggleState);

    // If turning on structured view, parse ALL citations in a single batch request
    if (newToggleState && searchResults?.citations) {
      try {
        const response = await fetch('http://localhost:5001/api/parse/batch', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ citations: searchResults.citations }),
        });
        if (response.ok) {
          const data = await response.json();
          // data.results is an array of parsed citations
          const newParsedCitations = {};
          data.results.forEach((parsed, i) => {
            newParsedCitations[i] = parsed;
          });
          setParsedCitations(newParsedCitations);
        } else {
          setError('Failed to parse citations in batch.');
        }
      } catch (err) {
        setError('Network error during batch parsing.');
        console.error('Batch parse error:', err);
      }
    }
  };

  const handleSortChange = (selectedOption) => {
    setSortDropdown(selectedOption);
  };

  // Get sorted citations based on current sort selection
  const displayedCitations = searchResults?.citations
    ? sortCitations(searchResults.citations, sortDropdown.value)
    : [];

  return (
    <div className="search-page">
      <header className="search-header">
        <button className="back-button" onClick={handleBackToHome}>
          ← Back to Alexandria
        </button>
        <h1 className="search-title">Explore the Library</h1>
      </header>

      <main className="search-main">
        <form onSubmit={handleSearch} className="search-form">
          <div className="search-input-wrapper">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search for books, authors, or topics..."
              className="search-input"
              autoFocus
              disabled={isLoading}
            />
            <button
              type="submit"
              className="search-button"
              disabled={isLoading}
            >
              {isLoading ? 'Searching...' : 'Search'}
            </button>
          </div>
        </form>

        {/* Results Section */}
        {searchResults && (
          <div className="results-section">
            <div className="results-header">
              <div className="header-controls">
                <div className="sort-dropdown-wrapper">
                  <Select
                    classNamePrefix="sort-dropdown"
                    value={sortDropdown}
                    onChange={handleSortChange}
                    options={sortOptions}
                    isSearchable={false}
                    styles={{
                      control: (base, state) => ({
                        ...base,
                        background: 'rgba(255,255,255,0.95)',
                        borderColor: state.isFocused
                          ? 'rgba(255,213,0,0.6)'
                          : 'rgba(44,24,16,0.3)',
                        boxShadow: state.isFocused
                          ? '0 0 0 3px rgba(255,213,0,0.2)'
                          : '0 2px 4px rgba(0,0,0,0.1)',
                        borderRadius: 8,
                        minWidth: 140,
                        height: 30,
                        minHeight: 30,
                        padding: '0 8px',
                        fontFamily: 'Almendra, serif',
                        fontWeight: 500,
                        fontSize: 14,
                        color: '#2c1810',
                        cursor: 'pointer',
                        transition: 'all 0.3s ease',
                        '&:hover': {
                          borderColor: 'rgba(44,24,16,0.5)',
                          background: 'rgba(255,255,255,1)',
                        },
                      }),
                      menu: (base) => ({
                        ...base,
                        background: 'rgba(255,255,255,0.98)',
                        borderRadius: 8,
                        boxShadow: '0 4px 8px rgba(0,0,0,0.15)',
                        fontFamily: 'Almendra, serif',
                        color: '#2c1810',
                        marginTop: 2,
                      }),
                      option: (base, state) => ({
                        ...base,
                        background: state.isSelected
                          ? 'rgba(255,213,0,0.2)'
                          : state.isFocused
                            ? 'rgba(255,213,0,0.1)'
                            : 'rgba(255,255,255,0.98)',
                        color: '#2c1810',
                        fontFamily: 'Almendra, serif',
                        fontSize: 15,
                        cursor: 'pointer',
                        padding: '10px 16px',
                      }),
                      singleValue: (base) => ({
                        ...base,
                        color: '#2c1810',
                        fontFamily: 'Almendra, serif',
                        fontWeight: 500,
                      }),
                      dropdownIndicator: (base) => ({
                        ...base,
                        color: '#2c1810',
                        '&:hover': { color: '#2c1810' },
                      }),
                      indicatorSeparator: () => ({ display: 'none' }),
                    }}
                  />
                </div>
                <div className="toggle-switch">
                  <input
                    type="checkbox"
                    id="citation-toggle"
                    className="toggle-input"
                    checked={toggleStructured}
                    onChange={handleToggleStructured}
                  />
                  <label htmlFor="citation-toggle" className="toggle-label">
                    <span className="toggle-slider"></span>
                  </label>
                </div>
                <button className="close-button" onClick={closeResults}>
                  ×
                </button>
              </div>
            </div>

            {displayedCitations.length > 0 ? (
              <div className="citations-container">
                {toggleStructured
                  ? displayedCitations.map((citation, index) =>
                      renderStructuredCitation(citation, index)
                    )
                  : displayedCitations.map((citation, index) => (
                      <div key={index} className="citation-item">
                        <div className="citation-number">{index + 1}</div>
                        <div className="citation-content">
                          <div className="citation-text">{citation}</div>
                        </div>
                      </div>
                    ))}
              </div>
            ) : (
              <div className="no-results">
                <p>No books with ISBN numbers found for this topic.</p>
              </div>
            )}
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className="error-section">
            <div className="error-message">
              <p>{error}</p>
              <button onClick={() => setError(null)}>Dismiss</button>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default SearchPage;
