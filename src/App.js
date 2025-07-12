import React from 'react';
import './App.css';
import libraryImage from './library.jpg';
import parchmentImage from './parchment.jpg';

function App() {
  const handleExploreLibrary = () => {
    console.log('Explore the Library button clicked');
    // Add your functionality here
  };

  const appStyle = {
    background: `linear-gradient(rgba(87, 171, 223, 0.8), rgba(87, 171, 223, 0.8)), url(${libraryImage})`,
    backgroundSize: 'cover',
    backgroundPosition: 'center',
    backgroundRepeat: 'no-repeat'
  };

  const buttonStyle = {
    background: `linear-gradient(rgba(255, 255, 255, 0.7), rgba(255, 255, 255, 0.7)), url(${parchmentImage})`,
    backgroundSize: 'cover',
    backgroundPosition: 'center'
  };

  const title = "Alexandria"; // 10 letters: A-l-e-x-a-n-d-r-i-a
  
  return (
    <div className="App" style={appStyle}>
      <header className="App-header">
        <div className="curved-text">
          {title.split('').map((letter, index) => (
            <span key={index} className={`letter-${index}`}>
              {letter}
            </span>
          ))}
        </div>
        <button 
          className="explore-library-btn"
          style={buttonStyle}
          onClick={handleExploreLibrary}
        >
          Explore the Library
        </button>
      </header>
    </div>
  );
}

export default App; 