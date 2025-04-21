import React from 'react';
import './About.css';

const About = () => {
  return (
    <div className="about-container">
      <section className="about-hero">
        <h1>About FitGPT</h1>
        <p>Your personal fitness assistant, designed to help you achieve your fitness goals.</p>
      </section>

      <section className="about-section">
        <h2>Who Is FitGPT For?</h2>
        <p>
          FitGPT is for anyone who wants to take control of their fitness journey. Whether you're a beginner looking for a starting point or an experienced fitness enthusiast seeking new challenges, FitGPT has something for you.
        </p>
        <div className="audience-cards">
          <div className="card">
            <h3>Beginners</h3>
            <p>New to working out? FitGPT provides easy-to-follow workout plans tailored to your fitness level and goals.</p>
          </div>
          <div className="card">
            <h3>Experienced Users</h3>
            <p>Looking for a new challenge? FitGPT offers advanced workouts to keep you motivated and progressing.</p>
          </div>
        </div>
      </section>

      <section className="about-section">
        <h2>How It Works</h2>
        <p>
          FitGPT makes it easy to get started. Simply input your fitness level, goals, available equipment, and time, and let FitGPT generate a personalized workout plan for you.
        </p>
        <ul className="how-it-works-list">
          <li>Choose your fitness level (beginner, intermediate, advanced).</li>
          <li>Set your goals (e.g., build muscle, lose weight, improve endurance).</li>
          <li>Select your available equipment (e.g., dumbbells, resistance bands, no equipment).</li>
          <li>Enter the time you have available for your workout.</li>
          <li>Get your customized workout plan!</li>
        </ul>
      </section>

      <section className="about-section call-to-action">
        <h2>Ready to Get Started?</h2>
        <p>Generate your first workout plan today and take the first step toward achieving your fitness goals.</p>
        <button className="cta-button" onClick={() => window.location.href = '/generate'}>
          Generate Workout
        </button>
      </section>
    </div>
  );
};

export default About;