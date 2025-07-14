import React, { useEffect, useState } from 'react';
import scrollLogo from './scroll_logo.png';
import './LoadingScreen.css';

function LoadingScreen({ onLoadingComplete }) {
  const [phase, setPhase] = useState('loading'); // 'loading', 'transitioning', 'complete'

  useEffect(() => {
    // Phase 1: Show loading screen for 2 seconds
    const loadingTimer = setTimeout(() => {
      setPhase('transitioning');
      
      // Phase 2: After transition animation completes, trigger landing page
      const transitionTimer = setTimeout(() => {
        setPhase('complete');
        onLoadingComplete();
      }, 1000); // 1 second for the transition animation
      
      return () => clearTimeout(transitionTimer);
    }, 2000);

    return () => clearTimeout(loadingTimer);
  }, [onLoadingComplete]);

  return (
    <div className={`loading-screen ${phase}`}>
      <div className={`loading-content ${phase}`}>
        <img src={scrollLogo} alt="Alexandria Logo" className={`loading-logo ${phase}`} />
        <div className={`loading-text ${phase}`}>Alexandria</div>
      </div>
    </div>
  );
}

export default LoadingScreen; 