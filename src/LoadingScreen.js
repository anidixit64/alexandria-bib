import React, { useEffect, useState } from 'react';
import scrollLogo from './scroll_logo.png';
import './LoadingScreen.css';

function LoadingScreen({ onLoadingComplete }) {
  const [isVisible, setIsVisible] = useState(true);

  useEffect(() => {
    // Show loading screen for 3 seconds
    const timer = setTimeout(() => {
      setIsVisible(false);
      // Wait for fade out animation to complete before calling onLoadingComplete
      setTimeout(() => {
        onLoadingComplete();
      }, 500); // 500ms for fade out animation
    }, 3000);

    return () => clearTimeout(timer);
  }, [onLoadingComplete]);

  if (!isVisible) {
    return null;
  }

  return (
    <div className="loading-screen">
      <div className="loading-content">
        <img src={scrollLogo} alt="Alexandria Logo" className="loading-logo" />
        <div className="loading-text">Alexandria</div>
      </div>
    </div>
  );
}

export default LoadingScreen; 