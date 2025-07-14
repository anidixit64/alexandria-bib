import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import './LandingPage.css';
import scrollLogo from './scroll_logo.png';

const LandingPage = () => {
  const navigate = useNavigate();
  const [animationState, setAnimationState] = useState('loading'); // loading, transitioning, complete

  useEffect(() => {
    // Start with large centered logo
    setAnimationState('loading');
    
    // After 2 seconds, start transition to corner
    const transitionTimer = setTimeout(() => {
      setAnimationState('transitioning');
    }, 2000);

    // After transition completes, show text and button
    const completeTimer = setTimeout(() => {
      setAnimationState('complete');
    }, 3000);

    return () => {
      clearTimeout(transitionTimer);
      clearTimeout(completeTimer);
    };
  }, []);

  const handleExploreClick = () => {
    navigate('/search');
  };

  return (
    <div className="landing-page">
      <div className={`logo-container ${animationState}`}>
        <img 
          src={scrollLogo} 
          alt="Alexandria Logo" 
          className="logo"
        />
      </div>
      
      <div className={`content ${animationState}`}>
        <h1 className="title">
          <span className="letter">A</span>
          <span className="letter">l</span>
          <span className="letter">e</span>
          <span className="letter">x</span>
          <span className="letter">a</span>
          <span className="letter">n</span>
          <span className="letter">d</span>
          <span className="letter">r</span>
          <span className="letter">i</span>
          <span className="letter">a</span>
        </h1>
        <button className="explore-button" onClick={handleExploreClick}>
          Explore the Library
        </button>
      </div>
    </div>
  );
};

export default LandingPage;
