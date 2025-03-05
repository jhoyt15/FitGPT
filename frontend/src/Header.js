import React from 'react';
import './Header.css';

const Header = ({ setCurrentSection }) => {
  return (
    <header className="app-header">
      <div className="logo-container">
        <h1>FitGPT</h1>
      </div>
      <nav className="navigation">
        <button 
          className="nav-button" 
          onClick={() => setCurrentSection('home')}
        >
          Home
        </button>
        <button 
          className="nav-button" 
          onClick={() => setCurrentSection('generate')}
        >
          Generate Workout
        </button>
        <button 
          className="nav-button" 
          onClick={() => setCurrentSection('about')}
        >
          About
        </button>
        <button 
          className="nav-button" 
          onClick={() => setCurrentSection('contact')}
        >
          Contact
        </button>
      </nav>
    </header>
  );
};

export default Header;