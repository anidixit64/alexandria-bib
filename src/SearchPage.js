import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './SearchPage.css';

function SearchPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showAllCitations, setShowAllCitations] = useState(false);
  const navigate = useNavigate();

  const handleSearch = async (e) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      setIsLoading(true);
      setError(null);
      setSearchResults(null);
      setShowAllCitations(false);

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
    setShowAllCitations(false);
  };

  const toggleCitations = () => {
    setShowAllCitations(!showAllCitations);
  };

  const displayedCitations =
    searchResults?.citations?.slice(0, showAllCitations ? undefined : 5) || [];
  const hasMoreCitations = searchResults?.citations?.length > 5;

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
              <button className="close-button" onClick={closeResults}>
                ×
              </button>
            </div>

            {searchResults.citations.length > 0 ? (
              <div className="citations-container">
                {displayedCitations.map((citation, index) => (
                  <div key={index} className="citation-item">
                    <span className="citation-number">{index + 1}.</span>
                    <span className="citation-text">{citation}</span>
                  </div>
                ))}

                {hasMoreCitations && !showAllCitations && (
                  <div className="citations-expand">
                    <span className="ellipsis">...</span>
                    <button className="expand-button" onClick={toggleCitations}>
                      Show All {searchResults.citations.length} Citations
                    </button>
                  </div>
                )}

                {hasMoreCitations && showAllCitations && (
                  <div className="citations-collapse">
                    <button
                      className="collapse-button"
                      onClick={toggleCitations}
                    >
                      Show Less
                    </button>
                  </div>
                )}
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
