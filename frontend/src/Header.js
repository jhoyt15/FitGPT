import React from 'react'
import './Header.css'

const Header = () => {
    return (
        <header className="app-header">
            <div className="logo-container">
                <h1>FitGPT</h1>
            </div>
            <nav className="navigation">
                <a href="/">Home</a>
                <a href="#generate">Generate Workout</a>
                <a href="#about">About</a>
                <a href="#contact">Contact</a>
            </nav>
        </header>
    )
}

export default Header