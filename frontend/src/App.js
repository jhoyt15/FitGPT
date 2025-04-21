import React, { useState } from 'react';
import './App.css';
import Content from './Content';
import Chat from './components/Chat'
import Auth from './components/Auth';
import Header from './Header'
import Home from './Home'; // Import the Home component
import About from './About'; // Import the About component
import Contact from './Contact'; // Import the Contact component
import Footer from './Footer';

function App() {
  const [currentSection, setCurrentSection] = useState('home'); // State to track the current section

  // Function to render the appropriate section based on the state
  const renderSection = () => {
    switch (currentSection) {
      case 'home':
        return <Home setCurrentSection={setCurrentSection} />;
      case 'generate':
        return <Content />;
      case 'chat':
        return <Chat/>;
      case 'about':
        return <About />;
      case 'contact':
        return <Contact />;
      case 'login':
        return <Auth setIsAuthenticated={() => {}} setCurrentSection={setCurrentSection} />;
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