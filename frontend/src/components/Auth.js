import React, { useState } from 'react';
import { 
    signInWithEmailAndPassword,
    createUserWithEmailAndPassword,
    signOut,
    GoogleAuthProvider,
    signInWithPopup
} from 'firebase/auth';
import { auth } from '../firebase';
import './Auth.css';

const Auth = ({ onLogin, onLogout, user }) => {
    const [isLogin, setIsLogin] = useState(true);
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');

    const syncUserWithBackend = async (firebaseUser) => {
        try {
            const response = await fetch('http://localhost:5001/auth/google', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    token: await firebaseUser.getIdToken(),
                    email: firebaseUser.email,
                    name: firebaseUser.displayName,
                    profile_pic: firebaseUser.photoURL
                }),
                credentials: 'include'
            });

            const data = await response.json();
            if (data.status === 'success' && data.user) {
                onLogin(data.user);
            } else {
                throw new Error('Failed to sync user with backend');
            }
        } catch (error) {
            console.error('Error syncing user with backend:', error);
            throw error;
        }
    };

    const handleFirebaseLogin = async (e) => {
        e.preventDefault();
        try {
            const userCredential = await signInWithEmailAndPassword(auth, email, password);
            await syncUserWithBackend(userCredential.user);
        } catch (error) {
            setError(error.message);
        }
    };

    const handleFirebaseRegister = async (e) => {
        e.preventDefault();
        try {
            const userCredential = await createUserWithEmailAndPassword(auth, email, password);
            await syncUserWithBackend(userCredential.user);
        } catch (error) {
            setError(error.message);
        }
    };

    const handleGoogleLogin = async () => {
        try {
            const provider = new GoogleAuthProvider();
            const result = await signInWithPopup(auth, provider);
            await syncUserWithBackend(result.user);
        } catch (error) {
            console.error('Google login failed:', error);
            setError('Login failed. Please try again.');
        }
    };

    const handleLogout = async () => {
        try {
            await signOut(auth);
            await fetch('http://localhost:5001/auth/logout', {
                method: 'GET',
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
                <div className="auth-forms">
                    <div className="auth-tabs">
                        <button 
                            className={`auth-tab ${isLogin ? 'active' : ''}`}
                            onClick={() => setIsLogin(true)}
                        >
                            Login
                        </button>
                        <button 
                            className={`auth-tab ${!isLogin ? 'active' : ''}`}
                            onClick={() => setIsLogin(false)}
                        >
                            Register
                        </button>
                    </div>

                    <form onSubmit={isLogin ? handleFirebaseLogin : handleFirebaseRegister}>
                        <div className="form-group">
                            <input
                                type="email"
                                placeholder="Email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                required
                            />
                        </div>
                        <div className="form-group">
                            <input
                                type="password"
                                placeholder="Password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                required
                            />
                        </div>
                        {error && <div className="error-message">{error}</div>}
                        <button type="submit" className="auth-button">
                            {isLogin ? 'Login' : 'Register'}
                        </button>
                    </form>

                    <div className="divider">
                        <span>or</span>
                    </div>

                    <div className="google-login-wrapper">
                        <button 
                            onClick={handleGoogleLogin}
                            className="google-login-button"
                        >
                            Continue with Google
                        </button>
                    </div>
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