import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './SearchPage.css';

function SearchPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const [toggleStructured, setToggleStructured] = useState(false);
  const [parsedCitations, setParsedCitations] = useState({});
  const navigate = useNavigate();

  // Function to determine which parser to use based on citation format
  const determineParser = (citation) => {
    // Check for chapter citations (has quotes)
    if (citation.includes('"') || citation.includes("'")) {
      return 'type3'; // Chapter citations with quotes
    }
    
    // Check for parenthetical dates (Type 1)
    if (citation.includes('(') && citation.match(/\([^)]*\d{4}[^)]*\)/)) {
      return 'type1';
    }
    
    // Check for standalone years (Type 2)
    if (citation.match(/\b(19|20)\d{2}\b/) && !citation.includes('(')) {
      return 'type2';
    }
    
    // Default to Type 1 for unknown formats
    return 'type1';
  };

  // Function to parse citation using backend parsers
  const parseCitation = async (citation) => {
    const parserType = determineParser(citation);
    
    try {
      const response = await fetch(`http://localhost:5001/api/parse/${parserType}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ citation }),
      });

      if (response.ok) {
        const result = await response.json();
        return result;
      } else {
        console.error(`Failed to parse citation with ${parserType} parser`);
        return null;
      }
    } catch (err) {
      console.error('Error parsing citation:', err);
      return null;
    }
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
            <div className="book-title">{parsed.book_title || 'Unknown Book'}</div>
            <div className="book-author">
              <strong>Book Authors:</strong> {parsed.book_authors || 'Unknown'}
            </div>
            <div className="chapter-title">
              <strong>Chapter:</strong> {parsed.chapter_title}
            </div>
            <div className="book-author">
              <strong>Chapter Author:</strong> {parsed.chapter_authors || 'Unknown'}
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
  };



  const handleToggleStructured = async () => {
    const newToggleState = !toggleStructured;
    setToggleStructured(newToggleState);
    
    // If turning on structured view, parse ALL citations (not just displayed ones)
    if (newToggleState && searchResults?.citations) {
      const newParsedCitations = {};
      
      // Parse all citations in the search results
      for (let i = 0; i < searchResults.citations.length; i++) {
        const parsed = await parseCitation(searchResults.citations[i]);
        if (parsed) {
          newParsedCitations[i] = parsed;
        }
      }
      
      setParsedCitations(newParsedCitations);
    }
  };

  const displayedCitations = searchResults?.citations || [];

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

            {searchResults.citations.length > 0 ? (
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
                    ))
                }


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
