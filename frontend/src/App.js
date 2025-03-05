import React, { useState } from 'react';
import './App.css';
import Header from './Header';
import Content from './Content';
import Footer from './Footer';
import Home from './Home'; // Import the Home component
import About from './About'; // Import the About component
import Contact from './Contact'; // Import the Contact component

function App() {
  const [currentSection, setCurrentSection] = useState('home'); // State to track the current section

  // Function to render the appropriate section based on the state
  const renderSection = () => {
    switch (currentSection) {
      case 'home':
        return <Home />;
      case 'generate':
        return <Content />;
      case 'about':
        return <About />;
      case 'contact':
        return <Contact />;
      default:
        return <Home />;
    }
  };

  return (
    <div className="App">
      <Header setCurrentSection={setCurrentSection} /> {/* Pass setCurrentSection to Header */}
      {renderSection()} {/* Render the current section */}
      <Footer />
    </div>
  );
}

export default App;