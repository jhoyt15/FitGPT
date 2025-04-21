import React from 'react';
import './Home.css';

const Home = ({ setCurrentSection }) => {
  return (
    <div className="home-container">
      {/* Hero Section */}
      <section className="hero-section">
        <div className="hero-content">
          <h1>FITGPT</h1>
          <h1>Your AI-Powered Fitness Coach</h1>
          <p>Personalized workouts, feedback and fitness tracking—all in one chat.</p>
          <button className="cta-button" onClick={() => setCurrentSection('generate')}>
            Get Your Fitness Plan!
          </button>
        </div>
      </section>

      {/* How It Works Section */}
      <section className="how-it-works-section">
        <h2>How It Works</h2>
        <div className="steps-container">
          <div className="step">
            <div className="step-icon">1</div>
            <h3>Chat with FitGPT</h3>
            <p>Tell us your fitness goals, experience level, and preferences.</p>
          </div>
          <div className="step">
            <div className="step-icon">2</div>
            <h3>Get Your Plan</h3>
            <p>Receive a personalized workout plan tailored just for you.</p>
          </div>
          <div className="step">
            <div className="step-icon">3</div>
            <h3>Track Progress</h3>
            <p>Monitor your progress and stay motivated with regular updates.</p>
          </div>
        </div>
      </section>
    </div>
  );
};

export default Home;