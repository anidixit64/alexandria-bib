import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './SearchPage.css';

function SearchPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const navigate = useNavigate();

  const handleSearch = (e) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      console.log('Searching for:', searchQuery);
      // TODO: Implement search functionality
    }
  };

  const handleBackToHome = () => {
    navigate('/');
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
              />
              <button type="submit" className="search-button">
                Search
              </button>
            </div>
          </form>
        </div>
      </main>
    </div>
  );
}

export default SearchPage; 