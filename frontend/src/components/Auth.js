import React from 'react';
import { GoogleLogin } from '@react-oauth/google';
import './Auth.css';

const Auth = ({ onLogin, onLogout, user }) => {
    const handleSuccess = async (credentialResponse) => {
        console.log('Google login successful, credential response:', credentialResponse);
        try {
            const response = await fetch('http://localhost:5001/auth/google', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    token: credentialResponse.credential
                }),
                credentials: 'include'
            });

            const data = await response.json();
            console.log('Backend response:', data);
            
            if (data.status === 'success' && data.user) {
                console.log('Login successful, user data:', data.user);
                await onLogin(data.user);
            } else {
                console.error('Login failed:', data);
            }
        } catch (error) {
            console.error('Login failed:', error);
        }
    };

    const handleLogout = async () => {
        try {
            await fetch(`${process.env.REACT_APP_API_URL}/auth/logout`, {
                credentials: 'include'
            });
            onLogout();
        } catch (error) {
            console.error('Logout failed:', error);
        }
    };

    return (
        <div className="auth-container">
            {!user ? (
                <div className="google-login-wrapper">
                    <GoogleLogin
                        onSuccess={handleSuccess}
                        onError={(error) => {
                            console.error('Login Failed:', error);
                        }}
                        useOneTap
                        theme="filled_blue"
                        shape="pill"
                        size="large"
                        text="continue_with"
                        locale="en"
                    />
                </div>
            ) : (
                <div className="user-profile">
                    <img src={user.profile_pic} alt={user.name} className="profile-pic" />
                    <span className="user-name">{user.name}</span>
                    <button onClick={handleLogout} className="logout-button">
                        Logout
                    </button>
                </div>
            )}
        </div>
    );
};

export default Auth; 