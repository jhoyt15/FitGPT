import React from 'react';
import './App.css';
import Content from './Content';
import Footer from './Footer';
import Chat from './components/Chat'


function App() {
  return (
    <div className="App">
      <Content />
      <Chat/>
      <Footer />
    </div>
  );
}

export default App;
