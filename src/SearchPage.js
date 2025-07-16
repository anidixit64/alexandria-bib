import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Select from 'react-select';
import './SearchPage.css';

function SearchPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [disambiguationOptions, setDisambiguationOptions] = useState(null);

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

  // Function to get sortable value from parsed citation data
  const getSortableValue = (originalIndex, sortType) => {
    const parsed = parsedCitations[originalIndex];

    if (!parsed) {
      return '';
    }

    switch (sortType) {
      case 'Title A - Z':
      case 'Title Z - A': {
        return parsed.title || parsed.chapter_title || parsed.book_title || '';
      }
      case 'Author A - Z':
      case 'Author Z - A': {
        return (
          parsed.authors || parsed.chapter_authors || parsed.book_authors || ''
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
  };

  // Function to sort citations based on selected option
  const sortCitations = (citations, sortType) => {
    // Always create an array of objects with citation and original index
    const citationsWithIndex = citations.map((citation, index) => ({
      citation,
      originalIndex: index,
    }));

    if (!sortType || sortType === '') {
      return citationsWithIndex; // No sorting, return original order with indices
    }

    const sortedCitationsWithIndex = citationsWithIndex.sort((a, b) => {
      const aValue = getSortableValue(a.originalIndex, sortType);
      const bValue = getSortableValue(b.originalIndex, sortType);

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

    // Return the sorted citations with their original indices
    return sortedCitationsWithIndex;
  };

  // Function to render structured citation
  const renderStructuredCitation = (citation, originalIndex, displayIndex) => {
    const parsed = parsedCitations[originalIndex];

    if (!parsed) {
      return (
        <div key={displayIndex} className="citation-item">
          <div className="citation-number">{displayIndex + 1}</div>
          <div className="citation-content">
            <div className="citation-text">{citation}</div>
          </div>
        </div>
      );
    }

    // Check if it's a chapter citation (has chapter_title)
    if (parsed.chapter_title) {
      return (
        <div key={displayIndex} className="citation-item structured">
          <div className="citation-number">{displayIndex + 1}</div>
          <div className="citation-content">
            <div className="book-title">
              {parsed.book_title || 'Unknown Book'}
            </div>
            <div className="book-author">
              by {parsed.book_authors || 'Unknown'}
            </div>
            {parsed.year && <div className="year-badge">{parsed.year}</div>}
            {parsed.isbn && <div className="isbn-badge">{parsed.isbn}</div>}
          </div>
        </div>
      );
    } else {
      return (
        <div key={displayIndex} className="citation-item structured">
          <div className="citation-number">{displayIndex + 1}</div>
          <div className="citation-content">
            <div className="book-title">{parsed.title || 'Unknown Title'}</div>
            <div className="book-author">by {parsed.authors || 'Unknown'}</div>
            {parsed.year && <div className="year-badge">{parsed.year}</div>}
            {parsed.isbn && <div className="isbn-badge">{parsed.isbn}</div>}
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
      setDisambiguationOptions(null);
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
          // Check if this is a disambiguation or suggestions response
          if (
            data.status === 'disambiguation' ||
            data.status === 'suggestions'
          ) {
            setDisambiguationOptions(data.options);
          } else {
            setSearchResults(data);

            // Immediately parse all citations in a single batch request
            if (data.citations && data.citations.length > 0) {
              try {
                const parseResponse = await fetch(
                  'http://localhost:5001/api/parse/batch',
                  {
                    method: 'POST',
                    headers: {
                      'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ citations: data.citations }),
                  }
                );
                if (parseResponse.ok) {
                  const parseData = await parseResponse.json();
                  // parseData.results is an array of parsed citations
                  const newParsedCitations = {};
                  parseData.results.forEach((parsed, i) => {
                    newParsedCitations[i] = parsed;
                  });
                  setParsedCitations(newParsedCitations);
                } else {
                  console.error('Failed to parse citations in batch.');
                }
              } catch (err) {
                console.error('Batch parse error:', err);
              }
            }
          }
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

  const handleDisambiguationOption = async (option) => {
    setIsLoading(true);
    setError(null);
    setDisambiguationOptions(null);

    try {
      const response = await fetch('http://localhost:5001/api/search/page', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ page_title: option.title }),
      });

      const data = await response.json();

      if (response.ok) {
        setSearchResults(data);

        // Immediately parse all citations in a single batch request
        if (data.citations && data.citations.length > 0) {
          try {
            const parseResponse = await fetch(
              'http://localhost:5001/api/parse/batch',
              {
                method: 'POST',
                headers: {
                  'Content-Type': 'application/json',
                },
                body: JSON.stringify({ citations: data.citations }),
              }
            );
            if (parseResponse.ok) {
              const parseData = await parseResponse.json();
              // parseData.results is an array of parsed citations
              const newParsedCitations = {};
              parseData.results.forEach((parsed, i) => {
                newParsedCitations[i] = parsed;
              });
              setParsedCitations(newParsedCitations);
            } else {
              console.error('Failed to parse citations in batch.');
            }
          } catch (err) {
            console.error('Batch parse error:', err);
          }
        }
      } else {
        setError(data.error || 'Failed to fetch page content');
      }
    } catch (err) {
      setError('Network error. Please try again.');
      console.error('Disambiguation option error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const closeResults = () => {
    setSearchResults(null);
    setError(null);
    setDisambiguationOptions(null);
    setParsedCitations({});
    setSortDropdown(sortOptions[0]); // Reset sort to default
  };

  const handleToggleStructured = () => {
    setToggleStructured(!toggleStructured);
  };

  const handleSortChange = (selectedOption) => {
    setSortDropdown(selectedOption);
  };

  // Get sorted citations based on current sort selection
  const sortedCitationsWithIndex = searchResults?.citations
    ? sortCitations(searchResults.citations, sortDropdown.value)
    : [];

  return (
    <div className="search-page">
      <header className="search-header">
        <button className="back-button" onClick={handleBackToHome}>
          ← Back to Alexandria
        </button>
        <div className="header-title-section">
          <h1 className="search-title">Explore the Library</h1>
        </div>
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

        {/* Disambiguation/Suggestions Section */}
        {disambiguationOptions && (
          <div className="disambiguation-section">
            <div className="disambiguation-header">
              <h2>Did you mean:</h2>
              <button className="close-button" onClick={closeResults}>
                ×
              </button>
            </div>
            <div className="disambiguation-options">
              {disambiguationOptions.map((option, index) => (
                <button
                  key={index}
                  className="disambiguation-option"
                  onClick={() => handleDisambiguationOption(option)}
                  disabled={isLoading}
                >
                  {option.display_text || option.title}
                </button>
              ))}
            </div>
          </div>
        )}

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

            {sortedCitationsWithIndex.length > 0 ? (
              <div className="citations-container">
                {toggleStructured
                  ? sortedCitationsWithIndex.map((item, index) =>
                      renderStructuredCitation(
                        item.citation,
                        item.originalIndex,
                        index
                      )
                    )
                  : sortedCitationsWithIndex.map((item, index) => (
                      <div key={index} className="citation-item">
                        <div className="citation-number">{index + 1}</div>
                        <div className="citation-content">
                          <div className="citation-text">
                            {item.citation
                              ? item.citation
                              : 'No citation found'}
                          </div>
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
