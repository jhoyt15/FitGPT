import React from 'react';
import './TimeoutWarning.css';

const TimeoutWarning = ({ onStay, onLogout, timeLeft }) => {
    return (
        <div className="timeout-warning-overlay">
            <div className="timeout-warning-modal">
                <h3>Session Timeout Warning</h3>
                <p>Your session will expire in {timeLeft} seconds due to inactivity.</p>
                <p>Would you like to stay logged in?</p>
                <div className="timeout-warning-buttons">
                    <button onClick={onStay} className="stay-button">Stay Logged In</button>
                    <button onClick={onLogout} className="logout-button">Logout</button>
                </div>
            </div>
        </div>
    );
};

export default TimeoutWarning; 