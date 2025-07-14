import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import './App.css';
import libraryImage from './library.jpg';
import parchmentImage from './parchment.jpg';
import scrollLogo from './scroll_logo.png';

function LandingPage() {
  const navigate = useNavigate();
  const [showContent, setShowContent] = useState(false);

  useEffect(() => {
    // Show content after a brief delay to allow loading screen transition
    const timer = setTimeout(() => {
      setShowContent(true);
    }, 500); // 500ms delay to sync with loading screen transition

    return () => clearTimeout(timer);
  }, []);

  const handleExploreLibrary = () => {
    console.log('Explore the Library button clicked');
    navigate('/search');
  };

  const appStyle = {
    background: `linear-gradient(rgba(87, 171, 223, 0.8), rgba(87, 171, 223, 0.8)), url(${libraryImage})`,
    backgroundSize: 'cover',
    backgroundPosition: 'center',
    backgroundRepeat: 'no-repeat',
  };

  const buttonStyle = {
    background: `linear-gradient(rgba(255, 255, 255, 0.7), rgba(255, 255, 255, 0.7)), url(${parchmentImage})`,
    backgroundSize: 'cover',
    backgroundPosition: 'center',
  };

  const title = 'Alexandria'; // 10 letters: A-l-e-x-a-n-d-r-i-a

  return (
    <div className="App" style={appStyle}>
      <div className="top-left-logo">
        <img src={scrollLogo} alt="Alexandria Logo" className="site-logo-small" />
      </div>
      <header className={`App-header ${showContent ? 'show' : ''}`}>
        <div className="curved-text">
          {title.split('').map((letter, index) => (
            <span key={index} className={`letter-${index} ${showContent ? 'show' : ''}`}>
              {letter}
            </span>
          ))}
        </div>
        <button
          className={`explore-library-btn ${showContent ? 'show' : ''}`}
          style={buttonStyle}
          onClick={handleExploreLibrary}
        >
          Explore the Library
        </button>
      </header>
    </div>
  );
}

export default LandingPage;
