import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './SearchPage.css';

function SearchPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  const handleSearch = async (e) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      setIsLoading(true);
      setError(null);
      setSearchResults(null);
      
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
  };

  return (
    <div className="search-page">
      <header className="search-header">
        <button 
          className="back-button"
          onClick={handleBackToHome}
        >
          ← Back to Alexandria
        </button>
        <h1 className="search-title">Explore the Library</h1>
      </header>
      
      <main className="search-main">
        <div className="search-container">
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
              <button type="submit" className="search-button" disabled={isLoading}>
                {isLoading ? 'Searching...' : 'Search'}
              </button>
            </div>
          </form>
          
          {/* Results Popup */}
          {searchResults && (
            <div className="results-popup">
              <div className="results-header">
                <h3>Books found for "{searchResults.query}"</h3>
                <p>From Wikipedia: {searchResults.page_title}</p>
                <button className="close-button" onClick={closeResults}>×</button>
              </div>
              
              {searchResults.citations.length > 0 ? (
                <div className="citations-list">
                  {searchResults.citations.map((citation, index) => (
                    <div key={index} className="citation-item">
                      <span className="citation-number">{index + 1}.</span>
                      <span className="citation-text">{citation}</span>
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
            <div className="error-message">
              <p>{error}</p>
              <button onClick={() => setError(null)}>Dismiss</button>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default SearchPage; 